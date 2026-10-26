
from Simulation.resource_report import ResourceReport
from Simulation.unreliable_report import create_stale_report


def test_stale_report_preserves_old_values():
    old_report = ResourceReport(
        node_id="Node-1",
        cpu=40,
        ram=50,
        bandwidth=100,
        latency=20,
        queue_length=2,
        reported_at=100,
        sequence=1,
    )

    stale_report = create_stale_report(old_report)

    assert stale_report.cpu == 40
    assert stale_report.reported_at == 100
    assert stale_report.sequence == 1
    assert stale_report.is_stale is True

    # Changing the new report must not alter the old report.
    stale_report.cpu = 90
    assert old_report.cpu == 40

    print("Stale report test passed!")


if __name__ == "__main__":
    test_stale_report_preserves_old_values()
