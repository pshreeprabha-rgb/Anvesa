
class Task:
    VALID_TYPES = {
        "computation",
        "data_processing",
        "sensor",
        "compute-heavy",
        "memory-heavy",
        "bandwidth-heavy",
        "latency-sensitive",
        "mixed-resource",
    }

    def __init__(
        self,
        task_id,
        task_type,
        cpu_required,
        ram_required,
        bandwidth_required,
        max_latency=None,
    ):
        if task_type not in self.VALID_TYPES:
            raise ValueError(f"Unsupported task type: {task_type}")

        self.task_id = task_id
        self.task_type = task_type
        self.cpu_required = cpu_required
        self.ram_required = ram_required
        self.bandwidth_required = bandwidth_required
        self.max_latency = max_latency

    def display(self):
        print("Task ID:", self.task_id)
        print("Task Type:", self.task_type)
        print("CPU Required:", self.cpu_required)
        print("RAM Required:", self.ram_required)
        print("Bandwidth Required:", self.bandwidth_required)
        print("Maximum Latency:", self.max_latency)


def create_workload_task(task_id, task_type):
    """Create a task with requirements based on its workload type."""

    workload_profiles = {
        "compute-heavy": (90, 40, 80),
        "memory-heavy": (40, 90, 80),
        "bandwidth-heavy": (40, 40, 150),
        "latency-sensitive": (50, 50, 80),
        "mixed-resource": (75, 75, 120),
    }

    if task_type not in workload_profiles:
        raise ValueError(f"Unknown workload type: {task_type}")

    cpu, ram, bandwidth = workload_profiles[task_type]

    return Task(
        task_id=task_id,
        task_type=task_type,
        cpu_required=cpu,
        ram_required=ram,
        bandwidth_required=bandwidth,
        max_latency=15 if task_type == "latency-sensitive" else None,
    )
