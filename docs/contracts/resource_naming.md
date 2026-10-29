# Contract Note: Resource Naming and Boundary Mapping (Phase II Gate 1)

## 1. Context & Motivation
Different modules in the pipeline historically used conflicting key formats (unit-suffixed names vs. simplified metric names). To preserve compatibility with the core integration contract while keeping simulation realistic, boundary responsibilities are established as follows.

## 2. Layer Specifications
- **Layer 1 (Simulation - Yuvarani):**
  - Generates `ResourceReport` and `Task` using unit-suffixed metric names:
    - `cpu_pct` (Float, % capacity or utilization)
    - `ram_pct` (Float, % capacity or utilization)
    - `bandwidth_mbps` (Float, Available bandwidth in Mbps)
    - `latency_ms` (Float, Latency in milliseconds)
    - `queue_length` (Integer, Pending task count)

- **Layer 2 (Reliability Tracker - Prerana):**
  - Receives `ResourceReport` (with unit-suffixed keys).
  - Emits `ReliabilityEstimate.resources` with short canonical keys:
    - `cpu`
    - `ram`
    - `bandwidth`
    - `latency`
    - `queue_length`
  - *Internal Mapping Rule:* The tracker maps:
    - `cpu_pct` -> `cpu`
    - `ram_pct` -> `ram`
    - `bandwidth_mbps` -> `bandwidth`
    - `latency_ms` -> `latency`
    - `queue_length` -> `queue_length`

- **Layer 3 (Scheduler - Prathiksha):**
  - Consumes `ReliabilityEstimate.resources` using the short keys directly (`cpu`, `ram`, `bandwidth`, `latency`, `queue_length`).
  - Evaluates task requirements using task weights matching the short keys.

## 3. Sign-off
- Gate 1 Status: AGREED & LOCKED