import os
import time
import requests
import json
import pandas as pd
from typing import Dict, List, Optional
from tqdm import tqdm

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_API_KEY:
    raise RuntimeError("Please set SERPAPI_API_KEY in your environment.")

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

# ---- Tunables ----
CITY_TEXT = "Christchurch, New Zealand"
DISCOVERY_QUERIES = [
    f"restaurants in {CITY_TEXT}",
    f"bars in {CITY_TEXT}",
    f"food in {CITY_TEXT}",
    f"vietnamese restaurant in {CITY_TEXT}",
    f"chinese restaurant in {CITY_TEXT}",
    f"thai restaurant in {CITY_TEXT}",
    f"japanese restaurant in {CITY_TEXT}",
    f"indian restaurant in {CITY_TEXT}",
]

HL = "en"
RESULTS_PER_PAGE = 20    # Per SerpAPI docs: max 20 for Google Maps search
MAX_START = 100          # Recommended by SerpAPI (pages: 0,20,40,60,80,100)
PAGE_SLEEP_S = 2.0

OUT_DIR = "data/google-data/google-restaurants-place/raw"
os.makedirs(OUT_DIR, exist_ok=True)

OUTPUT_PARQUET = f"{OUT_DIR}/chc_google_places.parquet"
OUTPUT_CSV = f"{OUT_DIR}/chc_google_places.csv"
OUTPUT_JSONL = f"{OUT_DIR}/chc_google_places.jsonl"

CHECKPOINT_PATH = f"{OUT_DIR}/checkpoint_places.parquet"


def _safe_int(n) -> Optional[int]:
    if n is None:
        return None
    try:
        return int(str(n).replace(",", ""))
    except:
        return None


def _extract_items(resp_json: Dict) -> List[Dict]:
    for key in ["local_results", "places", "results", "place_results"]:
        if key in resp_json and isinstance(resp_json[key], list):
            return resp_json[key]
    return []


def _extract_normalized_row(item: Dict, query: str, start: int, search_id: Optional[str]) -> Dict:
    gps = item.get("gps_coordinates", {}) or {}
    itype = item.get("type") or item.get("category")
    if isinstance(itype, list):
        itype = ", ".join(itype)

    reviews_count = _safe_int(item.get("reviews_count", item.get("reviews")))

    return {
        "place_id": item.get("place_id"),
        "data_id": item.get("data_id"),
        "title": item.get("title"),
        "address": item.get("address"),
        "lat": gps.get("latitude"),
        "lon": gps.get("longitude"),
        "type": itype,
        "rating": item.get("rating"),
        "reviews_count": reviews_count,
        "url": item.get("link") or item.get("place_link"),
        "search_query": query,
        "start_offset": start,
        "serpapi_search_id": search_id,
    }


def serpapi_google_maps_search(query: str) -> List[Dict]:
    """
    Uses correct SerpAPI pagination for engine=google_maps.
    Requires location + z parameter for pagination.
    """
    all_rows = []
    start = 0

    while start <= MAX_START:
        params = {
            "engine": "google_maps",
            "q": query,
            "hl": HL,
            "api_key": SERPAPI_API_KEY,
            "location": CITY_TEXT,
            "z": 14,                 
            "start": start,
            "num": RESULTS_PER_PAGE,
        }

        r = requests.get(SERPAPI_ENDPOINT, params=params, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"SerpAPI error {r.status_code}: {r.text[:200]}")

        data = r.json()
        search_id = data.get("search_metadata", {}).get("id")

        items = _extract_items(data)
        if not items:
            break

        for item in items:
            all_rows.append(_extract_normalized_row(item, query, start, search_id))

        start += RESULTS_PER_PAGE
        time.sleep(PAGE_SLEEP_S)

    return all_rows

def discover_christchurch_places() -> pd.DataFrame:
    all_records = []

    # Load checkpoint if exists
    already_scraped = set()
    if os.path.exists(CHECKPOINT_PATH):
        print(f"Resuming from checkpoint: {CHECKPOINT_PATH}")
        df_checkpoint = pd.read_parquet(CHECKPOINT_PATH)
        already_scraped = set(df_checkpoint["search_query"].unique())
        all_records.extend(df_checkpoint.to_dict(orient="records"))

    print(f"Already scraped: {len(already_scraped)} queries")
    print(f"Queries to scrape: {len(DISCOVERY_QUERIES)}")

    for q in tqdm(DISCOVERY_QUERIES, desc="Scraping Google Maps queries"):
        if q in already_scraped:
            tqdm.write(f"Skipping already scraped query: {q}")
            continue

        rows = serpapi_google_maps_search(q)
        tqdm.write(f"Retrieved {len(rows)} rows")

        all_records.extend(rows)

        # Save checkpoint
        df_temp = pd.DataFrame(all_records)
        df_temp.to_parquet(CHECKPOINT_PATH, index=False)
        tqdm.write("Checkpoint updated.")

    df = pd.DataFrame(all_records)
    if df.empty:
        print("No data discovered.")
        return df

    # Deduplicate by place_id OR data_id
    df["unique_key"] = df["place_id"].fillna(df["data_id"])
    df = df.dropna(subset=["unique_key"])
    df = df.sort_values("reviews_count", ascending=False)
    df = df.drop_duplicates(subset=["unique_key"], keep="first")

    return df


def save_outputs(df: pd.DataFrame):
    df.to_parquet(OUTPUT_PARQUET, index=False)
    df.to_csv(OUTPUT_CSV, index=False)

    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for rec in df.to_dict(orient="records"):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    df_places = discover_christchurch_places()

    if not df_places.empty:
        print(f"Total unique places discovered: {len(df_places)}")
        save_outputs(df_places)
        print("Finished! All outputs saved.")
    else:
        print("Nothing to save.")