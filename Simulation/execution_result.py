
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    task_id: str
    node_id: str | None
    success: bool
    failure_reason: str | None = None
    actual_cpu: float | None = None
    actual_ram: float | None = None
    actual_bandwidth: float | None = None
    started_at: float | None = None
    completed_at: float | None = None
