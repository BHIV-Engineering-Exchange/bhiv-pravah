# FAQ.md
# ARTHA v0.1 — Developer FAQ
# Phase 6 | Handover Package

---

## Q1: How do I run Artha UI?

**Prerequisites:** Node.js 18+, backend running on port 5000, MongoDB Atlas connected.

```bash
# 1. Backend (terminal 1)
cd AI-Artha-main/backend
cp .env.example .env          # configure MONGODB_URI, JWT_SECRET, HMAC_SECRET
npm install
node scripts/seed.js          # required: creates CompanySettings + Chart of Accounts
node scripts/seed-tds.js      # required: creates TDS sample data
npm run dev                   # starts on http://localhost:5000

# 2. Frontend (terminal 2)
cd AI-Artha-main/frontend
npm install
npm run dev                   # starts on http://localhost:5173
```

**Access:** Open `http://localhost:5173` → redirected to `/login`

**Default credentials after seeding:**
The seed script creates an admin user. Check `backend/scripts/seed.js` for the seeded email/password, or register via `/signup` and manually update role to `admin` in MongoDB.

**Verify everything is working:**
```bash
curl http://localhost:5000/health
# → {"success":true,"message":"ARTHA API is running",...}
```

---

## Q2: How does runtime mode work?

Runtime mode is the single source of truth for backend connection state. It runs on every app boot and on manual recheck.

**Detection logic (`useRuntimeMode.js`):**
1. Check `VITE_MOCK_MODE=true` → if yes: `MOCK_MODE` (no network calls)
2. `GET /health` (5s timeout, no auth):
   - fails → `BACKEND_UNAVAILABLE`
   - succeeds → check signals
3. `GET /api/v1/signals/snapshot` (5s timeout, with auth):
   - succeeds or 401 → `BACKEND_CONNECTED`
   - fails (not 401) → `BACKEND_DEGRADED`

**Where it's visible:**
`RuntimeModeBanner` component is rendered at the top of every intelligence page (Dashboard + SignalDashboard). It is always visible — never hidden, never conditional on data availability.

**To trigger each mode deliberately:**
```bash
BACKEND_CONNECTED   → run backend normally
BACKEND_DEGRADED    → start backend but break the /signals/snapshot handler (throw error in controller)
BACKEND_UNAVAILABLE → kill the backend process
MOCK_MODE           → add VITE_MOCK_MODE=true to frontend/.env
```

---

## Q3: How does SETU dispatch work?

SETU dispatch is the process of sending a compliance signal from Artha to the SETU intelligence hub.

**Step-by-step:**

1. Select a persisted signal (has `signal_id` like `SIG-<uuid>`)
2. Click "SEND TO SETU" in `SignalDetailEngine`
3. Frontend calls `POST /api/v1/signals/:signalId/dispatch`
4. Backend runs the 4-stage pipeline:
   - **NORMALIZE** — converts DB shape to canonical internal shape
   - **VALIDATE** — checks all required fields, known signal types, severity
   - **MAP** — transforms to SETU canonical payload (ARTHA_SETU_CONTRACT.md)
   - **SERIALIZE** — JSON.stringify + build HTTP headers
5. If `SETU_ENABLED=false` (default): returns payload proof — dispatch not attempted
6. If `SETU_ENABLED=true`: `axios.post(SETU_BASE_URL/api/v1/signals/ingest, body, headers)`
7. Result returned with exact `dispatch_attempted`, `setu_status`, `failure_reason`

**Enable SETU dispatch:**
```bash
# backend/.env
SETU_ENABLED=true
SETU_BASE_URL=https://your-setu-endpoint.com
SETU_API_KEY=your-api-key
SETU_TIMEOUT_MS=5000
```

**Snapshot-derived signals cannot be dispatched** directly — they have no `signal_id`. The client-side guard in `SignalDetailEngine` catches this immediately.

---

## Q4: How does trace reconstruction work?

Trace reconstruction links a signal back to its origin in the ledger chain.

**Trigger:** Click "Show Trace Chain" on any signal with a `trace_id`.

