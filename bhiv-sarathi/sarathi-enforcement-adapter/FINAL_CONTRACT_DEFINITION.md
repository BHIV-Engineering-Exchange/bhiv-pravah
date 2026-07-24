# Sarathi — Final Contract Definition (v15.11)

**Audience:** BHIV management + BHIV Core / Bucket / InsightFlow integration owners.
**Purpose:** The frozen contracts. Every byte on the wire between Sarathi and the BHIV peer systems is defined here. Once signed off, these contracts do not change without a versioned schema bump.
**Status:** Frozen v15.11. Tests green. Build clean.

---

## 1. Contract inventory

There are exactly four contracts in scope. Each has a schema_version that pins the wire shape.

| # | Contract | Direction | schema_version | Authentication |
|---|---|---|---|---|
| 1 | **TANTRA Decision** | Sovereign Core → Sarathi | `tantra.decision.v1` | Ed25519 signature in body + sha256 API-key fingerprint |
| 2 | **Sarathi Enforcement Attestation** | Sarathi → audit log | `tantra.decision.v1` | Ed25519 signature by Sarathi (`bhiv.sarathi.enforcement.prod.v1`) |
| 3 | **Outbound Propagation** | Sarathi → Bucket / InsightFlow / BHIV Core | `sarathi.response/v13.0` | None (byte-identity proven by receipt callback) |
| 4 | **Peer Receipt** | Bucket / InsightFlow / Core → Sarathi | `sarathi.live.receipt/v1.0` | Ed25519 signature in body + peer-key pinning + replay rejection |

---

## 2. Contract #1 — TANTRA Decision (Sovereign Core → Sarathi)

### 2.1 Endpoint

```
POST https://<sarathi-host>/sarathi/enforce
Content-Type: application/json
X-API-Key: <raw 64-char hex secret>
X-Sarathi-Trace-ID: <same uuid as body.trace_id>
```

### 2.2 Body schema (exactly 11 top-level fields, fixed order)

```json
{
  "schema_version": "tantra.decision.v1",
  "trace_id": "<uuid-v4>",
  "input_hash": "<hex sha256 of raw input>",
  "decision_id": "<deterministic uuid-shape — see §2.4>",
  "decision_hash": "<hex sha256 of 6-field material — see §2.3>",
  "verdict": "ALLOW | DENY | ESCALATE",
  "policy_reference": "<policy_pack_id@version>",
  "evaluator_id": "bhiv.sovereign.decision.prod.v1",
  "enforcement_binding": "<status>:<reason>",
  "timestamp": "<RFC3339Nano UTC>",
  "signature": {
    "alg": "Ed25519",
    "key_id": "<evaluator_id>#<rotation-tag>",
    "encoding": "base64url_no_pad",
    "value": "<base64url-no-pad of 64-byte Ed25519 signature>"
  }
}
```

Field order is part of what gets signed. Anything other than these 11 fields fails closed.

### 2.3 `decision_hash` formula

```
material = canonical_json({
    "schema_version":   "tantra.decision.v1",
    "trace_id":         "<value>",
    "input_hash":       "<value>",
    "verdict":          "ALLOW",
    "policy_reference": "<value>",
    "evaluator_id":     "<value>"
})
decision_hash = sha256_hex(material)
```

Six fields in this exact fixed order. Canonical JSON = no whitespace, no extra fields, exact field order as listed. `timestamp` deliberately excluded so replays of the same logical decision collide.

### 2.4 `decision_id` formula (Sarathi default — confirm with Core before integration)

```
material = canonical_json({
    "trace_id":     "<value>",
    "input_hash":   "<value>",
    "evaluator_id": "<value>"
})
hex_digest = sha256_hex(material)
decision_id = f"{hex_digest[0:8]}-{hex_digest[8:12]}-{hex_digest[12:16]}-{hex_digest[16:20]}-{hex_digest[20:32]}"
```

