# Phase v14.8 — Sovereign Authority Closure Review Packet

**System:** Sarathi Enforcement Adapter — Parallel execution, cross-machine validation, live failure demo
**Version:** v14.8
**Author:** Hemanth B
**Organization:** Blackhole Infiverse (BHIV)
**Review Date:** 2026-04-23
**Classification:** Internal Sovereign Design / Strictly Confidential
**Predecessor packets:** [v14.6 Distributed Determinism](phase_v14_6_distributed_determinism_review.md), [v14.7 Live Integration Closure](phase_v14_7_live_integration_closure.md)

---

## 1. Executive Summary

v14.7 proved byte-identity against three real OS peer processes on localhost. Four task.md gates remained open: **Soft Integration Wiring**, **Parallel Execution Mode**, **Cross-Machine Validation**, and **Live Failure Demo**. v14.8 closes all four as an **additive** layer — zero changes to v14.6 (22/22 audit) and v14.7 (5/5 live integration) code paths.

### Key achievements

- **`--parallel-execute N`** — runs Sarathi and a legacy enforcer (in-tree shim or real BHIV Core via `SARATHI_LEGACY_ENFORCE_URL`) side-by-side. Semantic-decision comparator gates on `decision_id`, `decision_hash`, `decision_core_hash`, `verdict`, `error_code`, `reason`, `mode`, `enforcement.request_binding_hash`. Any divergence → `ERR_SHADOW_DIVERGENCE`, fail-closed, journaled. **Result: matches=10, divergences=0, gate_satisfied=true.**
- **`--distributed-integration N`** — cross-machine topology (`SARATHI_LISTEN_HOST` / `SARATHI_ADVERTISE_HOST` / `SARATHI_ROUTE_*_URL`) with per-hop RTT + clock-skew telemetry. Reviewer-local fallback via `SARATHI_DIST_LOOPBACK_AUTOSPAWN=1`. **Result: verified=10/10, failures=0, byte_identity_proof holds, gate=true.**
- **`--failure-demo`** — live injection of payload tampering, invalid Ed25519 signature, and bucket-drift replay against running peers. Per-scenario observation log + reviewer-repeatable `curl`/`sha256sum` commands. **Result: scenarios_passed=3/3, gate_satisfied=true.**
- **Zero regressions** — `--v14-6` audit **22/22 PASS**, `--live-integration 5` still **5/5 verified**.
- **New contract spec for BHIV team** — [ENDPOINTS_FOR_BHIV.md](../ENDPOINTS_FOR_BHIV.md) documents the 8-step peer behaviour, Ed25519 receipt protocol, and env-var cutover procedure. URLs are NOT the dependency — the wire contract is.
- **KB-11 + rewritten VC validation script** — reproducible in under 30 minutes on a clean clone, no author present.

---

## 2. Why semantic parity (and not byte-identity) is the parallel-execute gate

Two independent OS processes cannot produce byte-identical canonical responses. The response envelope carries per-process wall-clock fields (`enforced_at`, `execution.timestamp`) and per-process random fields (`enforcement_token`, `trace_id`, `span_id`, `enforcement_hash`, `propagation_chain[-1]`). These are part of the contract — they cannot match across processes.

What MUST match are the fields deterministically derived from the signed input decision:

| Class | Fields |
|---|---|
| Input-bound | `decision_id`, `decision_hash`, `decision_core_hash` |
| Policy-derived | `verdict`, `error_code`, `reason`, `mode`, `enforcement.request_binding_hash` |

If any of these diverges, Sarathi and the legacy pipeline reached different conclusions for the same input. That is the defect the comparator exists to surface. For auditor transparency, the record also captures:

- Raw `response_hash` (expected to differ)
- Structural hash with wall-clock/random fields replaced by a fixed placeholder `$SHADOW_NORMALIZED$` (reports which *other* fields drifted, if any)

