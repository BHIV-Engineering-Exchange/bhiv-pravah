# Schema Catalog — docs/schemas

This folder contains canonical JSON Schemas used as signal contracts between Sampada and SETU partners.

Purpose
- Provide machine-readable contracts for producers and consumers (Gateway, Agent, LangGraph, Niyantran, Artha)
- Enable CI validation of schema examples and runtime payloads
- Serve as a single source-of-truth for dashboard wiring and replay/trace tooling

Files
- `match_request.json` — match requests from Gateway → Agent; used by Control Center for matching panels
- `workflow_trigger.json` — canonical workflow trigger payloads for LangGraph and replay
- `execution_telemetry.json` — execution telemetry events produced by Niyantran / execution systems
- `payroll_visibility.json` — minimal payroll visibility payloads (visibility-only; no PII)

Producers / Consumers (high level)
- Gateway (producer/consumer): produces `workflow_trigger`, consumes `execution_telemetry`, produces `match_request`
- Agent (consumer): consumes `match_request` and returns match responses
- LangGraph (consumer/producer): consumes `workflow_trigger`, produces `execution_telemetry` via webhooks
- Niyantran / Execution systems (producer): emit `execution_telemetry`
- Artha (producer): emit `payroll_visibility` (permissioned channel)

Validation (local)
1. Ensure your Python environment has `jsonschema` installed. From repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

2. Run the schema validation test (pytest):

```powershell
pytest -q tests/test_schemas.py
```

Validation (CI)
- Add a job that runs `pytest -q tests/test_schemas.py` to fail the pipeline when schema examples do not conform.

Versioning
- Increment schema versions by adding a `version` field or using a changelog entry in this README when making breaking changes.

Contact
- For schema disputes or ownership questions, use the owner request templates in `docs/requests/` and escalate to Rishabh Yadav for approval.
