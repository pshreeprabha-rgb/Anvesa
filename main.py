import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import csv
import random

import matplotlib.pyplot as plt

from Simulation.execution import execute_task
from Simulation.node import Node
from Simulation.resource_report import ResourceReport
from Simulation.scheduler import find_node_from_reports
from Simulation.simulation_config import SimulationConfig
from Simulation.task import Task
from Simulation.unreliable_report import add_noise

# ============================================================
# SETTINGS
# ============================================================

CONFIG = SimulationConfig()

NUMBER_OF_TRIALS = CONFIG.number_of_trials
NUMBER_OF_NODES = CONFIG.number_of_nodes
NUMBER_OF_TASKS = CONFIG.number_of_tasks
NOISE_PERCENTAGE = CONFIG.noise_percentage


# ============================================================
# CREATE EDGE NODES
# ============================================================

def create_nodes():
    nodes = []

    for i in range(1, NUMBER_OF_NODES + 1):
        node = Node(
            node_id=i,
            cpu=random.randint(20, 100),
            ram=random.randint(20, 100),
            bandwidth=random.randint(50, 200),
            latency=random.randint(5, 50),
            queue_length=random.randint(0, 10)
        )

        nodes.append(node)

    return nodes


# ============================================================
# CREATE TASKS
# ============================================================

def create_tasks():
    tasks = []

    for i in range(1, NUMBER_OF_TASKS + 1):
        task = Task(
            task_id=i,
            task_type=random.choice(
                [
                    "computation",
                    "data_processing",
                    "sensor"
                ]
            ),
            cpu_required=random.randint(50, 100),
            ram_required=random.randint(50, 100),
            bandwidth_required=random.randint(80, 150)
        )

        tasks.append(task)

    return tasks


# ============================================================
# CREATE RESOURCE REPORTS
# ============================================================

def create_reports(nodes, noise_percentage, rng=None):
    if rng is None:
        rng = random

    reports = []

    for node in nodes:
        report = ResourceReport(
            node_id=node.node_id,
            cpu=add_noise(
                node.cpu,
                noise_percentage,
                rng=rng
            ),
            ram=add_noise(
                node.ram,
                noise_percentage,
                rng=rng
            ),
            bandwidth=add_noise(
                node.bandwidth,
                noise_percentage,
                rng=rng
            ),
            latency=add_noise(
                node.latency,
                noise_percentage,
                rng=rng
            ),
            queue_length=round(
                add_noise(
                    node.queue_length,
                    noise_percentage,
                    rng=rng
                )
            )
        )

        reports.append(report)

    return reports


# ============================================================
# RUN ONE EXPERIMENT
# ============================================================

def run_experiment(reports, nodes, tasks):
    successful_tasks = 0
    failed_tasks = 0

    for task in tasks:
        node = find_node_from_reports(
            reports,
            nodes,
            task
        )

        if node is None:
            failed_tasks += 1
        else:
            result = execute_task(
                node,
                task
            )

            if result == "SUCCESS":
                successful_tasks += 1
            else:
                failed_tasks += 1

    if not tasks:
        return 0, 0, 0.0

    success_rate = (
        successful_tasks / len(tasks)
    ) * 100

    return (
        successful_tasks,
        failed_tasks,
        success_rate
    )


# ============================================================
# START SIMULATION
# ============================================================

