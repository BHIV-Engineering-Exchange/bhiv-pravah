# Sarathi — Integration Architecture Note

**Audience:** BHIV management / reviewer / VC due-diligence reader.
**Length:** ~3 minutes.
**Purpose:** One-page summary of where Sarathi sits in the TANTRA chain, what it does, and what changed for v15.11 deployment readiness.

---

## 1. What Sarathi is

Sarathi is the **Policy Enforcement Point (PEP)** for the BHIV TANTRA execution chain. Every action the system takes on behalf of a user must transit Sarathi:

```
   Sovereign Core    →    Sarathi    →    Bucket / InsightFlow / BHIV Core
   (decides)              (enforces)        (stores, observes, executes)
```

Sarathi answers one question per request:

> *Is this decision cryptographically authentic, structurally valid, and properly bound — and has every governance rule been applied so nothing downstream can change it?*

If yes, Sarathi seals an immutable record and propagates it to the three peer systems. If no, it halts the chain fail-closed and records the rejection.

---

## 2. Why Sarathi is integration-critical

Without Sarathi, the BHIV chain has three integrity gaps:

| Gap | Without Sarathi | With Sarathi |
|---|---|---|
| Decision authenticity | Core / Bucket / InsightFlow trust whatever Sovereign sent. | Sarathi cryptographically verifies Sovereign's signature against a registered key before letting the decision propagate. |
| Cross-system byte-equality | Each system can re-marshal / mutate the decision before storing. | Sarathi seals a canonical envelope; peers prove byte-identical receipt via signed callbacks. |
| Audit chain | Loose JSONL logs per system, hard to reconcile. | Single `trace_id` flows through every hop; every artefact is hash-bound to a `chain_binding_hash`. |

Sarathi is the cryptographic spine that makes the chain audit-replayable.

---

## 3. The v15.11 release

Six independent capabilities locked in for final deployment:

| Capability | Status | Why it matters |
|---|---|---|
| TANTRA Final Contract verifier | Live | Sarathi accepts only the BHIV-frozen `tantra.decision.v1` shape. 12-step fail-closed verifier. |
| Crypto-agile provider | Live | Ed25519 today; one env var flip to post-quantum Composite ML-DSA-65 + Ed25519 (via Cloudflare CIRCL). No business-logic change. |
| Peer-key registry with pinning | Live | Bucket / InsightFlow / Core public keys are pinned in operator-controlled storage. No more trust-on-first-use. |
| Receipt-replay rejection | Live | Captured-once peer receipts cannot be replayed (300 s window per peer). |
| Production peer propagation hook | Live | After every accepted decision, Sarathi POSTs the canonical record to all three peers in a background goroutine. |
| Load-bearing X-API-Key fingerprint | Live | sha256(API key) constant-time compare against a registered fingerprint. Defense-in-depth on top of the Ed25519 signature. |

Build clean. Tests green. Fail-closed verified at every gate.

---

## 4. Cross-team integration model

```
                                 ┌───────────────────────────┐
                                 │   BHIV Core / Sovereign   │
                                 │     (Raj / Aakanksha)     │
                                 └─────────────┬─────────────┘
                                  signs        │ POST /sarathi/enforce
                                  TANTRA       │  (tantra.decision.v1 + Ed25519)
                                  decision     │  + X-API-Key (sha256 fingerprint match)
                                               ▼
                                 ┌───────────────────────────┐
                                 │          Sarathi          │
                                 │   12-step TANTRA verifier │
                                 │   Seal canonical envelope │
                                 │   Cryptographic chain     │
                                 └────────┬───────┬──────────┘
                            raw canonical │       │ raw canonical
                            envelope      │       │ envelope (post-exec)
                                          ▼       ▼
              ┌──────────────────────────────┐    ┌─────────────────────────┐
              │       Bucket (Siddhesh)      │    │   BHIV Core (Raj)       │
              │       persist atomically     │    │   record post-execution │
              │       sign receipt → Sarathi │    │   sign receipt → Sarathi│
              └──────────────────────────────┘    └─────────────────────────┘

              ┌──────────────────────────────┐
              │   InsightFlow (Vijay/Nupur)  │ ←── raw canonical envelope
              │   process + observe          │
              │   sign receipt → Sarathi     │
              └──────────────────────────────┘
```

