# Backend Handover: Read This First

If you are new to this project, read this file first, then follow the linked docs in order.

## What this backend does

The backend powers three role-based frontend portals (candidate, recruiter, client) and provides:

- authentication and role-aware APIs
- jobs and candidate lifecycle APIs
- AI matching integration via agent service
- workflow automation integration via langgraph service
- candidate document collection and notification flows
- candidate task integration with external workflow backend

## Runtime services

- Gateway: `http://localhost:8000`
- Agent: `http://localhost:9000`
- LangGraph: `http://localhost:9001`

## Day-1 setup sequence

1. `backend/docs/guides/QUICK_START_GUIDE.md`
2. `backend/docs/architecture/PROJECT_STRUCTURE.md`
3. `backend/docs/api/API_DOCUMENTATION.md`
4. `backend/docs/guides/TROUBLESHOOTING_GUIDE.md`

## Required env baseline

Create `backend/.env` from `backend/.env.example` and set at least:

- `DATABASE_URL`
- `API_KEY_SECRET`
- `JWT_SECRET_KEY`
- `CANDIDATE_JWT_SECRET_KEY`
- `GATEWAY_SECRET_KEY`

For workflow tasks integration:

- `WORKFLOW_API_BASE_URL`
- `WORKFLOW_API_BASE_URL_DOCKER` (for Docker-to-host local workflow access)
- `WORKFLOW_USER_PASSWORD` / candidate link credentials as applicable

## Critical flows to verify before handoff

1. **Auth**: login for candidate, recruiter, client
2. **Jobs/candidates**: list/create/search routes
3. **Matching**: gateway match endpoints return data
4. **Document workflow**:
   - request docs (client/recruiter)
   - upload doc (candidate)
   - view/download doc (client/recruiter)
   - notification bell updates
5. **Candidate tasks**: workflow link and task fetch path works

## Known high-risk areas

- Auth token/role mismatches between frontend and backend
- Workflow API URL mismatch between local and Docker runtime
- Missing secrets causing 401/500 across services
- Notification flow regressions after document workflow updates

## Quick commands

Start backend:

```powershell
cd backend
setup_venv.bat
run_with_venv.bat
```

Or:

```powershell
cd backend
python run_services.py
```

Health checks:

```powershell
curl http://localhost:8000/health
curl http://localhost:9000/health
curl http://localhost:9001/health
```

## Ownership guidance for intern handover

- Always update docs when changing routes, payloads, or auth behavior.
- Prefer backward-compatible API changes for frontend stability.
- Before merging, run:
  - frontend build
  - backend health checks
  - key workflow/document flow smoke tests

## Reference links

- Backend docs index: `backend/docs/README.md`
- Gateway docs: `backend/services/gateway/README.md`
- Agent docs: `backend/services/agent/README.md`
- LangGraph docs: `backend/services/langgraph/README.md`
- Root project guide: `README.md`
