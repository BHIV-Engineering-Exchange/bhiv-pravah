# BHIV Phase IV — Complete Tier 1 Runtime Evidence

**Date:** 2026-07-13  
**Phase:** BHIV Phase IV — Production Transition  
**Owner / acceptance authority:** Rishabh Yadav  
**Evidence run:** `evidence/phase_iv_tier1/20260713T035150Z/`

> Operational boundary: Sampada is a visibility and intelligence surface; execution authority stays with owning systems. Observability ≠ Authority; Replay ≠ Execution; Dashboard ≠ Governance.

---

## Environment

| Target | Detail |
|---|---|
| Live gateway | `https://bhiv-hr-gateway-l0xp.onrender.com` |
| Local gateway | In-process FastAPI harness over `mongomock_motor` (real route layer, ephemeral store) |
| Shared correlation id | `c530d0b7-eb17-4fb8-bc78-e81a500042fd` |
| Harness | `evidence/phase_iv_tier1/harness/run_tier1_capture.py` |
| Environment checkpoint | `evidence/phase_iv_tier1/environment_checkpoint.json` |

---

## Tier table (honest assessment)

| System | Tier | Sampada signal_id | trace_id | Blocker / notes |
|---|---|---|---|---|
| **Sampada** (own runtime) | **Tier 1** | `sig-502f26a49b89` (local in-process) | `local-trace-c530d0b7` | 32/32 offline tests pass; live Render ingest confirmed for partners below |
| **Artha** | **Tier 2** | `sig-66c8d789c660` | `TRC-20260702-19f21bf0` | Dispatcher invoked directly; server boot failed (`MODULE_NOT_FOUND` on `node start.js`) |
| **CRM** | **Tier 2** | `sig-5f80c230999c` | `crm-trace-c530d0b7` | `sampada_dispatcher.py` invoked directly; CRM FastAPI server not booted |
| **Logistics** | **Tier 2** | `sig-8ae9c683f2ef` | `logistics-trace-c530d0b7` | Routed via CRM dispatcher with `subsystem: logistics`; no independent backend |
| **Niyantran** | **Not Yet Available** | — | — | Boot failed (`MODULE_NOT_FOUND` in `index.js`); Mongo dispatch script exit non-zero |
| **Bucket** | **Not evidenced** | — | — | No Sampada/SETU dispatcher in repo — route GC/MDU |
| **PRANA** | **Not evidenced** | — | — | Posts to Bucket only |
| **InsightFlow** | **Not evidenced** | — | — | No Sampada dispatcher |
| **Karma** | **Not evidenced** | — | — | Forwards to InsightFlow via `stp_bridge.py` |

---

## Boot probe results

Captured in `evidence/phase_iv_tier1/20260713T035150Z/boot_probes.json`:

- **Niyantran:** `workflow-blackhole/server` — process exited code 1 within 8s (`MODULE_NOT_FOUND` in require stack)
- **Artha:** `Artha/backend` — process exited code 1 (`MODULE_NOT_FOUND`)

**Conclusion:** Tier 1 (native server → business workflow → dispatcher → Sampada) was **not achieved** for any partner in this environment. Tier 2 live HTTP dispatches succeeded for Artha, CRM, and Logistics where credentials and Mongo were available.

---

## Trace continuity

- Local in-process: `POST /v1/setu/signals/setu_aggregation` → HTTP 200 with lineage envelope `schema_version: 1.0.0`
- Live Render: partner dispatches returned HTTP 200 with `signal_id` in response body (see `capture_index_tier1.json`)

---

## Open owner decisions (unchanged from prior sprint)

1. **Logistics signal_type:** separate type in `SIGNAL_TYPES` vs `crm_participation` + `subsystem` marker → **GC / MDU**
2. **Tier 1 acceptability:** shared test environment with bootable partner servers + `npm ci` in partner repos → **Rishabh / partner owners**

---

## Raw capture index

| File | Description |
|---|---|
| `capture_index_tier1.json` | Master index with per-partner dispatch + confirm |
| `boot_probes.json` | Server boot attempt results |
| `SUMMARY.md` | Human summary for this run |
| `evidence/phase_iv_tier1/latest_run.json` | Pointer to latest run |

**Sampada SETU contract:** unchanged (`backend/services/gateway/app/setu_participation.py`).
