# Sarathi Enforcement Adapter — TANTRA Integration Handoff

**Audience:** Nupur (InsightFlow Convergence), NICAI + SVACS integration owners
**Scope:** Live TANTRA execution participation. Wire contract only.
**Status:** Integration-ready. No outstanding blockers on the Sarathi side.

This document defines exactly what Sarathi sends, what it expects back, and the
deterministic rules that govern the `Core → Sarathi → Bucket → InsightFlow`
chain. Anything not listed here is **out of integration scope** and should not
be relied on.

---

## 1. Enforcement chain (deterministic order)

```
   Upstream PDP (Sovereign / Core decision)
                │  signed decision bytes
                ▼
        Sarathi Enforcement
                │  sealed canonical response bytes
                ▼
   ┌──── in-chain, ack-required, deterministic order ────┐
   │                                                     │
   ▼                                                     ▼
 BHIV Core (sync)  ──▶  Bucket (sync, audit)  ──▶  InsightFlow (digest-only)
```

Rules:

- **Order is fixed**: Core → Bucket → InsightFlow.
- **Core and Bucket are in-chain and ack-required.** Missing or invalid ack → chain halts, downstream peers receive a `CHAIN_HALTED` notice.
- **InsightFlow is digest-only (read-only consumer).** It receives fingerprints and convergence signals; it does **not** receive the full enforcement body and cannot mutate, re-enter, or reorder the chain.
- **Nothing downstream can re-enter the enforcement gate.** Re-entry attempts are rejected at the bridge before policy evaluation.

---

## 2. trace_id continuity contract

### 2.1 Where trace_id originates
- `trace_id` is an **upstream property** — it must be present on the inbound decision/request.
- Production mode rejects requests that lack an inbound `trace_id`. Sarathi does **not** mint a trace_id for inbound traffic in production.

### 2.2 How it is preserved
- `trace_id` is sealed into an immutable propagation envelope at decision ingestion.
- The envelope has no public mutator. Any subsequent hop that attempts to mutate it fails the chain-binding verification.
- Every outbound HTTP request and every signed peer receipt carries the same `trace_id` bytes verbatim.

### 2.3 What downstream peers MUST NOT do
- Do **not** regenerate, normalize, or re-format `trace_id`.
- Do **not** strip or lowercase the value.
- Do **not** echo a different `trace_id` in the ack — the receipt is rejected and the chain halts.

### 2.4 Validation
- The four-element propagation chain hash is bound to `trace_id`. Any drift invalidates the chain binding and produces `ERR_PROPAGATION_CHAIN_BROKEN`.

---

## 3. Outbound headers (every in-chain hop)

These nine headers are present on **every** outbound request from Sarathi to a downstream peer. They are the integration contract — downstream services must read them, log them, and echo the relevant ones in the ack.

| Header                       | Meaning                                                              | Echo required in ack |
|------------------------------|----------------------------------------------------------------------|----------------------|
| `X-Sarathi-Trace-ID`         | Upstream trace identifier. Constant across all hops.                 | Yes                  |
| `X-Sarathi-Span-ID`          | Span identifier at envelope creation.                                | Optional             |
| `X-Sarathi-Correlation-ID`   | Upstream correlation identifier (propagated unchanged).              | Optional             |
| `X-Sarathi-Decision-ID`      | PDP decision identifier.                                             | Yes                  |
| `X-Sarathi-Execution-ID`     | Sarathi execution identifier.                                        | Yes                  |
| `X-Sarathi-Response-Hash`    | SHA-256 hex of the canonical response bytes being sent.              | **Yes — exact match**|
| `X-Sarathi-Chain-Binding`    | SHA-256 hex of the four-element propagation chain.                   | Optional             |
| `X-Sarathi-Enforcement-Hash` | SHA-256 hex of the enforcement result.                               | Optional             |
| `X-Sarathi-Schema-Version`   | Propagation envelope schema version.                                 | Yes                  |

For digest-only targets (e.g. InsightFlow process endpoint), an additional
header is set:

