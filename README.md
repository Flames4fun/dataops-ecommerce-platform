# DataOps E-commerce Platform

Production-like, end-to-end **Data Engineering** project: ingest → warehouse → transform → test → orchestrate → serve.

> Portfolio focus: reproducibility, data quality, schema-as-code, and deployable components.

---

## What this project demonstrates

- **Idempotent ingestion** into a local analytical warehouse
- **Warehouse-first modeling** with dbt (staging → marts)
- **Automated data quality** (pytest + dbt tests)
- **Orchestration-ready** workflows (Prefect flows)
- **API serving layer** for curated datasets (FastAPI)
- **Observability hooks** (structured logs + basic metrics)

---

## Architecture

**CSV dataset** → **Ingestion (Python)** → **DuckDB (`warehouse/ecommerce.duckdb`)** → **dbt models** → **FastAPI endpoints**

Quality gates:
- `pytest` (pipeline/unit checks)
- `dbt test` (schema + business rules)

Orchestration (planned):
- Prefect flows schedule ingestion + dbt

---

## Tech stack

| Layer | Technology | Why it’s here |
| --- | --- | --- |
| Language | Python 3.11+ | Pipelines, orchestration, API |
| Warehouse | DuckDB | Portable analytics warehouse |
| Transformations | dbt | SQL modeling + tests |
| Orchestration | Prefect | Scheduling + retries |
| API | FastAPI | Serve curated data products |
| Testing | pytest | Unit/integration checks |
| CI | GitHub Actions | Automated checks on PRs |

---

## Project status (roadmap)

| Phase | Status | Deliverable |
| --- | :---: | --- |
| 1 — Raw ingestion | ✅ | Download + ingest + validation tests |
| 2 — dbt transformations | 🚧 | Staging + marts + dbt tests |
| 3 — Orchestration | ⏳ | Prefect flows + schedules |
| 4 — API serving | ⏳ | FastAPI endpoints over marts |
| 5 — Observability | ⏳ | Logs + metrics + basic dashboards |

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
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### Run Phase 1 (download → ingest → validate)

```bash
# 1) Download dataset into data/raw/
python scripts/download_dataset.py

# 2) Ingest raw CSVs into DuckDB
python scripts/ingest_raw.py

# 3) Validate ingestion
pytest -q
```

Expected:
- `warehouse/ecommerce.duckdb` created
- 9 tables under the `raw` schema
- tests pass

---

## Query examples

### DuckDB CLI

```bash
duckdb warehouse/ecommerce.duckdb
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
├── api/                    # FastAPI app (Phase 4)
├── dbt/                    # dbt project (Phase 2)
├── docs/                   # Documentation (data dictionary, decisions)
├── pipelines/              # Prefect flows (Phase 3)
├── scripts/                # Download + ingestion + helpers
├── tests/                  # Unit/integration tests
├── data/                   # Local data (gitignored)
└── warehouse/              # DuckDB file (gitignored)
```

---

## Documentation

- **Data directory**: `data/README.md` (local layout + verification)
- **Data dictionary**: `docs/data_dictionary.md` (raw schema field-level docs)

---

## Dataset & license

- **Dataset**: Brazilian E-Commerce Public Dataset by Olist
- **Source**: Kaggle (`olistbr/brazilian-ecommerce`)
- **License**: **CC BY-NC-SA 4.0 (Non-Commercial)**  
  Do not use this dataset for commercial purposes. See the Kaggle dataset page for details.

---

## Contributing

This is a portfolio project. If you want to suggest improvements, open an issue.

---

## Project license

MIT — see `LICENSE`.
