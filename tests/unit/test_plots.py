import os
import pandas as pd
from src.evaluation.plots import generate_experiment_plots


def test_generate_experiment_plots(tmp_path):
    # Create temporary CSV dataset
    data = {
        "policy": ["ARRRO", "ARRRO", "Greedy", "Greedy"],
        "unreliability_level": [0.0, 0.2, 0.0, 0.2],
        "avg_latency_ms": [15.2, 18.4, 15.0, 32.1],
        "completion_rate": [98.0, 92.0, 97.0, 65.0],
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "results.csv"
    df.to_csv(csv_path, index=False)

    out_dir = tmp_path / "figures"
    generate_experiment_plots(str(csv_path), output_dir=str(out_dir))

    assert os.path.exists(out_dir / "latency_vs_unreliability.png")
    assert os.path.exists(out_dir / "completion_vs_unreliability.png")