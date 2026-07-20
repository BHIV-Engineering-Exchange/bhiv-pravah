# Ownership Metadata & Lineage Propagation Evidence (Live WO/GE/SETU Sprint · Phase 6)

**Workflow position:** Step 6 of 11  
**Prerequisites:** Steps 1, 3, 5 (workforce, governance, SETU samples exist)  
**Next step:** Step 7 → `CONTROL_CENTER_EVIDENCE.md`

---

## Execution method

1. Extract lineage envelope from three subsystem samples (workforce employee, governance decision, SETU signal).
2. Verify all seven required fields present in each sample.
3. Follow one correlation id (`9fda459e-…`) across systems via `GET /v1/setu/trace/{trace_id}`.
4. Confirm: 1 SETU signal + 14 audit events share the lifecycle correlation id.
5. Confirm `schema_version=1.0.0` (Gap Fix #2 — already present in code).

---

## Capture metadata

**Date**: 2026-06-27
**Gateway base URL**: in-process FastAPI app mounting the real `routes/workforce_governance_routes.py` router
**Environment**: local in-process runtime over in-memory async Mongo (`mongomock_motor`) — real runtime code path; not deployed
**Auth type used**: API key (platform/admin)
**Status**: `live_capture` (local in-process runtime capture; reuses captures from Phases 1, 3, 5 — no re-run)
**Raw capture**: `evidence/live_workforce_governance_setu/lineage/phase6_lineage.json`

> Owner / acceptance authority: Rishabh Yadav. Builder surfaces evidence only.

---

## Scenario Narrative

This phase proves that the ownership/lineage envelope propagates across three different subsystems and that a single correlation id genuinely threads more than one system. Gap Fix #2 (`schema_version`) was **confirmed already present** in `app/lineage_envelope.py` (`schema_version: str = "1.0.0"`, emitted by `to_dict()`), and it appears in every captured envelope. Three cross-system samples (a workforce employee from Phase 1, a governance decision from Phase 3, a SETU signal from Phase 5) each carry all seven required fields. End-to-end propagation is demonstrated by following the lifecycle correlation id `9fda459e-1916-42f8-81d1-f9a6f7d7f7ec` from the workforce lifecycle into the audit ledger and into the linked niyantran SETU signal.

## Field-by-field presence (3 cross-system samples)

| Field | Workforce employee (Phase 1) | Governance decision (Phase 3, Leave) | SETU signal (Phase 5, niyantran) |
|---|---|---|---|
| origin_system | gateway | gateway | niyantran |
| owning_system | sampada | sampada | niyantran |
| schema_version | **1.0.0** | **1.0.0** | **1.0.0** |
| trace_id | 9fda459e-…-7f7ec | c8cd9063-…-83e83 | 9fda459e-…-7f7ec |
| correlation_id | 9fda459e-…-7f7ec | c8cd9063-…-83e83 | 9fda459e-…-7f7ec |
| trust_classification | canonical | canonical | observed |
| visibility_scope | tenant | tenant | tenant |

All seven required fields (`origin_system`, `owning_system`, `schema_version`, `trace_id`, `correlation_id`, `trust_classification`, `visibility_scope`) are present in all three samples. Note the meaningful difference in `origin_system`/`owning_system`/`trust_classification`: Sampada-authored objects are `gateway/sampada/canonical`, while an external-declared SETU signal is `niyantran/niyantran/observed` — ownership metadata is not flattened.

## End-to-end propagation (one correlation id across systems)

`GET /v1/setu/trace/9fda459e-1916-42f8-81d1-f9a6f7d7f7ec` (the Phase 1 lifecycle correlation id) returned:

- **signal_count = 1** — the niyantran SETU signal (`sig-a101a7ebdd58`), proving a SETU signal joined the workforce trace.
- **audit_count = 14** — the 13 workforce-lifecycle audit events (`organization_create` … `employee_offboard_prepare`) **plus** `setu_signal_niyantran_telemetry`, all carrying the same `correlation_id`.

This is presence **and** propagation: the same correlation/trace id is observable in the workforce object, in every workforce audit row, and in a cross-system SETU signal — not three unrelated objects that merely each contain a lineage block.

## Step / Evidence Table

| Item | Source call | Result | HTTP |
|---|---|---|---|
| schema_version confirmation | code (`app/lineage_envelope.py`) + every captured envelope | present, `1.0.0` | n/a |
| Workforce sample | Phase 1 `POST /v1/workforce/employees` | 7/7 fields | 200 |
| Governance sample | Phase 3 `POST /v1/decisions` (Leave) | 7/7 fields | 200 |
| SETU sample | Phase 5 `POST /v1/setu/signals/niyantran_telemetry` | 7/7 fields | 200 |
| Cross-system trace | `GET /v1/setu/trace/9fda459e…` | 1 signal + 14 audits, shared correlation_id | 200 |

## Known Limitations

- Local in-process runtime capture (see Phase 1 header).

## Cross-references

- Workforce lineage source: `LIVE_WORKFORCE_OPERATIONS_EVIDENCE.md`
- Governance lineage source: `GOVERNANCE_REPLAY_EVIDENCE.md`
- SETU lineage source: `SETU_PARTICIPATION_EVIDENCE.md`
- Raw: `evidence/live_workforce_governance_setu/lineage/phase6_lineage.json`
