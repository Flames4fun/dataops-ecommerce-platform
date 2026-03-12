from pathlib import Path

from db_utils import get_connection, resolve_warehouse_path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"

LOADS = [
    ("orders", "olist_orders_dataset.csv"),
    ("order_items", "olist_order_items_dataset.csv"),
    ("payments", "olist_order_payments_dataset.csv"),
    ("customers", "olist_customers_dataset.csv"),
    ("products", "olist_products_dataset.csv"),
    ("sellers", "olist_sellers_dataset.csv"),
    ("reviews", "olist_order_reviews_dataset.csv"),
    ("categories", "product_category_name_translation.csv"),
    ("geolocation", "olist_geolocation_dataset.csv"),
]


def main() -> None:
    with get_connection() as conn:
        conn.execute("create schema if not exists raw;")

        for table, filename in LOADS:
            csv_path = RAW_DIR / filename
            if not csv_path.exists():
                raise FileNotFoundError(f"No existe: {csv_path}")

            conn.execute(
                f"""
                create or replace table raw.{table} as
                select * from read_csv_auto(?, header=true);
                """,
                [str(csv_path)],
            )
            count = conn.execute(f"select count(*) from raw.{table}").fetchone()[0]
            print(f"OK raw.{table}: {count:,} filas")

    print(f"Carga completada en: {resolve_warehouse_path()}")


if __name__ == "__main__":
    main()
