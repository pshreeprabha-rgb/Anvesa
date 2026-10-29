from datetime import UTC, datetime

from src.common.schemas import (
    PlacementDecision,
    RankedCandidate,
    ReliabilityEstimate,
    ResourceReport,
    Task,
)
from src.scheduler.cost import calculate_cost
from src.scheduler.risk import calculate_task_risk


def decide(
    task: Task,
    reports: list[ResourceReport],
    estimates: list[ReliabilityEstimate],
    risk_limit: float = 1.0,
    lambda_value: float = 2.0,
    performance_weights: dict[str, float] | None = None,
) -> PlacementDecision:
    if risk_limit < 0 or lambda_value < 0:
        raise ValueError("Risk limit and lambda must be non-negative")

    if performance_weights is None:
        performance_weights = {
            "cpu": 1.0,
            "ram": 1.0,
            "latency": 1.0,
            "queue": 1.0,
            "bandwidth": 1.0,
        }

    estimate_by_node = {estimate.node_id: estimate for estimate in estimates}
    requirements = task.requirements
    weights = task.weights.model_dump()

    candidates = []
    for report in reports:
        resources = report.resources

        if (
            resources.cpu_pct < requirements.cpu_pct
            or resources.ram_pct < requirements.ram_pct
            or resources.bandwidth_mbps < requirements.min_bandwidth_mbps
            or resources.latency_ms > requirements.max_latency_ms
        ):
            continue

        estimate = estimate_by_node.get(report.node_id)
        if estimate is None:
            raise ValueError(
                f"Missing reliability estimates for node '{report.node_id}'"
            )

        node = {
            "name": report.node_id,
            "cpu_pct": resources.cpu_pct,
            "ram_pct": resources.ram_pct,
            "bandwidth_mbps": resources.bandwidth_mbps,
            "latency_ms": resources.latency_ms,
            "queue_length": resources.queue_length,
        }

        reliability_data = {
            report.node_id: {
                name: value.model_dump()
                for name, value in estimate.resources.items()
            }
        }

        risk = calculate_task_risk(
            node,
            {"weights": weights},
            reliability_data,
        )
        performance = calculate_cost(node, performance_weights)

        candidates.append({
            "node_id": report.node_id,
            "performance_cost": performance,
            "decision_risk": risk,
            "objective": performance + lambda_value * risk,
        })

    if not candidates:
        raise ValueError("No feasible node is available for this task")

    eligible = [
        candidate for candidate in candidates
        if candidate["decision_risk"] <= risk_limit
    ]

    if eligible:
        ranked = sorted(
            eligible,
            key=lambda candidate: (
                candidate["objective"], candidate["node_id"]
            ),
        )
        reason_codes = ["RISK_LIMIT_MET"]
    else:
        ranked = sorted(
            candidates,
            key=lambda candidate: (
                candidate["decision_risk"],
                candidate["objective"],
                candidate["node_id"],
            ),
        )
        reason_codes = ["RISK_LIMIT_UNMET"]

    selected = ranked[0]

    return PlacementDecision(
        task_id=task.task_id,
        selected_node=selected["node_id"],
        decision_timestamp=datetime.now(UTC).isoformat(),
        performance_cost=selected["performance_cost"],
        decision_risk=selected["decision_risk"],
        **{"lambda": lambda_value},
        objective=selected["objective"],
        ranked_candidates=[
            RankedCandidate(
                node_id=candidate["node_id"],
                objective=candidate["objective"],
            )
            for candidate in ranked
        ],
        reason_codes=reason_codes,
    )
