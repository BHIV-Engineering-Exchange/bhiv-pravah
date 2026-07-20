# Backend API Documentation

This file documents the current backend API surfaces:

- Gateway (`:8000`)
- Agent (`:9000`)
- LangGraph (`:9001`)

## How beginners should use this file

Follow this sequence:

1. Start all backend services.
2. Open `/docs` for each service to view live schemas.
3. Read the "Authentication" section below.
4. Test one endpoint from each group: health, auth, jobs, candidates.
5. Test one end-to-end flow:
   - candidate apply
   - recruiter/client request docs
   - candidate upload docs
   - fetch portal notifications

For exact request/response schemas, always use each service OpenAPI at `/docs`.

## Base URLs

- Gateway: `http://localhost:8000`
- Agent: `http://localhost:9000`
- LangGraph: `http://localhost:9001`

## Authentication

Most protected routes accept:

```http
Authorization: Bearer <token>
```

Token types in use:

- API key token (`API_KEY_SECRET`)
- JWT tokens from login endpoints

## Gateway API (`backend/services/gateway/app/main.py`)

### Core and monitoring

- `GET /`
- `GET /health`
- `GET /docs`
- `GET /openapi.json`
- `GET /metrics`
- `GET /health/detailed`
- `GET /metrics/dashboard`
- `GET /v1/test-candidates`

### Job management

- `POST /v1/jobs`
- `GET /v1/jobs`
- `GET /v1/jobs/autocomplete`
- `GET /v1/jobs/skills/autocomplete`
- `GET /v1/jobs/locations/autocomplete`
- `GET /v1/jobs/{job_id}`
- `PUT /v1/jobs/{job_id}`
- `DELETE /v1/jobs/{job_id}`
- `POST /v1/jobs/{job_id}/shortlist`
- `POST /v1/jobs/{job_id}/reject`

### Candidate management

- `GET /v1/candidates`
- `GET /v1/candidates/stats`
- `GET /v1/candidates/autocomplete`
- `GET /v1/candidates/search`
- `GET /v1/candidates/job/{job_id}`
- `GET /v1/candidates/{candidate_id}`
- `POST /v1/candidates/parse-pdf`
- `POST /v1/candidates/check-duplicates`
- `POST /v1/candidates/bulk`
- `GET /v1/notifications/history/{candidate_id}`

### Matching

- `GET /v1/match/{job_id}/top`
- `POST /v1/match/batch`

### Assessment and operations

- `POST /v1/feedback`
- `GET /v1/feedback`
- `GET /v1/interviews`
- `POST /v1/interviews`
- `POST /v1/offers`
- `GET /v1/offers`
- `GET /v1/database/schema`
- `GET /v1/reports/job/{job_id}/export.csv`

### Client APIs

- `POST /v1/client/register`
- `POST /v1/client/login`
- `GET /v1/client/profile`
- `GET /v1/client/by-connection/{connection_id}`
- `GET /v1/client/connected-recruiter`
- `GET /v1/client/connection-events`
- `GET /v1/client/jobs`
- `GET /v1/client/stats`
- `GET /v1/client/applicants`
- `POST /v1/client/applications/{application_id}/required-documents`
- `GET /v1/client/applications/{application_id}/documents/{document_type}`

### Recruiter APIs

- `GET /v1/recruiter/connection-events`
- `POST /v1/recruiter/confirm-connection`
- `POST /v1/recruiter/disconnect`
- `GET /v1/recruiter/current-connection`
- `GET /v1/recruiter/jobs`
- `GET /v1/recruiter/applicants`
- `POST /v1/recruiter/applications/{application_id}/required-documents`
- `GET /v1/recruiter/applications/{application_id}/documents/{document_type}`
- `GET /v1/recruiter/stats`

### Connection utility

- `POST /v1/connection/health-check`

### Security testing and CSP

- `GET /v1/security/rate-limit-status`
- `GET /v1/security/blocked-ips`
- `POST /v1/security/test-input-validation`
- `POST /v1/security/validate-email`
- `POST /v1/security/test-email-validation`
- `POST /v1/security/validate-phone`
- `POST /v1/security/test-phone-validation`
- `GET /v1/security/test-headers`
- `GET /v1/security/security-headers-test`
- `POST /v1/security/penetration-test`
- `GET /v1/security/test-auth`
- `GET /v1/security/penetration-test-endpoints`
- `POST /v1/security/csp-report`
- `GET /v1/security/csp-violations`
- `GET /v1/security/csp-policies`
- `POST /v1/security/test-csp-policy`

### 2FA and password management

