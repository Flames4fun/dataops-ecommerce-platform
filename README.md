# DataOps E-commerce Platform

Production-like, end-to-end **Data Engineering** project: ingest -> warehouse -> transform -> test -> orchestrate -> serve.

> Portfolio focus: reproducibility, data quality, schema-as-code, and deployable components.

---

## What this project demonstrates

- **Idempotent ingestion** into a local analytical warehouse
- **Warehouse-first modeling** with dbt (`staging -> intermediate -> marts`)
- **Automated data quality** (`pytest` + `dbt test` + reconciliation tests + dbt model/source contracts via `data_tests`)
- **Orchestration-ready** workflows (Prefect flows)
- **API serving layer** for curated datasets (FastAPI)
- **Observability hooks** (structured logs + basic metrics)

---

## Architecture

**CSV dataset** -> **Ingestion (Python)** -> **DuckDB (`WAREHOUSE_PATH`, default: `data/warehouse/ecommerce.duckdb`)** -> **dbt models** -> **FastAPI endpoints**

Quality gates:
- `pytest` (pipeline/unit checks)
- `dbt test` (schema + business rules + reconciliation tests)

Orchestration (planned):
- Prefect flows schedule ingestion + dbt

---

## Tech stack

| Layer | Technology | Why it is here |
| --- | --- | --- |
| Language | Python 3.11+ | Pipelines, orchestration, API |
| Warehouse | DuckDB | Portable analytics warehouse |
| Transformations | dbt | SQL modeling + tests + docs |
| Orchestration | Prefect | Scheduling + retries |
| API | FastAPI | Serve curated data products |
| Testing | pytest | Unit/integration checks |
| CI | GitHub Actions | Automated checks on PRs |

---

## Project status (roadmap)

| Phase | Status | Deliverable |
| --- | :---: | --- |
| 1 - Raw ingestion | Completed | Download + ingest + validation tests |
| 2 - dbt transformations | Completed (core) / Phase 2.2 local closure evidence complete (CI evidence pending) | `staging` + `intermediate` + `marts` + `facts` + `dbt tests` + `reconciliation` + `fact_payments` + `mart_kpis_daily` + `exposures` + `owner/SLA metadata` + `technical benchmark` |
| 3 - Orchestration | Planned | Prefect flows + schedules |
| 4 - API serving | Planned | FastAPI endpoints over marts |
| 5 - Observability | Planned | Logs + metrics + basic dashboards |

---

## Quick start

### Prerequisites
- Python 3.11+
- Git
- (Optional) DuckDB CLI

### Setup

```bash
git clone https://github.com/Flames4fun/dataops-ecommerce-platform.git
cd dataops-ecommerce-platform

python -m venv .venv
# Linux/Mac
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.lock

# Optional: override warehouse path (default already works)
# Linux/Mac
export WAREHOUSE_PATH=data/warehouse/ecommerce.duckdb
# Windows (PowerShell)
$env:WAREHOUSE_PATH="data/warehouse/ecommerce.duckdb"
```

### Run Phase 1 (download -> ingest -> validate)

```bash
# 1) Download dataset into data/raw/
python scripts/download_dataset.py

# 2) Ingest raw CSVs into DuckDB
python scripts/ingest_raw.py

# 3) Validate ingestion
pytest -q
```

Expected:
- warehouse file created at `WAREHOUSE_PATH` (default: `data/warehouse/ecommerce.duckdb`)
- 9 tables under the `raw` schema
- tests pass

### Run Phase 2 (dbt)

```bash
# 1) Validate dbt configuration and warehouse connection
dbt debug --project-dir ./dbt --profiles-dir ./dbt

# 2) Run end-to-end dbt pipeline (models + tests)
dbt build --project-dir ./dbt --profiles-dir ./dbt

# 3) Run reconciliation tests only (counts/sums)
dbt test --project-dir ./dbt --profiles-dir ./dbt --select path:tests/test_reconcile_fact_orders_count.sql
dbt test --project-dir ./dbt --profiles-dir ./dbt --select path:tests/test_reconcile_fact_order_items_count.sql
dbt test --project-dir ./dbt --profiles-dir ./dbt --select path:tests/test_reconcile_fact_order_items_sums.sql
dbt test --project-dir ./dbt --profiles-dir ./dbt --select path:tests/test_reconcile_mart_kpis_daily_order_counts.sql
dbt test --project-dir ./dbt --profiles-dir ./dbt --select path:tests/test_reconcile_mart_kpis_daily_gmv.sql

# 4) Generate and serve dbt documentation locally
dbt docs generate --project-dir ./dbt --profiles-dir ./dbt
dbt docs serve --project-dir ./dbt --profiles-dir ./dbt
```

### Run Phase 2.2 Technical Benchmark (formal evidence)

