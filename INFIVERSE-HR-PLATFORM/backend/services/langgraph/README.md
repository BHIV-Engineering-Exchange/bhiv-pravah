# LangGraph Service (`backend/services/langgraph`)

FastAPI workflow orchestration service used by gateway for automation and notification workflows.

## Start here (for beginners)

1. Ensure gateway is running (`:8000`).
2. Start langgraph on `:9001`.
3. Verify health and integration test endpoints.
4. Trigger one workflow endpoint from `/docs`.
5. Confirm gateway `LANGGRAPH_SERVICE_URL` points here.

## Runtime

- Default port: `9001`
- App entry: `app/main.py`
- OpenAPI docs: `http://localhost:9001/docs`
- Health: `http://localhost:9001/health`

## Exposed endpoints

Current `app/main.py` routes:

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

## Responsibilities

- Execute and track automation workflows
- Manage notification send/test/preview flows
- Expose workflow monitoring and stats
- Provide RL-related performance hooks used by surrounding services

## Core files

```text
services/langgraph/
├── app/
│   ├── main.py
│   ├── graphs.py
│   ├── state.py
│   ├── agents.py
│   ├── communication.py
│   ├── monitoring.py
│   └── rl_integration/
├── config.py
├── dependencies.py
├── jwt_auth.py
└── requirements.txt
```

## Required environment variables

```env
DATABASE_URL=<mongodb-uri>
MONGODB_DB_NAME=bhiv_hr
API_KEY_SECRET=<secret>
JWT_SECRET_KEY=<secret>
CANDIDATE_JWT_SECRET_KEY=<secret>
GATEWAY_SERVICE_URL=http://localhost:8000
LOG_LEVEL=INFO
ENVIRONMENT=development
```

Optional communication and AI keys:

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_NUMBER`
- `GMAIL_EMAIL`
- `GMAIL_APP_PASSWORD`
- `TELEGRAM_BOT_TOKEN`
- `GEMINI_API_KEY`

## Local run

```powershell
cd backend/services/langgraph
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 9001 --reload
```

Quick verification:

```powershell
curl http://localhost:9001/health
curl http://localhost:9001/test-integration
```

## Integration notes

- Gateway calls this service for workflow orchestration and automation operations.
- Keep `LANGGRAPH_SERVICE_URL` in gateway config aligned.
- For containerized local runs, gateway should target `http://langgraph:9001`.

## Verification checklist

- `GET /health`
- `GET /workflows/stats`
- `POST /workflows/application/start` with test payload
- `GET /test-integration`

## Operational notes

- If communication keys are missing, messaging features may degrade while core workflow APIs remain available.
- Use `/docs` as the canonical route and schema reference for client integrations.

## Related docs and full locations

- `INFIVERSE-HR/backend/services/langgraph/README.md`
- `INFIVERSE-HR/backend/services/gateway/README.md`
- `INFIVERSE-HR/backend/services/agent/README.md`
- `INFIVERSE-HR/backend/docs/api/API_DOCUMENTATION.md`
- `INFIVERSE-HR/backend/docs/guides/QUICK_START_GUIDE.md`
- `INFIVERSE-HR/backend/docs/guides/TROUBLESHOOTING_GUIDE.md`
