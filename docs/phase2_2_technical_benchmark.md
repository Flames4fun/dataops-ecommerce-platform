# Phase 2.2 Technical Benchmark (Formal Note)

Last updated: 2026-03-30  
Status: Completed (formal benchmark executed)

## 1) Goal

Answer the following question with reproducible evidence:

Whether materializing marts as `table` reduces end-to-end `dbt build` runtime for the Phase 2.2 analytical slice without changing model semantics or quality outcomes.

## 2) Scope

- Primary benchmark command scope: full project `dbt build`
- Secondary benchmark command scope: `dbt build --select mart_kpis_daily+`
- dbt project: `./dbt`
- Adapter/warehouse: DuckDB (`WAREHOUSE_PATH`)
- Note for isolated fresh-warehouse runs (`warehouse_reuse_policy=recreate`):
  - use `dbt build --select +mart_kpis_daily+` when upstream dependencies must be rebuilt from scratch in the same run

## 3) Fixed Variables

- Same dataset and raw snapshot for all scenarios.
- Same machine/environment per benchmark session.
- Same dbt and adapter versions per benchmark session.
- Same selector per compared scenario set.
- Same number of repeated runs per scenario.
- Same warehouse reuse policy during one benchmark session.

## 4) Variables Under Test

- Marts materialization mode (`view` vs `table`)
- Thread count (`1` vs `4`)

Scenarios:

- Baseline A: `view`, `threads=1`
- Variant B: `view`, `threads=4`
- Variant C: `table`, `threads=1`
- Optimized D: `table`, `threads=4`

## 5) Method

- Run each scenario exactly 5 times.
- Controlled repeated-run mode with artifact cleanup and fixed warehouse reuse policy:
  - clean dbt artifacts (`target/`, `logs/`) before every run
  - keep warehouse policy fixed and explicit (`reuse` or `recreate`) for the entire session
- Warehouse policy for current formal plan:
  - DuckDB file is reused across scenarios in one session (`warehouse_reuse_policy=reuse`)
  - no selective warehouse recreation between scenarios
  - `reuse` was kept fixed across all runs to preserve comparability within the benchmark session
- Capture:
  - wall-clock duration
  - `run_results.json` metadata (elapsed time, node timings, status counts, invocation id, args)
  - benchmark context: `clean_artifacts`, `warehouse_path`, `warehouse_reuse_policy`, `dbt_version`, `adapter`, `environment_name`
- Persist all outputs in:
  - `artifacts/benchmarks/phase2_2_benchmark_results.json`
  - `artifacts/benchmarks/phase2_2_benchmark_results.csv`
- Compute summary statistics:
  - by selector
  - by scenario
  - by scenario-selector pair
  - metrics: median, p95, min, max, average wall-clock seconds
  - median method: `statistics.median`
  - p95 method: linear interpolation on sorted values with position `(n-1)*0.95`

Executed benchmark context:

- Benchmark ID: `phase2_2_20260330T183852Z`
- Runs: `40` total (`4 scenarios * 2 selectors * 5 repetitions`)
- Failed runs: `0`
- dbt: `1.8.7`
- Adapter: `duckdb 1.8.2`
- Environment: `local`
- Quality parity: all runs completed successfully with no failed runs and consistent quality outcomes across scenarios

## 6) Results Table

| Scenario | Materialization | Threads | Selector | Runs | Median (s) | P95 (s) | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline A | view | 1 | full_project | 5 | 25.053387 | 25.136057 | Baseline |
| Variant B | view | 4 | full_project | 5 | 13.995131 | 14.008187 | Threads-only vs A |
| Variant C | table | 1 | full_project | 5 | 22.242003 | 22.288300 | Materialization-only vs A |
| Optimized D | table | 4 | full_project | 5 | 13.189889 | 13.252602 | Combined optimization |
| Baseline A | view | 1 | mart_kpis_daily+ | 5 | 8.093080 | 8.094327 | Baseline |
| Variant B | view | 4 | mart_kpis_daily+ | 5 | 6.971284 | 6.996710 | Threads-only vs A |
| Variant C | table | 1 | mart_kpis_daily+ | 5 | 7.253726 | 7.357564 | Materialization-only vs A |
| Optimized D | table | 4 | mart_kpis_daily+ | 5 | 6.732583 | 6.735523 | Combined optimization |

## 7) Interpretation

- Full project (`dbt build`):
  - Threads-only impact (`A` vs `B`): `44.14%` faster median.
  - Materialization-only impact (`A` vs `C`): `11.22%` faster median.
  - Combined impact (`A` vs `D`): `47.35%` faster median.
- Phase 2.2 slice (`mart_kpis_daily+`):
  - Threads-only impact (`A` vs `B`): `13.86%` faster median.
  - Materialization-only impact (`A` vs `C`): `10.37%` faster median.
  - Combined impact (`A` vs `D`): `16.81%` faster median.

Conclusion from data:

- In this repository and environment, thread parallelism is the strongest single contributor.
- Table materialization provides additional gains, especially in full-project builds.
- The best overall runtime is consistently `table + threads=4` (Scenario D).

## 8) Tradeoffs

- `table` materialization:
  - Pros: lower median runtime in benchmark and persistent marts for downstream consumers.
  - Cons: more write/persistence work than pure `view` workflows.
- Higher thread count (`4`):
  - Pros: strong runtime reduction in this environment.
  - Cons: may increase contention in constrained environments.
- Practical note:
  - If local resources are limited, `view + threads=4` is a viable fallback with competitive times.

## 9) Final Decision

- Recommended default for Phase 2.2:
  - marts materialization: `table`
  - threads: `4`
- Rationale:
  - Scenario D (`table + 4`) is the fastest in both selectors.
  - Improvement vs baseline A:
    - Full project: `47.35%` median reduction.
    - Phase 2.2 slice: `16.81%` median reduction.
  - No failed runs (`0/40`) under this setup.

## 10) Reproducibility

Reference script:

- `scripts/benchmark_dbt_build.py`

Executed command (default scope: full project + Phase 2.2 slice):

```bash
python scripts/benchmark_dbt_build.py --dbt-executable .venv/Scripts/dbt.exe --project-dir dbt --profiles-dir dbt --runs-per-scenario 5 --phase2-selector "mart_kpis_daily+" --clean-artifacts --warehouse-reuse-policy reuse --environment-name local
```

Example command (only full project):

```bash
python scripts/benchmark_dbt_build.py --dbt-executable .venv/Scripts/dbt.exe --project-dir dbt --profiles-dir dbt --runs-per-scenario 5 --only-full-project --clean-artifacts --warehouse-reuse-policy reuse --environment-name local
```

Example command (only Phase 2.2 slice):

```bash
python scripts/benchmark_dbt_build.py --dbt-executable .venv/Scripts/dbt.exe --project-dir dbt --profiles-dir dbt --runs-per-scenario 5 --only-phase2-slice --phase2-selector "mart_kpis_daily+" --clean-artifacts --warehouse-reuse-policy reuse --environment-name local
```

## 11) Evidence Artifacts

- JSON: `artifacts/benchmarks/phase2_2_benchmark_results.json`
- CSV: `artifacts/benchmarks/phase2_2_benchmark_results.csv`
