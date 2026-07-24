# DRIFT DETECTION SPECIFICATION

**Author:** Hemanth B
**Target System:** Sarathi Governance Kernel — Policy Decision Point
**Host Organization:** Blackhole Infiverse (BHIV)
**Classification:** Internal Sovereign Design / Strictly Confidential
**Version:** 1.0
**Date:** March 2026
**Task Reference:** Observability & Traceability Contract — Phase B
**Upstream Dependencies:**
- `decision_trace_spec.md` (Phase A) — defines what is recorded per decision
- `evaluation_order_spec.md` (Day 3) — defines 7-stage pipeline, timing budget (54ms p99)
- `failure_mode_contract.md` (Day 4) — defines 17 failure modes
- `sarathi_pdp_lock_v1.md` (v1.1) — defines 12 guarantees, policy version binding (G-11)
- `SARATHI_PDP_INTERFACE.md` (Task 3) — defines circuit breakers, 3-tier algorithmic circuit breakers

**Scope Boundary:** This document defines how drift is DETECTED and CLASSIFIED. It does NOT modify the PDP evaluation logic, Canon rules, or any schema. Detection is passive observation of decision trace data. No inline PDP changes.

---

## 1. PURPOSE

Governance drift is the silent divergence between what the system SHOULD do and what it ACTUALLY does. It is the most dangerous failure mode because it produces no errors, no alerts, and no obvious symptoms — until an audit reveals that unauthorized actions were permitted for weeks.

This specification defines how Sarathi detects drift before it becomes a governance breach. It answers one question: **Is the system behaving the way the specification says it should?**

---

## 2. DRIFT TAXONOMY

Not all anomalies are drift. Not all drift is dangerous. This taxonomy classifies deviations into categories that determine response severity.

### 2.1 Categories

| Category | Definition | Example | Severity |
|---|---|---|---|
| **Policy Drift** | The active policy bundle differs from the expected baseline | PDP instance running stale policy after failed bundle update | CRITICAL |
| **Token Drift** | Issued tokens behave inconsistently with the policy that produced them | Token issued under policy v3 used after policy v4 deployed | HIGH |
| **Verdict Drift** | The distribution of verdicts shifts without a corresponding policy change | ALLOW rate increases 15% week-over-week with no policy modification | HIGH |
| **Timing Drift** | Evaluation latency systematically exceeds budget | p99 creeping from 40ms to 52ms over 2 weeks (approaching 54ms budget) | MEDIUM |
| **Behavioral Drift** | Agent request patterns change in ways that suggest probing or adaptation | Agent issues 50 nearly-identical requests with slight parameter variations | MEDIUM |
| **Dependency Drift** | External dependency health degrades below SLA | CRL staleness averaging 400ms (approaching 500ms fail-closed threshold) | MEDIUM |
| **System Noise** | Random variation within expected bounds | ALLOW rate fluctuates ±3% day-to-day with no trend | NONE |

### 2.2 The Drift vs. Noise Decision Rule

A deviation is classified as **drift** (not noise) when ANY of the following hold:

1. **Monotonic trend** — the metric moves in one direction for 3+ consecutive measurement windows
2. **Threshold proximity** — the metric is within 20% of a hard limit (e.g., latency at 43ms against 54ms budget)
3. **Uncorrelated change** — the metric shifts without a corresponding policy, infrastructure, or traffic change
4. **Statistical anomaly** — the metric exceeds 3 standard deviations from its 30-day rolling baseline (Population Stability Index > 0.2)

If none of these hold, the deviation is noise. Noise is logged but does not trigger alerts.

---

## 3. DRIFT DETECTION METRICS

### 3.1 Policy Version Metrics

These detect whether all PDP instances are running the same policy and whether that policy is the intended one.

| Metric ID | Metric | Computation | Window | Alert Condition |
|---|---|---|---|---|
| **PM-01** | Policy Hash Uniformity | Count of distinct `pdp_policy_hash` values across all active PDP instances | 1 minute | > 1 distinct hash for > 5 minutes |
| **PM-02** | Policy Version Age | `now() - policy_bundle.last_updated_at` for each PDP instance | Continuous | Any instance with age > 10 minutes after a new bundle is published |
| **PM-03** | Request-PDP Policy Mismatch Rate | `count(policy_version_match == false) / count(all requests)` | 5 minutes | > 5% mismatch rate sustained for 10 minutes |
| **PM-04** | Policy Rollback Detection | `current_policy_hash == any_previous_hash AND current_policy_hash != expected_hash` | On every policy load | Any occurrence (zero tolerance) |

