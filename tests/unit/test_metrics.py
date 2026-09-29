from src.evaluation.metrics import compute_experiment_metrics


def test_compute_experiment_metrics():
    mock_results = [
        {
            "task_id": "task-01",
            "node_id": "edge-01",
            "success": True,
            "actual": {"latency_ms": 20.0, "energy_j": 5.0},
            "predicted": {"latency_ms": 18.0},
        },
        {
            "task_id": "task-02",
            "node_id": "edge-02",
            "success": False,
            "actual": {"latency_ms": 50.0, "energy_j": 10.0},
            "predicted": {"latency_ms": 20.0},
        },
    ]

    metrics = compute_experiment_metrics(mock_results)

    assert metrics["total_tasks"] == 2
    assert metrics["completion_rate"] == 50.0
    assert metrics["failure_rate"] == 50.0
    assert metrics["avg_latency_ms"] == 35.0
    assert metrics["total_energy_j"] == 15.0
    assert metrics["mean_prediction_error"] == 16.0