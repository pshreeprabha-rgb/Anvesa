
import csv

from Simulation.node import Node
from Simulation.task import Task
from Simulation.resource_report import ResourceReport
from Simulation.unreliable_report import create_stale_report
from Simulation.scheduler import find_node_from_reports
from Simulation.execution import execute_task


NUMBER_OF_TRIALS = 20
TASKS_PER_TRIAL = 5


def run_trial(use_stale_report):
    successful_tasks = 0
    not_scheduled = 0

    for trial_task in range(TASKS_PER_TRIAL):
        node = Node(
            node_id="Node-1",
            cpu=80,
            ram=80,
            bandwidth=150,
            latency=10,
            queue_length=1,
        )

        task = Task(
            task_id=f"Task-{trial_task + 1}",
            task_type="computation",
            cpu_required=60,
            ram_required=60,
            bandwidth_required=100,
        )

        old_report = ResourceReport(
            node_id="Node-1",
            cpu=30,
            ram=30,
            bandwidth=50,
            latency=10,
            queue_length=1,
            reported_at=1,
            sequence=1,
        )

        fresh_report = ResourceReport(
            node_id="Node-1",
            cpu=node.cpu,
            ram=node.ram,
            bandwidth=node.bandwidth,
            latency=node.latency,
            queue_length=node.queue_length,
            reported_at=2,
            sequence=2,
        )

        report = (
            create_stale_report(old_report)
            if use_stale_report
            else fresh_report
        )

        selected_node = find_node_from_reports(
            [report], [node], task
        )

        if selected_node is None:
            not_scheduled += 1
            continue

        if execute_task(selected_node, task) == "SUCCESS":
            successful_tasks += 1

    return successful_tasks, not_scheduled


def main():
    results = []

    for scenario, use_stale in [
        ("fresh_reports", False),
        ("stale_reports", True),
    ]:
        total_successes = 0
        total_not_scheduled = 0

        for _ in range(NUMBER_OF_TRIALS):
            successes, skipped = run_trial(use_stale)
            total_successes += successes
            total_not_scheduled += skipped

        total_tasks = NUMBER_OF_TRIALS * TASKS_PER_TRIAL

        row = {
            "scenario": scenario,
            "trials": NUMBER_OF_TRIALS,
            "total_tasks": total_tasks,
            "successful_tasks": total_successes,
            "not_scheduled": total_not_scheduled,
            "success_rate_percentage": round(
                total_successes / total_tasks * 100, 2
            ),
        }

        results.append(row)

        print(
            f"{scenario}: "
            f"{row['success_rate_percentage']:.2f}% success "
            f"({total_successes}/{total_tasks})"
        )

    with open(
        "ARRRO_stale_report_results.csv",
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

    print("\nResults saved to ARRRO_stale_report_results.csv")


if __name__ == "__main__":
    main()
