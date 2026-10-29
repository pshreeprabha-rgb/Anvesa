"""Signal calculation functions for ARRRO reliability tracking."""

import math
from datetime import datetime, timezone

import numpy as np


def calculate_staleness(
    reported_at_str: str, current_time_str: str, max_age_sec: float = 30.0
) -> float:
    """Calculates report age and normalizes staleness to [0.0, 1.0]."""
    try:
        t_rep = datetime.strptime(
            reported_at_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S"
        ).replace(tzinfo=timezone.utc)
        t_curr = datetime.strptime(
            current_time_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S"
        ).replace(tzinfo=timezone.utc)
        age = max(0.0, (t_curr - t_rep).total_seconds())
    except (ValueError, AttributeError, TypeError):
        return 1.0

    return min(1.0, max(0.0, age / max_age_sec))


def calculate_relative_error(
    actual: float, predicted: float, epsilon: float = 1e-6
) -> float:
    """Calculates normalized relative prediction error bounded in [0.0, 1.0]."""
    if math.isnan(actual) or math.isnan(predicted):
        return 1.0
    denom = max(abs(actual), epsilon)
    err = abs(actual - predicted) / denom
    return min(1.0, max(0.0, float(err)))


def calculate_temporal_instability(recent_values: list[float]) -> float:
    """Calculates coefficient of variation of recent reports normalized to [0.0, 1.0]."""
    clean_vals = [v for v in recent_values if not math.isnan(v)]
    if len(clean_vals) < 2:
        return 0.0

    arr = np.array(clean_vals, dtype=float)
    std = float(np.std(arr))
    mean = float(np.mean(arr))
    cv = std / (abs(mean) + 1e-6)
    return min(1.0, max(0.0, cv))


def calculate_cross_resource_inconsistency(res_data: dict[str, float | int]) -> float:
    """
    Computes heuristic inconsistency between related resource metrics.
    Returns a score normalized in [0.0, 1.0].
    """
    violations = 0
    total_checks = 3

    cpu = float(res_data.get("cpu_pct", res_data.get("cpu", 0.0)))
    latency = float(res_data.get("latency_ms", res_data.get("latency", 0.0)))
    bandwidth = float(res_data.get("bandwidth_mbps", res_data.get("bandwidth", 100.0)))
    queue = int(res_data.get("queue_length", 0))

    # Rule 1: Negligible bandwidth reported with unrealistically low latency (< 2ms)
    if bandwidth < 1.0 and latency < 2.0:
        violations += 1

    # Rule 2: Near max CPU utilization reported alongside an empty queue
    if cpu > 90.0 and queue == 0:
        violations += 1

    # Rule 3: Idle CPU reported with a heavily backed-up queue
    if cpu < 5.0 and queue > 10:
        violations += 1

    return float(violations / total_checks)