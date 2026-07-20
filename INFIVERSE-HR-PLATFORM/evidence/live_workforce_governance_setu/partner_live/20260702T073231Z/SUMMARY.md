# Partner-initiated live SETU capture — 20260702T073231Z

- Gateway: `https://bhiv-hr-gateway-l0xp.onrender.com`
- Auth: `API_KEY_SECRET` (Bearer) — `GATEWAY_SECRET_KEY` returned 401
- Shared correlation_id: `3d0a7d1a-1be8-4267-af5b-8d239ea25049`

## Per-partner
- **artha**: Tier 2 — dispatcher invoked directly against live gateway; Artha API server not started (JWT-gated dispatch route).
- **crm**: Tier 2 — sampada_dispatcher invoked directly; CRM FastAPI server not started.
- **niyantran**: Tier 2 — setuDispatcher invoked with real ExecutionEvent from Niyantran Mongo when available, else blocker recorded.
- **logistics**: Tier 2 — crm_participation with payload.subsystem=logistics via CRM dispatcher (no separate Logistics backend).