**Response to PM-01 breach:** A PDP fleet with mixed policies produces non-deterministic verdicts for the same request routed to different instances. This violates G-02 (Deterministic Evaluation). Alert is CRITICAL. Remediation: force bundle sync or drain the stale instance.

---

### 3.2 Token Consistency Metrics

These detect whether capability tokens remain consistent with the policy that authorized them.

| Metric ID | Metric | Computation | Window | Alert Condition |
|---|---|---|---|---|
| **TM-01** | Token-Policy Version Gap | Count of tokens where `token.policy_hash != current_pdp_policy_hash` that are still within TTL | 1 minute | > 0 (any unexpired token from a prior policy version after new policy is active for > 60s) |
| **TM-02** | Token TTL Violation | Count of tokens with `exp - iat > 60 seconds` | Continuous | Any occurrence (violates ENF-04, Canon MF-05) |
| **TM-03** | Token Reuse Detection | Count of `token_jti` values seen more than once | Continuous | Any occurrence (violates ENF-03, single-use) |
| **TM-04** | Token Scope Inflation | Cases where token scope is broader than the evaluated request scope | Continuous | Any occurrence (violates ENF-05, exact scope) |

**Response to TM-01 breach:** After a policy update, all tokens issued under the old policy should expire within 60 seconds (TTL). If old-policy tokens persist beyond 60s post-update, either the TTL is misconfigured or the CRL is not invalidating them. Alert is HIGH.

---

### 3.3 Verdict Distribution Metrics

These detect whether the ratio of ALLOW/DENY/ESCALATE shifts without a policy change.

| Metric ID | Metric | Computation | Window | Alert Condition |
|---|---|---|---|---|
| **VD-01** | ALLOW Rate | `count(ALLOW) / count(all verdicts)` | 1 hour rolling | Shift > 10% from 7-day baseline without policy change |
| **VD-02** | DENY Rate by Reason Code | `count(DENY with reason X) / count(all DENY)` per reason code | 1 hour rolling | Any reason code's share shifts > 15% from 7-day baseline |
| **VD-03** | ESCALATE Rate | `count(ESCALATE) / count(all verdicts)` | 1 hour rolling | > 2% of verdicts are ESCALATE (indicates systemic conflict) |
| **VD-04** | Short-Circuit Rate | `count(verdict_source == "SHORT_CIRCUIT") / count(all verdicts)` per stage | 1 hour rolling | Stage 1 short-circuit rate > 30% (indicates mass authentication failures) |
| **VD-05** | ALLOW-After-DENY Pattern | Count of agent_id values that receive DENY then ALLOW for the same resource within 5 minutes | Continuous | > 3 occurrences per agent per hour (indicates iterative probing that found a bypass) |
| **VD-06** | Population Stability Index | PSI comparing current hour's verdict distribution to 30-day baseline | 1 hour | PSI > 0.2 (established statistical threshold for significant shift) |

**Response to VD-05 breach:** An agent that repeatedly gets denied and then succeeds is either (a) legitimately retrying with corrected credentials, or (b) iteratively probing the policy boundary. If the ALLOW-producing request differs from the DENY-producing requests in only one field, it is a probe. Alert is HIGH with Security review required.

---

### 3.4 Borderline Denial Metrics

These detect agents that consistently operate at the edge of policy boundaries — a strong indicator of adversarial adaptation.

| Metric ID | Metric | Computation | Window | Alert Condition |
|---|---|---|---|---|
| **BD-01** | Near-Miss Rate per Agent | Count of requests per agent_id where DENY was triggered by a single rule (all other stages PASS) | 1 hour | > 10 near-misses per agent per hour |
| **BD-02** | Rule Boundary Clustering | Count of requests that trigger the same single rule in the same stage for the same resource_type | 1 hour | > 20 requests clustering on one rule boundary |
| **BD-03** | Sensitivity Understatement Rate | Count of requests where `declared_sensitivity < registry_sensitivity` | 1 hour | > 5% of requests from any single agent |
| **BD-04** | Classification Downgrade Attempts | Count of requests where `declared_data_classification < registry_data_classification` | Continuous | Any occurrence from a non-PENETRATION_TESTER agent |

