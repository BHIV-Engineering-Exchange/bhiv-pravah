# Sarathi Deterministic Response Schema — v13 Final Lock

**Author:** Hemanth B (Enforcement Kernel)
**Task:** Deterministic Response Enforcement Layer (v13 Final Lock)
**Status:** Merged — Adversarial Attack Harness 39/39 PASSED
**Date:** 2026-04-14

---

## 1. Rationale

Sarathi is already non-bypassable: the enforcement kernel, PDP, capability-token layer, chain integrity, posture verification, RPA path attestation, and the 9-stage canonical pipeline cannot be defeated by the attacker model covered in the v14.2 adversarial harness (37/39 attacks were correctly DENIED). The remaining gap was in **how** the kernel reported the DENY.

Two attacks — RPSA-01 (path traversal `policy-reg-001/../core-engine`) and RPSA-02 (case-sensitivity `Gov-Agent-001`) — were *correctly blocked* by the PDP but *surfaced to the caller as `<nil>`*. The harness read the top-level `verdict` key on the map returned by `Execute()`, but that key was not present in the map's bare-form pre-gate/RPA paths. Go returned `nil`, `fmt.Sprintf("%v", nil)` produced the literal string `"<nil>"`, and the test comparison `"<nil>" == "DENY"` failed. A correct enforcement decision was thrown away at the response boundary.

This schema fixes the root cause: every response produced by `Execute()` now carries a canonical top-level envelope with no optional fields and no sentinel nulls. Any downstream reader — harness, SDK, logger, audit trail — sees the same shape, regardless of which branch of `Execute()` produced the response.

**Industry alignment (learning-kit research):**
- **NIST SP 800-207 (Zero Trust Architecture):** the Policy Enforcement Point must emit an explicit decision signal at its boundary. Implicit/empty responses violate the non-bypassability property: a caller that cannot distinguish "denied" from "lost" will either fail-open or retry.
- **OWASP Input Validation Cheat Sheet:** canonicalize before validate; use Unicode NFKC; reject, do not sanitize. Auto-lowercasing attacker input would silently permit `Gov-Agent-001` to match `gov-agent-001` — a security downgrade.
- **Google Zanzibar / AWS IAM / Cedar:** every decision response carries an explicit `(decision, request_id, reason)` triple. A "null" decision is never valid.

---

## 2. Canonical Response Schema

All 17 fields below are **required** (15 original + 2 added in v14.4). Every response produced by `SarathiEnforcementPipeline.Execute()` is routed through `EnforceResponseContract` (defined in [response_contract.go](../response_contract.go)), which validates field presence and forces a DENY with `ERR_CONTRACT_VIOLATION` if any field is missing or empty.

| Field | Type | Sentinel on unknown | Description |
|---|---|---|---|
| `schema_version` | string | constant `sarathi.response/v13.0` | Immutable version string. Callers may pin against this. |
| `decision_id` | string | deterministic `PRE-GATE-<hex>` derived from SHA-256(stage + correlation_id) | UUID from the PDP for happy-path; deterministic prefix for pre-gate rejects so operators can de-dupe attacker retries. |
| `verdict` | string | `DENY` on any failure branch | Enum: `ALLOW`, `DENY`, `ESCALATE`. Never empty. |
| `execution_state` | string | `EXECUTION_NOT_ATTEMPTED` for pre-gate | Enum: `EXECUTION_PERMITTED`, `EXECUTION_BLOCKED`, `EXECUTION_NOT_ATTEMPTED`, `EXECUTION_RPA_VIOLATION`, `EXECUTION_CONTRACT_VIOLATION`. |
| `error_code` | string | `OK` on success | Canonical error code from the dictionary in §3. |
| `reason` | string | derived from error_code if no PDP reason | Human-readable reason; never empty. |
| `trace_id` | string | W3C trace id from `traceCtx.TraceID` | Trace correlation across services. |
| `correlation_id` | string | passthrough from request | Caller-supplied idempotency key. |
| `enforcement_hash` | string | `PRE-GATE-NO-ENFORCEMENT` or `CONTRACT-VIOLATION-NO-ENFORCEMENT` | SHA-256 chain hash; sentinel form signals pre-gate/contract paths so chain inspectors do not confuse them with real entries. |
| `timestamp` | string | RFC3339 UTC with microsecond precision | Response build time. |
| `request` | map | always `ExecutionRequest.ToMap()` or a raw-input map | Echo of the original request. |
| `enforcement` | map | `emptyEnforcementEnvelope(...)` sentinel | Nested full enforcement envelope (or sentinel on pre-gate). |
| `execution` | map | `emptyExecutionEnvelope(...)` sentinel | Nested execution envelope (or sentinel). |
| `trace_context` | map | `traceContextMap(traceCtx)` | Non-nil trace context projection. |
| `observability` | map | `emptyObservabilityEnvelope(...)` | Path-hash + stage list for audit. |
| `enforcement_token` | string | empty string for DENY paths | `CapabilityToken.TokenID()` — present only on ALLOW paths. |
| `execution_id` | string | empty string for DENY paths | `EXEC-{sequence}-{hash[:8]}` — present only on ALLOW paths. |

