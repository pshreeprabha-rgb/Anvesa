def execute_task(node, task):
    if getattr(node, "is_failed", False):
        return "FAILED - node unavailable"

    if node.cpu < task.cpu_required:
        return "FAILED - insufficient CPU"

    if node.ram < task.ram_required:
        return "FAILED - insufficient RAM"

    if node.bandwidth < task.bandwidth_required:
        return "FAILED - insufficient bandwidth"

    return "SUCCESS"