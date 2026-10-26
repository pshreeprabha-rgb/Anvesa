
import json

from performance_model import calculate_performance_cost


# -----------------------------------------
# 1. LOAD CONFIGURATION
# -----------------------------------------

def load_config():
    with open("scheduler_config.json", "r", encoding="utf-8") as file:
        return json.load(file)


# -----------------------------------------
# 2. FEASIBILITY FILTER
# -----------------------------------------

def filter_feasible_nodes(nodes, task):
    required_cpu = task["required_cpu_pct"]
    required_ram = task["required_ram_pct"]
    min_bandwidth = task["min_bandwidth_mbps"]
    max_latency = task["max_latency_ms"]

    if required_cpu < 0 or required_cpu > 100:
        raise ValueError("CPU requirement must be between 0 and 100")

    if required_ram < 0 or required_ram > 100:
        raise ValueError("RAM requirement must be between 0 and 100")

    if min_bandwidth < 0:
        raise ValueError("Minimum bandwidth cannot be negative")

    if max_latency < 0:
        raise ValueError("Maximum latency cannot be negative")

    feasible = []

    for node in nodes:
        if (
            node["cpu_pct"] >= required_cpu
            and node["ram_pct"] >= required_ram
            and node["bandwidth_mbps"] >= min_bandwidth
            and node["latency_ms"] <= max_latency
        ):
            feasible.append(node)

    return feasible


# -----------------------------------------
# 3. TASK-SPECIFIC RISK CALCULATION
# -----------------------------------------

def calculate_task_risk(node, task, reliability_estimates):
    node_name = node["name"]

    if node_name not in reliability_estimates:
        raise ValueError(
            f"Missing reliability estimates for node '{node_name}'"
        )

    estimates = reliability_estimates[node_name]
    weights = task["weights"]

    risk = (
        weights["cpu"] * estimates["cpu"]["uncertainty"]
        + weights["ram"] * estimates["ram"]["uncertainty"]
        + weights["bandwidth"] * estimates["bandwidth"]["uncertainty"]
        + weights["latency"] * estimates["latency"]["uncertainty"]
    )

    return risk


# -----------------------------------------
# 4. TASK SCHEDULER
# -----------------------------------------

def schedule_task(
    nodes,
    task,
    reliability_estimates,
    risk_limit,
    lambda_value,
    performance_weights
):
    feasible_nodes = filter_feasible_nodes(nodes, task)

    if not feasible_nodes:
        return {
            "status": "NO_FEASIBLE_NODE",
            "selected_node": None,
            "ranked_candidates": []
        }

    candidates = []

    for node in feasible_nodes:
        risk = calculate_task_risk(
            node,
            task,
            reliability_estimates
        )

        performance = calculate_performance_cost(
            node,
            performance_weights
        )

        objective = performance + lambda_value * risk

        candidates.append({
            "name": node["name"],
            "performance_cost": performance,
            "decision_risk": risk,
            "lambda": lambda_value,
            "objective": objective
        })

    # Prefer candidates that satisfy the risk limit.
    eligible = [
        candidate
        for candidate in candidates
        if candidate["decision_risk"] <= risk_limit
    ]

    if eligible:
        ranked = sorted(
            eligible,
            key=lambda item: (
                item["objective"],
                item["name"]
            )
        )

        status = "RISK_LIMIT_MET"
        selected = ranked[0]

    else:
        # No feasible node meets the risk limit.
        # Choose the lowest-risk feasible node and report this honestly.
        ranked = sorted(
            candidates,
            key=lambda item: (
                item["decision_risk"],
                item["objective"],
                item["name"]
            )
        )

        status = "RISK_LIMIT_UNMET"
        selected = ranked[0]

    return {
        "status": status,
        "selected_node": selected["name"],
        "ranked_candidates": ranked
    }


# -----------------------------------------
# 5. DISPLAY RESULTS
# -----------------------------------------

def print_decision(decision):
    print("Risk status:", decision["status"])
    print("\nRanked candidates:")

    for candidate in decision["ranked_candidates"]:
        print(
            f"Node {candidate['name']} | "
            f"Performance: {candidate['performance_cost']:.4f} | "
            f"Risk: {candidate['decision_risk']:.4f} | "
            f"Objective: {candidate['objective']:.4f}"
        )

    print("\nSelected node:", decision["selected_node"])


# -----------------------------------------
# 6. MAIN PROGRAM AND EXPERIMENTS
# -----------------------------------------

if __name__ == "__main__":

    # Sample data for the current standalone demonstration.
    # Later, these can be replaced with Atlas and Sentinel outputs.
    from demo_inputs import (
        nodes,
        task,
        reliability_estimates
    )

    config = load_config()

    risk_limit = config["risk_limit"]
    lambda_value = config["lambda_value"]
    performance_weights = config["performance_weights"]

    print("========== VECTOR SCHEDULER ==========")

    decision = schedule_task(
        nodes,
        task,
        reliability_estimates,
        risk_limit,
        lambda_value,
        performance_weights
    )

    print_decision(decision)

    # -------------------------------------
    # RISK-LIMIT EXPERIMENT
    # -------------------------------------

    print("\n========== RISK-LIMIT EXPERIMENT ==========")

    for limit in [0.20, 0.10, 0.05]:
        result = schedule_task(
            nodes,
            task,
            reliability_estimates,
            limit,
            lambda_value,
            performance_weights
        )

        print(
            f"Limit={limit:.2f} | "
            f"Status={result['status']} | "
            f"Selected={result['selected_node']}"
        )

    # -------------------------------------
    # LAMBDA EXPERIMENT
    # -------------------------------------

    print("\n========== LAMBDA EXPERIMENT ==========")

    for lam in [0, 50, 100, 200]:
        result = schedule_task(
            nodes,
            task,
            reliability_estimates,
            risk_limit,
            lam,
            performance_weights
        )

        print(
            f"Lambda={lam} | "
            f"Selected={result['selected_node']}"
        )
