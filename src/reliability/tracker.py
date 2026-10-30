"""Reliability tracker for edge nodes in ARRRO."""

from datetime import datetime, timezone
from typing import ClassVar

import numpy as np

from src.common.schemas import (
    ExecutionResult,
    ReliabilityEstimate,
    ResourceReport,
    ResourceScore,
)
from src.reliability.signals import (
    calculate_cross_resource_inconsistency,
    calculate_relative_error,
    calculate_staleness,
    calculate_temporal_instability,
)


class ReliabilityTracker:
    """Tracks and computes reliability and uncertainty estimates per node."""

    KEY_MAPPING: ClassVar[dict[str, str]] = {
        "cpu_pct": "cpu",
        "ram_pct": "ram",
        "bandwidth_mbps": "bandwidth",
        "latency_ms": "latency",
        "queue_length": "queue_length",
    }

    FEEDBACK_MAPPING: ClassVar[dict[str, str]] = {
        "latency_ms": "latency",
        "latency": "latency",
        "cpu_pct": "cpu",
        "cpu": "cpu",
        "ram_pct": "ram",
        "ram": "ram",
        "bandwidth_mbps": "bandwidth",
        "bandwidth": "bandwidth",
    }

    def __init__(
        self,
        history_window: int = 10,
        recent_error_window: int = 3,
        use_feedback: bool = True,
        constant_reliability: bool = False,
    ) -> None:
        self.history_window = history_window
        self.recent_error_window = recent_error_window
        self.use_feedback = use_feedback
        self.constant_reliability = constant_reliability

        # State storage: {node_id: {key: [...]}}
        self.value_history: dict[str, dict[str, list[float]]] = {}
        self.error_history: dict[str, dict[str, list[float]]] = {}
        self.last_reliability: dict[str, dict[str, float]] = {}

        # Signal weights
        self.weights = {
            "staleness": 0.45,
            "history_error": 0.25,
            "temporal_instability": 0.15,
            "cross_resource_inconsistency": 0.15,
        }

    def _init_node_storage(self, node_id: str, resource_keys: list[str]) -> None:
        if node_id not in self.value_history:
            self.value_history[node_id] = {r: [] for r in resource_keys}
            self.error_history[node_id] = {r: [] for r in resource_keys}
            self.last_reliability[node_id] = {}
        else:
            for r in resource_keys:
                self.value_history[node_id].setdefault(r, [])
                self.error_history[node_id].setdefault(r, [])

    def process_report(
        self, report: ResourceReport, current_time_str: str | None = None
    ) -> ReliabilityEstimate:
        """Processes an incoming ResourceReport and produces a contract-compliant ReliabilityEstimate."""
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

        canonical_keys = ["cpu", "ram", "bandwidth", "latency", "queue_length"]
        self._init_node_storage(node_id, canonical_keys)

        if self.constant_reliability:
            res_scores = {
                k: ResourceScore(reliability=0.8, uncertainty=0.2)
                for k in canonical_keys
            }
            return ReliabilityEstimate(
                timestamp=now_str,
                node_id=node_id,
                resources=res_scores,
                signals={},
            )

        cross_inconsistency = calculate_cross_resource_inconsistency(res_data)
        staleness = calculate_staleness(str(reported_at), now_str)

        resource_scores: dict[str, ResourceScore] = {}
        resource_signals: dict[str, dict[str, float]] = {}

        for raw_k, short_k in self.KEY_MAPPING.items():
            if raw_k not in res_data:
                continue

            val = float(res_data[raw_k])

            hist = self.value_history[node_id][short_k]
            hist.append(val)
            if len(hist) > self.history_window:
                hist.pop(0)

            temporal = calculate_temporal_instability(hist)

            err_hist = self.error_history[node_id][short_k]
            hist_err = float(np.mean(err_hist)) if err_hist else 0.0
            recent_err = (
                float(np.mean(err_hist[-self.recent_error_window :]))
                if err_hist
                else 0.0
            )

            # Cold start: sparsity ratio
            history_len = len(hist)
            sparsity = max(0.0, 1.0 - (history_len / self.history_window))

            # Target instantaneous reliability
            penalty = (
                self.weights["staleness"] * staleness
                + self.weights["history_error"] * hist_err
                + self.weights["temporal_instability"] * temporal
                + self.weights["cross_resource_inconsistency"] * cross_inconsistency
            )
            raw_target_rel = max(0.0, min(1.0, 1.0 - penalty))

            # Smoothing
            if short_k not in self.last_reliability[node_id]:
                # Cold start assignment
                smoothed_rel = raw_target_rel
            else:
                prev_rel = self.last_reliability[node_id][short_k]
                if raw_target_rel < prev_rel:
                    # Quick drop on degradation
                    smoothed_rel = max(raw_target_rel, prev_rel - 0.35)
                else:
                    # Smooth recovery
                    smoothed_rel = min(raw_target_rel, prev_rel + 0.10)

            self.last_reliability[node_id][short_k] = smoothed_rel

            # Uncertainty rises with sparsity (cold-start), staleness, temporal volatility, and recent errors
            uncert_raw = (
                0.65 * sparsity
                + 0.15 * staleness
                + 0.10 * temporal
                + 0.10 * recent_err
            )
            uncertainty = max(0.05, min(1.0, float(uncert_raw)))

            resource_scores[short_k] = ResourceScore(
                reliability=float(round(smoothed_rel, 4)),
                uncertainty=float(round(uncertainty, 4)),
            )
            resource_signals[short_k] = {
                "staleness": float(round(staleness, 4)),
                "history_error": float(round(hist_err, 4)),
                "temporal_instability": float(round(temporal, 4)),
                "cross_resource_inconsistency": float(round(cross_inconsistency, 4)),
            }

        return ReliabilityEstimate(
            timestamp=now_str,
            node_id=node_id,
            resources=resource_scores,
            signals=resource_signals,
        )

    def process_execution_feedback(self, feedback: ExecutionResult) -> None:
        """Processes execution feedback and updates per-resource prediction error history."""
        if not self.use_feedback:
            return

        node_id = feedback.node_id
        if not feedback.actual or not feedback.predicted:
            return

        for act_k, act_val in feedback.actual.items():
            short_k = self.FEEDBACK_MAPPING.get(act_k)
            keys_to_update = {act_k}
            if short_k:
                keys_to_update.add(short_k)

            self._init_node_storage(node_id, list(keys_to_update))

            pred_val = None
            if act_k in feedback.predicted:
                pred_val = feedback.predicted[act_k]
            elif short_k and short_k in feedback.predicted:
                pred_val = feedback.predicted[short_k]

            if pred_val is not None:
                rel_err = calculate_relative_error(float(act_val), float(pred_val))
                for target_key in keys_to_update:
                    err_hist = self.error_history[node_id][target_key]
                    err_hist.append(rel_err)
                    if len(err_hist) > self.history_window:
                        err_hist.pop(0)

    # Alias for backward compatibility
    record_feedback = process_execution_feedback