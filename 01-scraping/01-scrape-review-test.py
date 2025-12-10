"""
01-scrape-review.py
----------------------------------
Fetch Yelp reviews for all restaurants in Christchurch (Stage 2)
using SerpApi 'yelp_reviews' engine and the place_ids scraped in Stage 1.
"""

import os 
import json
import csv 
import time 
import requests 
import pandas as pd 
from tqdm import tqdm

# --- CONFIGURATION ---
API_KEY = os.getenv("SERPAPI_API_KEY")   
BASE_URL = "https://serpapi.com/search"
INPUT_CSV = "data/Christchurch_place_ids.csv"
OUTPUT_CSV = "christchurch_reviews.csv"
OUTPUT_JSON = "christchurch_reviews.json"
REVIEWS_PER_PAGE = 49
DELAY = 1.0  # seconds between requests
MAX_PER_PAGE = 49

def fetch_reviews_page(place_id, start=0, not_recommended=False):
    """Fetch one page of Yelp reviews."""
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

    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_all_reviews(place_id):
    """Paginate through all review pages for one restaurant."""
    all_reviews = []
    # --- Recommended reviews ---
    start = 0
    while True:
        data = fetch_reviews_page(place_id, start=start, not_recommended=False)
        reviews = data.get("reviews", [])
        if not reviews:
            break
        # Add flag to indicate recommended reviews
        for r in reviews:
            r["review_type"] = "recommended"
        all_reviews.extend(reviews)
        if len(reviews) < MAX_PER_PAGE:
            break
        start += MAX_PER_PAGE
        time.sleep(DELAY)

    # --- Not recommended reviews ---
    start = 0
    while True:
        data = fetch_reviews_page(place_id, start=start, not_recommended=True)
        reviews = data.get("reviews", [])
        if not reviews:
            break
        # Add flag to indicate not recommended reviews
        for r in reviews:
            r["review_type"] = "not_recommended"
        all_reviews.extend(reviews)
        # Yelp only gives ~10 not-recommended per page
        if len(reviews) < 10:
            break
        start += 10
        time.sleep(DELAY)

    return all_reviews

def main():
    if not API_KEY:
        print("Missing SERPAPI_API_KEY environment variable.")
        return

    if not os.path.exists(INPUT_CSV):
        print(f"{INPUT_CSV} not found.")
        return

    df = pd.read_csv(INPUT_CSV)
    place_ids = df["place_id"].dropna().unique()
    print(f"Found {len(place_ids)} unique restaurants to scrape.\n")

    all_reviews_flat = []
    all_raw_json = {}

    for pid in tqdm(place_ids, desc="Scraping Yelp Reviews", unit="restaurant"):
        try:
            reviews = fetch_all_reviews(pid)
        except Exception as e:
            print(f"Failed {pid}: {e}")
            continue

        all_raw_json[pid] = reviews

        for r in reviews:
            all_reviews_flat.append({
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

    tqdm.write(f"Total reviews collected: {len(all_reviews_flat)}")


    # Save to CSV and JSON
    if all_reviews_flat:
        keys = all_reviews_flat[0].keys()
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_reviews_flat)
        tqdm.write(f"Saved CSV → {OUTPUT_CSV}")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_raw_json, f, indent=2, ensure_ascii=False)
    tqdm.write(f"Saved JSON → {OUTPUT_JSON}")

if __name__ == "__main__":
    main()