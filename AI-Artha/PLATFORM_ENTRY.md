# PLATFORM_ENTRY.md — Canonical Application Entry Contract

**Schema Version:** 1.0.0  
**Status:** FROZEN  
**Last Updated:** 2026-07-04  
**Owner:** Ashmit Pandey — Platform Integration Lead

---

## 1. System Identity

| Field | Value |
|-------|-------|
| System Name | AI Content Platform |
| System ID | ai-agent-aff6 |
| Role | Platform composition, adapters, integration ownership |
| Parent Ecosystem | TANTRA |
| Entry Point | `POST /platform/execute` |
| Health Check | `GET /health` |
| Contract Schema | `PLATFORM_ENTRY v1.0.0` |
| Schema Version | 1.0.0 (semver) |

---

## 2. Platform Request Contract

Every request to the AI Content Platform MUST carry the following envelope:

### 2.1 Required Request Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `X-Trace-ID` | string (UUID v4) | YES | Unique trace identifier for distributed tracing |
| `X-Schema-Version` | string | YES | Schema version (e.g., `1.0.0`) |
| `X-Request-ID` | string (UUID v4) | YES | Unique request identifier |
| `Authorization` | string | Conditional | Bearer token for authenticated endpoints |
| `Content-Type` | string | YES | `application/json` for POST/PUT |

### 2.2 Required Request Body (POST /platform/execute)

```json
{
  "trace_id": "string (UUID v4)",
  "schema_version": "1.0.0",
  "module": "string",
  "action": "string",
  "payload": {},
  "metadata": {
    "source": "string",
    "timestamp": "ISO 8601",
    "user_id": "string (optional)"
  }
}
```

### 2.3 Required Response Envelope

```json
{
  "trace_id": "string",
  "schema_version": "1.0.0",
  "status": "success | error | partial | pending | rejected",
  "module": "string",
  "execution_id": "string (UUID v4)",
  "timestamp": "ISO 8601 UTC",
  "duration_ms": "number",
  "data": {},
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

### 2.4 Status Values

| Status | Meaning | Usage |
|--------|---------|-------|
| `success` | Operation completed successfully | All successful responses |
| `error` | Operation failed with documented error | Failed operations |
| `partial` | Operation completed with degraded results | Partial success |
| `pending` | Operation is async, check status later | Async operations |
| `rejected` | Operation rejected by validation/moderation | Content moderation |

---

## 3. Module Registry

| Module ID | Module Name | Owner | Responsibility |
|-----------|-------------|-------|----------------|
| `platform` | AI Content Platform | Ashmit Pandey | Platform composition, adapters |
| `prompt_runner` | Prompt Runner | Siddhesh Narkar | Deterministic execution interface |
| `moderation` | Moderation UI | Hrujul Todankar | Application presentation, moderation |
| `metadata` | Metadata Enrichment | Vijay Dhawan | Tagging, structured metadata |
| `ui` | UI/UX | Chandragupta | Production user experience |
| `bhiv_core` | BHIV Core | Raj Prajapati | Governed application integration |
| `testing` | Testing & Depository | Vinayak Tiwari | Validation, documentation, evidence |
| `verification` | Functionality Testing | Akash | Runtime verification, regression |

---

## 4. Execution Flow

```
User Request
  |
  v
[TracePropagationMiddleware] --- trace_id generated/injected, schema validated
  |
  v
[Platform Entry] --- POST /platform/execute
  |
  v
[Prompt Runner] --- deterministic execution, status tracked
  |
  v
[Moderation] --- content validation, approval/rejection
  |
  v
[Metadata] --- tagging, enrichment, structured output
  |
  v
