# Sarathi ↔ Bridge — Integration Request

**For:** Bridge team
**Re:** Wiring the `Sarathi → Bridge` hop of the convergence chain
**Status:** Sarathi builds a complete, ready-to-send handoff for every allowed chain. It is currently held as `PREPARED_NOT_TRANSMITTED` — Sarathi will not claim a forward it has not actually made. This doc is the handoff contract + the short list each side needs from the other to turn on live transmission.

The chain: **Core → CET → Sarathi → Bridge → Runtime → InsightFlow → Bucket.** Sarathi enforces, then hands a validated, capability-bound contract to Bridge; Bridge verifies and forwards to Runtime for execution.

---

## 1. The handoff Sarathi sends Bridge (request body)

```json
{
  "system_name": "Sarathi",
  "artifact_type": "bridge_handoff",
  "boundary": "Sarathi->Bridge",
  "schema_version": "1.0",
  "contract_version": "TANTRA-CONVERGENCE-v1",
  "execution_id": "exec-tantra-001",
  "trace_id": "trace-tantra-001",
  "cet_hash": "<64-hex>",
  "bucket_key": "<64-hex>",
  "decision": "allow",
  "enforcement_token_reference": "<capability reference>",
  "capability_token": "<the capability Bridge verifies offline>",
  "hash_continuity": {
    "cet_hash_preserved": true,
    "trace_id_preserved": true,
    "execution_id_preserved": true,
    "sarathi_seal_hash": "<64-hex Sarathi seal over the received contract>"
  },
  "headers": { "...": "the X-Sarathi-* set below" }
}
```

Outbound headers on the hop:

| Header | Meaning |
|---|---|
| `X-Sarathi-Execution-ID` | locked `execution_id` |
| `X-Sarathi-Trace-ID` | locked `trace_id` |
| `X-Sarathi-Decision-ID` | sealed decision id |
| `X-Sarathi-CET-Hash` | locked `cet_hash` (Bridge re-checks continuity) |
| `X-Sarathi-Bucket-Key` | Bucket replay reference |
| `X-Sarathi-SumScript-Seal` | Sarathi's mutation-detection seal |
| `X-Sarathi-Schema-Version` / `X-Sarathi-Contract-Version` | `1.0` / `TANTRA-CONVERGENCE-v1` |

---

## 2. The capability Bridge verifies (offline)

Sarathi issues an enforcement capability bound to the locked identity. Bridge should verify it **without any round-trip to Sarathi**:

- It is a compact, signed token (algorithm **EdDSA / Ed25519**) carrying the locked identity and verdict: `execution_id`, `trace_id`, `cet_hash`, `bucket_key`, `verdict=ALLOW`, and the SUM-SCRIPT seal.
- Audience is **`bhiv-core-runtime`** (the Runtime stage). Bridge should pin the expected `aud` and issuer.
- Bridge verifies the signature against Sarathi's **published verification key set (JWKS)** at:
  ```
  GET  https://<sarathi-public-url>/sarathi/.well-known/jwks.json
  ```
  Resolve the signing key by its `kid`, cache the key set, and re-fetch on rotation (Sarathi rotates with a grace window so previously-issued tokens keep verifying).

Bridge's gate on each handoff should be: signature valid → `aud`/issuer pinned → `cet_hash` / `trace_id` / `execution_id` in the token equal those in the headers and body → `bucket_key` reference resolves. Any mismatch: reject and do not forward to Runtime.

---

## 3. What Sarathi needs FROM Bridge (to go live)

1. **Bridge ingress URL** — the HTTPS endpoint where Sarathi POSTs the handoff (§1).
2. **Capability-verification confirmation** — confirm Bridge consumes the JWKS in §2, pins `aud=bhiv-core-runtime` + issuer, and re-checks hash continuity. If Bridge wants a different audience or an additional claim, tell us now.
3. **Handoff shape confirmation** — confirm §1 is acceptable, or send Bridge's required request schema so Sarathi aligns the body before cutover.
4. **ACK contract** — what Bridge returns on accept (status + body). Sarathi only marks a handoff `TRANSMITTED` on a real, acknowledged response; please define the ACK (and whether it is signed — if so, send Bridge's `peer`/key so Sarathi can verify it).
5. **Bridge identity (optional)** — if Bridge signs its ACK or its forward-to-Runtime record, send Bridge's Ed25519 public key + key_id for registration.

---

## 4. What Sarathi GIVES Bridge (already ready)

- The handoff contract (§1) + the capability + the `X-Sarathi-*` headers + the continuity hashes.
- The JWKS verification surface (§2) for offline capability verification, with grace-window rotation.
- A guarantee: the locked `execution_id` / `trace_id` / `cet_hash` in the headers, body, and capability are identical and preserved from the upstream seal; `bucket_key` is the Bucket replay reference; `sarathi_seal_hash` lets Bridge confirm the contract was not mutated at Sarathi.

---

## 5. Why "not transmitted yet"

Sarathi has built and is holding the handoff for the locked chain (`exec-tantra-001`) as `PREPARED_NOT_TRANSMITTED`. It has **not** forwarded it because no live Bridge ingress + acknowledged response exists yet. As soon as §3 items 1–4 arrive, Sarathi transmits and flips the status to `TRANSMITTED` on the Bridge ACK.

---

## 6. One-line ask

Send the **Bridge ingress URL**, confirm **capability verification via JWKS + `aud=bhiv-core-runtime`**, and define the **ACK shape**. With those, Sarathi can do a live `Sarathi → Bridge` handoff for the locked chain immediately.