def main():
    print("========================================")
    print("ARRRO SIMULATION")
    print("========================================")

    print("Random seed:", CONFIG.random_seed)
    print("Number of trials:", NUMBER_OF_TRIALS)
    print("Number of nodes:", NUMBER_OF_NODES)
    print("Number of tasks:", NUMBER_OF_TASKS)
    print("Unreliable report noise:", NOISE_PERCENTAGE, "%")

    # Store results
    normal_results = []
    unreliable_results = []
    all_results = []

    # ========================================================
    # RUN MULTIPLE TRIALS
    # ========================================================

    for trial in range(1, NUMBER_OF_TRIALS + 1):
        # Use independent, reproducible random streams
        trial_seed = CONFIG.random_seed + trial

        # Create nodes and tasks reproducibly
        generation_rng = random.Random(trial_seed)

        nodes = []
        for i in range(1, NUMBER_OF_NODES + 1):
            node = Node(
                node_id=i,
                cpu=generation_rng.randint(20, 100),
                ram=generation_rng.randint(20, 100),
                bandwidth=generation_rng.randint(50, 200),
                latency=generation_rng.randint(5, 50),
                queue_length=generation_rng.randint(0, 10)
            )
            nodes.append(node)

        tasks = []
        for i in range(1, NUMBER_OF_TASKS + 1):
            task = Task(
                task_id=i,
                task_type=generation_rng.choice(
                    [
                        "computation",
                        "data_processing",
                        "sensor"
                    ]
                ),
                cpu_required=generation_rng.randint(50, 100),
                ram_required=generation_rng.randint(50, 100),
                bandwidth_required=generation_rng.randint(80, 150)
            )
            tasks.append(task)

        # ----------------------------------------------------
        # NORMAL REPORT EXPERIMENT
        # ----------------------------------------------------

        normal_rng = random.Random(trial_seed + 1000)

        normal_reports = create_reports(
            nodes,
            0,
            rng=normal_rng
        )

        (
            normal_successful,
            normal_failed,
            normal_success_rate
        ) = run_experiment(
            normal_reports,
            nodes,
            tasks
        )

        # ----------------------------------------------------
        # UNRELIABLE REPORT EXPERIMENT
        # ----------------------------------------------------

        unreliable_rng = random.Random(trial_seed + 2000)

        unreliable_reports = create_reports(
            nodes,
            NOISE_PERCENTAGE,
            rng=unreliable_rng
        )

        (
            unreliable_successful,
            unreliable_failed,
            unreliable_success_rate
        ) = run_experiment(
            unreliable_reports,
            nodes,
            tasks
        )

        # ----------------------------------------------------
        # STORE RESULTS
        # ----------------------------------------------------

        normal_results.append(normal_success_rate)
        unreliable_results.append(unreliable_success_rate)

        trial_difference = (
            normal_success_rate - unreliable_success_rate
        )

        all_results.append(
            [
                trial,
                normal_successful,
                normal_failed,
                normal_success_rate,
                unreliable_successful,
                unreliable_failed,
                unreliable_success_rate,
                trial_difference
            ]
        )

        # ----------------------------------------------------
        # DISPLAY TRIAL RESULT
        # ----------------------------------------------------

        print("\n----------------------------------------")
        print("TRIAL", trial)
        print("----------------------------------------")

        print(
            "Normal Reports:",
            normal_successful,
            "successful,",
            normal_failed,
            "failed,",
            round(normal_success_rate, 2),
            "%"
        )

        print(
            "Unreliable Reports:",
            unreliable_successful,
            "successful,",
            unreliable_failed,
            "failed,",
            round(unreliable_success_rate, 2),
            "%"
        )

    # ========================================================
    # CALCULATE AVERAGES
    # ========================================================

    average_normal = (
        sum(normal_results) / len(normal_results)
        if normal_results else 0.0
    )

    average_unreliable = (
        sum(unreliable_results) / len(unreliable_results)
        if unreliable_results else 0.0
    )

    difference = average_normal - average_unreliable

    # ========================================================
    # FINAL RESULTS
    # ========================================================

    print("\n========================================")
    print("FINAL EXPERIMENT RESULTS")
    print("========================================")

    print(
        "Average Normal Report Success Rate:",
        round(average_normal, 2),
        "%"
    )

    print(
        "Average Unreliable Report Success Rate:",
        round(average_unreliable, 2),
        "%"
    )

    print(
        "Difference:",
        round(difference, 2),
        "percentage points"
    )

    # ========================================================
    # RESULTS TABLE
    # ========================================================

    print("\n========================================")
    print("TRIAL RESULTS TABLE")
    print("========================================")

    print("Trial | Normal (%) | Unreliable (%)")
    print("----------------------------------------")

    for i in range(len(normal_results)):
        print(
            str(i + 1).ljust(6),
            "|",
            str(round(normal_results[i], 2)).ljust(11),
            "|",
            round(unreliable_results[i], 2)
        )

    # ========================================================
    # SAVE RESULTS TO CSV
    # ========================================================

    with open(
        "ARRRO_trial_results.csv",
        "w",
        newline=""
    ) as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "Trial",
                "Normal_Successful",
                "Normal_Failed",
                "Normal_Success_Rate",
                "Unreliable_Successful",
                "Unreliable_Failed",
                "Unreliable_Success_Rate",
                "Difference"
            ]
        )

        writer.writerows(all_results)

    print("\n========================================")
    print("CSV FILE CREATED")
    print("========================================")
    print("File: ARRRO_trial_results.csv")

    # ========================================================
    # SIMULATION COMPLETED
    # ========================================================

    print("\n========================================")
    print("SIMULATION COMPLETED")
    print("========================================")

    # ========================================================
    # CREATE SUCCESS RATE GRAPH
    # ========================================================

    trials = range(1, NUMBER_OF_TRIALS + 1)

    plt.figure(figsize=(10, 6))

    plt.plot(
        trials,
        normal_results,
        marker="o",
        label="Normal Reports"
    )

    plt.plot(
        trials,
        unreliable_results,
        marker="o",
        label="Unreliable Reports"
    )

    plt.title("ARRRO: Normal vs Unreliable Report Success Rate")
    plt.xlabel("Trial Number")
    plt.ylabel("Success Rate (%)")

    plt.xticks(range(1, NUMBER_OF_TRIALS + 1))
    plt.ylim(0, 100)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.savefig("ARRRO_success_rate_graph.png")
    plt.show()


if __name__ == "__main__":
    main()