- `POST /v1/auth/2fa/setup`
- `POST /v1/auth/2fa/verify`
- `POST /v1/auth/2fa/login`
- `GET /v1/auth/2fa/status/{user_id}`
- `POST /v1/auth/2fa/disable`
- `POST /v1/auth/2fa/backup-codes`
- `POST /v1/auth/2fa/test-token`
- `GET /v1/auth/2fa/qr/{user_id}`
- `POST /v1/auth/password/validate`
- `GET /v1/auth/password/generate`
- `GET /v1/auth/password/policy`
- `POST /v1/auth/password/change`
- `POST /v1/auth/password/strength`
- `GET /v1/auth/password/security-tips`

### Candidate portal and document upload

- `POST /v1/candidate/register`
- `POST /v1/candidate/login`
- `GET /v1/candidate/profile/{candidate_id}`
- `PUT /v1/candidate/profile/{candidate_id}`
- `POST /v1/candidate/apply`
- `GET /v1/candidate/stats/{candidate_id}`
- `GET /v1/candidate/applications/{candidate_id}`
- `POST /v1/candidate/applications/{application_id}/documents/{document_type}`

### Candidate workflow bridge and tasks

- `GET /v1/candidate/workflow-link-status`
- `POST /v1/candidate/workflow-link`
- `DELETE /v1/candidate/workflow-link`
- `GET /v1/candidate/workflow-tasks`
- `GET /v1/candidate/workflow-tasks/{task_id}`
- `POST /v1/candidate/workflow-tasks/{task_id}/submit`
- `GET /v1/candidate/workflow-bridge-health`

### Portal notifications

- `GET /v1/portal/notifications`
- `POST /v1/portal/notifications/{notification_id}/read`
- `POST /v1/portal/notifications/read-all`

### Legacy/automation notification APIs

- `GET /v1/notifications/health`
- `POST /v1/notifications/send`
- `POST /v1/notifications/test-sequence`
- `POST /v1/notifications/preview`
- `POST /v1/notifications/bulk`
- `POST /v1/automation/trigger`
- `POST /v1/notifications/send-grouped-by-candidate`
- `POST /v1/notifications/send-per-job`

## Agent API (`backend/services/agent/app.py`)

- `GET /`
- `GET /health`
- `GET /test-db`
- `POST /match`
- `POST /batch-match`
- `GET /analyze/{candidate_id}`

## LangGraph API (`backend/services/langgraph/app/main.py`)

- `GET /`
- `GET /health`
- `POST /workflows/application/start`
- `GET /workflows/{workflow_id}/status`
- `POST /workflows/{workflow_id}/resume`
- `GET /workflows`
- `POST /automation/notifications/send`
- `POST /automation/test/email`
- `POST /automation/test/whatsapp`
- `POST /automation/test/telegram`
- `POST /automation/test/whatsapp-buttons`
- `POST /automation/test/sequence`
- `POST /automation/workflows/trigger`
- `POST /automation/notifications/bulk`
- `POST /automation/notifications/preview`
- `POST /automation/webhooks/whatsapp`
- `GET /workflows/stats`
- `GET /rl/performance`
- `POST /rl/start-monitoring`
- `GET /test-integration`

## High-value user flows and APIs

### Candidate applies and uploads requested docs

1. `POST /v1/candidate/apply`
2. Client/recruiter requests docs:
   - `POST /v1/client/applications/{application_id}/required-documents`
   - `POST /v1/recruiter/applications/{application_id}/required-documents`
3. Candidate uploads:
   - `POST /v1/candidate/applications/{application_id}/documents/{document_type}`
4. Client/recruiter fetch docs:
   - `GET /v1/client/applications/{application_id}/documents/{document_type}`
   - `GET /v1/recruiter/applications/{application_id}/documents/{document_type}`
5. Notification bell sync:
   - `GET /v1/portal/notifications`
   - mark read endpoints

### Candidate tasks workflow bridge

Gateway task flow uses workflow bridge configuration and candidate link credentials. Related APIs include workflow-link status/link/unlink routes plus candidate task retrieval paths exposed through gateway docs.

## API validation checklist

1. Start backend services.
2. Open `/docs` on all three services.
3. Validate auth endpoint responses.
4. Validate one job, one candidate, one matching endpoint.
5. Validate applicant document request/upload/download path.
6. Validate notifications list and read actions.

## Related docs and full locations

- `INFIVERSE-HR/README.md`
- `INFIVERSE-HR/backend/docs/README.md`
- `INFIVERSE-HR/backend/docs/guides/QUICK_START_GUIDE.md`
- `INFIVERSE-HR/backend/docs/guides/TROUBLESHOOTING_GUIDE.md`
- `INFIVERSE-HR/backend/services/gateway/README.md`
- `INFIVERSE-HR/backend/services/agent/README.md`
- `INFIVERSE-HR/backend/services/langgraph/README.md`
