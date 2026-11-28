
from src.common.schemas import (
    Task,
    ResourceReport,
    ReliabilityEstimate,
    PlacementDecision,
    RankedCandidate,
)


class ReliabilityAwareScheduler:
    """Ranks edge nodes using performance cost and reliability risk."""

    def select_node(
        self,
        task: Task,
        reports: list[ResourceReport],
        estimates: list[ReliabilityEstimate],
        current_time: float,
        lambda_param: float = 2.0,
    ) -> PlacementDecision:

        estimate_map = {e.node_id: e for e in estimates}
        candidates = []

        req = task.requirements
        weights = task.weights

        for report in reports:
            resources = report.resources
            estimate = estimate_map.get(report.node_id)

            cpu = float(resources.cpu_pct)
            ram = float(resources.ram_pct)
            bandwidth = float(resources.bandwidth_mbps)
            latency = float(resources.latency_ms)

            projected_cpu = cpu + req.cpu_pct
            projected_ram = ram + req.ram_pct

            feasible = (
                projected_cpu <= 100
                and projected_ram <= 100
                and bandwidth >= req.min_bandwidth_mbps
                and latency <= req.max_latency_ms
            )

            # Normalize performance costs.
            cpu_cost = min(projected_cpu / 100.0, 1.0)
            ram_cost = min(projected_ram / 100.0, 1.0)
            bandwidth_cost = min(
                req.min_bandwidth_mbps / max(bandwidth, 0.001), 1.0
            )
            latency_cost = min(
                latency / max(req.max_latency_ms, 0.001), 1.0
            )

            performance_cost = (
                weights.cpu * cpu_cost
                + weights.ram * ram_cost
                + weights.bandwidth * bandwidth_cost
                + weights.latency * latency_cost
            )

            # Calculate reliability risk.
            risk = 0.0

            if estimate:
                for key, weight in [
                    ("cpu", weights.cpu),
                    ("ram", weights.ram),
                    ("bandwidth", weights.bandwidth),
                    ("latency", weights.latency),
                ]:
                    score = estimate.resources.get(key)

                    if score:
                        resource_risk = (
                            0.7 * (1.0 - score.reliability)
                            + 0.3 * score.uncertainty
                        )
                    else:
                        resource_risk = 1.0

                    risk += weight * resource_risk
            else:
                risk = 1.0

            # Penalize nodes that cannot satisfy task requirements.
            violation_penalty = 0.0 if feasible else 1.0

            objective = (
                performance_cost
                + lambda_param * risk
                + violation_penalty
            )

            candidates.append({
                "node_id": report.node_id,
                "performance_cost": performance_cost,
                "risk": risk,
                "objective": objective,
                "feasible": feasible,
            })

        if not candidates:
            raise ValueError("Scheduler received no resource reports.")

        candidates.sort(key=lambda item: item["objective"])
        selected = candidates[0]

        return PlacementDecision(
            task_id=task.task_id,
            selected_node=selected["node_id"],
            decision_timestamp=str(current_time),
            performance_cost=selected["performance_cost"],
            decision_risk=selected["risk"],
            lambda_param=lambda_param,
            objective=selected["objective"],
            ranked_candidates=[
                RankedCandidate(
                    node_id=item["node_id"],
                    objective=item["objective"],
                )
                for item in candidates
            ],
            reason_codes=(
                ["LOWEST_OBJECTIVE"]
                if selected["feasible"]
                else ["NO_FEASIBLE_NODE", "LOWEST_OBJECTIVE"]
            ),
        )
