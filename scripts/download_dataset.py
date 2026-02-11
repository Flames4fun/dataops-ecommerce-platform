#!/usr/bin/env python3
"""
feat(ingestion): Download Olist Brazilian E-Commerce dataset

Dataset: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce[web:5]
9 CSV files: customers, orders, payments, items, products, etc.
"""

import os
import logging
import requests
from pathlib import Path
from typing import List
import zipfile

# Configuración logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
URLS = {
    "olist_customers_dataset.csv": "https://raw.githubusercontent.com/lavanyabk/Predictive-Analysis-on-Olist-dataset/master/olist_customers_dataset.csv",
    "olist_orders_dataset.csv": "https://raw.githubusercontent.com/lavanyabk/Predictive-Analysis-on-Olist-dataset/master/olist_orders_dataset.csv",
    "olist_order_items_dataset.csv": "https://raw.githubusercontent.com/lavanyabk/Predictive-Analysis-on-Olist-dataset/master/olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv": "https://raw.githubusercontent.com/lavanyabk/Predictive-Analysis-on-Olist-dataset/master/olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv": "https://raw.githubusercontent.com/lavanyabk/Predictive-Analysis-on-Olist-dataset/master/olist_order_reviews_dataset.csv",
    "olist_products_dataset.csv": "https://raw.githubusercontent.com/lavanyabk/Predictive-Analysis-on-Olist-dataset/master/olist_products_dataset.csv",
    "olist_sellers_dataset.csv": "https://raw.githubusercontent.com/lavanyabk/Predictive-Analysis-on-Olist-dataset/master/olist_sellers_dataset.csv",

    "olist_geolocation_dataset.csv": "https://raw.githubusercontent.com/kiranbudati/data/master/olist_geolocation_dataset.csv",
    "product_category_name_translation.csv": "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets/product_category_name_translation.csv",
}

def download_file(url: str, filepath: Path) -> None:
    """Download single file with progress."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    logger.info(f"Downloaded: {filepath}")

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    for filename, url in URLS.items():
        filepath = RAW_DIR / filename
        if filepath.exists():
            logger.info(f"Already exists: {filename}")
            continue
        download_file(url, filepath)
    
    logger.info(f"Dataset ready in {RAW_DIR}")
    logger.info(f"Files: {len(list(RAW_DIR.glob('*.csv')))}")

if __name__ == "__main__":
    main()