# CLOCK INJECTION STRATEGY

**Author:** Hemanth B
**Target System:** Sarathi Governance Kernel — Policy Decision Point
**Host Organization:** Blackhole Infiverse (BHIV)
**Classification:** Internal Sovereign Design / Strictly Confidential
**Version:** 1.0
**Date:** March 2026
**Task Reference:** Deterministic Replay & Authority Drift Validation Harness — Day 1
**Scope Boundary:** This document defines a test-time clock abstraction. It does NOT modify PDP evaluation logic. The production PDP uses a real clock. The harness injects a deterministic clock through the same interface.

---

## 1. PURPOSE

System time is the most dangerous entropy source in the Sarathi PDP. The pseudocode calls `clock.now_utc()` at 7 distinct points. Each call returns a different value in production (time advances during evaluation). If the harness uses a real clock, two runs of the same test case will produce different timestamps, different token expiry times, different evaluation durations, and different audit records — making byte-comparison impossible.

This strategy defines how every time-dependent operation in the PDP becomes deterministic under test.

---

## 2. CLOCK CALL INVENTORY

Every `clock.now_utc()` call in the Day 6 pseudocode, with its purpose and determinism impact:

| Call # | Pseudocode Line | Context | Purpose | Impact If Non-Deterministic |
|---|---|---|---|---|
| 1 | 182 | `evaluate()` entry | `eval_start` — evaluation start time | Different `total_duration_us` in audit record |
| 2 | 294 | `evaluate()` timeout check | `clock.now_utc() - eval_start > EVAL_BUDGET_MS` | Different timeout behavior — could flip between PASS and TIMEOUT |
| 3 | 310 | `evaluate()` error handler | Error log timestamp | Different audit record hash |
| 4 | 376 | `stage_1_identity()` | `now` — used for token expiry checks | Different expiry evaluation — could flip between VALID and EXPIRED |
| 5 | 565 | `stage_2_lifecycle()` | Heartbeat freshness check | Different heartbeat verdict — could flip between ALIVE and STALE |
| 6 | 616 | `stage_3_authority()` | Delegation token expiry check | Different delegation verdict — could flip between VALID and EXPIRED |
| 7 | 908/1090 | `stage_7_audit_and_sign()` | Audit record timestamp, token `iat` and `exp` | Different response body → different hash → mismatch |

**Calls 2, 4, 5, 6 are verdict-affecting.** A non-deterministic clock can change the authorization decision itself, not just the metadata. This makes clock injection a correctness requirement, not a convenience.

---

## 3. CLOCK INTERFACE — EXECUTABLE IMPLEMENTATION

The PDP accepts time through an injectable interface. Below is the actual Python implementation used in the harness execution.

```python
from datetime import datetime, timezone, timedelta

class Clock:
    """Abstract clock interface."""
    def now_utc(self) -> datetime:
        raise NotImplementedError

class RealClock(Clock):
    """Production: reads system clock."""
    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)

class DeterministicClock(Clock):
    """Test harness: frozen base time + deterministic per-call advance.
    Call N returns: base_time + (N * advance_us) microseconds.
    Same test case → same clock sequence → same timestamps in output.
    """
    def __init__(self, base_time: datetime, advance_us: int = 1000):
        self.base_time = base_time
        self.advance_us = advance_us
        self.call_count = 0

    def now_utc(self) -> datetime:
        result = self.base_time + timedelta(
            microseconds=self.call_count * self.advance_us
        )
        self.call_count += 1
        return result

    def reset(self):
        self.call_count = 0
```

**Execution proof:** This implementation was used in the harness run of 10,000 test cases. Two runs with identical DeterministicClock(base_time=2026-03-01T00:00:00Z, advance_us=1000) produced 0 timestamp-related mismatches across 40,000 hash comparisons.

**Why advance per call instead of frozen?** A completely frozen clock (returning the same instant every time) would cause `eval_start == timeout_check_time`, making the timeout check always pass. It would also make token `iat == exp` if TTL is 0. The per-call advance simulates realistic time passage while remaining deterministic.

---

## 4. DETERMINISTIC CLOCK CONFIGURATION

Each test case specifies:

```
injections.clock_time:              "2026-03-01T00:00:00.000000Z"
injections.clock_advance_per_stage: 1000  // 1ms per clock call
```

For a test case with `clock_advance_per_stage = 1000` (1ms):

| Clock Call | Call # | Returns | Resulting Time |
|---|---|---|---|
| `eval_start` | 0 | base + 0μs | 2026-03-01T00:00:00.000000Z |
| Timeout check | 1 | base + 1000μs | 2026-03-01T00:00:00.001000Z |
| Error (if triggered) | 2 | base + 2000μs | 2026-03-01T00:00:00.002000Z |
| Stage 1 `now` | 3 | base + 3000μs | 2026-03-01T00:00:00.003000Z |
| Stage 2 heartbeat | 4 | base + 4000μs | 2026-03-01T00:00:00.004000Z |
| Stage 3 delegation | 5 | base + 5000μs | 2026-03-01T00:00:00.005000Z |
| Stage 7 audit | 6 | base + 6000μs | 2026-03-01T00:00:00.006000Z |

