"""ARRRO Main Experiment Runner.

Pipeline flow: Simulation -> Reliability -> Scheduler -> Execution -> Evaluation
"""

from __future__ import annotations

import argparse
import os
import random
from typing import Any

import yaml

from src.common.schemas import (
    ExecutionResult,
    PlacementDecision,
    RankedCandidate,
    ReliabilityEstimate,
    ResourceReport,
)
from src.evaluation.metrics import save_metrics_to_csv, summarize_policy_run
from src.reliability.tracker import ReliabilityTracker


def load_config(config_path: str) -> dict[str, Any]:
    """Load experiment configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_contracts() -> None:
    """Ensure shared contract models are importable and constructible."""
    assert ResourceReport is not None
    assert ReliabilityEstimate is not None
    assert PlacementDecision is not None
    assert ExecutionResult is not None


def generate_node_report(
    node_id: str,
    sequence: int,
    timestamp: str,
    unreliability: float = 0.0,
) -> ResourceReport:
    """Simulate a periodic node heartbeat report compliant with canonical schemas."""
    # Under high unreliability, inject degraded signals and high utilization
    is_faulty = random.random() < unreliability
    cpu_val = random.uniform(70.0, 95.0) if is_faulty else random.uniform(15.0, 60.0)
    ram_val = random.uniform(65.0, 90.0) if is_faulty else random.uniform(20.0, 55.0)
    lat_val = random.uniform(40.0, 100.0) if is_faulty else random.uniform(5.0, 25.0)

    return ResourceReport(
        timestamp=timestamp,
        node_id=node_id,
        sequence=sequence,
        resources={
            "cpu_pct": cpu_val,
            "ram_pct": ram_val,
            "bandwidth_mbps": random.uniform(30.0, 100.0),
            "latency_ms": lat_val,
            "queue_length": random.randint(3, 8) if is_faulty else random.randint(0, 2),
            "reported_at": timestamp,
        },
    )

def compute_node_score(estimate: ReliabilityEstimate) -> float:
    """Extract an aggregate reliability score from the estimate's resources dictionary."""
    if not estimate.resources:
        return 0.5
    scores: list[float] = []
    for val in estimate.resources.values():
        if hasattr(val, "score"):
            scores.append(float(val.score))
        elif isinstance(val, (int, float)):
            scores.append(float(val))
        elif isinstance(val, dict) and "score" in val:
            scores.append(float(val["score"]))
    return sum(scores) / len(scores) if scores else 0.5

def select_target_node(
    policy: str,
    task_id: str,
    node_ids: list[str],
    estimates: dict[str, ReliabilityEstimate],
    step: int,
    lambda_param: float = 2.0,
    timestamp: str = "2026-10-30T00:00:00Z",
) -> PlacementDecision:
    """Select target node based on evaluation policy and build PlacementDecision."""
    if policy == "round_robin":
        selected = node_ids[step % len(node_ids)]
    elif policy == "greedy":
        selected = node_ids[0]
    elif policy == "random":
        selected = random.choice(node_ids)
    else:
        # ARRRO policy: pick node with highest aggregate reliability score
        if estimates:
            selected = max(
                estimates.keys(),
                key=lambda n: compute_node_score(estimates[n]),
            )
        else:
            selected = node_ids[0]

    chosen_score = (
        compute_node_score(estimates[selected])
        if (estimates and selected in estimates)
        else 0.8
    )
    risk_val = round(1.0 - chosen_score, 3)
    cost_val = round(random.uniform(10.0, 30.0), 2)
    obj_val = round(cost_val + (lambda_param * risk_val), 2)

    # Build typed ranked candidates satisfying Member 3's schema
    candidates = [
        RankedCandidate(
            node_id=nid,
            objective=obj_val if nid == selected else round(obj_val * 1.15, 2),
        )
        for nid in node_ids
    ]

    decision_data = {
        "task_id": task_id,
        "selected_node": selected,
        "decision_timestamp": timestamp,
        "policy": policy,
        "performance_cost": cost_val,
        "decision_risk": risk_val,
        "lambda": lambda_param,
        "objective": obj_val,
        "ranked_candidates": candidates,
        "reason_codes": [f"POLICY_{policy.upper()}"],
    }

    return PlacementDecision(**decision_data)

