# Sarathi — System Overview

A new developer should be able to read this once and understand what Sarathi is,
what it does, and how the pieces fit. Details on running it are in
`SETUP_GUIDE.md`; the code layout is in `REPO_MAP.md`.

---

## 1. What Sarathi is

Sarathi is a **Policy Enforcement Point (PEP)** for the BHIV ecosystem. It is the
component that takes a governance **decision** (already made by an upstream
decision authority), **enforces** it, proves it was enforced honestly, and
records an immutable trail. It does not invent policy — it executes and witnesses
enforcement.

One sentence: **Sarathi receives a sealed decision, verifies it cryptographically,
records an immutable audit entry, and optionally propagates the verified result
to downstream systems — without ever trusting an unverified input.**

---

## 2. What it does (responsibilities)

| Responsibility | Meaning |
|---|---|
| **Enforce** | Apply ALLOW / DENY / ESCALATE to an incoming decision and produce a sealed enforcement response. |
| **Verify** | Check the decision's hashes and signatures before acting (fail-closed). |
| **Seal + sign** | Canonicalize the response (RFC 8785) and sign it with Sarathi's Ed25519 enforcement key. |
| **Audit** | Append every decision, transmission, and receipt to immutable JSONL logs. |
| **Propagate (optional)** | Fan out the verified result to peers (Bucket, InsightFlow, Core) and collect signed receipts. |
| **Witness** | Independently verify downstream storage (e.g. read an artifact back from Bucket and confirm byte-identity). |

---

## 3. What it is NOT

- Not a policy **decision** engine — the verdict arrives from upstream; Sarathi enforces it.
- Not a database — storage durability belongs to the downstream chain (Bucket).
- Not dependent on any single peer — peers are integrated through stable wire contracts and can be enabled independently.

---

## 4. The ecosystem around Sarathi

| Peer | Relationship | Direction |
|---|---|---|
| **Decision authority / Bridge** | Sends Sarathi the decision to enforce (inbound, authenticated). | → Sarathi |
| **Bucket** | The shared append-only custody chain. Sarathi writes the sealed decision and reads it back to witness it. | Sarathi → Bucket |
| **InsightFlow** | Observability / intelligence layer. Sarathi sends digest + full-record events; InsightFlow returns signed receipts. Off-chain (its failure never halts enforcement). | Sarathi ↔ InsightFlow |
| **Core** | Records post-execution results. | Sarathi → Core |

---

## 5. Two integrity guarantees

1. **Transport integrity** — `body_hash`: SHA-256 over the exact bytes Sarathi
   sends on the wire. Catches in-flight corruption.
2. **Decision integrity** — `response_hash`: SHA-256 over the sealed canonical
   decision bytes. Catches tampering with the decision content.

Both are minted **before** sending and verified on the way back (read-back for
Bucket; signed receipt for InsightFlow). This "dual-hash" model is the backbone
of Sarathi's non-repudiation.

---

## 6. How a request flows (short version)

```
Inbound decision
   → authenticate caller
   → verify decision hashes/signature (fail-closed)
   → enforce verdict + seal canonical response
   → sign custody receipt
   → append to audit log
   → (if enabled) propagate to peers + collect receipts
   → return enforcement response
```

The detailed version, with the gated-bridge bypass prevention and the
propagation fan-out, is in `ARCHITECTURE_FLOW.md`.

---

## 7. Operating modes

| Mode | Command | Use |
|---|---|---|
| Service | `--service` | Long-lived HTTP enforcement endpoint (the production mode). |
| Bucket transmit | `--bucket-transmit --bucket-url=...` | One-shot live Bucket integration proof. |
| Post task to Core | `--post-task-to-core ...` | Drive a decision through the chain. |
| Other CLIs | `cmd_*` entry points | Key generation, JWT authority, peer-key registration, convergence. |

---

## 8. Security posture (one paragraph)

Every inbound request transits a gated bridge that makes bypass structurally
impossible (compile-time passport check). Decisions are verified before
enforcement and the pipeline fails closed. Private keys never leave the process;
only public keys and fingerprints cross the wire. In `SARATHI_ENV=production`,
the service refuses to start without inbound auth, non-default caller keys, and a
populated trust registry. See `SETUP_GUIDE.md` §5.5 for the production gates.
