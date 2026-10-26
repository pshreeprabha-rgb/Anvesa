
import csv

from Simulation.node import Node
from Simulation.task import Task
from Simulation.resource_report import ResourceReport
from Simulation.unreliable_report import manipulate_report
from Simulation.scheduler import find_node_from_reports
from Simulation.execution import execute_task


def run_trial(use_manipulated_report):
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

    report = ResourceReport(
        node_id=node.node_id,
        cpu=node.cpu,
        ram=node.ram,
        bandwidth=node.bandwidth,
        latency=node.latency,
        queue_length=node.queue_length,
    )

    if use_manipulated_report:
        report = manipulate_report(
            report,
            reduction_percentage=30,
        )

    selected_node = find_node_from_reports(
        [report], [node], task
    )

    if selected_node is None:
        return "NOT SCHEDULED"

    return execute_task(selected_node, task)


def main():
    number_of_trials = 20
    results = []

    for scenario, manipulated in [
        ("normal_reports", False),
        ("manipulated_reports", True),
    ]:
        outcomes = [
            run_trial(manipulated)
            for _ in range(number_of_trials)
        ]

        successes = outcomes.count("SUCCESS")
        not_scheduled = outcomes.count("NOT SCHEDULED")

        row = {
            "scenario": scenario,
            "trials": number_of_trials,
            "successful_tasks": successes,
            "not_scheduled": not_scheduled,
            "success_rate_percentage": round(
                successes / number_of_trials * 100, 2
            ),
        }
        results.append(row)

        print(
            f"{scenario}: "
            f"{row['success_rate_percentage']:.2f}% success "
            f"({successes}/{number_of_trials})"
        )

    with open(
        "ARRRO_manipulation_results.csv",
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

    print("\nResults saved to ARRRO_manipulation_results.csv")


if __name__ == "__main__":
    main()