| Header                     | Meaning                                                          |
|----------------------------|------------------------------------------------------------------|
| `X-Sarathi-Digest-Only`    | `true` — body is fingerprint only; no ack-hash echo required.     |

---

## 4. Downstream acknowledgement contract

Applies to in-chain peers (BHIV Core, Bucket). InsightFlow is digest-only and
exempt from receipt signing but should still 2xx the request.

### 4.1 Peer must POST a signed receipt to Sarathi's ack endpoint

Sarathi exposes:

```
POST /v1/handshake          (one-time peer handshake)
POST /v1/downstream-ack     (per-execution signed receipt)
```

### 4.2 Receipt body (JSON, canonical)

| Field                 | Type   | Notes                                                            |
|-----------------------|--------|------------------------------------------------------------------|
| `schema_version`      | string | Must equal the live peer-receipt schema version Sarathi declares.|
| `peer_id`             | string | Stable peer identifier registered at handshake.                  |
| `peer_public_key_hex` | string | Ed25519 public key for verification (hex).                       |
| `trace_id`            | string | Exact value Sarathi sent. Mismatch → rejected.                   |
| `decision_id`         | string | Echo of `X-Sarathi-Decision-ID`.                                  |
| `execution_id`        | string | Echo of `X-Sarathi-Execution-ID`.                                 |
| `received_body_hash`  | string | SHA-256 hex Sarathi sent in `X-Sarathi-Response-Hash`.            |
| `response_hash`       | string | Same as `received_body_hash` — receipt also self-binds to it.    |
| `received_at`         | string | RFC3339Nano timestamp.                                            |
| `receipt_signature`   | string | Ed25519 signature over the canonical receipt body with the       |
|                       |        | `receipt_signature` field cleared, hex-encoded.                  |

### 4.3 Rules

- `received_body_hash` **must equal** `response_hash` in the same receipt.
- `received_body_hash` **must equal** the `X-Sarathi-Response-Hash` Sarathi sent.
  - Mismatch → ack rejected with `ERR_RESPONSE_HASH_MISMATCH`, chain halts.
- Signature verification uses the `peer_public_key_hex` embedded in the
  receipt. Invalid signature → `ERR_DOWNSTREAM_RECEIPT_INVALID`.
- Per-execution ack gate timeout: 5000 ms by default (operator-configurable).
  Missed ack → execution gate fails, chain halt event recorded.

### 4.4 What peers MUST NOT do
- Do **not** re-serialize the body before hashing — Sarathi sends canonical
  bytes; any pretty-print, key reorder, or whitespace change breaks the hash.
- Do **not** sign a hash other than the receipt's own canonical bytes.
- Do **not** alter the `trace_id` or `decision_id`.

---

## 5. InsightFlow propagation contract (digest-only)

InsightFlow is a **read-only consumer**. It receives four schema shapes,
one per endpoint, in the deterministic order Sarathi emits them.

| Endpoint                  | Direction | Body shape                              | Ack required        |
|---------------------------|-----------|-----------------------------------------|---------------------|
| `POST /sarathi_trigger`   | Sarathi → IF | Start-of-trace signal                | 2xx only            |
| `POST /core_execute`      | Sarathi → IF | Multi-hop event with hop counter     | 2xx only            |
| `POST /bucket_persist`    | Sarathi → IF | Bucket persistence fingerprint       | 2xx only            |
| `POST /insightflow_process` | Sarathi → IF | Convergence verdict (PASS/FAIL)    | 2xx only            |
| `GET  /bucket/verify/{trace_id}` | IF → Bucket (or Sarathi-mediated) | Trace-level verification probe | JSON body |

### 5.1 Common fields (every InsightFlow body)

