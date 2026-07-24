# Sarathi Governance Kernel — Audit Resolution Report

**Document ID:** SARATHI-AUDIT-RESOLUTION-V7.0.2
**Author:** Hemanth B / Governance Engineering
**System:** Sarathi Enforcement Adapter v7.0.2
**Audit Version:** Deep Audit V2 (benchmarked against Zanzibar, Cedar, Vault, OPA, SPIFFE, NIST 800-207)
**Date:** March 2026
**Audit Status:** 43 findings → 36 RESOLVED | 7 DEFERRED (non-blocking)

---

## Summary Table

| Severity | Total Found | Resolved | Deferred |
|----------|:-----------:|:--------:|:--------:|
| CRITICAL | 11 | **11** | 0 |
| HIGH | 14 | **14** | 0 |
| MEDIUM | 12 | 8 | 4 |
| LOW | 6 | 3 | 3 |
| **Total** | **43** | **36** | **7** |

All CRITICAL and HIGH findings resolved. Zero stubs remain in the critical path.

---

## CRITICAL FINDINGS — ALL 11 RESOLVED

### C-01: No `context.Context` in Pipeline Functions
**Severity:** CRITICAL | **Status:** RESOLVED
**Finding:** No function in the enforcement pipeline accepted `context.Context`. Cancellation, deadlines, and trace propagation were impossible.
**Resolution:** `context.Context` added to all major pipeline functions: `Enforce()`, `Execute()`, `ProcessRequest()`, `RouteExecution()`, and PDP `Evaluate()`. Timeout budget is respected. Trace context propagated through spans.
**Evidence:** `system_full_integration.go` TRACE-001 through TRACE-005 pass.

---

### C-02: Timing Attack in `VerifyIntegrity()`
**Severity:** CRITICAL | **Status:** RESOLVED
**Finding:** Token integrity verification used `ct.tokenHash == recomputed` — a non-constant-time string comparison. An attacker could measure timing variation to determine valid hash prefixes.
**Resolution:** Replaced with `crypto/subtle.ConstantTimeCompare([]byte(ct.tokenHash), []byte(recomputed)) == 1`.
**File:** `capability_token.go:VerifyIntegrity()`
**Reference:** NIST SP 800-57, OWASP Timing Side-Channel Attacks

---

### C-03: `crypto/rand.Read` Errors Silently Ignored
**Severity:** CRITICAL | **Status:** RESOLVED
**Finding:** `_, _ = rand.Read(traceID)` in `NewTraceContext()`, `NewChildSpan()`, and `ecosystem_contracts.go` silently discarded errors from the OS CSPRNG.
**Resolution:** Error is now checked. On failure, fallback is `SHA-256(fmt.Sprintf("fallback-%d", time.Now().UnixNano()))` — deterministic, non-panicking, non-empty.
**Files:** `sovereign_governance_v9.go`, `ecosystem_contracts.go`

---

### C-04: No Clock Skew Tolerance in Token Expiry
**Severity:** CRITICAL | **Status:** RESOLVED
**Finding:** `IsExpired()` used `time.Now().UTC().After(ct.expiresAt)`. Clock drift between adapter and engine nodes causes valid tokens to be rejected.
**Resolution:** `ClockSkewTolerance = 5 * time.Second` constant added. Token expired only when `time.Now().UTC().After(ct.expiresAt.Add(ClockSkewTolerance))`.
**File:** `capability_token.go:IsExpired()`
**Reference:** JWT best practices (30–60s), Kerberos (5 minutes)

---

### C-05: No Issuer or Audience Claims in Tokens
**Severity:** CRITICAL | **Status:** RESOLVED
**Finding:** No `issuer` or `audience` fields. A token issued by adapter-A could be replayed to adapter-B, or a resource-X token used for resource-Y.
**Resolution:** Added `issuer` (set to `"sarathi-enforcement-adapter"`) and `audience` (set to `resp.ResourceTypeField()`). Both fields in serialization payload and integrity hash. Accessors: `Issuer()`, `Audience()`.
**File:** `capability_token.go`
**Reference:** JWT RFC 7519 §4.1.1 (`iss`), §4.1.3 (`aud`)

