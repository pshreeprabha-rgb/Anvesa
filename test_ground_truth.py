
from Simulation.node import Node
from Simulation.resource_state import capture_ground_truth
from Simulation.resource_report import ResourceReport
from Simulation.unreliable_report import manipulate_report


def main():
    node = Node(
        node_id="Node-1",
        cpu=80,
        ram=60,
        bandwidth=100,
        latency=10,
        queue_length=2,
    )

    # Capture the actual state.
    ground_truth = capture_ground_truth(node)

    # Create a report that understates the resources.
    report = ResourceReport(
        node_id=node.node_id,
        cpu=node.cpu,
        ram=node.ram,
        bandwidth=node.bandwidth,
        latency=node.latency,
        queue_length=node.queue_length,
    )

    manipulated_report = manipulate_report(report, 30)

    print("Actual CPU:", ground_truth["cpu"])
    print("Reported CPU:", manipulated_report.cpu)
    print("Actual RAM:", ground_truth["ram"])
    print("Reported RAM:", manipulated_report.ram)

    assert ground_truth["cpu"] == 80
    assert manipulated_report.cpu == 56
    assert ground_truth["ram"] == 60
    assert manipulated_report.ram == 42

    # The actual node and saved snapshot must remain unchanged.
    assert node.cpu == 80
    assert ground_truth["cpu"] == 80

    print("\nGround-truth test passed!")


if __name__ == "__main__":
    main()
