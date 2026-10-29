"""Signal calculation functions for ARRRO reliability tracking."""

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
    except ValueError:
        return 1.0

    return min(1.0, age / max_age_sec)


def calculate_relative_error(
    actual: float, predicted: float, epsilon: float = 1e-6
) -> float:
    """Calculates normalized relative prediction error bounded in [0.0, 1.0]."""
    denom = max(abs(actual), epsilon)
    err = abs(actual - predicted) / denom
    return min(1.0, float(err))


def calculate_temporal_instability(recent_values: list[float]) -> float:
    """Calculates variance/instability of recent reports normalized to [0.0, 1.0]."""
    if len(recent_values) < 2:
        return 0.0

    arr = np.array(recent_values, dtype=float)
    std = float(np.std(arr))
    mean = float(np.mean(arr))
    cv = std / (abs(mean) + 1e-6)
    return min(1.0, cv)
