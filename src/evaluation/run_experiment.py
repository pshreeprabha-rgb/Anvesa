"""ARRRO experiment runner.

Pipeline per task: simulation reports -> reliability tracker -> scheduler
-> execution against ground truth -> feedback to the tracker. The runner only
wires the layers together; it contains no algorithm logic of its own.
"""

import argparse
import json
import os
import random
import subprocess
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import yaml

from src.common.schemas import ExecutionResult, ResourceReport, Task
from src.evaluation.metrics import summarize_policy_run
from src.reliability.tracker import ReliabilityTracker
from src.scheduler.scheduler import decide
from src.simulation.execution import ExecutionSimulator
from src.simulation.nodes import generate_nodes
from src.simulation.reports import generate_reports
from src.simulation.tasks import generate_task_stream
from src.simulation.timeutil import sim_time_to_iso
from src.simulation.unreliability import UnreliabilityInjector

# name -> (tracker options, whether the scheduler uses the risk term)
POLICIES: dict[str, dict[str, Any]] = {
    # Full ARRRO: reliability + uncertainty, feedback-updated, risk-aware.
    "arrro": {"tracker": {}, "risk": True},
    # Ablation: reliability is estimated but never corrected by feedback.
    "no_feedback": {"tracker": {"use_feedback": False}, "risk": True},
    # Ablation: reliability is tracked, but the scheduler ignores risk.
    "no_risk": {"tracker": {}, "risk": False},
    # Conventional baseline: trust reported values, minimize performance cost.
    "greedy": {"tracker": {"constant_reliability": True}, "risk": False},
}

METRIC_COLUMNS = [
    "completion_rate",
    "failure_rate",
    "not_scheduled",
    "avg_latency_ms",
    "total_energy_j",
    "mean_prediction_error",
]


def load_config(config_path: str) -> dict:
    """Load experiment configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path) as f:
        return yaml.safe_load(f)


def predict_outcome(report: ResourceReport, task: Task) -> dict[str, float]:
    """Predict a successful run from *reported* values only (no ground truth)."""
    r = report.resources
    req = task.requirements
    return {
        "latency_ms": r.latency_ms + r.queue_length * 5.0 + req.cpu_pct * 0.5,
        "cpu_pct": r.cpu_pct + req.cpu_pct * 0.4,
        "ram_pct": r.ram_pct + req.ram_pct * 0.3,
    }


def predict_rejection(report: ResourceReport) -> dict[str, float]:
    """What the report claimed, to compare with the state a rejection reveals."""
    r = report.resources
    return {
        "cpu_pct": r.cpu_pct,
        "ram_pct": r.ram_pct,
        "bandwidth_mbps": r.bandwidth_mbps,
    }


def run_policy(
    policy: str,
    node_count: int,
    task_count: int,
    unreliability: float,
    seed: int,
    lambda_value: float = 2.0,
    verbose: bool = False,
    load_decay_s: float = 1.0,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run one policy over one seeded scenario and return (task rows, summary)."""
    spec = POLICIES[policy]

    # Separate seeded streams so every policy sees identical nodes, tasks and
    # unreliable reports regardless of its own decisions.
    nodes = generate_nodes(node_count, random.Random(seed))
    tasks = generate_task_stream(task_count, random.Random(seed + 1))
    report_rng = random.Random(seed + 2)
    injector = UnreliabilityInjector(level=unreliability)

    tracker = ReliabilityTracker(**spec["tracker"])
    lam = lambda_value if spec["risk"] else 0.0
    sim = ExecutionSimulator()
    by_id = {n["id"]: n for n in nodes}

    rows: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    utilization: list[dict[str, float]] = []

    for i, task in enumerate(tasks):
        now = float(i + 1)  # one task per simulated second
        now_iso = sim_time_to_iso(now)
        reports = generate_reports(nodes, i + 1, now, report_rng, injector)
        estimates = [tracker.process_report(r, now_iso) for r in reports]
        report_by_id = {r.node_id: r for r in reports}

        row: dict[str, Any] = {
            "policy": policy,
            "seed": seed,
            "unreliability_level": unreliability,
            "task_id": task.task_id,
            "task_type": task.task_type,
        }

        try:
            decision = decide(
                task, reports, estimates, lambda_value=lam, decision_time=now_iso
            )
        except ValueError as exc:
            if "No feasible node" not in str(exc):
                raise
            row.update(
                node_id=None,
                success=False,
                failure_reason="NO_FEASIBLE_NODE",
                risk=None,
                predicted_latency_ms=None,
                actual_latency_ms=None,
            )
            rows.append(row)
            results.append(
                {"task_id": task.task_id, "node_id": None, "success": False}
            )
            for node in nodes:
                sim.decay_node_load(node, load_decay_s)
            if verbose:
                print(f"  {task.task_id} {task.task_type:<17} -> no feasible node")
            continue

        node = by_id[decision.selected_node]
        report = report_by_id[decision.selected_node]
        result: ExecutionResult = sim.execute_task(task, node, now)
        predicted = (
            predict_outcome(report, task)
            if result.success
            else predict_rejection(report)
        )
        result = result.model_copy(update={"predicted": predicted})
        tracker.process_execution_feedback(result)

        actual_latency = result.actual.get("latency_ms")
        row.update(
            node_id=decision.selected_node,
            success=result.success,
            failure_reason=result.failure_reason,
            risk=round(decision.decision_risk, 4),
            predicted_latency_ms=(
                round(predicted["latency_ms"], 2) if result.success else None
            ),
            actual_latency_ms=(
                round(actual_latency, 2) if actual_latency is not None else None
            ),
        )
        rows.append(row)
        results.append(
            {
                "task_id": task.task_id,
                "node_id": decision.selected_node,
                "success": result.success,
                "actual": result.actual if result.success else {},
                "predicted": predicted if result.success else {},
            }
        )

        if verbose:
            status = "ok" if result.success else f"FAILED ({result.failure_reason})"
            detail = (
                f"pred={predicted['latency_ms']:.0f}ms act={actual_latency:.0f}ms"
                if result.success
                else ""
            )
            print(
                f"  {task.task_id} {task.task_type:<17} -> "
                f"{decision.selected_node} risk={decision.decision_risk:.2f} "
                f"{detail} {status}"
            )

        for node in nodes:
            sim.decay_node_load(node, load_decay_s)
            ts = node["true_state"]
            utilization.append(
                {"cpu": ts["cpu_pct"] / 100.0, "ram": ts["ram_pct"] / 100.0}
            )

    summary = summarize_policy_run(policy, results, utilization)
    latencies = [r["actual_latency_ms"] for r in rows if r["success"]]
    # Average latency over completed tasks only; failed tasks have no latency.
    summary["avg_latency_ms"] = (
        round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    )
    summary["not_scheduled"] = sum(
        1 for r in rows if r["failure_reason"] == "NO_FEASIBLE_NODE"
    )
    summary["unreliability_level"] = unreliability
    summary["seed"] = seed
    return rows, summary


