# Sarathi — TANTRA Convergence Evidence (Enforcement Boundary)

**For:** TANTRA Convergence / CET integration owners, Bridge team
**Re:** Canonical Live Trace Convergence Lock — Sarathi enforcement participation
**Scope:** Boundary evidence + wire contract for the locked chain. Only the boundary contract and the produced artifacts are described here.
**Status:** Sarathi enforcement boundary implemented, exercised against the locked identity, and integration-ready. Live Sarathi→Bridge transmission is pending endpoint + key provisioning (see §6 and §7).

---

## 1. Locked chain identity (echoed verbatim)

Sarathi consumed the locked identity unchanged. No regeneration, no alias, no substitution.

| Field | Value |
|---|---|
| `execution_id` | `exec-tantra-001` |
| `trace_id` | `trace-tantra-001` |
| `cet_hash` | `89d18ea108d45ece5b98e07e6f54b54b54c8b115e0610e58952328530e8e6801` |
| `schema_version` | `1.0` |
| `contract_version` | `TANTRA-CONVERGENCE-v1` |
| `bucket_key` | `b64147889ed9eff3f303afe8457f5e318e9f77ba24ac2b2a35b7e2ac572d4f80` |
| `boundary` | `CET->Sarathi` |

---

## 2. Required artifact — Sarathi enforcement_decision

This is the artifact requested in the convergence packet, produced by running the locked identity through Sarathi's real enforcement boundary. Fields beyond the template (`schema_version`, `contract_version`, `bucket_key`, `sarathi_seal_hash`, `cet_hash_verification_mode`, `provenance`) are additive and satisfy the packet's Global Artifact Requirements.

```json
{
  "system_name": "Sarathi",
  "artifact_type": "enforcement_decision",
  "schema_version": "1.0",
  "contract_version": "TANTRA-CONVERGENCE-v1",
  "execution_id": "exec-tantra-001",
  "trace_id": "trace-tantra-001",
  "cet_hash": "89d18ea108d45ece5b98e07e6f54b54b54c8b115e0610e58952328530e8e6801",
  "bucket_key": "b64147889ed9eff3f303afe8457f5e318e9f77ba24ac2b2a35b7e2ac572d4f80",
  "boundary": "CET->Sarathi",
  "decision": "allow",
  "enforcement_status": "authorized",
  "enforcement_token_reference": "cap-jwt:f67068ad-74d9-4aee-86ea-e64636c5a396",
  "contract_continuity": {
    "sum_script_received": true,
    "cet_hash_verified": true,
    "trace_id_preserved": true,
    "mutation_detected": false
  },
  "sarathi_seal_hash": "5b9fe4024ad570567904590d3e604003d719da1e0b6f86c81c0ffb76dc94d6df",
  "cet_hash_verification_mode": "continuity",
  "provenance": "sarathi.enforcement_adapter@CET->Sarathi",
  "timestamp_utc": "2026-06-01T09:50:21.5036162Z"
}
```

> `sarathi_seal_hash` is Sarathi's own SHA-256 over the exact SUM-SCRIPT bytes it received — the mutation-detection anchor. It is **not** the cet_hash and does not replace it. The `enforcement_token_reference` (capability jti), `sarathi_seal_hash`, and `timestamp_utc` are regenerated fresh on each enforcement; the authoritative current copy is `proof_logs/tantra_convergence/enforcement_decision_exec-tantra-001.json`. The **locked identifiers (`execution_id`/`trace_id`/`cet_hash`/`bucket_key`) are byte-stable** across every run, as is the signed enforcement-decision reference (`a0019342-…`).

---

## 3. Answers to the 10 evidence questions

