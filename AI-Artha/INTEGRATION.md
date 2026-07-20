# Integration Documentation — AI Content Platform

**System:** AI Content Platform  
**System ID:** ai-agent-aff6  
**Owner:** Ashmit Pandey (Platform Integration Lead)  
**Date:** 2026-07-04  
**Version:** 1.0.0  
**Status:** Complete

---

## 1. Integration Overview

The AI Content Platform integrates into the TANTRA ecosystem through a standardized platform contract. This document describes all integration points, APIs, and configuration requirements.

### 1.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TANTRA Ecosystem                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  Platform    │    │   Prompt     │    │  Moderation  │   │
│  │  (ai-agent)  │◄──►│   Runner     │◄──►│     UI       │   │
│  └──────┬───────┘    └──────────────┘    └──────────────┘   │
│         │                                                     │
│         ▼                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  Metadata    │    │  BHIV Core   │    │   Testing    │   │
│  │  Enrichment  │◄──►│              │◄──►│   & Docs     │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              AI Content Platform (ai-agent-aff6)             │
├─────────────────────────────────────────────────────────────┤
│  Platform Entry: POST /platform/execute                      │
│  Health Check:   GET /health                                 │
│  Contract:       PLATFORM_ENTRY v1.0.0 (frozen)              │
│  Database:       MongoDB Atlas                               │
│  Runtime:        Python 3.11 + FastAPI + Uvicorn             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Platform Entry Contract

### 2.1 Request Envelope

Every request to the platform MUST carry the following envelope:

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

### 2.2 Response Envelope

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

### 2.3 Status Values

| Status | Meaning | Usage |
|--------|---------|-------|
| `success` | Operation completed successfully | All successful responses |
| `error` | Operation failed with documented error | Failed operations |
| `partial` | Operation completed with degraded results | Partial success |
| `pending` | Operation is async, check status later | Async operations |
| `rejected` | Operation rejected by validation/moderation | Content moderation |

---

## 3. API Endpoints

### 3.1 Platform Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `POST /platform/execute` | POST | Module execution with trace | No |
| `POST /platform/validate-contract` | POST | Contract validation | No |
| `GET /platform/contract` | GET | Contract specification | No |
| `GET /platform/modules` | GET | Module registry | No |
| `GET /platform/schema` | GET | Schema version query | No |

### 3.2 Observability Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `GET /observability/events` | GET | Runtime events | No |
| `GET /observability/events/trace/{trace_id}` | GET | Trace-specific events | No |
| `GET /observability/health` | GET | Observability health | No |
| `GET /observability/stats/modules` | GET | Module statistics | No |

### 3.3 Bucket Validation Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `POST /bucket-validation/write-and-verify` | POST | Write/read proof | No |
| `GET /bucket-validation/status` | GET | Bucket status | No |
| `GET /bucket-validation/list-artifacts` | GET | Artifact listing | No |
| `GET /bucket-validation/read-artifact/{id}` | GET | Read with integrity check | No |

### 3.4 Health Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `GET /health` | GET | Application health | No |
| `GET /health/platform` | GET | Platform health checklist | No |
| `GET /health/detailed` | GET | Detailed health with observability | No |

### 3.5 Authentication Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `POST /users/login` | POST | User login (form data) | No |
| `POST /users/login-json` | POST | User login (JSON body) | No |
| `POST /users/register` | POST | User registration | No |
| `POST /users/refresh` | POST | Token refresh | No |
| `GET /users/profile` | GET | User profile | Yes |
| `POST /users/logout` | POST | Token invalidation | Yes |

### 3.6 Content Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `POST /upload` | POST | File upload | Yes |
| `GET /download/{id}` | GET | File download | Yes |
| `GET /stream/{id}` | GET | File streaming | Yes |
| `GET /contents` | GET | Content listing | Yes |
| `POST /generate-video` | POST | Video generation | Yes |

---

## 4. Module Registry

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

## 5. Trace Propagation

### 5.1 Middleware Stack

