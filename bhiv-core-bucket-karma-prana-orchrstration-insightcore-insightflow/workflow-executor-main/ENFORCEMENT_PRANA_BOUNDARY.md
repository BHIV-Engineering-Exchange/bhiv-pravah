# Enforcement ↔ Prana Boundary

## Purpose

Define a strict boundary between:

- **Enforcement** → the sole execution authority
- **Prana** → a real-time observational and monitoring layer

Prana may observe execution flow and timing signals.  
Prana must never influence, gate, delay, or modify execution.

This guarantees that adding or removing Prana cannot change system
behavior.

---

## 1. What Prana May Observe

Prana may subscribe to lightweight runtime signals such as:

- execution started
- execution completed
- execution duration
- adapter selected
- success or failure status
- trace_id and timestamps

These signals are emitted as non-blocking telemetry events.

They exist to support:

- monitoring
- dashboards
- health tracking
- latency measurement
- alerting

They are not inputs to execution logic.

Flow:
**Enforcement** → (async signals) → **Prana**

There is no reverse path.

---

## 2. What Prana Must Never Do

Prana is strictly forbidden from:

- Allowing or blocking any workflow
- Delaying execution while waiting for monitoring
- Triggering retries or replays
- Modifying payloads or results
- Injecting new execution requests
- Writing to Bucket
- Becoming a required dependency for Enforcement startup or runtime

Execution must never wait for Prana.

If Prana is slow, down, or disconnected,
execution continues without degradation.

---

## 3. No Gating, No Feedback, No Control Loop

Prana cannot sit “in front of” execution.

It cannot:

- approve before execution
- veto after execution
- request re-evaluation
- feed signals back into Enforcement

There is no control loop such as:

`Execution → Prana → Enforcement` (blocked)


The only valid topology is:

`Intent → Enforcement → Execution → Signals → Prana`
**→ (stops here)**

Signals are observational only.

---

## 4. Absence Safety Guarantee

If Prana is:

- not deployed
- temporarily offline
- permanently removed
- returning malformed or delayed data

then:

- Enforcement decisions are identical
- Execution ordering is identical
- Success and failure outcomes are identical
- No retries or compensations are triggered

Prana absence has zero behavioral effect.

---

## 5. Non-Blocking Emission Contract

Telemetry emission to Prana must be:

- asynchronous
- fire-and-forget
- exception-isolated

Any emission failure must be swallowed and logged,
never propagated to the execution path.

Execution correctness has priority over observability.

---

## Final Boundary Lock

**Prana observes live execution signals but cannot gate, delay, or alter execution.**
