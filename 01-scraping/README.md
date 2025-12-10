# 📘 01-Scraping Directory — Overview & Structure

This directory contains all scraping components used to build the Christchurch Restaurant AI Agent’s knowledge base.
It includes production-grade scripts for extracting, cleaning, enhancing, and logging restaurant data from Yelp and Google Maps, along with optional AWS upload utilities.

The scraping pipeline is designed with the following goals:

Reproducibility

Fault-tolerant resumability

Consistent data schema

Separation of raw, processed, and enriched datasets

Cloud-ready storage and versioning

## 📁 Directory Structure

```
01-scraping/
│
├── scrape-enhance-features/       # Feature engineering layer for restaurants
│
├── data/                          # Raw + cleaned + processed datasets
│   ├── yelp-data/                 # Yelp place_ids, reviews, JSON dumps
│   ├── google-data/               # Google review datasets
│   ├── scraped-examples-data/     # Samples used for testing/debugging
│   └── jupyter-notebook-experiments/  # Interactive analysis notebooks
│
├── 00-scrape-yelp-restaurants.py  # Scrape Yelp search results (restaurant metadata)
├── 01-scrape-review-test.py       # Small test script for Yelp review scraping
├── 02-scrape-yelp-reviews.py      # Full Yelp review scraper (non-resumable)
├── 03-logged-yelp-aws.py          # Yelp scraper with automated S3 upload
├── 04-scrape-google-restaurants.py# Scrape restaurant metadata from Google
├── 05-scrape-google-reviews.py    # Google reviews scraper
├── 06-logged-aws-google-reviews.py# Google reviews scraper + AWS logger
└── README.md
```

## 🚀 Workflow Summary

| Stage                             | Description                                                         | Script / Directory                                                                                              |
| --------------------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **1. Scrape Restaurant Metadata** | Collect basic restaurant info (name, address, place_id, etc.)       | 🍽 **Yelp:** `00-scrape-yelp-restaurants.py`<br>📍 **Google:** `04-scrape-google-restaurants.py`                |
| **2. Scrape Reviews**             | Retrieve paginated reviews (recommended + not-recommended)          | ⭐ **Yelp:** `02-scrape-yelp-reviews.py` *(or resumable version)*<br>⭐ **Google:** `05-scrape-google-reviews.py` |
| **3. Optional AWS Upload**        | Upload processed datasets to S3 for storage or downstream pipelines | ☁️ **Yelp:** `03-logged-yelp-aws.py`<br>☁️ **Google:** `06-logged-aws-google-reviews.py`                        |
| **4. Enhance Features**           | Add cuisine tagging, embeddings, normalisation, enriched metadata   | 🧠 `scrape-enhance-features/`                                                                                   |


## 🧩 Key Capabilities

| Capability                       | Description                                                                      |
| -------------------------------- | -------------------------------------------------------------------------------- |
| **Resumable Scraping**           | Checkpoint-based system prevents loss of progress                                |
| **Per-Restaurant JSON Archival** | Stores raw, structured datasets for reproducibility                              |
| **RAG-Ready Outputs**            | Flattened CSV + Parquet for efficient retrieval + indexing                       |
| **Retry Logic**                  | Automatic exponential backoff during rate limits or 5xx errors                   |
| **Strict Schema Consistency**    | Uniform fields for easy merging + downstream processing                          |
| **Ecosystem Compatibility**      | Works seamlessly with **Streamlit**, **Phoenix**, **Qdrant**, and your RAG agent |


##  🛠 Requirements

Python 3.10+

requests, pandas, tqdm

SerpAPI key for Yelp/Google scraping

AWS credentials if using upload scripts

## 📌 Notes

Scrapers inside this folder are intended for batch ingestion, not on-demand queries.

All heavy scraping should run locally or via a job scheduler, not inside Streamlit.

## Author 

Dario Dang

Applied Data Scientist | MLOps & Data Engineering Enthusiast