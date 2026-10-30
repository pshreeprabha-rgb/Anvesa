import random

from src.common.schemas import ResourceReport
from src.simulation.timeutil import sim_time_to_iso


def generate_reports(
    nodes: list[dict],
    sequence: int,
    timestamp: float,
    rng: random.Random,
    unreliability_injector=None,
) -> list[ResourceReport]:
    """Emit ResourceReports visible to the scheduler; true state stays hidden."""
    reports = []
    for node in nodes:
        state = node["true_state"]
        raw = {
            "cpu_pct": state["cpu_pct"],
            "ram_pct": state["ram_pct"],
            "bandwidth_mbps": state["bandwidth_mbps"],
            "latency_ms": state["latency_ms"],
            "queue_length": state["queue_length"],
            "reported_at": timestamp,
        }
        if unreliability_injector:
            raw = unreliability_injector.apply(node["id"], raw, rng)
        # Convert last, so stale reports keep their older float time until here
        raw["reported_at"] = sim_time_to_iso(raw["reported_at"])
        reports.append(
            ResourceReport(
                node_id=str(node["id"]),
                sequence=sequence,
                timestamp=sim_time_to_iso(timestamp),
                resources=raw,
            )
        )
    return reports