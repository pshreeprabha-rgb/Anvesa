import os
import matplotlib.pyplot as plt
import pandas as pd


def generate_experiment_plots(
    results_csv_path: str, output_dir: str = "data/sample/figures"
):
    """
    Reads experiment results from CSV and generates comparison plots across unreliability levels:
    - Average Latency (ms) vs. Unreliability Level (%)
    - Completion Rate (%) vs. Unreliability Level (%)
    """
    if not os.path.exists(results_csv_path):
        print(f"[Member 4 Plots] Results file not found: {results_csv_path}")
        return

    df = pd.read_csv(results_csv_path)
    os.makedirs(output_dir, exist_ok=True)

    required_cols = {"policy", "unreliability_level", "avg_latency_ms", "completion_rate"}
    if not required_cols.issubset(df.columns):
        print(f"[Member 4 Plots] Missing required columns in CSV: {required_cols - set(df.columns)}")
        return

    # 1. Latency vs Unreliability
    plt.figure(figsize=(8, 5))
    for policy, group in df.groupby("policy"):
        plt.plot(
            group["unreliability_level"],
            group["avg_latency_ms"],
            marker="o",
            linewidth=2,
            label=policy,
        )
    plt.title("Average Latency vs. Unreliability Level")
    plt.xlabel("Unreliability Level")
    plt.ylabel("Average Latency (ms)")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "latency_vs_unreliability.png"))
    plt.close()

    # 2. Completion Rate vs Unreliability
    plt.figure(figsize=(8, 5))
    for policy, group in df.groupby("policy"):
        plt.plot(
            group["unreliability_level"],
            group["completion_rate"],
            marker="s",
            linewidth=2,
            label=policy,
        )
    plt.title("Task Completion Rate vs. Unreliability Level")
    plt.xlabel("Unreliability Level")
    plt.ylabel("Completion Rate (%)")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "completion_vs_unreliability.png"))
    plt.close()

    print(f"[Member 4 Plots] Figures generated successfully in: {output_dir}")