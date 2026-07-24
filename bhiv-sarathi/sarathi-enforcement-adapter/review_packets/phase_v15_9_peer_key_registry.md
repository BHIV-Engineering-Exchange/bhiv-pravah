# Phase v15.9 — Peer-Key Registry + Receipt-Replay (closing the TOFU gap)

**Status:** Implemented; 10/10 new tests green; full suite green; build clean.
**Owner:** Hemanth B (Sarathi).
**Disclosure:** This phase was triggered by an honest correction to v15.7 docs that claimed pinning existed when the actual code was TOFU. The v15.9 implementation makes the docs accurate by adding the missing registry, not by softening the docs.

---

## 1. The gap I found and admitted to

The v15.7 KB / plan / NGROK script referenced `--register-peer-key` as if it existed. **It did not.** The actual peer-receipt code (`peer_common.go::VerifyReceipt`) ran trust-on-first-use:

- The peer's public key travelled INSIDE every receipt (`peer_public_key_hex` field).
- `VerifyReceipt` decoded that key and verified the receipt's signature against it.
- No registry, no pinning, no operator-side authority binding.

Threat:
- Any caller able to land a POST on `/v1/downstream-ack` could substitute their own keypair, sign their own receipt with it, and the signature would internally verify.
- An attacker who obtained one peer's private key could recycle it across other peer identities (cross-peer impersonation) because the verifier never checked which key BELONGED to which peer.
- A captured-once valid receipt could be replayed indefinitely (the existing `ExecutionGate` deduplicated per-peer but did not reject content-identical replays).

CRO grade: **High.** CSO grade: **Hard reject in any production posture.**

---

## 2. v15.9 fix

### 2.1 New files

| File | Role |
|---|---|
| `peer_key_registry.go` | In-memory registry of pinned peer public keys + 4-gate `CheckPinned` (peer-kind / presence / status / constant-time key match). |
| `peer_receipt_replay.go` | 300 s replay window keyed by `sha256(raw receipt bytes) || peer`. |
| `cmd_peer_key_register.go` | `--register-peer-key` CLI. Validates peer kind, validates Ed25519 32-byte hex, atomic snapshot write, audit row. |
| `peer_key_registry_test.go` | 10 round-trip tests covering relaxed-no-entry, strict-no-entry-rejects, registered-matching-accepts, mismatched-key-rejects, suspended-rejects, cross-peer-impersonation-rejects, unknown-peer-kind-rejects, replay-rejects, constant-time-compare correctness, entry shape validation. |

### 2.2 Files modified

| File | Change |
|---|---|
| `peer_common.go::VerifyReceipt` | Added pinning + replay gates AFTER the existing signature check. Both fail-closed. |
| `evaluator_admin_cli.go` | New CLI dispatch: `--register-peer-key`. |
| `enforcement_adapter_main.go` | Boot wiring: `BootstrapPeerKeyRegistry(SARATHI_TRUST_SNAPSHOT)` + `BootstrapPeerReceiptReplayStore()` after the TANTRA boot block. |

### 2.3 Trust snapshot schema (additive)

The `live/trust_snapshot.json` file gains a new optional array:

```json
{
  "version": "v15.9",
  "evaluators": [ ... ],
  "tantra_evaluators": [ ... ],
  "peer_keys": [
    {
      "peer": "bucket",
      "name": "Bucket production",
      "status": "ACTIVE",
      "public_key_hex": "<64-hex Ed25519>",
      "registered_at": "2026-05-26T08:00:00Z",
      "notes": "(optional)"
    }
  ]
}
```

Other top-level arrays are preserved across `--register-peer-key` writes via raw-map round-tripping in `cmd_peer_key_register.go` — no field loss across upgrades.

### 2.4 Pinning modes

Env `SARATHI_PEER_KEY_PINNING`:

| Mode | Behaviour | When to use |
|---|---|---|
| `relaxed` (default) | If a peer has a registry entry, embedded key MUST match. If no entry, warn loudly on stderr and accept embedded key (TOFU fallback). | Migration window — existing deployments keep working while you register each peer. |
| `strict` | Every receipt MUST come from a registered peer. Unregistered peers reject. | Production. |

Unknown values PANIC at boot (fail-closed; no ambiguous posture).

### 2.5 `VerifyReceipt` flow (after v15.9)

