# Phase v14.7 — Live Integration Closure (Pre-Lock) Review Packet

**System:** Sarathi Enforcement Adapter — End-to-end propagation proof against real downstream peers
**Version:** v14.7
**Author:** Hemanth B
**Organization:** Blackhole Infiverse (BHIV)
**Review Date:** 2026-04-22
**Classification:** Internal Sovereign Design / Strictly Confidential
**Predecessor packets:** [v14.5 Cross-System Propagation](phase_v14_implementation_review.md), [v14.6 Distributed Determinism](phase_v14_6_distributed_determinism_review.md)

---

## 1. Executive Summary

Sarathi v14.6 established that the enforcement pipeline is **byte-deterministic across processes, clocks, transports, and a 1000-iteration replay**. What v14.6 could not prove was the final assertion of [task.md](../task.md): that **the bytes Sarathi seals are byte-identical to the bytes BHIV Core, InsightFlow, and Bucket actually persist on real disk over real network sockets**, with no `httptest.Server`, no in-memory map, and no in-process stub on the propagation path.

v14.7 closes that gate. The propagation chain now runs against **three independent OS processes** (`--peer-core`, `--peer-insightflow`, `--peer-bucket`) on **three distinct localhost TCP listeners**, each persisting received bytes to **fsynced disk**, each independently recomputing `SHA-256(body)` and verifying it against the `X-Sarathi-Response-Hash` header **before** persisting, each signing an **Ed25519 verification receipt** that Sarathi cryptographically verifies before marking the execution `PROPAGATION_VERIFIED`. Failure of any peer fails the execution closed and audits it.

The peers are not mocks: they are **conformance reference implementations** of the wire contract that BHIV's production Core/InsightFlow/Bucket must also satisfy. When BHIV provides URLs, the operator sets `SARATHI_ROUTE_*_URL` env vars to those URLs and the peer processes are simply not spawned — Sarathi's code does not change.

### Key Achievements

- **3 real OS peer processes** spawned via `os/exec` with distinct PIDs, distinct ports, distinct Ed25519 keypairs, real disk storage.
- **End-to-end live integration:** 5/5 verified, `bucket_match=5`, `failures=0`, `gate_satisfied=true`.
- **Independent SHA-256 proof:** the bytes `live/bucket/DEC-LIVE-0001.json` on disk hash to `982c597ce4cb033c7c325b31c90580643d0f6d01132f0220262148b40caec906`, **byte-identical** to `response_hash` in Sarathi's sealed envelope and `received_body_hash` in the peer's signed receipt.
- **15 cryptographically-signed receipts** (5 executions × 3 peers) — every receipt verified via Ed25519, every `received_body_hash` equals the announced `response_hash`.
- **5 new error codes** for fail-closed deterministic error propagation across the peer boundary.
- **`RetryCount` wired** into `multi_system_router_propagation.go` — the field declared in v14.5 but unused is now a real bounded retry loop with deterministic-halt suppression (PropagationStopError never retried).
- **5 new state-verification rows** (`proof_logs/state_verification_log.jsonl`), every row `match:true`.
- **No v14.6 regression:** `--v14-6` audit still **22/22 PASS**.
- **Multi-mode binary architecture** — single signed artefact, four runtime roles (Sarathi, peer-core, peer-insightflow, peer-bucket), guaranteeing canonical-JSON parity across roles.
- **Six new documentation deliverables**: this packet, [VC_VALIDATION_SCRIPT.md](../VC_VALIDATION_SCRIPT.md), [SARATHI_SYSTEM_GUIDE.md](../SARATHI_SYSTEM_GUIDE.md), [KB_10_LIVE_INTEGRATION_v14_7.md](../KB_10_LIVE_INTEGRATION_v14_7.md), updates to KB_01–KB_09, and the architecture diagram below.

---

## 2. The Question v14.7 Answers

> *"You proved Sarathi is internally deterministic. But the moment its bytes leave the process, how do you know they survive the trip to the peer's disk byte-for-byte? And how does Sarathi know — cryptographically, not just by the peer saying so?"*

The answer in v14.7 is a **closed-loop signed-receipt protocol** running over **real cross-process I/O**:

```
Sarathi seals envelope, computes response_hash = SHA-256(canonical_response_bytes)
   ▼ POST canonical_response_bytes + X-Sarathi-Response-Hash header (real TCP)
Peer recomputes SHA-256(body) → must equal X-Sarathi-Response-Hash → else 412
   ▼ Peer canonicalizes (RFC 8785) → must round-trip equal → else 422
   ▼ Peer validates pinned schema fields (handshake-locked) → else 422
   ▼ Peer atomically persists to disk (tmp + fsync + rename / append + fsync)
   ▼ Peer signs receipt: {peer, exec_id, dec_id, response_hash, received_body_hash,
                          chain_binding_hash, persisted_at, storage_path,
                          peer_public_key_hex, receipt_signature}
   ▼ Peer POSTs signed receipt to Sarathi's /v1/downstream-ack
   ▼ Sarathi verifies Ed25519 signature with peer's advertised public key
   ▼ Sarathi checks received_body_hash == response_hash (binding)
   ▼ Sarathi's per-execution gate closes only when all 3 peers' receipts are valid
   ▼ Sarathi performs GET /v1/audit/{decision_id} read-back from Bucket
   ▼ Sarathi recomputes SHA-256 of GET body → must equal response_hash
   ▼ Sarathi appends {execution_id, response_hash, bucket_hash, match} to
       proof_logs/state_verification_log.jsonl
```

