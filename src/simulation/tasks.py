import random
from typing import Dict, List
from src.common.schemas import Task

# Task profiles mapping requirements and risk weights
TASK_PROFILES = {
    "compute-heavy": {
        "requirements": {"cpu_pct": (60, 95), "ram_pct": (20, 50), "min_bandwidth_mbps": (5, 20), "max_latency_ms": (150, 400)},
        "weights": {"cpu": 0.6, "ram": 0.2, "bandwidth": 0.1, "latency": 0.1},
    },
    "memory-heavy": {
        "requirements": {"cpu_pct": (20, 50), "ram_pct": (65, 95), "min_bandwidth_mbps": (10, 30), "max_latency_ms": (150, 400)},
        "weights": {"cpu": 0.2, "ram": 0.6, "bandwidth": 0.1, "latency": 0.1},
    },
    "bandwidth-heavy": {
        "requirements": {"cpu_pct": (10, 40), "ram_pct": (20, 40), "min_bandwidth_mbps": (80, 200), "max_latency_ms": (100, 300)},
        "weights": {"cpu": 0.1, "ram": 0.1, "bandwidth": 0.6, "latency": 0.2},
    },
    "latency-sensitive": {
        "requirements": {"cpu_pct": (15, 45), "ram_pct": (10, 30), "min_bandwidth_mbps": (20, 60), "max_latency_ms": (20, 80)},
        "weights": {"cpu": 0.1, "ram": 0.1, "bandwidth": 0.2, "latency": 0.6},
    },
    "mixed": {
        "requirements": {"cpu_pct": (30, 60), "ram_pct": (30, 60), "min_bandwidth_mbps": (30, 70), "max_latency_ms": (80, 200)},
        "weights": {"cpu": 0.25, "ram": 0.25, "bandwidth": 0.25, "latency": 0.25},
    },
}

def generate_task_stream(
    count: int,
    rng: random.Random,
    proportions: Dict[str, float] = None
) -> List[Task]:
    """Generates a seeded stream of Task objects adhering to canonical schemas."""
    if proportions is None:
        proportions = {k: 0.2 for k in TASK_PROFILES}

    task_types = list(proportions.keys())
    weights = list(proportions.values())

    tasks = []
    current_time = 0.0

    for i in range(count):
        t_type = rng.choices(task_types, weights=weights, k=1)[0]
        profile = TASK_PROFILES[t_type]
        reqs = profile["requirements"]

        current_time += rng.uniform(0.1, 1.0)

        task = Task(
            task_id=f"task-{i:04d}",
            task_type=t_type,                       # Added: required by schema
            arrival_time=f"{current_time:.4f}",       # Fixed: converted float to string
            requirements={
                "cpu_pct": rng.uniform(*reqs["cpu_pct"]),
                "ram_pct": rng.uniform(*reqs["ram_pct"]),
                "min_bandwidth_mbps": rng.uniform(*reqs["min_bandwidth_mbps"]),
                "max_latency_ms": rng.uniform(*reqs["max_latency_ms"]),
            },
            weights=profile["weights"],
        )
        tasks.append(task)

    return tasks