```
Request
  │
  ▼
[TracePropagationMiddleware] ← Outermost layer
  │ Generates trace_id if not provided
  │ Injects X-Trace-ID, X-Schema-Version, X-Execution-ID headers
  ▼
[GlobalAuthMiddleware]
  │ Enforces auth on protected endpoints
  ▼
[InputValidationMiddleware]
  │ 100MB body limit
  ▼
[RateLimitMiddleware]
  │ In-memory rate limiting
  ▼
[CORSMiddleware]
  │ CORS headers
  ▼
[Route Handler]
  │ Business logic
  ▼
Response
```

### 5.2 Trace Header Injection

Every response includes the following headers:

| Header | Description | Example |
|--------|-------------|---------|
| `X-Trace-ID` | Distributed trace identifier | `11111111-1111-1111-1111-111111111111` |
| `X-Schema-Version` | Active schema version | `1.0.0` |
| `X-Execution-ID` | Unique execution identifier | `22222222-2222-2222-2222-222222222222` |
| `X-Duration-Ms` | Execution duration in milliseconds | `12.34` |

---

## 6. Observability Integration

### 6.1 Event Structure

```json
{
  "trace_id": "string (UUID v4)",
  "execution_id": "string (UUID v4)",
  "module": "string",
  "action": "string",
  "status": "success | error | partial",
  "timestamp": "ISO 8601 UTC",
  "duration_ms": "number",
  "event_type": "platform_success | platform_error | platform_partial",
  "user_id": "string (optional)",
  "error": "string (optional)",
  "metadata": {}
}
```

### 6.2 Event Types

| Event Type | When Emitted |
|------------|--------------|
| `platform_success` | Successful platform execution |
| `platform_error` | Failed platform execution |
| `platform_partial` | Partially successful execution |

### 6.3 Integration with External Systems

| System | Configuration | Status |
|--------|---------------|--------|
| Sentry | `SENTRY_DSN` environment variable | Optional |
| PostHog | `POSTHOG_API_KEY` environment variable | Optional |

---

## 7. Bucket Storage Integration

### 7.1 Artifact Structure

```json
{
  "artifact_id": "string",
  "trace_id": "string (UUID v4)",
  "execution_id": "string (UUID v4)",
  "module": "string",
  "artifact_type": "output | metadata | log | provenance | validation_test",
  "content_hash": "string (SHA-256)",
  "created_at": "ISO 8601 UTC",
  "provenance": {
    "created_by": "string",
    "created_at": "ISO 8601 UTC",
    "chain": []
  }
}
```

### 7.2 Integrity Verification

1. **Write Proof**: Artifact written with SHA-256 content hash
2. **Read Proof**: Artifact read back and hash recalculated
3. **Verification**: Original hash matches recalculated hash
4. **Provenance**: Chain of custody recorded

---

## 8. Database Integration

### 8.1 MongoDB Collections

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| `users` | User accounts | username, email, password_hash |
| `content` | Uploaded content | title, file_path, user_id |
| `feedback` | User feedback | content_id, rating, sentiment |
| `scripts` | Generated scripts | content_id, script_text |
| `audit_logs` | Audit trail | action, user_id, timestamp |
| `analytics` | Usage analytics | event_type, count |
| `system_logs` | System logs | level, message, timestamp |
| `invitations` | User invitations | email, status, expires_at |
| `ratings` | Content ratings | content_id, score |

### 8.2 Connection Configuration

```python
# Environment Variable
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>

# Connection (automatic on import)
from core.mongodb import db
```

---

## 9. Authentication Integration

### 9.1 JWT Token Structure

```json
{
  "sub": "user_id",
  "exp": "timestamp",
  "iat": "timestamp",
  "type": "access | refresh"
}
```

### 9.2 Token Usage

```
Authorization: Bearer <access_token>
```

### 9.3 Token Refresh Flow

