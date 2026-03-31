# Phase 2 Evidence - Core + 2.2 Closure Progress

**Date:** 2026-03-30  
**Environment:** Windows 11 + Python 3.12 (`.venv`) + dbt-core 1.8.7 + dbt-duckdb 1.8.2  
**Warehouse:** `data/warehouse/ecommerce.duckdb`

## Commands Executed

```bash
.\.venv\Scripts\python.exe scripts/download_dataset.py
.\.venv\Scripts\python.exe scripts/ingest_raw.py
.\.venv\Scripts\pytest.exe -q

.\.venv\Scripts\dbt.exe debug --project-dir ./dbt --profiles-dir ./dbt
.\.venv\Scripts\dbt.exe parse --project-dir ./dbt --profiles-dir ./dbt
.\.venv\Scripts\dbt.exe build --project-dir ./dbt --profiles-dir ./dbt

.\.venv\Scripts\dbt.exe test --project-dir ./dbt --profiles-dir ./dbt --select path:tests/test_reconcile_fact_orders_count.sql
.\.venv\Scripts\dbt.exe test --project-dir ./dbt --profiles-dir ./dbt --select path:tests/test_reconcile_fact_order_items_count.sql
.\.venv\Scripts\dbt.exe test --project-dir ./dbt --profiles-dir ./dbt --select path:tests/test_reconcile_fact_order_items_sums.sql
.\.venv\Scripts\dbt.exe test --project-dir ./dbt --profiles-dir ./dbt --select path:tests/test_reconcile_mart_kpis_daily_order_counts.sql
.\.venv\Scripts\dbt.exe test --project-dir ./dbt --profiles-dir ./dbt --select path:tests/test_reconcile_mart_kpis_daily_gmv.sql

.\.venv\Scripts\dbt.exe docs generate --project-dir ./dbt --profiles-dir ./dbt

python scripts/benchmark_dbt_build.py --dbt-executable .venv/Scripts/dbt.exe --project-dir dbt --profiles-dir dbt --runs-per-scenario 5 --phase2-selector "mart_kpis_daily+" --clean-artifacts --warehouse-reuse-policy reuse --environment-name local
```

## Results

### Dataset + RAW ingestion

- `download_dataset.py`: all 9 dataset files available.
- `ingest_raw.py`: pass.
- RAW load summary:
  - 9 tables ingested in `raw` schema
  - total rows: `1,551,698`

### Pytest (Phase 1 + ingestion validation)

- Final summary: `6 passed in 0.26s`
- Status: pass

### dbt debug

- Status: pass
- Result: `All checks passed`

### dbt parse (configuration + contracts hygiene)

- Status: pass
- Result:
  - Parse completed successfully.
  - No deprecated schema-test syntax blocker observed for `data_tests`.

### dbt build (full project)

- Final summary: `PASS=327 WARN=0 ERROR=0 SKIP=0 TOTAL=327`
- Includes:
  - Sources + staging + intermediate + marts + exposures
  - Facts: `fact_orders`, `fact_order_items`, `fact_payments`
  - KPI mart: `mart_kpis_daily`
  - Reconciliation tests for facts and KPI mart
- Status: pass

### Reconciliation tests (targeted run)

- `test_reconcile_fact_orders_count`: pass (`PASS=1`)
- `test_reconcile_fact_order_items_count`: pass (`PASS=1`)
- `test_reconcile_fact_order_items_sums`: pass (`PASS=1`)
- `test_reconcile_mart_kpis_daily_order_counts`: pass (`PASS=1`)
- `test_reconcile_mart_kpis_daily_gmv`: pass (`PASS=1`)

### dbt docs generate

- Status: pass
- Artifact:
  - `dbt/target/catalog.json` generated successfully (2026-03-30)

## Technical Benchmark Evidence (Phase 2.2)

- Benchmark note:
  - `docs/phase2_2_technical_benchmark.md`
- Evidence artifacts:
  - `artifacts/benchmarks/phase2_2_benchmark_results.json`
  - `artifacts/benchmarks/phase2_2_benchmark_results.csv`

Latest benchmark execution:

- Benchmark ID: `phase2_2_20260330T183852Z`
- Status: `completed`
- Runs: `40` (`4 scenarios * 2 selectors * 5 repetitions`)
- Failed runs: `0`
- Decision supported by data:
  - Recommended runtime setup for Phase 2.2: `marts=table`, `threads=4`

## Traceability for Phase 2.2

- KPI formulas and business definitions: `docs/business_metrics.md`
- KPI model logic: `dbt/models/marts/kpis/mart_kpis_daily.sql`
- KPI model contracts/tests: `dbt/models/marts/kpis/_mart_kpis_daily.yml`
- KPI reconciliation tests:
  - `dbt/tests/test_reconcile_mart_kpis_daily_order_counts.sql`
  - `dbt/tests/test_reconcile_mart_kpis_daily_gmv.sql`
- Payments fact contract: `dbt/models/marts/facts/_fact_payments.yml`
- Semantic layer exposures:
  - `dbt/models/exposures.yml` (`ecommerce_kpis_api`, `ecommerce_daily_dashboard`)
- Ownership/SLA metadata (`meta`) on critical models:
  - `dbt/models/marts/facts/_fact_orders.yml`
  - `dbt/models/marts/facts/_fact_order_items.yml`
  - `dbt/models/marts/facts/_fact_payments.yml`
  - `dbt/models/marts/kpis/_mart_kpis_daily.yml`
- Contract hardening migration (`tests` -> `data_tests`) validated in model/source YAML files under:
  - `dbt/models/staging/`
  - `dbt/models/intermediate/`
  - `dbt/models/marts/`

## CI Evidence Snapshot for Draft PR (Phase 2.2)

Captured on: `2026-03-31T19:33:42Z` (UTC)

- Repository: `Flames4fun/dataops-ecommerce-platform`
- Pull Request: `#9` (draft)
- Branch: `phase2-2-semantic-layer`
- Workflow: `ci` (`.github/workflows/ci.yml`)
- Run URL: `https://github.com/Flames4fun/dataops-ecommerce-platform/actions/runs/23815457040`
- Run ID: `23815457040`
- Job ID: `69413631700` (`validate`)
- Commit SHA: `58e42dadda71d3a20806e69944b8628d870c6ab1`
- Event: `pull_request`
- Run created at: `2026-03-31T19:26:05Z`
- Run updated at: `2026-03-31T19:27:03Z`
- Workflow result: `success`

Step-level quality gate results:

- `Run pytest`: `success` (`2026-03-31T19:26:42Z` -> `2026-03-31T19:26:42Z`)
- `Run dbt build`: `success` (`2026-03-31T19:26:45Z` -> `2026-03-31T19:27:00Z`)

Machine-readable evidence artifact:

- `artifacts/ci/phase2_2_ci_evidence.json`

Note:
- This section is a versioned evidence snapshot tied to the listed SHA/run.
- The most recent post-push SHA evidence is tracked in PR conversation comments to avoid "latest SHA" drift after new commits.

## Pending for Final Closure

1. Keep PR in draft or switch to ready-for-review, depending on release decision for final closure.
2. Prepare final PR checklist:
   - change summary
   - evidence links
   - rollback/risk notes
