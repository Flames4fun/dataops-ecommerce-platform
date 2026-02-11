#!/usr/bin/env python3
"""
RAW layer ingestion for the DataOps E-commerce Platform.

Reads Olist CSV files from data/raw/ and loads them "as-is" into DuckDB
under the `raw` schema.

Requirements:
- data/raw/*.csv downloaded previously (scripts/download_dataset.py)
- scripts/db_utils.py exposing get_connection()
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

# --- Make imports work whether you run as a script or as a module ---
import sys
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from db_utils import get_connection  # scripts/db_utils.py

# Project root (repo root) = parent of /scripts
PROJECT_ROOT = SCRIPTS_DIR.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Explicit mapping: filename -> table name (without schema)
FILE_TABLE_MAPPING: Dict[str, str] = {
    "olist_customers_dataset.csv": "customers",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "payments",
    "olist_order_reviews_dataset.csv": "reviews",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "olist_geolocation_dataset.csv": "geolocation",
    "product_category_name_translation.csv": "categories",
}

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def validate_expected_files() -> None:
    """Ensure all expected CSV files exist inside data/raw/."""
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"RAW directory not found: {RAW_DIR}")

    missing: List[str] = [
        filename
        for filename in FILE_TABLE_MAPPING.keys()
        if not (RAW_DIR / filename).exists()
    ]

    if missing:
        raise FileNotFoundError(
            f"Missing dataset files in {RAW_DIR}: {', '.join(missing)}. "
            "Run scripts/download_dataset.py first."
        )


def ingest_one_csv(csv_path: Path, table_name: str) -> int:
    """
    Load a single CSV into DuckDB as raw.<table_name>.

    Returns the number of loaded rows.
    """
    with get_connection() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS raw")

        # DuckDB reads the CSV directly (faster + lower RAM than pandas)
        conn.execute(
            f"""
            CREATE OR REPLACE TABLE raw.{table_name} AS
            SELECT * FROM read_csv_auto(?, HEADER=true)
            """,
            [str(csv_path)],
        )

        rows = conn.execute(f"SELECT COUNT(*) FROM raw.{table_name}").fetchone()[0]

    logger.info("Ingested %s -> raw.%s (%d rows)", csv_path.name, table_name, rows)
    return int(rows)


def ingest_raw() -> None:
    """
    Run the full RAW ingestion.

    - Validates all expected files exist.
    - Loads each CSV into its corresponding table under `raw`.
    - Idempotent: each run replaces the tables.
    """
    logger.info("Starting RAW ingestion from %s", RAW_DIR)
    validate_expected_files()

    total_rows = 0
    loaded_tables: List[str] = []

    for filename, table_name in FILE_TABLE_MAPPING.items():
        csv_path = RAW_DIR / filename
        rows = ingest_one_csv(csv_path, table_name)
        total_rows += rows
        loaded_tables.append(f"raw.{table_name}")

    
    logger.info(
        "RAW ingestion completed. Tables: %s | Total rows: %d",
        ", ".join(loaded_tables),
        total_rows,
    )

if __name__ == "__main__":
    ingest_raw()