---

### 3.5 Timing and Performance Metrics

These detect latency drift that could indicate resource exhaustion, dependency degradation, or denial-of-service.

| Metric ID | Metric | Computation | Window | Alert Condition |
|---|---|---|---|---|
| **TP-01** | p99 Evaluation Latency | 99th percentile of `total_duration_us` | 5 minutes | > 54ms (p99 budget) sustained for 10 minutes |
| **TP-02** | Per-Stage Latency | p99 of `stages[N].duration_us` for each stage | 5 minutes | Any stage exceeding its allocated budget (Stage 1: 15ms, Stage 2: 5ms, Stage 3: 10ms, Stage 4: 8ms, Stage 5: 7ms, Stage 6: 3ms, Stage 7: 2ms + 200ms write timeout) |
| **TP-03** | Timeout Rate | `count(verdict_source == "TIMEOUT") / count(all verdicts)` | 5 minutes | > 0.1% (1 in 1000 requests timing out) |
| **TP-04** | Latency Trend | Linear regression slope of p99 over 7 days | Daily | Positive slope that projects p99 > budget within 14 days |

---

### 3.6 Dependency Health Metrics

These detect degradation in external systems that could compromise governance guarantees.

| Metric ID | Metric | Computation | Window | Alert Condition |
|---|---|---|---|---|
| **DH-01** | CRL Staleness | `now() - crl.last_updated_at` across all PDP instances | 1 minute | > 400ms average (500ms triggers fail-closed per DEP-05) |
| **DH-02** | State Registry Latency | p99 of `state_registry_latency_us` | 5 minutes | > 8ms (10ms triggers fail-closed per DEP-06) |
| **DH-03** | BHIV Bucket Write Latency | p99 of Stage 7 audit write duration | 5 minutes | > 150ms (200ms triggers AUDIT_WRITE_TIMEOUT) |
| **DH-04** | Emergency Buffer Usage | Count of records written to emergency buffer instead of BHIV Bucket | 1 minute | > 0 for > 2 minutes (indicates sustained BHIV outage) |
| **DH-05** | NTP Drift | Maximum observed clock drift across PDP fleet | 1 minute | > 400ms (500ms triggers fail-closed per DEP-07) |
| **DH-06** | Hash Chain Continuity | Count of hash chain breaks detected in the last batch | Hourly (at Merkle batch time) | > 0 (any break triggers FM-16) |

---

## 4. ALERT SEVERITY FRAMEWORK

| Severity | Meaning | Response SLA | Notification Target |
|---|---|---|---|
| **CRITICAL** | Governance guarantee potentially violated. Immediate human review required. | 5 minutes | Security Lead + Governance Officer + on-call Engineering |
| **HIGH** | Significant deviation detected. Investigation required. | 30 minutes | Security team + on-call Engineering |
| **MEDIUM** | Trending toward a threshold. Preventive action recommended. | 4 hours | Operations team |
| **LOW** | Informational anomaly. Logged for correlation. | Next business day | Operations dashboard |

### 4.1 Alert Escalation

If a MEDIUM alert remains unresolved for 24 hours and the metric continues trending toward the threshold, it automatically escalates to HIGH. If a HIGH alert remains unresolved for 4 hours, it escalates to CRITICAL.

### 4.2 Alert Suppression

Alerts are suppressed during:
- **Planned policy deployments** — PM-01, PM-03, and VD-01 through VD-06 are suppressed for 10 minutes after a policy deployment begins (policy propagation window)
- **Planned maintenance** — DH-01 through DH-06 are suppressed during declared maintenance windows
- **No other suppression is permitted.** There is no "snooze" for CRITICAL alerts.

---

## 5. DRIFT DETECTION ARCHITECTURE

