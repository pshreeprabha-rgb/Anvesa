
from demo_inputs import nodes, reliability_estimates, task
from performance_model import calculate_performance_cost
from vector_scheduler import (
    calculate_task_risk,
    filter_feasible_nodes,
    load_config,
    schedule_task,
)


def run_scenario(scenario_name, scenario_nodes, scenario_task,
                 scenario_reliability, config):

    feasible = filter_feasible_nodes(scenario_nodes, scenario_task)

    result = schedule_task(
        scenario_nodes,
        scenario_task,
        scenario_reliability,
        config["risk_limit"],
        config["lambda_value"],
        config["performance_weights"]
    )

    print(f"\nScenario: {scenario_name}")
    print(f"Feasible nodes: {len(feasible)}")
    print(f"Selected node: {result['selected_node']}")
    print(f"Status: {result['status']}")

    if result["selected_node"] is not None:
        selected = next(
            node for node in feasible
            if node["name"] == result["selected_node"]
        )

        risk = calculate_task_risk(
            selected, scenario_task, scenario_reliability
        )

        cost = calculate_performance_cost(
            selected, config["performance_weights"]
        )

        print(f"Estimated risk: {risk:.4f}")
        print(f"Performance cost: {cost:.4f}")

    return result


def main():
    config = load_config()

    print("=" * 45)
    print("VECTOR MULTI-SCENARIO EXPERIMENT")
    print("=" * 45)

    # Scenario 1: Original conditions
    run_scenario(
        "Normal conditions",
        nodes,
        task,
        reliability_estimates,
        config
    )

    # Scenario 2: Tighter risk limit
    strict_config = config.copy()
    strict_config["risk_limit"] = 0.10

    run_scenario(
        "Strict risk limit",
        nodes,
        task,
        reliability_estimates,
        strict_config
    )

    # Scenario 3: Higher bandwidth requirement
    demanding_task = task.copy()
    demanding_task["min_bandwidth_mbps"] = 70

    run_scenario(
        "High bandwidth requirement",
        nodes,
        demanding_task,
        reliability_estimates,
        config
    )

    # Scenario 4: No node can satisfy the requirements
    impossible_task = task.copy()
    impossible_task["required_cpu_pct"] = 100
    impossible_task["min_bandwidth_mbps"] = 1000

    run_scenario(
        "No feasible node",
        nodes,
        impossible_task,
        reliability_estimates,
        config
    )


if __name__ == "__main__":
    main()
