def calculate_task_risk(node, task, reliability_estimates):
    node_name = node["name"]

    if node_name not in reliability_estimates:
        raise ValueError(
            f"Missing reliability estimates for node '{node_name}'"
        )

    estimates = reliability_estimates[node_name]
    weights = task["weights"]

    required_resources = {
        "cpu": "cpu",
        "ram": "ram",
        "bandwidth": "bandwidth",
        "latency": "latency",
    }

    risk = 0.0
    for resource, estimate_key in required_resources.items():
        weight = weights[resource]
        uncertainty = estimates[estimate_key]["uncertainty"]

        if not 0 <= uncertainty <= 1:
            raise ValueError(
                f"{resource} uncertainty must be between 0 and 1"
            )
        if weight < 0:
            raise ValueError(f"{resource} weight cannot be negative")

        risk += weight * uncertainty

    return risk
