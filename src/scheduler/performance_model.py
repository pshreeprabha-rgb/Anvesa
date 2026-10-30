
def calculate_performance_cost(node, weights):
    latency_cost = weights["latency"] * node["latency_ms"]
    queue_cost = weights["queue"] * node["queue_length"]
    bandwidth_cost = (
        weights["bandwidth"] / max(node["bandwidth_mbps"], 1)
    )
    cpu_cost = weights["cpu"] * node["cpu_pct"] / 100
    ram_cost = weights["ram"] * node["ram_pct"] / 100

    return (
        latency_cost
        + queue_cost
        + bandwidth_cost
        + cpu_cost
        + ram_cost
    )
