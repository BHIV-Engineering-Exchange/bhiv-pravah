# Critical Files — ARTHA BHIV Ecosystem Integration

## Why Each File Is Critical

### 1. capabilityRegistry.service.js
**Criticality:** HIGHEST
**Why:** This is the SINGLE SOURCE OF TRUTH for all capability contracts. Without this service, the entire governance system has no authoritative registry. Every policy decision, every route resolution, every capability check flows through this service. If this service fails or is tampered with, the entire authority boundary system collapses.

**Key Functions:**
- `loadContracts()` — Loads all contracts from JSON files
- `resolveRoute(method, path)` — Maps request to capability
- `canMutateCollection(capId, collection)` — Checks mutation authorization
- `verifyAllContracts()` — Verifies contract integrity via SHA-256 hashes

**Failure Impact:** Complete governance system failure

### 2. policyEngine.js
**Criticality:** HIGHEST
**Why:** This is the MISSING policy engine that enforces capability boundaries at the middleware level. Without this middleware, capabilities are declarative but not enforced. This is the gap identified in the review: "Capability contracts remain largely declarative rather than runtime-enforced."

**Key Functions:**
- `policyEnforcement` — Middleware that enforces boundaries on every request
- `guardCollection(req, collection)` — Controller-level collection authorization
- `validateCapabilityInput(capId, endpoint, data)` — Input schema validation

**Failure Impact:** Unauthorized operations allowed

### 3. provenanceChain.service.js
**Criticality:** HIGH
**Why:** Creates an immutable, append-only log of governance decisions. Each entry is hash-linked, making tampering detectable. Without this, there's no audit trail for governance decisions.

**Key Functions:**
- `append(event)` — Adds governance event to chain
- `verifyIntegrity()` — Walks chain verifying hash links
- `recordCapabilityDecision(decision)` — Records ALLOW/DENY decisions

**Failure Impact:** No governance audit trail

### 4. deterministicReplay.service.js
**Criticality:** HIGH
**Why:** Enables independent verification that execution produces deterministic outputs. This is the MISSING deterministic replay system identified in the gap analysis.

**Key Functions:**
- `recordExecution(execution)` — Captures input/output with hashes
- `verifyReplay(replayId, actualOutput)` — Compares output hashes
- `generateReplayProof(replayId)` — Creates verification proof

**Failure Impact:** Cannot verify execution determinism

### 5. server.js
**Criticality:** HIGH
**Why:** The integration point where all services are initialized and middleware is mounted. Changes here affect the entire application. The modifications must maintain backward compatibility with all existing endpoints.

**Key Changes:**
- Added BHIV ecosystem service imports
- Added service initialization block
- Added policy enforcement middleware
- Added governance routes
- Added startup logging
- Added deployment evidence recording

**Failure Impact:** Application startup failure or backward incompatibility

### 6. capability_route_map.json
**Criticality:** MEDIUM
**Why:** Maps API routes to capabilities. If this mapping is incorrect, requests will be routed to wrong capabilities or blocked entirely.

**Key Changes:**
- Added governance route mapping
- Updated version to 1.1.0

**Failure Impact:** Incorrect capability resolution

## Files That Must NOT Be Modified

These files contain existing functionality that must remain unchanged:

1. `backend/src/middleware/auth.js` — JWT authentication
2. `backend/src/middleware/security.js` — Rate limiting, helmet
3. `backend/src/middleware/authorityBoundary.js` — Existing authority enforcement
4. `backend/src/middleware/monitoring.js` — Request logging
5. `backend/src/routes/ledger.routes.js` — All existing route files
6. `backend/src/services/ledger.service.js` — All existing service files
7. `backend/src/models/JournalEntry.js` — All existing model files

## Backward Compatibility Verification

All existing endpoints remain unchanged:
- `/api/v1/ledger/*` — Ledger operations
- `/api/v1/invoices/*` — Invoice operations
- `/api/v1/expenses/*` — Expense operations
- `/api/v1/gst/*` — GST operations
- `/api/v1/tds/*` — TDS operations
- `/api/v1/reports/*` — Financial reports
- `/api/v1/signals/*` — Compliance signals
- `/api/v1/trace/*` — Trace operations
- `/api/v1/banking/*` — Banking operations
- `/api/v1/audit/*` — Audit trail
- `/api/v1/compliance/*` — Compliance operations
- `/api/v1/settings/*` — Settings
- `/api/v1/users/*` — User management
- `/api/v1/runtime/*` — Runtime status
- `/api/v1/tantra/*` — TANTRA integration
- All health endpoints (`/health`, `/ready`, `/live`)
- All auth endpoints (`/api/v1/auth/*`)
