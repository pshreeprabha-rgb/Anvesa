import json
import random
from pathlib import Path
from src.simulation.tasks import generate_task_stream
from src.simulation.reports import generate_reports

def main():
    rng = random.Random(42)
    nodes = [
        {
            "id": f"edge-{i:02d}",
            "true_state": {
                "cpu_pct": round(rng.uniform(10.0, 40.0), 2),
                "ram_pct": round(rng.uniform(15.0, 50.0), 2),
                "bandwidth_mbps": round(rng.uniform(50.0, 200.0), 2),
                "latency_ms": round(rng.uniform(10.0, 50.0), 2),
                "queue_length": rng.randint(0, 3),
            },
        }
        for i in range(10)
    ]

    tasks = generate_task_stream(count=20, rng=rng)
    reports = generate_reports(nodes, sequence=1, timestamp=100.0, rng=rng)

    payload = {
        "seed": 42,
        "nodes": [n["id"] for n in nodes],
        "reports": [r.model_dump() for r in reports],
        "tasks": [t.model_dump() for t in tasks],
    }

    out_path = Path("data/sample/sample_run.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Sample fixture written to {out_path}")

if __name__ == "__main__":
    main()