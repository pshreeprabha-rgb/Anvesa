
from Simulation.node import Node
from Simulation.resource_report import ResourceReport
from Simulation.resource_state import capture_ground_truth
from Simulation.unreliable_report import manipulate_report


def test_ground_truth_is_preserved_when_report_is_manipulated():
    node = Node(
        node_id="Node-1",
        cpu=80,
        ram=60,
        bandwidth=100,
        latency=10,
        queue_length=2,
    )

    ground_truth = capture_ground_truth(node)

    report = ResourceReport(
        node_id=node.node_id,
        cpu=node.cpu,
        ram=node.ram,
        bandwidth=node.bandwidth,
        latency=node.latency,
        queue_length=node.queue_length,
    )

    manipulated_report = manipulate_report(report, 30)

    assert ground_truth["cpu"] == 80
    assert manipulated_report.cpu == 56
    assert ground_truth["ram"] == 60
    assert manipulated_report.ram == 42
    assert node.cpu == 80
    assert node.ram == 60
    assert manipulated_report.bandwidth == 70

    assert report.cpu == 80
    assert report.ram == 60
