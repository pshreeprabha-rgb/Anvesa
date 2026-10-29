from src.scheduler.cost import calculate_cost
from src.scheduler.feasibility import filter_feasible_nodes
from src.scheduler.risk import calculate_task_risk


def decide(nodes, task, reliability_estimates, risk_limit,
           lambda_value, performance_weights):
    feasible_nodes = filter_feasible_nodes(nodes, task)

    if not feasible_nodes:
        return {
            "status": "NO_FEASIBLE_NODE",
            "selected_node": None,
            "ranked_candidates": [],
        }

    candidates = []

    for node in feasible_nodes:
        risk = calculate_task_risk(node, task, reliability_estimates)
        performance = calculate_cost(node, performance_weights)

        candidates.append({
            "name": node["name"],
            "performance_cost": performance,
            "decision_risk": risk,
            "lambda": lambda_value,
            "objective": performance + lambda_value * risk,
        })

    eligible = [
        c for c in candidates
        if c["decision_risk"] <= risk_limit
    ]

    if eligible:
        ranked = sorted(
            eligible,
            key=lambda c: (c["objective"], c["name"]),
        )
        status = "RISK_LIMIT_MET"
    else:
        ranked = sorted(
            candidates,
            key=lambda c: (c["decision_risk"], c["objective"], c["name"]),
        )
        status = "RISK_LIMIT_UNMET"

    return {
        "status": status,
        "selected_node": ranked[0]["name"],
        "ranked_candidates": ranked,
    }
