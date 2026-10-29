
import csv
import random

from Simulation.execution import execute_task
from Simulation.node import Node
from Simulation.resource_report import ResourceReport
from Simulation.scheduler import find_node_from_reports
from Simulation.task import Task
from Simulation.unreliable_report import add_noise

NUMBER_OF_TRIALS = 20
NUMBER_OF_NODES = 10
NUMBER_OF_TASKS = 5

NOISE_LEVELS = [0, 10, 20, 30, 40]


def create_nodes(rng):
    nodes = []

    for i in range(NUMBER_OF_NODES):
        nodes.append(
            Node(
                node_id=f"Node-{i + 1}",
                cpu=rng.randint(20, 100),
                ram=rng.randint(20, 100),
                bandwidth=rng.randint(50, 200),
                latency=rng.randint(5, 50),
                queue_length=rng.randint(0, 10),
            )
        )

    return nodes


def create_tasks(rng):
    tasks = []
    task_types = ["computation", "data_processing", "sensor"]

    for i in range(NUMBER_OF_TASKS):
        tasks.append(
            Task(
                task_id=f"Task-{i + 1}",
                task_type=task_types[i % len(task_types)],
                cpu_required=rng.randint(50, 100),
                ram_required=rng.randint(50, 100),
                bandwidth_required=rng.randint(80, 150),
            )
        )

    return tasks


def create_reports(nodes, noise_percentage, rng):
    reports = []

    for node in nodes:
        reports.append(
            ResourceReport(
                node_id=node.node_id,
                cpu=add_noise(node.cpu, noise_percentage, rng),
                ram=add_noise(node.ram, noise_percentage, rng),
                bandwidth=add_noise(
                    node.bandwidth, noise_percentage, rng
                ),
                latency=add_noise(
                    node.latency, noise_percentage, rng
                ),
                queue_length=round(
                    add_noise(
                        node.queue_length,
                        noise_percentage,
                        rng,
                    )
                ),
            )
        )

    return reports


def run_trial(nodes, tasks, noise_percentage, seed):
    rng = random.Random(seed)

    reports = create_reports(nodes, noise_percentage, rng)
    successful = 0

    for task in tasks:
        selected_node = find_node_from_reports(
            reports, nodes, task
        )

        if selected_node is None:
            continue

        result = execute_task(selected_node, task)

        if result == "SUCCESS":
            successful += 1

    return successful


def main():
    results = []

    print("=" * 50)
    print("ARRRO: MEASUREMENT NOISE EXPERIMENT")
    print("=" * 50)

    for noise in NOISE_LEVELS:
        total_successes = 0
        total_tasks = 0

        for trial in range(1, NUMBER_OF_TRIALS + 1):
            trial_seed = 1000 + trial

            # Reuse the same actual nodes and tasks
            # for every noise level in this trial.
            nodes = create_nodes(random.Random(trial_seed))
            tasks = create_tasks(
                random.Random(trial_seed + 5000)
            )

            successes = run_trial(
                nodes,
                tasks,
                noise,
                seed=trial_seed + 2000,
            )

            total_successes += successes
            total_tasks += len(tasks)

        success_rate = (
            total_successes / total_tasks * 100
            if total_tasks else 0
        )

        results.append({
            "noise_percentage": noise,
            "trials": NUMBER_OF_TRIALS,
            "total_tasks": total_tasks,
            "successful_tasks": total_successes,
            "failed_tasks": total_tasks - total_successes,
            "success_rate_percentage": round(success_rate, 2),
        })

        print(
            f"Noise: {noise:2}% | "
            f"Success rate: {success_rate:6.2f}% | "
            f"Successes: {total_successes}/{total_tasks}"
        )

    with open(
        "ARRRO_noise_level_results.csv",
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

    print("\nResults saved to ARRRO_noise_level_results.csv")
    print("Experiment completed.")


if __name__ == "__main__":
    main()
