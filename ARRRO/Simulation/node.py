
from Simulation.resource_state import ResourceState


class Node:
    def __init__(self, node_id, cpu, ram, bandwidth, latency, queue_length):
        self.node_id = node_id

        self.state = ResourceState(
            cpu=cpu,
            ram=ram,
            bandwidth=bandwidth,
            latency=latency,
            queue_length=queue_length,
        )

    @property
    def cpu(self):
        return self.state.cpu

    @property
    def ram(self):
        return self.state.ram

    @property
    def bandwidth(self):
        return self.state.bandwidth

    @property
    def latency(self):
        return self.state.latency

    @property
    def queue_length(self):
        return self.state.queue_length

    def display(self):
        print("Node ID:", self.node_id)
        print("CPU:", self.cpu)
        print("RAM:", self.ram)
        print("Bandwidth:", self.bandwidth)
        print("Latency:", self.latency)
        print("Queue Length:", self.queue_length)



def fail_node(node):
    """Mark a node as failed without deleting its resource state."""
    node.is_failed = True


def recover_node(node):
    """Restore a node after a simulated failure."""
    node.is_failed = False
