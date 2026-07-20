# Partner SETU Live Closeout — End-to-End Runbook (What Was Done, Live Behavior, Deployment Changes, and Testing)

**Date:** 2026-07-02  
**Workspace:** `INFIVERSE-HR-PLATFORM`  
**Owner/Acceptance Authority:** Rishabh Yadav  
**Execution Role:** Convergence & Expansion Builder (additive changes only, no ownership/contract change)

---

## 1) Executive Snapshot

This closeout completed **partner-initiated SETU participation** for all four systems with **real HTTP calls to the live Sampada gateway**:

- Artha -> `artha_payroll_visibility`
- CRM -> `crm_participation`
- Logistics (through CRM backend) -> `crm_participation` with `payload.subsystem="logistics"`
- Niyantran -> `niyantran_telemetry`

All four are captured as **Tier 2**:
- Real partner data used
- Real live gateway request/response captured
- Partner servers were not fully booted through full business route path in this session

**Canonical evidence bundle:**
`evidence/live_workforce_governance_setu/partner_live/20260702T073708Z/`

---

## 2) Proper Flow — Step by Step (What Was Done)

## Step 0 — Guardrails Confirmed
- Sampada SETU contract was frozen (no route/schema changes)
- Existing historical evidence bundles were preserved
- Secrets remained in git-ignored `.env` files only
- Only additive partner-side changes were allowed

## Step 1 — Live Gateway Reachability and Auth Resolution
- Health check against live gateway passed
- Two-key probe executed:
  - `API_KEY_SECRET` -> HTTP 200 on `GET /v1/setu/signals?limit=1` (partner-facing bearer key)
  - `GATEWAY_SECRET_KEY` -> HTTP 401 (not used by partner dispatchers)

## Step 2 — Topology/Codebase Check
- Embedded partner repos in workspace were used:
  - `Artha/`
  - `ai-crm/`
  - `workflow-blackhole/`
- No conflicting alternate ZIP source chosen in execution path

## Step 3 — Artha (Phase 5A)
- Added Sampada envelope adapter
- Re-pointed dispatch target to:
  - `POST /v1/setu/signals/artha_payroll_visibility`
- Used real Artha signal data and dispatched to live gateway
- Captured request/response and confirmed signal presence in Sampada list endpoint

## Step 4 — CRM + Logistics (Phase 5B)
- Added outbound dispatcher in CRM backend (`sampada_dispatcher.py`)
- Hooked dispatcher into telemetry flow as additive side-effect
- Sent:
  - CRM participation signal
  - Logistics-marked participation signal (`payload.subsystem="logistics"`)
- Confirmed both in live Sampada via signal list query

## Step 5 — Niyantran (Phase 5C)
- Added outbound dispatcher service (`setuDispatcher.js`)
- Hooked into execution event emission path (additive fire-and-forget)
- Invoked dispatcher using real Niyantran execution event data
- Confirmed live Sampada receipt

## Step 6 — Consolidated Evidence and Documentation (Phase 5D)
- Stored all captures under one timestamped evidence folder
- Updated sprint docs and root status docs to reflect:
  - Partner live dispatch done
  - Tier level for each partner
  - Open owner decisions

## Step 7 — Regression Verification
- Sampada gateway tests run and passing
- Compileall check passed
- Sampada SETU contract files unchanged

---

## 3) Live Runtime Reaction — How Each System Behaves

## Sampada (Gateway)
When partner signal arrives at:
- `POST /v1/setu/signals/{signal_type}`

Sampada:
1. Validates auth bearer token
2. Validates signal type and payload envelope
3. Stores signal + lineage metadata
4. Returns success response with `sig-...` id
5. Makes signal queryable via:
   - `GET /v1/setu/signals`
   - `GET /v1/setu/trace/{trace_id}`

## Artha
When Artha dispatch is triggered:
1. Signal is normalized/serialized
2. Adapter maps into Sampada `SetuSignalIngest` shape
3. POST sent to Sampada `artha_payroll_visibility` route
4. Response/attempt metadata captured on Artha side
5. Signal visible in Sampada list/trace reads

## CRM
When CRM telemetry event is emitted:
1. Dispatcher builds Sampada envelope (`crm_participation`)
2. Sends HTTP POST to Sampada
3. Result stored/logged in CRM telemetry flow
4. Signal becomes available in Sampada signal list/trace

## Logistics (inside ai-crm)
No independent logistics backend service is used here.
1. Logistics context is represented in CRM-dispatched payload
2. Same signal type (`crm_participation`) is used
3. `payload.subsystem="logistics"` differentiates source context
4. Sampada stores and exposes it as CRM participation with subsystem marker

## Niyantran
When execution event is produced:
1. Niyantran dispatcher maps event fields into Sampada envelope
2. Sends to `niyantran_telemetry` endpoint
3. Ack/signal id received and logged
4. Signal becomes queryable in Sampada by type/correlation

---

## 4) What Must Be Changed for Live Deployment (Backend + Frontend)

> This section is the deployment checklist for making this sustainable in live environments (beyond one capture session).

## 4.1 Sampada (Backend)
- Keep SETU contract unchanged unless owner-approved future sprint
- Ensure env contains valid:
  - API key secret used for partner auth
  - Mongo connection values
- Ensure routes remain exposed and monitored:
  - `/v1/setu/signals/{signal_type}`
  - `/v1/setu/signals`
  - `/v1/setu/trace/{trace_id}`
- Add rotation plan for exposed/old secrets after this closeout

## 4.2 Sampada (Frontend)
- No mandatory new UI required for ingestion correctness
- Recommended:
  - Control Center widget/filter for partner-originated SETU signals
  - Optional badge by source system (Artha/CRM/Logistics/Niyantran)
