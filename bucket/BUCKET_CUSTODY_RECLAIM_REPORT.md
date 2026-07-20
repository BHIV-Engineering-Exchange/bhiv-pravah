# BUCKET_CUSTODY_RECLAIM_REPORT

Date: 2026-05-20
Author: Automated custody reclaim run

Purpose
-------
This report captures the immediate custody reclaim snapshot for the BHIV `bucket` repository. It documents repository state, running state (local vs deployed), environment inventory (redacted), artifact storage snapshot, discrepancies, and recommended immediate actions so Soham can hand custody back cleanly.

Summary (top-level)
-------------------
- Backup branch created locally (custody backup created).
- Active local branch: `contract-api` (latest local commit: `e3c34f5` — "Merge origin/contract-api — resolve conflicts (accept remote for admin-panel files)").
- `.env.example` is staged/modified locally (contains production connection strings). Values have been redacted in this report.
- Local service: no HTTP health response on `http://localhost:8005` (local server not running).
- Deployed service (Render/ngrok): reachable and healthy at https://bhiv-bucket.onrender.com — `/health` reports `status: healthy`.
- Artifact storage on this machine (local repo `data/artifacts`) contains 3 artifacts; deployed service reports 0 artifacts. There is a divergence to investigate.

Actions performed
-----------------
1. Created a local backup branch prior to any changes (custody backup).
2. Captured current Git state (branch, HEAD commit id/message).
3. Read and redacted `.env.example` to inventory external services referenced.
4. Read local append-only storage files in `data/artifacts`:
   - `artifact_log.jsonl` (3 entries)
   - `artifact_index.json` (3 index entries)
   - `chain_state.json` (artifact_count: 3, last_hash present)
5. Probed health endpoints:
   - Local: `http://localhost:8005/health` — connection refused (local server not running).
   - Deployed: `https://bhiv-bucket.onrender.com/health` — returned healthy JSON (append-only active).
6. Probed deployed `/bucket/latest-hash` — returned `{"last_hash":null,"artifact_count":0}`.

Repository state
----------------
- Current branch: `contract-api`
- HEAD: `e3c34f54d55f80ec7e255b892145e15430058983` — Merge commit created during merge conflict resolution.
- Staged changes (local): `.env.example` (sensitive values present)
- Notable recent collaborator commit merged: `a787c6a` — "chore: prepare code for Render deployment" (modified `main.py`, `admin-panel` files, added `README.md`).

Environment & secrets inventory (redacted)
-----------------------------------------
- `.env.example` contains keys for the following external services (values redacted in this report):
  - `MONGODB_URI` (present, points to a cloud MongoDB instance)
  - `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_USERNAME` (present, remote Redis cluster referenced)
  - `FASTAPI_PORT` (present)

Note: `.env.example` contains live-looking connection strings. Do not commit production secrets in plaintext in VCS; rotate credentials if these are live.

Local append-only storage snapshot
---------------------------------
- `data/artifacts/chain_state.json`:
  - `last_hash`: `642a0cee554bb172a8b3f8f83c4c49f10b1908290c98d92e04ba32c6aee23e97`
  - `artifact_count`: 3
- `data/artifacts/artifact_index.json` entries (artifact_id → byte offset):
  - `test_artifact_001`
  - `83f04c2a-78a9-490e-a61d-aee500b65bd8`
  - `4ac417c4-38a7-4e25-8ecf-2ec963c8b588`
- `data/artifacts/artifact_log.jsonl` (chronological log) — 3 artifacts recorded. Example summaries:
  1. `test_artifact_001` — `trace_id`: `trace-123` — timestamp `2026-05-06T12:00:00Z`
  2. `83f04c2a-78a9-490e-a61d-aee500b65bd8` — `trace_id`: `ce377202-476a-4a5b-9c40-5f0135c95bcb` — perception artifact with `parent_hash` linking to `test_artifact_001`
  3. `4ac417c4-38a7-4e25-8ecf-2ec963c8b588` — `trace_id`: `e456c3e9-e61a-4e87-ae8e-c7c312255c31` — perception artifact chained to previous

Deployed service snapshot (Render / public)
-----------------------------------------
- Base URL probed: `https://bhiv-bucket.onrender.com`
- `/docs`: OpenAPI docs are available.
- `/health`: reports `status: healthy`, `append_only_storage.status: active`, but `append_only_storage.artifact_count: 0` and `last_hash: null`.
- `/bucket/latest-hash`: returns `{"last_hash":null,"artifact_count":0}`.

Discrepancy / Risk
------------------
- Divergence: local artifact store has 3 artifacts (head hash present) but deployed service reports 0 artifacts. Possible explanations:
  1. Local artifacts were created locally and not pushed to the deployed backend (expected if deployment uses a separate persistent storage).
  2. Deployed backend uses a different persistent data store (e.g., cloud storage, different DB) and has no records.
  3. There is replication delay or a separate environment configured for Render (i.e., different `MONGODB_URI` / storage path).

- Secrets exposure: `.env.example` contains apparent live credentials. This is an operational risk if those values are used in CI or committed. Rotate if these are live credentials.

Immediate recommended actions
-----------------------------
1. Do NOT perform destructive writes to the deployed service without coordination (SVACS / Testing team). We must avoid polluting production data.
2. Confirm where the deployed instance persists artifact data (Mongo, file store, S3, etc.). Check `main.py` config or Render environment variables for `MONGODB_URI` / storage path.
3. If you want parity between local and deployed artifact stores for testing, choose one of:
   - Import local `artifact_log.jsonl` into deployed storage (only with approvals and migration plan), or
   - Run a test flow against deployed service and validate full chain lifecycle there.
4. Rotate any credentials leaked into ` .env.example` if they are real production secrets.
5. Start local server (if you intend to run local validation): `python main.py` (ensure `.env` points to appropriate test DB), then re-run health and chain checks locally.

Next steps I will take if you approve
-------------------------------------
1. Create `BUCKET_CUSTODY_RECLAIM_REPORT.md` (this file) in repo (done).
2. Optionally collect and export the raw artifact log and index into an artifacts snapshot folder (redacted) for handoff.
3. Proceed with Phase 2 (contract guide) or run an isolated trace continuity verification per your instruction.

Files referenced / created during audit
-------------------------------------
- `.env.example` (redacted in the report; contains `MONGODB_URI` and Redis config)
- `data/artifacts/artifact_log.jsonl` (read)
- `data/artifacts/artifact_index.json` (read)
- `data/artifacts/chain_state.json` (read)

Sign-off
--------
This custody snapshot was generated automatically from the working copy on 2026-05-20. If you want me to proceed to Phase 2 or run specific validation flows (trace continuity or replay checks), instruct me which step to run next.
