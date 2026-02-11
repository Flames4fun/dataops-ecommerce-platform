"""
Tests for the RAW layer ingestion pipeline.

Validates that:
- RAW schema exists
- All expected tables are present
- Tables contain data
- Key columns exist (smoke test)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts/ to path for imports (consider turning scripts/ into a package instead)
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from db_utils import get_connection
from ingest_raw import FILE_TABLE_MAPPING, ingest_raw


@pytest.fixture(scope="session", autouse=True)
def ensure_raw_ingested() -> None:
    """
    Ensure RAW tables exist before running tests.

    If RAW schema/tables are missing, run the ingestion pipeline once.
    """
    with get_connection() as conn:
        exists = conn.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'raw' AND table_name = 'orders'
            """
        ).fetchone()

    if not exists:
        ingest_raw()


def test_raw_schema_exists():
    with get_connection() as conn:
        schema_names = {
            row[0]
            for row in conn.execute(
                "SELECT schema_name FROM information_schema.schemata"
            ).fetchall()
        }
    assert "raw" in schema_names, "raw schema not found"


def test_all_expected_tables_exist():
    expected_tables = set(FILE_TABLE_MAPPING.values())

    with get_connection() as conn:
        actual_tables = {
            row[0]
            for row in conn.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'raw'
                """
            ).fetchall()
        }

    missing = expected_tables - actual_tables
    assert not missing, f"Missing tables in raw schema: {missing}"


def test_all_tables_have_data():
    tables = set(FILE_TABLE_MAPPING.values())
    with get_connection() as conn:
        for table_name in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM raw.{table_name}").fetchone()[0]
            assert count > 0, f"raw.{table_name} is empty (0 rows)"


def test_orders_table_structure():
    expected_columns = {
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
    }

    with get_connection() as conn:
        actual_columns = {
            row[0]
            for row in conn.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'raw' AND table_name = 'orders'
                """
            ).fetchall()
        }

    missing = expected_columns - actual_columns
    assert not missing, f"raw.orders missing columns: {missing}"


def test_relationship_keys_exist():
    checks = [
        ("customers", "customer_id"),
        ("products", "product_id"),
        ("sellers", "seller_id"),
        ("order_items", "order_id"),
        ("order_items", "product_id"),
    ]

    with get_connection() as conn:
        for table_name, column_name in checks:
            exists = conn.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'raw'
                  AND table_name = ?
                  AND column_name = ?
                """,
                [table_name, column_name],
            ).fetchone()
            assert exists, f"raw.{table_name} missing key column: {column_name}"


def test_geolocation_large_table():
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM raw.geolocation").fetchone()[0]
    assert count > 900_000, (
        f"raw.geolocation has only {count:,} rows, expected 900k+ (possible incomplete load)"
    )