---

### C-06: Bridge Passport Nonce Deduplication Missing
**Severity:** CRITICAL | **Status:** RESOLVED
**Finding:** `VerifyPassport()` did not deduplicate nonces. An intercepted passport could be replayed within its 30-second validity window.
**Resolution:** `usedNonces sync.Map` added to `BridgePassportAuthority`. `VerifyPassport()` calls `usedNonces.LoadOrStore(nonce, time.Now())` — duplicate → `NONCE_ALREADY_USED`. Background cleanup evicts nonces older than 30s.
**File:** `ecosystem_contracts.go:BridgePassportAuthority`

---

### C-07: Key Management Audit Writes Silently Ignored
**Severity:** CRITICAL | **Status:** RESOLVED
**Finding:** 6 locations in `key_management.go` used `_ = km.auditSink.RecordSystemEvent(...)` — errors discarded. Key lifecycle events could fail silently.
**Resolution:** All 6 locations now check errors and log structured warnings.
**File:** `key_management.go`
**Reference:** HashiCorp Vault — audit write failures are always surfaced

---

### C-08: Numeric Comparison Using String Compare in Cedar Conditions
**Severity:** CRITICAL | **Status:** RESOLVED
**Finding:** `greater_than`/`less_than` operators used Go string comparison (`contextValue > condition.Value`). `"9" > "10"` returns true (lexicographic) — completely incorrect for numeric trust scores.
**Resolution:** Both operators now parse values as `float64` via `strconv.ParseFloat`.
**File:** `sovereign_governance_v9.go:EvaluateCondition()`
**Reference:** AWS Cedar — `long` type comparison is always numeric
**Evidence:** CEDAR-001 through CEDAR-008 pass with correct results.

---

### C-09: TokenRegistry Unbounded Memory Growth
**Severity:** CRITICAL | **Status:** RESOLVED
**Finding:** `consumed map[string]bool` had no eviction. Every consumed token hash remained in memory forever.
**Resolution:** Changed to `consumed map[string]time.Time`. Background `cleanupLoop()` evicts entries older than `2*maxTTL + ClockSkewTolerance`. `StopCleanup()` for graceful shutdown. `IsConsumed()` fixed to `_, exists := tr.consumed[hash]; return exists`.
**File:** `capability_token.go:TokenRegistry`

---

### C-10: FIX-03 Service Decomposition Missing
**Severity:** CRITICAL | **Status:** RESOLVED
**Finding:** NIST SP 800-207 requires PE/PA/PEP as separate, well-defined interfaces. v6.0 had no formal interface separation.
**Resolution:** Four interfaces implemented: `PolicyDecisionService`, `TokenSigningService`, `AuditService`, `EnforcementPointService`.
**File:** `sovereign_governance_v9.go`
**Reference:** NIST SP 800-207 §2.1 — Logical Components of Zero Trust Architecture

---

### C-11: Escalation Webhook Was a Stub
**Severity:** CRITICAL | **Status:** RESOLVED
**Finding:** `NotifyEscalation()` incremented a counter only. Security incidents were silently swallowed.
**Resolution:** Full HTTP webhook: JSON payload, real `http.Post()`, exponential backoff retry (3 attempts), circuit breaker (5 failures → 60s cooldown), metrics tracking.
**File:** `sovereign_governance_v9.go:NotifyEscalation()`
**Evidence:** ESCALATE-002 verifies real HTTP POST is attempted and failure is recorded.

---

## HIGH FINDINGS — ALL 14 RESOLVED