Sarathi's verifier recomputes and rejects mismatch with `ERR_TANTRA_DECISION_ID_MISMATCH`.

### 2.5 Canonical-bytes for signing

Build the JSON with all 10 non-signature fields in §2.2 order. Canonicalize via RFC 8785 in **the fixed order specified** (not alphabetical). Sign with Ed25519. Base64url-no-pad-encode the 64-byte signature. Insert into the `signature.value` field. The signature OBJECT is excluded from the bytes that get signed.

### 2.6 Verification steps Sarathi performs

In strict order, each fail-closed:

```
0a  Strict body decode (DisallowUnknownFields)
0b  Required-field + verdict whitelist
0c  evaluator_id matches regex bhiv.<s>.<c>.<e>.v<v>
0d  Timestamp parses + ±300 s skew
1   Extract signature object
2   Compute canonical signing bytes (signature OMITTED)
3   schema_version == "tantra.decision.v1"
4   Evaluator lookup: exists + status ACTIVE
5   Registered schema_version + key_id + algorithm match payload
6   Round-trip canonical wire bytes (catch upstream re-encoders)
7   base64url-no-pad decode signature.value; Ed25519 verify against registered key
7b  sha256_hex(X-API-Key) == registered api_key_fingerprint (constant time)
8   Recompute decision_hash from 6-field material
9   Compare to payload decision_hash
10  Recompute decision_id
11  Compare to payload decision_id
12  Replay check (decision_hash + signed-payload-hash, 300 s)
```

### 2.7 Error codes (all 19)

| HTTP | Code |
|---|---|
| 400 | `ERR_TANTRA_SCHEMA_VERSION_UNKNOWN` |
| 400 | `ERR_TANTRA_MISSING_FIELD` |
| 400 | `ERR_TANTRA_UNKNOWN_FIELD` |
| 400 | `ERR_TANTRA_VERDICT_INVALID` |
| 400 | `ERR_TANTRA_EVALUATOR_ID_FORMAT` |
| 400 | `ERR_TANTRA_ENCODING_UNSUPPORTED` |
| 400 | `ERR_TANTRA_CANONICAL_ENCODING` |
| 400 | `ERR_TANTRA_BODY_TOO_LARGE` |
| 400 | `ERR_TANTRA_TIMESTAMP_UNPARSEABLE` |
| 401 | `ERR_TANTRA_TIMESTAMP_SKEWED` |
| 401 | `ERR_TANTRA_SIGNATURE_DECODE` |
| 401 | `ERR_TANTRA_SIGNATURE_INVALID` |
| 401 | `ERR_TANTRA_API_KEY_REQUIRED` |
| 401 | `ERR_TANTRA_API_KEY_INVALID` |
| 403 | `ERR_TANTRA_EVALUATOR_NOT_REGISTERED` |
| 403 | `ERR_TANTRA_EVALUATOR_NOT_ACTIVE` |
| 403 | `ERR_TANTRA_EVALUATOR_SCHEMA_MISMATCH` |
| 403 | `ERR_TANTRA_KEY_ID_MISMATCH` |
| 403 | `ERR_TANTRA_ALG_MISMATCH` |
| 409 | `ERR_TANTRA_DECISION_HASH_MISMATCH` |
| 409 | `ERR_TANTRA_DECISION_ID_MISMATCH` |
| 409 | `ERR_TANTRA_REPLAY` |

Every error carries `X-Sarathi-Error-Code` HTTP header AND `error_code` body field.

---

## 3. Contract #2 — Sarathi Enforcement Attestation (Sarathi → audit log)

After every successful `/sarathi/enforce`, Sarathi emits a TANTRA-shape payload signed by `bhiv.sarathi.enforcement.prod.v1`. Same schema as Contract #1 with `evaluator_id` substituted and `enforcement_binding` carrying the CLEARED/BLOCKED string.

