# Sarathi Integration Guide — InsightFlow

**For:** Nupur / Vijay Dhawan (BHIV InsightFlow)
**Purpose:** Self-contained integration spec. Read top-to-bottom and you have everything InsightFlow needs to receive enforcement records from Sarathi and send back signed receipts.
**Out of scope:** Sarathi's internal implementation. Only the wire contract.

---

## 1. The two HTTP surfaces

| Direction | Method | URL | Purpose |
|---|---|---|---|
| **Sarathi → InsightFlow** | `POST` | `https://<insightflow-url>/insightflow_process` | Sarathi sends the InsightFlow Schema D wrapper containing the enforcement record. |
| **InsightFlow → Sarathi** | `POST` | `https://<sarathi-url>/v1/downstream-ack` | InsightFlow asynchronously sends a signed receipt with TWO hash proofs (transport + decision). |

Both URLs use TLS / HTTPS in production. You will receive Sarathi's host out-of-band; Sarathi will receive your InsightFlow host out-of-band.

Sarathi also posts three smaller digest-only events to your `/sarathi_trigger`, `/core_execute`, `/bucket_persist` endpoints (Schemas A, C, B respectively). Those continue to work per the existing InsightFlow contract — no changes there. This document covers only `/insightflow_process` (Schema D) which carries the full enforcement record for the dual-hash callback.

---

## 2. Surface 1 — Sarathi POSTs to InsightFlow `/insightflow_process`

### 2.1 Request

```
POST https://<insightflow-url>/insightflow_process
Content-Type: application/json
X-Sarathi-Decision-ID: <id>
X-Sarathi-Execution-ID: <id>
X-Sarathi-Trace-ID: <uuid>
X-Sarathi-Response-Hash: <64-hex sha256 of the embedded canonical 20-field response>
X-Sarathi-Body-Hash: <64-hex sha256 of the body bytes Sarathi sends on the wire>
X-Sarathi-Chain-Binding-Hash: <64-hex>
X-Sarathi-Enforcement-Hash: <64-hex>
X-Sarathi-Schema-Version: bhiv.insightflow.process/v1.0
X-Sarathi-Sealed-At: <RFC3339Nano UTC>
X-Sarathi-Digest-Only: 1
```

**Two distinct hash headers** — different values:
- `X-Sarathi-Response-Hash` = SHA-256 of the canonical 20-field enforcement record embedded in `canonical_response_b64`.
- `X-Sarathi-Body-Hash` = SHA-256 of the full Schema D body bytes sent on the wire.

### 2.2 Body — InsightFlow Schema D

Per InsightFlow's existing Schema D contract, with three fields added in v15.12 (`decision_id`, `response_hash`, `canonical_response_b64`):

```json
{
  "trace_id":         "<uuid>",
  "status":           "PASS | FAIL",
  "checks": {
    "mutation_check": true,
    "loss_check":     true,
    "order_check":    true
  },
  "systems_verified": ["..."],
  "error_details":    [],
  "run_metrics": {
    "total_runs": 1,
    "success":    1,
    "failure":    0
  },
  "decision_id":            "<id — added in v15.12>",
  "response_hash":          "<64-hex — same value as X-Sarathi-Response-Hash header — added in v15.12>",
  "canonical_response_b64": "<base64-std of the verbatim canonical 20-field response bytes Sarathi sealed — added in v15.12>"
}
```

The base Schema D fields are unchanged. The three new fields are additive and carry the enforcement record for InsightFlow to verify decision integrity independently.

### 2.3 What InsightFlow does on receive (5 steps)

```
1. body = raw bytes from HTTP body
2. observed_body_hash    = sha256_hex(body)
   confirm observed_body_hash == X-Sarathi-Body-Hash header
       → transport integrity proof; reject 412 if mismatch
3. parse body as Schema D JSON
   canonical_bytes = base64_std_decode(canonical_response_b64)
   observed_response_hash = sha256_hex(canonical_bytes)
   confirm observed_response_hash == X-Sarathi-Response-Hash header
       → decision integrity proof; reject 412 if mismatch
4. apply InsightFlow's normal processing (telemetry projection,
   trace-graph indexing, etc.)
5. respond 202 Accepted with:
   - header X-Sarathi-Ack-Hash: <observed_body_hash>
   - body { "peer":"insightflow", "ack_hash":"<observed_body_hash>",
            "decision_id":"<id>", "endpoint":"/insightflow_process" }

   then asynchronously POST the receipt to Sarathi per §3 within 300 s.
```

