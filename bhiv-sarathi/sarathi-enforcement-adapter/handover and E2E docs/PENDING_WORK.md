# Sarathi — Pending Work

Open items for the next owner, in priority order. Each lists what is done, what
remains, and who owns the blocker. None require changes to the enforcement core.

---

## P1 — InsightFlow live propagation (blocked on InsightFlow)

- **Status:** Sarathi side complete and correct. The deployed InsightFlow server
  (`bhiv-6.onrender.com`) returns `500 Internal Server Error` on ALL POST
  endpoints (`/sarathi_trigger`, `/core_execute`, `/bucket_persist`,
  `/insightflow_process`) while `GET /docs` returns 200.
- **Diagnosis:** systemic server-side failure on their end (every endpoint
  crashes identically; a payload problem would be 422, not 500). Body is generic
  "Internal Server Error" — traceback only in their Render logs.
- **Remaining:** InsightFlow team must read their Render logs and fix the handler
  pipeline / deployment config. Then re-run `.\scripts\test_insightflow.ps1`.
- **Owner:** InsightFlow team. **Sarathi action:** none.

---

## P2 — Bridge inbound token / JWKS

- **Status:** Inbound auth and JWT capability verification implemented. A 401 was
  diagnosed: the Bridge must fetch Sarathi's JWKS from a reachable URL.
- **Remaining:** publish Sarathi's JWKS at a URL the Bridge can reach, register
  the key id, and confirm one authenticated inbound decision end-to-end.
- **Owner:** joint (Sarathi exposes JWKS URL; Bridge fetches).

---

## P3 — Core live end-to-end

- **Status:** Core endpoints wired via `SARATHI_CORE_*_URL`. Post-execution record
  path implemented.
- **Remaining:** one live end-to-end run against Core with the propagation flag on,
  confirming the post-exec record and any receipt.
- **Owner:** joint (needs a reachable Core URL).

---

## P4 — Enable propagation in the target environment

- **Status:** Fan-out is implemented and OFF by default.
- **Remaining:** in the deployment environment set
  `SARATHI_PROPAGATE_ON_INGEST=1` plus peer URLs + `SARATHI_INSIGHT_API_KEY`, then
  confirm rows appear in `proof_logs/peer_propagation_audit.jsonl`.
- **Owner:** operator. See `SETUP_GUIDE.md` §5.4.

---

## P5 — Cloud listener binding

- **Status:** Listener is env-driven (`SARATHI_SERVICE_ADDR`).
- **Remaining:** on any cloud host set `SARATHI_SERVICE_ADDR=0.0.0.0:<port>` so the
  platform health check and external traffic reach it. No code change needed.
- **Owner:** operator.

---

## P6 — Peer deployment discrepancies to confirm with Bucket

- **Status:** Sarathi adapted to the live Bucket; integration verified working.
- **Remaining (Bucket team):** reconcile their canonical doc with the deployment
  on two points the live server enforces but the doc omits:
  1. `trace_id` is not an allowed top-level field (must be inside `payload`).
  2. The genesis artifact must omit `parent_hash` entirely.
  Also confirm whether the deployment uses persistent storage (the observed
  deployment reset its chain across restarts).
- **Owner:** Bucket team (doc reconciliation). Sarathi already adapted.

---

## Technical debt (non-blocking)

- Two Bucket-posting code paths (`bucket_bhiv_adapter.go` test/proof path and
  `translation_bucket_artifact.go` fan-out path); consider unifying.
- `DefaultEndpoints()` uses fail-loud placeholders; operators must set env vars.
- Test harnesses write regenerable `*_report.json` / `*_results.json` to the repo
  root; safe to clean periodically.

---

## Definition of done for full closure

1. InsightFlow 500s resolved and `test_insightflow.ps1` passes (P1).
2. One authenticated inbound decision via the Bridge (P2).
3. One live Core post-exec record (P3).
4. Propagation enabled in the deployment with audit rows present (P4, P5).
5. Bucket doc reconciled (P6) — optional, integration already works.
