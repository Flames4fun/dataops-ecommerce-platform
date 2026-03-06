# Phase 2 Evidence - dbt Build + Tests

**Date:** 2026-03-06  
**Environment:** Windows 11 + Python 3.12.10 + dbt-core 1.8.7 + dbt-duckdb adapter 1.8.2  
**Warehouse:** `data/warehouse/ecommerce.duckdb`

## Commands executed

```bash
dbt debug --project-dir ./dbt --profiles-dir ./dbt
dbt deps --project-dir ./dbt --profiles-dir ./dbt
dbt build --project-dir ./dbt --profiles-dir ./dbt
dbt test --project-dir ./dbt --profiles-dir ./dbt -s test_reconcile_fact_orders_count
dbt test --project-dir ./dbt --profiles-dir ./dbt -s test_reconcile_fact_order_items_count
dbt test --project-dir ./dbt --profiles-dir ./dbt -s test_reconcile_fact_order_items_sums
dbt docs generate --project-dir ./dbt --profiles-dir ./dbt
```

## Results

### dbt debug

- Status: `All checks passed`
- Connection target: `data/warehouse/ecommerce.duckdb`

### dbt build

- Final summary: `PASS=235 WARN=0 ERROR=0 SKIP=0 TOTAL=235`
- Duration: ~5.12s
- Warning observed (non-blocking):
  - Unused config paths in `dbt_project.yml`: `seeds.dataops_ecommerce`, `snapshots.dataops_ecommerce`

### Reconciliation tests

- `test_reconcile_fact_orders_count`: `PASS=1 WARN=0 ERROR=0 SKIP=0 TOTAL=1`
- `test_reconcile_fact_order_items_count`: `PASS=1 WARN=0 ERROR=0 SKIP=0 TOTAL=1`
- `test_reconcile_fact_order_items_sums`: `PASS=1 WARN=0 ERROR=0 SKIP=0 TOTAL=1`

### dbt docs

- `dbt docs generate`: successful
- Artifact path: `dbt/target/catalog.json` (and companion artifacts in `dbt/target/`, gitignored)
- `dbt docs serve`: not executed in this evidence run (interactive server command)

## Notes

- `dbt deps` was required before `dbt build` because package macros from `dbt_utils` are referenced by tests.
- Known data-quality gaps are modeled explicitly instead of silently dropped:
  - Missing product category mappings are flagged via `is_missing_category`.
  - Missing product dimensions are flagged via `is_missing_dimensions`.
  - Order-delivery anomalies are modeled with flags such as `is_late_delivery` and `is_missing_purchased_at`.
- Raw layer keeps source fidelity (minimal transformations), while quality and business logic are enforced in `staging`, `intermediate`, and `marts`.