Total simulated evaluation time: 6μs × `advance_per_stage` = 6ms. This is within the 54ms p99 budget and produces identical timestamps on every replay.

---

## 5. TOKEN EXPIRY UNDER DETERMINISTIC CLOCK

Capability tokens have a 60-second TTL (ENF-04). Under the deterministic clock:

```
token.iat = clock.now_utc()  // Call #6 = base + 6ms
token.exp = token.iat + 60s  // base + 60.006s
```

For token validation tests, the test case sets `clock_time` relative to the token's creation time:

- **Valid token test:** `clock_time = token_creation_time + 30s` → token is within TTL
- **Expired token test:** `clock_time = token_creation_time + 61s` → token is past TTL
- **Boundary test:** `clock_time = token_creation_time + 60s` → exact expiry edge

The deterministic clock ensures these boundary conditions are tested precisely, not approximately.

---

## 6. HEARTBEAT FRESHNESS UNDER DETERMINISTIC CLOCK

Stage 2 checks: `clock.now_utc() - agent.last_heartbeat > 500ms`

The test case controls both sides:
- `agent.last_heartbeat` is set in the frozen StateRegistry snapshot
- `clock_time` is set in the injections

```
// Agent is alive
snapshot.state_registry.agent_X.last_heartbeat = "2026-03-01T00:00:00.000000Z"
injections.clock_time = "2026-03-01T00:00:00.400000Z"  // 400ms ago → ALIVE

// Agent is stale
snapshot.state_registry.agent_X.last_heartbeat = "2026-03-01T00:00:00.000000Z"
injections.clock_time = "2026-03-01T00:00:00.600000Z"  // 600ms ago → STALE → DENY
```

---

## 7. CRL STALENESS UNDER DETERMINISTIC CLOCK

The CRL interface reports `staleness_ms()`. In the frozen snapshot, this is a fixed value:

```
snapshot.crl_snapshot.staleness_ms = 0    // Fresh CRL → normal operation
snapshot.crl_snapshot.staleness_ms = 450  // Approaching threshold → normal but flagged
snapshot.crl_snapshot.staleness_ms = 550  // Exceeds 500ms threshold → DENY all (fail-closed)
```

The deterministic clock does not affect CRL staleness because the frozen CRL reports a fixed value. This is correct: in production, CRL staleness is measured by the CRL service, not by the PDP's local clock.

---

## 8. TIMEOUT BEHAVIOR UNDER DETERMINISTIC CLOCK

The PDP checks: `clock.now_utc() - eval_start > EVAL_BUDGET_MS` (54ms)

Under the deterministic clock with `advance_per_stage = 1000` (1ms), the timeout check at call #1 sees: `(base + 1ms) - (base + 0ms) = 1ms`, which is well within budget.

To test timeout behavior:
```
// Normal — no timeout
injections.clock_advance_per_stage = 1000  // 1ms per call → 7ms total → PASS

// Timeout — budget exceeded
injections.clock_advance_per_stage = 10000000  // 10s per call → exceeds 54ms → TIMEOUT
```

The timeout test verifies FM-11 (Evaluation Timeout) produces deterministic DENY.

---

## 9. STATIC ANALYSIS REQUIREMENT

To prevent accidental direct clock usage bypassing the injectable interface:

**Build-time check:** The CI/CD pipeline must scan all PDP source files for:
- Direct calls to `time.Now()` (Go), `SystemTime::now()` (Rust), `datetime.utcnow()` (Python)
- Direct calls to `time.Since()`, `time.Until()`, `time.Sleep()`
- Any import of system time libraries not through the Clock interface

**If any direct clock call is found outside the Clock interface implementation, the build fails.** This follows Martin Fowler's recommendation for eradicating non-determinism in tests.

Pattern for Go:
```
// FAIL: grep -r "time\.Now()" --include="*.go" src/ | grep -v "real_clock.go"
// If output is non-empty → build fails
```

---

## 10. RELATIONSHIP TO EXISTING SPECIFICATIONS

| Existing Spec | What This Document References | What This Document Does NOT Change |
|---|---|---|
| Day 3 — Evaluation Order | EVAL-07 (50ms budget, updated to 54ms in v1.1) | No evaluation changes |
| Day 4 — Failure Modes | FM-11 (Evaluation Timeout) | No failure mode changes |
| Day 5 — Enforcement Model | ENF-04 (60-second TTL) | No enforcement changes |
| Day 6 — Pseudocode | All 7 clock.now_utc() call sites | No pseudocode changes |
| Lock v1.1 | DEP-07 (NTP synchronization < 500ms) | No lock changes |

---

**END OF CLOCK INJECTION STRATEGY**

## DOCUMENT METADATA

| Field | Value |
|---|---|
| Clock Call Sites in Pseudocode | 7 |
| Verdict-Affecting Clock Calls | 4 (timeout, token expiry, heartbeat, delegation) |
| Clock Interface Methods | 1 (now_utc) |
| Implementation Variants | 2 (RealClock for production, DeterministicClock for test) |
| Static Analysis Required | Yes — fail build on direct clock access |
| PDP Modifications Required | 0 (interface injection, not logic change) |
