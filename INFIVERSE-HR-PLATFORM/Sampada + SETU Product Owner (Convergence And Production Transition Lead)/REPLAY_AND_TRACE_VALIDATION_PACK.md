# Replay & Trace Validation Pack — BHIV Phase IV

**Date:** 2026-07-13

---

## Workforce replay

**Path:** `GET /v1/workforce/trace-replay?correlation_id={cid}`  
**Module:** `workforce_runtime.workforce_trace_replay()`  
**Evidence:** `evidence/workforce_runtime/replay_trace_proof.md`; Live WO/GE/SETU Sprint 13-event lifecycle replay

---

## Decision replay

**Path:** `GET /v1/decisions/replay`  
**Modes:** `supersedes_chain`, `correlation_timeline`  
**Module:** `decision_ledger.replay_decisions()`  
**Evidence:** `evidence/live_workforce_governance_setu/governance_replay/phase3_scenarios.json`

---

## SETU trace continuity

**Path:** `GET /v1/setu/trace/{trace_id}`  
**Module:** `setu_participation.setu_trace_continuity()`  
**Evidence:** Prior sprint niyantran cross-system (1 signal + 14 audits); Phase IV local sample `sig-502f26a49b89`

---

## Control Center audit replay

**Path:** `GET /v1/control-center/audit-replay`  
**Module:** `control_center_governance.build_audit_replay()`  
**Evidence:** `evidence/live_workforce_governance_setu/control_center/phase7_control_center.json`

---

## Lineage envelope

All writers stamp `LineageEnvelope` with `schema_version: 1.0.0`, `correlation_id`, `trace_id` — mirrored by partner dispatchers (Implementation.md §4).

---

## Phase IV harness confirmation

- Local in-process SETU ingest + trace fields: `evidence/phase_iv_tier1/20260713T035150Z/capture_index_tier1.json`
- Production validation sustained loop (29 iterations / 30s): `evidence/phase_iv_production_validation/20260713T035319Z/long_duration_capture.json`

---

## Boundary

Replay reconstructs stored audit/signal order — **does not re-execute** business workflows.
