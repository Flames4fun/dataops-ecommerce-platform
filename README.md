# DataOps E-commerce Platform

Production-like data platform for e-commerce: ingestion ? storage ? transformations (dbt) ? data quality ? orchestration (Prefect) ? API (FastAPI) ? observability [file:1].

## Goal

Demonstrate end-to-end Data Engineering skills on e-commerce data (customers, orders, payments, shipments, products) [file:1].

## Repository structure (high level)

- data/: local data (raw, DuckDB warehouse)
- dbt/: models, tests, sources, docs
- pipelines/: Prefect flows and jobs
- api/: FastAPI service
- scripts/: utilities (bootstrap, validation, helpers)
- tests/: unit and light integration tests
- docs/: documentation, data dictionary, metrics definitions [file:1].
