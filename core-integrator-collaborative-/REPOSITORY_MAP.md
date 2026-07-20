# Repository Map

## Root Overview

This repository is organized to support a multi-service integration pipeline. Key top-level files and folders are:

- `.gitignore` — local ignore rules
- `.env*` — environment variable templates and deployment-specific overrides
- `README.md` — primary project overview and quick start guide
- `DEPLOYMENT_GUIDE.md` — deployment instructions (existing, to be aligned with this handover)
- `start_all.py` — orchestrated local startup for all services
- `deploy_and_test.py` — deployment and test helper script
- `test_services.py` — health check script for services
- `integration_bridge.py` — full pipeline orchestrator
- `main.py` — BHIV Core runtime service
- `bhiv_bucket.py` — artifact storage service
- `full_tantra_flow_test.py` — full TANTRA flow validation harness
- `config/` — centralized configuration definitions
- `creator-core/` — Creator Core service and engine
- `prompt-runner01/` — Prompt Runner FastAPI service
- `audit_packets/` — audit, review, replay, and architecture analysis artifacts
- `data/` — runtime artifacts and storage
- `db/` — database and telemetry storage
- `review_packets/` — handover review packet output

## Entry Points

### Local startup
- `python start_all.py` — starts all services in dependency order using `core/service_orchestrator.py`
- `python deploy_and_test.py` — deploys services and verifies readiness

### Single service
- `python prompt-runner01/run_server.py` — runs the Prompt Runner FastAPI service
- `python creator-core/Core-Integrator-Sprint-1.1/main.py` — runs Creator Core
- `python main.py` — runs BHIV Core
- `python integration_bridge.py` — runs Integration Bridge
- `python bhiv_bucket.py` — runs BHIV Bucket

### Tests and validation
- `python test_services.py` — health checks for each service
- `python run_comprehensive_live_tests.py` — live 8-service + 4-product validation
- `python test_production_runtime.py` — cold-start + auth + pipeline validation
- `python full_tantra_flow_test.py` — full TANTRA validation and replay proof generation
- `python -m pytest creator-core/Core-Integrator-Sprint-1.1/tests` — Creator Core unit tests

## Important folders

### `config/`
- `services.yml` — service definitions, ports, and environment settings
- `config_manager.py` — config loader/validator used by orchestrator
- `service_urls.py` — runtime URL construction
- `config.py` — startup validation and configuration helpers

### `core/`
- `service_orchestrator.py` — starts services respecting dependencies and health checks
- `service_mesh.py` — service health and connection helpers

### `creator-core/Core-Integrator-Sprint-1.1/`
- `main.py` — Creator Core FastAPI endpoint
- `app_config.py` — Creator Core environment and URL configuration
- `creator_core_engine/` — blueprint generator, bucket adapter, telemetry, and service logic
- `tests/` — Creator Core tests
- `EXTERNAL_SERVICES.md` — Creator Core external service instructions

### `prompt-runner01/`
- `run_server.py` — FastAPI prompt-to-instruction service

### `audit_packets/`
- `architecture/` — architecture audit, component boundaries, and ecosystem analysis
- `replay_logs/` — reserved for replay validation logs and proofs
- `governance/`, `handover/`, `integration_logs/`, `pipeline/`, `runtime_proofs/`, `security/` — audit and handover artifacts

### `bhiv_bucket/`
- `instructions/`, `blueprints/`, `executions/`, `results/`, `traces/` — stored artifact files
- `results/` and `traces/` contain live sample artifacts and proof traces

## Critical services

- **Prompt Runner** — `prompt-runner01/run_server.py`
- **Creator Core** — `creator-core/Core-Integrator-Sprint-1.1/main.py`
- **BHIV Core** — `main.py`
- **Integration Bridge** — `integration_bridge.py` (orchestrates Prompt Runner → Creator Core → CET → Sarathi → Gate → BHIV Core → Bucket)
- **CET Service** — `cet_service.py`
- **Sarathi Service** — `sarathi_service.py`
- **Gate Service** — `gate_service.py`
- **BHIV Bucket** — `bhiv_bucket.py`

## Configuration files

- `config/services.yml` — default service topology and runtime configuration
- `.env.example` — base environment variable template
- `.env.integration_bridge.example` — Integration Bridge environment template
- `.env.production` — production environment overrides
- `.env.vercel` — Vercel deployment environment
- `creator-core/Core-Integrator-Sprint-1.1/.env.example` — Creator Core service variables

## Environment files

- `.env` — local environment overrides (not committed)
- `.env.integration_bridge` — local Integration Bridge overrides
- `.env.production` — production environment values
- `.env.vercel` — Vercel-specific environment configuration

## Test files

- `test_services.py` — microservice health checker
- `full_tantra_flow_test.py` — end-to-end TANTRA flow and replay validation
- `creator-core/Core-Integrator-Sprint-1.1/tests/test_creator_core_engine.py` — Creator Core unit tests

## Replay and proof files

- `bhiv_bucket/traces/*.json` — stored trace indexes and artifact chains
- `bhiv_bucket/results/*.json` — example result artifacts
- `audit_packets/replay_logs/` — replay validation logs and proof artifacts

## Review packet location

- `review_packets/full_handover_packet_v1.md`

## Expected directory structure

```
/ (repository root)
├─ .env*
├─ README.md
├─ start_all.py
├─ deploy_and_test.py
├─ test_services.py
├─ integration_bridge.py
├─ main.py
├─ bhiv_bucket.py
├─ full_tantra_flow_test.py
├─ config/
├─ core/
├─ creator-core/Core-Integrator-Sprint-1.1/
├─ prompt-runner01/
├─ audit_packets/
├─ bhiv_bucket/
├─ data/
├─ db/
├─ review_packets/
```

## Starting points for a new developer

1. Read `README.md` for high-level flow.
2. Inspect `integration_bridge.py` for pipeline orchestration.
3. Open `creator-core/Core-Integrator-Sprint-1.1/main.py` for Creator Core entrypoint.
4. Review `main.py` for BHIV Core gateway and replay logic.
5. Check `bhiv_bucket.py` for artifact storage and trace retrieval.
6. Validate with `python test_services.py` and `python full_tantra_flow_test.py`.
