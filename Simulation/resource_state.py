
from dataclasses import dataclass, asdict


@dataclass
class ResourceState:
    cpu: float
    ram: float
    bandwidth: float
    latency: float
    queue_length: int


def capture_ground_truth(node):
    """Capture the node's actual resources as an independent snapshot."""
    return asdict(node.state)

