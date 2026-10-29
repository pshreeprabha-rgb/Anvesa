import numpy as np
from typing import Dict, List
from src.common.schemas import ResourceReport, ReliabilityEstimate, ResourceScore, ExecutionResult
from src.reliability.signals import calculate_staleness, calculate_relative_error, calculate_temporal_instability

class ReliabilityTracker:
    def __init__(self, history_window: int = 5):
        self.history_window = history_window
        # History storage per node and resource
        self.value_history: Dict[str, Dict[str, List[float]]] = {}
        self.error_history: Dict[str, Dict[str, List[float]]] = {}

        # Default signal weights
        self.weights = {
            "w_error": 0.40,
            "w_stale": 0.30,
            "w_instability": 0.30,
            "u_stale": 0.35,
            "u_error": 0.35,
            "u_cold": 0.30
        }

    def _init_node_storage(self, node_id: str, resource_keys: List[str]):
        if node_id not in self.value_history:
            self.value_history[node_id] = {r: [] for r in resource_keys}
            self.error_history[node_id] = {r: [] for r in resource_keys}

    def process_report(self, report: ResourceReport, current_time: str) -> ReliabilityEstimate:
        """Processes a ResourceReport and returns a canonical ReliabilityEstimate."""
        node_id = report.node_id
        resources = report.resources
        self._init_node_storage(node_id, list(resources.keys()))

        resource_scores: Dict[str, ResourceScore] = {}
        signals_breakdown: Dict[str, Dict[str, float]] = {}

        for res_name, res_value in resources.items():
            # Update rolling value history
            v_hist = self.value_history[node_id][res_name]
            v_hist.append(res_value)
            if len(v_hist) > self.history_window:
                v_hist.pop(0)

            # Compute Signals
            staleness = calculate_staleness(report.reported_at, current_time)
            instability = calculate_temporal_instability(v_hist)
            
            err_hist = self.error_history[node_id].get(res_name, [])
            avg_hist_error = float(np.mean(err_hist)) if err_hist else 0.0

            # Calculate History Support (Cold-start mitigation)
            history_support = min(len(err_hist) / self.history_window, 1.0)

            # Calculate Reliability B(i,r,t)
            w = self.weights
            b_val = (
                w["w_error"] * (1.0 - avg_hist_error) +
                w["w_stale"] * (1.0 - staleness) +
                w["w_instability"] * (1.0 - instability)
            )
            reliability = float(np.clip(b_val, 0.0, 1.0))

            # Calculate Uncertainty U(i,r,t)
            u_val = (
                w["u_stale"] * staleness +
                w["u_error"] * avg_hist_error +
                w["u_cold"] * (1.0 - history_support)
            )
            uncertainty = float(np.clip(u_val, 0.0, 1.0))

            resource_scores[res_name] = ResourceScore(
                reliability=round(reliability, 2),
                uncertainty=round(uncertainty, 2)
            )

            signals_breakdown[res_name] = {
                "staleness": round(staleness, 2),
                "temporal_instability": round(instability, 2),
                "history_error": round(avg_hist_error, 2),
                "history_support": round(history_support, 2)
            }

        return ReliabilityEstimate(
            schema_version="1.0",
            node_id=node_id,
            timestamp=current_time,
            resources=resource_scores,
            signals=signals_breakdown
        )

    def process_execution_feedback(self, feedback: ExecutionResult):
        """Updates internal historical error buffers using actual execution feedback."""
        node_id = feedback.node_id
        actuals = feedback.actual
        predicts = feedback.predicted

        self._init_node_storage(node_id, list(actuals.keys()))

        for res_name, actual_val in actuals.items():
            if res_name in predicts:
                pred_val = predicts[res_name]
                err = calculate_relative_error(pred_val, actual_val)
                
                err_buffer = self.error_history[node_id][res_name]
                err_buffer.append(err)
                if len(err_buffer) > self.history_window:
                    err_buffer.pop(0)