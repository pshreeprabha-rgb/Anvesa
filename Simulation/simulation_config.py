
from dataclasses import dataclass


@dataclass
class SimulationConfig:
    number_of_trials: int = 20
    number_of_nodes: int = 10
    number_of_tasks: int = 5
    noise_percentage: float = 10.0
    random_seed: int = 42
