# RUNTIME_MODES.md
# Phase 4 — Production Mode Closure
# ARTHA v0.1 | Zero Demo Ambiguity

---

## Governing Rule

Mode is always visible. No hidden mock. No silent fallback.
Every state transition is deterministic and observable.

---

## The 4 Runtime Modes

### MODE 1 — BACKEND_CONNECTED

**Label in UI:** `● LIVE BACKEND SIGNALS` (green dot, pulsing)
**Color:** `text-success / bg-success/10 / border-success/30`

**Trigger condition:**
```
1. GET /health (axios, no auth, 5s timeout) → 200 OK
2. GET /api/v1/signals/snapshot (api, with Bearer token, 5s timeout) → 200 OK
   OR → 401 (token expired — still connected, auth issue only)
```

**What renders:**
- `RuntimeModeBanner`: green "● LIVE BACKEND SIGNALS · checked HH:MM:SS"
- `useSignals.fetchSignals()` runs immediately
- Attempt 1: `GET /api/v1/signals?limit=50` → if list.length > 0 → LIVE_LIST source
- Attempt 2 (fallback): `GET /api/v1/signals/snapshot` → LIVE_SNAPSHOT source
- Signal cards render with real DB data
- SignalDetailEngine active — SETU dispatch available
- ComplianceVisibilityLayer loads GST + TDS from real endpoints

**Deterministic proof:**
```bash
curl http://localhost:5000/health
# → {"success":true,"message":"ARTHA API is running",...}
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/v1/signals/snapshot
# → {"success":true,"data":{"source":"ledger-only","cashFlow":"..."},...}
```

---

### MODE 2 — BACKEND_DEGRADED

**Label in UI:** `● SNAPSHOT FALLBACK ACTIVE` (amber dot, pulsing)
**Color:** `text-warning / bg-warning/10 / border-warning/30`

**Trigger condition:**
```
1. GET /health → 200 OK  (backend is up)
2. GET /api/v1/signals/snapshot → 500 / 503 / ECONNABORTED (signals failing, not 401)
```

**What renders:**
- `RuntimeModeBanner`: amber "● SNAPSHOT FALLBACK ACTIVE · checked HH:MM:SS"
- `useSignals.fetchSignals()` still runs
- If both signal endpoints fail → error state surfaces: "SIGNAL FETCH FAILED" red card
  with exact URL + HTTP status (e.g., `GET /api/v1/signals → HTTP 500: Internal Server Error`)
- Empty signal list with Refresh button
- ComplianceVisibilityLayer still attempts GST + TDS — may show partial data or errors

**Deterministic proof:**
Backend signals working but snapshot 500:
```
useRuntimeMode.check():
  GET /health → 200 ✓
  GET /signals/snapshot → 500 ✗
  → mode = BACKEND_DEGRADED
```

---

### MODE 3 — BACKEND_UNAVAILABLE

**Label in UI:** `● BACKEND UNAVAILABLE` (red dot, solid)
**Color:** `text-destructive / bg-destructive/10 / border-destructive/30`

**Trigger condition:**
```
1. GET /health → ECONNREFUSED / ENOTFOUND / timeout / 5xx
   (any network-level failure OR server error on health endpoint)
```

**What renders:**
- `RuntimeModeBanner`: red "● BACKEND UNAVAILABLE · checked HH:MM:SS"
- Full-page `BackendUnavailableState`:
  - `WifiOff` icon
  - "Cannot reach the Artha API. Ensure backend is running on port 5000."
  - "Retry Connection" button → calls `recheck()` → re-runs health check
- NO signals fetched
- NO mock data shown
- NO crash

**Deterministic proof:**
```bash
# Kill backend process, then:
# useRuntimeMode.check() → axios.get('/health') → ECONNREFUSED
# → mode = BACKEND_UNAVAILABLE
# UI: WifiOff + "Retry Connection"
# Click retry → recheck() → same ECONNREFUSED → stays BACKEND_UNAVAILABLE
```

**Recovery:**
Start backend → click "Retry Connection" → GET /health → 200 → mode transitions to BACKEND_CONNECTED.

---

### MODE 4 — MOCK_MODE

