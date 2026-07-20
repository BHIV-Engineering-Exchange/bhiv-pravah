# Deployment Guide

This guide explains how to deploy the BHIV Core-Integrator system locally, remotely, and in mixed environments.

## Local deployment

### Prerequisites

- Python 3.11 or higher
- `pip` installed
- Available ports: `8000`, `8001`, `8003`, `8004`, `8005`
- Optional: `uvicorn` for FastAPI services

### Install dependencies

```bash
python -m pip install -r requirements.txt
python -m pip install -r creator-core/Core-Integrator-Sprint-1.1/requirements.txt
```

### Startup order (all 8 services)

Use the orchestrator (recommended):

```bash
python start_all.py
```

Dependency order from `config/services.yml`:

1. `BHIV Bucket` — port 8005
2. `Prompt Runner` — port 8003
3. `Creator Core` — port 8000
4. `BHIV Core` — port 8001
5. `CET Service` — port 8006
6. `Sarathi Service` — port 8007
7. `Gate Service` — port 8008
8. `Integration Bridge` — port 8004 (depends on all above)

Manual startup (if needed):

1. `python bhiv_bucket.py`
2. `python prompt-runner01/run_server.py`
3. `cd creator-core/Core-Integrator-Sprint-1.1 && python main.py`
4. `python main.py`
5. `python cet_service.py`
6. `python sarathi_service.py`
7. `python gate_service.py`
8. `python integration_bridge.py`

Alternative:

```bash
python deploy_and_test.py
```

### Environment variables

Key variables used by the system:

- `PROMPT_RUNNER_URL` — Prompt Runner URL (default `http://127.0.0.1:8003`)
- `CREATOR_CORE_URL` — Creator Core URL (default `http://127.0.0.1:8000`)
- `BHIV_CORE_URL` — BHIV Core URL (default `http://127.0.0.1:8001`)
- `INTEGRATION_BRIDGE_URL` — Integration Bridge URL (default `http://127.0.0.1:8004`)
- `CET_URL` — CET service URL (default `http://127.0.0.1:8006`)
- `SARATHI_URL` — Sarathi service URL (default `http://127.0.0.1:8007`)
- `GATE_URL` — Gate service URL (default `http://127.0.0.1:8008`)
- `AUTH_API_KEY` — shared API key for protected endpoints
- `AUTH_ENABLED` — set to `true` to enforce auth (default in orchestrator)
- `RATE_LIMIT_IP_PER_MIN` — IP rate limit (orchestrator sets 10000 for local dev)
- `HOST` — host binding for services
- `DB_PATH` — path for BHIV Core database
- `STORAGE_PATH` — artifact folder for Bucket

Use `.env`, `.env.integration_bridge`, or service-local env files to override default values.

### Service ports

| Service | Default Port |
|---|---|
| Creator Core | 8000 |
| BHIV Core | 8001 |
| Prompt Runner | 8003 |
| Integration Bridge | 8004 |
| BHIV Bucket | 8005 |
| CET Service | 8006 |
| Sarathi Service | 8007 |
| Gate Service | 8008 |
| API Gateway | 8080 |

### Health checks

- Prompt Runner: `http://127.0.0.1:8003/health`
- Creator Core: `http://127.0.0.1:8000/`
- BHIV Core: `http://127.0.0.1:8001/system/health`
- Integration Bridge: `http://127.0.0.1:8004/pipeline/health`
- BHIV Bucket: `http://127.0.0.1:8005/bucket/stats`
- CET: `http://127.0.0.1:8006/health`
- Sarathi: `http://127.0.0.1:8007/health`
- Gate: `http://127.0.0.1:8008/health`

### Live validation

```bash
python run_comprehensive_live_tests.py
python test_production_runtime.py
```

### Common local deployment failures

- Port collisions
- Missing Python dependencies
- Invalid or missing environment variables
- Prompt Runner stub not matching expected response shape
- Bucket storage folder permission issues

### Recovery procedures

1. Stop all services.
2. Verify env variables and ports.
3. Restart services in correct order.
4. Run `python test_services.py`.
5. Inspect logs and `bhiv_bucket/traces/`.

---

## Remote deployment

### Supported files

- `render.yaml` — Render deployment configuration
- `vercel.json` — Vercel deployment configuration
- `RENDER_DEPLOYMENT.md` — remote deployment notes
- `VERCEL_DEPLOYMENT.md` — Vercel-specific notes

### Remote deployment guidance

- Services can be deployed individually on remote hosts.
- Use HTTPS and secure endpoints.
- Set service URLs in remote environment variables.
- Ensure `PROMPT_RUNNER_URL`, `CREATOR_CORE_URL`, `BHIV_CORE_URL`, and `BUCKET_URL` match remote service locations.

### Remote environment variables

- `PROMPT_RUNNER_URL`
- `CREATOR_CORE_URL`
- `BHIV_CORE_URL`
- `INTEGRATION_BRIDGE_URL`
- `BUCKET_URL`
- `PORT`
- `HOST`
- `DB_PATH`
- `STORAGE_PATH`

### Remote deployment risks

- network latency
- inconsistent environment configuration
- missing or invalid service URL references
- unsecured HTTP endpoints

---

## Mixed deployment

Mixed deployment means some services run locally while others run remotely.

### Example configuration

- Local BHIV Core: `http://127.0.0.1:8001`
- Remote Creator Core: `https://creator.example.com`
- Remote Prompt Runner: `https://prompt-runner.example.com`
- Local Bucket: `http://127.0.0.1:8005`
- Local Integration Bridge: `http://127.0.0.1:8004`

### Requirements

- Remote endpoints must be reachable from the Integration Bridge process.
- All service URLs must be updated consistently.
- The prompt runner stub must be replaced if remote prompt generation is required.

### Common mixed deployment failures

- firewalls and routing issues
- mismatched protocols (`http` vs `https`)
- service URL misconfiguration
- version mismatch between services

---

## Dependencies

### Python dependencies

- `requirements.txt` — core dependencies
- `creator-core/Core-Integrator-Sprint-1.1/requirements.txt` — Creator Core dependencies
- `requirements-vercel.txt` — Vercel deployment dependencies

### Runtime dependencies

- `uvicorn`
- `fastapi`
- `pydantic`
- `requests`

## Deployment checklist

1. Install dependencies.
2. Validate environment variables.
3. Start Bucket.
4. Start Creator Core.
5. Start BHIV Core.
6. Start Prompt Runner.
7. Start Integration Bridge.
8. Run health checks.
9. Execute sample prompt.
10. Confirm artifact chain exists in Bucket.

## Troubleshooting

### Service unreachable

- Check process logs
- Confirm port listening
- Verify env configuration

### Data storage failure

- Validate `STORAGE_PATH`
- Check disk permissions and free space

### Bridge or pipeline errors

- Verify all upstream services are healthy
- Confirm `trace_id` propagation and artifact storage
- Inspect `bhiv_bucket/traces/` and service logs
