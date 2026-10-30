from datetime import datetime, timedelta, timezone

EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)
def sim_time_to_iso(t: float) -> str:
    """Simulation seconds -> '2026-01-01T00:00:10Z' (whole seconds)."""
    return (EPOCH + timedelta(seconds=t)).strftime("%Y-%m-%dT%H:%M:%SZ")