| # | Question | Answer |
|---|---|---|
| 1 | Sarathi received contract proof | **Yes.** The SUM-SCRIPT envelope (`schema_version=1.0`, `contract_version=TANTRA-CONVERGENCE-v1`) carrying the locked identity was decoded and accepted at the `CET->Sarathi` boundary. Proof: `contract_continuity.sum_script_received = true` and `sarathi_seal_hash = 5b9fe4024ad570567904590d3e604003d719da1e0b6f86c81c0ffb76dc94d6df`. |
| 2 | Sarathi validation result | **Validated / accepted.** Every boundary gate passed: envelope schema + contract version match the lock; `execution_id`/`trace_id`/`cet_hash`/`bucket_key` present and well-formed; the inner sealed decision verified cryptographically (Ed25519, full multi-gate verifier); trace continuity confirmed. |
| 3 | Enforcement decision: allow/reject | **`allow`** — `enforcement_status = authorized`. |
| 4 | Enforcement token / decision reference | **Yes.** An enforcement capability is issued for the Bridge→Runtime hop, cryptographically bound to the locked identity (`execution_id`, `trace_id`, `cet_hash`, `bucket_key`, `verdict=ALLOW`) under Sarathi's authority key, and verifiable by the Bridge stage offline (no round-trip to Sarathi). Correlation reference for this run: `cap-jwt:f67068ad-74d9-4aee-86ea-e64636c5a396`. A long-lived, re-verifiable signed enforcement-decision reference (`a0019342-6494-0d72-0ebe-237fa67d439f`) is also recorded. (Token issuance/verification mechanics belong to the Bridge integration contract and are out of scope here.) |
| 5 | Rejection reason, if rejected | **N/A — this chain was allowed.** The fail-closed rejection format Sarathi emits when a chain does not validate is documented in §5, with two real demonstrated rejections. |
| 6 | cet_hash verification result | **Verified (mode: `continuity`).** `cet_hash` is structurally valid (64-hex), preserved byte-identical from ingress through every Sarathi egress surface, and bound into the issued capability token. Value unchanged: `89d1…6801`. Sarathi additionally supports **independent recomputation** — when the cet_hash pre-image is supplied, Sarathi recomputes `sha256(pre-image)` and asserts equality (mechanism verified, see §5). For `exec-tantra-001` the pre-image was not supplied, so verification is continuity-based (Sarathi does not fabricate a pre-image — `cet_hash` originates at CET). See §7 to upgrade to recompute. |
| 7 | trace_id verification result | **Preserved (`trace_id_preserved = true`).** Envelope `trace_id` == inner decision `trace_id` == every egress surface == `trace-tantra-001`. Never regenerated, normalized, lowercased, or re-formatted. A mismatch fails closed (see §5). |
| 8 | mutation check result | **`mutation_detected = false`.** Sarathi seals the received SUM-SCRIPT (`sarathi_seal_hash`) and re-asserts identity preservation on egress. Any post-receipt byte change to the contract or the sealed decision changes the inner signature and/or the seal and is rejected fail-closed (demonstrated in §5). |
| 9 | Sarathi → Bridge handoff proof | **The handoff contract is built and READY, but NOT transmitted.** See §6 — `transmission_status = PREPARED_NOT_TRANSMITTED`. **Sarathi has not forwarded this (or any) chain to Bridge:** no acknowledged POST to a registered Bridge ingress has occurred, because no live Bridge connection has been established. This is consistent with the Bridge team's report that the chain is not found on their side. |
| 10 | timestamp / log reference | `timestamp_utc = 2026-06-01T09:50:21.5036162Z`. Evidence artifacts: `proof_logs/tantra_convergence/enforcement_decision_exec-tantra-001.json`, `…/bridge_handoff_exec-tantra-001.json`, `…/sarathi_rejections.jsonl`, and the consolidated `…/CONVERGENCE_SUMMARY.json`. |

---

## 4. Did Sarathi forward this exact chain to Bridge?

**No.** Sarathi did **not** forward `exec-tantra-001 / trace-tantra-001` to Bridge.

- No live connection to Bridge has been established for this chain; no acknowledged Bridge ingress POST exists.
- The Bridge team's finding ("chain not found on their side") is therefore expected and correct.
- What Sarathi **has** done: built the complete, ready-to-send Sarathi→Bridge handoff contract for this exact chain (capability token + headers + continuity hashes, §6). It awaits the Bridge ingress URL + key registration (§7) to transmit. Sarathi does not self-certify a forward it has not actually performed; the handoff status remains `PREPARED_NOT_TRANSMITTED` until a real Bridge ACK is recorded.

