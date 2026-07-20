# PRANA Demo Failure Matrix

## Purpose

Failure scenarios during PRANA demos and defensive responses. Documents what failures mean and what they don't mean.

---

## Failure Categories

1. **Signal Collection** - Signals unavailable or corrupted
2. **State Engine** - State derivation fails
3. **Packet Construction** - Packet cannot be built
4. **Transmission** - Packet cannot reach Bucket
5. **Replay** - Historical packets unavailable

---

## Signal Collection Failures

### SIG-001: Signal Collection Unavailable
**What happens:** Cannot collect signals (event listeners fail).

**Response:** "PRANA emits IDLE and continues. No application impact."

**Does NOT mean:** System broken, user inactive, policy violation, surveillance disabled.

**Safety:** Fail-open, non-blocking, no retry.

---

### SIG-002: Signal Corruption
**What happens:** Signals corrupted or invalid.

**Response:** "PRANA discards corrupted signals, emits IDLE, continues."

**Does NOT mean:** Data integrity issue, security breach, user tampering, system compromise.

**Safety:** Fail-open, non-blocking, no retry.

---

### SIG-003: Signal Overload
**What happens:** Too many signals to process.

**Response:** "PRANA processes up to capacity, drops excess, continues."

**Does NOT mean:** User misbehaving, system under attack, performance degradation, critical data loss.

**Safety:** Fail-open, non-blocking, graceful degradation.

---

## State Engine Failures

### ENG-001: State Evaluation Exception
**What happens:** Exception during state evaluation.

**Response:** "PRANA catches exception, emits IDLE, continues."

**Does NOT mean:** State logic broken, user state unknown, policy evaluation failed, system compromised.

**Safety:** Fail-open, non-blocking, no retry.

---

### ENG-002: State Transition Logic Failure
**What happens:** State transition logic fails.

**Response:** "PRANA falls back to IDLE, continues."

**Does NOT mean:** User behavior unclassifiable, state machine broken, cognitive state unknown, policy compliance uncertain.

**Safety:** Fail-open, non-blocking, safe fallback.

---

## Packet Construction Failures

### PKT-001: Packet Construction Exception
**What happens:** Exception during packet construction.

**Response:** "PRANA skips packet, continues to next window."

**Does NOT mean:** Data lost, telemetry incomplete, system broken, user activity unrecorded.

**Safety:** Fail-open, non-blocking, no retry.

---

### PKT-002: Packet Serialization Failure
**What happens:** Packet cannot be serialized to JSON.

**Response:** "PRANA skips packet, continues."

**Does NOT mean:** Schema broken, data invalid, contract violation, system incompatibility.

**Safety:** Fail-open, non-blocking, no retry.

---

### PKT-003: Packet Size Limit Exceeded
**What happens:** Packet exceeds size limits.

**Response:** "PRANA truncates or skips packet, continues."

**Does NOT mean:** User generating excessive signals, system misbehaving, data critical, telemetry incomplete.

**Safety:** Fail-open, non-blocking, graceful degradation.

---

## Transmission Failures

### BKT-001: Bucket Endpoint Unavailable
**What happens:** Bucket endpoint unreachable.

**Response:** "PRANA attempts once, discards packet on failure, continues."

**Does NOT mean:** Network broken, Bucket down, data lost, telemetry critical.

**Safety:** Single attempt, no retry, fail-open.

---

### BKT-002: Bucket Authentication Failure
**What happens:** Authentication to Bucket fails.

**Response:** "PRANA discards packet, continues, no retry."

**Does NOT mean:** Credentials invalid, security breach, access unauthorized, system compromised.

**Safety:** Fail-open, non-blocking, no retry.

---

### BKT-003: Bucket Rate Limit Exceeded
**What happens:** Bucket rate limit exceeded.

**Response:** "PRANA discards packet, continues, no backoff."

**Does NOT mean:** System overloaded, user generating too much data, telemetry excessive, Bucket misconfigured.

**Safety:** Fail-open, non-blocking, no backoff.

---

### BKT-004: Bucket Storage Full
**What happens:** Bucket storage full.

**Response:** "PRANA discards packet, continues."

**Does NOT mean:** Data critical, storage misconfigured, system broken, telemetry lost.

**Safety:** Fail-open, non-blocking, no retry.

---

## Replay Failures

### REP-001: Packets Missing from Storage
**What happens:** Historical packets missing.

**Response:** "Replay fails gracefully, read-only access incomplete."

**Does NOT mean:** Data deleted, storage corrupted, telemetry incomplete, historical access invalid.

**Safety:** Fail-open, graceful degradation.

---

### REP-002: Packets Corrupted in Storage
**What happens:** Historical packets corrupted.

**Response:** "Replay skips corrupted packets, continues with available data."

**Does NOT mean:** Storage compromised, data integrity broken, historical access invalid, system broken.

**Safety:** Fail-open, graceful degradation.

---

## Failure Handling Principles

- **Fail-open:** All failures → Silent cessation. No application impact.
- **Non-blocking:** Failures do not block application operations.
- **No retry storms:** Single attempt only. No retries, backoff, or queues.
- **No authority:** PRANA does not request changes from other systems.
- **Non-authority:** Failures are operational events, not diagnostic events.

---

## Demo Defense Responses

**"What if signals fail?"**  
"PRANA emits IDLE and continues. No application impact. Fail-open design."

**"What if packets are lost?"**  
"PRANA discards failed packets and continues. Telemetry is non-critical. Fail-open ensures no application impact."

**"What if Bucket is down?"**  
"PRANA attempts once, discards on failure, continues. No retry storms. Bucket has full authority."

**"What if replay fails?"**  
"Replay fails gracefully. Historical read-only access incomplete, but current operation continues. Fail-open design."

**"Do failures indicate problems?"**  
"Failures are operational events, not diagnostic events. Do not indicate system problems, user problems, or policy violations."

---

## Summary

PRANA failures are **operational events, not diagnostic events**:
- All failures result in fail-open behavior
- No application impact
- No retry storms
- No authority over other systems
- Failures do not indicate problems or violations
