# demo_inputs.py
# Illustrative inputs for local testing.
# These are NOT real measurements from an edge network.

nodes = [
    {
        "name": "A",
        "cpu_pct": 80,
        "ram_pct": 40,
        "bandwidth_mbps": 80,
        "latency_ms": 12,
        "queue_length": 3
    },
    {
        "name": "B",
        "cpu_pct": 60,
        "ram_pct": 30,
        "bandwidth_mbps": 50,
        "latency_ms": 20,
        "queue_length": 5
    },
    {
        "name": "C",
        "cpu_pct": 40,
        "ram_pct": 20,
        "bandwidth_mbps": 30,
        "latency_ms": 35,
        "queue_length": 8
    }
]

task = {
    "required_cpu_pct": 20,
    "required_ram_pct": 15,
    "min_bandwidth_mbps": 40,
    "max_latency_ms": 30,
    "weights": {
        "cpu": 0.15,
        "ram": 0.15,
        "bandwidth": 0.50,
        "latency": 0.20
    }
}

reliability_estimates = {
    "A": {
        "cpu": {"reliability": 0.95, "uncertainty": 0.05},
        "ram": {"reliability": 0.95, "uncertainty": 0.05},
        "bandwidth": {"reliability": 0.60, "uncertainty": 0.30},
        "latency": {"reliability": 0.90, "uncertainty": 0.10},
        "queue": {"reliability": 0.85, "uncertainty": 0.15}
    },
    "B": {
        "cpu": {"reliability": 0.90, "uncertainty": 0.10},
        "ram": {"reliability": 0.95, "uncertainty": 0.05},
        "bandwidth": {"reliability": 0.95, "uncertainty": 0.05},
        "latency": {"reliability": 0.90, "uncertainty": 0.10},
        "queue": {"reliability": 0.90, "uncertainty": 0.10}
    },
    "C": {
        "cpu": {"reliability": 0.90, "uncertainty": 0.10},
        "ram": {"reliability": 0.90, "uncertainty": 0.10},
        "bandwidth": {"reliability": 0.80, "uncertainty": 0.20},
        "latency": {"reliability": 0.85, "uncertainty": 0.15},
        "queue": {"reliability": 0.80, "uncertainty": 0.20}
    }
}