# FAILURE_MATRIX.md
# Phase 3 — Failure Path Closure
# ARTHA v0.1 | Every Failure Mode Documented

---

## Verification Rule

Every failure below must satisfy:
- Surfaces clearly (UI or API response contains the exact failure)
- Does not silently succeed (no 200 with hidden error state)
- Does not crash the server or frontend
- Has a deterministic recovery path

---

## F-01: Backend Unavailable

| Field | Detail |
|-------|--------|
| **Failure** | Backend process not running or network unreachable |
| **Trigger** | `useRuntimeMode.check()` → `GET /health` times out or ECONNREFUSED |
| **Backend behavior** | N/A — backend is down |
| **UI behavior** | `mode = BACKEND_UNAVAILABLE` → `RuntimeModeBanner` shows red "BACKEND UNAVAILABLE" strip → `BackendUnavailableState` component renders with "Retry Connection" button → No mock data substituted |
| **Recovery path** | Click "Retry Connection" → calls `recheck()` → re-runs `GET /health` → if backend is back, mode transitions to BACKEND_CONNECTED |
| **Code location** | `useRuntimeMode.js:check()`, `FinancialIntelligenceDashboard.jsx` render branch |
| **Silent success risk** | NONE — dashboard refuses to render any financial data until backend confirms |

---

## F-02: Signal Endpoint Failure (/api/v1/signals returns 5xx)

| Field | Detail |
|-------|--------|
| **Failure** | `/api/v1/signals` returns 500 or network error |
| **Trigger** | MongoDB query fails, or signals collection is corrupted |
| **Backend behavior** | Returns `{ "success": false, "message": "..." }` with HTTP 500 |
| **UI behavior** | `useSignals.fetchSignals()` catches the error silently (no throw) and falls through to Attempt 2: `GET /api/v1/signals/snapshot`. If snapshot also fails, `error` state is set with `{ message, status, url }`. Dashboard renders `Card` with red "SIGNAL FETCH FAILED" banner showing exact URL and HTTP status. Signals list is empty. |
| **Recovery path** | `useSignals` returns `source = SIGNAL_SOURCE.ERROR`. Dashboard shows EmptySignalState or error card. Manual refresh via "Refresh" button re-calls `fetchSignals()`. |
| **Code location** | `useSignals.js:fetchSignals()`, `FinancialIntelligenceDashboard.jsx` error surface |

---

## F-03: Empty Signals (no signals in DB yet)

| Field | Detail |
|-------|--------|
| **Failure** | `/api/v1/signals` returns `{ "data": [], "pagination": { "total": 0 } }` |
| **Trigger** | Fresh database, no expenses/invoices created yet |
| **Backend behavior** | Returns 200 with empty array — this is not an error |
| **UI behavior** | `useSignals` falls through to snapshot (Attempt 2). If snapshot returns data, renders snapshot-derived signals. If snapshot also returns 0 (no ledger entries), `signals = []`. Dashboard renders `EmptySignalState` with message "No signals in database yet. Create invoices, expenses, or run compliance filings to generate signals." |
| **Recovery path** | Create invoices or expenses, approve expenses (triggers ledger posting), then fetch snapshot to generate SIG_CASHFLOW_NEGATIVE if cash is negative. Or call `POST /api/v1/signals/evaluate/overdue-invoices` to generate overdue signals. |
| **Code location** | `useSignals.js` fallthrough logic, `EmptySignalState` component in dashboard |

---

## F-04: Schema Mismatch (signal missing required fields)

| Field | Detail |
|-------|--------|
| **Failure** | A signal in DB is missing `trace_id`, `type`, or `severity` |
| **Trigger** | Manual DB manipulation, or a bug in a signal persistence path |
| **Backend behavior** | `normalizeSignal()` in `setu.pipeline.js` throws `NormalizationError`. `pipelineCheck` / `dispatchSignal` catch this and return `{ "success": false, "pipeline_stage": "NORMALIZE", "pipeline_error": "trace_id is required" }` with HTTP 422. |
| **UI behavior** | `mapDbSignalToDisplay()` in dashboard has defensive defaults: `severity` defaults to `'LOW'` if unrecognized, `label` falls back to `sig.type || 'Signal'`. Signal renders with degraded display, not a crash. |
| **Recovery path** | Pipeline-check endpoint surfaces the exact missing field. Fix the signal data in DB or re-emit the signal via `signalEngine.emitSignal()`. |
| **Code location** | `setu.pipeline.js:normalizeSignal()`, `FinancialIntelligenceDashboard.jsx:mapDbSignalToDisplay()` |

