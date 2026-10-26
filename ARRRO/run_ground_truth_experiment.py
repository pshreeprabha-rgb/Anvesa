
import csv

from Simulation.node import Node
from Simulation.resource_state import capture_ground_truth
from Simulation.resource_report import ResourceReport
from Simulation.unreliable_report import (
    add_noise,
    create_stale_report,
    manipulate_report,
)


def main():
    node = Node(
        node_id="Node-1",
        cpu=80,
        ram=60,
        bandwidth=100,
        latency=10,
        queue_length=2,
    )

    ground_truth = capture_ground_truth(node)

    fresh_report = ResourceReport(
        node_id=node.node_id,
        cpu=node.cpu,
        ram=node.ram,
        bandwidth=node.bandwidth,
        latency=node.latency,
        queue_length=node.queue_length,
        reported_at=2,
        sequence=2,
    )

    noisy_report = ResourceReport(
        node_id=node.node_id,
        cpu=add_noise(node.cpu, 20),
        ram=add_noise(node.ram, 20),
        bandwidth=add_noise(node.bandwidth, 20),
        latency=add_noise(node.latency, 20),
        queue_length=round(add_noise(node.queue_length, 20)),
        reported_at=2,
        sequence=2,
    )

    old_report = ResourceReport(
        node_id=node.node_id,
        cpu=40,
        ram=40,
        bandwidth=60,
        latency=20,
        queue_length=5,
        reported_at=1,
        sequence=1,
    )

    stale_report = create_stale_report(old_report)
    manipulated = manipulate_report(fresh_report, 30)

    scenarios = [
        ("fresh", fresh_report),
        ("noisy_20_percent", noisy_report),
        ("stale", stale_report),
        ("manipulated_30_percent", manipulated),
    ]

    rows = []

    for scenario, report in scenarios:
        row = {
            "scenario": scenario,
            "node_id": node.node_id,
            "actual_cpu": ground_truth["cpu"],
            "reported_cpu": report.cpu,
            "actual_ram": ground_truth["ram"],
            "reported_ram": report.ram,
            "actual_bandwidth": ground_truth["bandwidth"],
            "reported_bandwidth": report.bandwidth,
            "actual_latency": ground_truth["latency"],
            "reported_latency": report.latency,
            "actual_queue_length": ground_truth["queue_length"],
            "reported_queue_length": report.queue_length,
            "reported_at": report.reported_at,
            "sequence": report.sequence,
        }
        rows.append(row)

        print(
            f"{scenario}: "
            f"actual CPU={ground_truth['cpu']}, "
            f"reported CPU={report.cpu}"
        )

    with open(
        "ARRRO_ground_truth_results.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys(),
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nResults saved to ARRRO_ground_truth_results.csv")


if __name__ == "__main__":
    main()