### 2.4 Off-chain semantics

InsightFlow is "off-chain" in Sarathi's propagation model: an InsightFlow failure or slow response does NOT halt the rest of the propagation chain. Sarathi will retry per its own policy if the POST returns 5xx or times out. Bucket and Core hops continue independently.

That said, InsightFlow's receipt is still required for full observability gate closure — without it, the per-execution gate does not close cleanly even though no failure propagates.

---

## 3. Surface 2 — InsightFlow POSTs receipt to Sarathi

### 3.1 Request

```
POST https://<sarathi-url>/v1/downstream-ack
Content-Type: application/json
```

No additional headers required.

### 3.2 Receipt schema — exactly 12 fields (v15.12)

```json
{
  "schema_version":         "sarathi.live.receipt/v1.0",
  "peer":                   "insightflow",
  "execution_id":           "<echo from X-Sarathi-Execution-ID>",
  "decision_id":            "<echo from X-Sarathi-Decision-ID>",
  "response_hash":          "<echo from X-Sarathi-Response-Hash>",
  "received_body_hash":     "<observed_body_hash from §2.3 step 2>",
  "observed_response_hash": "<observed_response_hash from §2.3 step 3>",
  "chain_binding_hash":     "<echo from X-Sarathi-Chain-Binding-Hash>",
  "persisted_at":           "<RFC3339Nano UTC, when InsightFlow finished processing>",
  "storage_path":           "<InsightFlow's internal identifier — optional, any string>",
  "peer_public_key_hex":    "<InsightFlow's 64-hex Ed25519 PUBLIC key>",
  "receipt_signature":      "<128-hex Ed25519 signature — see §4>"
}
```

### 3.3 Field rules

| Field | Rule |
|---|---|
| `schema_version` | Literal `"sarathi.live.receipt/v1.0"`. |
| `peer` | Literal `"insightflow"`. Any other value rejects. |
| `execution_id`, `decision_id`, `response_hash`, `chain_binding_hash` | Verbatim echoes of the matching `X-Sarathi-*` request headers. |
| `received_body_hash` | InsightFlow's SHA-256 over the raw body bytes received. Sarathi compares this to the minted body_hash (transport integrity). |
| `observed_response_hash` | InsightFlow's SHA-256 over the bytes from base64-decoding `canonical_response_b64`. Sarathi compares this to the minted response_hash (decision integrity). |
| `persisted_at` | RFC3339Nano UTC. Use the timestamp when InsightFlow finished its processing. |
| `storage_path` | Any string useful for audit. |
| `peer_public_key_hex` | InsightFlow's PUBLIC Ed25519 key, 64 hex chars. |
| `receipt_signature` | Ed25519 signature over the canonical bytes of the 11 non-signature fields above; hex, 128 chars. |

### 3.4 Verification Sarathi performs (dual-hash gate)

```
1.  schema_version matches "sarathi.live.receipt/v1.0"
2.  Ed25519 signature verifies against peer_public_key_hex
3.  TRANSPORT INTEGRITY:
        received_body_hash == minted body_hash for (decision_id, peer)
4.  DECISION INTEGRITY:
        observed_response_hash == minted response_hash
        AND response_hash (echo) == minted response_hash
5.  peer field is one of {bucket, core, insightflow}
6.  Registered InsightFlow public key matches embedded peer_public_key_hex
        (constant-time compare)
7.  InsightFlow status is ACTIVE
8.  Same receipt bytes not seen within last 300 s (replay rejection)
```

Both gates 3 and 4 must pass. Either failure rejects the receipt with `ERR_DOWNSTREAM_RECEIPT_INVALID` + reason string.

---

## 4. Canonicalization and signing

### 4.1 Canonicalization algorithm

**RFC 8785 JSON Canonicalization Scheme (JCS) — alphabetical key ordering at every level.**

Properties:
- Keys sorted lexicographically at every nesting depth.
- No insignificant whitespace.
- Strings escaped per JSON spec (`\"`, `\\`, `\b`, `\f`, `\n`, `\r`, `\t`, `\u00XX` for 0x00–0x1F).
- No HTML-safety escaping — write `&`, `<`, `>` raw.
- Numbers in shortest round-trip form.
- No trailing newline.

