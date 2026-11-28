
import random
from typing import Any


def create_nodes(
    count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """Create reproducible edge nodes with simulated ground-truth resources."""

    if count <= 0:
        raise ValueError("Node count must be greater than zero.")

    nodes = []

    for i in range(count):
        node = {
            "id": f"edge-{i:02d}",
            "true_state": {
                "cpu_pct": round(rng.uniform(10.0, 40.0), 2),
                "ram_pct": round(rng.uniform(15.0, 50.0), 2),
                "bandwidth_mbps": round(rng.uniform(50.0, 200.0), 2),
                "latency_ms": round(rng.uniform(10.0, 50.0), 2),
                "queue_length": rng.randint(0, 3),
            },
        }

        nodes.append(node)

    return nodes
