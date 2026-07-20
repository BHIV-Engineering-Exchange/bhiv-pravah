# INFIVERSE-HR Quick Start

This guide gets the project running quickly with the current architecture:

- Frontend (React + Vite): `http://localhost:3000`
- Gateway service (FastAPI): `http://localhost:8000`
- Agent service (FastAPI): `http://localhost:9000`
- LangGraph service (FastAPI): `http://localhost:9001`

If you have zero project knowledge, complete every step in order and do not skip environment setup.

## Step 0: Understand what you are starting

- Frontend is the website you open in browser (`:3000`).
- Gateway is the main backend API (`:8000`).
- Agent provides matching intelligence (`:9000`).
- LangGraph provides workflow automation (`:9001`).

## Prerequisites

- Windows 10/11, macOS, or Linux
- Python `3.11+` (3.12 recommended)
- Node.js `18+` and npm
- Docker Desktop (optional, for containerized backend)
- MongoDB connection string (ask your team lead if you do not have one)

## 1) Configure environment (must do first)

### Backend

```powershell
cd backend
copy .env.example .env
```

Update required values in `backend/.env`:

- `DATABASE_URL`
- `API_KEY_SECRET`
- `JWT_SECRET_KEY`
- `CANDIDATE_JWT_SECRET_KEY`
- `GATEWAY_SECRET_KEY`

Workflow/task bridge values (important for candidate `Tasks` page):

- Local workflow server: set `WORKFLOW_API_BASE_URL=http://127.0.0.1:<port>/api`
- Docker gateway to local workflow server: set `WORKFLOW_API_BASE_URL_DOCKER=http://host.docker.internal:<port>/api`
- Hosted workflow server: set `WORKFLOW_API_BASE_URL=https://<host>/api`

### Frontend

```powershell
cd ..\frontend
copy .env.example .env
```

Set:

- `VITE_API_BASE_URL=http://localhost:8000`

## 2) Run locally (recommended)

### Backend services

```powershell
cd ..\backend
setup_venv.bat
run_with_venv.bat
```

Or manually:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_services.py
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Expected result after Step 2:

- frontend opens on `http://localhost:3000`
- `http://localhost:8000/health` returns healthy response
- `http://localhost:9000/health` returns healthy response
- `http://localhost:9001/health` returns healthy response

## 3) Run backend with Docker (optional alternative)

```powershell
cd backend
docker compose -f docker-compose.production.yml up --build -d
```

Stop:

```powershell
docker compose -f docker-compose.production.yml down
```

## 4) Verify health and docs

Open these URLs:

- `http://localhost:3000`
- `http://localhost:8000/health`
- `http://localhost:9000/health`
- `http://localhost:9001/health`

Open API docs:

- `http://localhost:8000/docs`
- `http://localhost:9000/docs`
- `http://localhost:9001/docs`

## 5) Common first checks (beginner smoke test)

- Frontend build:
  - `cd frontend && npm run build`
- Backend endpoint smoke test:
  - `GET /health` on all three services
- Authentication smoke test:
  - Login from frontend, verify protected routes load
- Candidate tasks smoke test:
  - Link workflow in candidate `Tasks` page and confirm tasks are fetched

## 6) Troubleshooting quick hits

- Port already used:
  - `netstat -ano | findstr :8000`
  - `taskkill /PID <PID> /F`
- Gateway cannot reach workflow server in Docker:
  - Use `WORKFLOW_API_BASE_URL_DOCKER=http://host.docker.internal:<port>/api`
- 401/403 from APIs:
  - Check JWT/API-key secrets in `backend/.env`
- Frontend shows network error:
  - Confirm `VITE_API_BASE_URL` matches running gateway URL

## 7) What to read next (learning path)

- Project overview: `README.md`
- Frontend docs: `frontend/README.md`
- Frontend auth details: `frontend/AUTHENTICATION_STRUCTURE.md`
- Backend docs index: `backend/docs/README.md`
- Gateway service docs: `backend/services/gateway/README.md`

## Full file locations (repo structure)

- `INFIVERSE-HR/README.md`
- `INFIVERSE-HR/QUICK_START.md`
- `INFIVERSE-HR/frontend/README.md`
- `INFIVERSE-HR/frontend/AUTHENTICATION_STRUCTURE.md`
- `INFIVERSE-HR/backend/docs/README.md`
- `INFIVERSE-HR/backend/services/gateway/README.md`

