# Remote Deployment Results

**Status:** not executed in this sprint session  
**Classification:** planned / documented procedure

## What exists in repo

- `vercel.json` — 4 serverless functions (prompt-runner, creator-core, bhiv-core, bucket)
- `render.yaml` — multi-service Render config (needs module path fix per audit)
- `VERCEL_DEPLOYMENT.md`, `RENDER_DEPLOYMENT.md`

## Gap

Vercel deploys 4 of 8 services. CET, Sarathi, Gate, and Integration Bridge are **not** on Vercel yet. Full remote validation of the wired pipeline requires either:

1. Extending `vercel.json` / `api/` for remaining services, or
2. Deploying the full mesh on Render with corrected start commands

## Recommended remote test plan

```bash
vercel --prod
# Set env vars from config/.env.example with real domain URLs
curl https://your-app.vercel.app/api/prompt-runner/health
curl https://your-app.vercel.app/api/bhiv-core/system/health
```

## Pass/fail

- **NOT RUN** — no live remote trace_id captured in this session
