import copy

import pytest

from src.common.schemas import (
    ReliabilityEstimate,
    ResourceMetrics,
    ResourceReport,
    Task,
    TaskRequirements,
    TaskWeights,
)
from src.scheduler.feasibility import filter_feasible_nodes
from src.scheduler.risk import calculate_task_risk
from src.scheduler.scheduler import decide


def make_task(min_bandwidth=40):
    return Task(
        task_id="task-1",
        task_type="compute",
        arrival_time="2026-10-29T10:00:00Z",
        requirements=TaskRequirements(
            cpu_pct=20,
            ram_pct=15,
            min_bandwidth_mbps=min_bandwidth,
            max_latency_ms=30,
        ),
        weights=TaskWeights(
            cpu=0.15, ram=0.15, bandwidth=0.50, latency=0.20
        ),
    )


def make_report(node_id, cpu, ram, bandwidth, latency, queue):
    return ResourceReport(
        timestamp="2026-10-29T10:00:00Z",
        node_id=node_id,
        sequence=1,
        resources=ResourceMetrics(
            cpu_pct=cpu,
            ram_pct=ram,
            bandwidth_mbps=bandwidth,
            latency_ms=latency,
            queue_length=queue,
            reported_at="2026-10-29T10:00:00Z",
        ),
    )


def make_estimate(node_id, cpu, ram, bandwidth, latency):
    return ReliabilityEstimate(
        node_id=node_id,
        timestamp="2026-10-29T10:00:00Z",
        resources={
            "cpu": {"reliability": 1 - cpu, "uncertainty": cpu},
            "ram": {"reliability": 1 - ram, "uncertainty": ram},
            "bandwidth": {
                "reliability": 1 - bandwidth,
                "uncertainty": bandwidth,
            },
            "latency": {
                "reliability": 1 - latency,
                "uncertainty": latency,
            },
        },
    )


def sample_data():
    reports = [
        make_report("A", 80, 40, 80, 12, 3),
        make_report("B", 60, 30, 50, 20, 5),
        make_report("C", 40, 20, 30, 35, 8),
    ]
    estimates = [
        make_estimate("A", 0.05, 0.05, 0.30, 0.10),
        make_estimate("B", 0.10, 0.05, 0.05, 0.10),
        make_estimate("C", 0.10, 0.10, 0.20, 0.15),
    ]
    return reports, estimates


def test_feasibility_filters_nodes():
    reports, _ = sample_data()
    task = make_task()
    nodes = [
        {
            "name": r.node_id,
            "cpu_pct": r.resources.cpu_pct,
            "ram_pct": r.resources.ram_pct,
            "bandwidth_mbps": r.resources.bandwidth_mbps,
            "latency_ms": r.resources.latency_ms,
        }
        for r in reports
    ]
    feasible = filter_feasible_nodes(
        nodes,
        {
            "required_cpu_pct": task.requirements.cpu_pct,
            "required_ram_pct": task.requirements.ram_pct,
            "min_bandwidth_mbps": task.requirements.min_bandwidth_mbps,
            "max_latency_ms": task.requirements.max_latency_ms,
        },
    )
    assert [node["name"] for node in feasible] == ["A", "B"]


def test_task_risk_uses_task_weights():
    reports, estimates = sample_data()
    node = {
        "name": reports[0].node_id,
    }
    estimate_map = {
        estimate.node_id: {
            name: value.model_dump()
            for name, value in estimate.resources.items()
        }
        for estimate in estimates
    }
    risk = calculate_task_risk(
        node,
        {"weights": make_task().weights.model_dump()},
        estimate_map,
    )
    assert risk == pytest.approx(0.185)


def test_scheduler_returns_shared_placement_decision():
    reports, estimates = sample_data()
    decision = decide(make_task(), reports, estimates)
    assert decision.task_id == "task-1"
    assert decision.selected_node in {"A", "B"}
    assert decision.reason_codes == ["RISK_LIMIT_MET"]
    assert len(decision.ranked_candidates) == 2


def test_scheduler_reports_no_feasible_node():
    reports, estimates = sample_data()
    with pytest.raises(ValueError, match="No feasible node"):
        decide(make_task(min_bandwidth=1000), reports, estimates)


def test_scheduler_does_not_mutate_estimates():
    reports, estimates = sample_data()
    before = copy.deepcopy(estimates)
    decide(make_task(), reports, estimates)
    assert estimates == before


def test_missing_reliability_estimate_raises_error():
    reports, _ = sample_data()
    with pytest.raises(ValueError, match="Missing reliability estimates"):
        decide(make_task(), reports, [])


def test_scheduler_rejects_negative_risk_limit():
    reports, estimates = sample_data()
    with pytest.raises(ValueError, match="non-negative"):
        decide(make_task(), reports, estimates, risk_limit=-1)