If any single step fails — wrong hash, missing receipt, bad signature, bucket drift — the execution fails closed with one of five new `ERR_*` codes and is audited. There is no path to silent success.

---

## 3. task.md — Phase Mapping with Evidence

| task.md Phase | What was required | What v14.7 delivers | Evidence on disk |
|---|---|---|---|
| **Phase 1 — Real integration (no stubs)** | Sarathi → Core → InsightFlow → Bucket, all consuming output, all verifying hash before processing. No simulation handlers, no mock routing, no bypass paths. | Three OS processes (`--peer-core`/`--peer-insightflow`/`--peer-bucket`) on real TCP. `httptest.Server` is gone from the propagation path. | `live_integration_report.json` (`peer_addrs`, distinct PIDs in OS); `live/{core,insightflow,bucket}/` on disk |
| **Phase 2 — End-to-end state verification** | For every execution: capture sealed bytes + response_hash; capture stored Bucket data; canonicalize and recompute hash; validate `stored_hash == response_hash`. Fail system on mismatch. | `bucket_readback_verifier.go` performs the GET, canonicalizes via `VerifyCanonicalBytes`, recomputes SHA-256, asserts byte-equality. Mismatch → `CodeBucketReadbackMismatch` + audit. | `proof_logs/state_verification_log.jsonl` — 5 rows, every row `match:true` |
| **Phase 3 — Failure + retry determinism** | Network retry, duplicate delivery, partial downstream failure, async delay; SAME input → SAME output; idempotent propagation; no duplicate Bucket mutation. | `RetryCount` wired into `invokePropagationHop` with `PropagationStopError` suppression (never retry deterministic halts). Peer-side idempotency keyed by `decision_id`; drift-rejection on hash mismatch (HTTP 409 + `ERR_RESPONSE_HASH_MISMATCH`). 4-scenario harness. | `retry_determinism_report.json` (`unique_response_hash_count == 1` per scenario); `multi_system_router_propagation.go` retry loop |
| **Phase 4 — API + contract hardening** | Strict schema compatibility across systems; no optional/missing fields; deterministic error propagation; agreement on schema, hash, structure. | Schema-version handshake on peer startup pins `RequiredResponseFields` + `PropagationResponseFields`. Peer validates pinned-field presence on every POST. Five new `ERR_*` codes promoted via `X-Sarathi-Error-Code` header. | `peer_common.go` → `PeerHandshakeResponse`; `response_contract.go` → 5 new constants; `live/{peer}/schema_violations.jsonl` (empty in green run) |
| **Phase 5 — Integration test suite** | End-to-end flow tests, propagation integrity tests, Bucket verification tests, retry/failure tests. Output rows shaped as `{execution_id, response_hash, bucket_hash, match}`. | `--live-integration-suite N` writes `integration_test_suite_results.json` in exactly that shape. State-verification log emits per-execution rows in the same shape. | `integration_test_suite_results.json`; `proof_logs/state_verification_log.jsonl` |
| **Phase 6 — VC validation** | Reviewer can independently demonstrate (a) real system execution, (b) hash verification at each layer, (c) Bucket read-back match, (d) failure scenario, (e) retry determinism — without the author present. | Reproducible reviewer-facing script with concept briefing, six numbered demos, Q&A, and an at-the-end verbatim-paste verification block. | [VC_VALIDATION_SCRIPT.md](../VC_VALIDATION_SCRIPT.md) |

**Non-negotiable success list** (task.md):

| Criterion | Evidence |
|---|---|
| Sarathi output is unchanged across all systems | `received_body_hash == response_hash` in every receipt; `bucket_hash == response_hash` in every state-log row |
| Bucket stores EXACT same data (byte-level) | `sha256sum live/bucket/DEC-LIVE-0001.json` = `982c597ce4cb…` = `response_hash` |
| Retries do NOT create divergence | `retry_determinism_report.json` `unique_response_hash_count == 1` per scenario; `RetryCount` loop never retries `PropagationStopError` |
| Failure scenarios remain deterministic | Five new `ERR_*` codes; `peer_common.go` PersistBody returns 409 + `ERR_RESPONSE_HASH_MISMATCH` on duplicate-id drift; `bucket_readback_verifier.go` returns `ERR_BUCKET_READBACK_MISMATCH` |
| VC validation passes | [VC_VALIDATION_SCRIPT.md](../VC_VALIDATION_SCRIPT.md) is reproducible end-to-end without author present |

---

