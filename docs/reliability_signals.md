# Reliability and Uncertainty Tracker Design Note

## 1. Overview
The `ReliabilityTracker` produces resource-level reliability and uncertainty metrics based on incoming `ResourceReport` data and subsequent `ExecutionResult` ground-truth feedback.

## 2. Resource Signals (Normalized to [0.0, 1.0])
- **Staleness**: Computed as `(current_time - reported_at) / max_age_sec`, capped at 1.0.
- **History Error**: Long-run mean relative prediction error across tasks run on the node.
- **Temporal Instability**: Coefficient of variation ($CV = \sigma / \mu$) calculated across the sliding window of resource values.
- **Cross-Resource Inconsistency**: Logical violations evaluated across resource couplings (low bandwidth with microsecond latency, high CPU with zero queue, or idle CPU with high queue).
- **Recent Prediction Error**: Rolling average error from the last 3 execution feedback reports.

## 3. Smoothing and Asymmetric Recovery
- **Degradation**: Drops by up to 0.35 per evaluation when conditions deteriorate.
- **Recovery**: Recovers gradually at a maximum rate of 0.10 per observation under good behavior.

## 4. Uncertainty Formulation
Uncertainty scales with data sparsity (ensuring high uncertainty during cold start), staleness, volatility, and recent errors:
$$\text{Uncertainty} = 0.65 \cdot \text{Sparsity} + 0.15 \cdot \text{Staleness} + 0.10 \cdot \text{Temporal} + 0.10 \cdot \text{Recent Error}$$