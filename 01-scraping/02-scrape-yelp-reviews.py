"""
01-scrape-review-resume.py

Resumable Yelp review scraper using SerpApi:
- Reads place_ids from INPUT_CSV
- For each place_id it scrapes ALL reviews (recommended + not_recommended)
- Saves per-place JSON files under "reviews/" and appends flattened rows to a master CSV
- Maintains processed_ids.json to avoid re-scraping completed places on restart
- Uses retries + exponential backoff and tqdm progress bar
"""

import os
import json
import csv
import time
import requests
import pandas as pd
from tqdm import tqdm
from pathlib import Path

# CONFIG
API_KEY = os.getenv("SERPAPI_API_KEY")
BASE_URL = "https://serpapi.com/search"
INPUT_CSV = "data/Christchurch_place_ids_cleaned.csv"
OUTPUT_DIR = Path("reviews")                 # per-place JSON will be saved here
OUTPUT_CSV = "christchurch_reviews_all_pages.csv"
CHECKPOINT_FILE = Path("processed_ids.json")
DELAY = 1.0              # polite pause between requests
MAX_PER_PAGE = 49
RETRY_LIMIT = 5
INITIAL_BACKOFF = 1.0

# Helper: ensure dirs
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----- HTTP helper with retries/backoff -----
def safe_get(params, max_retries=RETRY_LIMIT):
    backoff = INITIAL_BACKOFF
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(BASE_URL, params=params, timeout=30)
            
            # 400 for 'not_recommended' means "no hidden reviews"
            if r.status_code == 400 and params.get("not_recommended") == "true":
                return {"reviews": []}
            
            # Handle transient errors (rate-limit or 5xx)
            if r.status_code == 429 or 500 <= r.status_code < 600:
                raise requests.exceptions.HTTPError(f"{r.status_code} {r.reason}")
            
            r.raise_for_status()
            return r.json()

        except requests.exceptions.HTTPError as e:
            if attempt == max_retries:
                raise
            wait = backoff * (2 ** (attempt - 1))
            tqdm.write(f"⚠️ HTTP error (attempt {attempt}/{max_retries}): {e}. Retrying in {wait:.1f}s...")
            time.sleep(wait)

# ----- SerpApi wrappers -----
def fetch_reviews_page(place_id, start=0, not_recommended=False):
    params = {
        "api_key": API_KEY,
        "engine": "yelp_reviews",
        "place_id": place_id,
        "num": MAX_PER_PAGE,
        "sortby": "date_desc",
    }
    if not_recommended:
        params["not_recommended"] = "true"
        params["not_recommended_start"] = start
    else:
        params["not_recommended"] = "false"
        params["start"] = start
    return safe_get(params)

def fetch_all_reviews(place_id, delay=DELAY):
    all_reviews = []

    # Recommended reviews pagination
    start = 0
    while True:
        data = fetch_reviews_page(place_id, start=start, not_recommended=False)
        reviews = data.get("reviews", [])
        if not reviews:
            break
        for r in reviews:
            r["review_type"] = "recommended"
        all_reviews.extend(reviews)
        if len(reviews) < MAX_PER_PAGE:
            break
        start += MAX_PER_PAGE
        time.sleep(delay)

    # Not-recommended reviews pagination (use not_recommended_start; pages typically 10)
    start = 0
    data = fetch_reviews_page(place_id, start=start, not_recommended=True)
    reviews = data.get("reviews", []) if data else []

    # Only process if there are hidden reviews — otherwise silently skip
    while reviews:
        for r in reviews:
            r["review_type"] = "not_recommended"
        all_reviews.extend(reviews)
        if len(reviews) < 10:
            break
        start += 10
        time.sleep(delay)
        data = fetch_reviews_page(place_id, start=start, not_recommended=True)
        reviews = data.get("reviews", [])
            
    return all_reviews

# ----- Checkpoint helpers -----
def load_processed_ids():
    if CHECKPOINT_FILE.exists():
        try:
            return set(json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()

def save_processed_ids(processed):
    CHECKPOINT_FILE.write_text(json.dumps(sorted(list(processed))), encoding="utf-8")

# ----- CSV append helpers (atomic-ish) -----
def append_rows_to_csv(rows, csv_path=OUTPUT_CSV):
    if not rows:
        return
    file_exists = Path(csv_path).exists()
    keys = rows[0].keys()
    # write in append mode; create header if file absent
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

# ----- Main -----
def main():
    if not API_KEY:
        print("SERPAPI_API_KEY not set. export SERPAPI_API_KEY=your_key")
        return
    if not Path(INPUT_CSV).exists():
        print(f"Input CSV {INPUT_CSV} not found.")
        return

    df = pd.read_csv(INPUT_CSV)
    place_ids = list(pd.Series(df["place_id"].dropna().unique()))
    total_places = len(place_ids)
    if total_places == 0:
        print("No place_id found in input CSV.")
        return

    processed = load_processed_ids()
    tqdm.write(f"{total_places} restaurants found in CSV, {len(processed)} already processed (from checkpoint).")

    # progress bar over only the remaining
    remaining_ids = [pid for pid in place_ids if pid not in processed]
    if not remaining_ids:
        print("Nothing to do — all places processed.")
        return

    # iterate with tqdm
    for pid in tqdm(remaining_ids, desc="Scraping Yelp Reviews", unit="restaurant"):
        try:
            # fetch all reviews (paginated)
            reviews = fetch_all_reviews(pid)
        except Exception as e:
            tqdm.write(f"⚠️ Failed to fetch {pid}: {e}. Skipping and continuing.")
            # do not mark as processed; will retry on next run
            time.sleep(DELAY)
            continue

        # save per-place JSON (overwrite safe)
        place_file = OUTPUT_DIR / f"{pid}.json"
        try:
            place_file.write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            tqdm.write(f"Could not write JSON for {pid}: {e}")

        # flatten and append to master CSV immediately (so work is persisted)
        flat_rows = []
        for r in reviews:
            flat_rows.append({
                "place_id": pid,
                "review_type": r.get("review_type"),
                "user": r.get("user", {}).get("name"),
                "rating": r.get("rating"),
                "date": r.get("date"),
                "text": r.get("comment", {}).get("text", ""),
                "review_position": r.get("position"),
                "user_address": r.get("user", {}).get("address"),
                "useful": r.get("feedback", {}).get("useful"),
                "cool": r.get("feedback", {}).get("cool"),
                "funny": r.get("feedback", {}).get("funny"),
                "user_link": r.get("user", {}).get("link"),
            })

        try:
            append_rows_to_csv(flat_rows, OUTPUT_CSV)
        except Exception as e:
            tqdm.write(f"Could not append CSV for {pid}: {e}")

        # mark processed and persist checkpoint immediately
        processed.add(pid)
        save_processed_ids(processed)

        # small polite pause
        time.sleep(DELAY)

    tqdm.write(f"Completed. Total processed restaurants (checkpoint): {len(processed)}")
    tqdm.write(f"Per-place JSON saved to: {OUTPUT_DIR.resolve()}")
    tqdm.write(f"Master CSV saved to: {Path(OUTPUT_CSV).resolve()}")

if __name__ == "__main__":
    main()