---

## 5. Fail-closed behaviour (rejection visibility)

Any chain that does not validate is rejected fail-closed with a trace-bound rejection artifact carrying the locked identifiers, an explicit reason, and `fail_closed: true`. This was exercised against the locked chain identity; two representative rejections produced:

**Mutated sealed decision → signature reject:**
```json
{
  "system_name": "Sarathi",
  "artifact_type": "enforcement_rejection",
  "execution_id": "exec-tantra-001",
  "trace_id": "trace-tantra-001",
  "cet_hash": "89d18ea108d45ece5b98e07e6f54b54b54c8b115e0610e58952328530e8e6801",
  "boundary": "CET->Sarathi",
  "validation_status": "rejected",
  "decision": "reject",
  "error_code": "ERR_CET_INNER_DECISION_INVALID",
  "rejection_reason": "[ERR_TANTRA_SIGNATURE_INVALID] inner decision verification failed",
  "fail_closed": true
}
```

**Trace-id discontinuity (envelope ≠ sealed decision) → reject:**
```json
{
  "error_code": "ERR_CET_TRACE_ID_DISCONTINUITY",
  "validation_status": "rejected",
  "decision": "reject",
  "fail_closed": true,
  "rejection_reason": "inner decision trace_id \"trace-tantra-001\" != envelope trace_id \"trace-tantra-DIFFERENT-999\""
}
```

Boundary rejection codes: `ERR_CET_SCHEMA_VERSION_UNKNOWN`, `ERR_CET_CONTRACT_VERSION_UNKNOWN`, `ERR_CET_MISSING_FIELD`, `ERR_CET_HASH_MALFORMED`, `ERR_CET_BUCKET_KEY_MALFORMED`, `ERR_CET_DECISION_DECODE`, `ERR_CET_TRACE_ID_DISCONTINUITY`, `ERR_CET_HASH_RECOMPUTE_MISMATCH`, `ERR_CET_INNER_DECISION_INVALID`. Every code is returned in both the response body (`error_code`) and the `X-Sarathi-Error-Code` header on the live surface.

---

## 6. Sarathi → Bridge handoff (prepared, ready, not transmitted)

When the chain is allowed, Sarathi prepares the next-hop contract for Bridge. For the locked chain it is built and persisted with `transmission_status = PREPARED_NOT_TRANSMITTED`.

**Outbound headers (Sarathi → Bridge):**

| Header | Value for this chain |
|---|---|
| `X-Sarathi-Execution-ID` | `exec-tantra-001` |
| `X-Sarathi-Trace-ID` | `trace-tantra-001` |
| `X-Sarathi-Decision-ID` | `<sealed decision id>` |
| `X-Sarathi-CET-Hash` | `89d18ea108d45ece5b98e07e6f54b54b54c8b115e0610e58952328530e8e6801` |
| `X-Sarathi-Bucket-Key` | `b64147889ed9eff3f303afe8457f5e318e9f77ba24ac2b2a35b7e2ac572d4f80` |
| `X-Sarathi-SumScript-Seal` | `5b9fe4024ad570567904590d3e604003d719da1e0b6f86c81c0ffb76dc94d6df` |
| `X-Sarathi-Schema-Version` | `1.0` |
| `X-Sarathi-Contract-Version` | `TANTRA-CONVERGENCE-v1` |

**Capability for the Bridge stage:** Sarathi issues an enforcement capability bound to the locked identity (`execution_id`, `trace_id`, `cet_hash`, `bucket_key`, `verdict`) and the SUM-SCRIPT seal, verifiable by the Bridge stage offline (no round-trip to Sarathi). The credential for this run is carried in the handoff artifact (`proof_logs/tantra_convergence/bridge_handoff_exec-tantra-001.json`). Its issuance/verification mechanics belong to the Bridge integration contract and are out of scope here.

**Hash continuity Bridge re-checks:** `cet_hash_preserved`, `trace_id_preserved`, `execution_id_preserved`, plus `sarathi_seal_hash`.

