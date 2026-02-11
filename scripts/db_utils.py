from pathlib import Path
from typing import Generator
from contextlib import contextmanager

import duckdb

DB_PATH = Path("warehouse") / "ecommerce.duckdb"


def init_warehouse() -> None:
    """Asegura que exista el directorio del warehouse."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Context manager para DuckDB."""
    init_warehouse()  # asegura carpeta antes de conectar
    conn = duckdb.connect(str(DB_PATH))
    try:
        yield conn
    finally:
        conn.close()