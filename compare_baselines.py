
from performance_model import calculate_performance_cost

from demo_inputs import nodes, reliability_estimates, task
from vector_scheduler import (
    calculate_task_risk,
    filter_feasible_nodes,
    load_config,
    schedule_task,
)

# -----------------------------------------
# 1. PERFORMANCE-ONLY BASELINE
# -----------------------------------------

def performance_only_baseline(nodes, task, performance_weights):
    feasible_nodes = filter_feasible_nodes(nodes, task)

    if not feasible_nodes:
        return None

    ranked = sorted(
        feasible_nodes,
        key=lambda node: (
            calculate_performance_cost(node, performance_weights),
            node["name"]
        )
    )

    return ranked[0]["name"]


# -----------------------------------------
# 2. RUN BASELINE COMPARISON
# -----------------------------------------

def main():
    config = load_config()

    weights = config["performance_weights"]
    risk_limit = config["risk_limit"]
    lambda_value = config["lambda_value"]

    # Performance-only baseline
    baseline_choice = performance_only_baseline(
        nodes, task, weights
    )

    # Risk-aware Vector scheduler
    vector_result = schedule_task(
        nodes,
        task,
        reliability_estimates,
        risk_limit,
        lambda_value,
        weights
    )

    print("========== BASELINE COMPARISON ==========")
    print("Performance-only choice:", baseline_choice)
    print("Risk-aware Vector choice:", vector_result["selected_node"])
    print("Vector status:", vector_result["status"])

    # -------------------------------------
    # 3. RISK-LIMIT COMPARISON
    # -------------------------------------

    print("\n========== RISK-LIMIT COMPARISON ==========")

    for limit in [0.20, 0.10, 0.05]:
        result = schedule_task(
            nodes,
            task,
            reliability_estimates,
            limit,
            lambda_value,
            weights
        )

        print(
            f"Risk limit={limit:.2f} | "
            f"Selected={result['selected_node']} | "
            f"Status={result['status']}"
        )

    # -------------------------------------
    # 4. CANDIDATE DETAILS
    # -------------------------------------

    print("\n========== CANDIDATE DETAILS ==========")

    for node in filter_feasible_nodes(nodes, task):
        performance = calculate_performance_cost(node, weights)

        risk = calculate_task_risk(
            node, task, reliability_estimates
        )

        print(
            f"Node {node['name']} | "
            f"Performance cost: {performance:.4f} | "
            f"Risk: {risk:.4f}"
        )

    # -------------------------------------
    # 5. TRADE-OFF ANALYSIS
    # -------------------------------------

    node_a = next(
        node for node in nodes if node["name"] == "A"
    )

    node_b = next(
        node for node in nodes if node["name"] == "B"
    )

    cost_a = calculate_performance_cost(node_a, weights)
    cost_b = calculate_performance_cost(node_b, weights)

    risk_a = calculate_task_risk(
        node_a, task, reliability_estimates
    )

    risk_b = calculate_task_risk(
        node_b, task, reliability_estimates
    )

    print("\n========== TRADE-OFF ANALYSIS ==========")

    if risk_a > 0:
        risk_reduction = (risk_a - risk_b) / risk_a * 100
        print(f"Risk reduction by choosing B: {risk_reduction:.2f}%")
    else:
        print("Risk reduction: undefined because Node A risk is zero")

    if cost_a > 0:
        cost_increase = (cost_b - cost_a) / cost_a * 100
        print(f"Performance-cost increase: {cost_increase:.2f}%")
    else:
        print("Performance-cost increase: undefined because Node A cost is zero")


# -----------------------------------------
# 6. ENTRY POINT
# -----------------------------------------

if __name__ == "__main__":
    main()
