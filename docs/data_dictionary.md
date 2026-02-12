# Data Dictionary — Raw Layer (`raw` schema)

Field-level documentation for the **raw ingestion layer** stored in `warehouse/ecommerce.duckdb` under the `raw` schema.

## Scope

- **Layer**: `raw` (landed-as-is from CSV; no business transformations)
- **Source**: Olist Brazilian E-Commerce Public Dataset (Kaggle)
- **Granularity**: Table-level purpose + column-level definitions
- **Typing**: In `raw`, timestamps may be ingested as **strings** and cast in downstream layers (e.g., staging).

## Conventions

- **Primary keys (PK)** and **foreign keys (FK)** are documented per table.
- `*_timestamp`, `*_date` columns in `raw` are expected in `YYYY-MM-DD HH:MM:SS` or `YYYY-MM-DD` formats (verify with profiling).
- Monetary values (`price`, `freight_value`, `payment_value`) are in **BRL**.
- Row counts are **expected** counts from the canonical dataset snapshot; validate after ingestion.

---

## `raw.customers`

**Purpose**: Customer address dimension (one row per *customer address*).

**Primary key**: `customer_id`  
**Relationships**:
- `raw.orders.customer_id` → `raw.customers.customer_id`

| Column | Type | Nullable | Description |
| --- | --- | :---: | --- |
| `customer_id` | VARCHAR | No | Unique customer address identifier (PK). |
| `customer_unique_id` | VARCHAR | No | Person identifier; multiple addresses may map to the same person. |
| `customer_zip_code_prefix` | VARCHAR | No | First 5 digits of the ZIP code. |
| `customer_city` | VARCHAR | No | Customer city name. |
| `customer_state` | VARCHAR | No | 2-letter state code (e.g., `SP`, `RJ`). |

**Notes / data quality**:
- `customer_unique_id` is useful for customer-level analytics beyond address changes.
- **Expected rows**: 99,441

---

## `raw.orders`

**Purpose**: Order header facts (one row per order).

**Primary key**: `order_id`  
**Relationships**:
- `raw.orders.customer_id` → `raw.customers.customer_id`
- `raw.order_items.order_id` → `raw.orders.order_id`
- `raw.payments.order_id` → `raw.orders.order_id`
- `raw.reviews.order_id` → `raw.orders.order_id`

| Column | Type | Nullable | Description |
| --- | --- | :---: | --- |
| `order_id` | VARCHAR | No | Unique order identifier (PK). |
| `customer_id` | VARCHAR | No | Customer address FK → `raw.customers.customer_id`. |
| `order_status` | VARCHAR | No | Order state. See **Status values** below. |
| `order_purchase_timestamp` | VARCHAR | No | Order creation timestamp. |
| `order_approved_at` | VARCHAR | Yes | Payment approval timestamp. |
| `order_delivered_carrier_date` | VARCHAR | Yes | Handoff timestamp to the carrier/logistics. |
| `order_delivered_customer_date` | VARCHAR | Yes | Actual delivery timestamp to customer. |
| `order_estimated_delivery_date` | VARCHAR | Yes | Estimated delivery date/timestamp. |

**Status values**: `delivered`, `shipped`, `canceled`, `processing`, `invoiced`, `unavailable`

**Notes / data quality**:
- In `raw`, timestamps may be strings; cast to TIMESTAMP/DATE in downstream layers.
- Canceled/unavailable orders often have NULL delivery fields.
- **Expected rows**: 99,441

---

## `raw.order_items`

**Purpose**: Order line items (one row per product line in an order).

**Primary key**: (`order_id`, `order_item_id`)  
**Relationships**:
- `raw.order_items.order_id` → `raw.orders.order_id`
- `raw.order_items.product_id` → `raw.products.product_id`
- `raw.order_items.seller_id` → `raw.sellers.seller_id`

| Column | Type | Nullable | Description |
| --- | --- | :---: | --- |
| `order_id` | VARCHAR | No | Order FK → `raw.orders.order_id`. |
| `order_item_id` | INTEGER | No | Line item sequence within the order (1, 2, 3...). |
| `product_id` | VARCHAR | No | Product FK → `raw.products.product_id`. |
| `seller_id` | VARCHAR | No | Seller FK → `raw.sellers.seller_id`. |
| `shipping_limit_date` | VARCHAR | No | Seller deadline timestamp for shipping the item. |
| `price` | DOUBLE | No | Item price in BRL. |
| `freight_value` | DOUBLE | No | Freight/shipping cost in BRL **per item** (not per order). |

**Notes / data quality**:
- A single order may include items sold by multiple sellers.
- Validate that `order_item_id` is unique per `order_id`.
- **Expected rows**: 112,650

---

## `raw.payments`

**Purpose**: Payment transactions (one or more rows per order).

**Primary key**: (`order_id`, `payment_sequential`)  
**Relationships**:
- `raw.payments.order_id` → `raw.orders.order_id`

