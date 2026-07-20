# Ecosystem Repository Map — Sampada + SETU (BHIV Phase IV)

**Purpose:** Canonical mapping of every repository/folder involved in the task
*"Sampada + SETU Product Owner (Convergence And Production Transition Lead)"*.
Read this first before any integration, convergence, or evidence work — humans and AI agents alike.

**Owner / acceptance authority:** Rishabh Yadav
**Last updated:** 2026-07-11

---

## 1. Primary Repository (committed)


| Repository                          | System      | Notes                                                                                                                                                                                                     |
| ----------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `INFIVERSE-HR-PLATFORM` (this repo) | **Sampada** | HR / Workforce Intelligence platform. The SETU ingestion layer lives **inside this repo** (`backend/services/gateway/app/setu_participation.py`, routes `/v1/setu/`*). SETU is not a separate repository. |


---



## 2. Integration & Partner / External Repositories (local folders, gitignored)

These folders sit alongside the primary repo in the workspace root. They are listed in `.gitignore` and must **never be committed** into Sampada git history. Only Sampada-side integration code is committed.


| Local folder         | System(s)                             | Role                                                                                                                                         |
| -------------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `workflow-blackhole` | **Niyantran** (= Complete-Infiverse)  | Tasking, reviews, execution telemetry. "**Workflow Executor**" is the title of the work done in this repo — it is NOT a separate repository. |
| `Artha` / `AI-Artha` | **Artha**                             | Payroll truth, financial systems, payments.                                                                                                  |
| `ai-crm`             | **CRM + Logistics + SETU** (together) | Relationship intelligence, Logistics (frontend, no separate backend), and the SETU module. These three live together in this one repo.       |
| `bucket`             | **Bucket**                            | Storage / artifact / append-only persistence; replay-chain participation.                                                                    |
| `Prana`              | **PRANA**                             | Signal / packet participation (bucket bridge, packet builder, state engine).                                                                 |
| `bhiv-registry`      | **InsightFlow**                       | Analytics / registry system.                                                                                                                 |
| `Karma-Tracker`      | **Karma**                             | Karma tracking / participation system.                                                                                                       |


---



## 3. Not Separate Repositories (common confusions)


| Name                   | What it actually is                                                                                           |
| ---------------------- | ------------------------------------------------------------------------------------------------------------- |
| **SETU**               | Module inside Sampada gateway (ingestion) + SETU module inside `ai-crm`. Not a standalone repo.               |
| **Complete-Infiverse** | Same repo as `workflow-blackhole` (Niyantran). Not a second folder.                                           |
| **Workflow Executor**  | Title/capability of Niyantran (`workflow-blackhole`). Not a repo.                                             |
| **Logistics**          | Lives inside `ai-crm` (frontend only). No separate backend repo.                                              |
| **TANTRA**             | The **whole BHIV ecosystem** — the constitutional execution flow across all systems. Not a single repository. |


---



## 4. Pending / Not Yet Available

_None at this time — all known partner repos are listed in Section 2._

---



## 5. Ecosystem Picture

```
TANTRA (whole ecosystem — not a repo)
  ├── Sampada                     → INFIVERSE-HR-PLATFORM (primary, committed)
  ├── Niyantran / Workflow Executor / Complete-Infiverse
  │                               → workflow-blackhole
  ├── Artha                       → Artha / AI-Artha
  ├── CRM + Logistics + SETU      → ai-crm
  ├── Bucket                      → bucket
  ├── PRANA                       → Prana
  ├── InsightFlow                 → bhiv-registry
  └── Karma                       → Karma-Tracker
```

TANTRA constitutional execution flow:

```
Signal → Intelligence → Decision → Governance → Contract → Execution
       → Replay → Bucket → InsightFlow → Observability
```

---



## 6. Authority Routing (when ownership/governance/schema is unclear)


| Question                   | Route to |
| -------------------------- | -------- |
| Strategic placement        | **TMS**  |
| Governance / Authority     | **GC**   |
| Data / Schema / Provenance | **MDU**  |


Unknown remains UNKNOWN until clarified.

---



## 7. Rules for Agents and Developers

1. **Never commit** partner/external repo folders (`workflow-blackhole`, `Artha`, `ai-crm`, `bucket`, `Prana`, `bhiv-registry`, `Karma-Tracker`) into Sampada git history — they are gitignored on purpose.
2. **Never commit secrets** — partner `.env` files stay local.
3. Sampada is a **visibility and intelligence surface** — execution authority stays with the owning systems (Observability ≠ Authority; Replay ≠ Execution; Dashboard ≠ Governance).
4. Integration changes to partner repos must be **additive only**; the Sampada SETU contract (`/v1/setu/`* routes and schemas) is frozen unless the owner approves changes.
5. Cross-system calls must carry `correlation_id` / lineage envelope per `docs/SAMPADA_SETU_CONVERGENCE_MAP.md`.

---



## 8. Related Documents

- Task file: `Sampada + SETU Product Owner (Convergence And Production Transition Lead)/`
- Convergence map: `docs/SAMPADA_SETU_CONVERGENCE_MAP.md`
- Current state: `SAMPADA_CURRENT_STATE.md`
- Review packet: `REVIEW_PACKET.md`
- Partner runbook: `PARTNER_SETU_LIVE_RUNBOOK.md`
- Access & integration request: `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder)/ACCESS_AND_INTEGRATION_REQUEST.md`

---

## 9. Restoring Local Dependencies (safe to delete, reinstall anytime)

Partner `node_modules/` and Sampada `backend/venv/` are **not** in git. Deleting them frees disk space and does **not** affect `git pull`, commits, or deployed services.

| What you removed | Restore command |
|---|---|
| Sampada Python venv | `cd backend` → `python -m venv venv` → `.\venv\Scripts\activate` → `pip install -r requirements.txt` |
| Niyantran server (`workflow-blackhole`) | `cd workflow-blackhole\server` → `npm ci` *(or `npm install` if no lockfile)* |
| Artha backend | `cd Artha\backend` → `npm ci` |
| ai-crm Node backend | `cd ai-crm\backend-nodejs` → `npm ci` |
| Sampada frontend | `cd frontend` → `npm ci` |
| Bucket / partner Python extras | `backend\venv\Scripts\pip install -r bucket\requirements.txt` (+ `python-socketio`, `asyncpg`) |

**Important:** If you export `DATABASE_URL` or `MONGODB_URI` from Sampada `backend/.env` in your shell, partner services may inherit the wrong database. The startup script `scripts/start_all_ecosystem_services.ps1` clears these before launching partners. Run partners from their own folders or use that script.

**InsightFlow (bhiv-registry)** requires **PostgreSQL** on `localhost:5432` with database `bhiv_registry` (see `bhiv-registry/.env.example`). Copy to `bhiv-registry/backend/.env` and start Postgres before launching port 8020.

