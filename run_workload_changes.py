
import csv

from Simulation.execution import execute_task
from Simulation.node import Node
from Simulation.resource_report import ResourceReport
from Simulation.scheduler import find_node_from_reports
from Simulation.task import create_workload_task


def main():
    nodes = [
        Node(
            node_id="Node-1",
            cpu=60,
            ram=60,
            bandwidth=100,
            latency=10,
            queue_length=1,
        ),
        Node(
            node_id="Node-2",
            cpu=95,
            ram=95,
            bandwidth=180,
            latency=8,
            queue_length=1,
        ),
    ]

    # The workload changes from lighter to heavier tasks.
    workload_phases = [
        ("light_phase", "latency-sensitive"),
        ("heavy_phase", "mixed-resource"),
        ("heavy_phase", "compute-heavy"),
        ("heavy_phase", "memory-heavy"),
        ("heavy_phase", "bandwidth-heavy"),
    ]

    results = []

    for task_number, (phase, workload_type) in enumerate(
        workload_phases, start=1
    ):
        task = create_workload_task(
            f"Task-{task_number}",
            workload_type,
        )

        reports = [
            ResourceReport(
                node_id=node.node_id,
                cpu=node.cpu,
                ram=node.ram,
                bandwidth=node.bandwidth,
                latency=node.latency,
                queue_length=node.queue_length,
            )
            for node in nodes
            if not getattr(node, "is_failed", False)
        ]

        selected_node = find_node_from_reports(
            reports, nodes, task
        )

        if selected_node is None:
            outcome = "NOT SCHEDULED"
            selected_node_id = ""
        else:
            outcome = execute_task(selected_node, task)
            selected_node_id = selected_node.node_id

        row = {
            "task_id": task.task_id,
            "workload_phase": phase,
            "workload_type": workload_type,
            "selected_node": selected_node_id,
            "outcome": outcome,
        }
        results.append(row)

        print(
            f"{phase} | {workload_type} | "
            f"Node: {selected_node_id or 'None'} | "
            f"Result: {outcome}"
        )

    with open(
        "ARRRO_workload_change_results.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys(),
        )
        writer.writeheader()
        writer.writerows(results)

    print("\nResults saved to ARRRO_workload_change_results.csv")


if __name__ == "__main__":
    main()
