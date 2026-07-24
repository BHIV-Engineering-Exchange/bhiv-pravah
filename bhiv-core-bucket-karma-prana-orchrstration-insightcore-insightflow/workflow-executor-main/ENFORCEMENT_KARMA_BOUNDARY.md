# Enforcement ↔ Karma Boundary

## Purpose

Define a strict, non-negotiable boundary between:

- **Enforcement** → the authoritative execution gate  
- **Karma** → an observational, analytical layer

Karma may observe execution truth.  
Karma must never influence execution authority.

This document ensures Karma can integrate safely without gaining
control, introducing dependencies, or destabilizing live demos.

---

## 1. What Enforcement Emits (Observable Surface)

Enforcement emits structured, append-only execution events for
observability and audit.

Each event may include fields such as:

- `trace_id`
- `action_type`
- `adapter`
- `status` (success / failed)
- `error_code` (if failure)
- `product`
- `timestamp`

Properties of these emissions:

- Generated after or during execution decisions
- Side-channel only (telemetry/log stream)
- Not read back by Enforcement
- Not required for execution to proceed
- Safe to ignore without changing behavior

These events represent **recorded truth**, not control signals.

Flow:
**Enforcement** → (non-blocking events) → **Karma**

There is no reverse path.

---

## 2. What Karma May Do

Karma is allowed to:

- Subscribe to and read emitted execution events
- Perform analytics, scoring, trend detection, or reputation models
- Store its own derived or aggregated data in its own storage
- Produce reports, dashboards, or offline insights

Karma operates entirely out-of-band from execution.

Karma may never assume that:
- events are complete
- events are ordered
- events are guaranteed to arrive

Karma must tolerate loss, delay, or duplication of events.

---

## 3. What Karma Must Never Do

Karma is strictly prohibited from:

- Allowing or blocking any execution
- Triggering retries, replays, or compensations
- Injecting or modifying decisions
- Writing to the execution path
- Writing to or mutating Bucket records
- Requesting schema or contract changes in Enforcement
- Becoming a required runtime dependency for Enforcement startup

Karma has:
- no API to call back into Enforcement for control
- no channel to alter requests, payloads, or outcomes

If Karma is:
- offline
- delayed
- overloaded
- returning incorrect analytics

then Enforcement behavior is completely unchanged.

---

## 4. Authority Guarantee

Execution authority is fully contained inside Enforcement.

Allow/block decisions are computed only from:
- the inbound request
- internal deterministic evaluators

No external observational system, including Karma, participates in
decision computation.

There is:
- no feedback loop
- no corrective loop
- no advisory loop

Integration is strictly one-way:
`Intent → Enforcement → Execution → Events → Karma`
**→ (stops here)**

Truth flows forward and is recorded.  
Authority never flows backward.

---

## 5. Dependency and Failure Safety

Karma is an optional consumer.

If Karma is removed entirely:

- Enforcement starts normally
- Enforcement processes requests normally
- Execution determinism is identical
- No errors or retries are introduced

Event emission is:

- asynchronous
- non-blocking
- best-effort

Telemetry failure must never fail execution.

---

## Final Boundary Lock

**Karma observes execution truth but cannot influence execution authority.**
