# Replay / Trace Proof

## Workforce replay path

1. Create workforce entities through governance APIs:
   - `POST /v1/workforce/organizations`
   - `POST /v1/workforce/divisions`
   - `POST /v1/workforce/departments`
   - `POST /v1/workforce/employees`
2. Capture response/request `X-Correlation-ID`.
3. Query replay endpoint:
   - `GET /v1/workforce/trace-replay?correlation_id=<captured_cid>`
4. Validate returned event sequence includes workforce writes in order.

## SETU trace continuity path

1. Ingest SETU signals:
   - `POST /v1/setu/signals/niyantran_telemetry`
   - `POST /v1/setu/signals/artha_payroll_visibility`
2. Use shared `trace_id` and correlation metadata in payload lineage.
3. Query trace continuity endpoint:
   - `GET /v1/setu/trace/<trace_id>`
4. Validate continuity response includes expected signal chain and audit references.

## Live Production Capture

- **Date:** 2026-06-08
- **Gateway:** https://bhiv-hr-gateway-l0xp.onrender.com
- **org_id:** 6a26664c88b72534dc0c06ab
- **trace_id:** f6f72b52-57ed-4ddf-a5c1-43379364c180
- **X-Correlation-ID (org create):** 9a83b441-e387-4e26-aeb2-2616e86d2762
- **Outcome:** All workforce and SETU sequence calls returned HTTP 200; evidence files updated to `live_capture`.

## Linked evidence

- `evidence/workforce_runtime/api_proof_workforce.json`
- `evidence/workforce_runtime/setu_signal_proof.json`
- `evidence/workforce_runtime/api_trace_matrix.md`
