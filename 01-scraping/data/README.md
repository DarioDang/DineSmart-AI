# 📁 Data Directory — Structure & Purpose

This directory stores all datasets generated during the restaurant scraping pipeline, including raw extracted data, cleaned and merged datasets, enriched outputs, and example files used for debugging.

The folder is organized into logical layers to ensure clarity, reproducibility, and compatibility with downstream components (Qdrant indexing, Streamlit Agent, Phoenix evaluations, etc.).

## 📂 Folder Breakdown

```
data/
│
├── yelp-data/
│   ├── chc-yelps-reviews-data/
│   │   ├── chc-yelp-place-ids-reviews.parquet
│   │   ├── chc-yelp-place-ids.json
│   │   └── christchurch-reviews-all-pages.csv
│   │
│   ├── final-dataset/
│   │   ├── chc-yelp-place-ids.json
│   │   ├── chc-yelp-reviews.json
│   │   ├── chc-yelp-reviews.parquet
│   │   └── chc-yelp-reviews.csv
│   │
│   └── README.md (optional)
│
├── google-data/
│   ├── google-restaurants-place/
│   │   └── chc_google_places.csv
│   │
│   ├── google-reviews/
│   │   ├── raw/
│   │   │   ├── chc_reviews.csv
│   │   │   ├── chc_reviews.json
│   │   │   └── chc_reviews.parquet
│   │   │
│   │   └── final/
│   │       ├── chc-google-reviews.json
│   │       └── chc-google-reviews.parquet
│
├── scraped-examples-data/
│   ├── sample-yelp-review.json
│   └── sample-google-review.json
│
└── jupyter-notebook-experiments/
    ├── scrape-advanced-features-test.ipynb
    ├── scrape-google-reviews.ipynb
    └── scrape-yelp-reviews.ipynb         
```

## 🗂 Folder Purpose Breakdown
### 📘 Yelp Data
| Folder                              | Description                                                                  | Key Files                                                                                                       |
| ----------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `yelp-data/chc-yelps-reviews-data/` | Raw + flattened Yelp reviews scraped from SerpAPI                            | - `christchurch-reviews-all-pages.csv`<br>- `chc-yelp-place-ids.json`<br>- `chc-yelp-place-ids-reviews.parquet` |
| `yelp-data/final-dataset/`          | Cleaned, merged, and final Yelp datasets used for downstream ingestion & RAG | - `chc-yelp-reviews.json`<br>- `chc-yelp-reviews.parquet`<br>- `chc-yelp-reviews.csv`                           |
| (optional) README.md                | Explains Yelp scraping lineage                                               | —                                                                                                               |

### 📗 Google Data
| Folder                      | Description                                                         | Key Files                                                              |
| --------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `google-restaurants-place/` | Google Places metadata (IDs, names, addresses)                      | - `chc_google_places.csv`                                              |
| `google-reviews/raw/`       | Raw exported reviews directly from the scraper                      | - `chc_reviews.csv`<br>- `chc_reviews.json`<br>- `chc_reviews.parquet` |
| `google-reviews/final/`     | Cleaned + processed datasets ready for model ingestion or S3 upload | - `chc-google-reviews.json`<br>- `chc-google-reviews.parquet`          |

### 🧪 Examples & Notebooks
| Folder                          | Purpose                                                                                                                        |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `scraped-examples-data/`        | Minimal example review files used for debugging pipeline steps                                                                 |
| `jupyter-notebook-experiments/` | Notebooks used to prototype scrapers, validate review extraction, test feature enhancement (e.g., cuisine tagging, embeddings) |


### 🎯 Usage in the Pipeline

| Stage            | Input Folder            | Output Folder                       |
| ---------------- | ----------------------- | ----------------------------------- |
| Scrape place_ids | —                       | `yelp-data/chc-yelps-reviews-data/` |
| Scrape reviews   | Yelp/Google raw folders | Same folder (raw JSON + CSV)        |
| Clean & merge    | Raw folders             | `final-dataset/` or `final/`        |
| Enrich features  | Final datasets          | Qdrant-ready vectors or metadata    |
| Upload to S3     | Final datasets          | `dario-ai-agent-reviews` bucket     |


## 📝 Notes

Large datasets should not be committed to GitHub.

Parquet is the preferred format for downstream use.

All review timestamps should be normalized before ingestion.

## Author

Dario Dang

Applied Data Scientist | MLOps & Data Engineering Enthusiast

