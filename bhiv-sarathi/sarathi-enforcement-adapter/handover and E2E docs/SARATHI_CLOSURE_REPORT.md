# Sarathi — Closure Report

**Purpose:** operational closure per task.md — convert Sarathi from a completed
build into a transferable, testable, reconstructable asset. The test of done is
not feature count; it is **continuity**: a new developer can deploy, run, test,
understand, and continue Sarathi without the original builder.

---

## 1. Achievements

- **Enforcement core complete and stable.** Single Go binary (module
  `sarathi-enforcement-adapter`, Go 1.25.0); `go build` and `go vet` both clean.
  Every request transits a gated bridge that makes bypass structurally
  impossible; the pipeline fails closed on verification mismatch.
- **Cryptographic integrity.** Ed25519 enforcement signing with an ML-DSA-65
  hybrid toggle (crypto-agility). Dual-hash model (transport `body_hash` +
  decision `response_hash`) minted before send and verified on return. Private
  keys never cross the wire.
- **Bucket integration verified live.** Full custody flow proven end-to-end:
  `POST /bucket/artifact` → 200, read-back `chain_verified: true`, chain head
  advances, Sarathi-signed custody receipt. Adapted to two undocumented live
  Bucket rules (trace_id in payload; genesis omits parent_hash).
- **Trust + peer-key registry.** Pinned per-peer Ed25519 keys with cross-peer
  impersonation defence; receipt verification gated on the registered key.
- **Audit + observability.** Immutable JSONL trails for decisions, transmissions,
  and receipts; health, deep-health, and Prometheus metrics surfaces.
- **Handover package delivered.** `SETUP_GUIDE.md`, `BUILD_STATE.md`,
  `SYSTEM_OVERVIEW.md`, `ARCHITECTURE_FLOW.md`, `REPO_MAP.md`, `FAQ.md`,
  `PENDING_WORK.md`, this report, and the existing `REVIEW_PACKET.md`.

---

## 2. Known gaps

| Gap | Nature | Owner |
|---|---|---|
| InsightFlow live propagation | Their deployed server returns 500 on all POST endpoints (server-side). Sarathi side correct. | InsightFlow team |
| Bridge inbound JWKS | Bridge needs a reachable Sarathi JWKS URL; 401 diagnosed, not closed. | Joint |
| Core live E2E | Endpoints wired; one live confirmation pending. | Joint |
| Propagation enablement | OFF by default; must be enabled via env in the target environment. | Operator |
| Cloud listener binding | Must set `SARATHI_SERVICE_ADDR=0.0.0.0:<port>` on a cloud host. | Operator |
| Bucket doc vs deployment | Their doc omits two rules the live server enforces. Sarathi already adapted. | Bucket team |

Full detail and "definition of done" in `PENDING_WORK.md`.

---

## 3. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| A peer deployment drifts from its published contract (as Bucket did) | Medium | Always treat the live `schema-info`/contract endpoint as authoritative; Sarathi verifies via read-back, not assumptions. |
| Peer using ephemeral storage loses chain continuity across restarts | Medium | Confirm persistent storage with the peer; Sarathi's audit trail is independent and durable locally. |
| Running production without the boot gates | High | `SARATHI_ENV=production` enforces inbound auth, non-default keys, and a trust snapshot; do not bypass. |
| Propagation enabled with placeholder URLs | Low | Fan-out fails loud on placeholder URLs and logs to the audit trail. |
| Enforcement key missing in deployment | Medium | Receipts go unsigned and surface a warning; set `SARATHI_ENFORCEMENT_PRIV_PATH`. |

---

## 4. Recommendations for the next owner

1. **Stand it up first.** Build, run `--service`, confirm `/health`. Then read
   `BUILD_STATE.md` and `ARCHITECTURE_FLOW.md`.
2. **Unblock InsightFlow at the source.** It is not a Sarathi problem — get their
   Render logs and the server-side traceback.
3. **Close the Bridge JWKS loop** to enable authenticated inbound decisions.
4. **Enable propagation deliberately** (env flag + URLs) and watch
   `proof_logs/peer_propagation_audit.jsonl`.
5. **Keep the enforcement core untouched** unless a contract changes; extend at
   the translation/peer layer, where peer-specific shapes already live.
6. **Trust live contract endpoints over docs** when integrating any peer.

---

## 5. Transfer readiness

| Dimension | State |
|---|---|
| Build reproducible | ✅ `go build` clean from a fresh clone |
| Runs without the original builder | ✅ `SETUP_GUIDE.md` is self-contained |
| Understandable | ✅ Overview + flow + repo map provided |
| Testable | ✅ Bucket runbook + scripts; InsightFlow script (blocked on their server) |
| Open items documented | ✅ `PENDING_WORK.md` with owners + done-criteria |
| Deployment documented | ✅ Cloud binding + env vars in `SETUP_GUIDE.md` |

**Assessment:** Sarathi is **transfer-ready**. The enforcement asset is complete,
documented, and reconstructable. Remaining work is integration closure with peers
that are external to Sarathi (and not yet healthy on their side), plus
environment configuration — all documented with owners. A new developer can
take ownership from these documents alone.

---

## 6. Proof captured (Phases 3–4)

Evidence is captured under `validation screenshots/`:

**Phase 3 — Deployment validation (✅ captured)**
- `deployment validation- build.png` — `go build` + `go vet`, both clean.
- `sarathi service .png` — service boots with full banner and route list.
- `Sarathi health check.png` — `/health` → `status: healthy, service_status:
  READY, bridge_active: True`.
- `sarathi deep healt check.png` — `/health/deep` → healthy with bridge/router/
  service checks.

**Phase 4 — End-to-end traces (✅ captured: 5 traces + failure case)**
- `bucket trace -1.png` … `bucket trace-5.png` — five complete custody traces,
  each: input (sealed decision) → processing (mint/seal) → output (Bucket
  `success:true`) → logging (chain head advance) → observability (read-back
  `chain_verified: true`).
- `bucket-artifact-1.png` … `-5.png` — chain head advancing `artifact_count`
  0 → 5.
- `bucket failure test-duplicate .png` — failure handling: a stale `parent_hash`
  is rejected with HTTP 400 (`Invalid parent_hash. Expected… Got…`), proving
  fail-closed chain integrity.

**Honest scope note.** These five traces exercise the **live Bucket custody +
chain-integrity path end-to-end against the real peer** — the strongest external
proof available today. They are not driven through the internal service ingest
endpoint (`/v1/ingest-decision`) with full peer fan-out, because that path
additionally requires Bridge inbound auth and a healthy InsightFlow — both
external blockers documented in `PENDING_WORK.md` (P1, P2). The five traces
nonetheless cover every stage task.md requires (input → processing → output →
logging → observability → failure handling).
