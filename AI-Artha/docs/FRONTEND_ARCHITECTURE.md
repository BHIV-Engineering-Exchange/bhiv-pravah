# FRONTEND_ARCHITECTURE.md
# Phase 6 — Frontend Architecture
# ARTHA v0.1 | Handover Package

---

## Entry Points

| File | Route | Auth | Purpose |
|------|-------|------|---------|
| `src/main.jsx` | — | — | Vite entry, mounts `<App/>` with BrowserRouter + QueryClient + Toaster |
| `src/App.jsx` | — | — | Route definitions, ProtectedRoute / RoleProtectedRoute guards |
| `src/pages/dashboard/FinancialIntelligenceDashboard.jsx` | `/dashboard` | any auth | Primary intelligence surface |
| `src/pages/compliance/SignalDashboard.jsx` | `/signals` | admin/accountant | Dedicated signal + SETU dispatch |
| `src/pages/auth/Login.jsx` | `/login` | public | JWT login form |
| `src/pages/auth/Signup.jsx` | `/signup` | public | New user registration |

---

## Component Map

```
src/
├── App.jsx                          Route tree + auth guards
├── main.jsx                         App bootstrap
│
├── components/
│   ├── common/                      Shared UI primitives
│   │   ├── Badge.jsx                Severity / status badges
│   │   ├── Button.jsx               Primary / outline / ghost variants
│   │   ├── Card.jsx                 Container with border + shadow
│   │   ├── Loading.jsx              Spinner + Loading.Page
│   │   ├── Modal.jsx                Dialog overlay
│   │   └── ...                      Input, Select, Table, etc.
│   │
│   ├── intelligence/                Signal intelligence widgets
│   │   ├── RuntimeModeBanner.jsx    ← ALWAYS VISIBLE mode indicator
│   │   ├── SignalDetailEngine.jsx   ← SETU dispatch UI + state machine
│   │   ├── SignalStackPanel.jsx     Signal list grouped by severity
│   │   ├── SignalTracePanel.jsx     5-step chain reconstruction
│   │   └── ComplianceVisibilityLayer.jsx  GST + TDS snapshot
│   │
│   └── layout/
│       ├── Layout.jsx               App shell (sidebar + navbar + outlet)
│       ├── Sidebar.jsx              Navigation with role-filtered menu items
│       ├── Navbar.jsx               Top bar with user menu
│       └── AuthLayout.jsx           Centered auth form container
│
├── hooks/
│   ├── useRuntimeMode.js            ← Runtime state (4 modes)
│   ├── useSignals.js                ← Signal fetching (2-attempt strategy)
│   ├── useComplianceSnapshot.js     ← GST + TDS fetching
│   ├── useDashboard.js              Dashboard KPIs
│   ├── useInvoices.js               Invoice list + pagination
│   ├── useExpenses.js               Expense list + pagination
│   ├── useTheme.jsx                 Dark / universe mode toggle
│   └── index.js                     Barrel export
│
├── pages/
│   ├── dashboard/
│   │   ├── FinancialIntelligenceDashboard.jsx   Signal + compliance overview
│   │   └── Dashboard.jsx                        (legacy, redirects)
│   ├── compliance/
│   │   ├── SignalDashboard.jsx                  Full signal intelligence page
│   │   ├── GSTDashboard.jsx                     GST filing + summary
│   │   └── TDSManagement.jsx                    TDS entries + deductions
│   ├── invoices/                     Invoice CRUD
│   ├── expenses/                     Expense CRUD + approval
│   ├── accounting/                   Journal entries, COA, ledger integrity
│   ├── reports/                      P&L, Balance Sheet, Cash Flow, etc.
│   ├── statements/                   Bank statement upload + detail
│   ├── settings/                     Company settings, user management
│   └── upload/                       Smart upload (OCR)
│
├── services/
│   ├── api.js                        Axios instance + interceptors
│   └── index.js                      (legacy barrel)
│
├── store/
│   └── authStore.js                  Zustand auth state (user, isAuthenticated)
│
└── utils/
    ├── formatters.js                 Currency, date, number formatters
    └── themeUtils.js                 CSS variable helpers
```

