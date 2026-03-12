from contextlib import contextmanager
import os
from pathlib import Path
from typing import Generator

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WAREHOUSE_PATH = Path("data") / "warehouse" / "ecommerce.duckdb"


def resolve_warehouse_path() -> Path:
    """
    Resolve DuckDB warehouse path from environment variables.

    Priority:
    1. WAREHOUSE_PATH
    2. DUCKDB_PATH (legacy fallback)
    3. data/warehouse/ecommerce.duckdb
    """
    configured = os.getenv("WAREHOUSE_PATH") or os.getenv("DUCKDB_PATH")
    path = Path(configured) if configured else DEFAULT_WAREHOUSE_PATH
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def init_warehouse(db_path: Path | None = None) -> Path:
    """Ensure warehouse directory exists and return resolved path."""
    resolved_path = db_path or resolve_warehouse_path()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    return resolved_path


@contextmanager
def get_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Context manager for DuckDB connections."""
    db_path = init_warehouse()
    conn = duckdb.connect(str(db_path))
    try:
        yield conn
    finally:
        conn.close()
