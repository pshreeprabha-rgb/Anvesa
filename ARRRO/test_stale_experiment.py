
from Simulation.resource_report import ResourceReport
from Simulation.unreliable_report import create_stale_report


def main():
    # Simulate an older report from before the node changed.
    old_report = ResourceReport(
        node_id="Node-1",
        cpu=40,
        ram=50,
        bandwidth=100,
        latency=20,
        queue_length=2,
        reported_at=1,
        sequence=1,
    )

    # Simulate the latest report after the node's resources changed.
    current_report = ResourceReport(
        node_id="Node-1",
        cpu=85,
        ram=80,
        bandwidth=150,
        latency=10,
        queue_length=1,
        reported_at=2,
        sequence=2,
    )

    # Deliberately use the older report.
    report_used = create_stale_report(old_report)

    print("Current CPU:", current_report.cpu)
    print("CPU in report used by scheduler:", report_used.cpu)
    print("Current report sequence:", current_report.sequence)
    print("Sequence in report used by scheduler:", report_used.sequence)
    print("Is report stale:", report_used.is_stale)

    assert report_used.cpu == 40
    assert report_used.sequence == 1
    assert report_used.is_stale is True

    print("\nStale-report experiment passed!")


if __name__ == "__main__":
    main()