Drift detection is a READ-ONLY consumer of decision trace data. It does not modify, intercept, or influence PDP decisions.

```
 PDP Instance 1 ──┐
 PDP Instance 2 ──┤──→ BHIV Bucket ──→ Drift Detection Pipeline
 PDP Instance N ──┘         │
                            │
                            ▼
                    Elasticsearch (Hot Tier)
                            │
                            ▼
                ┌───────────────────────┐
                │  Drift Detection      │
                │  ─────────────────    │
                │  1. Metric Computation │
                │  2. Baseline Comparison│
                │  3. Threshold Checking │
                │  4. PSI Calculation    │
                │  5. Trend Analysis     │
                │  6. Alert Generation   │
                └───────────┬───────────┘
                            │
                            ▼
                    Alert Router
                    ├── CRITICAL → PagerDuty / immediate
                    ├── HIGH     → Slack #sarathi-security
                    ├── MEDIUM   → Slack #sarathi-ops
                    └── LOW      → Dashboard only
```

**Pipeline cadence:**
- PM, TM, DH metrics: evaluated every 1 minute
- VD, BD metrics: evaluated every 5 minutes (requires aggregation)
- TP metrics: evaluated every 5 minutes
- PSI and trend analysis: evaluated hourly
- Baseline recalculation: daily at 00:00 UTC using 30-day rolling window

---

## 6. GOVERNANCE DRIFT vs. SYSTEM NOISE — DECISION MATRIX

| Signal | Single Occurrence | Sustained (>10 min) | Trending (>3 windows) | With Policy Change | Without Policy Change |
|---|---|---|---|---|---|
| ALLOW rate +5% | Noise | Noise | Investigate | Expected (noise) | **Drift — HIGH** |
| ALLOW rate +15% | Investigate | **Drift — HIGH** | **Drift — CRITICAL** | Investigate | **Drift — CRITICAL** |
| p99 latency +10ms | Noise | **Drift — MEDIUM** | **Drift — HIGH** | Noise (if policy is heavier) | **Drift — HIGH** |
| Single agent DENY→ALLOW | Noise | N/A | N/A | Noise | Investigate |
| Same agent 5× DENY→ALLOW | **Drift — HIGH** | N/A | N/A | Investigate | **Drift — CRITICAL** |
| CRL staleness 450ms | **Drift — MEDIUM** | **Drift — HIGH** | **Drift — CRITICAL** | N/A | N/A |
| 2+ policy hashes in fleet | **Drift — CRITICAL** | **Drift — CRITICAL** | N/A | Expected (during rollout, <5min) | **Drift — CRITICAL** |
| Hash chain break | **Drift — CRITICAL** | N/A | N/A | N/A | N/A |

---

## 7. RELATIONSHIP TO EXISTING SPECIFICATIONS

| Existing Spec | What This Document Reads | What This Document Does NOT Change |
|---|---|---|
| Decision Trace (Phase A) | All 56+ fields per decision | No trace field changes |
| Day 3 — Evaluation Order | Timing budget, stage structure | No evaluation changes |
| Day 4 — Failure Modes | FM-05, FM-11, FM-16 behaviors | No failure mode changes |
| Day 5 — Enforcement Model | Token invariants ENF-01 through ENF-14 | No enforcement changes |
| Lock v1.1 | Guarantees G-02 (Deterministic), G-05 (Audit), G-11 (Policy Binding) | No guarantee changes |
| PDP Interface | Circuit breaker thresholds, retention tiers | No interface changes |

---

**END OF DRIFT DETECTION SPECIFICATION**

## DOCUMENT METADATA

| Field | Value |
|---|---|
| Drift Categories | 7 (Policy, Token, Verdict, Timing, Behavioral, Dependency, Noise) |
| Detection Metrics | 24 (PM: 4, TM: 4, VD: 6, BD: 4, TP: 4, DH: 6) |
| Alert Severities | 4 (CRITICAL, HIGH, MEDIUM, LOW) |
| Noise Classification Rules | 4 (monotonic trend, threshold proximity, uncorrelated change, PSI > 0.2) |
| Pipeline Cadence Levels | 4 (1min, 5min, hourly, daily) |
| Existing Specs Modified | 0 |
