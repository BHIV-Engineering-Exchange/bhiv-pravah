# Backend Documentation Index

This index points to the current backend documentation for INFIVERSE-HR.

## 0 knowledge reading path (recommended)

Read in this exact order:

1. `guides/QUICK_START_GUIDE.md` (run services first)
2. `api/API_DOCUMENTATION.md` (know endpoints and auth)
3. `guides/TROUBLESHOOTING_GUIDE.md` (fix common failures fast)
4. `../services/gateway/README.md` (main API owner)
5. `../services/agent/README.md` (matching service)
6. `../services/langgraph/README.md` (workflow automation service)
7. `../../README.md` (full project context)

## Start here

1. `guides/QUICK_START_GUIDE.md`
2. `architecture/PROJECT_STRUCTURE.md`
3. `api/API_DOCUMENTATION.md`
4. `guides/TROUBLESHOOTING_GUIDE.md`

## Service docs

- Gateway: `../services/gateway/README.md`
- Agent: `../services/agent/README.md`
- LangGraph: `../services/langgraph/README.md`

## Cross-stack docs

- Project overview: `../../README.md`
- Root quick start: `../../QUICK_START.md`
- Frontend docs: `../../frontend/README.md`
- Frontend auth deep dive: `../../frontend/AUTHENTICATION_STRUCTURE.md`

## Full file locations

- `INFIVERSE-HR/backend/docs/README.md`
- `INFIVERSE-HR/backend/services/gateway/README.md`
- `INFIVERSE-HR/backend/services/agent/README.md`
- `INFIVERSE-HR/backend/services/langgraph/README.md`
- `INFIVERSE-HR/README.md`

## Documentation sections

### Guides (`guides/`)

- `QUICK_START_GUIDE.md` - backend bootstrapping and verification
- `TROUBLESHOOTING_GUIDE.md` - common failures and fixes
- `SERVICES_GUIDE.md` - service responsibilities and interactions
- `DEPLOYMENT_GUIDE.md` - deployment and env strategy

### API (`api/`)

- `API_DOCUMENTATION.md` - backend API reference (gateway + agent + langgraph)

### Architecture (`architecture/`)

- `PROJECT_STRUCTURE.md` - codebase structure and data flows

### Database (`database/`)

- `DATABASE_DOCUMENTATION.md`
- `MONGODB_COLLECTIONS.md`
- `MONGODB_ATLAS_SETUP.md`
- `MONGODB_QUICK_QUERIES.md`

### Security (`security/`)

- `SECURITY_AUDIT.md`
- `API_KEYS_SUMMARY.md`
- `AUDIT_AND_TRACEABILITY.md`

### Testing (`testing/`)

- `API_TESTING_GUIDE.md`
- `COMPREHENSIVE_TESTING_GUIDE.md`
- `TRIPLE_AUTHENTICATION_TESTING_GUIDE.md`

## Local docs URLs when services run

- Gateway docs: `http://localhost:8000/docs`
- Agent docs: `http://localhost:9000/docs`
- LangGraph docs: `http://localhost:9001/docs`

## Notes

- The canonical route inventory comes from each service OpenAPI (`/docs` and `/openapi.json`).
- Keep docs aligned to implemented routes in:
  - `backend/services/gateway/app/main.py`
  - `backend/services/agent/app.py`
  - `backend/services/langgraph/app/main.py`