---

## 7. What Sarathi needs from TANTRA to go live

To move from "boundary verified against the locked identity" to "live convergence on real CET-delivered traffic":

1. **Bridge ingress URL + capability verification handshake.** The HTTPS endpoint where Sarathi POSTs the handoff, and confirmation that the Bridge stage consumes Sarathi's published verification key set and pins the expected issuer + audience (mechanics per the Bridge integration contract). Until this is provided, Sarathi→Bridge stays `PREPARED_NOT_TRANSMITTED`.
2. **cet_hash pre-image (to upgrade verification from continuity → recompute).** Either embed the exact canonical bytes CET hashed in the SUM-SCRIPT (an optional `cet_material_b64` field — Sarathi will recompute `sha256` and assert equality), **or** publish the cet_hash canonicalization spec so Sarathi recomputes independently. Without it, Sarathi preserves + binds `cet_hash` (continuity) but cannot independently reproduce CET's digest.
3. **Live SUM-SCRIPT wire shape confirmation.** Confirm CET will POST the envelope Sarathi expects at the `CET->Sarathi` boundary (§8). If CET's live envelope differs, send the exact field list so Sarathi aligns before cutover.
4. **Sovereign decision producer key registration.** Sarathi verifies the *inner* sealed decision cryptographically; it needs the live producer's public key + key id + algorithm registered out-of-band. (In this evidence run a conformance key was used because no live Sovereign-signed decision for this chain has been delivered yet.)
5. **Optional — CET envelope signature.** If CET signs the SUM-SCRIPT envelope itself, share CET's `evaluator_id` + public key; Sarathi will additionally bind the envelope metadata (`execution_id`, `bucket_key`) cryptographically at ingress. Without it, Sarathi binds those into the signed capability token it issues downstream.
6. **Runtime audience confirmation.** Confirm `bhiv-core-runtime` is the intended capability-token audience consumed at the Runtime stage.

---

## 8. Live SUM-SCRIPT envelope Sarathi expects (CET → Sarathi)

```
POST https://<sarathi-url>/sarathi/cet/enforce
Content-Type: application/json
X-Sarathi-Trace-ID: <must equal body.trace_id>
```

```json
{
  "schema_version":   "1.0",
  "contract_version": "TANTRA-CONVERGENCE-v1",
  "execution_id":     "exec-tantra-001",
  "trace_id":         "trace-tantra-001",
  "cet_hash":         "<64-hex CET digest>",
  "bucket_key":       "<64-hex Bucket replay key>",
  "decision_b64":     "<base64-std of the sealed decision's exact canonical wire bytes>",
  "cet_material_b64": "<OPTIONAL base64-std of the bytes CET hashed to produce cet_hash>"
}
```

- `decision_b64` carries the sealed decision verbatim so its signature verifies on byte-identical input (no re-encoding).
- On accept: HTTP 200 + the `enforcement_decision` artifact (§2). On reject: HTTP 4xx + the trace-bound rejection artifact (§5) + `X-Sarathi-Error-Code`.
- Re-POSTing the byte-identical chain within the replay window is rejected fail-closed (replay protection); a fresh sealed decision is expected per logical execution.

---

## 9. Reproduce / verify

The evidence artifacts in `proof_logs/tantra_convergence/` are produced by Sarathi's enforcement boundary processing the locked identity end-to-end (real signature verification, real continuity gates, real token issuance, real fail-closed rejection paths). The same boundary serves the live HTTPS surface in §8.

---

## 10. Summary

- Sarathi's `CET->Sarathi` enforcement boundary is implemented and verified against the locked chain identity.
- Decision for `exec-tantra-001`: **allow / authorized**, with full contract-continuity proof and a bound capability token.
- `execution_id`, `trace_id`, `cet_hash` are preserved byte-identical; mutation and discontinuity fail closed and trace-bound.
- Sarathi has **not** forwarded this chain to Bridge; the handoff is prepared and awaits Bridge endpoint + key provisioning.
- To go live, Sarathi needs the items in §7.
