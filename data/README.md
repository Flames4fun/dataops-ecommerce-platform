# Data Directory

This directory documents the project's local data layout.

## Structure

- `data/raw/`: source CSV files downloaded from Kaggle (excluded from Git via `.gitignore`)
- `WAREHOUSE_PATH` (default: `data/warehouse/ecommerce.duckdb`): local DuckDB analytical warehouse file (excluded from Git via `.gitignore`)
- Raw files are not tracked because they are:
  - Large (1.5M+ rows combined)
  - Reproducible (can be re-downloaded)
  - Source data (kept as-is, without transformations)

## Dataset

- **Name**: Brazilian E-Commerce Public Dataset by Olist
- **Source**: Kaggle (`olistbr/brazilian-ecommerce`)
- **Time range**: 2016–2018 (as described on Kaggle; validate exact min/max timestamps from `raw.orders`)
- **License**: **CC BY-NC-SA 4.0** (Non-Commercial). Do not use the dataset for commercial purposes. See the Kaggle dataset page for details.

## Local verification (recommended)

After ingestion, validate the date range directly from the warehouse file configured by `WAREHOUSE_PATH` (default: `data/warehouse/ecommerce.duckdb`):

```sql
SELECT
  MIN(order_purchase_timestamp) AS min_ts,
  MAX(order_purchase_timestamp) AS max_ts
FROM raw.orders;
```

The ingestion pipeline loads each CSV into DuckDB under the `raw` schema.

| Table             |      Rows | Description                     |
| ----------------- | --------: | ------------------------------- |
| `raw.customers`   |    99,441 | Customer records                |
| `raw.orders`      |    99,441 | Orders (one row per order)      |
| `raw.order_items` |   112,650 | Order line items                |
| `raw.payments`    |   103,886 | Payments per order              |
| `raw.reviews`     |   100,000 | Reviews per order               |
| `raw.products`    |    32,951 | Product catalog                 |
| `raw.sellers`     |     3,095 | Seller records                  |
| `raw.geolocation` | 1,000,163 | Zip code geolocation mapping    |
| `raw.categories`  |        71 | Category translations (PT → EN) |

**Total**: 1,551,698 rows across 9 tables

## Source files

| DuckDB table      | CSV file                             |
| ----------------- | ------------------------------------ |
| `raw.customers`   | `olist_customers_dataset.csv`        |
| `raw.orders`      | `olist_orders_dataset.csv`           |
| `raw.order_items` | `olist_order_items_dataset.csv`      |
| `raw.payments`    | `olist_order_payments_dataset.csv`   |
| `raw.reviews`     | `olist_order_reviews_dataset.csv`    |
| `raw.products`    | `olist_products_dataset.csv`         |
| `raw.sellers`     | `olist_sellers_dataset.csv`          |
| `raw.geolocation` | `olist_geolocation_dataset.csv`      |
| `raw.categories`  | `product_category_name_translation.csv` |

## Notes

- Raw tables are loaded as-is (no transformations).
- Timestamps remain strings in `raw` and will be typed in later layers.
- Some products have a NULL category name, so joins to `raw.categories` may be missing for those rows. 
