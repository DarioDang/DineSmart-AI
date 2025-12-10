"""
Scrape newest Google Maps reviews for all restaurants in Christchurch.
- Uses engine=google_maps_reviews
- Fetches first page (~10 newest reviews) ONLY
- Auto-checkpointing (resume-safe)
- Error handling, retry, rate limit
- Saves CSV, Parquet, JSONL
"""

import os
import time
import json
import requests
import pandas as pd
from tqdm import tqdm

# Configuration
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
if not SERPAPI_API_KEY:
    raise RuntimeError("Please set SERPAPI_API_KEY")

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

INPUT_RESTAURANTS = "data/google-data/chc_google_places_v1.csv"

OUT_DIR = "data/google-data/google-reviews/raw"
os.makedirs(OUT_DIR, exist_ok=True)

CHECKPOINT_PATH = f"{OUT_DIR}/checkpoint_reviews.csv"
OUTPUT_JSONL = f"{OUT_DIR}/chc_reviews.jsonl"
OUTPUT_CSV = f"{OUT_DIR}/chc_reviews.csv"
OUTPUT_PARQUET = f"{OUT_DIR}/chc_reviews.parquet"

RATE_LIMIT_SECONDS = 1.5      # to avoid 1000 req/hr throttling
RETRY_LIMIT = 3               # retry on failures
PAGE_LIMIT = 1                # ONLY FIRST PAGE (10 newest reviews)


# Helper Functions
def scrape_google_reviews_page(place_id, next_page_token=None):
    """Fetch ONLY first page (~10 reviews)."""
    params = {
        "engine": "google_maps_reviews",
        "api_key": SERPAPI_API_KEY,
        "hl": "en",
        "place_id": place_id,
        "sort_by": "newestFirst",
    }
    if next_page_token:
        params["next_page_token"] = next_page_token

    r = requests.get(SERPAPI_ENDPOINT, params=params, timeout=60)

    if r.status_code != 200:
        raise RuntimeError(f"SerpAPI HTTP {r.status_code}: {r.text[:200]}")

    return r.json()


def scrape_reviews_for_place(place_id):
    """Scrape ONLY FIRST PAGE (~10 reviews) for one place_id."""
    all_reviews = []

    # retry handler
    for attempt in range(RETRY_LIMIT):
        try:
            data = scrape_google_reviews_page(place_id, None)
            break
        except Exception as e:
            print(f"[ERROR] {place_id}: {e}. Retry ({attempt+1}/{RETRY_LIMIT})")
            time.sleep(3)
    else:
        print(f"[FAILED] {place_id}, skipping.")
        return all_reviews

    # extract reviews
    reviews = data.get("reviews", [])
    if not reviews:
        return all_reviews

    for r in reviews:
        r["page_number"] = 1
        r["place_id"] = place_id

    all_reviews.extend(reviews)
    return all_reviews



# Load restaurants + checkpoint
restaurants = pd.read_csv(INPUT_RESTAURANTS)
place_ids = restaurants["place_id"].dropna().unique().tolist()

if os.path.exists(CHECKPOINT_PATH):
    scraped_df = pd.read_csv(CHECKPOINT_PATH)
    already_done = set(scraped_df["place_id"])
else:
    scraped_df = pd.DataFrame(columns=["place_id"])
    already_done = set()

print(f"Total restaurants: {len(place_ids)}")
print(f"Already scraped: {len(already_done)}")
print(f"Remaining: {len(set(place_ids) - already_done)}")


# Main scraping loop
all_reviews = []

for place_id in tqdm(place_ids, desc="Scraping restaurants"):
    if place_id in already_done:
        continue

    reviews = scrape_reviews_for_place(place_id)
    all_reviews.extend(reviews)

    # checkpoint
    scraped_df = pd.concat(
        [scraped_df, pd.DataFrame([{"place_id": place_id}])],
        ignore_index=True
    )
    scraped_df.to_csv(CHECKPOINT_PATH, index=False)

    # rate limit to avoid exceeding 1000 / hour
    time.sleep(RATE_LIMIT_SECONDS)


# Save outputs
df = pd.json_normalize(all_reviews)
df = df.astype(str)  # prevent Parquet dtype errors

df.to_csv(OUTPUT_CSV, index=False)
df.to_parquet(OUTPUT_PARQUET, index=False)

with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
    for row in all_reviews:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print("\nScraping finished!")
print(f"Total reviews saved: {len(df)}")
print(f"CSV → {OUTPUT_CSV}")
print(f"Parquet → {OUTPUT_PARQUET}")
print(f"JSONL → {OUTPUT_JSONL}")