```bash
python scripts/benchmark_dbt_build.py --dbt-executable .venv/Scripts/dbt.exe --project-dir dbt --profiles-dir dbt --runs-per-scenario 5 --phase2-selector "mart_kpis_daily+" --clean-artifacts --warehouse-reuse-policy reuse --environment-name local
```

Important:
- `dbt/target/` and `dbt/logs/` are intentionally gitignored.
- Generated docs artifacts (`manifest.json`, `catalog.json`, `index.html`, etc.) are local build outputs and are not committed.
- YAML schema checks in `dbt/models/**` and `dbt/models/staging/_sources.yml` use `data_tests:` (dbt deprecation-safe syntax).
- Semantic layer metadata is declared via `dbt/models/exposures.yml` and model-level `meta` fields on critical marts/facts.
- Formal technical benchmark evidence is generated under `artifacts/benchmarks/` and documented in `docs/phase2_2_technical_benchmark.md`.

### Star schema (marts)

| Model | Type | Grain |
| --- | --- | --- |
| `dim_customers` | Dimension | 1 row per `customer_unique_id` |
| `dim_products` | Dimension | 1 row per `product_id` |
| `dim_sellers` | Dimension | 1 row per `seller_id` |
| `dim_dates` | Dimension | 1 row per `date_day` |
| `fact_orders` | Fact | 1 row per `order_id` |
| `fact_order_items` | Fact | 1 row per `order_item_key` (derived from `order_id` + `order_item_id`) |
| `fact_payments` | Fact | 1 row per `payment_key` (derived from `order_id` + `payment_sequential`) |
| `mart_kpis_daily` | KPI Mart | 1 row per `kpi_date` |

---

## Query examples

### DuckDB CLI

```bash
# Linux/Mac
duckdb "${WAREHOUSE_PATH:-data/warehouse/ecommerce.duckdb}"

# Windows (PowerShell)
duckdb $env:WAREHOUSE_PATH
```

```sql
SHOW TABLES FROM raw;

SELECT order_status, COUNT(*) AS n
FROM raw.orders
GROUP BY order_status
ORDER BY n DESC;
```

### Python

```python
from scripts.db_utils import get_connection

with get_connection() as conn:
    df = conn.execute(
        """
        SELECT order_status, COUNT(*) AS n
        FROM raw.orders
        GROUP BY order_status
        ORDER BY n DESC
        """
    ).fetchdf()

print(df)
```

---

## Repository layout

```text
dataops-ecommerce-platform/
|-- api/                    # FastAPI app (Phase 4)
|-- dbt/                    # dbt project (Phase 2)
|   |-- models/
|   |   |-- staging/        # Source cleanup and standardization models
|   |   |-- intermediate/   # Reusable business logic models
|   |   `-- marts/          # Final dimensional/fact models for analytics
|   |-- tests/              # Custom data reconciliation tests (SQL)
|   |-- macros/             # Reusable SQL macros
|   `-- target/             # Generated artifacts (gitignored)
|-- docs/                   # Documentation (data dictionary, decisions)
|-- pipelines/              # Prefect flows (Phase 3)
|-- scripts/                # Download + ingestion + helpers
|-- tests/                  # Python unit/integration tests
`-- data/                   # Local data (gitignored)
    |-- raw/                # Source CSVs (gitignored)
    `-- warehouse/          # DuckDB file: data/warehouse/ecommerce.duckdb (gitignored)
```

---

## Documentation

- **Data directory**: `data/README.md` (local layout + verification)
- **Data dictionary**: `docs/data_dictionary.md` (raw schema field-level docs)
- **Business metrics**: `docs/business_metrics.md` (GMV, AOV, cancel_rate, late_delivery_rate)
- **Semantic layer metadata**: `dbt/models/exposures.yml` + marts model `meta` (owner/SLA)
- **Phase 2 evidence**: `docs/phase2_evidence.md` (commands, run results, and quality gates)
- **Phase 2.2 technical benchmark**: `docs/phase2_2_technical_benchmark.md` (formal benchmark method, results, and decision)
- **Phase 2.2 closure plan**: `docs/cv_phase2_plan_upgrade.md` (delivery audit, pending items, and exit criteria)
- **dbt docs (local)**: run `dbt docs generate` and `dbt docs serve` inside `dbt/`

---

## Dataset and license

- **Dataset**: Brazilian E-Commerce Public Dataset by Olist
- **Source**: Kaggle (`olistbr/brazilian-ecommerce`)
- **License**: **CC BY-NC-SA 4.0 (Non-Commercial)**
  Do not use this dataset for commercial purposes. See the Kaggle dataset page for details.

---

## Contributing

This is a portfolio project. If you want to suggest improvements, open an issue.

---

## Project license

MIT - see `LICENSE`.
