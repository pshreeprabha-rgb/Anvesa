from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class ResourceMetrics(BaseModel):
    cpu_pct: float = Field(ge=0.0, le=100.0)
    ram_pct: float = Field(ge=0.0, le=100.0)
    bandwidth_mbps: float = Field(ge=0.0)
    latency_ms: float = Field(ge=0.0)
    queue_length: int = Field(ge=0)

class ResourceReport(BaseModel):
    schema_version: str = "1.0"
    timestamp: str
    node_id: str
    sequence: int
    resources: Dict[str, float]
    reported_at: str

class ResourceScore(BaseModel):
    reliability: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)

class ReliabilityEstimate(BaseModel):
    schema_version: str = "1.0"
    node_id: str
    timestamp: str
    resources: Dict[str, ResourceScore]
    signals: Dict[str, Dict[str, float]]

class ExecutionResult(BaseModel):
    schema_version: str = "1.0"
    task_id: str
    node_id: str
    success: bool
    actual: Dict[str, float]
    predicted: Dict[str, float]