**Label in UI:** `● MOCK DEVELOPMENT MODE` (purple dot, solid)
**Color:** `text-secondary / bg-secondary/10 / border-secondary/30`

**Trigger condition:**
```
VITE_MOCK_MODE=true in frontend/.env
```

**What renders:**
- `RuntimeModeBanner`: purple "● MOCK DEVELOPMENT MODE"
- Card: "MOCK DEVELOPMENT MODE — Set VITE_MOCK_MODE=false in frontend/.env to connect to real backend."
- No signals fetched
- No health check attempted
- No data of any kind shown

**Hard guarantee:** Mock mode ONLY activates when `VITE_MOCK_MODE=true` is explicitly set.
It is NEVER triggered by network failure, empty data, or backend errors.
Network failure → BACKEND_UNAVAILABLE (not mock).
Empty signals → empty state (not mock).

**Default in `.env`:**
```
VITE_MOCK_MODE is not set → resolves to undefined → mock mode NOT active
```

---

### TRANSIENT STATE — CHECKING

**Label in UI:** `● CHECKING CONNECTION` (grey dot, pulsing)
**Duration:** Until `check()` resolves (typically < 2s on local)

**Trigger:** App boot or manual `recheck()` call.

**What renders:**
- `RuntimeModeBanner`: grey pulsing "● CHECKING CONNECTION"
- `Loading.Page` spinner
- Nothing else rendered

---

## State Transition Diagram

```
App Boot / recheck()
        ↓
   [CHECKING]
        ↓
   GET /health ──────────────────────────────── fails (ECONNREFUSED/timeout/5xx)
        │                                                ↓
        │ 200 OK                               [BACKEND_UNAVAILABLE]
        ↓                                                ↑
   GET /signals/snapshot ──── fails (not 401)            │
        │                         ↓                  retry()
        │ 200 OK or 401    [BACKEND_DEGRADED]             │
        ↓                                                 │
  [BACKEND_CONNECTED] ────────────────────────────────────┘

  OR (overrides all above):
  VITE_MOCK_MODE=true → [MOCK_MODE] (no network calls)
```

---

## Code Locations

| Component | File | Responsibility |
|-----------|------|----------------|
| `useRuntimeMode` | `frontend/src/hooks/useRuntimeMode.js` | Mode detection logic |
| `RuntimeModeBanner` | `frontend/src/components/intelligence/RuntimeModeBanner.jsx` | Always-visible mode indicator |
| `RUNTIME_MODES` enum | `frontend/src/hooks/useRuntimeMode.js` | 5 constants: CHECKING, BACKEND_CONNECTED, BACKEND_DEGRADED, BACKEND_UNAVAILABLE, MOCK_MODE |
| `MODE_META` map | `frontend/src/hooks/useRuntimeMode.js` | Label + color for each mode |
| Dashboard render branches | `frontend/src/pages/dashboard/FinancialIntelligenceDashboard.jsx` | Renders correct view per mode |
| Signal Dashboard branches | `frontend/src/pages/compliance/SignalDashboard.jsx` | Same 4-way switch |

---

## Mock Prevention Checklist

| Check | Status |
|-------|--------|
| No mock data array in production code paths | ✓ Verified — no static mock arrays |
| MOCK_MODE only from explicit VITE_MOCK_MODE=true | ✓ Verified — `useRuntimeMode.js` line 1 check |
| Network failure → BACKEND_UNAVAILABLE (not mock) | ✓ Verified — catch block sets BACKEND_UNAVAILABLE |
| Empty signals → empty state (not mock) | ✓ Verified — EmptySignalState component, no fallback |
| Mode always rendered (RuntimeModeBanner) | ✓ Verified — renders in all branches before any data |
| Raw payload exposed for inspection | ✓ Verified — `rawPayload` collapsible in both pages |

---

## Per-Mode UI Summary

| Mode | Banner Color | Data Source | Dispatch Available | Signals |
|------|-------------|------------|-------------------|---------|
| BACKEND_CONNECTED | Green | Real DB + Snapshot | Yes | Full |
| BACKEND_DEGRADED | Amber | None (endpoints fail) | No | Error shown |
| BACKEND_UNAVAILABLE | Red | None | No | None |
| MOCK_MODE | Purple | None | No | None |
| CHECKING | Grey | None | No | Loading |