Persisted to `proof_logs/sarathi_enforcement_attestations.jsonl`. Not POSTed anywhere — it is a side-channel audit record any downstream observer can re-verify against Sarathi's registered enforcement public key.

---

## 4. Contract #3 — Outbound Propagation (Sarathi → Bucket / InsightFlow / BHIV Core)

### 4.1 What Sarathi POSTs (under Path A, v15.11 current)

```
POST https://<peer-host>/<peer-endpoint>
Content-Type: application/json
X-Sarathi-Decision-ID: <id>
X-Sarathi-Execution-ID: <id>
X-Sarathi-Trace-ID: <uuid>
X-Sarathi-Response-Hash: <64-hex sha256 of body>
X-Sarathi-Chain-Binding-Hash: <64-hex>
X-Sarathi-Enforcement-Hash: <64-hex>
X-Sarathi-Schema-Version: sarathi.response/v13.0
X-Sarathi-Sealed-At: <RFC3339Nano>
X-Sarathi-Bucket-Parent-Hash: <64-hex>     # Bucket only
```

### 4.2 Body — the canonical 20-field enforcement record

A JSON object in RFC 8785 alphabetical canonical order, no whitespace. Approximate shape:

```json
{
  "agent_id":            "...",
  "chain_binding_hash":  "<64-hex>",
  "correlation_id":      "<uuid>",
  "decision_hash":       "<64-hex>",
  "decision_id":         "<id>",
  "enforced_at":         "<RFC3339Nano>",
  "enforcement_hash":    "<64-hex>",
  "evaluator_id":        "bhiv.sovereign.decision.prod.v1",
  "execution_id":        "<id>",
  "execution_state":     "EXECUTION_PERMITTED",
  "error_code":          "OK",
  "pdp_decision_id":     "<id>",
  "policy_pack_id":      "...",
  "propagation_chain":   ["..."],
  "resource_id":         "...",
  "response_hash":       "<64-hex>",
  "schema_version":      "sarathi.response/v13.0",
  "trace_id":            "<uuid>",
  "verdict":             "ALLOW"
}
```

`SHA-256(body bytes) == X-Sarathi-Response-Hash`. Equality is by construction since the body IS the canonical bytes Sarathi sealed.

### 4.3 Open coordination item — Path A vs Path B

**Path A (v15.11 default — currently wired):** raw 20-field canonical envelope as body. Trivial byte-equality; peers don't extract fields. Requires peer endpoints to accept this body shape (not a wrapper).

**Path B (fallback if peers built strict wrapper validators):** Sarathi wraps in `BucketArtifact{artifact_id, parent_hash, payload:{...}}` for Bucket and Schemas A/B/C/D for InsightFlow. Then `received_body_hash != response_hash` — verifier must be augmented to compare `received_body_hash` against a Sarathi-side stored "what I sent" hash table.

**Resolution requires asking each peer team:**
- Siddhesh: does Bucket's `/bucket/artifact` accept arbitrary 20-field JSON, or strictly validate the BucketArtifact wrapper?
- Vijay: does InsightFlow's `/insightflow_process` accept the full ~20-field record, or strictly validate Schema D?

Until they answer, the contract is **Path A**. If they require wrappers, Sarathi will switch in <100 LOC and re-publish this section.

### 4.4 What the peer responds (ACK)

`200 OK` (Bucket / Core) or `202 Accepted` (InsightFlow) plus:

```
X-Sarathi-Ack-Hash: <64-hex sha256 of body the peer received>
```

And a minimal JSON body identifying the peer + ack hash. Sarathi does not strictly validate the ACK body shape — only the header.

---

## 5. Contract #4 — Peer Receipt (Bucket / InsightFlow / Core → Sarathi)

### 5.1 Endpoint

```
POST https://<sarathi-host>/v1/downstream-ack
Content-Type: application/json
```

No authentication headers. Authentication is the Ed25519 signature in the body.

### 5.2 Body schema (exactly 11 fields)

