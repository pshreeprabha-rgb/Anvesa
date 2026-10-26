
from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionResult:
    task_id: str
    node_id: Optional[str]
    success: bool
    failure_reason: Optional[str] = None
    actual_cpu: Optional[float] = None
    actual_ram: Optional[float] = None
    actual_bandwidth: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
