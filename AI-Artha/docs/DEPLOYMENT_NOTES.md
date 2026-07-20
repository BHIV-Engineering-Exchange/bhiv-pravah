# DEPLOYMENT_NOTES.md
# Phase 6 — Deployment Notes
# ARTHA v0.1 | Frontend + Backend

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NODE_ENV` | Yes | `development` | `development` / `production` / `test` |
| `PORT` | No | `5000` | HTTP server port |
| `MONGODB_URI` | Yes | — | MongoDB Atlas connection string |
| `MONGODB_TEST_URI` | Test only | — | Separate test DB URI |
| `JWT_SECRET` | Yes | — | Min 32 chars. Signs all access tokens. |
| `JWT_EXPIRES_IN` | No | `7d` | Token lifetime |
| `HMAC_SECRET` | Yes | — | Min 32 chars. Signs ledger hash chain. Changing this breaks existing chain. |
| `APP_URL` | No | `http://localhost:5000` | This API's public base |
| `FRONTEND_URL` | No | `http://localhost:5173` | SPA origin (used in CORS + redirects) |
| `CORS_ORIGIN` | No | `http://localhost:5173` | Browser-accessible origin for CORS |
| `SETU_ENABLED` | No | `false` | Set `true` to enable real SETU dispatch |
| `SETU_BASE_URL` | SETU only | — | SETU endpoint base URL |
| `SETU_API_KEY` | SETU only | — | SETU Bearer token |
| `SETU_TIMEOUT_MS` | No | `5000` | SETU request timeout in milliseconds |
| `RATE_LIMIT_WINDOW_MS` | No | `900000` | Rate limit window (15 min) |
| `RATE_LIMIT_MAX` | No | `100` | Max requests per window |
| `STORAGE_TYPE` | No | `local` | `local` or `s3` for receipt uploads |
| `AWS_BUCKET_NAME` | S3 only | — | S3 bucket for receipt storage |
| `AWS_REGION` | S3 only | — | AWS region |
| `AWS_ACCESS_KEY_ID` | S3 only | — | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | S3 only | — | AWS secret |
| `INSIGHTCORE_ENABLED` | No | `false` | InsightCore telemetry |
| `LOG_LEVEL` | No | `debug` | `error` / `warn` / `info` / `debug` |

**Critical:** `HMAC_SECRET` must never change in production. Changing it invalidates all existing ledger hashes. Store it in a secret manager.

### Frontend (`frontend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | No | (auto) | Full API base URL e.g. `https://api.artha.com/api/v1` |
| `VITE_API_ORIGIN` | No | (auto) | API origin only e.g. `https://api.artha.com` |
| `VITE_MOCK_MODE` | No | unset | Set `true` to force mock mode (dev only) |

**Auto-resolution:** If neither `VITE_API_URL` nor `VITE_API_ORIGIN` is set:
- `localhost` → `http://localhost:5000/api/v1`
- Production → `${window.location.origin}/api/v1`

---

## Startup Instructions

### Development (Local)

```bash
# Terminal 1 — Backend
cd backend
npm install
cp .env.example .env           # fill in MONGODB_URI, JWT_SECRET, HMAC_SECRET
npm run dev                    # nodemon src/server.js → port 5000

# Terminal 2 — Seed database (first time only)
cd backend
node scripts/seed.js           # creates CompanySettings + 33 Chart of Accounts + sample data
node scripts/seed-tds.js       # creates 6 TDS sample entries for Q4 FY2025-26

# Terminal 3 — Frontend
cd frontend
npm install
npm run dev                    # vite → http://localhost:5173
```

**Verify health:**
```bash
curl http://localhost:5000/health
# → {"success":true,"message":"ARTHA API is running","version":"0.1.0",...}

curl http://localhost:5000/status
# → {"success":true,"data":{"database":"connected","redis":"disabled",...}}
```

### Production (Docker)

```bash
# Full production stack
docker-compose -f docker-compose.prod.yml up -d

# Or development stack
docker-compose -f docker-compose.dev.yml up -d
```

**Production Docker images:**
- Backend: `backend/Dockerfile.prod` — Node 18 Alpine, non-root user
- Frontend: `frontend/Dockerfile.prod` — Vite build → Nginx static serve

### Render.com Deployment

See `backend/render.yaml` for Render service definitions.
Required env vars in Render dashboard: `MONGODB_URI`, `JWT_SECRET`, `HMAC_SECRET`, `FRONTEND_URL`, `CORS_ORIGIN`.

---

