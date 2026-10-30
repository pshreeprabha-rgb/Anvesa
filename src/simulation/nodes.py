import random
from typing import Any


def generate_nodes(count: int, rng: random.Random) -> list[dict[str, Any]]:
    """Create `count` edge nodes with seeded ground-truth state.

    cpu_pct and ram_pct are utilization (how busy the node is), matching
    the convention in docs/contracts/resource_naming.md.
    """
    nodes = []
    for i in range(count):
        cpu = rng.uniform(5.0, 40.0)
        ram = rng.uniform(5.0, 40.0)
        bandwidth = rng.uniform(50.0, 200.0)
        latency = rng.uniform(5.0, 40.0)
        queue = rng.randint(0, 3)
        nodes.append(
            {
                "id": f"edge-{i:02d}",
                "true_state": {
                    "cpu_pct": cpu,
                    "ram_pct": ram,
                    "bandwidth_mbps": bandwidth,
                    "latency_ms": latency,
                    "queue_length": queue,
                },
            }
        )
    return nodes