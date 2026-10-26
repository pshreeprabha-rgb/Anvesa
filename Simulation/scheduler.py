
def find_node_for_task(nodes, task):

    for node in nodes:
        if getattr(node, "is_failed", False):
            continue

        if (
            node.cpu >= task.cpu_required
            and node.ram >= task.ram_required
            and node.bandwidth >= task.bandwidth_required
        ):
            return node

    return None


def find_node_from_reports(reports, nodes, task):

    for report in reports:
        if report.can_handle_task(task):

            for node in nodes:
                if node.node_id != report.node_id:
                    continue

                if getattr(node, "is_failed", False):
                    break

                return node

    return None