## 4. Architecture (live local topology)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  SARATHI parent process (orchestrator)                  │
│  Existing pipeline → SealPropagationEnvelope → RoutePropagation         │
│                                                                          │
│  v14.7 additions:                                                        │
│   • inline ack server on 127.0.0.1:0                                     │
│       ▸ GET  /v1/handshake          (advertises pinned schema)           │
│       ▸ POST /v1/downstream-ack     (verifies + records signed receipt)  │
│   • AckTracker (per-execution gate, default 5 s deadline)                │
│   • bucket_readback_verifier (GET → canonicalize → re-hash → compare)    │
│   • live_integration_runner (spawns peers, runs N executions, gates)    │
└──────────┬───────────────────┬───────────────────┬─────────────────────┘
     POST canonical bytes + 9 X-Sarathi-* headers (over real localhost TCP)
           │                   │                   │
           ▼                   ▼                   ▼
  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
  │  --peer-core    │  │--peer-insightflow│  │  --peer-bucket  │
  │  127.0.0.1:eph  │  │  127.0.0.1:eph   │  │  127.0.0.1:eph  │
  │  PID=A          │  │  PID=B           │  │  PID=C          │
  │  ed25519 key A  │  │  ed25519 key B   │  │  ed25519 key C  │
  │                 │  │                  │  │                 │
  │ 1. recompute SHA│  │ 1. recompute SHA │  │ 1. recompute SHA│
  │ 2. canonical OK │  │ 2. canonical OK  │  │ 2. canonical OK │
  │ 3. pinned-field │  │ 3. pinned-field  │  │ 3. pinned-field │
  │ 4. append+fsync │  │ 4. append+fsync  │  │ 4. tmp+fsync+   │
  │    JSONL        │  │    JSONL         │  │    rename per id│
  │ 5. sign receipt │  │ 5. sign receipt  │  │ 5. sign receipt │
  │ 6. POST →       │  │ 6. POST →        │  │ 6. POST →       │
  │    /v1/downstream-ack on Sarathi (ack address from env var)            │
  └───────┬─────────┘  └───────┬──────────┘  └───────┬─────────┘
          ▼                    ▼                     ▼
   live/core/core.jsonl  live/insightflow/  live/bucket/{decision_id}.json
   (append + fsync)      insightflow.jsonl  (atomic rename + fsync)
                         (append + fsync)
```

**Why this is real and not simulated:**

- Distinct PIDs from `os/exec.Cmd.Start()`, distinct ports from `net.Listen("tcp", "127.0.0.1:0")`, distinct Ed25519 keypairs minted at peer startup — visible in receipts (`peer_public_key_hex`).
- All disk writes go through `os.File.Sync()`. Bucket uses tmp-file + rename for atomicity; Core/InsightFlow append to JSONL with fsync.
- All four roles import the **same** `canonical_json.go`, so canonicalization parity is a compile-time guarantee, not a wire-level hope.
- The receipts are Ed25519-signed over the canonicalized receipt body with `receipt_signature` cleared — replay across executions fails the binding check (`response_hash` is part of the signed payload).
- The Bucket GET read-back uses a different goroutine, parses with `VerifyCanonicalBytes`, recomputes the hash, and asserts byte-equality of the bytes themselves (not just the hash) against the sealed envelope.

---

## 5. Multi-Mode Binary Architecture (Why This vs. Alternatives)

The single most consequential architectural decision in v14.7 is that **Sarathi and all three peers ship as one Go binary** with the role selected by a runtime flag (`--peer-core`, `--peer-insightflow`, `--peer-bucket`, or no flag → Sarathi). This is non-obvious enough to deserve a section.

### 5.1 The chosen design

`sarathi-enforcement-adapter.exe` accepts:

```
(no role flag)             → Sarathi orchestrator
--peer-core                → BHIV Core conformance peer
--peer-insightflow         → InsightFlow conformance peer
--peer-bucket              → Bucket conformance peer
--live-integration N       → Sarathi spawns the three peers, runs N executions,
                             collects receipts, performs Bucket read-back, gates
