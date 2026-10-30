import random
from typing import Any


class UnreliabilityInjector:
    def __init__(
        self,
        level: float = 0.0,
        stale_ratio: float = 0.5,
        manipulation_ratio: float = 0.5,
    ):
        """
        level: probability that a report is unreliable (0.0 to 0.4)
        stale_ratio / manipulation_ratio: mix between the two failure modes
        """
        self.level = level
        self.stale_ratio = stale_ratio
        self.manipulation_ratio = manipulation_ratio
        self.stale_cache: dict[str, dict[str, Any]] = {}
    def apply(
        self, node_id: str, resources: dict[str, Any], rng: random.Random
    ) -> dict[str, Any]:
        if rng.random() > self.level:
            self.stale_cache[node_id] = resources.copy()
            return resources
        mode = rng.choices(
            ["stale", "manipulation"],
            weights=[self.stale_ratio, self.manipulation_ratio],
        )[0]
        if mode == "stale" and node_id in self.stale_cache:
            # Stale report keeps the older timestamp from the cached copy
            return self.stale_cache[node_id].copy()
        # Manipulation: report deceptively healthy numbers
        manipulated = resources.copy()
        manipulated["cpu_pct"] = max(5.0, manipulated["cpu_pct"] * 0.3)
        manipulated["latency_ms"] = max(10.0, manipulated["latency_ms"] * 0.4)
        manipulated["queue_length"] = 0
        return manipulated