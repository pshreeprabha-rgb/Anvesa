
import csv

from Simulation.node import Node, fail_node, recover_node
from Simulation.task import Task
from Simulation.resource_report import ResourceReport
from Simulation.scheduler import find_node_from_reports
from Simulation.execution import execute_task


def main():
    node = Node(
        node_id="Node-1",
        cpu=80,
        ram=80,
        bandwidth=150,
        latency=10,
        queue_length=1,
    )

    task = Task(
        task_id="Task-1",
        task_type="computation",
        cpu_required=60,
        ram_required=60,
        bandwidth_required=100,
    )

    # Each phase represents a simulation step.
    phases = [
        ("step_1_healthy", "healthy"),
        ("step_2_failure", "failed"),
        ("step_3_failed", "failed"),
        ("step_4_recovery", "recovered"),
        ("step_5_healthy", "healthy"),
    ]

    results = []

    for step, (step_name, state) in enumerate(phases, start=1):
        if state == "failed":
            fail_node(node)
        else:
            recover_node(node)

        report = ResourceReport(
            node_id=node.node_id,
            cpu=node.cpu,
            ram=node.ram,
            bandwidth=node.bandwidth,
            latency=node.latency,
            queue_length=node.queue_length,
            reported_at=step,
            sequence=step,
        )

        selected_node = find_node_from_reports(
            [report], [node], task
        )

        if selected_node is None:
            outcome = "NOT SCHEDULED"
        else:
            outcome = execute_task(selected_node, task)

        row = {
            "step": step,
            "step_name": step_name,
            "node_state": state,
            "task_outcome": outcome,
        }
        results.append(row)

        print(
            f"{step_name}: "
            f"state={state}, outcome={outcome}"
        )

    with open(
        "ARRRO_node_lifecycle_results.csv",
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

    print("\nResults saved to ARRRO_node_lifecycle_results.csv")

    assert results[0]["task_outcome"] == "SUCCESS"
    assert results[1]["task_outcome"] == "NOT SCHEDULED"
    assert results[2]["task_outcome"] == "NOT SCHEDULED"
    assert results[3]["task_outcome"] == "SUCCESS"
    assert results[4]["task_outcome"] == "SUCCESS"

    print("Node lifecycle experiment passed!")


if __name__ == "__main__":
    main()
