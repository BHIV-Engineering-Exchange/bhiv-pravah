# CONTRACT_VERIFICATION.md
# Phase 1 — Contract Lock + Runtime Verification
# ARTHA v0.1 | Generated: 2025

---

## Verification Methodology

Every contract below was verified against live source code — not documentation.
Format: endpoint → request shape → actual response shape → frontend mapping → mismatches.

---

## 1. Authentication Contracts

### POST /api/v1/auth/login
**Request:**
```json
{ "email": "string", "password": "string" }
```
**Actual Response (200):**
```json
{
  "success": true,
  "data": {
    "token": "eyJ...",
    "user": { "id": "...", "email": "...", "name": "...", "role": "viewer", "roles": ["viewer"] }
  }
}
```
**Error (401):**
```json
{ "success": false, "message": "Invalid email or password" }
```
**Frontend mapping:** `authStore.js` — token stored to `localStorage['artha_auth_token']`, user stored in Zustand state.
**Mismatches:** NONE. Contract is exact.

---

### POST /api/v1/auth/signup
**Request:**
```json
{ "name": "string", "email": "string", "password": "string", "phone": "string (optional)" }
```
**Actual Response (201):**
```json
{
  "success": true,
  "data": { "token": "eyJ...", "user": { "id": "...", "email": "...", "name": "...", "role": "viewer", "roles": ["viewer"] } }
}
```
**Error (409):** `{ "success": false, "message": "An account with this email already exists" }`
**Mismatches:** New users always get `role: viewer`. Admin must be set in DB manually.

---

### GET /api/v1/auth/me
**Headers:** `Authorization: Bearer <token>`
**Actual Response (200):**
```json
{
  "success": true,
  "data": { "id": "...", "email": "...", "name": "...", "role": "...", "roles": [...], "allowedApps": [] }
}
```
**Frontend mapping:** `authStore.checkAuth()` — called on app boot to hydrate user state.
**Mismatches:** NONE.

---

## 2. Signal Contracts

