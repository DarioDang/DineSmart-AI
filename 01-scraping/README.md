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

Scrape Restaurant Metadata

Yelp → `00-scrape-yelp-restaurants.py`

Google → `04-scrape-google-restaurants.py`

Scrape Reviews

Yelp reviews → `02-scrape-yelp-reviews.py` (or resumable version)

Google reviews → `05-scrape-google-reviews.py`

Optional AWS Upload

Yelp → `03-logged-yelp-aws.py`

Google → `06-logged-aws-google-reviews.py`

Enhance Features

Cuisine tagging, embeddings, normalisation → `scrape-enhance-features/`

## 🧩 Key Capabilities

Resumable scraping with checkpoints

Per-restaurant JSON archival

Flattened, RAG-ready CSV/Parquet outputs

Retry logic with exponential backoff

Strict schema consistency

Compatible with Streamlit, Phoenix, Qdrant

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