[UI Response] --- formatted response, trace_id preserved
```

Every stage MUST:
- Preserve `trace_id` from original request
- Return structured response matching Section 2.3
- Report deterministic status values (Section 2.4)
- Handle failures using documented error responses (Section 5)

---

## 5. Error Response Contract

```json
{
  "trace_id": "string",
  "schema_version": "1.0.0",
  "status": "error",
  "module": "string",
  "execution_id": "string (UUID v4)",
  "timestamp": "ISO 8601 UTC",
  "duration_ms": "number",
  "error": {
    "code": "VALIDATION_ERROR | AUTH_ERROR | TIMEOUT | INTERNAL_ERROR | MODULE_ERROR | WRITE_FAILED | READ_FAILED",
    "message": "Human-readable error description",
    "details": {
      "field": "string (optional)",
      "reason": "string"
    }
  }
}
```

### 5.1 Error Code Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `AUTH_ERROR` | 401 | Authentication required or failed |
| `MODULE_NOT_FOUND` | 404 | Requested module not registered |
| `TIMEOUT` | 408 | Operation timed out |
| `WRITE_FAILED` | 500 | Bucket/storage write failed |
| `READ_FAILED` | 500 | Bucket/storage read failed |
| `MODULE_ERROR` | 500 | Module execution failed |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## 6. Observability Contract

Every execution MUST produce:

| Field | Source | Description |
|-------|--------|-------------|
| `trace_id` | Request header | Distributed trace identifier |
| `execution_id` | Platform | Unique execution identifier |
| `module` | Request body | Module performing work |
| `action` | Request body | Action being performed |
| `status` | Response | Deterministic status value |
| `duration_ms` | Middleware | Wall-clock execution time |
| `timestamp` | Middleware | ISO 8601 UTC execution timestamp |
| `event_type` | Platform | `execution_started`, `execution_completed`, `execution_failed` |

### 6.1 Event Types

| Event Type | When Emitted |
|------------|--------------|
| `platform_execution_started` | Request received by platform |
| `platform_execution_completed` | Request processed successfully |
| `platform_execution_failed` | Request processing failed |

### 6.2 Observability Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/observability/events` | GET | List recent execution events |
| `/observability/events/trace/{trace_id}` | GET | Events for specific trace |
| `/observability/stats/modules` | GET | Per-module execution statistics |
| `/observability/health` | GET | Observability system health |

---

## 7. Bucket Storage Contract

Artifacts written through the platform layer MUST include:

| Field | Type | Description |
|-------|------|-------------|
| `artifact_id` | string | Unique artifact identifier |
| `trace_id` | string | Trace from originating request |
| `execution_id` | string | Execution that produced artifact |
| `module` | string | Module that produced artifact |
| `artifact_type` | string | `output`, `metadata`, `log`, `provenance`, `validation_test` |
| `content_hash` | string | SHA-256 of artifact content |
| `created_at` | ISO 8601 | Creation timestamp |
| `provenance` | object | Chain of custody information |

### 7.1 Bucket Validation Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/bucket-validation/write-and-verify` | POST | Write + read proof with integrity check |
| `/bucket-validation/status` | GET | Bucket storage configuration |
| `/bucket-validation/list-artifacts` | GET | List stored artifacts |
| `/bucket-validation/read-artifact/{id}` | GET | Read artifact with integrity verification |

---

## 8. Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MONGO_URI` | Yes | `mongodb://localhost:27017` | MongoDB connection string |
| `JWT_SECRET_KEY` | Yes | (generated) | JWT signing secret |
| `PLATFORM_SCHEMA_VERSION` | No | `1.0.0` | Active schema version |
| `PLATFORM_STRICT_MODE` | No | `false` | Reject requests with missing optional fields |
| `BHIV_STORAGE_BACKEND` | Yes | `local` | Storage backend (local/s3) |
| `SENTRY_DSN` | No | (empty) | Sentry error tracking DSN |
| `POSTHOG_API_KEY` | No | (empty) | PostHog analytics key |

---

## 9. Deployment Verification Checklist

### Pre-Deployment
- [ ] MongoDB Atlas cluster accessible
- [ ] `.env` file configured with all required variables
- [ ] `pymongo[srv]` installed
- [ ] No hardcoded credentials in source code
- [ ] All environment variables set via secrets manager