---

## Runtime Flows

### Flow 1 — App Boot

```
main.jsx
  → BrowserRouter + QueryClientProvider + Toaster
  → App.jsx renders
  → useAuthStore.checkAuth()
      → localStorage.getItem('artha_auth_token')
      → if token: GET /api/v1/auth/me → sets user + isAuthenticated
      → if no token: isAuthenticated=false
  → ProtectedRoute checks isAuthenticated
      → false → redirect /login
      → true → render Layout + route
  → Layout renders Sidebar + Navbar + Outlet
```

### Flow 2 — Dashboard Intelligence Surface

```
FinancialIntelligenceDashboard mounts
  → useRuntimeMode.check()
      → GET /health (no auth)
      → GET /api/v1/signals/snapshot (with auth)
      → sets mode: BACKEND_CONNECTED | BACKEND_DEGRADED | BACKEND_UNAVAILABLE
  → useEffect: if CONNECTED/DEGRADED → useSignals.fetchSignals()
      → Attempt 1: GET /api/v1/signals?limit=50
          → if list > 0: source=LIVE_LIST, map via mapDbSignalToDisplay()
      → Attempt 2: GET /api/v1/signals/snapshot
          → if data: source=LIVE_SNAPSHOT, map via mapSnapshotToSignals()
      → if both fail: error state set
  → ComplianceVisibilityLayer mounts
      → useComplianceSnapshot.fetch()
          → GET /api/v1/gst/summary?period=YYYY-MM
          → GET /api/v1/tds/dashboard?quarter=Qx&financialYear=FYxx
```

### Flow 3 — SETU Dispatch

```
User selects signal in SignalDashboard
  → setSelected(signal)
SignalDetailEngine renders with selectedSignal
User clicks "SEND TO SETU"
  → handleSendToSetu()
  → client-side check: signal.signal_id exists?
      → no: FAILED immediately
  → setDispatchState(DISPATCHING)
  → POST /api/v1/signals/:signalId/dispatch
      Backend: runPipeline() → if ok: check SETU config → attempt dispatch
  → response handling:
      200 + dispatch_attempted=false → SUCCESS (pipeline proof)
      200 + dispatch_attempted=true  → SUCCESS (SETU confirmed)
      422 → FAILED (pipeline error)
      502 → TIMEOUT or FAILED (SETU error)
      ECONNABORTED → TIMEOUT
  → setDispatchState(SUCCESS|FAILED|TIMEOUT)
  → setDispatchResult(response data)
```

### Flow 4 — Trace Reconstruction

```
User clicks "Show Trace Chain" on SignalDashboard
  → setShowTrace(true)
  → SignalTracePanel mounts with signal prop
  → extracts traceId = signal.trace_id
  → if traceId: GET /api/v1/signals/trace/:traceId
      → response: { steps: [step1..step5], reconstructed_at }
      → renders TraceStep components (collapsible per step)
  → if no traceId: "snapshot-derived signal" message
```

---

## API Contracts (Frontend Perspective)

### Axios Instance Config (`api.js`)

```js
baseURL = resolveApiConfig().baseUrl
// Dev:  http://localhost:5000/api/v1
// Prod: same-origin /api/v1 (or VITE_API_URL override)

withCredentials: true
headers: { 'Content-Type': 'application/json' }
```

### Request Interceptor
Injects `Authorization: Bearer <token>` from `localStorage['artha_auth_token']` if present.

### Response Interceptor Error Handling

| HTTP Status | Action |
|------------|--------|
| 401 on `/auth/me` | Silent — used for boot check |
| 401 on other routes | Clear token + redirect `/login` + toast "Session expired" |
| 403 + `app_not_allowed` | Toast "Your account is not enabled for this app" |
| 400 with `errors[]` | Toast each error message |
| 409 | Toast message |
| 429 | Toast message |
| 503 | Toast "Service temporarily unavailable" |
| 500+ | Toast "Server error. Please try again later." |