```json
{
  "schema_version":     "sarathi.live.receipt/v1.0",
  "peer":               "bucket | insightflow | core",
  "execution_id":       "<echo from X-Sarathi-Execution-ID>",
  "decision_id":        "<echo from X-Sarathi-Decision-ID>",
  "response_hash":      "<echo from X-Sarathi-Response-Hash>",
  "received_body_hash": "<sha256_hex of bytes received in the forward POST body>",
  "chain_binding_hash": "<echo from X-Sarathi-Chain-Binding-Hash>",
  "persisted_at":       "<RFC3339Nano UTC>",
  "storage_path":       "<peer's internal path>",
  "peer_public_key_hex":"<peer's 64-hex Ed25519 public key>",
  "receipt_signature":  "<128-hex Ed25519 signature>"
}
```

### 5.3 Canonical-bytes for signing

Build the JSON with all 10 non-signature fields. Set `receipt_signature` to `""`. Canonicalize via RFC 8785 in **alphabetical** key order (NOT fixed). Sign with Ed25519. Hex-encode the 64-byte signature. Insert into `receipt_signature`. Re-canonicalize.

### 5.4 Verification steps Sarathi performs

```
1   Schema version match
2   Decode embedded peer_public_key_hex (32 bytes)
3   Decode receipt_signature (64 bytes)
4   Canonicalize with receipt_signature cleared
5   Ed25519 verify against embedded public key
6   received_body_hash == response_hash (byte equality proof)
7   peer field is one of {bucket, core, insightflow}
8   Registered peer-key matches embedded key (constant time)
9   Registered peer status is ACTIVE
10  sha256(raw receipt bytes) not seen in last 300 s
```

### 5.5 Error code

| HTTP | Code | Reason in detail |
|---|---|---|
| 400 / 401 | `ERR_DOWNSTREAM_RECEIPT_INVALID` | One of: `schema_version mismatch`, `invalid peer_public_key_hex`, `invalid receipt_signature`, `signature verification failed`, `body_hash != response_hash`, `peer_key_pinning: ...`, `peer "X" status=...`, `peer_receipt_replay: ...` |

---

## 6. Cryptographic primitives

| Use | Algorithm | Standard | Notes |
|---|---|---|---|
| Canonical JSON (TANTRA payload) | RFC 8785 JCS | RFC 8785 | **Fixed field order** (not alphabetical) per §2.5 |
| Canonical JSON (peer receipt) | RFC 8785 JCS | RFC 8785 | **Alphabetical** key order |
| Hash | SHA-256 | FIPS 180-4 | Used for decision_hash, response_hash, chain_binding_hash, received_body_hash, all key fingerprints |
| Signature (Ed25519 mode) | Ed25519 | RFC 8032 | NOT Ed25519ph, NOT Ed25519ctx. Pure Ed25519. |
| Signature (hybrid mode, opt-in) | Composite ML-DSA-65 + Ed25519 | FIPS 204 + RFC 8032 | TLV-framed, composite-AND verify. Behind `SARATHI_CRYPTO_PROVIDER=hybrid` env var. |
| Constant-time compare | `crypto/subtle.ConstantTimeCompare` | Go stdlib | Used for all secret-derived comparisons |
| Encoding (TANTRA signature value) | base64url no-pad | RFC 4648 §5 | Padded base64 rejected |
| Encoding (peer receipt signature) | hex (lowercase) | — | 128 chars for 64-byte signature |

No proprietary primitives. No experimental algorithms. No mock crypto on the live path.

---

## 7. Identity / Key model

### 7.1 Identifiers

| Identifier | Format | Issuer | Purpose |
|---|---|---|---|
| Evaluator ID | `bhiv.<system>.<component>.<environment>.v<major>` | BHIV system catalogue | Identifies the decision-issuing authority |
| Peer name | one of `bucket`, `core`, `insightflow` | Closed set | Identifies the propagation peer |
| key_id | `<evaluator_id>#<rotation_tag>` | Per evaluator | Pins a specific key version |
| api_key_fingerprint | 64-char sha256 hex | Per evaluator | Validates the X-API-Key header |

