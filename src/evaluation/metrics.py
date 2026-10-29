"""Evaluation metrics calculation module for ARRRO.

Computes latency, task completion, failure rates, energy consumption,
prediction error, and node resource utilization.
"""

from __future__ import annotations

import os
from typing import Any

import numpy as np
import pandas as pd


def compute_experiment_metrics(
    execution_results: list[dict[str, Any]],
) -> dict[str, float]:
    """Compute key performance indicators across all executed tasks."""
    if not execution_results:
        return {
            "total_tasks": 0,
            "completion_rate": 0.0,
            "failure_rate": 0.0,
            "avg_latency_ms": 0.0,
            "total_energy_j": 0.0,
            "mean_prediction_error": 0.0,
        }

    df = pd.DataFrame(execution_results)
    total_tasks = len(df)
    completed_tasks = int(df["success"].sum()) if "success" in df else 0
    failed_tasks = total_tasks - completed_tasks

    completion_rate = (completed_tasks / total_tasks) * 100.0
    failure_rate = (failed_tasks / total_tasks) * 100.0

    actual_latencies = [
        res.get("actual", {}).get("latency_ms", 0.0) for res in execution_results
    ]
    actual_energies = [
        res.get("actual", {}).get("energy_j", 0.0) for res in execution_results
    ]

    avg_latency = float(np.mean(actual_latencies)) if actual_latencies else 0.0
    total_energy = float(np.sum(actual_energies)) if actual_energies else 0.0

    prediction_errors = [
        abs(
            res.get("actual", {}).get("latency_ms", 0.0)
            - res.get("predicted", {}).get("latency_ms", 0.0)
        )
        for res in execution_results
        if "predicted" in res and "latency_ms" in res["predicted"]
    ]
    mean_prediction_error = (
        float(np.mean(prediction_errors)) if prediction_errors else 0.0
    )

    return {
        "total_tasks": float(total_tasks),
        "completion_rate": round(completion_rate, 2),
        "failure_rate": round(failure_rate, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "total_energy_j": round(total_energy, 2),
        "mean_prediction_error": round(mean_prediction_error, 2),
    }


def compute_utilization_metrics(
    node_utilizations: list[dict[str, float]],
) -> dict[str, float]:
    """Calculate mean and peak utilization across all reporting nodes."""
    if not node_utilizations:
        return {
            "mean_cpu": 0.0,
            "peak_cpu": 0.0,
            "mean_ram": 0.0,
            "peak_ram": 0.0,
            "mean_bandwidth": 0.0,
            "peak_bandwidth": 0.0,
        }

    df_util = pd.DataFrame(node_utilizations)
    metrics: dict[str, float] = {}

    for resource in ["cpu", "ram", "bandwidth"]:
        if resource in df_util.columns:
            metrics[f"mean_{resource}"] = round(float(df_util[resource].mean()), 4)
            metrics[f"peak_{resource}"] = round(float(df_util[resource].max()), 4)
        else:
            metrics[f"mean_{resource}"] = 0.0
            metrics[f"peak_{resource}"] = 0.0

    return metrics


def summarize_policy_run(
    policy_name: str,
    execution_results: list[dict[str, Any]],
    node_utilizations: list[dict[str, float]] | None = None,
) -> dict[str, Any]:
    """Aggregate task execution KPIs and node utilization for a policy run."""
    base_metrics = compute_experiment_metrics(execution_results)
    utilization_metrics = compute_utilization_metrics(node_utilizations or [])

    summary: dict[str, Any] = {"policy": policy_name}
    summary.update(base_metrics)
    summary.update(utilization_metrics)
    return summary


def save_metrics_to_csv(
    metrics: dict[str, Any] | list[dict[str, Any]],
    output_path: str,
) -> None:
    """Save calculated metrics to a CSV file."""
    records = metrics if isinstance(metrics, list) else [metrics]
    df = pd.DataFrame(records)
    parent_dir = os.path.dirname(output_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[Member 4 Metrics] Metrics saved successfully to {output_path}")