| Field                | Type   | Notes                                                     |
|----------------------|--------|-----------------------------------------------------------|
| `trace_id`           | string | Exact upstream trace_id, unchanged.                       |
| `source_system`      | string | Always `"Sarathi"` for outbound from Sarathi.             |
| `event_type`         | string | One of the four endpoint identifiers above.               |
| `timestamp`          | string | RFC3339Nano.                                              |
| `payload_hash`       | string | SHA-256 hex of the canonical payload (digest commitment). |
| `schema_version`     | string | Sarathi InsightFlow schema version Sarathi declares.      |

### 5.2 Per-endpoint shape (minimum required keys)

**Trigger (start-of-trace):**
```
{
  "trace_id", "source_system", "event_type": "sarathi_trigger",
  "payload": { "request_id", "user_id", "query",
               "data": { "decision_id", "verdict",
                         "decision_hash", "response_hash", "enforcement_hash" } }
}
```

**Core execute (multi-hop):**
```
{
  "trace_id", "origin_system": "Sarathi", "current_system": "Core",
  "event_sequence": <int hop counter>,
  "payload": { "request_id", "user_id", "query", "data": { ... } },
  "trace_metadata": { "payload_hash", "hop_count" }
}
```

**Bucket persist (fingerprint only):**
```
{ "trace_id", "payload_hash": "<response_hash>", "system_tag": "Sarathi" }
```

**InsightFlow process (PASS/FAIL convergence):**
```
{
  "trace_id",
  "status": "PASS" | "FAIL",
  "systems_verified": [ "<peer_id>", ... ],
  "error_details": "<empty when PASS>"
}
```

### 5.3 Convergence rule (the PASS criterion InsightFlow should evaluate)

A trace converges (`status: PASS`) only if:

1. **Mutation check** — every in-chain peer's echoed `received_body_hash`
   equals Sarathi's `X-Sarathi-Response-Hash`.
2. **Loss check** — both in-chain peers (Core, Bucket) returned signed
   receipts within the execution gate deadline.
3. **Order check** — peer receipt timestamps respect the deterministic
   propagation order (Core before Bucket).

Any failed check → `status: FAIL`, with `error_details` listing the failed
checks. InsightFlow should record both the PASS/FAIL signal and the
underlying check outcomes.

---

## 6. Response contract (what Sarathi returns to the caller)

The top-level response carries a fixed set of required fields. Every field is
always present on every response, success or failure.

| Field              | Notes                                                            |
|--------------------|------------------------------------------------------------------|
| `schema_version`   | Sarathi response schema version.                                 |
| `decision_id`      | PDP decision id, or a synthetic pre-gate id for early rejects.   |
| `verdict`          | `ALLOW` \| `DENY` \| `ESCALATE`.                                   |
| `execution_state`  | `EXECUTION_PERMITTED` \| `EXECUTION_BLOCKED` \| `EXECUTION_NOT_ATTEMPTED` \| `RPA_VIOLATION` \| `CONTRACT_VIOLATION`. |
| `error_code`       | Standardized code, `OK` on success.                              |
| `reason`           | Free text. Empty on `OK`.                                        |
| `trace_id`         | Upstream trace_id, unchanged.                                    |
| `correlation_id`   | Upstream correlation id, unchanged.                              |
| `enforcement_hash` | SHA-256 hex.                                                     |
| `timestamp`        | RFC3339Nano.                                                     |
| `request`          | Normalized request object.                                       |
| `enforcement`      | Enforcement metadata block.                                      |
| `execution`        | Execution result block.                                          |
| `trace_context`    | Trace context object (W3C-shaped).                               |
| `observability`    | Observability metadata block.                                    |

Propagation-stage responses additionally carry:

| Field                | Notes                                                          |
|----------------------|----------------------------------------------------------------|
| `response_hash`      | SHA-256 hex of the canonical response bytes.                   |
| `chain_binding_hash` | SHA-256 hex binding the four propagation chain elements.       |
| `propagation_chain`  | `[decision_hash, decision_core_hash, enforcement_hash, response_hash]`. |
| `pdp_decision_id`    | Echo of the upstream decision id.                              |
| `execution_id`       | Sarathi execution id.                                          |

---

## 7. Telemetry expectations