### Startup Validation
- [ ] `core/mongodb.py` connects to MongoDB on import
- [ ] `core/database.py` creates indexes via `ensure_indexes()`
- [ ] 9 collections created: users, content, feedback, scripts, audit_logs, analytics, system_logs, invitations, ratings
- [ ] All routers loaded (71+ routes)
- [ ] TracePropagationMiddleware active
- [ ] No Redis/SQLite/psycopg2 warnings

### Health Endpoints
- [ ] `GET /health` returns `{"status": "healthy"}`
- [ ] `GET /health/platform` returns all checks `true`
- [ ] `GET /observability/health` returns 200 OK
- [ ] `GET /bucket-validation/status` returns 200 OK

### Authentication
- [ ] Demo user created with bcrypt password
- [ ] `POST /users/login` returns JWT tokens
- [ ] Authenticated endpoints reject requests without token (401)
- [ ] Authenticated endpoints accept requests with valid token

### Platform Contract
- [ ] `POST /platform/execute` accepts valid contract
- [ ] `POST /platform/validate-contract` validates request structure
- [ ] `GET /platform/modules` lists registered modules
- [ ] Every response carries `X-Trace-ID`, `X-Schema-Version`, `X-Execution-ID` headers
- [ ] trace_id preserved across all response headers

### Observability
- [ ] Runtime events recorded in-memory + daily log files
- [ ] `GET /observability/events` returns event list
- [ ] `GET /observability/stats/modules` returns module statistics
- [ ] Events include: trace_id, module, action, status, duration_ms, timestamp

### Bucket Validation
- [ ] `POST /bucket-validation/write-and-verify` returns write proof + read proof
- [ ] `GET /bucket-validation/list-artifacts` lists stored artifacts
- [ ] `GET /bucket-validation/read-artifact/{id}` reads and verifies integrity
- [ ] Content hash SHA-256 verification on read-back

### Backward Compatibility
- [ ] All 9-step workflow endpoints preserved
- [ ] Auth endpoints (`/users/login`, `/users/register`) unchanged
- [ ] Upload, download, stream endpoints functional
- [ ] Analytics, feedback, tag recommendation endpoints functional

---

## 10. Canonical Classification

| Classification | Value |
|---------------|-------|
| Phase | IV — Production Transition |
| Category | Infrastructure / Platform Integration |
| Risk Level | Low |
| Backward Compatible | Yes |
| Breaking Changes | None |
| New Dependencies | `pymongo[srv]` |
| Removed Dependencies | `psycopg2-binary`, `sqlmodel`, `redis`, `alembic` |
| Integration Type | Platform composition adapter |
| Routing | All requests via `POST /platform/execute` |
| Observability | InsightFlow-compatible event emission |
| Storage | BHIV Bucket with provenance tracking |

---

## 11. Required Routing

| Route | Method | Purpose |
|-------|--------|---------|
| `POST /platform/execute` | POST | Module execution with trace |
| `POST /platform/validate-contract` | POST | Contract validation |
| `GET /platform/contract` | GET | Contract specification |
| `GET /platform/modules` | GET | Module registry |
| `GET /observability/events` | GET | Runtime events |
| `GET /observability/events/trace/{trace_id}` | GET | Trace-specific events |
| `GET /observability/health` | GET | Observability health |
| `GET /observability/stats/modules` | GET | Module statistics |
| `POST /bucket-validation/write-and-verify` | POST | Write/read proof |
| `GET /bucket-validation/status` | GET | Bucket status |
| `GET /bucket-validation/list-artifacts` | GET | Artifact listing |
| `GET /bucket-validation/read-artifact/{id}` | GET | Read with integrity check |
| `GET /health` | GET | Application health |
| `GET /health/platform` | GET | Platform health checklist |
| `GET /health/detailed` | GET | Detailed health with observability |

---

**Contract Status:** FROZEN  
**Version:** 1.0.0  
**Last Verified:** 2026-07-04  
**Verified By:** Ashmit Pandey — Platform Integration Lead