```
1. JSON decode → PeerReceipt
2. schema_version == "sarathi.live.receipt/v1.0"
3. Decode peer_public_key_hex → 32 bytes
4. Decode receipt_signature → 64 bytes
5. Canonicalise with receipt_signature cleared
6. ed25519.Verify(embedded_pubkey, canonical_bytes, signature)
7. received_body_hash == response_hash
8. [NEW v15.9] Peer-key registry CheckPinned():
     - peer is one of bucket/core/insightflow              (G1)
     - registry entry exists (relaxed-warn / strict-reject)(G2)
     - status == ACTIVE                                     (G3)
     - constant-time compare embedded vs registered key    (G4)
9. [NEW v15.9] Receipt-replay store Check():
     - sha256(raw bytes) keyed by peer
     - reject if seen within 300 s
```

Every gate fail-closed. The signature check ALONE no longer suffices.

---

## 3. CRO findings + resolutions

| # | Finding | Resolution |
|---|---|---|
| CRO-1 | Docs claimed `--register-peer-key` existed; code lacked it. | CLI implemented; KB_17 §14b corrected; SARATHI_SYSTEM_GUIDE XII.5 corrected; NGROK script section was already accurate. |
| CRO-2 | Trust snapshot file may carry multiple arrays; `--register-peer-key` must not clobber other arrays. | Raw-map round-trip in `cmd_peer_key_register.go` preserves every other top-level key. Verified via smoke test (snapshot containing evaluators + tantra_evaluators is unchanged after registering a peer key). |
| CRO-3 | Atomic write to avoid mid-write corruption. | `writePeerKeySnapshotAtomically` writes to `.tmp` then `os.Rename`. |
| CRO-4 | Audit trail of registrations. | Every `--register-peer-key` invocation appends one JSONL row to `proof_logs/peer_key_registry_audit.jsonl` with timestamp + action + peer + key fingerprint + replaced flag. |
| CRO-5 | Rotation procedure. | Re-run `--register-peer-key` with the new public key. The CLI prints "updated" (not "registered") and the audit row carries `replaced: true`. The replay store does NOT bind to keys, so an in-flight receipt under the old key fails at the pinning gate immediately after registry update. Operator must coordinate with the peer. |
| CRO-6 | Mode-mismatch protection. | Unknown values for `SARATHI_PEER_KEY_PINNING` panic at boot. No "default to relaxed on parse error". |
| CRO-7 | Backwards compatibility. | `relaxed` is default, so existing TOFU deployments keep working with a stderr warning per receipt. Operator can pin at their own pace. Strict mode is explicit opt-in. |

---

## 4. CSO findings + resolutions

