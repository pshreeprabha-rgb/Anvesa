import random
from typing import List
from src.common.schemas import ResourceReport

def generate_reports(
    nodes: List[dict],
    sequence: int,
    timestamp: float,
    rng: random.Random,
    unreliability_injector=None
) -> List[ResourceReport]:
    """
    Emits ResourceReports visible to the scheduler.
    Leaves true node state intact and isolated for the evaluator.
    """
    reports = []
    for node in nodes:
        # Base report built from internal true values
        raw_resources = {
            "cpu_pct": node["true_state"]["cpu_pct"],
            "ram_pct": node["true_state"]["ram_pct"],
            "bandwidth_mbps": node["true_state"]["bandwidth_mbps"],
            "latency_ms": node["true_state"]["latency_ms"],
            "queue_length": node["true_state"]["queue_length"],
            "reported_at": timestamp,
        }

        # Apply noise/stale/manipulation if an injector is active
        if unreliability_injector:
            raw_resources = unreliability_injector.apply(node["id"], raw_resources, rng)

        report = ResourceReport(
            node_id=str(node["id"]),  # e.g., "edge-01"
            sequence=sequence,
            timestamp=timestamp,
            resources=raw_resources,
        )
        reports.append(report)

    return reports
