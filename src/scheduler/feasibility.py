import math


def filter_feasible_nodes(nodes, task):
    required_cpu = task["required_cpu_pct"]
    required_ram = task["required_ram_pct"]
    min_bandwidth = task["min_bandwidth_mbps"]
    max_latency = task["max_latency_ms"]

    if not math.isfinite(required_cpu) or not 0 <= required_cpu <= 100:
        raise ValueError("CPU requirement must be between 0 and 100")

    if not math.isfinite(required_ram) or not 0 <= required_ram <= 100:
        raise ValueError("RAM requirement must be between 0 and 100")

    if not min_bandwidth >= 0:
        raise ValueError("Minimum bandwidth must be non-negative")

    if not max_latency >= 0:
        raise ValueError("Maximum latency must be non-negative")

    return [
        node for node in nodes
        if node["cpu_pct"] >= required_cpu
        and node["ram_pct"] >= required_ram
        and node["bandwidth_mbps"] >= min_bandwidth
        and node["latency_ms"] <= max_latency
    ]