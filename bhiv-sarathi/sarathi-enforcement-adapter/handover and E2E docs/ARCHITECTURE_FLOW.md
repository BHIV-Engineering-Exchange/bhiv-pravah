# Sarathi — Architecture Flow

How data moves through Sarathi, end to end. Pair this with `SYSTEM_OVERVIEW.md`
(concepts) and `REPO_MAP.md` (where each piece lives).

---

## 1. End-to-end enforcement flow

```
                         INBOUND
   caller (Bridge / decision authority)
        │  POST /v1/ingest-decision  (or /v1/enforce, /sarathi/enforce)
        ▼
   ┌─────────────────────────────────────────────┐
   │ 1. Inbound authentication                    │  reject unauthenticated
   │    (production: SARATHI_INBOUND_AUTH=required)│  callers (fail-closed)
   ├─────────────────────────────────────────────┤
   │ 2. Gated Bridge transit                       │  compile-time passport;
   │    (bypass is structurally impossible)        │  no path skips this
   ├─────────────────────────────────────────────┤
   │ 3. Decision verification                      │  verify hashes + signature
   │    (fail-closed on mismatch)                  │
   ├─────────────────────────────────────────────┤
   │ 4. Enforce verdict                            │  ALLOW / DENY / ESCALATE
   │    + seal canonical response (RFC 8785)       │  → response_hash minted
   ├─────────────────────────────────────────────┤
   │ 5. Sign custody receipt (Ed25519)             │  Sarathi enforcement key
   ├─────────────────────────────────────────────┤
   │ 6. Append to audit log                        │  immutable JSONL
   ├─────────────────────────────────────────────┤
   │ 7. Fire propagation hook (async, optional)    │  only if
   │                                               │  SARATHI_PROPAGATE_ON_INGEST=1
   └─────────────────────────────────────────────┘
        │
        ▼  enforcement response returned to caller (does NOT wait on peers)
```

Step 7 runs in a background goroutine and never blocks the inbound response.

---

## 2. Propagation fan-out (step 7 expanded)

When `SARATHI_PROPAGATE_ON_INGEST=1` and peer URLs are configured:

```
   sealed enforcement envelope
        │
        ├──► Bucket   POST /bucket/artifact      (in-chain; custody)
        │        └─ read-back GET /bucket/artifact/{id} → verify byte-identity
        │
        ├──► InsightFlow  4 endpoints            (off-chain; observability)
        │        /sarathi_trigger /core_execute /bucket_persist /insightflow_process
        │        └─ InsightFlow POSTs signed receipt → /v1/downstream-ack
        │
        └──► Core    POST /v1/enforce            (post-execution record)

   every hop → one row in proof_logs/peer_propagation_audit.jsonl
```

Failure semantics:
- **Bucket** is in-chain: failure is logged; it does not retroactively fail the
  already-returned response.
- **InsightFlow** is off-chain: failure never halts the chain or the request.
- **Core** post-exec record is best-effort and audited.

---

## 3. The dual-hash, end to end

```
  Sarathi mints BEFORE send:
     body_hash      = SHA-256(exact wire bytes)        ← transport integrity
     response_hash  = SHA-256(sealed canonical bytes)  ← decision integrity

  Peer receives, recomputes, and either:
     - Bucket:      Sarathi reads the artifact back and re-verifies both
     - InsightFlow: returns a signed receipt echoing received_body_hash +
                    observed_response_hash; Sarathi verifies both match the
                    minted values (dual-hash gate) before accepting the receipt
```

Both hashes must match for a receipt to be accepted; either mismatch rejects.

---

## 4. Bucket custody sub-flow (the witness model)

Bucket is the chain authority; Sarathi is the seal + the witness.

```
 1. GET  /bucket/latest-hash        → parent_hash (omit on genesis)
 2. mint body_hash + response_hash  (Sarathi-owned, before send)
 3. POST /bucket/artifact           → Bucket stores, returns its own server hash
 4. GET  /bucket/artifact/{id}      → read-back
 5. verify trace_id / decision_id / canonical_response_b64 / response_hash match
 6. Sarathi signs its own custody receipt (Bucket never signs one)
```

Key envelope rules learned from the live deployment (authoritative source is
`GET /bucket/schema-info`):
- `trace_id` lives **inside `payload`**, not top-level.
- The **genesis** artifact must **omit** `parent_hash`; later artifacts set it to
  the prior chain head.
- Bucket computes its **own** server hash; it differs from Sarathi's transport
  `body_hash` by design. Integrity is proven by the read-back, not hash equality.

---

## 5. Trust model

```
  Each peer (bucket / core / insightflow) has a pinned Ed25519 PUBLIC key
  in the trust/peer-key registry.

  Inbound receipts → signature verified against the REGISTERED key for that
  peer name (cross-peer impersonation rejected even if a signature internally
  verifies under a different peer's key).

  Sarathi → peer requests:
     - Bucket / Core:   integrity via dual-hash headers
     - InsightFlow:     authenticated by X-API-Key (forward); receipts from
                        InsightFlow are Ed25519-signed (reverse)
```

Private keys never cross the wire. Only public keys + fingerprints are shared.

---

## 6. Observability surfaces

| Surface | Where |
|---|---|
| Liveness / readiness | `GET /health`, `GET /health/deep` |
| Metrics | `GET /metrics`, `GET /metrics/prometheus` |
| Propagation audit | `proof_logs/peer_propagation_audit.jsonl` |
| Receipts in/out | `proof_logs/downstream_ack_receipts.jsonl` / `..._rejections.jsonl` |
| Bucket proofs | `proof_logs/bucket/` |
| Per-peer event logs | `live/<peer>/` |
