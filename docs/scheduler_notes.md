# ARRRO — Vector Scheduler Experiment Notes

## 1. Project Overview

**Project:** Adaptive Resource Reliability and Risk-Aware Task Offloading in Edge Computing (ARRRO)

**My role:** Vector — Risk-Aware Offloading and Scheduler Engineer

**Objective:** Select a feasible edge node by considering estimated performance cost and task-specific decision risk.

## 2. Current Implementation

The scheduler currently includes:

- Feasibility filtering based on CPU, RAM, bandwidth and latency requirements.
- Task-specific risk calculation using resource weights and uncertainty estimates.
- Performance-cost calculation using configurable weights.
- Combined objective:

  `objective = performance_cost + lambda_value * decision_risk`

- Risk-limit filtering and a lowest-risk fallback when no feasible candidate meets the risk limit.
- Configurable risk limit, lambda value and performance weights in `scheduler_config.json`.
- Sample inputs separated into `demo_inputs.py`.

## 3. Initial Experimental Setup

The current experiment uses three illustrative edge nodes: A, B and C.

Node C is rejected because it does not satisfy the task's bandwidth and latency requirements.

Nodes A and B are feasible.

**Important:** These inputs are simulated examples, not measurements from a real edge network.

## 4. Risk-Limit Experiment

| Risk limit | Selected node | Status |
|---|---|---|
| 0.20 | A | RISK_LIMIT_MET |
| 0.10 | B | RISK_LIMIT_MET |
| 0.05 | B | RISK_LIMIT_UNMET |

### Observation

A stricter risk limit excludes Node A at 0.10 because its estimated risk is 0.185. Node B has estimated risk 0.0675 and remains eligible.

At 0.05, neither feasible node meets the limit. The scheduler selects B as the lowest-risk fallback and explicitly reports that the limit is unmet.

## 5. Lambda Experiment

| Lambda | Selected node |
|---|---|
| 0 | A |
| 50 | A |
| 100 | A |
| 200 | B |

### Observation

Lambda controls how strongly the objective penalizes estimated decision risk.

Node A has a lower performance cost (20.45) but higher estimated risk (0.185). Node B has a higher performance cost (32.90) but lower estimated risk (0.0675).

At lambda 200, the risk penalty is large enough to make Node B the preferred candidate.

## 6. Initial Automated Testing

Command:

`python -m unittest -v test_scheduler.py`

**Result:** 6
## Latest Verification

- Automated tests: 8 passed.
- Standalone scheduler execution: successful.
- Default configuration: Node A selected; risk limit met.
- Risk-limit experiment: tighter limits change the selected node and explicitly report when the limit cannot be met.
- Lambda experiment: increasing the risk penalty to 200 changes the selected node from A to B.
- Input validation: rejects out-of-range CPU/RAM requirements and negative bandwidth/latency requirements.
- Missing reliability data: raises a clear `ValueError`.

**Limitations:** Results use illustrative input data. Model weights and risk estimates have not yet been validated against real measurements. These results demonstrate implementation behaviour, not real-world effectiveness.