## Frontend/Backend Compatibility Notes

| Frontend version | Backend version | Compatible |
|-----------------|-----------------|-----------|
| 1.0.0 | 0.1.0 | ✓ Current |

**API version:** All routes are under `/api/v1/`. No versioned breaking changes in v0.1.

**CORS:** Backend uses manual CORS middleware (not the `cors` npm package despite it being installed). Origins are controlled via `CORS_ORIGIN` / `CORS_ALLOWED_ORIGINS` env vars + always allows `localhost:5173` unless `ALLOW_LOCALHOST_CORS=false`.

**Auth token:** Frontend stores JWT in `localStorage['artha_auth_token']`. Token lifetime: 7 days (configurable via `JWT_EXPIRES_IN`). No refresh token — user must re-login after expiry.

**File uploads:** Receipts stored in `backend/uploads/receipts/` (local mode) or S3. Frontend uploads via multipart form. Max 5 receipts per expense. Max file size 10MB (Express JSON limit).

---

## Known Runtime Dependencies

### Required (app will not start without these)

| Dependency | Version | Why |
|------------|---------|-----|
| MongoDB Atlas | 7+ | Primary database. Must be accessible at `MONGODB_URI`. |
| Node.js | 18+ | ESM modules (`type: module`), `randomUUID()` from crypto |

### Optional (app degrades gracefully without these)

| Dependency | Effect if absent |
|------------|-----------------|
| Redis | Caching disabled. All cache reads return null. App continues without performance optimization. |
| MongoDB Replica Set | Transactions disabled. `withTransaction()` runs without ACID guarantees. Logged as warning. |
| SETU endpoint | Signals persisted locally. Dispatch returns payload proof only (not HTTP dispatch). |
| Tesseract.js | OCR disabled. Receipt scanning unavailable. Other expense features unaffected. |

### MongoDB Atlas Setup

1. Create free M0 cluster at `cloud.mongodb.com`
2. Create database user with read/write access
3. Whitelist IP (or allow all: `0.0.0.0/0` for dev)
4. Get connection string → set as `MONGODB_URI`
5. Connection string format: `mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?appName=Artha`

**Note on transactions:** Free M0 clusters are replica sets → transactions available.

### Redis Setup (optional)

See `docs/REDIS-SETUP.md`. If Redis is unavailable, the app logs one warning and continues with zero-cache mode. No feature is blocked.

---

## Database Seeding (Required for GST + TDS)

```bash
cd backend

# Required: CompanySettings + Chart of Accounts + sample invoices/expenses
node scripts/seed.js

# Required for TDS dashboard: 6 TDS entries for Q4 FY2025-26
node scripts/seed-tds.js

# Verify integrity after seeding
node scripts/verify-integrity.js
```

**What seed.js creates:**
- `CompanySettings` with `_id: 'company_settings'`, sample GSTIN, Karnataka state
- 33 Chart of Accounts (Assets, Liabilities, Equity, Income, Expenses)
- Sample invoices with journal entries
- Sample expenses with ledger entries

**Warning:** Running `seed.js` again does not duplicate — it uses upsert patterns for most records.

---

## First-Run Checklist

```
□ MONGODB_URI set and cluster reachable
□ JWT_SECRET set (min 32 chars)
□ HMAC_SECRET set (min 32 chars)
□ node scripts/seed.js ran successfully
□ node scripts/seed-tds.js ran successfully
□ GET /health returns 200
□ GET /status returns database: "connected"
□ Login works at /login
□ Dashboard loads at /dashboard (RuntimeModeBanner shows green)
□ GET /api/v1/signals/snapshot returns cashFlow value
□ Signals page at /signals loads (admin/accountant role required)
```

---

## Learning Kit

### Recommended Keywords
- "React runtime state architecture"
- "Production frontend observability"
- "Distributed system failure surfaces"
- "API contract testing frontend backend"
- "Traceability UI systems"
- "Operational dashboard design"

### Recommended Reading
- React docs: `useEffect`, `useCallback`, `useMemo` (hooks used throughout)
- Axios error handling docs: interceptors + error shapes
- OpenTelemetry tracing concepts: trace_id, span chains
- REST API contract validation: request/response schema validation
- System observability patterns: health checks, degraded modes, circuit breakers

### LLM Study Prompts
- "Teach me deterministic runtime mode design for React systems."
- "Teach me API contract verification between frontend and backend."
- "Explain operational failure surfaces in production dashboards."
- "Explain trace visualization systems for ledger-backed intelligence platforms."
