from datetime import datetime
import numpy as np
from typing import List

def calculate_staleness(reported_at_str: str, current_time_str: str, max_age_sec: float = 30.0) -> float:
    """Calculates report age and normalizes staleness to [0.0, 1.0]."""
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    try:
        t_rep = datetime.strptime(reported_at_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
        t_curr = datetime.strptime(current_time_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
        age = max(0.0, (t_curr - t_rep).total_seconds())
    except ValueError:
        age = 0.0

    staleness = age / max_age_sec
    return float(np.clip(staleness, 0.0, 1.0))


def calculate_relative_error(predicted: float, actual: float) -> float:
    """Calculates normalized error between predicted/reported value and ground-truth actual outcome."""
    if predicted == 0.0 and actual == 0.0:
        return 0.0
    denom = max(abs(predicted), abs(actual), 1.0)
    error = abs(predicted - actual) / denom
    return float(np.clip(error, 0.0, 1.0))


def calculate_temporal_instability(recent_values: List[float]) -> float:
    """Calculates variance/instability of recent reports normalized to [0.0, 1.0]."""
    if len(recent_values) < 2:
        return 0.0
    std_dev = float(np.std(recent_values))
    mean_val = float(np.mean(recent_values))
    if mean_val == 0.0:
        return 0.0
    coef_var = std_dev / abs(mean_val)
    return float(np.clip(coef_var, 0.0, 1.0))