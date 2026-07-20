# Partner-initiated live SETU capture — 20260702T073708Z

- **Gateway**: `https://bhiv-hr-gateway-l0xp.onrender.com`
- **Auth**: `API_KEY_SECRET` (Bearer) — `GATEWAY_SECRET_KEY` returned 401
- **Shared correlation_id**: `3d0a7d1a-1be8-4267-af5b-8d239ea25049`

## Per-partner results (Tier 2)

| Partner | Tier | Sampada signal_id | trace_id | Capture file |
|---|---|---|---|---|
| Artha | Tier 2 — dispatcher invoked directly | `sig-9802342a158c` | `TRC-20260702-19f21bf0` | `artha_payroll_visibility_capture.json` |
| CRM | Tier 2 — dispatcher invoked directly | `sig-5ffbd0b0bde4` | `crm-trace-3d0a7d1a` | `crm_participation_capture.json` |
| Logistics | Tier 2 — CRM dispatcher + `subsystem: logistics` | `sig-3acbbfa3ca0a` | `logistics-trace-3d0a7d1a` | `logistics_crm_participation_capture.json` |
| Niyantran | Tier 2 — real ExecutionEvent from Mongo | `sig-29f9efbb899a` | `trace_demo_002` | `niyantran_telemetry_capture.json` |

## Environment checkpoint

- Repo topology: embedded partner copies used (no ZIP divergence)
- Partner API servers: not booted (Tier 2 path)
- Sampada contract: unchanged

## Open owner decisions

1. Logistics separate `signal_type` vs `crm_participation` + subsystem marker
2. Tier 2 acceptability vs Tier 1 full partner-server flows
