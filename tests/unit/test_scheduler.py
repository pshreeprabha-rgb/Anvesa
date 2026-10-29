import pytest

from demo_inputs import nodes, reliability_estimates, task
from src.scheduler.feasibility import filter_feasible_nodes
from src.scheduler.risk import calculate_task_risk
from src.scheduler.scheduler import decide


def test_feasibility_filters_nodes():
    feasible = filter_feasible_nodes(nodes, task)
    assert [node["name"] for node in feasible] == ["A", "B"]


def test_feasibility_returns_empty_when_none_match():
    impossible_task = {**task, "min_bandwidth_mbps": 1000}
    assert filter_feasible_nodes(nodes, impossible_task) == []

def test_task_risk_uses_task_weights():
    risk = calculate_task_risk(nodes[0], task, reliability_estimates)
    expected = (
        0.15 * 0.05
        + 0.15 * 0.05
        + 0.50 * 0.30
        + 0.20 * 0.10
    )
    assert risk == pytest.approx(expected)


def test_missing_reliability_estimate_raises_error():
    with pytest.raises(ValueError, match="Missing reliability estimates"):
        calculate_task_risk(nodes[0], task, {})


def test_scheduler_returns_a_feasible_selected_node():
    decision = decide(
        nodes,
        task,
        reliability_estimates,
        risk_limit=1.0,
        lambda_value=2.0,
        performance_weights={"cpu": 1.0, "ram": 1.0, "latency": 1.0, "queue": 1.0, "bandwidth": 1.0},
    )
    assert decision["selected_node"] in {"A", "B"}
    assert decision["status"] == "RISK_LIMIT_MET"


def test_scheduler_reports_no_feasible_node():
    impossible_task = {**task, "min_bandwidth_mbps": 1000}
    decision = decide(
        nodes,
        impossible_task,
        reliability_estimates,
        risk_limit=1.0,
        lambda_value=2.0,
        performance_weights={"cpu": 1.0, "ram": 1.0, "latency": 1.0, "queue": 1.0, "bandwidth": 1.0},
    )
    assert decision["status"] == "NO_FEASIBLE_NODE"
    assert decision["selected_node"] is None


def test_scheduler_does_not_mutate_reliability_estimates():
    import copy

    estimates_before = copy.deepcopy(reliability_estimates)
    decide(
        nodes,
        task,
        reliability_estimates,
        risk_limit=1.0,
        lambda_value=2.0,
        performance_weights={"cpu": 1.0, "ram": 1.0, "latency": 1.0, "queue": 1.0, "bandwidth": 1.0},
    )
    assert reliability_estimates == estimates_before