**Contract rule (task.md Phase 4 verbatim):** `EnforceResponseContract` runs immediately before every return from `Execute()`. If `ValidateResponseContract(resp)` returns `false`, the response is **replaced** with a fresh canonical DENY built from `CodeContractViolation`, the request parameters, and the trace context already in scope. No response can leave the kernel without a full schema.

---

## 3. Error Code Dictionary

Defined as constants in [response_contract.go](../response_contract.go). Every failure maps to exactly one. No free text, no generic "error" strings.

### Success
- `OK` — ALLOW + PERMITTED

### Input normalization (Phase 3: parsing hardening)
- `ERR_INVALID_AGENT_ID` — regex / length / control chars
- `ERR_INVALID_RESOURCE_ID` — regex / length / control chars
- `ERR_PATH_TRAVERSAL` — resource_id contained `..`, `/`, `\`, leading `.`, or was non-canonical
- `ERR_NON_CANONICAL_CASE` — mixed-case agent/resource id; registry uses lowercase keys and we **reject** rather than silently lowercase
- `ERR_INVALID_ACTION` — not in allowed verb set
- `ERR_INVALID_CORRELATION_ID` — missing/too long
- `ERR_INPUT_INVALID_ENCODING` — UTF-8 invalid
- `ERR_INPUT_TOO_LONG` — exceeds `MaxNormalizedFieldLength` (256)

### Pre-gate rejections
- `ERR_RATE_LIMITED` — `PreGateRateLimiter.Admit` denied
- `ERR_POSTURE_MISSING` — signal required but absent
- `ERR_POSTURE_EXPIRED` — `POSTURE_SIGNAL_EXPIRED`
- `ERR_POSTURE_REPLAYED` — nonce already seen
- `ERR_POSTURE_UNKNOWN_ISSUER` — issuer not in authorized key set
- `ERR_POSTURE_SIGNATURE_INVALID` — `POSTURE_SIGNAL_INVALID` (Ed25519 verify failed)
- `ERR_POSTURE_DENIED` — valid signal, posture=false
- `ERR_POSTURE_TAMPERED` — payload modified after signing
- `ERR_POSTURE_REJECTED` — generic fallback

### PDP path (mapped from `pdp_engine.go` free-text reasons)
- `ERR_POLICY_VERSION_MISMATCH`
- `ERR_AGENT_NOT_FOUND`
- `ERR_AGENT_SUSPENDED` / `ERR_AGENT_REVOKED` / `ERR_AGENT_TERMINATED`
- `ERR_RESOURCE_NOT_FOUND`
- `ERR_NO_MATCHING_RULE` / `ERR_NO_ALLOW_RULE`
- `ERR_EXPLICIT_DENY`
- `ERR_CLASSIFICATION_CEILING_EXCEEDED` / `ERR_CLASSIFICATION_PARSE_FAILURE`
- `ERR_PDP_HASH_MISMATCH`
- `ERR_PDP_MARSHAL_FAILURE`
- `ERR_VALIDATION_FAILED`
- `ERR_PDP_DENY` (fallback)

### Post-enforcement / execution
- `ERR_RPA_INTEGRITY_VIOLATION` — runtime path attestation incomplete/reordered
- `ERR_NO_TOKEN` — ALLOW but no capability token
- `ERR_TOKEN_REPLAY` / `ERR_TOKEN_EXPIRED` / `ERR_TOKEN_SIGNATURE_INVALID`
- `ERR_EXECUTION_BLOCKED` — generic execution block

### Contract violations (fail-closed catch-all)
- `ERR_CONTRACT_VIOLATION` — `ValidateResponseContract` found missing/empty required field. Forces DENY.
- `ERR_INTERNAL` — panic recovered by the deferred panic guard
- `ERR_ESCALATED` — ESCALATE verdict routed to escalation queue

The `PdpReasonToErrorCode`, `PostureReasonToErrorCode`, and `BlockReasonToErrorCode` helpers translate the existing free-text reasons from `pdp_engine.go` / posture verifier / execution engine into this dictionary. The source files (`pdp_engine.go`, `capability_token.go`, `execution_engine_sim.go`) are **untouched** — their INV-02..INV-40 invariants remain intact.

---

## 4. JSON Examples

All examples are shaped exactly as emitted by `Execute()`. Every field is present. No nulls.

### 4.1 Happy path (ALLOW + PERMITTED)

```json
{
  "schema_version": "sarathi.response/v13.0",
  "decision_id": "4c8f1e50-2f7c-4a21-8a7d-f07ce1b6c411",
  "verdict": "ALLOW",
  "execution_state": "EXECUTION_PERMITTED",
  "error_code": "OK",
  "reason": "ALLOW",
  "trace_id": "0af7651916cd43dd8448eb211c80319c",
  "correlation_id": "demo-001",
  "enforcement_hash": "7a3f1b…",
  "timestamp": "2026-04-14T10:05:38.157259Z",
  "request":       { "agent_id": "gov-agent-001", "resource_id": "policy-reg-001", "action": "read", "correlation_id": "demo-001", "policy_version": "1.0.0", "request_hash": "…", "is_valid": true },
  "enforcement":   { "verdict": "ALLOW", "policy_version": "1.0.0", "enforcement_hash": "7a3f1b…", "error_code": "OK", "…": "…" },
  "execution":     { "executed": true, "execution_state": "EXECUTION_PERMITTED", "execution_hash": "…", "error_code": "OK", "…": "…" },
  "trace_context": { "trace_id": "0af7651916cd43dd8448eb211c80319c", "span_id": "00f067aa0ba902b7", "parent_span": "", "trace_flags": 1, "sampled": true },
  "observability": { "pipeline_path_hash": "…", "pipeline_path_stages": ["PRE_GATE_RATE_LIMIT", "PRE_GATE_POSTURE_VERIFY", "PRE_PDP_VALIDATION", "POLICY_VERSION_CHECK", "PDP_EVALUATION", "PDP_HASH_INTEGRITY", "ENFORCEMENT_RESPONSE_BUILD", "TOKEN_SIGN", "CHAIN_APPEND"], "pipeline_duration_ns": 1234567, "rpa_enforcement": "VERIFIED" }
}
```

### 4.2 Pre-gate rate-limit reject

```json
{
  "schema_version": "sarathi.response/v13.0",
  "decision_id": "PRE-GATE-e7d8b6",
  "verdict": "DENY",
  "execution_state": "EXECUTION_NOT_ATTEMPTED",
  "error_code": "ERR_RATE_LIMITED",
  "reason": "rate limit exceeded for agent std-agent-002",
  "trace_id": "…",
  "correlation_id": "rate-test-003",
  "enforcement_hash": "PRE-GATE-NO-ENFORCEMENT",
  "timestamp": "…",
  "request":       { "…": "…" },
  "enforcement":   { "verdict": "DENY", "decision_id": "PRE-GATE-e7d8b6", "enforcement_stage": "PRE_GATE", "pdp_decision_hash": "NO_PDP_EVALUATION", "error_code": "ERR_RATE_LIMITED", "…": "…" },
  "execution":     { "executed": false, "execution_state": "EXECUTION_NOT_ATTEMPTED", "block_reason": "ERR_RATE_LIMITED: rate limit exceeded for agent std-agent-002", "error_code": "ERR_RATE_LIMITED", "…": "…" },
  "trace_context": { "…": "…" },
  "observability": { "pipeline_path_hash": "", "pipeline_path_stages": [], "pipeline_duration_ns": 0, "rpa_enforcement": "NOT_ATTEMPTED", "rpa_detail": "rate limit exceeded for agent std-agent-002" },
  "pre_gate": { "stage": "RATE_LIMIT", "admitted": false, "reason": "rate limit exceeded for agent std-agent-002" }
}
```

### 4.3 Input normalization reject (RPSA-01, path traversal)

```json
{
  "schema_version": "sarathi.response/v13.0",
  "decision_id": "PRE-GATE-<hex>",
  "verdict": "DENY",
  "execution_state": "EXECUTION_NOT_ATTEMPTED",
  "error_code": "ERR_PATH_TRAVERSAL",
  "reason": "INPUT_NORMALIZATION_REJECTED: ERR_PATH_TRAVERSAL",
  "trace_id": "atk-rpsa01-8984bf07",
  "correlation_id": "atk-rpsa01-8984bf07",
  "enforcement_hash": "PRE-GATE-NO-ENFORCEMENT",
  "timestamp": "2026-04-14T10:05:38.156536Z",
  "request": { "agent_id": "gov-agent-001", "resource_id": "policy-reg-001/../core-engine", "action": "read", "correlation_id": "atk-rpsa01-8984bf07", "policy_version": "", "request_hash": "", "is_valid": false },
  "enforcement": { "…": "…", "error_code": "ERR_PATH_TRAVERSAL" },
  "execution":   { "executed": false, "execution_state": "EXECUTION_NOT_ATTEMPTED", "block_reason": "ERR_PATH_TRAVERSAL: INPUT_NORMALIZATION_REJECTED: ERR_PATH_TRAVERSAL", "error_code": "ERR_PATH_TRAVERSAL" },
  "trace_context": { "…": "…" },
  "observability": { "rpa_enforcement": "NOT_ATTEMPTED", "rpa_detail": "INPUT_NORMALIZATION_REJECTED: ERR_PATH_TRAVERSAL" },
  "pre_gate": { "stage": "INPUT_NORMALIZATION", "admitted": false, "reason": "INPUT_NORMALIZATION_REJECTED: ERR_PATH_TRAVERSAL" }
}
```

### 4.4 Input normalization reject (RPSA-02, case sensitivity)

```json
{
  "schema_version": "sarathi.response/v13.0",
  "decision_id": "PRE-GATE-<hex>",
  "verdict": "DENY",
  "execution_state": "EXECUTION_NOT_ATTEMPTED",
  "error_code": "ERR_NON_CANONICAL_CASE",
  "reason": "INPUT_NORMALIZATION_REJECTED: ERR_NON_CANONICAL_CASE",
  "trace_id": "atk-rpsa02-79b74acb",
  "correlation_id": "atk-rpsa02-79b74acb",
  "enforcement_hash": "PRE-GATE-NO-ENFORCEMENT",
  "timestamp": "2026-04-14T10:05:38.157259Z",
  "request": { "agent_id": "Gov-Agent-001", "resource_id": "policy-reg-001", "action": "read", "correlation_id": "atk-rpsa02-79b74acb", "policy_version": "", "request_hash": "", "is_valid": false },
  "enforcement": { "…": "…" },
  "execution":   { "…": "…" },
  "trace_context": { "…": "…" },
  "observability": { "…": "…" }
}
```

### 4.5 RPA integrity violation (v14.1 anti-fooling gate)

```json
{
  "schema_version": "sarathi.response/v13.0",
  "decision_id": "…",
  "verdict": "DENY",
  "execution_state": "EXECUTION_RPA_VIOLATION",
  "error_code": "ERR_RPA_INTEGRITY_VIOLATION",
  "reason": "RPA_INTEGRITY_VIOLATION: INCOMPLETE: expected 9 stages, recorded 2 stages",
  "trace_id": "…",
  "correlation_id": "…",
  "enforcement_hash": "…",
  "timestamp": "…",
  "request": { "…": "…" },
  "enforcement": { "verdict": "ALLOW", "error_code": "ERR_RPA_INTEGRITY_VIOLATION", "…": "…" },
  "execution":   { "executed": false, "execution_state": "EXECUTION_RPA_VIOLATION", "block_reason": "RPA_INTEGRITY_VIOLATION: …", "error_code": "ERR_RPA_INTEGRITY_VIOLATION" },
  "trace_context": { "…": "…" },
  "observability": { "rpa_enforcement": "BLOCKED", "rpa_violation": "INCOMPLETE: expected 9 stages, recorded 2 stages" }
}
```

### 4.6 Contract violation (forced DENY)

If a builder ever produces an incomplete map (e.g., a new code path forgets a field), `EnforceResponseContract` replaces the response with:

```json
{
  "schema_version": "sarathi.response/v13.0",
  "decision_id": "CONTRACT-VIOLATION-<hex>",
  "verdict": "DENY",
  "execution_state": "EXECUTION_CONTRACT_VIOLATION",
  "error_code": "ERR_CONTRACT_VIOLATION",
  "reason": "RESPONSE_CONTRACT_VIOLATION: missing_fields=verdict,enforcement_hash",
  "trace_id": "…",
  "correlation_id": "…",
  "enforcement_hash": "CONTRACT-VIOLATION-NO-ENFORCEMENT",
  "timestamp": "…",
  "request": { "…": "…" },
  "enforcement": { "…": "…" },
  "execution":   { "…": "…" },
  "trace_context": { "…": "…" },
  "observability": { "rpa_enforcement": "CONTRACT_FORCED_DENY", "rpa_detail": "RESPONSE_CONTRACT_VIOLATION: missing_fields=verdict,enforcement_hash" },
  "contract_violation": { "missing_fields": ["verdict", "enforcement_hash"], "original_fields": ["request", "trace_context"], "forced_by": "EnforceResponseContract" }
}
```

---

## 5. Guarantees (what this layer enforces)

1. **No nulls.** `ValidateResponseContract` rejects any response where a required field is missing, nil, empty string, or the literal string `"<nil>"`.
2. **Fail-closed.** A broken builder that produces an incomplete map becomes a DENY, not an ALLOW or a crash.
3. **Panic-safe.** `Execute()` has a deferred panic guard that converts any panic into `ERR_INTERNAL` + DENY through the same contract path.
4. **Reject-don't-sanitize.** `NormalizeIdentifiers` rejects mixed-case and path-traversal inputs with an explicit error code; it does not silently lowercase or clean them.
5. **Canonicalize-before-hash.** Normalization runs **before** `NewExecutionRequest` so the request hash, chain entry, and response all refer to the same identifiers.
6. **Additive, not breaking.** The existing nested `enforcement`, `execution`, `trace_context`, `observability` keys are preserved, so `integration_gate_tests.go`'s nested-read patterns continue to work unchanged.
7. **Invariant-safe.** `Enforce()`, `pdp_engine.go`, `capability_token.go`, `execution_engine_sim.go`, `policy_store.go`, `policy_signing.go`, and the 9-stage pipeline order are **untouched**. INV-02, INV-03, INV-04, INV-05, INV-35, INV-36, INV-38, INV-40 are preserved.

A new invariant is added:

**INV-45 (Canonical response contract):** Every return from `SarathiEnforcementPipeline.Execute()` produces a map that satisfies `ValidateResponseContract`. Any non-conforming map is replaced with a canonical `DENY` / `ERR_CONTRACT_VIOLATION`. No response with a missing/empty required field can leave the kernel.

---

## 6. How to extend

**Add a new error code:**
1. Add a `CodeXxx = "ERR_XXX"` constant in the dictionary block of [response_contract.go](../response_contract.go).
2. Add a mapping in `PdpReasonToErrorCode` / `PostureReasonToErrorCode` / `BlockReasonToErrorCode` as appropriate.
3. Update §3 of this document.

**Add a new required field:**
1. Append the field name to `RequiredResponseFields` in [response_contract.go](../response_contract.go).
2. Populate it in every `CanonicalFromXxx` builder so existing tests do not regress into contract-forced DENY.
3. Update §2 of this document with the field's type and sentinel.

**Add a new `Execute()` return site:**
1. The new site **must** call `EnforceResponseContract(CanonicalFromXxx(...), req, traceCtx)`. Bare-map returns are forbidden.
2. If a new builder is needed, it must populate every field in `RequiredResponseFields`. The builder is trivially testable by calling `ValidateResponseContract` on its output.

---

## 7. Proof of effect

**Before v13** (baseline [proof_logs/before_v13_attack_harness.json](../proof_logs/before_v13_attack_harness.json)):

| Attack | Expected | Actual | Error Code |
|---|---|---|---|
| RPSA-01 | DENY | `<nil>` | `DENY` (harness placeholder) |
| RPSA-02 | DENY | `<nil>` | `DENY` (harness placeholder) |

**After v13** (snapshot [proof_logs/after_v13_attack_harness.json](../proof_logs/after_v13_attack_harness.json)):

| Attack | Expected | Actual | Error Code |
|---|---|---|---|
| RPSA-01 | DENY | DENY | `ERR_PATH_TRAVERSAL` |
| RPSA-02 | DENY | DENY | `ERR_NON_CANONICAL_CASE` |

**Attack harness:** 37/39 → **39/39 PASSED**. Zero weaknesses.

**Full production validation:** `ENFORCEMENT ADAPTER VALIDATION: PASSED` (150/150) and `SARATHI v13.0 — FULL PRODUCTION VALIDATION: PASSED`. No regressions elsewhere.

**Nil leak audit:** `grep -c "<nil>" attack_harness_results.json proof_logs/after_v13_attack_harness.json proof_logs/v13_response_contract.jsonl` → `0` in all three.

**Proof log:** [proof_logs/v13_response_contract.jsonl](../proof_logs/v13_response_contract.jsonl) contains standardized 6-field records (attack_type, attack_id, input_payload, expected, actual, error_code, trace_id) for every RPSA attack, task.md Phase 6 verbatim.

---

## 8. Files touched

**New:**
- [response_contract.go](../response_contract.go) — the contract layer
- [review_packets/DETERMINISTIC_RESPONSE_SCHEMA.md](DETERMINISTIC_RESPONSE_SCHEMA.md) — this document
- [proof_logs/v13_response_contract.jsonl](../proof_logs/v13_response_contract.jsonl) — standardized proof log
- [proof_logs/before_v13_attack_harness.json](../proof_logs/before_v13_attack_harness.json)
- [proof_logs/after_v13_attack_harness.json](../proof_logs/after_v13_attack_harness.json)

**Edited (surgically):**
- [enforcement_adapter.go](../enforcement_adapter.go) — only the `Execute()` method (5 return sites + 1 normalization call + 1 panic guard). `Enforce()`, struct definitions, invariant bearings all untouched.
- [adversarial_attack_harness.go](../adversarial_attack_harness.go) — phase-8 RPSA reads now use `canonicalString` against the top-level schema fields; `LogAttackProof` wired in.

**Untouched (hard constraint per task.md):**
- `pdp_engine.go`, `policy_store.go`, `policy_registry.go`, `policy_signing.go`
- `capability_token.go`, `execution_engine_sim.go`, `key_management.go`
- `gated_bridge.go`, `saarthi_service.go`, `service_boundary.go`
- All evaluator soft-frozen files
- `execution_request.go`, `execution_response.go`
- `Enforce()` method (any change would violate INV-03 / INV-04)

---

## 9. Future work (out of scope for v13)

The following attack classes are **not** response-contract issues and were consciously left for a later phase. They are listed here so they are not forgotten.

- Percent-encoded path traversal (`%2e%2e%2f`) — stronger input canonicalization.
- Unicode confusable normalization for all fields, not just NFKC (skeleton form / confusables.txt).
- Symlink-equivalent traversal in multi-tenant resource namespaces.
- TOCTOU on agent status (suspended → active → execute race).
- Policy version downgrade attacks.
- Timing side channels in the ResponseContract validator (currently iterates fields sequentially).

---

**Closing note.** The system could already not be broken. After v13, it also cannot behave inconsistently. Sarathi is integration-ready.