| # | Finding | Resolution |
|---|---|---|
| CSO-1 | TOFU model accepts attacker-substituted keys. | Pinning gate (G4) compares against the registry-stored key in constant time. Mismatch rejects regardless of mode. |
| CSO-2 | Cross-peer impersonation (use peer X's key to forge peer Y receipts). | The registry is keyed by peer NAME. Looking up "bucket" returns bucket's pinned key, not insightflow's. A receipt with `peer: "bucket"` signed by the insightflow key fails at G4. Verified by `TestPeerKeyRegistry_CrossPeerImpersonation_Rejects`. |
| CSO-3 | Unknown peer-kind injection. | G1 rejects any `peer` value outside {bucket, core, insightflow}. Verified by `TestPeerKeyRegistry_UnknownPeerKind_Rejects`. |
| CSO-4 | Timing-attack key comparison. | `constantTimeHexEqual` lowercases, length-checks, decodes both sides, then `subtle.ConstantTimeCompare`. Malformed hex compares-false without leaking length. |
| CSO-5 | Status lifecycle (SUSPENDED / REVOKED). | G3 requires `status == ACTIVE`. SUSPENDED / REVOKED reject even with a matching key. Verified by `TestPeerKeyRegistry_SuspendedPeer_Rejects`. |
| CSO-6 | Receipt replay (captured-once recycled). | New `peer_receipt_replay.go` rejects sha256-identical receipt within 300 s, keyed per peer. Verified by `TestPeerReceiptReplay_DuplicateRejected`. |
| CSO-7 | Private-key exposure surface in CLI. | `--register-peer-key` accepts ONLY `--public-key`. The handler rejects oversized inputs; nothing in the path could accidentally accept a private key. |
| CSO-8 | Snapshot file permissions. | The snapshot is mode 0644 (operator-readable but not world-writable). Hardening note: on multi-tenant hosts the operator should run `chmod 0640` and assign group ownership to the Sarathi service user. Documented in KB_18. |
| CSO-9 | Boot-time integrity. | Malformed peer_keys rows are dropped with a stderr WARN, not silently accepted. Bad shape never reaches the active registry. |
| CSO-10 | Audit replay attack (an attacker forging audit rows). | Audit JSONL is append-only; tamper-resistance is at the filesystem layer (Sarathi does not sign individual rows). The TANTRA enforcement attestation chain remains the cryptographic anchor for cross-system audit. |

---

## 5. Test matrix — all passing

```
PASS  TestPeerKeyRegistry_RelaxedMode_NoEntry_AcceptsTOFU
PASS  TestPeerKeyRegistry_StrictMode_NoEntry_Rejects
PASS  TestPeerKeyRegistry_RegisteredAndMatching_Accepts
PASS  TestPeerKeyRegistry_RegisteredButMismatchedKey_Rejects
PASS  TestPeerKeyRegistry_SuspendedPeer_Rejects
PASS  TestPeerKeyRegistry_CrossPeerImpersonation_Rejects
PASS  TestPeerKeyRegistry_UnknownPeerKind_Rejects
PASS  TestPeerReceiptReplay_DuplicateRejected
PASS  TestPeerKeyRegistry_ConstantTimeHexEqual
PASS  TestPeerKeyRegistry_ValidatePeerKeyEntryShape
```

Plus full repo suite green (`go test ./... -count=1` → `ok 4.5s`).

Smoke against the built binary:

```
$ ./sarathi-enforcement-adapter --register-peer-key --peer=bucket --public-key=<hex> --snapshot=...
Successfully registered peer key for peer=bucket
  status:           ACTIVE
  public_key_hex:   <hex>
  key_fingerprint:  <first-16>
  snapshot:         <path>
```

Atomic snapshot write verified — file present after CLI exit, valid JSON, version field present.

---

## 6. Files this phase produces

New:
- `peer_key_registry.go`
- `peer_receipt_replay.go`
- `cmd_peer_key_register.go`
- `peer_key_registry_test.go`
- `review_packets/phase_v15_9_peer_key_registry.md` (this file)

Modified:
- `peer_common.go` — VerifyReceipt now calls the two new gates.
- `evaluator_admin_cli.go` — `--register-peer-key` dispatch.
- `enforcement_adapter_main.go` — boot wiring.
- `KB_17_TANTRA_DECISION_V1.md` — §14b added explaining the registry.
- `SARATHI_SYSTEM_GUIDE.md` — Part XII.5 corrected (TOFU disclosure + v15.9 description).

Audit log paths:
- `proof_logs/peer_key_registry_audit.jsonl` — registration events.

---

## 7. Operator runbook (production)

1. Pre-boot: ask each peer team (Bucket / InsightFlow / Core) to generate an Ed25519 keypair on THEIR side; receive their PUBLIC key out-of-band.
2. Register each peer:
   ```
   ./sarathi-enforcement-adapter --register-peer-key --peer=bucket      --public-key=<hex-from-Siddhesh>
   ./sarathi-enforcement-adapter --register-peer-key --peer=insightflow --public-key=<hex-from-Vijay>
   ./sarathi-enforcement-adapter --register-peer-key --peer=core        --public-key=<hex-from-Raj>
   ```
3. Set `SARATHI_PEER_KEY_PINNING=strict` in `live/.env`.
4. Start the service. Boot banner will show "loaded 3/3 peer key(s) (mode=strict)".
5. Any receipt from an unregistered peer or with a mismatched key now rejects at the boundary with `ERR_DOWNSTREAM_RECEIPT_INVALID` + reason in the audit log.

To rotate:
1. Coordinate with the peer team on rotation timing.
2. Re-run `--register-peer-key --peer=bucket --public-key=<new-hex>`.
3. Peer team flips to the new private key in lockstep.

---

**Phase v15.9 sign-off:** TOFU gap closed. Pinning + replay rejection live. Documentation accurate. No regressions in the v15.7 / v15.8 surfaces.
