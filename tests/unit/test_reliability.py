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
def test_all_four_signals_present_and_bounded():
    """Verify that every resource includes all 4 signals normalized within [0, 1]."""
    tracker = ReliabilityTracker(history_window=5)
    report = ResourceReport(
        timestamp="2026-10-23T20:00:00Z",
        node_id="edge-10",
        sequence=1,
        resources={
            "cpu_pct": 45.0,
            "ram_pct": 55.0,
            "bandwidth_mbps": 50.0,
            "latency_ms": 25.0,
            "queue_length": 3,
            "reported_at": "2026-10-23T20:00:00Z",
        },
    )
    est = tracker.process_report(report, current_time_str="2026-10-23T20:00:00Z")

    required_signals = [
        "staleness",
        "history_error",
        "temporal_instability",
        "cross_resource_inconsistency",
    ]

    for short_key, signals in est.signals.items():
        for sig in required_signals:
            assert sig in signals, f"Missing {sig} in {short_key}"
            assert 0.0 <= signals[sig] <= 1.0, f"{sig} out of range [0, 1] for {short_key}"


def test_asymmetric_recovery():
    """Verify reliability drops sharply after bad reports and recovers gradually."""
    tracker = ReliabilityTracker(history_window=5)

    def send_report(ts_rep, ts_curr, seq):
        rep = ResourceReport(
            timestamp=ts_rep,
            node_id="edge-recovery",
            sequence=seq,
            resources={
                "cpu_pct": 30.0,
                "ram_pct": 30.0,
                "bandwidth_mbps": 100.0,
                "latency_ms": 10.0,
                "queue_length": 1,
                "reported_at": ts_rep,
            },
        )
        return tracker.process_report(rep, current_time_str=ts_curr)

    # 1. Fresh report establishes good reliability
    est1 = send_report("2026-10-23T20:00:00Z", "2026-10-23T20:00:00Z", 1)
    good_rel = est1.resources["cpu"].reliability

    # 2. Severely stale report causes sharp drop
    est_bad = send_report("2026-10-23T19:50:00Z", "2026-10-23T20:00:00Z", 2)
    bad_rel = est_bad.resources["cpu"].reliability
    drop_delta = good_rel - bad_rel
    assert drop_delta > 0.15, "Reliability did not drop fast enough on degradation"

    # 3. Next fresh report recovers slowly (gradual recovery step)
    est_recovered = send_report("2026-10-23T20:01:00Z", "2026-10-23T20:01:00Z", 3)
    rec_rel = est_recovered.resources["cpu"].reliability
    recovery_delta = rec_rel - bad_rel
    assert recovery_delta <= 0.12, "Recovery jumped too fast instead of gradual increase"


def test_resource_specific_feedback():
    """Verify feedback specifically targets and degrades the failing resource."""
    tracker = ReliabilityTracker(history_window=5)

    # Feedback indicating severe bandwidth error
    fb = ExecutionResult(
        task_id="task-net",
        node_id="edge-res",
        success=False,
        started_at="2026-10-23T20:00:00Z",
        completed_at="2026-10-23T20:00:05Z",
        actual={"bandwidth_mbps": 5.0},
        predicted={"bandwidth_mbps": 100.0},
    )
    tracker.process_execution_feedback(fb)

    # Bandwidth error history populated, cpu error history clean
    assert len(tracker.error_history["edge-res"]["bandwidth"]) == 1
    assert len(tracker.error_history["edge-res"].get("cpu", [])) == 0


def test_ablation_flags():
    """Verify no-feedback and constant reliability modes operate as expected."""
    # 1. No feedback ablation
    tracker_no_fb = ReliabilityTracker(use_feedback=False)
    fb = ExecutionResult(
        task_id="task-ablation",
        node_id="edge-ablation",
        success=False,
        started_at="2026-10-23T20:00:00Z",
        completed_at="2026-10-23T20:00:05Z",
        actual={"cpu_pct": 90.0},
        predicted={"cpu_pct": 10.0},
    )
    tracker_no_fb.process_execution_feedback(fb)
    assert "edge-ablation" not in tracker_no_fb.error_history

    # 2. Constant reliability ablation
    tracker_const = ReliabilityTracker(constant_reliability=True)
    report = ResourceReport(
        timestamp="2026-10-23T20:00:00Z",
        node_id="edge-ablation",
        sequence=1,
        resources={
            "cpu_pct": 100.0,
            "ram_pct": 100.0,
            "bandwidth_mbps": 0.0,
            "latency_ms": 1000.0,
            "queue_length": 50,
            "reported_at": "2026-10-23T19:00:00Z",
        },
    )
    est = tracker_const.process_report(report)
    assert est.resources["cpu"].reliability == 0.8
    assert est.resources["cpu"].uncertainty == 0.2