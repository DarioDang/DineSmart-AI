"""
00-scrape-place-id.py
----------------------------------
Collect all Yelp place_id values for restaurants in Christchurch, New Zealand
using SerpApi's Yelp search engine.
"""

import os
import json
import csv 
import time
import requests

# Set the SerpApi API key from environment variable
API_KEY = os.getenv('SERPAPI_API_KEY')
BASE_URL = "https://serpapi.com/search"
CITY = "Christchurch, New Zealand"
TERM = "Restaurant"
PAGES = 10
DELAY = 1.0
MAX_EMPTY = 2

def fetch_place_ids(city=CITY, term=TERM, pages=PAGES):
    "Fetch unique Yelp place_ids for a city"
    place_data = []
    seen_ids = set()
    page = 0
    empty_pages = 0

    while True:
        print(f"Fetching page {page+1} for {city} ...")

        params = {
            "api_key": API_KEY,
            "engine": "yelp",
            "find_desc": term,
            "find_loc": city,
            "start": page * 10,  # Yelp pagination (10 results per page)
        }
        try: 
            resp = requests.get(BASE_URL, params=params, timeout= 20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print("Error fetching data:", e)
            break

        organic_results = data.get("organic_results", [])
        if not organic_results:
            empty_pages += 1
            print(f"No results on page {page+1}. ({empty_pages}/{MAX_EMPTY})")
            if empty_pages >= MAX_EMPTY:
                print("No more pages — stopping scrape.")
                break
            else:
                page += 1
                continue 
        
        empty_pages = 0  # reset counter if we got valid results

        for result in organic_results:
            title = result.get("title")
            link = result.get("link")
            rating = result.get("rating")
            reviews = result.get("reviews")
            price = result.get("price")
            categories = [c.get("title") for c in result.get("categories", [])]
            place_ids = result.get("place_ids", [])

            for pid in place_ids:
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    place_data.append({
                        "place_id": pid,
                        "title": title,
                        "rating": rating,
                        "reviews": reviews,
                        "price": price,
                        "categories": ", ".join(categories),
                        "link": link,
                    })
        print(f"Collected {len(seen_ids)} unique place_ids so far.")
        page += 1
        time.sleep(DELAY)
    return place_data

def save_results(place_data, prefix = "Christchurch"):
    "Write a function to saved the results to CSV and JSON files"
    json_file = f"{prefix}_place_ids.json"
    csv_file = f"{prefix}_place_ids.csv"

    with open(json_file, "w", encoding="utf-8") as jf:
        json.dump(place_data, jf, indent=2, ensure_ascii=False)
    print(f"Saved {len(place_data)} records to {json_file}")

    if place_data:
        keys = place_data[0].keys()
        with open(csv_file, "w", encoding="utf-8", newline='') as cf:
            writer = csv.DictWriter(cf, fieldnames=keys)
            writer.writeheader()
            writer.writerows(place_data)
        print(f"Saved {len(place_data)} records to {csv_file}")

def main():
    if not API_KEY:
        print("Missing SERPAPI_API_KEY environment variable.")
        return

    place_data = fetch_place_ids()
    print(f"Total unique businesses collected: {len(place_data)}")

    if place_data:
        save_results(place_data)

if __name__ == "__main__":
    main()