### 7.2 Key generation responsibility

| Key | Generated by | Sent to Sarathi (out of band) |
|---|---|---|
| Sovereign Core Ed25519 keypair | Core team | Public key + key_id + api_key_fingerprint |
| Bucket Ed25519 keypair | Bucket team | Public key only |
| InsightFlow Ed25519 keypair | InsightFlow team | Public key only |
| Core post-exec receipt Ed25519 keypair | Core team (can be same key as decision) | Public key only |
| Sarathi enforcement Ed25519 keypair | Sarathi side | Sarathi publishes public key to peers |

**Sarathi never holds any private key it didn't generate. Sarathi never generates a key it then transmits.** Each side keeps its own private material; only public material crosses the wire.

### 7.3 Registration commands (Sarathi side)

```bash
# Sovereign Core
./sarathi-enforcement-adapter --register-tantra-evaluator \
    --evaluator-id=bhiv.sovereign.decision.prod.v1 \
    --schema-version=tantra.decision.v1 \
    --algorithm=Ed25519 \
    --key-id=bhiv.sovereign.decision.prod.v1#ed25519-2026-05 \
    --public-key=<hex> \
    --api-key-fingerprint=<hex> \
    --snapshot=./live/trust_snapshot.json

# Each peer
./sarathi-enforcement-adapter --register-peer-key --peer=bucket      --public-key=<hex>
./sarathi-enforcement-adapter --register-peer-key --peer=insightflow --public-key=<hex>
./sarathi-enforcement-adapter --register-peer-key --peer=core        --public-key=<hex>
```

Audit trail: `proof_logs/tantra_registry_audit.jsonl` + `proof_logs/peer_key_registry_audit.jsonl`.

---

## 8. Replay and skew windows

| Surface | Window | Where enforced |
|---|---|---|
| TANTRA decision_hash | 300 s | TANTRA replay store |
| TANTRA signed-payload hash | 300 s | Same store, separate key |
| TANTRA timestamp skew (vs wall clock) | ±300 s | TANTRA verifier step 0d |
| Peer receipt (sha256 of raw bytes per peer) | 300 s | Receipt replay store |
| Peer receipt ack deadline | 300 s | Ack tracker (existing) |
| Inbound HTTP header nonce | 900 s | Existing nonce store (legacy) |

All windows are configurable but the defaults above are the contract baseline.

---

## 9. Schema version pinning

| Schema version | Where | Frozen at v15.11 |
|---|---|---|
| `tantra.decision.v1` | TANTRA inbound payload (Contract #1, #2) | ✅ |
| `sarathi.response/v13.0` | Outbound canonical envelope (Contract #3 body) | ✅ |
| `sarathi.live.receipt/v1.0` | Peer receipt (Contract #4) | ✅ |
| `sarathi.envelope/v14.5` | Internal envelope wrapper | ✅ |

A version bump on any of these requires a new contract definition document and coordination with all peer teams.

---

## 10. Sign-off

This contract is frozen at v15.11. Modifying any field, ordering, algorithm, encoding, or error-code is a schema-version bump and requires:

1. Updated `FINAL_CONTRACT_DEFINITION.md`.
2. Updated `CORE_INTEGRATION.md` / `BUCKET_INTEGRATION.md` / `INSIGHTFLOW_INTEGRATION.md` for any wire-affecting change.
3. Updated `REVIEW_PACKET.md` with the new "What changed" section.
4. Coordinated peer-team rollout.

— *Sign-off requires confirmation of the four items in `OPEN_BLOCKERS_LIST.md` (decision_id formula confirmation + Path A vs Path B peer-endpoint confirmation for Bucket and InsightFlow + peer key handover completion).*
