"""Unit tests for the Reliability Tracker."""

from src.common.schemas import ExecutionResult, ResourceReport
from src.reliability.tracker import ReliabilityTracker


def test_cold_start_handling():
    """Ensure cold-start reports exhibit higher uncertainty due to sparse history."""
    tracker = ReliabilityTracker(history_window=5)
    report = ResourceReport(
        timestamp="2026-10-23T20:00:00Z",
        node_id="edge-01",
        sequence=1,
        resources={
            "cpu_pct": 50.0,
            "ram_pct": 40.0,
            "bandwidth_mbps": 100.0,
            "latency_ms": 15.0,
            "queue_length": 2,
            "reported_at": "2026-10-23T20:00:00Z",
        },
    )

    estimate = tracker.process_report(report, current_time_str="2026-10-23T20:00:00Z")
    assert estimate.node_id == "edge-01"
    assert "cpu" in estimate.resources
    # With only 1 report in a window of 5, uncertainty should remain elevated
    assert estimate.resources["cpu"].uncertainty >= 0.5


def test_stale_report_degrades_scores():
    """Ensure an outdated report increases staleness and reduces reliability."""
    tracker = ReliabilityTracker(history_window=5)
    fresh_report = ResourceReport(
        timestamp="2026-10-23T20:00:00Z",
        node_id="edge-02",
        sequence=1,
        resources={
            "cpu_pct": 20.0,
            "ram_pct": 30.0,
            "bandwidth_mbps": 80.0,
            "latency_ms": 10.0,
            "queue_length": 1,
            "reported_at": "2026-10-23T20:00:00Z",
        },
    )
    fresh_est = tracker.process_report(
        fresh_report, current_time_str="2026-10-23T20:00:00Z"
    )

    stale_report = ResourceReport(
        timestamp="2026-10-23T20:01:00Z",
        node_id="edge-02",
        sequence=2,
        resources={
            "cpu_pct": 20.0,
            "ram_pct": 30.0,
            "bandwidth_mbps": 80.0,
            "latency_ms": 10.0,
            "queue_length": 1,
            "reported_at": "2026-10-23T19:59:00Z",  # 2 minutes old
        },
    )
    stale_est = tracker.process_report(
        stale_report, current_time_str="2026-10-23T20:01:00Z"
    )

    def mean_reliability(est):
        return sum(r.reliability for r in est.resources.values()) / len(est.resources)

    assert mean_reliability(stale_est) < mean_reliability(fresh_est)


def test_execution_feedback_loop():
    """Ensure execution feedback updates prediction history and affects future estimates."""
    tracker = ReliabilityTracker(history_window=5)
    feedback = ExecutionResult(
        task_id="task-101",
        node_id="edge-01",
        success=False,
        started_at="2026-10-23T20:00:00Z",
        completed_at="2026-10-23T20:00:05Z",
        actual={"cpu_pct": 95.0},
        predicted={"cpu_pct": 10.0},
    )
    tracker.record_feedback(feedback)
    assert len(tracker.error_history["edge-01"]["cpu_pct"]) == 1
