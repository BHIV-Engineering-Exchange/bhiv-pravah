# Sarathi ↔ CET — Integration Request

**For:** CET team (Contract / Canonical Execution Trace)
**Re:** Wiring the `CET → Sarathi` hop of the convergence chain
**Status:** Sarathi's CET-ingest boundary is implemented and verified against the locked chain identity. This doc is the wire contract + the short list of items each side needs from the other to go live.

The chain: **Core → CET → Sarathi → Bridge → Runtime → InsightFlow → Bucket.** CET seals the Core decision into a SUM-SCRIPT and hands it to Sarathi; Sarathi enforces and prepares the next hop.

---

## 1. The endpoint CET posts to

```
POST  https://<sarathi-public-url>/sarathi/cet/enforce
Content-Type: application/json
X-Sarathi-Trace-ID: <must equal body.trace_id>      # optional but recommended
```

- **Accept →** HTTP 200 + a Sarathi `enforcement_decision` artifact (preserves `execution_id`/`trace_id`/`cet_hash`, `decision=allow`, contract-continuity proof).
- **Reject →** HTTP 4xx + a trace-bound, fail-closed rejection artifact + `X-Sarathi-Error-Code` header.

(The live base URL is shared out-of-band once the tunnel/host is up.)

---

## 2. The SUM-SCRIPT envelope Sarathi expects (request body)

```json
{
  "schema_version":   "1.0",
  "contract_version": "TANTRA-CONVERGENCE-v1",
  "execution_id":     "exec-tantra-001",
  "trace_id":         "trace-tantra-001",
  "cet_hash":         "<64-hex CET integrity digest>",
  "bucket_key":       "<64-hex Bucket replay key>",
  "decision_b64":     "<base64-std of the sealed decision's EXACT canonical wire bytes>",
  "cet_material_b64": "<OPTIONAL: base64-std of the exact bytes CET hashed to produce cet_hash>"
}
```

Field rules:

| Field | Rule |
|---|---|
| `schema_version` | exactly `1.0` |
| `contract_version` | exactly `TANTRA-CONVERGENCE-v1` |
| `execution_id` | upstream-locked; Sarathi preserves it byte-identical, never regenerates |
| `trace_id` | upstream-locked; must equal the sealed decision's `trace_id` |
| `cet_hash` | 64 lowercase hex |
| `bucket_key` | 64 lowercase hex |
| `decision_b64` | base64-std of the sealed decision's exact canonical bytes (so its signature verifies on byte-identical input — **do not re-encode** the inner decision) |
| `cet_material_b64` | optional; see §4 |

No extra top-level fields (unknown fields are rejected fail-closed).

---

## 3. What Sarathi does with it (so CET knows the guarantees)

1. Validates the envelope (versions, identity fields, hex shapes).
2. Verifies the **sealed inner decision** cryptographically (Ed25519) against the registered producer key, and confirms its `trace_id` equals the envelope `trace_id`.
3. **Preserves** `execution_id` / `trace_id` / `cet_hash` unchanged on every downstream surface, and seals the received SUM-SCRIPT (a SHA-256 mutation anchor).
4. Emits the `enforcement_decision` artifact and prepares the Sarathi→Bridge handoff.
5. Any discontinuity, mutation, or signature failure → fail-closed rejection (the chain does not proceed to Bridge).

---

## 4. `cet_hash` — the one piece of logic we need to align

`cet_hash` originates at CET and Sarathi **preserves and binds** it. Sarathi does **not** invent CET's pre-image. There are two verification modes:

- **continuity** (default): `cet_hash` is structurally valid, preserved byte-identical end-to-end, and bound into Sarathi's signed outputs.
- **recompute + continuity** (stronger): if CET includes `cet_material_b64` (the exact bytes CET hashed), Sarathi recomputes `sha256(material)` and asserts it equals `cet_hash`. A mismatch is a hard reject.

**What we need from CET to enable recompute:** either
(a) include `cet_material_b64` in every SUM-SCRIPT, **or**
(b) publish the exact `cet_hash` canonicalization spec (the precise field set + ordering + encoding CET hashes) so Sarathi reproduces the digest independently.

Until one of those arrives, Sarathi runs in **continuity** mode (which is correct and fail-closed — it just doesn't independently recompute CET's digest).

---

## 5. What Sarathi needs FROM CET

1. **Confirm the SUM-SCRIPT shape** in §2 (or send CET's actual envelope field list so Sarathi aligns the decoder before cutover).
2. **`cet_hash` pre-image or spec** (§4) — to upgrade to recompute.
3. **Sealed-decision pass-through confirmation:** confirm the inner decision CET seals is the Core/Sovereign-signed `tantra.decision.v1`, carried **byte-identical** (Sarathi already holds the Core producer key). If CET re-serializes it, the inner signature breaks — please carry the exact signed bytes.
4. **Optional — does CET sign the envelope itself?** If CET adds its own signature over the envelope metadata (`execution_id`, `cet_hash`, `bucket_key`, `trace_id`), send CET's `evaluator_id` + Ed25519 public key + key_id so Sarathi can additionally bind the envelope at ingress. If not, Sarathi binds those into the signed capability it issues downstream.
5. **CET callback/endpoints (if any):** if Sarathi must fetch anything from CET (e.g. to resolve `cet_material` by `cet_hash`), send the URL + auth. If CET is push-only to Sarathi, say so.

---

## 6. What Sarathi GIVES CET (already ready)

- The live ingest endpoint (§1) + the exact envelope contract (§2) + the fail-closed error codes (`ERR_CET_*`).
- The `enforcement_decision` artifact shape returned on accept, echoing the locked identity + a contract-continuity proof.
- A guarantee: `execution_id` / `trace_id` / `cet_hash` are preserved byte-identical; mutation and discontinuity fail closed and are trace-bound.

---

## 7. One-line ask

Please confirm §2 (envelope shape) and choose a `cet_hash` option in §4 (material vs spec). With those two answers we can run a live `CET → Sarathi` SUM-SCRIPT post end-to-end.
