# Observability Certification — BHIV Phase IV

**Date:** 2026-07-13

---

## Certified surfaces

| Surface | Mechanism | Evidence |
|---|---|---|
| Audit ledger | `audit_logs` collection + `write_workforce_audit()` | Governance replay tests |
| SETU signal store | `setu_signals` + list/filter endpoints | Live partner captures 2026-07-13 |
| Trace continuity | `setu_trace_continuity()` joins signals + audits on `trace_id` | `setu_participation.py` |
| Control Center aggregates | `compute_dashboard_aggregates()`, `list_audit_events()` | `test_control_center_governance.py` |
| Gateway health | `/health`, `/metrics/dashboard` | Control Center executive zone |
| Correlation propagation | `X-Correlation-ID` middleware in harnesses | Phase IV captures |

---

## Telemetry cards (UI)

`TelemetryCard` primitive surfaces service health (Gateway, Agent, LangGraph) with endpoint attribution — read-only.

---

## Not certified (out of scope)

- Centralized log aggregation (ELK/Datadog) — **UNKNOWN / TMS**
- Cross-repo unified trace UI for Bucket/InsightFlow — no Sampada dispatcher

---

## Constitutional compliance

All observability surfaces include disclaimers: visibility does not confer execution authority.
