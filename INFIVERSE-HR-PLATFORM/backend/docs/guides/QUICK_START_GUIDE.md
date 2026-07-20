# Backend Quick Start Guide

This guide covers local backend startup for:

- Gateway (`:8000`)
- Agent (`:9000`)
- LangGraph (`:9001`)

If you are completely new, do every step in order and confirm expected output before moving ahead.

## Step 0: What each service does

- Gateway: main API and authentication.
- Agent: candidate matching/analysis.
- LangGraph: workflows and automation.

## Prerequisites

- Python `3.11+`
- pip
- MongoDB URI
- Windows PowerShell or terminal of choice
- Docker Desktop (only if using compose mode)

## Step 1: Configure backend env

```powershell
cd backend
copy .env.example .env
```

Set at minimum:

- `DATABASE_URL`
- `API_KEY_SECRET`
- `JWT_SECRET_KEY`
- `CANDIDATE_JWT_SECRET_KEY`
- `GATEWAY_SECRET_KEY`

Service URL defaults should usually remain:

- `GATEWAY_SERVICE_URL=http://localhost:8000`
- `AGENT_SERVICE_URL=http://localhost:9000`
- `LANGGRAPH_SERVICE_URL=http://localhost:9001`

Workflow bridge values:

- Local non-docker gateway: `WORKFLOW_API_BASE_URL=http://127.0.0.1:<port>/api`
- Docker gateway to host workflow: `WORKFLOW_API_BASE_URL_DOCKER=http://host.docker.internal:<port>/api`

## Step 2A: Run with local Python launcher

```powershell
cd backend
setup_venv.bat
run_with_venv.bat
```

Alternative manual run:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_services.py
```

## Step 2B: Run with Docker Compose

```powershell
cd backend
docker compose -f docker-compose.production.yml up --build -d
```

Stop:

```powershell
docker compose -f docker-compose.production.yml down
```

## Step 3: Verify services

Open:

- `http://localhost:8000/health`
- `http://localhost:9000/health`
- `http://localhost:9001/health`

Open API docs:

- `http://localhost:8000/docs`
- `http://localhost:9000/docs`
- `http://localhost:9001/docs`

## Step 4: Smoke-test key APIs

```powershell
curl http://localhost:8000/health
curl http://localhost:9000/health
curl http://localhost:9001/health
```

Gateway protected sample:

```powershell
curl -H "Authorization: Bearer <API_KEY_SECRET>" http://localhost:8000/v1/candidates
```

## Step 5: Validate frontend integration

From `frontend/.env`, confirm:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Then run frontend and login for role-based checks.

## Quick troubleshooting

- Port conflict: check with `netstat -ano | findstr :8000`
- 401 on protected endpoint: verify bearer token/secret
- Gateway cannot reach agent/langgraph: verify service URL env values
- Candidate tasks not loading: verify workflow URL variables and workflow backend availability

## Related docs

- `../README.md`
- `../api/API_DOCUMENTATION.md`
- `TROUBLESHOOTING_GUIDE.md`
- `../../services/gateway/README.md`
- `../../services/agent/README.md`
- `../../services/langgraph/README.md`

## Full file locations (resolved)

- `INFIVERSE-HR/backend/docs/guides/QUICK_START_GUIDE.md`
- `INFIVERSE-HR/backend/docs/README.md`
- `INFIVERSE-HR/backend/docs/api/API_DOCUMENTATION.md`
- `INFIVERSE-HR/backend/docs/guides/TROUBLESHOOTING_GUIDE.md`
- `INFIVERSE-HR/backend/services/gateway/README.md`
- `INFIVERSE-HR/backend/services/agent/README.md`
- `INFIVERSE-HR/backend/services/langgraph/README.md`