---

## F-05: Invalid Signal Payload (pipeline validation failure)

| Field | Detail |
|-------|--------|
| **Failure** | Signal has unknown `signal_id` type or unrecognized `source.module` |
| **Trigger** | Signal emitted with a type not in `VALID_SIGNAL_TYPES` enum or module not in `VALID_MODULES` |
| **Backend behavior** | `validateSignal()` returns `{ valid: false, errors: ["signal_id \"UNKNOWN_SIG\" is not a recognized signal type", "source.module \"UNKNOWN\" is not recognized"] }`. `dispatchSignal` returns HTTP 422 with `pipeline_stage: "VALIDATE"` and full error list. |
| **UI behavior** | Dispatch button in SignalDetailEngine receives 422 → shows error toast/state with pipeline error message. Signal continues to render in UI (it's already in DB). |
| **Recovery path** | Correct the signal type to one of the 26 valid types in `VALID_SIGNAL_TYPES`. Snapshot-derived signals use typed IDs like `SIG_CASHFLOW_NEGATIVE`. Model-generated IDs (`SIG-<uuid>`) bypass type check and pass validation. |
| **Code location** | `setu.pipeline.js:validateSignal()`, `signal.controller.js:dispatchSignal()` |

---

## F-06: SETU Unavailable (SETU_ENABLED=true but endpoint down)

| Field | Detail |
|-------|--------|
| **Failure** | SETU base URL is unreachable (ECONNREFUSED or ENOTFOUND) |
| **Trigger** | `SETU_ENABLED=true`, `SETU_BASE_URL` set to offline endpoint |
| **Backend behavior** | `axios.post()` throws with code `ECONNREFUSED`. `dispatchSignal` catches this, sets `failure_reason = 'SETU_UNREACHABLE'`. Returns HTTP 502 with `{ "success": false, "dispatch_attempted": true, "failure_reason": "SETU_UNREACHABLE", "failure_message": "connect ECONNREFUSED ...", "pipeline_stage": "COMPLETE", "payload": {...} }` |
| **UI behavior** | 502 response → API interceptor in `api.js` shows toast "Server error. Please try again later." (generic 5xx handler). Dispatch button shows failed state. |
| **Recovery path** | Set `SETU_ENABLED=false` to continue in local mode. Or fix `SETU_BASE_URL` in `.env`. |
| **Code location** | `signal.controller.js:dispatchSignal()` SETU catch block |

---

## F-07: SETU Timeout

| Field | Detail |
|-------|--------|
| **Failure** | SETU endpoint responds too slowly |
| **Trigger** | SETU endpoint takes longer than `SETU_TIMEOUT_MS` (default: 5000ms) |
| **Backend behavior** | `axios.post()` throws with `code: 'ECONNABORTED'`. `isTimeout = true`. Returns HTTP 502 with `failure_reason: "SETU_TIMEOUT"`. Pipeline payload is still included in response for inspection. |
| **UI behavior** | Same as F-06: 502 → generic error toast. |
| **Recovery path** | Increase `SETU_TIMEOUT_MS` in `.env`. Or check SETU endpoint performance. |
| **Code location** | `signal.controller.js:dispatchSignal()` |

---

## F-08: Trace Reconstruction Missing (no DB records for trace_id)

| Field | Detail |
|-------|--------|
| **Failure** | `GET /api/v1/signals/trace/:traceId` finds no matching records |
| **Trigger** | trace_id provided for a non-existent signal, or trace_id is from a snapshot-derived signal with no filing chain |
| **Backend behavior** | Returns HTTP 200 with all 5 steps having `found: false, data: null`. This is correct — not a 404. |
| **UI behavior** | SignalDetailEngine renders the chain with all steps showing "Not Found" state. Does not crash. |
| **Recovery path** | Snapshot-derived signals (cashflow, overdue) will always have steps 2–5 as not found — this is by design. For filing signals, ensure the filing was generated via compliance controller which persists ComplianceFiling and ComplianceValidationLog. |
| **Code location** | `signal.controller.js:reconstructTrace()` |

---

## F-09: Compliance Endpoint Failure (GST summary fails)

| Field | Detail |
|-------|--------|
| **Failure** | `GET /api/v1/gst/summary` returns 400 or 500 |
| **Trigger 1** | `period` query param missing → HTTP 400 `{ "success": false, "message": "Period is required (format: YYYY-MM)" }` |
| **Trigger 2** | CompanySettings not seeded → HTTP 500 `{ "success": false, "message": "Company GSTIN not configured" }` |
| **Trigger 3** | No invoices for the period → returns empty B2B/B2C arrays with zero totals (not an error) |
| **UI behavior** | GSTDashboard catches error response. If 400/500, shows error state. If empty data, shows "No GST data for this period." |
| **Recovery path** | Trigger 1: Always pass period param. Trigger 2: Run `node scripts/seed.js` or create CompanySettings via `/api/v1/settings/company`. Trigger 3: Expected behavior for empty periods. |
| **Code location** | `gst.controller.js:getGSTSummary()`, `GSTDashboard.jsx` |

---

## F-10: Expense Auto-Record Failure After Approval

| Field | Detail |
|-------|--------|
| **Failure** | `approveExpense()` succeeds but `recordExpense()` fails (GST validation error, missing account, etc.) |
| **Trigger** | Company state missing from CompanySettings when expense has `gstRate > 0`, or required Chart of Accounts not seeded |
| **Backend behavior** | `approveExpense()` catches the `recordExpense()` error with `logger.warn()` and continues. Expense status is `approved` but not `recorded`. No 500 returned — approval itself succeeds with HTTP 200. |
| **UI behavior** | Expense shows `status: approved` in UI. No visible error. The failure is in backend logs only. |
| **Silent success risk** | HIGH — this is the one failure mode that IS silent. The approval API returns success even though recording failed. |
| **Recovery path** | Approval response now includes `warnings: ["Auto-record failed: <reason>. Call POST /expenses/<id>/record to retry..."]`. Call `GET /api/v1/runtime/status` to inspect `transactions.recorded_expenses` count. Fix the underlying issue (seed CompanySettings, ensure account codes exist). Then manually call `POST /api/v1/expenses/:id/record` to retry recording only. |
| **Code location** | `expense.service.js:approveExpense()` try/catch block (line ~180) |
| **Recommended improvement** | Return a warning in the approval response when auto-record fails: add `warnings: ["Auto-record failed: <message>"]` to the response body. |

---

## F-11: JWT Expired / Invalid Token

| Field | Detail |
|-------|--------|
| **Failure** | User's JWT has expired (7-day lifetime) or been tampered |
| **Trigger** | Any authenticated API call after token expiry |
| **Backend behavior** | `protect` middleware catches `jwt.verify()` failure, returns HTTP 401 `{ "success": false, "message": "Token is invalid or expired", "redirect": "http://localhost:5173/login" }` |
| **UI behavior** | `api.js` response interceptor: 401 on non-auth routes → `localStorage.removeItem('artha_auth_token')` → `window.location.href = '/login'`. User is redirected to login. Toast: "Session expired. Please sign in again." |
| **Recovery path** | Log in again. No refresh token mechanism — user must re-authenticate. |
| **Code location** | `middleware/auth.js:protect()`, `frontend/src/services/api.js` response interceptor |

---

## F-12: Ledger Chain Hash Verification Failure

| Field | Detail |
|-------|--------|
| **Failure** | `GET /api/v1/ledger/verify-chain` returns `isValid: false` |
| **Trigger** | Manual DB edit of a LedgerEntry, incorrect HMAC_SECRET, or data corruption |
| **Backend behavior** | Returns HTTP 200 with `{ "isValid": false, "errors": [{ "position": 5, "journalId": "...", "issue": "Hash mismatch (possible tampering)" }], "totalEntries": 12 }` |
| **UI behavior** | LedgerIntegrity page renders error state with red indicators. Shows exact position and journal ID of the tampered entry. |
| **Recovery path** | Do NOT attempt to re-hash silently. Run `node scripts/verify-integrity.js` for full audit. Investigate the `position` returned. If environment migration changed `HMAC_SECRET`, run `node scripts/migrate-hash-chain.js`. |
| **Code location** | `ledger.service.js:verifyLedgerChain()`, `LedgerIntegrity.jsx` |

---

## F-13: MongoDB Replica Set Not Available (transactions degraded)

| Field | Detail |
|-------|--------|
| **Failure** | MongoDB Atlas free tier or single node — no replica set |
| **Trigger** | Server startup → `db.admin().command({ replSetGetStatus: 1 })` fails |
| **Backend behavior** | `transactionsAvailable = false`. All `withTransaction()` calls execute without sessions (`callback(null)`). Invoice sending, expense recording, and TDS deduction all work but without ACID transactions. Log warning: "Transactions not available - executing without transaction" |
| **UI behavior** | No visible change. All operations succeed. Risk: partial failure (e.g., journal entry created but status update fails) is not automatically rolled back. |
| **Recovery path** | Use MongoDB Atlas M10+ tier or configure a local replica set for production. |
| **Code location** | `config/database.js:withTransaction()` |

---

## F-14: Rate Limit Exceeded

| Field | Detail |
|-------|--------|
| **Failure** | Too many requests from same IP |
| **Trigger** | > 100 requests per 15 minutes (default config) |
| **Backend behavior** | express-rate-limit returns HTTP 429 with default message |
| **UI behavior** | `api.js` interceptor: `error.response?.status === 429` → `toast.error(message)` |
| **Recovery path** | Wait for rate limit window to reset (15 minutes). For development, set `RATE_LIMIT_MAX=10000` in `.env`. |

---

## F-15: CompanySettings Not Seeded (blocks GST + Invoice send)

| Field | Detail |
|-------|--------|
| **Failure** | Any invoice send or expense record with GST fails |
| **Trigger** | `CompanySettings.findById('company_settings')` returns null |
| **Backend behavior** | `invoice.service.js:sendInvoice()` throws `buildGSTValidationError('Company state is required for GST')`. Returns HTTP 500 with GST_VALIDATION_ERROR code. |
| **UI behavior** | Invoice send fails with error message "Company state is required for GST". |
| **Recovery path** | Navigate to `/settings/company` and create company settings with GSTIN and address.state. Or run `node scripts/seed.js` which creates default settings. |

---

## Summary Table

| Code | Failure | Silent? | Crashes? | Recovery |
|------|---------|---------|----------|----------|
| F-01 | Backend down | No | No | Retry button |
| F-02 | Signal 5xx | No | No | Auto-fallback to snapshot |
| F-03 | No signals | No | No | Create data |
| F-04 | Schema mismatch | Partial | No | Pipeline-check |
| F-05 | Invalid payload | No | No | Fix signal type |
| F-06 | SETU unreachable | No | No | Disable SETU |
| F-07 | SETU timeout | No | No | Increase timeout |
| F-08 | Trace missing | No | No | Expected for snapshot signals |
| F-09 | GST endpoint fail | No | No | Seed settings |
| **F-10** | **Expense auto-record silent fail** | **NO — fixed** | **No** | `warnings[]` in approval response. Manual retry via `POST /expenses/:id/record` |
| F-11 | JWT expired | No | No | Re-login |
| F-12 | Ledger tampered | No | No | Audit + migrate |
| F-13 | No transactions | No (warn) | No | Use replica set |
| F-14 | Rate limited | No | No | Wait |
| F-15 | No company settings | No | No | Seed or create via UI |

**F-10 is the only silent failure path in the system.** All others surface clearly.