def run_single_policy(
    policy_name: str,
    config: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Execute simulation and evaluation for a specific policy."""
    sim_cfg = config.get("simulation", {})
    node_count = sim_cfg.get("node_count", 10)
    task_count = sim_cfg.get("task_count", 50)
    unreliability = sim_cfg.get("unreliability_level", 0.10)
    lambda_val = config.get("scheduler", {}).get("lambda_param", 2.0)

    node_ids = [f"node-{i+1:02d}" for i in range(node_count)]
    tracker = ReliabilityTracker(history_window=5)

    execution_results: list[dict[str, Any]] = []
    node_utilizations: list[dict[str, float]] = []

    for task_idx in range(task_count):
        curr_time = f"2026-10-30T00:{task_idx % 60:02d}:00Z"

        # 1. Simulation -> Generate reports and update reliability tracker
        latest_estimates: dict[str, ReliabilityEstimate] = {}
        for nid in node_ids:
            report = generate_node_report(
                nid,
                sequence=task_idx + 1,
                timestamp=curr_time,
                unreliability=unreliability,
            )
            est = tracker.process_report(report, current_time_str=curr_time)
            latest_estimates[nid] = est

        # 2. Scheduler -> Placement decision
        task_id = f"task-{task_idx + 1:04d}"
        decision = select_target_node(
            policy_name,
            task_id,
            node_ids,
            latest_estimates,
            task_idx,
            lambda_param=lambda_val,
            timestamp=curr_time,
        )

        # 3. Execution -> Outcome simulation
        chosen_est = latest_estimates.get(decision.selected_node)
        reliability = compute_node_score(chosen_est) if chosen_est else 0.5

        is_success = random.random() < reliability
        base_latency = (
            random.uniform(10.0, 35.0) if is_success else random.uniform(50.0, 120.0)
        )
        predicted_lat = base_latency * random.uniform(0.95, 1.05)
        energy_j = base_latency * 1.2

        result_dict = {
            "task_id": task_id,
            "node_id": decision.selected_node,
            "success": is_success,
            "actual": {"latency_ms": base_latency, "energy_j": energy_j},
            "predicted": {"latency_ms": predicted_lat},
        }
        execution_results.append(result_dict)

        # 4. Feedback -> Track execution feedback
        feedback = ExecutionResult(
            task_id=task_id,
            node_id=decision.selected_node,
            success=is_success,
            started_at=curr_time,
            completed_at=curr_time,
            actual={"latency_ms": base_latency},
            predicted={"latency_ms": predicted_lat},
        )
        tracker.record_feedback(feedback)

        # 5. Monitor -> Sample node utilization
        node_utilizations.append(
            {
                "cpu": random.uniform(0.2, 0.75),
                "ram": random.uniform(0.25, 0.65),
                "bandwidth": random.uniform(0.1, 0.5),
            }
        )

    # 6. Evaluation -> Compute policy summary metrics
    summary = summarize_policy_run(policy_name, execution_results, node_utilizations)
    return summary, execution_results


def run_experiment(config_path: str) -> None:
    """Main entrypoint orchestrating policy runs and saving results."""
    validate_contracts()
    config = load_config(config_path)

    exp_id = config.get("experiment_id", "smoke_experiment")
    seed = config.get("seed", 42)
    random.seed(seed)

    sim_cfg = config.get("simulation", {})
    output_cfg = config.get("output", {})
    results_dir = output_cfg.get("results_dir", "data/sample")
    os.makedirs(results_dir, exist_ok=True)

    print(f"[Member 4 Pipeline] Starting experiment: {exp_id}")
    print(
        f"[Member 4 Pipeline] Seed: {seed}, Nodes: {sim_cfg.get('node_count')}, "
        f"Tasks: {sim_cfg.get('task_count')}, Unreliability: {sim_cfg.get('unreliability_level')}"
    )

    policies = ["arrro", "round_robin", "greedy", "random"]
    all_summaries: list[dict[str, Any]] = []

    for pol in policies:
        print(f" -> Running policy simulation: '{pol}'...")
        summary, _ = run_single_policy(pol, config)
        all_summaries.append(summary)

    if output_cfg.get("save_csv", True):
        csv_path = os.path.join(results_dir, f"{exp_id}_metrics.csv")
        save_metrics_to_csv(all_summaries, csv_path)
        print(
            f"[Member 4 Pipeline] Successfully exported evaluation metrics to: {csv_path}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ARRRO Experiment Runner")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/experiments/smoke.yaml",
        help="Path to experiment config YAML",
    )
    args = parser.parse_args()

    run_experiment(args.config)

