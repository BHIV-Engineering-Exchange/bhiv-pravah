# Remote and Mixed Deployment Constraints

**Date:** 2026-07-07  
**Status:** NOT RUN (documented blocker)

## What was done

- Fixed `render.yaml` creator-core `startCommand` (was invalid `uvicorn creator-core.Core-Integrator-Sprint-1.1.main:app`; now `python creator-core/Core-Integrator-Sprint-1.1/main.py`)
- Added Render service definitions for **cet**, **sarathi**, **gate** (8-service mesh)
- Updated integration-bridge Render env to include `CET_URL`, `SARATHI_URL`, `GATE_URL`
- Extended `vercel.json` with `api/cet.py`, `api/sarathi.py`, `api/gate.py`, `api/integration-bridge.py` serverless wrappers

## Blocker — no live remote trace

This sprint environment has **no Render/Vercel deploy credentials** and no provisioned remote hosts. Cannot produce a real remote `trace_id` or mixed local/remote trace without:

1. `render deploy` (or equivalent) for all 8 services
2. Setting cross-service URLs in each service's environment
3. Running `run_comprehensive_live_tests.py` with `BASE` pointed at remote Integration Bridge

## Mixed deployment plan (not executed)

| Topology | Local | Remote |
|----------|-------|--------|
| Option A | BHIV Core, Bucket | Integration Bridge, CET, Sarathi, Gate, Prompt Runner, Creator Core |
| Option B | Integration Bridge + Bucket | Authority stages + execution |

**Constraint:** Until remote hosts are live, mixed validation remains **NOT RUN**. Local 8-service validation is complete (see `05_evidence_packets/comprehensive_live_test_results.json`).

## Prior port-8000 blocker (resolved locally)

Earlier test run hit **Nyaya Legal AI** on port 8000 instead of Creator Core. Verified fix: `start_all.py` + orchestrator starts `creator-core/Core-Integrator-Sprint-1.1/main.py`; health check requires `creator_core_endpoint` in root response.
