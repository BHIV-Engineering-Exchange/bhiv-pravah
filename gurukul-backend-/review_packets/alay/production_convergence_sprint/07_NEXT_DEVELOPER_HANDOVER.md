# Next Developer Handover Guide

This guide is written for engineers taking over the Gurukul Observability codebase.

## 1. Project Hardening Status
The platform has transitioned from developer-only simulation to production-hardened status:
* All debug fallback keys have been removed.
* SQLite connections are disabled in production.
* Replays are validated deterministically via output hashes.

## 2. Key Modules to Maintain
* **Telemetry Validator:** [tantra_schema_validator.py](../../..//backend/app/services/tantra_schema_validator.py). To update schemas or add fields, modify the `PRAVAH_REQUIRED_FIELDS` or `BUCKET_REQUIRED_FIELDS` structures.
* **Replay Orchestrator:** [prana_replay_orchestrator.py](../../..//backend/app/services/prana_replay_orchestrator.py). Replay matches now run against logged outputs. Avoid introducing code that makes live LLM calls during replay runs.
* **Pravah Adapter:** [pravah_adapter.py](../../..//backend/app/services/pravah_adapter.py). Emits signal events. Always ensure the `TANTRA_API_KEY` is loaded and passed to the constructor.

## 3. Operational Testing Procedures
Before committing code changes, run the following verification steps:

```bash
# 1. Export required environment variables
$env:DATABASE_URL="postgresql://postgres:postgres@localhost/postgres"
$env:TANTRA_API_KEY="test-secret-key"

# 2. Run convergence unit tests
python -m pytest tests/test_convergence_convergence.py -v

# 3. Run connectors and retry simulation checks
python -m pytest tests/test_tantra_connectors.py -s
```
