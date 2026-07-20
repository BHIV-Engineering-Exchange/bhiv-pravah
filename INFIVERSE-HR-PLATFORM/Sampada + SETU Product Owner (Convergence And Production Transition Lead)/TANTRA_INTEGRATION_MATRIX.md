# TANTRA Integration Matrix — BHIV Phase IV

**Date:** 2026-07-13  
**Scope:** All 8 systems from Implementation.md §1 inventory  
**SETU contract:** Frozen at `backend/services/gateway/app/setu_participation.py` — 4 `SIGNAL_TYPES` only unless owner approves extension

---

## Matrix

| System | Repo folder | TANTRA layer | SETU status | Signal type | Authority vs observability | Runtime dependency | Replay | Observability | Governance | Blocker / route-to |
|---|---|---|---|---|---|---|---|---|---|---|
| **Sampada** | `INFIVERSE-HR-PLATFORM` | Intelligence + visibility + SETU ingest | Tier 1 | `setu_aggregation` + ingest for 4 types | Visibility surface; not execution owner | MongoDB, gateway | `workforce_trace_replay`, `replay_decisions`, `setu_trace_continuity` | audit_logs, control-center reads | challenge/review/override visibility | — |
| **Niyantran** | `workflow-blackhole` | Execution / tasking | Tier 2 | `niyantran_telemetry` | Execution owner; Sampada observes telemetry | Mongo, execution emitter | ExecutionEvent chain on partner side | SETU dispatch post-persist | Participates in tasking | Tier 1 blocked: server `MODULE_NOT_FOUND` — partner owner |
| **Artha** | `Artha` | Financial / payroll truth | Tier 2 | `artha_payroll_visibility` | Payroll ownership; Sampada visibility-only | Mongo, setu.pipeline | decision ledger + provenance on Artha side | dispatch + ack | authority_runtime boundaries | Tier 1 blocked: server boot — partner owner |
| **CRM** | `ai-crm` | Relationship intelligence | Tier 2 | `crm_participation` | CRM owns relationships; Sampada aggregates | CRM backend + SETU module | trace_continuity in ai-crm/setu | sampada_dispatcher | Participates | Tier 1 blocked: CRM server not booted |
| **Logistics** | `ai-crm` (frontend) | Logistics ops (no backend) | Tier 2 | `crm_participation` + `subsystem: logistics` | Logistics owner external; rides CRM | CRM dispatcher | Same as CRM | Same as CRM | Participates | **GC:** independent `signal_type`? |
| **Bucket** | `bucket` | Replay-chain / artifact persistence | **Not Available** | **UNKNOWN** | Artifact governance owner | FastAPI, Mongo, Redis | Internal provenance | event_bus | artifact admission | **GC** authority; **MDU** schema for SETU extension |
| **PRANA** | `Prana` | Signal / packet (browser) | **Not Available** | **UNKNOWN** | Packet builder only | Bucket ingest endpoint | offline queue | localStorage queue | — | No Sampada path; **MDU** for contract |
| **InsightFlow** | `bhiv-registry` | Dataset / schema registry | **Not Available** | **UNKNOWN** | Registry owner | FastAPI | replay-compatibility fields | registry API | trust levels | **GC/MDU** for Sampada participation |
| **Karma** | `Karma-Tracker` | Karmic feedback | **Not Available** | **UNKNOWN** | Sovereign bridge (signals ≠ consequences) | FastAPI | sovereign_bridge | stp_bridge → InsightFlow | signal types enum | No Sampada path; routes to InsightFlow |

---

## TANTRA execution chain coverage

```
Signal → Intelligence → Decision → Governance → Contract → Execution → Replay → Bucket → InsightFlow → Observability
```

| Leg | Status |
|---|---|
| Partner → Sampada SETU (Niyantran, Artha, CRM, Logistics) | **Proven Tier 2** — live HTTP 2026-07-13 |
| Sampada lineage + trace | **Proven** — tests + harness |
| Execution → Bucket → InsightFlow → Sampada | **Not implemented** — adjacent wiring only (PRANA→Bucket, Karma→InsightFlow) |

---

## Constitutional rules (enforced)

- Observability ≠ Authority  
- Replay ≠ Execution  
- Dashboard ≠ Governance  
- Cross-system calls require `correlation_id` / `LineageEnvelope` per `docs/SAMPADA_SETU_CONVERGENCE_MAP.md`

---

## Evidence

- `TIER1_RUNTIME_EVIDENCE.md`  
- `evidence/phase_iv_tier1/20260713T035150Z/capture_index_tier1.json`  
- `docs/SAMPADA_SETU_CONVERGENCE_MAP.md`