Off-the-shelf libraries: `cyberphone/json-canonicalization` (Python), `gibson042/canonicaljson-go` (Go), `erdtman/canonicalize` (Node).

### 4.2 Signing algorithm

**Ed25519 (RFC 8032)** — pure Ed25519. NOT Ed25519ph. NOT Ed25519ctx.

Receipt signing procedure:

```
1. Build the receipt JSON with all 11 NON-signature fields populated.
2. Set receipt_signature to "" (empty string).
3. Canonicalize via RFC 8785 with ALPHABETICAL key ordering.
   Result: UTF-8 byte string.
4. sig_bytes = Ed25519.Sign(insightflow_private_key, canonical_bytes)
   sig_bytes is 64 raw bytes.
5. receipt_signature = sig_bytes.hex()                  # 128 hex chars, lowercase
6. POST the receipt with receipt_signature filled in.
```

### 4.3 Reference snippet (Python, PyNaCl + standard library)

```python
import base64
import hashlib
import json
import time
from nacl.signing import SigningKey

def canonicalize_alphabetical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")

sk = SigningKey(open("live/keys/insightflow/issuer-priv.bin", "rb").read())

def handle_post_process(body_bytes: bytes, headers: dict):
    # Step 1+2: transport integrity gate
    observed_body_hash = hashlib.sha256(body_bytes).hexdigest()
    if observed_body_hash != headers["X-Sarathi-Body-Hash"]:
        return 412, {"error":"body_hash mismatch"}

    # Step 3: decision integrity gate
    schema_d = json.loads(body_bytes)
    canonical_bytes = base64.b64decode(schema_d["canonical_response_b64"])
    observed_response_hash = hashlib.sha256(canonical_bytes).hexdigest()
    if observed_response_hash != headers["X-Sarathi-Response-Hash"]:
        return 412, {"error":"response_hash mismatch"}

    # Step 4: InsightFlow processing (telemetry, trace graph, etc.)
    storage_id = process_for_observability(schema_d)

    # Step 5: receipt callback
    receipt = {
        "schema_version":         "sarathi.live.receipt/v1.0",
        "peer":                   "insightflow",
        "execution_id":           headers["X-Sarathi-Execution-ID"],
        "decision_id":            headers["X-Sarathi-Decision-ID"],
        "response_hash":          headers["X-Sarathi-Response-Hash"],
        "received_body_hash":     observed_body_hash,
        "observed_response_hash": observed_response_hash,
        "chain_binding_hash":     headers["X-Sarathi-Chain-Binding-Hash"],
        "persisted_at":           time.strftime("%Y-%m-%dT%H:%M:%S.000000000Z", time.gmtime()),
        "storage_path":           storage_id,
        "peer_public_key_hex":    sk.verify_key.encode().hex(),
        "receipt_signature":      "",
    }
    canon = canonicalize_alphabetical(receipt)
    sig = sk.sign(canon).signature
    receipt["receipt_signature"] = sig.hex()

    # POST receipt to https://<sarathi-url>/v1/downstream-ack
    post_receipt_to_sarathi(receipt)

    # Step 6: ACK Sarathi
    return 202, {
        "peer":         "insightflow",
        "ack_hash":     observed_body_hash,
        "decision_id":  headers["X-Sarathi-Decision-ID"],
        "endpoint":     "/insightflow_process",
    }
```

---

## 5. Key handover and registration

### 5.1 Ed25519 keypair generation (InsightFlow side)

```python
from nacl.signing import SigningKey
sk = SigningKey.generate()
private_key_bytes = sk.encode()                  # keep local, 32 bytes
public_key_hex = sk.verify_key.encode().hex()    # 64 chars, send to Sarathi
```

The private key NEVER leaves InsightFlow.

### 5.2 What to send Sarathi (one-time, out-of-band secure channel)

| Item | Format | Example |
|---|---|---|
| peer name | string | `insightflow` |
| public_key_hex | 64-char hex | `66889a48eb3cb0b09cf04370c7b78004f26fa1ab9ec49b8661bb13d028186d3a` |
| InsightFlow POST URL | string | `https://<insightflow-host>/insightflow_process` |

