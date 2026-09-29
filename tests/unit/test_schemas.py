from src.common.schemas import ResourceMetrics, ResourceReport


def test_resource_report_schema():
    metrics = ResourceMetrics(
        cpu_pct=80.0,
        ram_pct=40.0,
        bandwidth_mbps=80.0,
        latency_ms=12.0,
        queue_length=3,
        reported_at="2026-09-27T16:29:58Z",
    )
    report = ResourceReport(
        timestamp="2026-09-27T16:30:00Z",
        node_id="edge-07",
        sequence=1842,
        resources=metrics,
    )
    assert report.schema_version == "1.0"
    assert report.node_id == "edge-07"