**Backend call:** `GET /api/v1/signals/trace/:traceId`

**Returns 5-step chain:**
- Step 1: Signal record (from `ComplianceSignal` collection)
- Step 2: Compliance Validation Log (from `ComplianceValidationLog`)
- Step 3: Compliance Filing (from `ComplianceFiling`)
- Step 4: Source Journal Entries (from `JournalEntry`)
- Step 5: Ledger Entries (from `LedgerEntry`)

**Important:** Steps 2–5 are only populated for signals generated from compliance filings (GST, TDS). Snapshot-derived signals (e.g., `SIG_CASHFLOW_NEGATIVE`) will have steps 2–5 as `found: false` — this is correct, not an error. The signal is self-contained.

**Each step is collapsible** in `SignalTracePanel` with raw JSON.

---

## Q5: How does degraded mode behave?

Degraded mode (`BACKEND_DEGRADED`) means the backend is running but the signals intelligence layer is failing.

**What still works in degraded mode:**
- All non-intelligence pages (invoices, expenses, accounting, reports, GST, TDS)
- Authentication
- Health endpoint

**What doesn't work:**
- Signal fetching
- SETU dispatch
- RuntimeModeBanner shows amber "SNAPSHOT FALLBACK ACTIVE"

**UI behavior:**
- `useSignals.fetchSignals()` still runs both attempts
- Both fail → `error` state set
- Dashboard/SignalDashboard shows red "SIGNAL FETCH FAILED" card with exact URL + HTTP status
- Refresh button available

**`ComplianceVisibilityLayer` in degraded mode:**
GST and TDS endpoints (`/gst/summary`, `/tds/dashboard`) are independent of the signals endpoint. They may still work in degraded mode and show compliance data. Each has its own error surface if it fails.

---

## Q6: How does an incoming developer debug signal failures?

**Step 1 — Check runtime mode**
Open `/dashboard` or `/signals`. Look at `RuntimeModeBanner` at the top.
- Green = backend connected → signal issue is in data or auth
- Amber = signals endpoint failing → check backend logs
- Red = backend down → start backend first

**Step 2 — Check the raw payload**
On both dashboard pages, a "raw payload" collapsible shows the exact API response.
Click it to see what the backend actually returned.

**Step 3 — Check signal count**
```bash
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/v1/signals
# → { "data": [], "pagination": { "total": 0 } }
# If empty: generate signals first
```

**Step 4 — Generate signals manually**
```bash
# Trigger overdue invoice evaluation
curl -X POST -H "Authorization: Bearer <token>" http://localhost:5000/api/v1/signals/evaluate/overdue-invoices

# Trigger snapshot (emits SIG_CASHFLOW_NEGATIVE if cash is negative)
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/v1/signals/snapshot
```

**Step 5 — Run pipeline-check on a signal**
```bash
# Get signal_id from list
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/v1/signals
# Then:
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/v1/signals/<signal_id>/pipeline-check
# Shows: ok, stage, payload, errors
```

**Step 6 — Check runtime status**
```bash
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/v1/runtime/status
# Returns: DB state, signal count, ledger chain tip, SETU config, recent signals
```

**Step 7 — Check backend logs**
```bash
cd backend
cat logs/combined.log | grep -i "signal\|error\|warn" | tail -50
```

**Common issues:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| No signals in DB | Nothing has generated signals yet | Run overdue evaluation or approve an expense |
| GST snapshot fails | CompanySettings missing | Run `node scripts/seed.js` |
| Dispatch returns 422 | Signal has unknown type/module | Check `signal_id` — must be in `VALID_SIGNAL_TYPES` or `SIG-<uuid>` format |
| Dispatch returns 502 | SETU unreachable/timeout | Check `SETU_BASE_URL` or set `SETU_ENABLED=false` |
| mode = BACKEND_DEGRADED | `/signals/snapshot` failing | Check MongoDB connection + ChartOfAccounts seeded |
| All expenses show status=approved but not recorded | Auto-record failed silently | Check `warnings` field in approve response; call `POST /expenses/:id/record` |
