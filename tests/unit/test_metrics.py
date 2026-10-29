import os
import tempfile

from src.evaluation.metrics import (
    compute_experiment_metrics,
    compute_utilization_metrics,
    save_metrics_to_csv,
    summarize_policy_run,
)


def test_compute_experiment_metrics_empty():
    res = compute_experiment_metrics([])
    assert res["total_tasks"] == 0
    assert res["completion_rate"] == 0.0


def test_compute_experiment_metrics_standard():
    mock_results = [
        {
            "task_id": "t1",
            "success": True,
            "actual": {"latency_ms": 100.0, "energy_j": 50.0},
            "predicted": {"latency_ms": 90.0},
        },
        {
            "task_id": "t2",
            "success": False,
            "actual": {"latency_ms": 200.0, "energy_j": 70.0},
            "predicted": {"latency_ms": 180.0},
        },
    ]
    res = compute_experiment_metrics(mock_results)
    assert res["total_tasks"] == 2.0
    assert res["completion_rate"] == 50.0
    assert res["failure_rate"] == 50.0
    assert res["avg_latency_ms"] == 150.0
    assert res["total_energy_j"] == 120.0
    assert res["mean_prediction_error"] == 15.0


def test_compute_utilization_metrics():
    node_utils = [
        {"cpu": 0.2, "ram": 0.4, "bandwidth": 0.1},
        {"cpu": 0.8, "ram": 0.6, "bandwidth": 0.3},
    ]
    utils = compute_utilization_metrics(node_utils)
    assert utils["mean_cpu"] == 0.5
    assert utils["peak_cpu"] == 0.8
    assert utils["mean_ram"] == 0.5
    assert utils["peak_ram"] == 0.6


def test_summarize_policy_run():
    mock_results = [
        {
            "task_id": "t1",
            "success": True,
            "actual": {"latency_ms": 50.0, "energy_j": 20.0},
            "predicted": {"latency_ms": 50.0},
        }
    ]
    summary = summarize_policy_run("arrro", mock_results)
    assert summary["policy"] == "arrro"
    assert summary["completion_rate"] == 100.0
    assert "mean_cpu" in summary


def test_save_metrics_to_csv():
    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = os.path.join(tmp_dir, "test_metrics.csv")
        sample_metrics = {"total_tasks": 1, "completion_rate": 100.0}
        save_metrics_to_csv(sample_metrics, csv_path)
        assert os.path.exists(csv_path)
