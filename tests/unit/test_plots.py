import os

import pandas as pd
import pytest

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


def test_generate_experiment_plots_missing_file(tmp_path):
    csv_path = tmp_path / "missing.csv"
    out_dir = tmp_path / "figures"

    with pytest.raises(ValueError, match="Results file not found") as exc_info:
        generate_experiment_plots(str(csv_path), output_dir=str(out_dir))

    assert str(csv_path) in str(exc_info.value)
    assert not out_dir.exists()


@pytest.mark.parametrize(
    "missing_column",
    ["policy", "unreliability_level", "avg_latency_ms", "completion_rate"],
)
def test_generate_experiment_plots_missing_column(tmp_path, missing_column):
    data = {
        "policy": ["ARRRO"],
        "unreliability_level": [0.0],
        "avg_latency_ms": [15.2],
        "completion_rate": [98.0],
    }
    del data[missing_column]
    csv_path = tmp_path / "results.csv"
    pd.DataFrame(data).to_csv(csv_path, index=False)
    out_dir = tmp_path / "figures"

    with pytest.raises(ValueError, match="Missing required columns") as exc_info:
        generate_experiment_plots(str(csv_path), output_dir=str(out_dir))

    assert missing_column in str(exc_info.value)
    assert not out_dir.exists()
