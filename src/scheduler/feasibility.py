from src.common.schemas import ResourceMetrics, TaskRequirements


def is_feasible(resources: ResourceMetrics, requirements: TaskRequirements) -> bool:
    """cpu_pct and ram_pct are utilization, so headroom = 100 - utilization."""
    return (
        100.0 - resources.cpu_pct >= requirements.cpu_pct
        and 100.0 - resources.ram_pct >= requirements.ram_pct
        and resources.bandwidth_mbps >= requirements.min_bandwidth_mbps
        and resources.latency_ms <= requirements.max_latency_ms
    )