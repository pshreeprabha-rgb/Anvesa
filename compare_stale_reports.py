
from Simulation.node import Node
from Simulation.task import Task
from Simulation.resource_report import ResourceReport
from Simulation.unreliable_report import create_stale_report
from Simulation.scheduler import find_node_from_reports
from Simulation.execution import execute_task


def run_case(report):
    # The node's actual resources are sufficient for this task.
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

    selected_node = find_node_from_reports(
        [report], [node], task
    )

    if selected_node is None:
        return "NOT SCHEDULED"

    return execute_task(selected_node, task)


def main():
    # Old report incorrectly says the node has few resources.
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

    # Fresh report reflects the node's actual resources.
    fresh_report = ResourceReport(
        node_id="Node-1",
        cpu=80,
        ram=80,
        bandwidth=150,
        latency=10,
        queue_length=1,
        reported_at=2,
        sequence=2,
    )

    stale_report = create_stale_report(old_report)

    fresh_result = run_case(fresh_report)
    stale_result = run_case(stale_report)

    print("Fresh report result:", fresh_result)
    print("Stale report result:", stale_result)

    assert fresh_result == "SUCCESS"
    assert stale_result == "NOT SCHEDULED"

    print("\nFresh-vs-stale comparison passed!")


if __name__ == "__main__":
    main()
