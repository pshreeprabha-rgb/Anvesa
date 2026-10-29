import time
from typing import Dict, Any
from src.common.schemas import Task, ExecutionResult

class ExecutionSimulator:
    def __init__(self, energy_coefficient: float = 0.05):
        self.energy_coeff = energy_coefficient

    def execute_task(
        self,
        task: Task,
        node: Dict[str, Any],
        current_time: float
    ) -> ExecutionResult:
        """
        Executes a task against ground-truth node state.
        Calculates actual runtime values and dynamic node load impact.
        """
        true_state = node["true_state"]
        start_time = current_time

        # Check true feasibility (ground-truth evaluation)
        if true_state["cpu_pct"] + task.requirements["cpu_pct"] > 100.0:
            return ExecutionResult(
                success=False,
                started_at=start_time,
                completed_at=start_time,
                actual={},
                predicted={},  # Orchestrator populates this
                failure_reason="TRUE_CPU_EXHAUSTED"
            )

        if true_state["bandwidth_mbps"] < task.requirements["min_bandwidth_mbps"]:
            return ExecutionResult(
                success=False,
                started_at=start_time,
                completed_at=start_time,
                actual={},
                predicted={},
                failure_reason="INSUFFICIENT_BANDWIDTH"
            )

        # Dynamic execution calculation
        queue_delay = true_state["queue_length"] * 5.0  # 5 ms per queued item
        actual_latency = true_state["latency_ms"] + queue_delay + (task.requirements["cpu_pct"] * 0.5)
        actual_energy = self.energy_coeff * actual_latency * (task.requirements["cpu_pct"] / 100.0)

        # Apply node load increase
        true_state["cpu_pct"] += task.requirements["cpu_pct"] * 0.4
        true_state["queue_length"] += 1
        true_state["ram_pct"] += task.requirements["ram_pct"] * 0.3

        end_time = start_time + (actual_latency / 1000.0)

        return ExecutionResult(
            success=True,
            started_at=start_time,
            completed_at=end_time,
            actual={
                "latency_ms": actual_latency,
                "energy_j": actual_energy,
                "cpu_pct": true_state["cpu_pct"],
                "ram_pct": true_state["ram_pct"],
            },
            predicted={},  # Left for orchestrator to fill
            failure_reason=None
        )

    def decay_node_load(self, node: Dict[str, Any], elapsed_seconds: float):
        """Simulates task completion decay over time."""
        decay_factor = max(0.0, 1.0 - (0.2 * elapsed_seconds))
        node["true_state"]["cpu_pct"] = max(5.0, node["true_state"]["cpu_pct"] * decay_factor)
        node["true_state"]["ram_pct"] = max(10.0, node["true_state"]["ram_pct"] * decay_factor)
        node["true_state"]["queue_length"] = max(0, int(node["true_state"]["queue_length"] * decay_factor))