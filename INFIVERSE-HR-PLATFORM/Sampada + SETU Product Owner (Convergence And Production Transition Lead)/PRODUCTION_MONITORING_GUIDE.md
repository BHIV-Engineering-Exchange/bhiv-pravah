# Production Monitoring Guide — BHIV Phase IV

**Date:** 2026-07-13  
**Audience:** Operators accepting Sampada + SETU into production

---

## Gateway health

| Check | Endpoint | Expected |
|---|---|---|
| Liveness | `GET /health` | HTTP 200 |
| Detailed health | `GET /health/detailed` | CPU/RAM/DB status |
| Metrics dashboard | `GET /metrics/dashboard` | `performance_summary`, `system_metrics`, `business_metrics` |

Control Center executive zone consumes these via `fetchGatewayMetricsDashboard()` and `checkApiHealth()`.

---

## Workforce / governance

| Check | Endpoint |
|---|---|
| Org listing | `GET /v1/workforce/organizations` |
| Policy definitions | `GET /v1/policies/definitions` |
| Governance challenges | `GET /v1/governance/challenges` |
| Decision ledger | `GET /v1/decisions` |

---

## SETU participation

| Check | Endpoint |
|---|---|
| Ingest (partners) | `POST /v1/setu/signals/{signal_type}` |
| List signals | `GET /v1/setu/signals?signal_type=&correlation_id=` |
| Trace continuity | `GET /v1/setu/trace/{trace_id}` |

**Auth:** Bearer `API_KEY_SECRET` for partner dispatchers.

---

## Control Center observability

| Check | Endpoint |
|---|---|
| Dashboard aggregates | `GET /v1/control-center/dashboard-aggregates` |
| Audit events | `GET /v1/control-center/audit-events` |
| Audit replay | `GET /v1/control-center/audit-replay` |

---

## Render deployment

- Production gateway: `https://bhiv-hr-gateway-l0xp.onrender.com`  
- Monitor Render dashboard for instance health, deploy logs, and Mongo connection errors

---

## Evidence harnesses (regression)

```bash
# Offline governance suite (32 tests)
cd backend
python -m pytest tests/gateway/test_workforce_governance_runtime.py \
  tests/gateway/test_live_workforce_governance_setu_gapfix.py \
  tests/gateway/test_control_center_governance.py \
  tests/gateway/test_tenant_isolation_workforce.py \
  tests/gateway/test_workforce_lifecycle.py \
  tests/e2e/control_center/test_control_center_offline.py -q

# Phase IV production validation
python evidence/phase_iv_production_validation/harness/run_production_validation.py

# Phase IV Tier 1 capture (requires backend/.env API_KEY_SECRET)
python evidence/phase_iv_tier1/harness/run_tier1_capture.py
```

---

## Alerting guidance

Use `AlertCard` thresholds in Control Center (CPU/memory/disk ≥ 80%, error rate > 5%) as **visibility cues** — configure external alerting on the same gateway metrics for production paging.

---

## Out of scope

Centralized APM / log aggregation — **TMS** to provision.
