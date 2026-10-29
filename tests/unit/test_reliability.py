from src.common.schemas import ResourceReport, ExecutionResult
from src.reliability.tracker import ReliabilityTracker

def test_cold_start_handling():
    """Ensure cold-start reports exhibit higher uncertainty due to sparse history."""
    tracker = ReliabilityTracker(history_window=5)
    report = ResourceReport(
        timestamp="2026-10-23T20:00:00Z",
        node_id="edge-01",
        sequence=1,
        resources={"cpu_pct": 50.0, "bandwidth_mbps": 100.0},
        reported_at="2026-10-23T20:00:00Z"
    )
    estimate = tracker.process_report(report, current_time="2026-10-23T20:00:00Z")
    
    assert estimate.node_id == "edge-01"
    assert estimate.resources["cpu_pct"].uncertainty >= 0.30
    assert 0.0 <= estimate.resources["cpu_pct"].reliability <= 1.0

def test_stale_report_degrades_scores():
    """Ensure an outdated report increases staleness and reduces reliability."""
    tracker = ReliabilityTracker(history_window=5)
    stale_report = ResourceReport(
        timestamp="2026-10-23T20:00:00Z",
        node_id="edge-02",
        sequence=1,
        resources={"bandwidth_mbps": 80.0},
        reported_at="2026-10-23T19:59:00Z"  # 60s old
    )
    estimate = tracker.process_report(stale_report, current_time="2026-10-23T20:00:00Z")
    
    assert estimate.signals["bandwidth_mbps"]["staleness"] == 1.0
    assert estimate.resources["bandwidth_mbps"].reliability <= 0.70

def test_execution_feedback_loop():
    """Ensure execution feedback updates prediction history and affects future estimates."""
    tracker = ReliabilityTracker(history_window=5)
    feedback = ExecutionResult(
        task_id="task-101",
        node_id="edge-01",
        success=False,
        actual={"cpu_pct": 95.0},
        predicted={"cpu_pct": 10.0}  # Significant prediction error
    )
    tracker.process_execution_feedback(feedback)

    report = ResourceReport(
        timestamp="2026-10-23T20:05:00Z",
        node_id="edge-01",
        sequence=2,
        resources={"cpu_pct": 10.0},
        reported_at="2026-10-23T20:05:00Z"
    )
    estimate = tracker.process_report(report, current_time="2026-10-23T20:05:00Z")

    assert estimate.signals["cpu_pct"]["history_error"] > 0.50
    assert estimate.resources["cpu_pct"].reliability < 0.80