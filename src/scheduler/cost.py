from src.scheduler.performance_model import calculate_performance_cost


def calculate_cost(node, performance_weights):
    return calculate_performance_cost(node, performance_weights)