| Column | Type | Nullable | Description |
| --- | --- | :---: | --- |
| `order_id` | VARCHAR | No | Order FK → `raw.orders.order_id`. |
| `payment_sequential` | INTEGER | No | Payment sequence number within the order (1, 2, 3...). |
| `payment_type` | VARCHAR | No | Payment method. See **Payment types** below. |
| `payment_installments` | INTEGER | No | Number of installments (typically 1–24). |
| `payment_value` | DOUBLE | No | Paid amount in BRL for this transaction row. |

**Payment types**: `credit_card`, `boleto`, `voucher`, `debit_card`

**Notes / data quality**:
- Orders may be split across multiple transactions/methods; validate `SUM(payment_value)` per `order_id`.
- **Expected rows**: 103,886

---

## `raw.reviews`

**Purpose**: Customer reviews (zero or one review per order; dataset may include multiple review IDs historically).

**Primary key**: `review_id`  
**Relationships**:
- `raw.reviews.order_id` → `raw.orders.order_id`

| Column | Type | Nullable | Description |
| --- | --- | :---: | --- |
| `review_id` | VARCHAR | No | Unique review identifier (PK). |
| `order_id` | VARCHAR | No | Order FK → `raw.orders.order_id`. |
| `review_score` | INTEGER | No | Rating score (1–5). |
| `review_comment_title` | VARCHAR | Yes | Review title text. |
| `review_comment_message` | VARCHAR | Yes | Review body text. |
| `review_creation_date` | VARCHAR | No | Review creation timestamp. |
| `review_answer_timestamp` | VARCHAR | Yes | Seller response timestamp. |

**Notes / data quality**:
- Not all orders have reviews.
- Comments may be NULL for rating-only reviews.
- **Expected rows**: 100,000

---

## `raw.products`

**Purpose**: Product catalog dimension.

**Primary key**: `product_id`  
**Relationships**:
- `raw.order_items.product_id` → `raw.products.product_id`
- `raw.products.product_category_name` → `raw.categories.product_category_name` (optional)

| Column | Type | Nullable | Description |
| --- | --- | :---: | --- |
| `product_id` | VARCHAR | No | Unique product identifier (PK). |
| `product_category_name` | VARCHAR | Yes | Product category in Portuguese; may be NULL. |
| `product_name_length` | INTEGER | Yes | Character count of product name. |
| `product_description_length` | INTEGER | Yes | Character count of product description. |
| `product_photos_qty` | INTEGER | Yes | Number of product photos. |
| `product_weight_g` | INTEGER | Yes | Weight in grams. |
| `product_length_cm` | INTEGER | Yes | Package length in cm. |
| `product_height_cm` | INTEGER | Yes | Package height in cm. |
| `product_width_cm` | INTEGER | Yes | Package width in cm. |

**Notes / data quality**:
- Some products are uncategorized (`product_category_name` is NULL).
- Dimensions/weight are commonly used for freight/volume analysis.
- **Expected rows**: 32,951

---

## `raw.sellers`

**Purpose**: Seller dimension (one row per seller).

**Primary key**: `seller_id`  
**Relationships**:
- `raw.order_items.seller_id` → `raw.sellers.seller_id`

| Column | Type | Nullable | Description |
| --- | --- | :---: | --- |
| `seller_id` | VARCHAR | No | Unique seller identifier (PK). |
| `seller_zip_code_prefix` | VARCHAR | No | First 5 digits of ZIP code. |
| `seller_city` | VARCHAR | No | Seller city name. |
| `seller_state` | VARCHAR | No | 2-letter state code. |

**Notes / data quality**:
- **Expected rows**: 3,095

---

## `raw.geolocation`

**Purpose**: Brazilian ZIP-code geolocation reference. May contain **multiple entries per ZIP prefix**.

**Primary key**: None (reference table with duplicates)  
**Relationships**:
- `raw.customers.customer_zip_code_prefix` ↔ `raw.geolocation.geolocation_zip_code_prefix` (many-to-many)
- `raw.sellers.seller_zip_code_prefix` ↔ `raw.geolocation.geolocation_zip_code_prefix` (many-to-many)

| Column | Type | Nullable | Description |
| --- | --- | :---: | --- |
| `geolocation_zip_code_prefix` | VARCHAR | No | First 5 digits of ZIP code. |
| `geolocation_lat` | DOUBLE | No | Latitude. |
| `geolocation_lng` | DOUBLE | No | Longitude. |
| `geolocation_city` | VARCHAR | No | City name. |
| `geolocation_state` | VARCHAR | No | 2-letter state code. |

**Notes / data quality**:
- A ZIP prefix can map to multiple coordinates (coverage areas / data duplicates).
- Downstream layers typically deduplicate/aggregate (e.g., median lat/lng per ZIP prefix).
- **Expected rows**: 1,000,163

---

## `raw.categories`

**Purpose**: Product category translation mapping (Portuguese → English).

**Primary key**: `product_category_name`  
**Relationships**:
- `raw.products.product_category_name` → `raw.categories.product_category_name`

| Column | Type | Nullable | Description |
| --- | --- | :---: | --- |
| `product_category_name` | VARCHAR | No | Category name in Portuguese (PK). |
| `product_category_name_english` | VARCHAR | No | Category name in English. |

**Notes / data quality**:
- Join is optional because `raw.products.product_category_name` may be NULL.
- **Expected rows**: 71
