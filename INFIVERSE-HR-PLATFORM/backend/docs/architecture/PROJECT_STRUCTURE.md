# Backend Architecture Overview

This document describes the current backend structure used by INFIVERSE-HR.

## Service topology

```text
Frontend (React)
   -> Gateway (FastAPI, :8000)
      -> Agent (FastAPI, :9000)
      -> LangGraph (FastAPI, :9001)
      -> MongoDB
      -> External Workflow API (Complete-Infiverse bridge)
```

## Backend folder layout

```text
backend/
├── services/
│   ├── gateway/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── database.py
│   │   │   └── db_helpers.py
│   │   ├── workflow_proxy.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── jwt_auth.py
│   │   └── README.md
│   ├── agent/
│   │   ├── app.py
│   │   ├── semantic_engine/
│   │   │   └── phase3_engine.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── README.md
│   └── langgraph/
│       ├── app/
│       │   ├── main.py
│       │   ├── graphs.py
│       │   ├── state.py
│       │   ├── agents.py
│       │   └── communication.py
│       ├── config.py
│       └── README.md
├── docs/
│   ├── api/
│   ├── architecture/
│   ├── guides/
│   ├── security/
│   ├── testing/
│   └── database/
├── handover/
├── docker-compose.production.yml
├── run_services.py
└── .env.example
```

## Service responsibilities

### Gateway (`:8000`)

- Main API entry point for frontend
- Authentication and authorization
- Jobs, candidates, applications, interviews, offers
- Document request/upload/download workflow endpoints
- Notification APIs for bell feeds
- Bridges to agent/langgraph and workflow backend

### Agent (`:9000`)

- Candidate/job matching endpoints
- Batch matching
- Candidate analysis
- DB connectivity diagnostics

### LangGraph (`:9001`)

- Workflow orchestration endpoints
- Automation notification send/test/preview endpoints
- Workflow monitoring and stats
- Integration test endpoint

## Data and integrations

- Primary persistence: MongoDB (configured via `DATABASE_URL`)
- External workflow integration: URL via `WORKFLOW_API_BASE_URL` and related keys
- Service-to-service URLs:
  - `AGENT_SERVICE_URL`
  - `LANGGRAPH_SERVICE_URL`
  - `GATEWAY_SERVICE_URL` (langgraph side)

## Request flow examples

### Candidate task flow

1. Frontend candidate tasks page calls gateway.
2. Gateway resolves linked workflow credentials.
3. Gateway calls workflow backend.
4. Gateway returns normalized task payload to frontend.

### Document collection flow

1. Client/recruiter requests required docs per application.
2. Candidate uploads requested doc file.
3. Gateway stores metadata/content and emits notifications.
4. Client/recruiter download/view APIs return document blob.

## Deployment shapes

### Local Python mode

- `run_services.py` starts gateway + agent + langgraph.

### Docker mode

- `docker-compose.production.yml` starts the same three core services.
- Workflow host access from gateway container should use `host.docker.internal` for local host workflow service.

## Architecture maintenance rules

- Keep all external service URLs in env, never hardcoded.
- Keep route inventory synchronized with each service `/docs`.
- For new cross-service features, define:
  - gateway contract
  - service-level timeout behavior
  - fallback and notification behavior
- Update these docs whenever endpoints or auth behavior change.
