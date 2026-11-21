from typing import Any

from src.common.schemas import ExecutionResult, Task
from src.simulation.timeutil import sim_time_to_iso


class ExecutionSimulator:
    def __init__(self, energy_coefficient: float = 0.05):
        self.energy_coeff = energy_coefficient
    def _fail(
        self, task: Task, node: dict[str, Any], t: float, reason: str
    ) -> ExecutionResult:
        """A rejected task reveals the node's true utilization and bandwidth."""
        ts = sim_time_to_iso(t)
        s = node["true_state"]
        return ExecutionResult(
            task_id=task.task_id,
            node_id=str(node["id"]),
            started_at=ts,
            completed_at=ts,
            success=False,
            actual={
                "cpu_pct": s["cpu_pct"],
                "ram_pct": s["ram_pct"],
                "bandwidth_mbps": s["bandwidth_mbps"],
            },
            predicted={},
            failure_reason=reason,
        )
    def execute_task(
        self, task: Task, node: dict[str, Any], current_time: float
    ) -> ExecutionResult:
        """Run a task against ground-truth node state (utilization semantics)."""
        s = node["true_state"]
        req = task.requirements
        if s["cpu_pct"] + req.cpu_pct > 100.0:
            return self._fail(task, node, current_time, "TRUE_CPU_EXHAUSTED")
        if s["ram_pct"] + req.ram_pct > 100.0:
            return self._fail(task, node, current_time, "TRUE_RAM_EXHAUSTED")
        if s["bandwidth_mbps"] < req.min_bandwidth_mbps:
            return self._fail(task, node, current_time, "INSUFFICIENT_BANDWIDTH")
        queue_delay = s["queue_length"] * 5.0  # 5 ms per queued item
        actual_latency = s["latency_ms"] + queue_delay + req.cpu_pct * 0.5
        actual_energy = self.energy_coeff * actual_latency * (req.cpu_pct / 100.0)
        # Apply node load increase
        s["cpu_pct"] += req.cpu_pct * 0.4
        s["ram_pct"] += req.ram_pct * 0.3
        s["queue_length"] += 1
        return ExecutionResult(
            task_id=task.task_id,
            node_id=str(node["id"]),
            started_at=sim_time_to_iso(current_time),
            completed_at=sim_time_to_iso(current_time + actual_latency / 1000.0),
            success=True,
            actual={
                "latency_ms": actual_latency,
                "energy_j": actual_energy,
                "cpu_pct": s["cpu_pct"],
                "ram_pct": s["ram_pct"],
            },
            predicted={},  # filled in by the orchestrator
        )
    def decay_node_load(self, node: dict[str, Any], elapsed_seconds: float) -> None:
        """Simulate task completion: load decays over time."""
        s = node["true_state"]
        factor = max(0.0, 1.0 - 0.2 * elapsed_seconds)
        s["cpu_pct"] = max(5.0, s["cpu_pct"] * factor)
        s["ram_pct"] = max(10.0, s["ram_pct"] * factor)
        s["queue_length"] = max(0, int(s["queue_length"] * factor))