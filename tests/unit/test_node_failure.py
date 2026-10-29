
from Simulation.node import Node, fail_node, recover_node
from Simulation.resource_report import ResourceReport
from Simulation.scheduler import find_node_from_reports
from Simulation.task import Task


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

    report = ResourceReport(
        node_id="Node-1",
        cpu=80,
        ram=80,
        bandwidth=150,
        latency=10,
        queue_length=1,
    )

    # Initially, the node can be selected.
    assert find_node_from_reports([report], [node], task) is node

    # A failed node must be skipped.
    fail_node(node)
    assert find_node_from_reports([report], [node], task) is None

    # After recovery, the node can be selected again.
    recover_node(node)
    assert find_node_from_reports([report], [node], task) is node

    print("Node failure and recovery test passed!")


if __name__ == "__main__":
    main()
