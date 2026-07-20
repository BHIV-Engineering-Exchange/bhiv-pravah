# Backend Troubleshooting Guide

Use this guide for day-to-day backend debugging (gateway, agent, langgraph, and integration paths).

## Beginner rule before debugging

Always check in this order:

1. Are all services running?
2. Are ports reachable?
3. Are required env values present?
4. Is auth header correct?
5. Is the failing endpoint visible in `/docs`?

## 1) Fast health triage

```powershell
curl http://localhost:8000/health
curl http://localhost:9000/health
curl http://localhost:9001/health
```

If any fail, fix process start first before API-level debugging.

## 2) Common issues and fixes

### A) Port already in use

Symptoms:

- service fails to boot
- bind errors in logs

Fix:

```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

Repeat for `9000` and `9001`.

### B) 401/403 on protected APIs

Symptoms:

- login seems fine but API returns unauthorized

Checks:

1. `Authorization` header format is `Bearer <token>`.
2. Backend secrets in `.env` are present and consistent:
   - `API_KEY_SECRET`
   - `JWT_SECRET_KEY`
   - `CANDIDATE_JWT_SECRET_KEY`
3. Token is not expired.

### C) Gateway cannot reach agent/langgraph

Symptoms:

- `/v1/match/*` slow/failing
- workflow trigger errors

Checks:

- `AGENT_SERVICE_URL` and `LANGGRAPH_SERVICE_URL` values in `backend/.env`
- health of `:9000` and `:9001`
- Docker networking (if running containerized)

### D) Candidate tasks workflow integration fails

Symptoms:

- Tasks page not loading workflow tasks
- bridge/login errors from gateway

Checks:

1. `WORKFLOW_API_BASE_URL` resolves and responds.
2. In Docker, use `WORKFLOW_API_BASE_URL_DOCKER=http://host.docker.internal:<port>/api` for host workflow server.
3. Candidate workflow credentials are linked correctly.
4. If using hosted workflow API, ensure `.../api` path is included.

### E) Document upload/request flow mismatch

Symptoms:

- requested docs not reflected in candidate/client/recruiter views
- candidate upload remains disabled after re-request

Checks:

1. Verify request API success:
   - `POST /v1/client/applications/{application_id}/required-documents`
   - `POST /v1/recruiter/applications/{application_id}/required-documents`
2. Verify candidate upload API success:
   - `POST /v1/candidate/applications/{application_id}/documents/{document_type}`
3. Verify notifications API:
   - `GET /v1/portal/notifications`
4. Verify frontend is receiving refreshed application payload.

## 3) Useful debug endpoints

Gateway:

- `GET /health`
- `GET /metrics`
- `GET /health/detailed`
- `GET /v1/test-candidates`
- `GET /v1/security/rate-limit-status`

Agent:

- `GET /health`
- `GET /test-db`

LangGraph:

- `GET /health`
- `GET /test-integration`
- `GET /workflows/stats`

## 4) Docker-specific issues

### Containers up but APIs failing

```powershell
cd backend
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs -f gateway
docker compose -f docker-compose.production.yml logs -f agent
docker compose -f docker-compose.production.yml logs -f langgraph
```

### Gateway to host-service connectivity

If workflow backend runs on host machine and gateway runs in Docker, do not use `127.0.0.1` inside container config; use `host.docker.internal`.

## 5) Performance checks

- Gateway metrics endpoint: `GET /metrics`
- Match latency path: `GET /v1/match/{job_id}/top`
- Tune gateway timeout for agent fallback:
  - `AGENT_MATCH_TIMEOUT` in `backend/.env`

## 6) Recovery playbook

1. Restart only failed service.
2. Re-check `/health`.
3. Validate one protected API with auth header.
4. Validate one workflow/document endpoint relevant to the issue.
5. Validate frontend call path end-to-end.

## 7) Escalation data to collect

When raising an issue, include:

- failing endpoint + method
- request payload (without secrets)
- response status/body
- service logs around failure timestamp
- current env values for related keys (redact secrets)

## Related docs

- `QUICK_START_GUIDE.md`
- `../api/API_DOCUMENTATION.md`
- `../../services/gateway/README.md`
- `../../services/agent/README.md`
- `../../services/langgraph/README.md`

## Full file locations (resolved)

- `INFIVERSE-HR/backend/docs/guides/TROUBLESHOOTING_GUIDE.md`
- `INFIVERSE-HR/backend/docs/guides/QUICK_START_GUIDE.md`
- `INFIVERSE-HR/backend/docs/api/API_DOCUMENTATION.md`
- `INFIVERSE-HR/backend/services/gateway/README.md`
- `INFIVERSE-HR/backend/services/agent/README.md`
- `INFIVERSE-HR/backend/services/langgraph/README.md`