### GET /api/v1/signals
**Headers:** `Authorization: Bearer <token>`
**Query:** `?severity=HIGH&type=SIG_CASHFLOW_NEGATIVE&limit=50&page=1`
**Actual Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "_id": "...",
      "signal_id": "SIG-<uuid>",
      "trace_id": "TRC-YYYYMMDD-<8hex>",
      "source": "ARTHA",
      "type": "SIG_CASHFLOW_NEGATIVE",
      "severity": "HIGH",
      "context": { "cash_flow": "-50000", "source": { "module": "LEDGER", "entity_type": "JOURNAL_ENTRY", "entity_id": "LEDGER_SNAPSHOT" } },
      "recommendation": "[PRIORITIZE_COLLECTIONS] Net cash flow is negative...",
      "created_at": "2025-01-01T00:00:00.000Z"
    }
  ],
  "pagination": { "page": 1, "limit": 50, "total": 3 }
}
```
**Error (500):** `{ "success": false, "message": "..." }`
**Frontend mapping:** `useSignals.js` — primary fetch. If list.length > 0, sets LIVE_LIST source. Maps via `mapDbSignalToDisplay()` in dashboard.

**Critical note on mapping:**
The DB model stores `source` as a plain string `"ARTHA"` and buries module/entity info inside `context.source`. The `normalizeSignal()` in `setu.pipeline.js` handles this correctly. The frontend `mapDbSignalToDisplay()` reads `sig.context?.source?.module` — this matches.

---

### GET /api/v1/signals/snapshot
**Headers:** `Authorization: Bearer <token>`
**Query:** `?startDate=YYYY-MM-DD&endDate=YYYY-MM-DD` (optional)
**Actual Response (200):**
```json
{
  "success": true,
  "data": {
    "source": "ledger-only",
    "period": { "startDate": null, "endDate": null },
    "cashFlow": "-12500.00",
    "tdsPayable": "5000.00",
    "outputCGST": "9000.00",
    "outputSGST": "9000.00"
  }
}
```
**Frontend mapping:** `useSignals.js` fallback. If `/signals` returns empty list, tries snapshot. Sets LIVE_SNAPSHOT source. Dashboard maps via `mapSnapshotToSignals()`.
**Side effect:** If cashFlow is negative, `getSignalSnapshot()` also calls `emitSignal(SIG_CASHFLOW_NEGATIVE)` — persists a ComplianceSignal to DB.
**Mismatches:** NONE.

---

### GET /api/v1/signals/trace/:traceId
**Headers:** `Authorization: Bearer <token>`
**Actual Response (200):**
```json
{
  "success": true,
  "data": {
    "trace_id": "TRC-20250101-abcd1234",
    "steps": [
      { "step": 1, "label": "Signal", "found": true, "data": { "signal_id": "SIG-...", "type": "...", "severity": "HIGH", "created_at": "..." } },
      { "step": 2, "label": "Compliance Validation", "found": false, "data": null },
      { "step": 3, "label": "Compliance Filing", "found": false, "data": null },
      { "step": 4, "label": "Journal Entries", "found": false, "data": [] },
      { "step": 5, "label": "Ledger Entries", "found": false, "data": [] }
    ],
    "reconstructed_at": "2025-01-01T00:00:00.000Z"
  }
}
```
**Note:** Steps 2–5 will only have `found: true` if the signal was generated from a compliance filing workflow (not from snapshot). Snapshot-derived signals (SIG_CASHFLOW_NEGATIVE, SIG_INVOICE_OVERDUE) will have steps 2–5 as `found: false` — this is correct behavior, not an error.

---

### POST /api/v1/signals/:signalId/dispatch
**Auth:** `admin` or `accountant` role required.
**signalId param:** Must match `signal_id` field in ComplianceSignal (format: `SIG-<uuid>`).

**Response when SETU_ENABLED=false (default):**
```json
{
  "success": true,
  "dispatch_attempted": false,
  "setu_enabled": false,
  "reason": "SETU_ENABLED is false — set SETU_ENABLED=true to enable dispatch",
  "pipeline_stage": "COMPLETE",
  "payload": { "signal_id": "...", "trace_id": "...", "source": {...}, "severity": "HIGH", ... },
  "headers": { "Content-Type": "application/json", "X-Artha-Trace": "...", "X-Signal-Type": "...", "X-Severity": "HIGH" },
  "warnings": []
}
```
**Response when SETU_ENABLED=true and SETU reachable:**
```json
{
  "success": true,
  "dispatch_attempted": true,
  "setu_enabled": true,
  "dispatched_at": "2025-01-01T00:00:00.000Z",
  "setu_status": 200,
  "setu_response": { ... },
  "pipeline_stage": "COMPLETE",
  "payload": {...},
  "headers": {...},
  "warnings": []
}
```
**Response when SETU timeout (502):**
```json
{
  "success": false,
  "dispatch_attempted": true,
  "failure_reason": "SETU_TIMEOUT",
  "failure_message": "timeout of 5000ms exceeded",
  "setu_status": null,
  "pipeline_stage": "COMPLETE",
  "payload": {...}
}
```
**Pipeline failure (422):**
```json
{
  "success": false,
  "dispatch_attempted": false,
  "pipeline_stage": "VALIDATE",
  "pipeline_error": "signal_id \"UNKNOWN\" is not a recognized signal type",
  "warnings": []
}
```

---

### GET /api/v1/signals/:signalId/pipeline-check
**Auth:** `admin` or `accountant` role required.
**Actual Response (200):**
```json
{
  "success": true,
  "data": {
    "ok": true,
    "stage": "COMPLETE",
    "payload": { "signal_id": "...", "trace_id": "...", "source": {...}, "severity": "...", "context": {...}, "recommendation": {...} },
    "headers": { "Content-Type": "application/json", "X-Artha-Trace": "...", "X-Signal-Type": "...", "X-Severity": "..." },
    "warnings": []
  }
}
```

---

## 3. GST Contracts

### GET /api/v1/gst/summary
**Query:** `?period=2025-02` (required, format YYYY-MM)
**Actual Response (200):**
Depends on `gstFilingService.getGSTSummary()` — returns filing packet summary for the period.
**Error (400):** `{ "success": false, "message": "Period is required (format: YYYY-MM)" }`
**Prerequisite:** CompanySettings must exist with valid `gstin` field. Without it: `{ "success": false, "message": "Company GSTIN not configured" }`

### GET /api/v1/gst/filing-packet/gstr-1
**Auth:** `admin` or `accountant`
**Query:** `?period=2025-02`
**Response:** Filing packet JSON with B2B/B2C invoices, HSN summary, tax totals.

### GET /api/v1/gst/filing-packet/gstr-3b
**Auth:** `admin` or `accountant`
**Query:** `?period=2025-02`
**Response:** GSTR-3B summary return with outward/inward supplies, net tax liability.

---

## 4. TDS Contracts

### GET /api/v1/tds/dashboard
**Query:** `?quarter=Q4&financialYear=FY2025-26`
**Actual Response (200):**
```json
{
  "success": true,
  "data": {
    "quarter": "Q4",
    "financialYear": "FY2025-26",
    "summary": { "totalDeducted": 15000, "totalPaid": 10000, "pendingPayment": 5000, "pendingCount": 2 },
    "bySection": [{ "section": "194J", "name": "Professional", "deducted": 15000, "paid": 10000, "pending": 5000 }],
    "byStatus": { "pending": 2, "deducted": 1, "deposited": 1, "filed": 0 },
    "filingStatus": {
      "form24Q": { "status": "pending", "dueDate": "2025-05-31T00:00:00.000Z" },
      "form26Q": { "status": "pending", "dueDate": "2025-05-31T00:00:00.000Z" },
      "form27Q": { "status": "not_applicable", "dueDate": null }
    },
    "entries": [...]
  }
}
```

---

## 5. Health / Runtime Contracts

### GET /health
**Auth:** None (public)
**Actual Response (200):**
```json
{
  "success": true,
  "message": "ARTHA API is running",
  "timestamp": "2025-01-01T00:00:00.000Z",
  "version": "0.1.0",
  "uptime": 3600.5
}
```
**Frontend usage:** `useRuntimeMode.js` uses this to determine BACKEND_CONNECTED vs BACKEND_UNAVAILABLE.

### GET /health/detailed
**Auth:** None (public)
**Actual Response (200):**
```json
{
  "success": true,
  "message": "ARTHA API is healthy",
  "data": {
    "status": "healthy",
    "timestamp": "...",
    "version": "0.1.0",
    "environment": "development",
    "uptime": 3600.5,
    "memory": { "rss": 12345, "heapUsed": 8900 },
    "components": {
      "database": { "status": "healthy", "state": "connected", "host": "artha.rzneis7.mongodb.net" },
      "redis": { "status": "disabled", "message": "Redis not configured" },
      "disk": { "status": "healthy" }
    }
  }
}
```

### GET /status
**Auth:** None (public)
**Response:** `{ "success": true, "data": { "database": "connected", "redis": "disabled", "uptime": 3600, "environment": "development", "version": "0.1.0" } }`

---

## 6. Contract Mismatches (Verified Issues)

| # | Endpoint | Issue | Impact | Fix Required |
|---|----------|-------|--------|--------------|
| 1 | `GET /api/v1/signals` | DB `source` is string `"ARTHA"`, not object. Frontend `mapDbSignalToDisplay` reads `sig.context?.source?.module` — works only if `emitSignal` stored it in context.source | Medium | Already handled in `mapDbSignalToDisplay`. No backend fix needed. |
| 2 | `POST /api/v1/signals/:signalId/dispatch` | `signalId` param must be `signal_id` field (format `SIG-<uuid>`), NOT MongoDB `_id`. Frontend must use `signal.signal_id` not `signal._id` when constructing dispatch URL. | High | Frontend must use `signal.signal_id` in dispatch calls. |
| 3 | `GET /api/v1/signals/trace/:traceId` | Snapshot-derived signals (cashflow, overdue invoices) will have steps 2–5 `found: false`. This is not an error — trace is partial by design for non-filing signals. | Low | Document in UI. No code change needed. |
| 4 | `GET /api/v1/gst/summary` | Requires `CompanySettings` with `gstin`. If not seeded, all GST operations fail silently or with cryptic errors. | High | Run `node scripts/seed.js` before testing GST. |
| 5 | `POST /api/v1/tds/entries` | `nature` field is required but missing from TDS route validation schema. Will fail at Mongoose level with a 500 if omitted. | Medium | Add `nature` to required fields in frontend form. |
| 6 | `GET /api/v1/signals` | If no signals exist in DB, returns empty array. `useSignals.js` falls through to snapshot. This is correct behavior but the empty array case must not be treated as an error. | Low | Already handled correctly in `useSignals.js`. |

---

## 7. Frontend API Mapping File

```
Dashboard signals flow:
  useRuntimeMode → GET /health (axios, no auth)
                 → GET /api/v1/signals/snapshot (api, with auth)
  useSignals    → GET /api/v1/signals (primary)
                → GET /api/v1/signals/snapshot (fallback)

Signal dispatch:
  SignalDetailEngine → POST /api/v1/signals/{signal.signal_id}/dispatch
                     → GET /api/v1/signals/{signal.signal_id}/pipeline-check

Trace reconstruction:
  SignalDetailEngine → GET /api/v1/signals/trace/{signal.trace_id}

GST Dashboard:
  GSTDashboard → GET /api/v1/gst/summary?period=YYYY-MM
               → GET /api/v1/gst/filing-packet/gstr-1?period=YYYY-MM
               → GET /api/v1/gst/filing-packet/gstr-3b?period=YYYY-MM

TDS Dashboard:
  TDSManagement → GET /api/v1/tds/dashboard?quarter=Q4&financialYear=FY2025-26
                → GET /api/v1/tds/entries
                → POST /api/v1/tds/calculate
```