| ID | Finding | Resolution | Evidence |
|---|---|---|---|
| H-01 | No request size validation at bridge | `ValidateInputSizes()` at bridge entry before auth | Phase 3B bypass tests |
| H-02 | Idempotency cache no per-entry TTL | Per-entry `time.Time`, background eviction goroutine | Integration tests |
| H-03 | O(n) timestamp-array rate limiter | O(1) two-bucket sliding window | RATE-001 through RATE-004 |
| H-04 | PDP evaluation no timeout | `context.Context` with deadline propagated into PDP | TRACE tests |
| H-05 | No graceful request draining | `sync.WaitGroup` on active requests, `Shutdown()` waits | Stress tests |
| H-06 | Bridge passport HMAC key hardcoded | From `SARATHI_BRIDGE_SECRET` env var | CONFIG-001, CONFIG-002 |
| H-07 | `LocalRateLimiter` no cleanup | Background cleanup goroutine + `StopCleanup()` | RATE-001 through RATE-004 |
| H-08 | Redundant `time.Parse` in time range check | Parse once at policy load, not per evaluation | CEDAR-005 |
| H-09 | `GetPosture` returns internal pointer | Deep copy returned — external callers cannot mutate | POSTURE-001 through POSTURE-006 |
| H-10 | `fmt.Printf` used for logging | `log.Printf` with structured `key=value` context | Code review |
| H-11 | Inconsistent atomic vs mutex | Consistent `sync.Mutex` on all shared state | Concurrency stress tests |
| H-12 | BeyondCorp posture not wired | Step 0.5 in `Enforce()`, `postureMonitor` field | POSTURE-001 through POSTURE-006 |
| H-13 | DistributedRateLimiter not wired | Wired into pipeline constructor + bridge | RATE-001 through RATE-004 |
| H-14 | TraceContext not wired into pipeline | Root span in `Execute()`, child in `Enforce()` | TRACE-001 through TRACE-005 |

---

## MEDIUM FINDINGS — 8 RESOLVED, 4 DEFERRED

### Resolved (8)

| ID | Finding | Resolution |
|---|---|---|
| M-01 | Policy bundle signing not wired | Ed25519-signed bundles verified at load |
| M-02 | No path discovery at startup | 16 paths registered, 0 BYPASS_RISK (PATH-001 through PATH-004) |
| M-03 | KSML hook not through bridge | KSML decisions route via GatedBridge (KSML-001 through KSML-003) |
| M-04 | Unified config incomplete | `SarathiConfig` covers all 14+ parameters |
| M-05 | No escalation tracking | Metrics: sent, failed, lastError |
| M-06 | Only 4 env vars read | All config from env via `SarathiConfig` (CONFIG-001, CONFIG-002) |
| M-07 | Idempotency key not in request | Added to `SaarthiRequest` |
| M-08 | Break-glass no time limit | 15-minute TTL on break-glass activation |

### Deferred (4)

| ID | Finding | Reason |
|---|---|---|
| M-09 | No mTLS between services | Pending infrastructure provisioning |
| M-10 | PostgreSQL connection pool not runtime-tunable | Config-time only (acceptable for current scope) |
| M-11 | No canary policy evaluation | Planned for v8.0 |
| M-12 | Audit records not encrypted at rest | PostgreSQL-level encryption — infra team scope |

---

## LOW FINDINGS — 3 RESOLVED, 3 DEFERRED

### Resolved (3)

| ID | Finding | Resolution |
|---|---|---|
| L-01 | Version header inconsistent | `X-Sarathi-Version: 7.0.2` on all HTTP responses |
| L-02 | No `ParseTraceContext` field validation | Lengths validated per W3C Trace Context spec |
| L-03 | Test helpers in production code | Moved to `_test.go` files |

### Deferred (3)

| ID | Finding | Reason |
|---|---|---|
| L-04 | Policy file comments not stripped at load | Low risk — comments don't affect evaluation |
| L-05 | Rate limit metrics not in Prometheus | Planned for next sprint |
| L-06 | Key rotation notifications not configurable | Webhook covers critical events |

---

## Verification Results

All CRITICAL and HIGH fixes verified by the v7.0 integration test suite:

```
48/48 tests PASS:
  mandatory_audit:          4/4
  token_revocation:         5/5
  cedar_conditions:         8/8
  safe_errors:              3/3
  distributed_tracing:      5/5
  beyondcorp_posture:       6/6
  distributed_rate_limit:   4/4
  escalation_webhook:       2/2
  unified_config:           2/2
  path_discovery:           4/4
  ksml_governance:          3/3
  bypass_proof:             2/2

Total test suite: 172/172 passing
Build: zero errors
```

---

*Sarathi Enforcement Adapter v7.0.2 | Audit Resolution Report | 2026-03-31*
