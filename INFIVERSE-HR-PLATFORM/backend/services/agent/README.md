# Agent Service (`backend/services/agent`)

FastAPI service for AI-assisted candidate matching and candidate analysis.

## Start here (for beginners)

1. Ensure gateway is already running (`:8000`).
2. Start this service on `:9000`.
3. Verify health and DB connectivity.
4. Test `/match` with sample payload.
5. Confirm gateway `AGENT_SERVICE_URL` points here.

## Runtime

- Default port: `9000`
- App entry: `app.py`
- OpenAPI docs: `http://localhost:9000/docs`
- Health: `http://localhost:9000/health`

## Endpoints

The service exposes 6 routes:

- `GET /`
- `GET /health`
- `GET /test-db`
- `POST /match`
- `POST /batch-match`
- `GET /analyze/{candidate_id}`

## Responsibilities

- Produce candidate match rankings for a given job (`/match`)
- Process batch match requests (`/batch-match`)
- Provide candidate-level analysis details (`/analyze/{candidate_id}`)
- Integrate with MongoDB data used by gateway and frontend workflows

## Core files

```text
services/agent/
├── app.py
├── config.py
├── database.py
├── jwt_auth.py
├── semantic_engine/
│   └── phase3_engine.py
└── requirements.txt
```

## Expected integration pattern

1. Frontend calls gateway matching endpoints.
2. Gateway calls agent service.
3. Agent returns ranked results.
4. Gateway applies fallback logic if agent is unavailable or slow.

## Required environment variables

```env
DATABASE_URL=<mongodb-uri>
MONGODB_DB_NAME=bhiv_hr
API_KEY_SECRET=<secret>
JWT_SECRET_KEY=<secret>
CANDIDATE_JWT_SECRET_KEY=<secret>
LOG_LEVEL=INFO
ENVIRONMENT=development
```

Optional (model/runtime tuning):

- `HF_TOKEN`
- `TRANSFORMERS_VERBOSITY`
- `TOKENIZERS_PARALLELISM`
- `GEMINI_API_KEY` (if used by your branch features)

## Local run

```powershell
cd backend/services/agent
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 9000 --reload
```

Quick verification:

```powershell
curl http://localhost:9000/health
curl http://localhost:9000/test-db
```

## Verification checklist

- `GET /health` returns healthy response.
- `GET /test-db` confirms DB connectivity.
- `POST /match` returns ordered candidates for valid job ids.
- `POST /batch-match` returns grouped responses per job id.

## Operational notes

- Keep `AGENT_SERVICE_URL` in gateway config aligned with this service URL.
- If match latency is high, gateway may fallback based on `AGENT_MATCH_TIMEOUT`.
- Prefer using gateway APIs from frontend; call agent directly only for diagnostics or internal integrations.

## Related docs and full locations

- `INFIVERSE-HR/backend/services/agent/README.md`
- `INFIVERSE-HR/backend/services/gateway/README.md`
- `INFIVERSE-HR/backend/services/langgraph/README.md`
- `INFIVERSE-HR/backend/docs/api/API_DOCUMENTATION.md`
- `INFIVERSE-HR/backend/docs/guides/QUICK_START_GUIDE.md`
- `INFIVERSE-HR/backend/docs/guides/TROUBLESHOOTING_GUIDE.md`
