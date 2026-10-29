import random
from typing import Dict, Any

class UnreliabilityInjector:
    def __init__(self, level: float = 0.0, stale_ratio: float = 0.5, manipulation_ratio: float = 0.5):
        """
        level: Overall unreliability probability (0.0 to 0.4)
        stale_ratio / manipulation_ratio: Mix proportions
        """
        self.level = level
        self.stale_ratio = stale_ratio
        self.manipulation_ratio = manipulation_ratio
        self.stale_cache: Dict[str, Dict[str, Any]] = {}

    def apply(self, node_id: str, resources: Dict[str, Any], rng: random.Random) -> Dict[str, Any]:
        if rng.random() > self.level:
            self.stale_cache[node_id] = resources.copy()
            return resources

        mode = rng.choices(["stale", "manipulation"], weights=[self.stale_ratio, self.manipulation_ratio])[0]

        if mode == "stale" and node_id in self.stale_cache:
            stale_copy = self.stale_cache[node_id].copy()
            # Stale report retains an older timestamp
            return stale_copy

        # Manipulation: reporting deceptively healthy numbers
        manipulated = resources.copy()
        manipulated["cpu_pct"] = max(5.0, manipulated["cpu_pct"] * 0.3)
        manipulated["latency_ms"] = max(10.0, manipulated["latency_ms"] * 0.4)
        manipulated["queue_length"] = 0
        return manipulated