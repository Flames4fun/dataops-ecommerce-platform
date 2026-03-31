#!/usr/bin/env python3
"""
Phase 2.2 benchmark runner for dbt build scenarios.

Purpose:
- Execute reproducible dbt benchmark runs with controlled scenarios.
- Persist structured benchmark evidence in JSON and CSV formats.

This script is intentionally generic and documentation-driven so it can be
audited before execution.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_WAREHOUSE_PATH = "data/warehouse/ecommerce.duckdb"


@dataclass(frozen=True)
class Scenario:
    name: str
    marts_materialization: str
    threads: int
    description: str


DEFAULT_SCENARIOS: List[Scenario] = [
    Scenario(
        name="baseline_a",
        marts_materialization="view",
        threads=1,
        description="Baseline A: marts as views, single thread.",
    ),
    Scenario(
        name="variant_b",
        marts_materialization="view",
        threads=4,
        description="Variant B: marts as views, 4 threads.",
    ),
    Scenario(
        name="variant_c",
        marts_materialization="table",
        threads=1,
        description="Variant C: marts as tables, single thread.",
    ),
    Scenario(
        name="optimized_d",
        marts_materialization="table",
        threads=4,
        description="Optimized D: marts as tables, 4 threads.",
    ),
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Phase 2.2 dbt technical benchmark scenarios."
    )
    parser.add_argument(
        "--dbt-executable",
        default="dbt",
        help="dbt executable path/name (e.g., dbt or .venv/Scripts/dbt.exe).",
    )
    parser.add_argument("--project-dir", default="dbt", help="dbt project directory.")
    parser.add_argument("--profiles-dir", default="dbt", help="dbt profiles directory.")
    parser.add_argument(
        "--output-dir",
        default="artifacts/benchmarks",
        help="Directory where JSON/CSV benchmark evidence will be saved.",
    )
    parser.add_argument(
        "--runs-per-scenario",
        type=int,
        default=3,
        help="Number of repeated runs per scenario/selector pair.",
    )
    parser.add_argument(
        "--phase2-selector",
        default="mart_kpis_daily+",
        help="Phase 2.2 selector for the secondary benchmark slice.",
    )
    parser.add_argument(
        "--only-full-project",
        action="store_true",
        help="Run only full-project benchmark (skip Phase 2.2 selector slice).",
    )
    parser.add_argument(
        "--only-phase2-slice",
        action="store_true",
        help="Run only Phase 2.2 selector slice (skip full-project benchmark).",
    )
    parser.add_argument(
        "--materialization-var",
        default="benchmark_marts_materialized",
        help="dbt var name used to override marts materialization for benchmarks.",
    )
    parser.add_argument(
        "--clean-artifacts",
        action="store_true",
        help="Remove dbt target/logs before each run for cold-ish conditions.",
    )
    parser.add_argument(
        "--warehouse-path",
        default="",
        help="Optional WAREHOUSE_PATH override for benchmark runs.",
    )
    parser.add_argument(
        "--warehouse-reuse-policy",
        default="reuse",
        choices=["reuse", "recreate"],
        help="Benchmark warehouse policy used during the session.",
    )
    parser.add_argument(
        "--environment-name",
        default="local",
        help="Logical environment label (e.g., local, ci, perf-lab).",
    )
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def clean_dbt_artifacts(project_dir: Path) -> None:
    for rel in ("target", "logs"):
        path = project_dir / rel
        if path.exists():
            shutil.rmtree(path)


def ensure_path_within_repo(path: Path, repo_root: Path) -> None:
    if not path.resolve().is_relative_to(repo_root.resolve()):
        raise ValueError(
            f"Unsafe warehouse path outside repository root. path={path} repo_root={repo_root}"
        )


def resolve_warehouse_path_for_runtime(warehouse_path_value: str, repo_root: Path) -> Path:
    path = Path(warehouse_path_value)
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    else:
        path = path.resolve()
    return path


def parse_run_results(run_results_path: Path) -> Dict[str, Any]:
    if not run_results_path.exists():
        return {
            "exists": False,
            "elapsed_time": None,
            "invocation_id": None,
            "status_counts": {},
            "results": [],
            "args": {},
        }

    payload = json.loads(run_results_path.read_text(encoding="utf-8"))
    results = payload.get("results", [])
    status_counts: Dict[str, int] = {}

    for node in results:
        node_status = str(node.get("status", "unknown"))
        status_counts[node_status] = status_counts.get(node_status, 0) + 1

    parsed_results = [
        {
            "unique_id": node.get("unique_id"),
            "status": node.get("status"),
            "execution_time": node.get("execution_time"),
            "thread_id": node.get("thread_id"),
            "timing": node.get("timing", []),
        }
        for node in results
    ]

    return {
        "exists": True,
        "elapsed_time": payload.get("elapsed_time"),
        "invocation_id": payload.get("metadata", {}).get("invocation_id"),
        "metadata": payload.get("metadata", {}),
        "status_counts": status_counts,
        "results": parsed_results,
        "args": payload.get("args", {}),
    }


def build_dbt_command(
    dbt_executable: str,
    project_dir: Path,
    profiles_dir: Path,
    scenario: Scenario,
    materialization_var_name: str,
    selector: Optional[str],
) -> List[str]:
    vars_payload = {materialization_var_name: scenario.marts_materialization}

    cmd = [
        dbt_executable,
        "build",
        "--project-dir",
        str(project_dir),
        "--profiles-dir",
        str(profiles_dir),
        "--threads",
        str(scenario.threads),
        "--vars",
        json.dumps(vars_payload),
    ]

    if selector:
        cmd.extend(["--select", selector])

    return cmd


def run_command(cmd: List[str], env: Dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def resolve_python_executable(dbt_executable: str) -> str:
    dbt_path = Path(dbt_executable)
    if dbt_path.exists():
        candidate = dbt_path.with_name("python.exe")
        if candidate.exists():
            return str(candidate)
    return sys.executable


def prepare_warehouse_for_run(
    policy: str,
    warehouse_file: Path,
    repo_root: Path,
    env: Dict[str, str],
    python_executable: str,
) -> Dict[str, Any]:
    if policy == "reuse":
        return {
            "policy_applied": "reuse",
            "warehouse_recreated": False,
            "ingestion_return_code": None,
            "ingestion_stdout_tail": "",
            "ingestion_stderr_tail": "",
        }

    if policy != "recreate":
        raise ValueError(f"Unsupported warehouse_reuse_policy: {policy}")

    ensure_path_within_repo(warehouse_file, repo_root)
    warehouse_file.parent.mkdir(parents=True, exist_ok=True)
    if warehouse_file.exists():
        warehouse_file.unlink()

    ingest_script = repo_root / "scripts" / "ingest_raw.py"
    if not ingest_script.exists():
        raise FileNotFoundError(f"Ingestion script not found: {ingest_script}")

    ingest_cmd = [python_executable, str(ingest_script)]
    ingest_process = run_command(ingest_cmd, env)
    if ingest_process.returncode != 0:
        raise RuntimeError(
            "Warehouse recreate policy failed while re-ingesting raw snapshot. "
            f"return_code={ingest_process.returncode} "
            f"stderr_tail={ingest_process.stderr[-500:]}"
        )

    return {
        "policy_applied": "recreate",
        "warehouse_recreated": True,
        "ingestion_return_code": ingest_process.returncode,
        "ingestion_stdout_tail": ingest_process.stdout[-2000:],
        "ingestion_stderr_tail": ingest_process.stderr[-2000:],
    }


def parse_dbt_version_output(stdout: str) -> Dict[str, str]:
    core_version = "unknown"
    adapter_name = "unknown"
    adapter_version = "unknown"

    core_match = re.search(r"(?mi)^\s*-\s*installed:\s*([^\s]+)", stdout)
    if core_match:
        core_version = core_match.group(1)

    plugins_section = ""
    if "Plugins:" in stdout:
        plugins_section = stdout.split("Plugins:", maxsplit=1)[1]
    plugin_match = re.search(r"(?mi)^\s*-\s*([a-zA-Z0-9_]+):\s*([^\s]+)", plugins_section)
    if plugin_match:
        adapter_name = plugin_match.group(1)
        adapter_version = plugin_match.group(2)

    return {
        "dbt_version": core_version,
        "adapter": adapter_name,
        "adapter_version": adapter_version,
    }


def detect_dbt_environment(dbt_executable: str, env: Dict[str, str]) -> Dict[str, str]:
    try:
        result = subprocess.run(
            [dbt_executable, "--version"],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return {
            "dbt_version": "unknown",
            "adapter": "unknown",
            "adapter_version": "unknown",
            "dbt_version_command_rc": None,
        }

    metadata = parse_dbt_version_output(result.stdout or "")
    metadata["dbt_version_command_rc"] = result.returncode
    return metadata


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fieldnames = [
        "benchmark_id",
        "timestamp_utc",
        "environment_name",
        "selector_name",
        "selector",
        "scenario",
        "materialization",
        "threads",
        "run_number",
        "wall_clock_seconds",
        "run_results_elapsed_seconds",
        "clean_artifacts",
        "warehouse_path",
        "warehouse_reuse_policy",
        "dbt_version",
        "adapter",
        "command",
        "process_return_code",
        "status_counts",
        "invocation_id",
    ]

    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def compute_timing_stats(values: List[float]) -> Dict[str, Any]:
    if not values:
        return {
            "runs": 0,
            "median_seconds": None,
            "p95_seconds": None,
            "min_seconds": None,
            "max_seconds": None,
            "avg_seconds": None,
        }

    ordered = sorted(values)
    size = len(ordered)
    median_value = statistics.median(ordered)
    p95_position = (size - 1) * 0.95
    p95_lower = math.floor(p95_position)
    p95_upper = math.ceil(p95_position)
    if p95_lower == p95_upper:
        p95_value = ordered[p95_lower]
    else:
        p95_fraction = p95_position - p95_lower
        p95_value = ordered[p95_lower] + (ordered[p95_upper] - ordered[p95_lower]) * p95_fraction
    avg_value = sum(ordered) / size

    return {
        "runs": size,
        "median_seconds": round(median_value, 6),
        "p95_seconds": round(p95_value, 6),
        "min_seconds": round(min(ordered), 6),
        "max_seconds": round(max(ordered), 6),
        "avg_seconds": round(avg_value, 6),
    }


def aggregate_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "total_runs": len(rows),
        "failed_runs": sum(1 for row in rows if int(row["process_return_code"]) != 0),
        "by_selector": {},
        "by_scenario": {},
        "by_scenario_selector": {},
    }

    by_selector: Dict[str, List[float]] = {}
    by_scenario: Dict[str, List[float]] = {}
    by_scenario_selector: Dict[str, List[float]] = {}
    for row in rows:
        timing = float(row["wall_clock_seconds"])
        selector_key = str(row["selector_name"])
        scenario_key = str(row["scenario"])
        scenario_selector_key = f"{scenario_key}::{selector_key}"

        by_selector.setdefault(selector_key, []).append(timing)
        by_scenario.setdefault(scenario_key, []).append(timing)
        by_scenario_selector.setdefault(scenario_selector_key, []).append(timing)

    for key, values in by_selector.items():
        summary["by_selector"][key] = compute_timing_stats(values)

    for key, values in by_scenario.items():
        summary["by_scenario"][key] = compute_timing_stats(values)

    for key, values in by_scenario_selector.items():
        summary["by_scenario_selector"][key] = compute_timing_stats(values)

    return summary


def main() -> int:
    args = parse_args()

    project_dir = Path(args.project_dir).resolve()
    profiles_dir = Path(args.profiles_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    ensure_dir(output_dir)

    if args.only_full_project and args.only_phase2_slice:
        raise ValueError("Choose only one of --only-full-project or --only-phase2-slice.")

    selectors: List[Dict[str, Optional[str]]] = []
    if not args.only_phase2_slice:
        selectors.append({"name": "full_project", "selector": None})
    if not args.only_full_project:
        selectors.append({"name": "phase2_2_slice", "selector": args.phase2_selector})

    benchmark_id = f"phase2_2_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    rows: List[Dict[str, Any]] = []
    detailed_runs: List[Dict[str, Any]] = []
    completion_notes: List[str] = []

    base_env = os.environ.copy()
    if args.warehouse_path:
        base_env["WAREHOUSE_PATH"] = args.warehouse_path

    warehouse_path_value = args.warehouse_path or base_env.get("WAREHOUSE_PATH", DEFAULT_WAREHOUSE_PATH)
    if "WAREHOUSE_PATH" not in base_env:
        base_env["WAREHOUSE_PATH"] = warehouse_path_value

    repo_root = project_dir.parent.resolve()
    warehouse_file = resolve_warehouse_path_for_runtime(warehouse_path_value, repo_root)
    ensure_path_within_repo(warehouse_file, repo_root)

    dbt_env_metadata = detect_dbt_environment(args.dbt_executable, base_env)
    python_executable = resolve_python_executable(args.dbt_executable)

    for selector_cfg in selectors:
        selector_name = selector_cfg["name"]
        selector_value = selector_cfg["selector"]

        for scenario in DEFAULT_SCENARIOS:
            for run_number in range(1, args.runs_per_scenario + 1):
                warehouse_run_metadata = prepare_warehouse_for_run(
                    policy=args.warehouse_reuse_policy,
                    warehouse_file=warehouse_file,
                    repo_root=repo_root,
                    env=base_env,
                    python_executable=python_executable,
                )

                if args.clean_artifacts:
                    clean_dbt_artifacts(project_dir)

                cmd = build_dbt_command(
                    dbt_executable=args.dbt_executable,
                    project_dir=project_dir,
                    profiles_dir=profiles_dir,
                    scenario=scenario,
                    materialization_var_name=args.materialization_var,
                    selector=selector_value,
                )

                started_at = utc_now_iso()
                wall_start = time.perf_counter()
                process = run_command(cmd=cmd, env=base_env)
                wall_end = time.perf_counter()
                wall_seconds = round(wall_end - wall_start, 6)

                run_results_path = project_dir / "target" / "run_results.json"
                parsed = parse_run_results(run_results_path)

                row = {
                    "benchmark_id": benchmark_id,
                    "timestamp_utc": started_at,
                    "environment_name": args.environment_name,
                    "selector_name": selector_name,
                    "selector": selector_value or "<full_project>",
                    "scenario": scenario.name,
                    "materialization": scenario.marts_materialization,
                    "threads": scenario.threads,
                    "run_number": run_number,
                    "wall_clock_seconds": wall_seconds,
                    "run_results_elapsed_seconds": parsed["elapsed_time"],
                    "clean_artifacts": bool(args.clean_artifacts),
                    "warehouse_path": warehouse_path_value,
                    "warehouse_reuse_policy": args.warehouse_reuse_policy,
                    "dbt_version": dbt_env_metadata["dbt_version"],
                    "adapter": dbt_env_metadata["adapter"],
                    "command": " ".join(cmd),
                    "process_return_code": process.returncode,
                    "status_counts": json.dumps(parsed["status_counts"], sort_keys=True),
                    "invocation_id": parsed["invocation_id"],
                }
                rows.append(row)

                detailed_runs.append(
                    {
                        **row,
                        "scenario_metadata": asdict(scenario),
                        "selector_metadata": selector_cfg,
                        "environment_metadata": {
                            "environment_name": args.environment_name,
                            "warehouse_path": warehouse_path_value,
                            "warehouse_reuse_policy": args.warehouse_reuse_policy,
                            "clean_artifacts": bool(args.clean_artifacts),
                            "dbt_version": dbt_env_metadata["dbt_version"],
                            "adapter": dbt_env_metadata["adapter"],
                            "adapter_version": dbt_env_metadata["adapter_version"],
                        },
                        "warehouse_run_metadata": warehouse_run_metadata,
                        "stdout_tail": process.stdout[-4000:],
                        "stderr_tail": process.stderr[-4000:],
                        "run_results": parsed,
                    }
                )

                if process.returncode != 0:
                    completion_notes.append(
                        f"Run failed: selector={selector_name}, scenario={scenario.name}, run={run_number}, return_code={process.returncode}"
                    )
                if not parsed["exists"]:
                    completion_notes.append(
                        f"run_results.json not found after selector={selector_name}, scenario={scenario.name}, run={run_number}"
                    )

    json_path = output_dir / "phase2_2_benchmark_results.json"
    csv_path = output_dir / "phase2_2_benchmark_results.csv"

    if not rows:
        final_status = "failed"
    elif any(int(row["process_return_code"]) != 0 for row in rows):
        final_status = "failed"
    elif any("run_results.json not found" in note for note in completion_notes):
        final_status = "completed_with_notes"
    else:
        final_status = "completed"

    payload = {
        "status": final_status,
        "completion_notes": completion_notes,
        "benchmark_id": benchmark_id,
        "generated_at_utc": utc_now_iso(),
        "project_dir": str(project_dir),
        "profiles_dir": str(profiles_dir),
        "dbt_executable": args.dbt_executable,
        "runs_per_scenario": args.runs_per_scenario,
        "clean_artifacts": bool(args.clean_artifacts),
        "environment_name": args.environment_name,
        "warehouse_path": warehouse_path_value,
        "warehouse_reuse_policy": args.warehouse_reuse_policy,
        "dbt_version": dbt_env_metadata["dbt_version"],
        "adapter": dbt_env_metadata["adapter"],
        "adapter_version": dbt_env_metadata["adapter_version"],
        "dbt_version_command_rc": dbt_env_metadata["dbt_version_command_rc"],
        "python_executable": python_executable,
        "materialization_var": args.materialization_var,
        "p95_method": "linear_interpolation_on_sorted_values_(position=(n-1)*0.95)",
        "selectors": selectors,
        "scenarios": [asdict(s) for s in DEFAULT_SCENARIOS],
        "summary": aggregate_summary(rows),
        "runs": detailed_runs,
    }

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(csv_path, rows)

    print(f"Benchmark evidence saved:")
    print(f"- JSON: {json_path}")
    print(f"- CSV:  {csv_path}")
    print(f"- Final status: {final_status}")

    if final_status == "failed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