- Ensure existing flags are correctly set in live:
  - `VITE_ENABLE_CONTROL_CENTER=true`
  - `VITE_ENABLE_GOVERNANCE=true`

## 4.3 Artha (Backend)
- Keep dispatcher path pointed to Sampada SETU endpoint (not placeholder ingest route)
- Ensure env has:
  - `SETU_ENABLED=true`
  - `SETU_BASE_URL=<live_sampada_gateway>`
  - `SETU_API_KEY=<partner-facing bearer key>`
- Keep adapter logic additive and isolated from payroll core logic

## 4.4 Artha (Frontend)
- Usually no hard frontend change required for dispatch itself
- Optional:
  - Add dispatch status visibility in signal UI
  - Show last Sampada ack id/time

## 4.5 CRM / ai-crm (Backend)
- Keep `sampada_dispatcher.py` enabled and reachable
- Ensure env has:
  - `SAMPADA_SETU_BASE_URL`
  - `SAMPADA_SETU_API_KEY`
- Maintain telemetry hook as additive side-effect, not core flow replacement

## 4.6 CRM / ai-crm (Frontend)
- Optional:
  - Signal dispatch status component in admin/ops panel
  - Filter for `crm` vs `logistics` subsystem signals

## 4.7 Logistics (Frontend via ai-crm)
- If logistics dashboards consume SETU feedback, ensure they parse subsystem marker
- No separate backend deploy needed unless owner decides dedicated logistics service

## 4.8 Niyantran (Backend)
- Keep `setuDispatcher.js` + event hook wired after execution event persistence
- Ensure env has:
  - `SAMPADA_SETU_BASE_URL`
  - `SAMPADA_SETU_API_KEY`
- Keep fire-and-forget behavior resilient (timeouts/retries/logging)

## 4.9 Niyantran (Frontend)
- Optional:
  - Execution timeline UI can show “sent to Sampada” markers
  - Show retry/failure counters for visibility

---

## 5) How to Test Each Project Individually

## 5.1 Sampada Gateway
1. Health:
   - `GET /health` -> 200
2. Auth probe:
   - `GET /v1/setu/signals?limit=1` with partner bearer key -> 200
3. Test suite:
   - `python -m pytest -q backend/tests/gateway/`
4. Compile check:
   - `python -m compileall backend/services/gateway`

Expected: passing tests, compile success, no route/schema diff on SETU contract files.

## 5.2 Artha
1. Verify env loaded (`SETU_ENABLED`, base URL, API key)
2. Trigger dispatcher (route or script path used in closeout)
3. Capture outbound request + response
4. Confirm in Sampada:
   - `GET /v1/setu/signals?signal_type=artha_payroll_visibility&correlation_id=<id>`

Expected: HTTP 200 dispatch + `sig-...` visible in Sampada.

## 5.3 CRM
1. Verify dispatcher module import and env values
2. Trigger telemetry event that invokes dispatcher
3. Confirm outbound 200
4. Confirm in Sampada:
   - `GET /v1/setu/signals?signal_type=crm_participation&correlation_id=<id>`

Expected: signal appears with CRM origin fields.

## 5.4 Logistics (through CRM backend)
1. Trigger logistics-context event through CRM flow
2. Ensure payload includes `subsystem="logistics"`
3. Confirm in Sampada by same `crm_participation` signal type + correlation

Expected: signal appears with logistics marker in payload.

## 5.5 Niyantran
1. Verify dispatcher/env
2. Trigger execution event flow (or controlled dispatcher invocation with real event)
3. Confirm outbound HTTP 200
4. Confirm in Sampada:
   - `GET /v1/setu/signals?signal_type=niyantran_telemetry&correlation_id=<id>`

Expected: `sig-...` present and trace-linked.

---

## 6) How to Test All Systems Together (Integrated Run)

## Objective
Validate cross-system participation using one shared `correlation_id` and live Sampada confirmation.

## Integrated Sequence
1. Generate/select one shared `correlation_id`
2. Run Artha dispatch
3. Run CRM dispatch
4. Run Logistics-marked dispatch
5. Run Niyantran dispatch
6. Query Sampada list endpoint per type with same correlation id
7. Query traces to verify reconstruction continuity
8. Save consolidated evidence bundle with:
   - request payload snapshot
   - response snapshot
   - timestamp
   - signal id

## Pass Criteria
- All 4 dispatches -> HTTP 200
- All 4 return real `sig-...` ids
- All 4 retrievable from Sampada list endpoint
- No Sampada contract changes needed
- Evidence bundle complete and auditable

---

## 7) Current Known Decisions Pending (Owner)

1. Should Logistics get its own Sampada `signal_type`, or remain under `crm_participation` + subsystem marker?
2. Is Tier 2 acceptable for sprint closure, or is Tier 1 full partner-server path mandatory before final sign-off?

---

## 8) Canonical Evidence References

- Main evidence index:
  - `evidence/live_workforce_governance_setu/SUMMARY.md`
- Partner closeout bundle:
  - `evidence/live_workforce_governance_setu/partner_live/20260702T073708Z/`
- Partner closeout status in docs:
  - `REVIEW_PACKET.md`
  - `SAMPADA_CURRENT_STATE.md`
  - `Live WO, GE & SETU Participation Sprint (Sampada Convergence and Expansion Builder)/SETU_PARTICIPATION_EVIDENCE.md`

---

## 9) Recommended Immediate Next Action

If acceptance requires **Tier 1**, schedule one controlled window where each partner server is fully running and trigger real business routes (not direct dispatcher invocation), then append a new `partner_live/<timestamp>/` capture proving Tier 1 for each partner.