---

## Failure Behavior

### Signal fetch fails
- `useSignals` catches error, sets `error: { message, status, url }`
- Dashboard/SignalDashboard render "SIGNAL FETCH FAILED" red card with exact details
- Refresh button re-calls `fetchSignals()`

### Backend unreachable
- `useRuntimeMode` catches health check failure → `BACKEND_UNAVAILABLE`
- Full-page unavailable state shown — no data attempted

### Empty signals
- `useSignals` returns `signals = []`, `source = EMPTY`
- `EmptySignalState` renders with actionable message
- No crash, no mock substitution

### Schema mismatch (signal missing fields)
- `mapDbSignalToDisplay()` / `mapDbSignal()` have defensive defaults:
  - `severity`: defaults to `'LOW'` if not in enum
  - `label`: falls back to `sig.type || 'Signal'`
  - `recommendation`: falls back to `'Review with finance owner.'`
- Signal renders with degraded display — never throws

### GST/TDS endpoint failure
- `useComplianceSnapshot` sets `errors.gst` / `errors.tds`
- `ErrorSurface` component renders with exact message
- Other panel data still shows if available

---

## Runtime States (Intelligence Components)

### RuntimeModeBanner states
```
CHECKING            → grey dot + "CHECKING CONNECTION" (pulsing)
BACKEND_CONNECTED   → green dot + "LIVE BACKEND SIGNALS"
BACKEND_DEGRADED    → amber dot + "SNAPSHOT FALLBACK ACTIVE"
BACKEND_UNAVAILABLE → red dot  + "BACKEND UNAVAILABLE"
MOCK_MODE           → purple dot + "MOCK DEVELOPMENT MODE"
```

### SignalDetailEngine dispatch states
```
IDLE        → "SEND TO SETU" button (default)
DISPATCHING → spinner + "Dispatching to SETU..."
SUCCESS     → green: "PIPELINE VALIDATED — SETU NOT CONFIGURED" or "SETU DISPATCH CONFIRMED"
FAILED      → red:   "SETU DISPATCH FAILED" + error + payload
TIMEOUT     → amber: "SETU UNAVAILABLE — REQUEST TIMED OUT" + payload attempted
```

---

## Auth Guard Logic

```js
// ProtectedRoute — any authenticated user
if (!isAuthenticated) → <Navigate to="/login" />

// RoleProtectedRoute — specific roles
const userRoles = user?.roles || [user?.role];
const hasAccess = allowedRoles.some(r => userRoles.includes(r));
if (!hasAccess) → "Access Denied" page (not redirect)

// PublicRoute — unauthenticated only
if (isAuthenticated) → <Navigate to="/dashboard" />
```

**Role-protected routes:**
- `/invoices/new`, `/invoices/:id/edit` → admin, accountant
- `/expenses/new`, `/expenses/approval` → admin, accountant
- `/accounts`, `/journal-entries`, `/ledger-integrity` → admin, accountant
- `/signals` → admin, accountant
- `/statements/upload` → admin, accountant
- `/settings/company`, `/settings/users` → admin only

---

## Environment Variables (Frontend)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | (auto) | Override full API base URL including `/api/v1` |
| `VITE_API_ORIGIN` | (auto) | Override just the origin (no path) |
| `VITE_MOCK_MODE` | unset | Set to `true` to force MOCK_MODE (dev only) |

**Auto-resolution logic (`api.js:resolveApiConfig()`):**
1. If `VITE_API_URL` set → use it
2. If `VITE_API_ORIGIN` set → `${VITE_API_ORIGIN}/api/v1`
3. If `localhost` → `http://localhost:5000/api/v1`
4. Otherwise → `${window.location.origin}/api/v1` (production same-origin)
