from typing import Any, Dict, List
import numpy as np
import pandas as pd


def compute_experiment_metrics(
    execution_results: List[Dict[str, Any]]
) -> Dict[str, float]:
    """Computes key performance indicators across all executed tasks:

    - Average Latency (ms)
    - Task Completion Rate (%)
    - Failure Rate (%)
    - Total Energy Consumption (J)
    - Mean Prediction Error (Latency)
    """
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
    completed_tasks = df["success"].sum()
    failed_tasks = total_tasks - completed_tasks

    completion_rate = (completed_tasks / total_tasks) * 100.0
    failure_rate = (failed_tasks / total_tasks) * 100.0

    actual_latencies = [
        res["actual"].get("latency_ms", 0.0) for res in execution_results
    ]
    actual_energies = [
        res["actual"].get("energy_j", 0.0) for res in execution_results
    ]

    avg_latency = float(np.mean(actual_latencies)) if actual_latencies else 0.0
    total_energy = float(np.sum(actual_energies)) if actual_energies else 0.0

    prediction_errors = [
        abs(
            res["actual"].get("latency_ms", 0.0)
            - res["predicted"].get("latency_ms", 0.0)
        )
        for res in execution_results
        if "latency_ms" in res.get("predicted", {})
    ]
    mean_prediction_error = (
        float(np.mean(prediction_errors)) if prediction_errors else 0.0
    )

    return {
        "total_tasks": total_tasks,
        "completion_rate": round(completion_rate, 2),
        "failure_rate": round(failure_rate, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "total_energy_j": round(total_energy, 2),
        "mean_prediction_error": round(mean_prediction_error, 2),
    }


def save_metrics_to_csv(metrics: Dict[str, float], output_path: str):
    """Saves calculated metrics to a CSV file."""
    df = pd.DataFrame([metrics])
    df.to_csv(output_path, index=False)
    print(f"[Member 4 Metrics] Metrics saved successfully to {output_path}")