def git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def run_experiment(config_path: str, verbose: bool = False) -> pd.DataFrame:
    """Run every policy over every (unreliability level, seed) in the config."""
    config = load_config(config_path)
    sim_cfg = config["simulation"]
    sweep = config.get("sweep", {})
    levels = sweep.get("unreliability_levels", [sim_cfg["unreliability_level"]])
    seeds = sweep.get("seeds", [config.get("seed", 42)])
    policies = sweep.get("policies", list(POLICIES))
    lambda_value = config.get("scheduler", {}).get("lambda_param", 2.0)
    out_dir = config.get("output", {}).get("results_dir", "results/run")

    print(f"[ARRRO] Experiment {config.get('experiment_id')} (git {git_sha()})")
    print(
        f"[ARRRO] nodes={sim_cfg['node_count']} tasks={sim_cfg['task_count']} "
        f"levels={levels} seeds={seeds} policies={policies}"
    )

    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for level in levels:
        for seed in seeds:
            for policy in policies:
                show = verbose and policy == "arrro"
                if show:
                    print(f"[ARRRO] policy=arrro level={level} seed={seed}")
                rows, summary = run_policy(
                    policy,
                    sim_cfg["node_count"],
                    sim_cfg["task_count"],
                    level,
                    seed,
                    lambda_value,
                    verbose=show,
                    load_decay_s=sim_cfg.get("load_decay_s", 1.0),
                )
                all_rows.extend(rows)
                summaries.append(summary)

    runs = pd.DataFrame(summaries)
    keep = ["policy", "unreliability_level", *METRIC_COLUMNS]
    table = (
        runs[keep]
        .groupby(["policy", "unreliability_level"], as_index=False)
        .mean(numeric_only=True)
        .round(2)
        .sort_values(["unreliability_level", "policy"])
    )

    os.makedirs(out_dir, exist_ok=True)
    table.to_csv(os.path.join(out_dir, "summary.csv"), index=False)
    pd.DataFrame(all_rows).to_csv(os.path.join(out_dir, "tasks.csv"), index=False)
    with open(os.path.join(out_dir, "experiment.json"), "w") as f:
        json.dump(
            {
                "experiment_id": config.get("experiment_id"),
                "git_sha": git_sha(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "config": config,
            },
            f,
            indent=2,
        )

    print("\n[ARRRO] Results (mean over seeds)")
    print(table.to_string(index=False))
    print(f"\n[ARRRO] Wrote summary.csv, tasks.csv, experiment.json to {out_dir}")

    if len(levels) > 1:
        try:
            from src.evaluation.plots import generate_experiment_plots

            figures = os.path.join(out_dir, "figures")
            generate_experiment_plots(os.path.join(out_dir, "summary.csv"), figures)
            print(f"[ARRRO] Figures saved to {figures}")
        except ImportError:
            print("[ARRRO] matplotlib not installed; skipping figures")
    return table


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARRRO Experiment Runner")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/experiments/smoke.yaml",
        help="Path to experiment config YAML",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print one line per ARRRO decision"
    )
    args = parser.parse_args()
    run_experiment(args.config, verbose=args.verbose)