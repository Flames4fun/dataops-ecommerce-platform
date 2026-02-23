import os
import duckdb

DB_PATH = os.path.join("data", "warehouse", "ecommerce.duckdb")

LOADS = [
    ("orders",       "data/raw/olist_orders_dataset.csv"),
    ("order_items",  "data/raw/olist_order_items_dataset.csv"),
    ("payments",     "data/raw/olist_order_payments_dataset.csv"),
    ("customers",    "data/raw/olist_customers_dataset.csv"),
    ("products",     "data/raw/olist_products_dataset.csv"),
    ("sellers",      "data/raw/olist_sellers_dataset.csv"),
    ("reviews",      "data/raw/olist_order_reviews_dataset.csv"),
    ("categories",   "data/raw/product_category_name_translation.csv"),
    ("geolocation",  "data/raw/olist_geolocation_dataset.csv"),
]

def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = duckdb.connect(DB_PATH)
    con.execute("create schema if not exists raw;")

    for table, csv_path in LOADS:
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"No existe: {csv_path}")

        con.execute(f"""
            create or replace table raw.{table} as
            select * from read_csv_auto('{csv_path}', header=true);
        """)
        count = con.execute(f"select count(*) from raw.{table}").fetchone()[0]
        print(f"OK raw.{table}: {count:,} filas")

    con.close()
    print("Carga completada.")

if __name__ == "__main__":
    main()
