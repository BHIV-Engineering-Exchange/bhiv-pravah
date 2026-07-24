# Karma & Prana Demo Boundary

## Purpose

Define exactly how Karma and Prana are represented in internal and public demos without creating any impression that they influence execution authority.

Karma and Prana are **observational layers only**.

They are never execution gates.

---

## 1. What CAN Be Shown in Demo

It is safe to demonstrate that:

- Execution events are emitted with:
  - `trace_id`
  - `action_type`
  - `adapter`
  - `status`
  - `timestamp`

- Karma and/or Prana dashboards can:
  - display execution history
  - compute analytics or trends
  - visualize system behaviour

- Observers update in near-real-time as workflows run.

This proves:
> Execution is observable and auditable.

---

## 2. What MUST NOT Be Shown or Implied

Never show or suggest that Karma or Prana can:

- block or allow execution
- trigger retries
- modify payloads
- change adapter choice
- alter Enforcement decisions
- write back into Core or Executor

Do NOT demo any UI control that appears to “approve”, “deny”, or “re-run” execution.

No buttons, toggles, or actions from Karma/Prana may affect live workflows.

---

## 3. Safe Failure Demonstration

If demonstrating failure:

- Show that execution still returns a clear success/failure response.
- Show that observers may lag or be unavailable.
- Emphasize that execution result is unchanged.

Narrative to use:

> “Even if observability is down, execution continues deterministically and safely.”

---

## 4. Explicit Non-Authority Statement (to say in demos)

Use wording equivalent to:

> “Karma and Prana can see what happened, but they cannot change what happens.”

This reinforces separation between:
- Authority (Core + Enforcement)
- Action (Executor)
- Observation (Karma / Prana)

---

## 5. Red Lines for Live Demo

During live demos, never:

- disable Enforcement and let observers drive execution
- replay events from observers into the executor
- modify execution based on observer metrics
- claim optimisation or self-correction via Karma/Prana

Any such behaviour would violate sovereign execution boundaries.

---

## 6. Correct Demo Story

1. Core issues a workflow.
2. Enforcement authorizes or blocks.
3. Executor performs the action.
4. An immutable event is emitted.
5. Karma/Prana display and analyse that event.

Order is strict and irreversible.

Observers are the **last step**, not a control step.

---

## Final Rule

In every demo and explanation:

> Karma and Prana may observe everything  
> but they may command nothing.