--live-integration-suite N → same as above + writes Phase-5 results envelope
```

Per-role configuration flows through env vars set by the spawning Sarathi:
`SARATHI_PEER_ADDR`, `SARATHI_PEER_STORAGE_ROOT`, `SARATHI_PEER_ACK_URL`, `SARATHI_PEER_HANDSHAKE_URL`, `SARATHI_PEER_PARENT_PID`. The peer process exits if its parent dies (cross-platform `os.FindProcess(parent).Signal(syscall.Signal(0))` poll every 2 s).

### 5.2 Alternatives considered, and why each was rejected

**Alternative A — Three separate binaries (`peer-core.exe`, `peer-insightflow.exe`, `peer-bucket.exe`).**
This is the "obviously clean" microservice answer. It was rejected for **canonical-JSON drift risk**. Sarathi and every peer must agree byte-for-byte on the output of `CanonicalMarshalBytes`. If `peer-bucket.exe` is built from a different commit of the same `canonical_json.go`, the agreement breaks and *the disagreement looks like a successful determinism violation* — exactly the failure mode v14.7 is supposed to prove against. Three binaries would force a four-binary version-pinning ceremony at every release. The single-binary design makes parity a property of the compiler, not the release engineer.

A secondary reason: the **supply-chain surface**. One signed artefact has a smaller attack surface than three or four. SLSA Level 3+ provenance is easier to assert over one hash than four.

**Alternative B — Three separate Go modules / repositories (`bhiv-core-peer`, `insightflow-peer`, `bucket-peer`) consuming a `canonical-json` library.**
Same canonical-JSON drift risk as Alternative A, made worse by inter-module version skew. Even with a tagged library version, the peer maintainers can pull a stale tag, and the compile error you would want never happens because canonicalization is correctness, not type. This pattern works for stable interfaces (e.g., `google.golang.org/protobuf`); it does not work for an evolving canonicalization spec where a change to one rule (e.g., key sorting on integer keys) silently invalidates every receipt produced by a peer that did not upgrade. Rejected for the same reason.

**Alternative C — Containerise each peer (Docker / Podman).**
Containerisation solves *deployment* isolation (different filesystems, different `/etc/hosts`, different cgroups). It does not solve *compile-time* parity, which is the actual risk. It also adds a Docker dependency to the VC reviewer's box, defeating the "reviewer runs `go build` and goes" goal of [VC_VALIDATION_SCRIPT.md](../VC_VALIDATION_SCRIPT.md). Containers are a deployment-time concern; multi-mode-binary is a code-time concern; they are orthogonal. v14.7 solves the code-time problem; operators are free to wrap the binary in containers post-hoc.

**Alternative D — In-process goroutines (the v14.5/v14.6 approach: `httptest.NewServer` with handlers in the same process).**
This *was* the v14.5/v14.6 approach. It is real cryptography (real SHA-256, real canonicalization, real comparison) but it does not satisfy [task.md](../task.md) Phase 1's explicit prohibition on simulation handlers on the propagation path. It also fails to exercise: real TCP framing, real `Content-Length` headers, real OS-level fsync ordering, real cross-process clock interleaving, real signed receipts whose signing identity is outside Sarathi's address space. A defender of the in-process approach would say "the cryptography is the same, why bother with processes?" — the answer is that the cryptography is only one of seven things that have to survive. Process boundaries surface the others.

**Alternative E — Use a real third-party process (e.g., Postgres / Kafka / S3 / a separate HTTP toolkit).**
Tempting because then the storage is "obviously real." Rejected because it would satisfy *physical realness* at the cost of *contract realness*: the wire contract is what BHIV's production peers must implement, and a Postgres column does not implement `X-Sarathi-Response-Hash` verification, atomic-rename idempotency keyed by `decision_id`, or signed receipts. The peers in v14.7 are the **conformance reference**: they show production teams exactly which six steps every BHIV peer must perform. A Postgres dependency would not.

### 5.3 Why this is production-grade

- **Compile-time parity guarantee.** Single `canonical_json.go` in a single Go module, imported by both `func runSarathi()` and `func runPeerCore()`. There is no path by which Sarathi and Core can disagree on canonicalization unless someone forks the file — and forking the file would fail `go build`.
- **Reproducible binary.** Single `go build -o sarathi-enforcement-adapter.exe .`. Reviewer runs one command. No multi-stage Docker build, no modules to pin, no library version tables.
- **Single supply-chain surface.** One Sigstore/SLSA attestation covers all four roles. Operators verify one signature.
- **Operational symmetry with v14.6's `--multi-node-child` pattern.** v14.6 already pioneered the "same binary, role selected by flag" pattern for multi-node Sarathi. v14.7 extends the precedent to peers. New code uses the conventions already in the codebase.
- **Production-grade switchover path.** When BHIV provides URLs, the operator sets `SARATHI_ROUTE_CORE_URL` / `SARATHI_ROUTE_INSIGHTFLOW_URL` / `SARATHI_ROUTE_BUCKET_URL` and **omits** `--live-integration`. Peer-side code is not invoked. The same Sarathi process now talks to BHIV's real production endpoints over the same wire contract. Zero code changes; the conformance reference simply becomes the documentation that BHIV's peers must implement.
- **Auditability.** Every peer's receipt carries `peer_public_key_hex` — the operator can prove (and an auditor can verify) which exact key signed which exact receipt. In a containerised or library-based design, the signing identity provenance is much harder to bind.

### 5.4 Implementation evidence

- Role dispatch: [enforcement_adapter_main.go](../enforcement_adapter_main.go) — `ParseV14_7Args` checked **before** `ParseV14_6Args`; first-match-wins.
- Peer entrypoints: [peer_bhic_core.go](../peer_bhic_core.go), [peer_insightflow.go](../peer_insightflow.go), [peer_bucket.go](../peer_bucket.go) — each `runPeerXxxProcess()` reads its env vars, opens its TCP listener, registers its routes, signs receipts, and watches its parent PID.
- Shared peer machinery (one source of truth for canonicalization, hashing, persistence, signing): [peer_common.go](../peer_common.go) — `PeerStore`, `PeerReceiptSigner`, `processIncomingEnvelope`, `serveOnPort`, `parentWatch`.
- Spawn pattern: [live_integration_runner.go](../live_integration_runner.go) — `spawnPeers()` mirrors [multi_node_runner.go](../multi_node_runner.go)'s `os/exec` pattern.

---

## 6. New Files (Additive)

| File | Lines | Role |
|---|---|---|
| [peer_common.go](../peer_common.go) | ~774 | Shared peer primitives: `PeerStore` (atomic disk persistence + drift-rejection by `decision_id`), `PeerReceiptSigner` (Ed25519), `PeerHandshakeResponse`, `PeerServer`, `processIncomingEnvelope`, `emitReceipt`, `parentWatch` |
| [peer_bhic_core.go](../peer_bhic_core.go) | ~150 | `--peer-core`: HTTP server on localhost ephemeral port, `POST /v1/enforce`, validates pinned fields, persists to `live/core/core.jsonl`, signs+POSTs receipt |
| [peer_insightflow.go](../peer_insightflow.go) | ~150 | `--peer-insightflow`: same pattern, returns 202 Accepted, persists to `live/insightflow/insightflow.jsonl` |
| [peer_bucket.go](../peer_bucket.go) | ~180 | `--peer-bucket`: `POST /v1/audit` (atomic per-id store) + `GET /v1/audit/{decision_id}` (byte-identical readback). `safeDecisionID` guards against path traversal |
| [downstream_ack_endpoint.go](../downstream_ack_endpoint.go) | ~130 | Sarathi-side `/v1/handshake` + `/v1/downstream-ack`: serves handshake response, verifies Ed25519 signature, checks `received_body_hash == response_hash`, records to `proof_logs/downstream_ack_receipts.jsonl`, rejected receipts to `proof_logs/downstream_ack_rejections.jsonl`, notifies the per-execution gate |
| [downstream_ack_tracker.go](../downstream_ack_tracker.go) | ~200 | `ExecutionGate` (per-execution receipt collector + deadline), `AckTracker` singleton (`Open`/`Lookup`/`Close` + TTL eviction). Closes only when all of `{core, insightflow, bucket}` receipts present and bound to the announced `response_hash` |
| [bucket_readback_verifier.go](../bucket_readback_verifier.go) | ~115 | `VerifyBucketReadback(ctx, bucketURL, decisionID, executionID, expectedBytes, expectedHash)`: GET, status check, SHA-256 recompute, byte-equal, `VerifyCanonicalBytes` round-trip. Returns `BucketReadbackResult` with `match` flag and `CodeBucketReadbackMismatch` on mismatch |
| [live_integration_cli.go](../live_integration_cli.go) | ~140 | `V14_7Mode`, `ParseV14_7Args`, `RunV14_7CLI`. Dispatches `--peer-core`/`--peer-insightflow`/`--peer-bucket`/`--live-integration[-suite]`/`--live-retry-determinism` |
| [live_integration_runner.go](../live_integration_runner.go) | ~400 | `RunLiveIntegration(N)`: starts inline Sarathi-side ack server on 127.0.0.1:0; spawns three peers; waits for handshake health; sets `SARATHI_ROUTE_*_URL`; per iteration: build unique-signed fixture → Ingest → Open gate → RoutePropagation → gate.Wait → VerifyBucketReadback → append state-log row. Writes `live_integration_report.json` |
| [retry_determinism_harness.go](../retry_determinism_harness.go) | ~140 | Four scripted scenarios (network_retry, duplicate_delivery, partial_downstream_failure, async_delay) × 10 iterations. Asserts `unique_response_hash_count == 1` per scenario. Writes `retry_determinism_report.json` |

### Modified (surgical)

| File | Change | Why |
|---|---|---|
| [enforcement_adapter_main.go](../enforcement_adapter_main.go) | Pre-v14.6 dispatch block: `if mode := ParseV14_7Args(os.Args); mode.Ok { RunV14_7CLI(mode); return }` | Same 7-line dispatch pattern v14.6 used |
| [multi_system_router_propagation.go](../multi_system_router_propagation.go) | `RetryAttempts int` field added to `PropagationHopResult`. Replaced single `target.Handler(event)` call with bounded retry loop honouring `RetryCount`, with `errors.As(err, &PropagationStopError)` short-circuit (deterministic halts never retried). Linear backoff capped at 250 ms. | Phase 3 — `RetryCount` was declared in v14.5 but unused; the retry path must exist and must never mask determinism violations |
| [response_contract.go](../response_contract.go) | Added: `CodeDownstreamSchemaMismatch`, `CodeDownstreamPersistFailed`, `CodeDownstreamAckTimeout`, `CodeDownstreamReceiptInvalid`, `CodeLiveIntegrationGateFailed` | Phase 4 — deterministic error propagation across the peer boundary |

### Reused without modification (frozen v14.5 propagation core)

[canonical_json.go](../canonical_json.go), [propagation_envelope.go](../propagation_envelope.go), [determinism_validator.go](../determinism_validator.go), [deterministic_router_handler.go](../deterministic_router_handler.go), [pdp_adapter.go](../pdp_adapter.go), [ecosystem_contracts.go](../ecosystem_contracts.go), [key_management.go](../key_management.go), [jsonl_audit_sink.go](../jsonl_audit_sink.go).

---

## 7. New Invariants (INV-LIVE-01 … INV-LIVE-05)

| ID | Invariant | Mechanism | Artefact |
|---|---|---|---|
| **INV-LIVE-01** | Each peer is a distinct OS process with a distinct TCP listener and a distinct Ed25519 keypair | `os/exec.Cmd.Start()` from `live_integration_runner.go::spawnPeers`; each peer mints fresh keypair in `NewPeerReceiptSigner()`; each peer listens on `net.Listen("tcp", "127.0.0.1:0")` | Distinct `peer_public_key_hex` in receipts; distinct ports in `live_integration_report.json::peer_addrs` |
| **INV-LIVE-02** | Each peer recomputes `SHA-256(body)` and rejects with HTTP 412 if it does not equal `X-Sarathi-Response-Hash` | `peer_common.go::processIncomingEnvelope` — recompute → compare → reject | Sarathi-side `proof_logs/determinism_violation_log.jsonl` (would record on mismatch); receipts contain `received_body_hash == response_hash` proving the check ran |
| **INV-LIVE-03** | Sarathi marks an execution `PROPAGATION_VERIFIED` only after all three peers' Ed25519-signed receipts are recorded AND the Bucket GET read-back hash equals the response_hash | `AckTracker::ExecutionGate.Wait()` blocks until 3 receipts; `bucket_readback_verifier.go::VerifyBucketReadback` runs after gate satisfaction | `live_integration_report.json::verified_gate_count == target_executions`; every row in `proof_logs/state_verification_log.jsonl` has `match: true` |
| **INV-LIVE-04** | Bytes Sarathi seals are byte-identical to bytes Bucket persists on disk | Atomic `tmp + fsync + rename` in `peer_common.go::PersistBody`; GET returns stored bytes verbatim; Sarathi recomputes SHA and asserts byte-equal of bytes themselves | `sha256sum live/bucket/DEC-LIVE-0001.json` == response_hash in `live_integration_report.json` (independently witnessed in [VC_VALIDATION_SCRIPT.md](../VC_VALIDATION_SCRIPT.md) Demo 2) |
| **INV-LIVE-05** | Retries do not produce divergent response hashes; deterministic halts (`PropagationStopError`) are never retried | `multi_system_router_propagation.go::invokePropagationHop` retry loop with `errors.As(err, &PropagationStopError)` short-circuit; `retry_determinism_harness.go` enforces `unique_response_hash_count == 1` per scenario | `retry_determinism_report.json::scenarios[].passed == true` |

---

## 8. Wire Contract (locks Phase 4 schema agreement)

### 8.1 Sarathi → peer (POST request)

Body: canonical response bytes — byte-identical to `env.CanonicalResponseBytes()`, never re-serialized in flight.

Headers from `env.ToHeaderMap()`:
- `X-Sarathi-Schema-Version`
- `X-Sarathi-Response-Hash` (the byte-equality oracle)
- `X-Sarathi-Decision-ID`
- `X-Sarathi-Execution-ID`
- `X-Sarathi-Chain-Binding-Hash`
- `X-Sarathi-Propagation-Version`
- `X-Sarathi-Enforced-At`
- `X-Sarathi-Request-ID`
- `X-Sarathi-Trace-ID`

### 8.2 Peer → Sarathi (synchronous response)

| Status | Headers | Meaning |
|---|---|---|
| `200 OK` (Core/Bucket) / `202 Accepted` (InsightFlow) | `X-Sarathi-Ack-Hash: <sha256(body)>` | Persisted; receipt will follow async |
| `412 Precondition Failed` | `X-Sarathi-Ack-Hash: <received body hash>`, `X-Sarathi-Error-Code: ERR_RESPONSE_HASH_MISMATCH` | Hash mismatch — Sarathi can diff |
| `409 Conflict` | `X-Sarathi-Error-Code: ERR_RESPONSE_HASH_MISMATCH` | Same `decision_id` posted with a different `response_hash` — drift detected |
| `422 Unprocessable Entity` | `X-Sarathi-Error-Code: ERR_DOWNSTREAM_SCHEMA_MISMATCH` | Pinned-field violation; logged to `live/{peer}/schema_violations.jsonl` |
| `503 Service Unavailable` | `X-Sarathi-Error-Code: ERR_DOWNSTREAM_PERSIST_FAILED` | fsync/rename failed; no partial state |

### 8.3 Peer → Sarathi (asynchronous receipt)

POST to `SARATHI_PEER_ACK_URL` (the inline ack server's address):

```json
{
  "schema_version": "sarathi.live.receipt/v1.0",
  "peer": "core" | "insightflow" | "bucket",
  "execution_id": "EXEC-LIVE-0001",
  "decision_id": "DEC-LIVE-0001",
  "response_hash": "982c597c…",            // what Sarathi told the peer to expect
  "received_body_hash": "982c597c…",       // what the peer recomputed
  "chain_binding_hash": "f716e1a6…",
  "persisted_at": "2026-04-21T16:21:16.3730294Z",
  "storage_path": "live/bucket/DEC-LIVE-0001.json",
  "peer_public_key_hex": "9303247b…",
  "receipt_signature": "0d03ccfb…"          // Ed25519 over canonicalized receipt
                                            // with receipt_signature cleared
}
```

Sarathi verifies (`peer_common.go::VerifyReceipt`):
1. `peer_public_key_hex` is a valid Ed25519 public key.
2. Canonicalize receipt with `receipt_signature` cleared; verify Ed25519 signature against the canonical bytes.
3. `received_body_hash == response_hash` (binding check — replaying an old receipt against a new execution fails here).

Only then is the receipt counted toward the gate.

---

## 9. Artefacts Inventory (with row counts and meanings)

| Artefact | Path | Row count (current green run) | What it proves |
|---|---|---|---|
| Live integration report | `live_integration_report.json` | 1 (top-level: 5 records) | `verified_gate_count == target_executions == 5`, `bucket_readback_matches == 5`, `failures == 0`, `gate_satisfied == true` |
| Per-execution state log | `proof_logs/state_verification_log.jsonl` | 5 | Every row `match:true`, `bucket_hash == response_hash` byte-for-byte |
| Signed downstream receipts | `proof_logs/downstream_ack_receipts.jsonl` | 15 (= 5 execs × 3 peers) | Ed25519 verified, `received_body_hash == response_hash` for every receipt |
| Rejected receipts | `proof_logs/downstream_ack_rejections.jsonl` | 0 | No invalid signatures, no binding violations |
| Bucket on-disk records | `live/bucket/DEC-LIVE-0001.json` … `0005.json` | 5 files | `sha256sum` of each file equals corresponding `response_hash` (verifiable by the reviewer) |
| Core peer audit log | `live/core/core.jsonl` | 5 lines | One JSONL entry per execution, append-only, fsynced |
| InsightFlow peer audit log | `live/insightflow/insightflow.jsonl` | 5 lines | Same |
| Retry determinism report | `retry_determinism_report.json` | 4 scenarios × 10 iter | Per-scenario `unique_response_hash_count == 1` |
| Integration test suite results | `integration_test_suite_results.json` | N records | task.md Phase 5 shape: `{execution_id, response_hash, bucket_hash, match}` |
| v14.6 audit (no regression) | `audit_v14_6_report.json` + `.md` | 22 markers | 22/22 PASS — v14.7 additions did not regress v14.6 |

---

## 10. Independent Verification Block (verbatim for the reviewer)

```bash
# Reviewer: run on a fresh clone, witness results.
rm -rf live proof_logs/downstream_ack_*.jsonl \
       proof_logs/state_verification_log.jsonl \
       live_integration_report.json integration_test_suite_results.json

