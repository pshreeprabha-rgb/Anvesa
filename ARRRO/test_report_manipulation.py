
from Simulation.resource_report import ResourceReport
from Simulation.unreliable_report import manipulate_report


def main():
    report = ResourceReport(
        node_id="Node-1",
        cpu=80,
        ram=60,
        bandwidth=100,
        latency=10,
        queue_length=1,
    )

    manipulated = manipulate_report(
        report,
        reduction_percentage=30,
    )

    print("Original CPU:", report.cpu)
    print("Reported CPU after manipulation:", manipulated.cpu)
    print("Original RAM:", report.ram)
    print("Reported RAM after manipulation:", manipulated.ram)

    assert manipulated.cpu == 56
    assert manipulated.ram == 42
    assert manipulated.bandwidth == 70
    assert manipulated.is_manipulated is True

    # The original report must remain unchanged.
    assert report.cpu == 80
    assert report.ram == 60

    print("\nReport-manipulation test passed!")


if __name__ == "__main__":
    main()
