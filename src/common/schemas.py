from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# Base Schema for Schema Versioning
class BaseContract(BaseModel):
    schema_version: str = "1.0"


# 1. Resource Report (Owner: Member 1 -> Consumed by: Member 2)
class ResourceMetrics(BaseModel):
    cpu_pct: float
    ram_pct: float
    bandwidth_mbps: float
    latency_ms: float
    queue_length: int
    reported_at: str


class ResourceReport(BaseContract):
    timestamp: str
    node_id: str
    sequence: int
    resources: ResourceMetrics


# 2. Task (Consumed by: Member 3)
class TaskRequirements(BaseModel):
    cpu_pct: float
    ram_pct: float
    min_bandwidth_mbps: float
    max_latency_ms: float


class TaskWeights(BaseModel):
    cpu: float
    ram: float
    bandwidth: float
    latency: float


class Task(BaseContract):
    task_id: str
    task_type: str
    arrival_time: str
    requirements: TaskRequirements
    weights: TaskWeights


# 3. Reliability Estimate (Owner: Member 2 -> Consumed by: Member 3)
class ResourceReliability(BaseModel):
    reliability: float
    uncertainty: float


class ReliabilityEstimate(BaseContract):
    node_id: str
    timestamp: str
    resources: Dict[str, ResourceReliability]


# 4. Placement Decision (Owner: Member 3 -> Consumed by: Member 1/4)
class RankedCandidate(BaseModel):
    node_id: str
    objective: float


class PlacementDecision(BaseContract):
    task_id: str
    selected_node: str
    decision_timestamp: str
    performance_cost: float
    decision_risk: float
    lambda_param: float = Field(..., alias="lambda")
    objective: float
    ranked_candidates: List[RankedCandidate]
    reason_codes: List[str]


# 5. Execution Result (Owner: Member 1/Execution -> Consumed by: Member 2)
class ExecutionResult(BaseContract):
    task_id: str
    node_id: str
    started_at: str
    completed_at: str
    success: bool
    actual: Dict[str, float]
    predicted: Dict[str, float]