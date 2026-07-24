# Sarathi — Durability & Persistence Evidence (TANTRA Convergence)

**For:** TANTRA convergence / integration owners
**Re:** Sarathi durability side — persistent authority keys, key rotation, replay continuity after restart, persistence implementation
**Scope:** Verification evidence + proof-artifact locations. This describes behaviour and where the evidence lives.

---

## Verdict

**All four items are already implemented and in use — not pending.** Treat the Sarathi durability side as a **satisfied dependency** for convergence. Evidence locations and a deterministic proof are below. The only convergence items that remain open are the *live wire-up* to CET / Bridge (endpoints + key registration) — durability itself is done.

| # | Item | Status | Mechanism (summary) | Evidence |
|---|---|---|---|---|
| 1 | Persistent authority keys | ✅ Implemented | Signing/authority keys loaded from disk on boot (persistent, not ephemeral). Decision-producer + peer public keys persist in the signed trust snapshot. | `live/keys/…`, `live/trust_snapshot.json` |
| 2 | Key rotation strategy | ✅ Implemented | Grace-period rotation for the capability-issuing key; registry re-registration for producer/peer keys. No private key crosses the wire. | rotation + registration commands (below) |
| 3 | Replay verification continuity after restart | ✅ Implemented + proven | Replay window persisted append-only and rehydrated on boot within the TTL; stale rows dropped. | `proof_logs/tantra_replay.jsonl`; passing tests (below) |
| 4 | Durability / persistence implementation | ✅ Implemented | Append-only audit (JSONL) with optional database backing + fail-closed audit gate; outbound-hash store, inbound nonce store, sealed attestations, convergence artifacts — all persisted. | `proof_logs/…`, `live/…` |

---

## 1. Persistent authority keys

- The capability-issuing authority key is **persisted on disk and loaded on boot** — it survives restarts; the same public key continues to verify previously-issued credentials. (If no key file is present the process can fall back to an in-memory ephemeral key and warns loudly; production runs on the persisted key.)
- Decision-producer public keys and downstream peer public keys are **pinned in a persisted, signed trust snapshot** (with API-key fingerprints where applicable). They are loaded on boot and used for every verification.
- The enforcement-attestation signing key is persisted at an operator-configured path.

**Where the evidence lives (repo paths):**
- `live/keys/jwt_authority/` — persistent authority key + public key + key id.
- `live/keys/<producer>/` — persistent producer signing material (operator-provisioned).
- `live/trust_snapshot.json` — registered producer/peer public keys + fingerprints.

No private key material is included in any artifact handed out; only public keys / fingerprints / key ids are shareable.

---

## 2. Key rotation strategy

- **Capability-issuing key — grace-period rotation.** A rotation makes the new key current and keeps the **previous public key verifiable for a configurable grace window**, so credentials already issued under the old key keep verifying until the grace window expires. The published verification key set lists both the current and the grace-period key with an explicit expiry. Operator command shape:
  ```
  --rotate-jwt-authority [--grace-hours=<H>]
  ```
- **Decision-producer and peer keys — registry re-registration.** Rotation registers a new public key under a new key id; the old key id stops being accepted at the next registry reload. Operator command shapes:
  ```
  --register-tantra-evaluator  --evaluator-id=<id> --key-id=<new> --public-key=<hex> ...
  --register-peer-key          --peer=<bucket|core|insightflow> --public-key=<hex> ...
  ```
- Rotations are **out-of-band and public-key-only** — no private key ever crosses the wire. Every rotation/registration appends an audit row.

---

## 3. Replay verification continuity after restart

This is implemented and **proven deterministically**, not asserted:

- Every accepted decision is written **append-only** to a persistent replay log. On boot, the replay store **rehydrates** all rows still inside the TTL window (300 s) back into memory. A decision accepted **before** a restart is therefore still rejected as a replay **after** the restart, for the remainder of the window. Rows **outside** the window are dropped on rehydrate, so a stale entry never causes a false-positive replay.
- Two replay surfaces are enforced: the decision hash and the signed-payload hash.
- The peer-receipt replay surface has the same persist-and-rehydrate behaviour.

**Proof artifacts (repo paths):**
- Live trail: `proof_logs/tantra_replay.jsonl` (append-only; rehydrated on boot).
- Deterministic tests (both PASS):
  - `TestTantraReplay_ContinuityAfterRestart` — record → simulate restart (fresh store, rehydrate from the same log) → the same decision is rejected with the replay error code.
  - `TestTantraReplay_ExpiredRowsDroppedOnRehydrate` — a stale (out-of-window) row is dropped on rehydrate and does not block a fresh decision.

Reproduce:
```
go test -run "TestTantraReplay_" -count=1 -v .
# → PASS: TestTantraReplay_ContinuityAfterRestart
# → PASS: TestTantraReplay_ExpiredRowsDroppedOnRehydrate
```

---

## 4. Existing durability / persistence implementation

Beyond keys + replay, persistence is pervasive and fail-closed:

- **Audit trail** — append-only JSONL, with an **optional database backing**; an audit-write failure **fails closed** (no execution proceeds without its audit record). Backups are written alongside the live stream.
- **Outbound integrity store** — per-decision body/response hashes are persisted and **rehydrated on boot**, so receipt verification survives restarts.
- **Inbound nonce store** — persisted to prevent cross-restart nonce reuse.
- **Sealed enforcement attestations** — appended to `proof_logs/sarathi_enforcement_attestations.jsonl` (re-verifiable, long-lived decision records).
- **Convergence evidence** — every CET→Sarathi enforcement decision, rejection, and Bridge handoff is persisted under `proof_logs/tantra_convergence/` (per-execution standalone files + append-only JSONL + a consolidated summary).

---

## What is pending (so the dependency map is accurate)

Durability is **done**. The remaining convergence-open items are purely the **live connection** ones (not durability):

1. Bridge ingress URL + capability-verification handshake (to actually transmit the Sarathi→Bridge handoff; today it is built and held as `PREPARED_NOT_TRANSMITTED`).
2. The cet_hash pre-image (or its canonicalization spec) to upgrade cet_hash verification from continuity to independent recompute.
3. Live decision-producer key registration for the inner sealed decision.



---

## Summary for your dependency sheet

- Persistent authority keys — **implemented.**
- Key rotation (grace-period + registry re-registration) — **implemented.**
- Replay continuity after restart — **implemented + proven** (`proof_logs/tantra_replay.jsonl`; two passing tests).
- Durability/persistence (audit, outbound-hash, nonce, attestations, convergence artifacts) — **implemented.**

Mark the Sarathi durability side **satisfied**, not pending.
