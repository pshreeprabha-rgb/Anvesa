
class ResourceReport:
    def __init__(
        self,
        node_id,
        cpu,
        ram,
        bandwidth,
        latency,
        queue_length,
        reported_at=None,
        sequence=0,
    ):
        self.node_id = node_id
        self.cpu = cpu
        self.ram = ram
        self.bandwidth = bandwidth
        self.latency = latency
        self.queue_length = queue_length
        self.reported_at = reported_at
        self.sequence = sequence


    def age_at(self, current_time):
        """Return the age of this report at the given simulation time."""
        if self.reported_at is None:
            raise ValueError("Report timestamp is not set")

        age = current_time - self.reported_at
        return max(0.0, age)


    def display(self):
        print("Resource Report")
        print("Node ID:", self.node_id)
        print("CPU:", self.cpu)
        print("RAM:", self.ram)
        print("Bandwidth:", self.bandwidth)
        print("Latency:", self.latency)
        print("Queue Length:", self.queue_length)
        print("Reported At:", self.reported_at)
        print("Sequence:", self.sequence)

    def can_handle_task(self, task):
        return (
            self.cpu >= task.cpu_required
            and self.ram >= task.ram_required
            and self.bandwidth >= task.bandwidth_required
        )