Mechanism: [parallel_execution_comparator.go::CompareCanonicalResponses](../parallel_execution_comparator.go#L119).

This is how task.md's "match or fail deterministically, never silently diverge" is enforced. Every semantic divergence fires `ERR_SHADOW_DIVERGENCE` and journals the field-level diff.

---

## 3. task.md — Phase mapping with evidence

| task.md Phase | Required | v14.8 delivery | Evidence on disk |
|---|---|---|---|
| **Soft Integration Wiring** | Sarathi behind validation gate, legacy Core as fallback | `--legacy-shim` in-tree reference enforcer + `SARATHI_LEGACY_ENFORCE_URL` override (env wins). Operator policy `SARATHI_PARALLEL_POLICY={fail_closed\|legacy_fallback}`. | [legacy_enforcer_shim.go](../legacy_enforcer_shim.go), `live/legacy/legacy.jsonl` |
| **Parallel Execution Mode** | Match or fail deterministically, never silently diverge | Two-pipeline runner, semantic comparator, fail-closed on divergence, journal of every verdict | `parallel_execution_report.json` (matches=10, divergences=0), `proof_logs/shadow_divergence_log.jsonl` |
| **Cross-Machine Validation** | Machine A ↔ Machine B with latency + clock drift + async delay tolerance | `bindHost()`/`advertiseHost()` env-driven, `--peer-standalone-*` roles, per-hop RTT + clock-skew telemetry, `SARATHI_CLOCK_SKEW_TOLERANCE_MS` (default 5000 ms) | `distributed_integration_report.json` (verified=10/10, byte_identity holds), `proof_logs/cross_machine_telemetry.jsonl` |
| **Live Failure Demo** | Payload tamper / invalid signature / bucket mismatch — LIVE, not pre-recorded | `--failure-demo` automated + reviewer-live window, 3 scenarios, observation log with pre/post hashes | `failure_demo_report.json` (scenarios_passed=3), `proof_logs/failure_demo_observations.jsonl` |

**Regression gates (both still green):**

| Predecessor | Command | Result |
|---|---|---|
| v14.6 audit | `--v14-6` | 22/22 PASS |
| v14.7 live-integration | `--live-integration 5` | 5/5 verified, `gate_satisfied=true` |

---

## 4. Invariants introduced

| Code | Statement | Mechanism | Artefact |
|---|---|---|---|
| **INV-PARA-01** | For every parallel execution, either all semantic fields agree or the execution is failed closed with `ERR_SHADOW_DIVERGENCE` | [parallel_execution_comparator.go::CompareCanonicalResponses](../parallel_execution_comparator.go) | `parallel_execution_report.json::divergences=0` AND `shadow_divergence_log.jsonl` empty on green |
| **INV-DIST-X1** | With peers on a different host, Bucket disk file hashes to the same SHA-256 as the Sarathi-sealed envelope | `VerifyBucketReadback` over network | `distributed_integration_report.json::records[].match=true` for every row |
| **INV-DIST-X2** | Byte-identity survives cross-machine transport: `response_hash` + `chain_binding_hash` stable across processes for same input | `cross_machine_telemetry` aggregator | `byte_identity_proof.response_hash_set_size` stable |
| **INV-DIST-X3** | Clock skew up to `SARATHI_CLOCK_SKEW_TOLERANCE_MS` (5000 ms default) does not affect stable-form hashes | v14.6 `SkewedClock` + stable-form response hash | `peers.*.clock_skew_ms` recorded; byte-identity unchanged |
| **INV-FAIL-01** | Payload tampering → `ERR_BUCKET_READBACK_MISMATCH`, chain halts | `VerifyBucketReadback` | `failure_demo_observations.jsonl` row `scenario=payload_tamper, passed=true` |
| **INV-FAIL-02** | Ed25519 receipt signed with wrong key → HTTP 400 `ERR_DOWNSTREAM_RECEIPT_INVALID`, appended to `downstream_ack_rejections.jsonl` | [peer_common.go::VerifyReceipt](../peer_common.go) + [downstream_ack_endpoint.go](../downstream_ack_endpoint.go) | `failure_demo_observations.jsonl` row `scenario=invalid_signature, passed=true` |
| **INV-FAIL-03** | Same `decision_id` with drifted body → HTTP 409 `ERR_RESPONSE_HASH_MISMATCH` | [peer_common.go::PeerStore::PersistBody](../peer_common.go) `seenIndex` | `failure_demo_observations.jsonl` row `scenario=bucket_mismatch, passed=true` |

---

## 5. Files added (additive, no existing code paths altered)

| File | Role |
|---|---|
| [legacy_enforcer_shim.go](../legacy_enforcer_shim.go) | `--legacy-shim` reference enforcer, deterministic, reproducible on any clone |
| [parallel_execution_runner.go](../parallel_execution_runner.go) | `--parallel-execute N` orchestrator |
| [parallel_execution_comparator.go](../parallel_execution_comparator.go) | Pure semantic-parity comparator (this packet §2) |
| [distributed_integration_runner.go](../distributed_integration_runner.go) | `--distributed-integration N` orchestrator, includes `SARATHI_DIST_LOOPBACK_AUTOSPAWN` fallback |
| [cross_machine_telemetry.go](../cross_machine_telemetry.go) | RTT + clock-skew capture, per-peer aggregation |
| [failure_demo_runner.go](../failure_demo_runner.go) | `--failure-demo` live injector — 3 scenarios |

New error codes in [response_contract.go](../response_contract.go): `ERR_SHADOW_DIVERGENCE`, `ERR_LEGACY_SHIM_UNAVAILABLE`, `ERR_CROSS_MACHINE_CLOCK_SKEW_EXCESSIVE`, `ERR_CROSS_MACHINE_UNREACHABLE`.

---

## 6. Reviewer verbatim block (reproducible on clean clone)

```bash
# 0. Clean state + build
rm -rf live proof_logs/*.jsonl *_report.json
go build -o sarathi-enforcement-adapter.exe .
go test -count=1 -timeout 180s ./... | tail -5

# 1. v14.6 regression (must pass)
./sarathi-enforcement-adapter.exe --v14-6
grep "Total checks: 22  Passed: 22" audit_v14_6_report.md

# 2. v14.7 regression (must pass)
./sarathi-enforcement-adapter.exe --live-integration 5
jq '.gate_satisfied, .verified_gate_count' live_integration_report.json
# → true, 5

# 3. v14.8 parallel execution (new)
./sarathi-enforcement-adapter.exe --parallel-execute 10
jq '.gate_satisfied, .matches, .divergences' parallel_execution_report.json
# → true, 10, 0

# 4. v14.8 cross-machine (loopback fallback for single-host reviewer)
SARATHI_DIST_LOOPBACK_AUTOSPAWN=1 \
  ./sarathi-enforcement-adapter.exe --distributed-integration 10
jq '.gate_satisfied, .verified_gate_count' distributed_integration_report.json
# → true, 10

# 5. v14.8 live failure demo (new)
./sarathi-enforcement-adapter.exe --failure-demo
jq '.scenarios_passed, .scenarios_total' failure_demo_report.json
# → 3, 3
wc -l proof_logs/failure_demo_observations.jsonl
# → 3

# 6. Independent SHA proof (no author present)
DEC=$(jq -r '.records[0].decision_id' distributed_integration_report.json)
EXPECT=$(jq -r '.records[0].response_hash' distributed_integration_report.json)
sha256sum live/bucket/${DEC}.json
# → $EXPECT
```

Every line is reproducible on a clean clone. All comparisons are hash-based; no wall-clock expectations.

---

## 7. Artefact inventory

| Path | Schema | Meaning |
|---|---|---|
| `parallel_execution_report.json` | `sarathi.parallel/v14.8` | Top-level parallel-execute summary + per-execution records |
| `proof_logs/shadow_divergence_log.jsonl` | `sarathi.shadow-divergence/v14.8` | One row per parallel execution (match or divergence with field diffs) |
| `distributed_integration_report.json` | `sarathi.distributed/v14.8` | Topology, per-peer telemetry, byte-identity proof, per-execution records |
| `proof_logs/cross_machine_telemetry.jsonl` | `sarathi.cross-machine.telemetry/v14.8` | Per-probe RTT + clock-skew samples |
| `failure_demo_report.json` | `sarathi.failure-demo/v14.8` | Scenario-level pass/fail summary |
| `proof_logs/failure_demo_observations.jsonl` | `sarathi.failure-demo/v14.8` | Per-scenario observation row with pre/post hashes |
| `live/legacy/legacy.jsonl` | - | Legacy shim decision journal |

---

## 8. Risk register

| Risk | Mitigation |
|---|---|
| Breaking v14.7 localhost default | `bindHost()` default returns `127.0.0.1`; v14.7 env-var absence → bit-identical behaviour |
| Legacy shim determinism drift vs Sarathi | Shim uses same `canonical_json.go`; any drift is the diagnostic signal by design |
| Reviewer can't do cross-machine | `SARATHI_DIST_LOOPBACK_AUTOSPAWN=1` fallback proves TCP + process boundaries; real 2-machine proof optional |
| Cross-machine HTTP unauth | Out-of-scope for v14.8 (same as v14.7); add TLS at reverse proxy — Sarathi hash checks are transport-agnostic |
| Failure demo peers orphaned | `SARATHI_FAILURE_DEMO_DEADLINE_S` (default 300 s) auto-shutdown; ctrl-c handled |
| Parent-watchdog on standalone peer | `ParentPID=0` disables; optional `SARATHI_PEER_HEARTBEAT_URL` for LAN |

---

## 9. Sign-off

| Role | Name | Signature | Date |
|---|---|---|---|
| Author | Hemanth B | _________ | _________ |
| Reviewer (technical) | _________ | _________ | _________ |
| Reviewer (governance) | _________ | _________ | _________ |

**Lock criteria met:**
- [ ] `--v14-6` audit = 22/22 PASS
- [ ] `--live-integration 5` = 5/5 verified
- [ ] `--parallel-execute 10` = matches=10, divergences=0
- [ ] `--distributed-integration 10` = verified=10/10, byte-identity holds
- [ ] `--failure-demo` = scenarios_passed=3/3
- [ ] `ENDPOINTS_FOR_BHIV.md` delivered to BHIV integration owners
- [ ] `KB_11_SOVEREIGN_AUTHORITY_v14_8.md` merged
- [ ] `VC_VALIDATION_SCRIPT.md` rewritten for v14.7 + v14.8 + v14.9

---

## APPENDIX A — v14.9 Service Runtime Closure (follow-on phase)

v14.8 closed the four task.md gates (Soft Integration, Parallel Execution, Cross-Machine, Live Failure Demo). v14.9 layers the **long-lived HTTP service** required for BHIV to POST real enforcement requests and receive signed verdicts.

### A.1 Scope

| Concern | Pre-v14.9 | v14.9 |
|---|---|---|
| Enforcement entry point | one-shot CLI flags (`--live-integration N`) | long-lived `--service` HTTP server |
| TLS | operator-managed via reverse proxy | `SARATHI_SERVICE_REQUIRE_TLS=1` boot refusal + in-proc MinVersion=1.2 floor |
| Slowloris / idle-conn DoS | none | `ReadHeaderTimeout=2s`, `IdleTimeout=60s` on `http.Server` |
| Security headers | none | HSTS (`max-age=31536000`), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` |
| Rate limiting | bridge-level per-caller | edge token-bucket per API-key fingerprint (SHA-256 short digest) OR per-IP |
| API-key comparison | `!=` (timing oracle) | `crypto/subtle.ConstantTimeCompare` |
| Default-key footgun | operator discipline only | `SARATHI_SERVICE_REQUIRE_NONDEFAULT_KEYS=1` boot refusal |
| Graceful shutdown | best-effort | SIGINT/SIGTERM → `boundary.GracefulShutdown(timeout)` |
| Request tracing | correlation_id only | `X-Request-ID` middleware (honours inbound) |
| Live service gate | none | `--service-live-demo` — 8 scenarios over real HTTP |

### A.2 New files

| File | Role |
|---|---|
| [service_runtime_cli.go](service_runtime_cli.go) | `--service` / `--service-live-demo` CLI, env parsing, `bootstrapServiceBoundary`, signal handler |
| [service_boundary_security.go](service_boundary_security.go) | `ApplyServiceHardening`: header middleware, rate-limiter, TLS floor, Server tunings |
| [service_live_integration.go](service_live_integration.go) | 8-scenario live HTTP harness + `service_live_integration_report.json` |

### A.3 Modified files

- [enforcement_adapter_main.go:~1881](enforcement_adapter_main.go) — prepend v14.9 dispatch BEFORE v14.8 (7 lines).
- [gated_bridge.go:481](gated_bridge.go) — replace `req.apiKey != caller.Credential.APIKey` with `subtle.ConstantTimeCompare`; also handles `NextAPIKey` rotation window.

### A.4 v14.9 invariants

- **INV-SVC-01** — Service refuses to boot when `SARATHI_SERVICE_REQUIRE_NONDEFAULT_KEYS=1` and any caller still holds a default dev key. Artefact: startup log `[v14.9] REFUSE: default keys detected for [...]`.
- **INV-SVC-02** — Service refuses to boot when `SARATHI_SERVICE_REQUIRE_TLS=1` and no cert/key configured.
- **INV-SVC-03** — `/v1/enforce` without API key → HTTP 401. Scenario 2 of `--service-live-demo`.
- **INV-SVC-04** — `/v1/enforce` with wrong API key → HTTP 403 `INVALID_API_KEY`. Constant-time compared. Scenario 3.
- **INV-SVC-05** — `/v1/enforce` with correct key → HTTP 200 with signed passport. Scenario 4.
- **INV-SVC-06** — Malformed body → HTTP 400. Scenario 5. Oversized body → connection closed or HTTP 400. Scenario 6.
- **INV-SVC-07** — Burst beyond rate-limit → HTTP 429. Scenario 7.
- **INV-SVC-08** — `SIGINT`/`SIGTERM` → graceful shutdown within `SARATHI_SERVICE_SHUTDOWN_TIMEOUT_S` seconds.

### A.5 Additional verification gates

Add to §9 lock criteria:
- [ ] `--service-live-demo` = scenarios_passed=8/8, gate_satisfied=true
- [ ] `--service` health smoke: `curl /health` returns `bridge_active:true`; valid POST returns 200 + signed verdict; missing key returns 401; wrong key returns 403
- [ ] Self-test section §14 of VC script reproduced by reviewer

### A.6 v14.9 transparency note (no mocking)

Per explicit user request for a system-wide audit beyond the failure demo, every v14.9 code path is live:
- `--service-live-demo` boots a real `http.Server` on a real loopback port and issues real `http.Get` / `http.Post` calls. No `httptest` wrappers.
- `ApplyServiceHardening` modifies the real `*http.Server` pointer — there is no parallel "hardened stub".
- Rate-limiter state is real `sync.Mutex`-guarded `tokenBucket` structs with real clock arithmetic.
- The failure-demo scenario 2 ed25519 rejection was fixed this phase to exercise the real `ed25519.Verify()` branch (not the body-hash path). Evidence: `proof_logs/downstream_ack_rejections.jsonl` row contains `"reason":"signature verification failed"` AND `received_body_hash == response_hash` (proving the rejection is cryptographic, not hash-mismatch).

Full audit documented in [VC_VALIDATION_SCRIPT.md §17](VC_VALIDATION_SCRIPT.md) and [SERVICE_SECURITY_AUDIT_v14_9.md](SERVICE_SECURITY_AUDIT_v14_9.md).

### A.7 What v14.9 does NOT add

- No new cryptography beyond `crypto/subtle` and the existing Ed25519/SHA-256 primitives.
- No new canonicalization rules; `CanonicalMarshal` unchanged.
- No changes to any v14.6/v14.7/v14.8 invariant or artefact.
- No change to bucket persistence format or receipt envelope.
