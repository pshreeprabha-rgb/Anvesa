
import random


def add_noise(value, percentage=10, rng=None):
    if percentage < 0 or percentage > 100:
        raise ValueError("percentage must be between 0 and 100")

    if rng is None:
        rng = random

    noise = value * (percentage / 100)
    return round(rng.uniform(value - noise, value + noise), 2)




def create_stale_report(previous_report, current_time=None, max_age=None):
    """Copy an earlier report and optionally check whether it is stale."""
    from copy import deepcopy

    if previous_report is None:
        raise ValueError("previous_report cannot be None")

    stale_report = deepcopy(previous_report)

    if current_time is not None and max_age is not None:
        if max_age < 0:
            raise ValueError("max_age cannot be negative")

        age = stale_report.age_at(current_time)
        stale_report.is_stale = age > max_age
    else:
        stale_report.is_stale = True

    return stale_report




def manipulate_report(report, reduction_percentage=30):
    """Create a report that understates the node's resources."""
    if not 0 <= reduction_percentage <= 100:
        raise ValueError(
            "reduction_percentage must be between 0 and 100"
        )

    from copy import deepcopy

    manipulated = deepcopy(report)
    factor = 1 - reduction_percentage / 100

    manipulated.cpu = round(manipulated.cpu * factor, 2)
    manipulated.ram = round(manipulated.ram * factor, 2)
    manipulated.bandwidth = round(
        manipulated.bandwidth * factor, 2
    )
    manipulated.is_manipulated = True

    return manipulated