### 5.3 What Sarathi sends InsightFlow (out-of-band)

| Item | Format |
|---|---|
| Sarathi receipt callback URL | `https://<sarathi-url>/v1/downstream-ack` |
| Replay window | 300 s |
| Ack deadline | 300 s |

### 5.4 Rotation

Regenerate keypair locally, send new public key to Sarathi out-of-band, Sarathi updates registered key. In-flight receipts under old key continue to verify until registry update; after update, old key rejects.

### 5.5 API key

InsightFlow does NOT need an API key. The Ed25519 signature on the receipt body IS the authentication. The `/v1/downstream-ack` endpoint has no `X-API-Key` requirement.

---

## 6. Error responses InsightFlow may see from Sarathi

All errors carry `X-Sarathi-Error-Code` HTTP header AND a JSON body with `error_code`.

| HTTP | Code (reason in detail) | Cause |
|---|---|---|
| 400 | `ERR_DOWNSTREAM_RECEIPT_INVALID` (`schema_version mismatch`) | wrong schema_version |
| 400 | `ERR_DOWNSTREAM_RECEIPT_INVALID` (`signature verification failed`) | Ed25519 verify failed |
| 400 | `ERR_DOWNSTREAM_RECEIPT_INVALID` (`transport_integrity: ...`) | `received_body_hash` ≠ minted body_hash |
| 400 | `ERR_DOWNSTREAM_RECEIPT_INVALID` (`decision_integrity: receipt missing observed_response_hash`) | Field empty/absent |
| 400 | `ERR_DOWNSTREAM_RECEIPT_INVALID` (`decision_integrity: ...`) | `observed_response_hash` ≠ minted response_hash |
| 400 | `ERR_DOWNSTREAM_RECEIPT_INVALID` (`peer_key_pinning: ... does not match registered key`) | embedded key ≠ registered |
| 400 | `ERR_DOWNSTREAM_RECEIPT_INVALID` (`peer "insightflow" status=...`) | registered status `SUSPENDED` or `REVOKED` |
| 400 | `ERR_DOWNSTREAM_RECEIPT_INVALID` (`peer_receipt_replay: ...`) | same receipt bytes seen within 300 s |

---

## 7. Quick sanity-check checklist

Before the first integration call:

- [ ] `/insightflow_process` endpoint reads two headers — `X-Sarathi-Body-Hash` AND `X-Sarathi-Response-Hash`.
- [ ] Endpoint computes `observed_body_hash = sha256(body)` and rejects with 412 if it doesn't equal `X-Sarathi-Body-Hash`.
- [ ] Endpoint parses Schema D, extracts `canonical_response_b64`, base64-decodes, hashes, rejects with 412 if it doesn't equal `X-Sarathi-Response-Hash`.
- [ ] Ed25519 keypair generated. Private key stored locally. Public key in hex sent to Sarathi.
- [ ] Receipt builder populates BOTH `received_body_hash` AND `observed_response_hash`.
- [ ] Reference canonical-JSON implementation matches Sarathi's bytes (request a test fixture).
- [ ] Test posting one receipt to `/v1/downstream-ack`; confirm 200 OK.

---

## 8. Things to NOT do

- Do NOT send your private key to Sarathi or anyone else.
- Do NOT re-marshal the body before hashing — `received_body_hash` is over the EXACT bytes received.
- Do NOT skip the `observed_response_hash` field — it's the decision integrity proof.
- Do NOT add `X-API-Key` to receipt POSTs.
- Do NOT use Ed25519ph or Ed25519ctx.
- Do NOT post the receipt before InsightFlow processing completes — `persisted_at` should be after processing.
- Do NOT retry POSTing the SAME receipt within 300 s if the first POST got a transport error.

---

## 9. Why two hashes

| Hash field | Proves |
|---|---|
| `received_body_hash` | TRANSPORT INTEGRITY — the Schema D wrapper bytes received are byte-identical to what Sarathi sent on the wire. Catches in-flight corruption. |
| `observed_response_hash` | DECISION INTEGRITY — the enforcement record embedded inside the wrapper is byte-identical to what Sarathi sealed. Catches any tampering of the decision content. |

Both gates fail-closed. Both required.

---

## 10. Contact

If anything in this spec is ambiguous, ping back. The integration call must not be the first time something gets clarified.
