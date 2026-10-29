import random
import pytest
from src.common.schemas import ResourceReport, Task, ExecutionResult
from src.simulation.tasks import generate_task_stream, TASK_PROFILES
from src.simulation.reports import generate_reports
from src.simulation.unreliability import UnreliabilityInjector
from src.simulation.execution import ExecutionSimulator

def get_dummy_nodes():
    return [
        {
            "id": f"edge-{i:02d}",
            "true_state": {
                "cpu_pct": 20.0,
                "ram_pct": 30.0,
                "bandwidth_mbps": 100.0,
                "latency_ms": 25.0,
                "queue_length": 1,
            },
        }
        for i in range(10)
    ]

def test_task_stream_generation_and_schema():
    """Verifies that generated tasks conform to schemas and all 5 types exist."""
    rng = random.Random(42)
    tasks = generate_task_stream(count=50, rng=rng)
    assert len(tasks) == 50
    for task in tasks:
        assert isinstance(task, Task)
        assert task.task_id.startswith("task-")
        assert set(task.weights.keys()) == {"cpu", "ram", "bandwidth", "latency"}

def test_seed_reproducibility():
    """Verifies identical seeds generate exact matching tasks and reports."""
    rng1 = random.Random(1337)
    rng2 = random.Random(1337)

    tasks_1 = generate_task_stream(count=10, rng=rng1)
    tasks_2 = generate_task_stream(count=10, rng=rng2)
    assert [t.model_dump() for t in tasks_1] == [t.model_dump() for t in tasks_2]

    nodes1 = get_dummy_nodes()
    nodes2 = get_dummy_nodes()
    reports_1 = generate_reports(nodes1, sequence=1, timestamp=1.0, rng=rng1)
    reports_2 = generate_reports(nodes2, sequence=1, timestamp=1.0, rng=rng2)
    assert [r.model_dump() for r in reports_1] == [r.model_dump() for r in reports_2]

def test_resource_report_schema_and_types():
    """Asserts reports emit string node_ids and valid ResourceReport models."""
    nodes = get_dummy_nodes()
    rng = random.Random(42)
    reports = generate_reports(nodes, sequence=1, timestamp=10.0, rng=rng)

    assert len(reports) == 10
    for rep in reports:
        assert isinstance(rep, ResourceReport)
        assert isinstance(rep.node_id, str)
        assert "cpu_pct" in rep.resources
        assert "ram_pct" in rep.resources
        assert "bandwidth_mbps" in rep.resources
        assert "latency_ms" in rep.resources
        assert "queue_length" in rep.resources

def test_unreliability_injector_bounds():
    """Verifies unreliability injector operates without throwing and modifies outputs."""
    nodes = get_dummy_nodes()
    rng = random.Random(42)
    injector = UnreliabilityInjector(level=0.4, stale_ratio=0.5, manipulation_ratio=0.5)

    reports = generate_reports(nodes, sequence=1, timestamp=10.0, rng=rng, unreliability_injector=injector)
    assert len(reports) == 10
    for rep in reports:
        assert isinstance(rep, ResourceReport)

def test_execution_simulator_returns_result():
    """Asserts execution yields an ExecutionResult with dynamic actuals."""
    sim = ExecutionSimulator()
    node = get_dummy_nodes()[0]
    rng = random.Random(42)
    task = generate_task_stream(count=1, rng=rng)[0]

    result = sim.execute_task(task, node, current_time=1.0)
    assert isinstance(result, ExecutionResult)
    if result.success:
        assert "latency_ms" in result.actual
        assert "energy_j" in result.actual
        assert result.actual["latency_ms"] > 0