For each in-chain execution, the following telemetry signals are emitted and
should be ingested by InsightFlow (and / or the central observability sink):

| Signal                       | When emitted                                  | Carries                                  |
|------------------------------|-----------------------------------------------|------------------------------------------|
| `enforcement_decision`       | Every request                                 | verdict, error_code, enforcement_hash    |
| `propagation_hop_sent`       | Per outbound hop                              | peer_id, response_hash, trace_id         |
| `propagation_hop_acked`      | Per in-chain ack received                     | peer_id, received_body_hash, latency_ns  |
| `propagation_chain_halted`   | On any ack failure / mismatch                 | failing peer_id, error_code, reason      |
| `trace_convergence_result`   | After all in-chain peers acked or gate expired| status (PASS/FAIL), systems_verified     |
| `execution_gate_timeout`     | When ack window elapses                       | missing_peers, deadline_ms               |

All telemetry events carry the same `trace_id`, `decision_id`, `execution_id`,
and `response_hash` — these four are the canonical pivots for cross-system
correlation.

---

## 8. Error codes the integration may surface

| Code                          | Meaning (integration-relevant)                                  |
|-------------------------------|-----------------------------------------------------------------|
| `OK`                          | Success.                                                        |
| `ERR_RESPONSE_HASH_MISMATCH`  | Peer's echoed hash differs from sent hash.                      |
| `ERR_PROPAGATION_BYTE_MISMATCH`| Bytes on the wire differ from envelope hash.                   |
| `ERR_PROPAGATION_CHAIN_BROKEN`| Chain binding hash re-derivation failed.                        |
| `ERR_DOWNSTREAM_RECEIPT_INVALID`| Signature / schema mismatch on peer receipt.                  |
| `ERR_DETERMINISM_VIOLATION`   | Catch-all byte-equality break.                                  |
| `ERR_INTELLIGENCE_LAYER_BREACH`| Non-digest payload reached a digest-only target.                |

---

## 9. Operational requirements expected from the integration side

Sarathi will treat the following as preconditions. NICAI / SVACS owners and
Nupur's team should confirm each before live TANTRA cuts over.

1. Every inbound request to Sarathi carries a valid upstream `trace_id`.
2. Both in-chain peers (Core, Bucket) have completed `/v1/handshake` and
   registered a stable Ed25519 public key with Sarathi.
3. Both in-chain peers POST signed receipts to `/v1/downstream-ack` within
   the configured execution gate deadline.
4. InsightFlow consumes the four endpoint shapes verbatim and emits the
   convergence PASS/FAIL signal using the three-check rule in §5.3.
5. No downstream consumer attempts to re-enter the enforcement gate.
6. Deployment URLs for all peer endpoints are provided to Sarathi via the
   documented per-endpoint configuration surface — no host pinning, no
   binary edits.

---

## 10. Sarathi-side guarantees (counter-commitments)

1. `trace_id` is never mutated, normalized, or regenerated by Sarathi.
2. Canonical bytes are sent on the wire verbatim — no re-serialization.
3. The propagation order is deterministic and identical across runs.
4. Every emitted response carries the full required field set in §6.
5. Every chain failure produces a single, standardized error code (§8) and a
   `propagation_chain_halted` telemetry event.
6. The same inputs (decision, environment, peer set) produce byte-identical
   responses across runs (deterministic replay).

---

## 11. Sign-off checklist for go-live

- [ ] Inbound `trace_id` presence verified end-to-end (one NICAI + one SVACS sample).
- [ ] Both in-chain peers handshake-registered.
- [ ] One PASS trace and one deliberately-broken trace exercised; convergence verdicts match expectation.
- [ ] InsightFlow ingests all four endpoint shapes and emits convergence signal.
- [ ] No re-entry attempt observed in 24 h soak.
- [ ] Telemetry pivots (`trace_id`, `decision_id`, `execution_id`,
      `response_hash`) verified queryable in the central observability sink.

---

**End of integration handoff. Anything not in this document is not part of
the integration contract.**
