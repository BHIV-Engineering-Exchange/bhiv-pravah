# Render Deployment Guide

This repository includes a `render.yaml` manifest for deploying the BHIV system on Render.
The primary goal is to make the Prompt Runner + Creator Core flow work first.

## Services in render.yaml

- `prompt-runner` — starts `prompt-runner01/run_server.py`
- `creator-core` — starts `creator-core/Core-Integrator-Sprint-1.1/main.py`
- `bhiv-core` — starts `main.py`
- `bhiv-bucket` — starts `bhiv_bucket.py` via `uvicorn`
- `integration-bridge` — starts `integration_bridge_v2.py`

## Minimum deploy for prompt-runner + creator-core flow

1. Deploy `prompt-runner` and `creator-core` services.
2. Set environment variables for each service.

### prompt-runner env vars

- `GROQ_API_KEY` = your Groq API key
- `CREATOR_CORE_URL` = URL of Creator Core service, e.g. `https://creator-core.onrender.com/creator-core/generate-blueprint`

### creator-core env vars

- `BHIV_CORE_URL` (optional for now)
- `BUCKET_URL` (optional for now)
- `ENABLE_BHIV_FORWARD` = `false` by default

## Verification

Once both services are deployed and healthy, verify the core prompt flow:

### 1. Prompt Runner health

```bash
curl https://prompt-runner.onrender.com/health
```

### 2. Creator Core blueprint generation

```bash
curl -X POST https://creator-core.onrender.com/creator-core/generate-blueprint \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Test prompt","module":"creator","intent":"generate","topic":"test","tasks":["task1"],"output_format":"text"}'
```

### 3. Prompt Runner request flow

```bash
curl -X POST https://prompt-runner.onrender.com/run \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Design a simple landing page"}'
```

## Notes

- `prompt-runner01/run_server.py` now binds to `0.0.0.0`, which is required for Render.
- If you want full pipeline usage later, deploy `bhiv-core`, `bhiv-bucket`, and `integration-bridge`.
- Replace hostnames in `render.yaml` with the actual Render-generated URLs if needed.