1. Client sends expired access_token
2. Server returns 401 Unauthorized
3. Client sends refresh_token to `POST /users/refresh`
4. Server returns new access_token + refresh_token

---

## 10. Error Handling

### 10.1 Error Response Contract

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

### 10.2 Error Code Reference

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

## 11. Configuration

### 11.1 Required Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MONGO_URI` | Yes | `mongodb://localhost:27017` | MongoDB connection string |
| `JWT_SECRET_KEY` | Yes | (generated) | JWT signing secret |

### 11.2 Optional Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PLATFORM_SCHEMA_VERSION` | No | `1.0.0` | Active schema version |
| `PLATFORM_STRICT_MODE` | No | `false` | Reject requests with missing optional fields |
| `BHIV_STORAGE_BACKEND` | Yes | `local` | Storage backend (local/s3) |
| `SENTRY_DSN` | No | (empty) | Sentry error tracking DSN |
| `POSTHOG_API_KEY` | No | (empty) | PostHog analytics key |

---

## 12. Deployment

### 12.1 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MONGO_URI="mongodb://localhost:27017"
export JWT_SECRET_KEY="your-secret-key"

# Start server
python -m uvicorn app.main:app --host 127.0.0.1 --port 9000
```

### 12.2 Production Deployment (Render)

```yaml
# render.yaml
services:
  - type: web
    name: ai-content-platform
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python scripts/start_server.py
    envVars:
      - key: MONGO_URI
        fromSecret: mongo-uri
      - key: JWT_SECRET_KEY
        fromSecret: jwt-secret-key
```

### 12.3 Docker Deployment

```bash
# Build image
docker build -t ai-content-platform .

# Run container
docker run -p 9000:9000 \
  -e MONGO_URI="mongodb+srv://..." \
  -e JWT_SECRET_KEY="..." \
  ai-content-platform
```

---

## 13. Integration Testing

### 13.1 Running Tests

```bash
# Collect evidence (server must be running)
python scripts/collect_evidence.py

# Verify deployment
python scripts/verify_deployment.py
```

### 13.2 Evidence Files

| File | Description |
|------|-------------|
| `evidence/day1a_contract_validation.json` | Platform contract validation |
| `evidence/day1a_platform_modules.json` | Module registry |
| `evidence/day1a_platform_schema.json` | Schema version |
| `evidence/day1b_runtime_flow.json` | End-to-end flow |
| `evidence/day1c_observability_events.json` | Runtime events |
| `evidence/day1c_observability_health.json` | Observability health |
| `evidence/day1c_module_stats.json` | Module statistics |
| `evidence/day2a_bucket_write_verify.json` | Bucket write/read proof |
| `evidence/day2a_bucket_status.json` | Bucket status |
| `evidence/day2a_bucket_artifacts.json` | Artifact listing |
| `evidence/day2b_health_verification.json` | Health verification |
| `evidence/day2b_platform_health.json` | Platform health |
| `evidence/day2b_auth_flow.json` | Authentication flow |
| `evidence/day2b_deterministic_execution.json` | Deterministic execution |
| `evidence/day2b_graceful_failure.json` | Graceful failure handling |
| `evidence/deployment_verification.json` | Deployment verification |

---

## 14. Support & Contact

| Role | Name | Responsibility |
|------|------|----------------|
| Platform Integration Lead | Ashmit Pandey | Platform contract, integration ownership |
| Prompt Runner | Siddhesh Narkar | Deterministic execution interface |
| Moderation UI | Hrujul Todankar | Application presentation |
| Metadata Enrichment | Vijay Dhawan | Tagging, structured metadata |
| UI/UX | Chandragupta | Production user experience |
| BHIV Core | Raj Prajapati | Governed application integration |
| Testing & Depository | Vinayak Tiwari | Validation, documentation |
| Functionality Testing | Akash | Runtime verification |

---

**Document Version:** 1.0.0  
**Last Updated:** 2026-07-04  
**Status:** Complete  
**Verified By:** Ashmit Pandey — Platform Integration Lead
