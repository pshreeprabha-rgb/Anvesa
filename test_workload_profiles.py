
from Simulation.task import create_workload_task


def main():
    workload_types = [
        "compute-heavy",
        "memory-heavy",
        "bandwidth-heavy",
        "latency-sensitive",
        "mixed-resource",
    ]

    for index, workload_type in enumerate(workload_types, start=1):
        task = create_workload_task(
            f"Task-{index}",
            workload_type,
        )

        print(
            f"{task.task_type}: "
            f"CPU={task.cpu_required}, "
            f"RAM={task.ram_required}, "
            f"Bandwidth={task.bandwidth_required}"
        )

    print("\nAll workload profiles created successfully!")


if __name__ == "__main__":
    main()