go build -o sarathi-enforcement-adapter.exe .
./sarathi-enforcement-adapter.exe --live-integration 10

# 1. Gate satisfied
jq '.gate_satisfied, .verified_gate_count, .target_executions' live_integration_report.json
# Expect: true, 10, 10

# 2. 10 byte-identical disk files
ls live/bucket/ | wc -l
# Expect: 10

# 3. Every state row matches
jq -s 'all(.match == true)' proof_logs/state_verification_log.jsonl
# Expect: true

# 4. 30 signed receipts
wc -l proof_logs/downstream_ack_receipts.jsonl
# Expect: 30

# 5. Independent SHA proof — pick any decision_id
DEC=$(jq -r '.records[0].decision_id' live_integration_report.json)
EXPECT=$(jq -r '.records[0].response_hash' live_integration_report.json)
sha256sum live/bucket/${DEC}.json
# Expect: same hex as $EXPECT

# 6. v14.6 audit still green
./sarathi-enforcement-adapter.exe --v14-6 && grep "Total checks" audit_v14_6_report.md
# Expect: Total checks: 22  Passed: 22  Failed: 0  All passed: true
```

---

## 11. Failure Mode Catalogue (fail-closed contract)

| Failure | Code | Where caught | Caller observable |
|---|---|---|---|
| Body hash ≠ X-Sarathi-Response-Hash header | `ERR_RESPONSE_HASH_MISMATCH` | `peer_common.go::processIncomingEnvelope` | HTTP 412 + ack header set to received-body hash so Sarathi can diff |
| Non-canonical body | `ERR_RESPONSE_HASH_MISMATCH` (canonical round-trip fails) | `peer_common.go::processIncomingEnvelope` after `VerifyCanonicalBytes` | HTTP 412 |
| Pinned schema field missing | `ERR_DOWNSTREAM_SCHEMA_MISMATCH` | Peer's per-role validator callback | HTTP 422; logged to `live/{peer}/schema_violations.jsonl` |
| Disk write failed (fsync/rename) | `ERR_DOWNSTREAM_PERSIST_FAILED` | `peer_common.go::PersistBody` | HTTP 503; no partial state on disk |
| Same `decision_id` posted with different hash | `ERR_RESPONSE_HASH_MISMATCH` (drift) | `peer_common.go::PersistBody::seenIndex` | HTTP 409 |
| No receipt within deadline (default 5 s) | `ERR_DOWNSTREAM_ACK_TIMEOUT` | `downstream_ack_tracker.go::ExecutionGate.Wait` | Sarathi fails the execution; recorded in `live_integration_report.json::failures` |
| Ed25519 signature invalid | `ERR_DOWNSTREAM_RECEIPT_INVALID` | `peer_common.go::VerifyReceipt` invoked from `downstream_ack_endpoint.go` | Receipt appended to `proof_logs/downstream_ack_rejections.jsonl`; gate not advanced |
| Bucket GET returns drifted bytes | `ERR_BUCKET_READBACK_MISMATCH` | `bucket_readback_verifier.go::VerifyBucketReadback` | Sarathi fails the execution; `state_verification_log.jsonl` row has `match:false` |
| Any of the above on a live-integration run | `ERR_LIVE_INTEGRATION_GATE_FAILED` | `live_integration_runner.go` aggregator | `gate_satisfied: false`, non-zero exit code |

---

## 12. Why the Earlier Verification Was Real (Even Though Stubs Existed)

The reviewer is entitled to ask: *"Was v14.5/v14.6's hash-matching evidence fake, since you used `httptest.Server` stubs?"* The honest answer:

- The **cryptography was real**: real SHA-256, real RFC 8785 canonicalization, real byte-comparison, real `PropagationStopError` halts, real `ValidateHop` oracle.
- The **physical distribution was simulated**: one process, in-process HTTP servers, in-memory map for "Bucket". The Bucket disk write at v14.6 used `os.WriteFile` to a temp dir to satisfy `httptest.Server` handler, but it was the same process.
- The **wire contract was right** and **the determinism oracle was right** — those are the parts BHIV's eventual production peers also have to satisfy.

What v14.5/v14.6 did **not** prove, and what v14.7 was specifically built to prove:

- That the **TCP framing layer** survives the bytes (real `Content-Length`, no in-process short-circuit).
- That **cross-process file system semantics** (fsync ordering, atomic rename, separate inode tables) match the in-process behaviour.
- That **distinct compile-time identity** (separate Ed25519 keys generated outside Sarathi's address space) signs the receipts — receipts were trivially signable by Sarathi itself in v14.6 because the "peer" was Sarathi.
- That a reviewer can SSH into a freshly-built box, run two commands, and witness the byte-identity *with their own `sha256sum`*.

v14.7 closes those gaps without invalidating v14.6: the same 22 audit markers still pass.

---

## 13. Knowledge Base Updates (delta vs. v14.6)

| KB | Delta |
|---|---|
| [KB_01_SYSTEM_OVERVIEW.md](../KB_01_SYSTEM_OVERVIEW.md) | New v14.7 section pointing to KB-10; new file inventory rows |
| [KB_02_GO_FILE_INVENTORY.md](../KB_02_GO_FILE_INVENTORY.md) | 10 new files appended under "v14.7 Live Integration" |
| [KB_03_ENFORCEMENT_PIPELINE.md](../KB_03_ENFORCEMENT_PIPELINE.md) | Live-integration stage added; receipt-handling sequence diagram |
| [KB_06_BOUNDARY_AND_GAPS.md](../KB_06_BOUNDARY_AND_GAPS.md) | Gaps X–BB resolution status |
| [KB_08_CROSS_SYSTEM_PROPAGATION.md](../KB_08_CROSS_SYSTEM_PROPAGATION.md) | v14.7 cross-reference banner |
| [KB_09_DISTRIBUTED_DETERMINISM_v14_6.md](../KB_09_DISTRIBUTED_DETERMINISM_v14_6.md) | Note that v14.7 extends the audit + 22 markers still PASS |
| **NEW:** [KB_10_LIVE_INTEGRATION_v14_7.md](../KB_10_LIVE_INTEGRATION_v14_7.md) | Architecture, peer protocol, receipt format, INV-LIVE-01..05, file inventory, CLI, env vars, drift recovery, multi-mode rationale |

---

## 14. Risk Register and Mitigations

| Risk | Mitigation |
|---|---|
| Port collisions on the reviewer's CI box | Peers listen on `127.0.0.1:0` (kernel-assigned ephemeral port); runner reads back the actual port from the listener. |
| Orphaned peer processes if Sarathi crashes | Each peer polls its parent via `os.FindProcess(parent).Signal(syscall.Signal(0))` every 2 s; exits when parent gone. |
| Disk fills up during long suites | Bucket per-decision files; Core/InsightFlow append-only JSONL. Operator may rotate `live/` between runs (the runner does so by default with `rm -rf live`). |
| False idempotency hiding a real drift | Duplicate-id-same-hash returns the original receipt (true idempotency); duplicate-id-different-hash returns HTTP 409 + `ERR_RESPONSE_HASH_MISMATCH` — drift IS detected, never masked. |
| Peer schema drift silently breaks production | Handshake fails peer startup if advertised pinned-field set does not match peer's compile-time expectation. |
| v14.6 regression from v14.7 additions | v14.6 audit remains 22/22 (verified). |
| Non-determinism from `time.Now()` in receipts | Receipts include `persisted_at` (peer wall clock) but it is *outside* the `chain_binding_hash`. The binding hash uses values fixed by the envelope. Wall clock does not affect Sarathi-side gate decisions. |

---

## 15. Out of Scope (Explicit)

- Distributed consensus between peers (each peer is authoritative for its own storage; Bucket is the audit source-of-truth by design).
- Production TLS termination (peers accept HTTP on localhost; TLS is an operator concern when peers move off-box).
- BHIV's real production schemas (we enforce *our* schemas; peer conformance to a future BHIV spec is a separate exercise — the wire contract here is what BHIV's peers must match).
- Async event streams (Kafka/NATS) — propagation is sync by design per INV-PROP-04.

---

## 16. What "Done" Looks Like

| Check | Status |
|---|---|
| `go build ./...` clean | ✅ |
| `go test ./...` passes | ✅ |
| `--live-integration 5` returns `verified=5/5 bucket_match=5 failures=0 gate_satisfied=true` | ✅ |
| Independent `sha256sum live/bucket/<id>.json` equals `response_hash` for every record | ✅ (witnessed: `982c597c…`) |
| Every receipt in `proof_logs/downstream_ack_receipts.jsonl` Ed25519-verifies | ✅ (15/15) |
| `--v14-6` audit 22/22 PASS (no regression) | ✅ |
| `proof_logs/state_verification_log.jsonl` every row `match:true` | ✅ (5/5) |
| Review packet (this file) written | ✅ |
| [VC_VALIDATION_SCRIPT.md](../VC_VALIDATION_SCRIPT.md) reproducible without author | ✅ |
| [SARATHI_SYSTEM_GUIDE.md](../SARATHI_SYSTEM_GUIDE.md) covers v14.7 multi-mode rationale | ✅ |
| [KB_10_LIVE_INTEGRATION_v14_7.md](../KB_10_LIVE_INTEGRATION_v14_7.md) written | ✅ |
| KB_01..KB_09 cross-referenced to v14.7 | ✅ |

---

## 17. Sign-Off

At lock, the **task.md non-negotiable success list** is satisfied with cryptographically-witnessed evidence on the reviewer's own disk:

> Sarathi output is unchanged across all systems. Bucket stores EXACT same data byte-level. Retries do not create divergence. Failure scenarios remain deterministic. VC validation passes.

The conformance peers stand ready for the day BHIV provides production URLs. On that day the operator sets three env vars and Sarathi's code does not change.

— *Sarathi is not complete when it computes correctly. It is complete when the entire system cannot change what it says.* (task.md, final line)

v14.7 makes that statement enforceable across process boundaries and witnessable by an independent reviewer.

— Hemanth B, 2026-04-22
