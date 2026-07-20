# Gateway Service (`backend/services/gateway`)

Main FastAPI API surface for INFIVERSE-HR. This service owns authentication, jobs, candidates, applications, document workflows, and notifications.

## Start here (for new team members)

Do these steps first:

1. Read `../../docs/guides/QUICK_START_GUIDE.md`
2. Start gateway and confirm `http://localhost:8000/health`
3. Open `http://localhost:8000/docs`
4. Test login endpoints and one protected endpoint
5. Read integration sections for agent/langgraph/workflow bridge

## Runtime

- Default port: `8000`
- App entry: `app/main.py`
- OpenAPI docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Responsibilities

- JWT and API-key authenticated APIs
- Job and candidate lifecycle management
- Client/recruiter/candidate portal backend APIs
- Candidate document request/upload/download workflow
- Portal notifications (bell feed)
- Integrations with:
  - Agent service (`AGENT_SERVICE_URL`)
  - LangGraph service (`LANGGRAPH_SERVICE_URL`)
  - Workflow backend bridge (`WORKFLOW_API_BASE_URL`)

## Core files

```text
services/gateway/
├── app/
│   ├── main.py
│   ├── database.py
│   └── db_helpers.py
├── config.py
├── dependencies.py
├── jwt_auth.py
├── workflow_proxy.py
├── monitoring.py
└── requirements.txt
```

## Authentication model

- API key: `Authorization: Bearer <API_KEY_SECRET>`
- JWT for user login flows:
  - `JWT_SECRET_KEY`
  - `CANDIDATE_JWT_SECRET_KEY`
- Several route groups accept either JWT or API key through `get_auth`.

## Key endpoint groups

Gateway currently exposes a broad route set (100+). Use `/docs` for canonical live list.

### Monitoring and core

- `GET /`
- `GET /health`
- `GET /docs`
- `GET /openapi.json`
- `GET /metrics`
- `GET /health/detailed`
- `GET /metrics/dashboard`
- `GET /v1/test-candidates`

### Jobs

- `POST /v1/jobs`
- `GET /v1/jobs`
- `GET /v1/jobs/{job_id}`
- `PUT /v1/jobs/{job_id}`
- `DELETE /v1/jobs/{job_id}`
- `POST /v1/jobs/{job_id}/shortlist`
- `POST /v1/jobs/{job_id}/reject`
- `GET /v1/jobs/autocomplete`
- `GET /v1/jobs/skills/autocomplete`
- `GET /v1/jobs/locations/autocomplete`

### Candidates and matching

- `GET /v1/candidates`
- `GET /v1/candidates/search`
- `GET /v1/candidates/{candidate_id}`
- `GET /v1/candidates/job/{job_id}`
- `POST /v1/candidates/bulk`
- `POST /v1/candidates/parse-pdf`
- `POST /v1/candidates/check-duplicates`
- `GET /v1/candidates/stats`
- `GET /v1/candidates/autocomplete`
- `GET /v1/match/{job_id}/top`
- `POST /v1/match/batch`

### Candidate portal

- `POST /v1/candidate/register`
- `POST /v1/candidate/login`
- `GET /v1/candidate/profile/{candidate_id}`
- `PUT /v1/candidate/profile/{candidate_id}`
- `POST /v1/candidate/apply`
- `GET /v1/candidate/applications/{candidate_id}`
- `GET /v1/candidate/stats/{candidate_id}`
- `POST /v1/candidate/applications/{application_id}/documents/{document_type}`

### Candidate workflow bridge (tasks integration)

- `GET /v1/candidate/workflow-link-status`
- `POST /v1/candidate/workflow-link`
- `DELETE /v1/candidate/workflow-link`
- `GET /v1/candidate/workflow-tasks`
- `GET /v1/candidate/workflow-tasks/{task_id}`
- `POST /v1/candidate/workflow-tasks/{task_id}/submit`
- `GET /v1/candidate/workflow-bridge-health`

### Client portal

- `POST /v1/client/register`
- `POST /v1/client/login`
- `GET /v1/client/profile`
- `GET /v1/client/jobs`
- `GET /v1/client/stats`
- `GET /v1/client/applicants`
- `POST /v1/client/applications/{application_id}/required-documents`
- `GET /v1/client/applications/{application_id}/documents/{document_type}`

### Recruiter portal

- `GET /v1/recruiter/jobs`
- `GET /v1/recruiter/stats`
- `GET /v1/recruiter/applicants`
- `POST /v1/recruiter/applications/{application_id}/required-documents`
- `GET /v1/recruiter/applications/{application_id}/documents/{document_type}`
- Connection APIs:
  - `/v1/recruiter/connection-events`
  - `/v1/recruiter/confirm-connection`
  - `/v1/recruiter/disconnect`
  - `/v1/recruiter/current-connection`

### Notifications

- `GET /v1/portal/notifications`
- `POST /v1/portal/notifications/{notification_id}/read`
- `POST /v1/portal/notifications/read-all`
- legacy/send APIs under `/v1/notifications/*`

### Assessment and operations

- `POST /v1/feedback`
- `GET /v1/feedback`
- `GET /v1/interviews`
- `POST /v1/interviews`
- `POST /v1/offers`
- `GET /v1/offers`
- `GET /v1/database/schema`
- `GET /v1/reports/job/{job_id}/export.csv`

### Security and auth hardening

- Security test endpoints under `/v1/security/*`
- 2FA endpoints under `/v1/auth/2fa/*`
- Password endpoints under `/v1/auth/password/*`

## Workflow bridge notes

Gateway can sync candidate tasks from external workflow backend:

- Base URL: `WORKFLOW_API_BASE_URL`
- Docker-to-host local: `WORKFLOW_API_BASE_URL_DOCKER` (`host.docker.internal`)
- Candidate link status/link/unlink APIs exist through `workflow_proxy.py`
- Candidate-specific credentials are supported (encrypted storage path)

## Local run

```powershell
cd backend/services/gateway
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

First validation after boot:

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## Required env (minimum)

```env
DATABASE_URL=<mongodb-uri>
MONGODB_DB_NAME=bhiv_hr
API_KEY_SECRET=<secret>
JWT_SECRET_KEY=<secret>
CANDIDATE_JWT_SECRET_KEY=<secret>
GATEWAY_SECRET_KEY=<secret>
AGENT_SERVICE_URL=http://localhost:9000
LANGGRAPH_SERVICE_URL=http://localhost:9001
WORKFLOW_API_BASE_URL=<workflow-api-base>
```

## Operational tips

- Validate changes using `GET /health` and `GET /docs`.
- For frontend auth issues, verify token claims include correct role.
- For candidate tasks failures, verify workflow URL and candidate workflow credentials.

## Related docs and full locations

- `INFIVERSE-HR/backend/services/gateway/README.md`
- `INFIVERSE-HR/backend/docs/README.md`
- `INFIVERSE-HR/backend/docs/api/API_DOCUMENTATION.md`
- `INFIVERSE-HR/backend/docs/guides/TROUBLESHOOTING_GUIDE.md`
- `INFIVERSE-HR/backend/services/agent/README.md`
- `INFIVERSE-HR/backend/services/langgraph/README.md`
- `INFIVERSE-HR/README.md`