All three peers send signed Ed25519 receipts to `POST /v1/downstream-ack`. Sarathi verifies signature, byte-equality of received body vs sealed bytes, peer-key pinning, and replay status. Closes the per-execution gate when all three receipts arrive within 300 s.

---

## 5. Cryptographic posture

| Layer | Algorithm | Where |
|---|---|---|
| Decision authenticity (Core → Sarathi) | Ed25519 (RFC 8032) over RFC 8785-fixed-order canonical bytes | Inbound TANTRA payload signature |
| API key defense-in-depth | SHA-256 fingerprint check, constant-time compare | `/sarathi/enforce` |
| Outbound integrity (Sarathi → peers) | SHA-256 of canonical envelope; identity-equal at peer | `X-Sarathi-Response-Hash` header + receipt callback |
| Receipt authenticity (peers → Sarathi) | Ed25519 (RFC 8032) over RFC 8785-alphabetical canonical bytes | `/v1/downstream-ack` |
| Peer-key authority | Operator-controlled registry pinning, constant-time compare | `live/trust_snapshot.json` peer_keys |
| Replay protection | SHA-256 keyed by decision / receipt; 300 s window | TANTRA + receipt replay stores |
| Quantum-safety (optional) | Composite ML-DSA-65 + Ed25519 (FIPS 204 + RFC 8032) | Behind one env-var flip |

No proprietary primitives. Every primitive is RFC- or FIPS-standardised.

---

## 6. Production readiness verdict

| Dimension | Status |
|---|---|
| Build | ✅ Clean (Go 1.25, Windows AMD64, ~16 MB binary) |
| Tests | ✅ 30+ TANTRA / crypto / registry tests + 17 canonical-JSON tests green, no mocks on the live path |
| Static analysis | ✅ `go vet` clean |
| Fail-closed verified | ✅ Smoke-tested: bad provider value panics; mutated payload rejects; replay rejects; key mismatch rejects |
| Production env vars documented | ✅ `DEPLOYMENT_GUIDE.md` |
| Operator runbook | ✅ `DEPLOYMENT_GUIDE.md` + `NGROK_VALIDATION_SCRIPT.md` |
| Per-team integration specs | ✅ `CORE_INTEGRATION.md` / `BUCKET_INTEGRATION.md` / `INSIGHTFLOW_INTEGRATION.md` |
| Final contract definition | ✅ `FINAL_CONTRACT_DEFINITION.md` |
| Hash verification proof | ✅ `HASH_VERIFICATION_PROOF.md` |
| Cross-team blockers | ⚠️ See `OPEN_BLOCKERS_LIST.md` — 4 items requiring peer-team confirmation before going live |
| Live integration proof | ⏳ Pending real cross-team end-to-end run (template in `LIVE_PROOF_TEMPLATE.md`) |

---

## 7. What the integration call should produce

One end-to-end successful chain with:
- Core signs and posts one decision.
- Sarathi accepts (200 OK + sealed envelope JSON).
- Bucket / InsightFlow / Core post-exec receive the canonical envelope.
- Three signed receipts arrive back at Sarathi within 300 s.
- All three pass byte-equality, key pinning, and replay gates.
- Same `trace_id` visible in 8 audit JSONL files.

If that sequence works, Sarathi is live in the TANTRA chain.

---

## 8. Where to read more

| You want | File |
|---|---|
| Contract details (TANTRA decision + receipt) | `FINAL_CONTRACT_DEFINITION.md` |
| Peer team integration specs (share with Raj / Siddhesh / Vijay) | `CORE_INTEGRATION.md`, `BUCKET_INTEGRATION.md`, `INSIGHTFLOW_INTEGRATION.md` |
| Deployment / environment / runbook | `DEPLOYMENT_GUIDE.md` |
| Operator runbook for ngrok deployment | `NGROK_VALIDATION_SCRIPT.md` |
| Review packet (formal sign-off doc) | `REVIEW_PACKET.md` |
| Hash chain proof | `HASH_VERIFICATION_PROOF.md` |
| Open blockers / pending cross-team items | `OPEN_BLOCKERS_LIST.md` |
| Template for live-run proof artefacts | `LIVE_PROOF_TEMPLATE.md`, `CROSS_SYSTEM_EXECUTION_PROOF_TEMPLATE.md` |

— *Sarathi is integration-ready pending cross-team confirmations listed in `OPEN_BLOCKERS_LIST.md`.*
