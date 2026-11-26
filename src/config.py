"""Project-wide settings: paths, analysis window and campaign dates."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIRS = {"raw": ROOT / "data" / "raw", "sample": ROOT / "data" / "sample"}
SQL_DIR = ROOT / "sql"
BUILD_DIR = ROOT / "build"
REPORT_DIR = ROOT / "reports"

# Source CSV files -> table names in DuckDB (geolocation is not needed here)
TABLES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

# Olist volume is thin before 2017 and after Aug 2018, so monitoring uses a stable window
ANALYSIS_START = "2017-01-01"
ANALYSIS_END = "2018-08-31"

# Anomaly rule: compare each day with the previous ROLLING_DAYS days
ROLLING_DAYS = 28
Z_THRESHOLD = 3.0
MONITORED_METRICS = ["gmv", "orders", "aov", "bad_review_rate"]

# Campaign review: Black Friday 2017 (Fri 2017-11-24)
CAMPAIGN = {
    "name": "Black Friday 2017",
    "peak_day": "2017-11-24",
    "promo_start": "2017-11-20",
    "promo_end": "2017-11-26",       # the full promo week, Mon-Sun
    "baseline_start": "2017-10-23",
    "baseline_end": "2017-11-19",    # the 4 weeks before
}
