"""Reliability tracker for edge nodes in ARRRO."""

from datetime import datetime, timezone

import numpy as np

from src.common.schemas import (
    ExecutionResult,
    ReliabilityEstimate,
    ResourceReport,
    ResourceScore,
)
from src.reliability.signals import (
    calculate_relative_error,
    calculate_staleness,
    calculate_temporal_instability,
)


class ReliabilityTracker:
    """Tracks and computes reliability scores and estimates per node."""

    def __init__(self, history_window: int = 5) -> None:
        self.history_window = history_window
        self.value_history: dict[str, dict[str, list[float]]] = {}
        self.error_history: dict[str, dict[str, list[float]]] = {}

        self.weights = {
            "staleness": 0.4,
            "prediction_error": 0.4,
            "temporal_instability": 0.2,
        }

    def _init_node_storage(self, node_id: str, resource_keys: list[str]) -> None:
        if node_id not in self.value_history:
            self.value_history[node_id] = {r: [] for r in resource_keys}
            self.error_history[node_id] = {r: [] for r in resource_keys}
        else:
            for r in resource_keys:
                self.value_history[node_id].setdefault(r, [])
                self.error_history[node_id].setdefault(r, [])

    def process_report(
        self, report: ResourceReport, current_time_str: str | None = None
    ) -> ReliabilityEstimate:
        """Processes an incoming ResourceReport and produces a ReliabilityEstimate."""
        node_id = report.node_id
        res_data = (
            report.resources.model_dump()
            if hasattr(report.resources, "model_dump")
            else dict(report.resources)
        )

        reported_at = res_data.get("reported_at", report.timestamp)
        now_str = (
            current_time_str
            if current_time_str
            else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        res_keys = [
            k
            for k in res_data
            if k != "reported_at" and isinstance(res_data[k], (int, float))
        ]
        self._init_node_storage(node_id, res_keys)

        key_mapping = {
            "cpu_pct": "cpu",
            "ram_pct": "ram",
            "bandwidth_mbps": "bandwidth",
            "latency_ms": "latency",
            "queue_length": "queue_length",
        }
        resource_scores: dict[str, ResourceScore] = {}
        resource_signals: dict[str, dict[str, float]] = {}

        for k in res_keys:
            val = float(res_data[k])
            hist = self.value_history[node_id][k]
            hist.append(val)
            if len(hist) > self.history_window:
                hist.pop(0)

            staleness = calculate_staleness(reported_at, now_str)
            temporal = calculate_temporal_instability(hist)

            err_hist = self.error_history[node_id][k]
            mean_err = float(np.mean(err_hist)) if err_hist else 0.0

            penalty = (
                self.weights["staleness"] * staleness
                + self.weights["prediction_error"] * mean_err
                + self.weights["temporal_instability"] * temporal
            )
            score = max(0.0, min(1.0, 1.0 - penalty))

            # Uncertainty drops as more samples are gathered
            uncertainty = max(0.05, 1.0 - (len(hist) / self.history_window))

            short_key = key_mapping.get(k, k)
            resource_scores[short_key] = ResourceScore(
                reliability=score,
                uncertainty=uncertainty,
            )
            resource_signals[short_key] = {
                "staleness": float(staleness),
                "prediction_error": mean_err,
                "temporal_instability": float(temporal),
            }

        return ReliabilityEstimate(
            timestamp=now_str,
            node_id=node_id,
            resources=resource_scores,
            signals=resource_signals,
        )

    def record_feedback(self, feedback: ExecutionResult) -> None:
        """Records ground-truth task execution outcome and updates prediction error."""
        node_id = feedback.node_id
        if not feedback.actual or not feedback.predicted:
            return

        res_keys = list(feedback.actual.keys())
        self._init_node_storage(node_id, res_keys)

        for k, act_val in feedback.actual.items():
            if k in feedback.predicted:
                pred_val = feedback.predicted[k]
                rel_err = calculate_relative_error(float(act_val), float(pred_val))
                err_hist = self.error_history[node_id][k]
                err_hist.append(rel_err)
                if len(err_hist) > self.history_window:
                    err_hist.pop(0)
