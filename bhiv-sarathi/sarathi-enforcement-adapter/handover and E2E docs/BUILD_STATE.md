# Sarathi — Build State (Phase 1 Audit)

Honest snapshot of what exists, what works, what is incomplete, and known
limitations / technical debt. Written for a new owner deciding where it is safe
to build next.

---

## 1. At a glance

| Property | Value |
|---|---|
| Language / module | Go 1.25.0, module `sarathi-enforcement-adapter` |
| Source files | 135 `.go` source + 17 `_test.go` |
| Build | `go build -o sarathi-enforcement-adapter.exe .` — **clean** |
| Static analysis | `go vet ./...` — **clean** |
| External deps | Minimal (see `go.mod`; notably `github.com/google/uuid`) |
| Database | Not required for runtime (optional PostgreSQL integration is opt-in) |
| Runtime shape | Single self-contained binary; long-lived HTTP service or one-shot CLI modes |

---

## 2. What exists and works (verified)

| Capability | State | Evidence |
|---|---|---|
| Build + vet | ✅ Clean | `go build`, `go vet` both no-output |
| HTTP enforcement service | ✅ Works | `--service` boots, binds, serves routes, graceful shutdown |
| Enforcement pipeline (PEP) | ✅ Works | Every request routes through the gated bridge; decision verified + audited |
| Cryptographic verification | ✅ Works | Ed25519 default; ML-DSA-65 hybrid toggle (crypto-agility provider) |
| Signed custody receipts | ✅ Works | Sarathi signs receipts under its enforcement key |
| **Bucket integration** | ✅ **Verified live** | `POST /bucket/artifact` 200, read-back `chain_verified: true`, chain advances; see `BUCKET_TEST_COMMANDS.md` |
| Audit trail | ✅ Works | Append-only JSONL under `proof_logs/` and `live/` |
| Trust + peer-key registry | ✅ Works | Ed25519 pinned keys per peer; cross-peer impersonation defence |
| JWT capability authority | ✅ Works | Mint/verify capability tokens (CLI + handlers) |
| Test harnesses | ✅ Present | Adversarial attack, determinism, bypass-elimination, replay, multi-node |

---

## 3. What is incomplete / blocked (not a Sarathi defect)

| Item | State | Owner / blocker |
|---|---|---|
| **InsightFlow live propagation** | ⛔ Blocked | InsightFlow's deployed server returns `500` on **all** POST endpoints (server-side crash; their Render logs needed). Sarathi side is correct and ready. |
| **Bridge JWKS / inbound token** | ⚠️ Pending | Bridge must fetch Sarathi's JWKS from a reachable URL; 401 diagnosed, not yet closed end-to-end. |
| **Core live E2E** | ⚠️ Pending | Core endpoints are wired via env vars; live end-to-end confirmation outstanding. |
| Cloud reachability | ⚠️ Config | On a cloud host the listener must bind `0.0.0.0:<port>` via `SARATHI_SERVICE_ADDR` (see `SETUP_GUIDE.md`). |

---

## 4. Known limitations

- **Propagation is OFF by default.** Fan-out to peers requires
  `SARATHI_PROPAGATE_ON_INGEST=1` plus peer URLs + InsightFlow API key.
  Enforcement itself always runs.
- **Peer deployments may drift from their own contracts.** The deployed Bucket
  rejected `trace_id` top-level and rejected `parent_hash` on the genesis
  artifact, despite its canonical doc allowing both. Sarathi adapted on its side;
  the authoritative source is the live `GET /bucket/schema-info`, not the doc.
- **Peer durability.** The Bucket deployment observed on a free cloud tier reset
  its chain (`artifact_count` returned to 0) across restarts — ephemeral storage.
  Not a Sarathi issue, but integrators should not assume cross-restart continuity
  from that deployment.

---

## 5. Technical debt

| Item | Impact | Note |
|---|---|---|
| Two Bucket-posting code paths | Low | `bucket_bhiv_adapter.go` (the `--bucket-transmit` test/proof path) and `translation_bucket_artifact.go` (the production fan-out path) both build the envelope. Both were corrected for the `trace_id`-in-payload fix; consider unifying later. |
| `DefaultEndpoints()` placeholders | Low | Peer URLs default to fail-loud placeholders; operators must set env vars. Intentional, but a fresh dev must know to set them. |
| Generated report files | Cosmetic | Several test harnesses write `*_results.json` / `*_report.json` to the repo root. These are regenerable outputs, safe to delete. |

---

## 6. Bottom line

The core enforcement engine, cryptography, audit, and Bucket integration are
**working and verified**. The remaining work is **integration closure with peers
that are not yet healthy on their side** (InsightFlow) or **awaiting a reachable
URL** (Bridge/Core), plus the deployment env-var configuration documented in
`SETUP_GUIDE.md`. None of the open items require changes to Sarathi's
enforcement core.
