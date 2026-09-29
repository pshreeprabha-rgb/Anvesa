import os
import matplotlib.pyplot as plt
import pandas as pd


def plot_metrics_vs_unreliability(
    results_df: pd.DataFrame, output_dir: str = "results/figures"
):
    """
    Generates plots comparing ARRRO against baselines across unreliability levels (0% to 40%).
    Metrics plotted: Latency, Task Completion Rate, and Energy Consumption.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Latency vs Unreliability Level
    plt.figure(figsize=(8, 5))
    for policy, group in results_df.groupby("policy"):
        plt.plot(
            group["unreliability_level"],
            group["avg_latency_ms"],
            marker="o",
            label=policy,
        )
    plt.title("Average Latency vs. Unreliability Level")
    plt.xlabel("Unreliability Level")
    plt.ylabel("Average Latency (ms)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "latency_vs_unreliability.png"))
    plt.close()

    # 2. Task Completion Rate vs Unreliability Level
    plt.figure(figsize=(8, 5))
    for policy, group in results_df.groupby("policy"):
        plt.plot(
            group["unreliability_level"],
            group["completion_rate"],
            marker="s",
            label=policy,
        )
    plt.title("Task Completion Rate vs. Unreliability Level")
    plt.xlabel("Unreliability Level")
    plt.ylabel("Completion Rate (%)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "completion_vs_unreliability.png"))
    plt.close()

    print(f"[Member 4 Plots] Experiment figures saved to {output_dir}")