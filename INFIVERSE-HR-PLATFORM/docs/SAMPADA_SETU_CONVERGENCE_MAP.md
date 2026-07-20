
## SAMPADA_SETU_CONVERGENCE_MAP

Status: Draft

Owner: Rishabh Yadav (authority and sign-off required)

Purpose:
- Define the interaction model and boundaries between Sampada and SETU domain systems (Niyantran, Artha, Logistics, CRM, SETU aggregator) to ensure clear ownership, participation rules, and signal exchange contracts.

Scope:
- Covers API-level interactions, event/workflow integrations, replay and trace expectations, and boundary enforcement required for safe convergence.

1) Ownership Matrix

| System | Primary Ownership | Responsibilities |
|---|---:|---|
| Sampada (this repo) | Rishabh Yadav (owner) | Intelligence, workforce visibility, candidate/recruiter portals, data models, dashboards (visibility-only execution) |
| Niyantran | Niyantran Owner (external) | Tasking, reviews, execution participation, execution telemetry, testing orchestration, payroll calculation participation (not ownership) |
| Artha | Artha Owner (external) | Financial systems, payroll ownership, payments, ledger reconciliation |
| Logistics | Logistics Owner (external) | Logistics (asset movement, equipment provisioning) |
| CRM | CRM Owner (external) | Relationship intelligence, client engagement, contact records |
| SETU (Aggregator) | SETU Platform | Cross-domain aggregation, unified operational visibility, cross-system alerting and analytics |

Notes:
- Payroll visibility participation ≠ payroll ownership: Sampada may surface payroll cues (visibility) but must not perform payroll calculations or finalization — that remains Artha's responsibility.

2) Participation Matrix

- Participation summarizes how each system participates in functional areas (Read = visibility only, Write = authoritative change allowed, Participate = contribute signals or calculations):

| Functional Area | Sampada | Niyantran | Artha | Logistics | CRM | SETU |
|---|---:|---:|---:|---:|---:|---:|
| Hiring Intelligence | Read & Provide Signals | Participate (tasking) | Read | Read | Participate (candidate relationships) | Aggregate |
| Workforce Operations | Read & Surface | Participate (execution telemetry) | Authoritative (payroll) | Authoritative (logistics ops) | Read | Aggregate |
| Payroll | Visibility-only | Participation (telemetry inputs) | Ownership | Read | Read | Aggregate/View |
| Tasking / Execution | Provide context & visibility | Ownership (tasking engine) | Read | Participate | Read | Aggregate |
| Notifications & Workflow | Trigger & Surface | Participate (execution) | Read | Participate | Participate | Aggregate/Orchestrate visibility |
| Observability & Replay | Provide audit data & traces | Provide execution telemetry | Provide financial traces | Provide logistics traces | Provide CRM traces | Aggregate and correlate |

3) Signal Exchange Model (example signals & contracts)

- Source: canonical API contracts and integration maps (see `backend/handover/api_contract` and `backend/handover/integration_maps`). Use these canonical endpoints as the baseline for signal shapes.

- Example signals (owner → consumer) and mapping to endpoints:

	- Job/Match Request
		- Source: Client/Portal → Gateway (`GET /v1/match/{job_id}/top` or `POST /v1/match/batch`)
		- Consumer: Agent Service (internal POST /match)
		- Payload: job_id, job_requirements, candidate_ids (optional)

	- Workflow Trigger (candidate application, shortlist, interview)
		- Source: Gateway → LangGraph (`POST /v1/langgraph/trigger`)
		- Payload: { workflow_id, workflow_type, input_data: { candidate_id, job_id, candidate_email, job_title } }

	- RL Feedback
		- Source: Gateway/Portal → LangGraph (`POST /rl/feedback`) and `POST /v1/feedback`
		- Payload: { candidate_id, job_id, feature_scores, human_feedback }

	- Payroll Cue (visibility)
		- Source: Artha → SETU (financial events) and Artha → Sampada (visibility API or event feed)
		- Payload (visibility-only): { employee_id, payroll_period, gross_amount, payroll_state: "calculated|processed|error", minimal identifiers }
		- Constraints: PII minimization, hashed identifiers where possible, explicit opt-in for payroll visibility per tenant

	- Execution Telemetry
		- Source: Niyantran → SETU / Sampada (execution telemetry feed)
		- Payload: { task_id, executor_id (hashed), start_ts, end_ts, status, trace_id }

4) Replay Expectations

- Sampada must produce deterministic, chronological audit logs for actions and state transitions. Requirements:
	- Audit logs persisted to `audit_logs` collection with: timestamp, correlation_id, actor (service/role), action, payload reference, prior_state, post_state.
	- Replay engine: `evidence/replay/replay_script.js` must reconstruct state from ordered audit logs.
	- Integration requirement: external systems (Niyantran, Artha, LangGraph) must include correlation IDs when sending execution telemetry so SETU can correlate across systems.

5) Trace Expectations (observability contract)

- Correlation & trace fields (canonical):
	- `correlation_id` (UUID) — must be present on all cross-system requests/events
	- `trace_timestamp` (ISO8601 UTC)
	- `source_system` (e.g., Sampada, Niyantran, Artha)
	- `event_type` (e.g., candidate_applied, match_requested, payroll_calculated)
	- `actor_id` (hashed user/tenant id where PII not required)
	- `status` (success | failure | in_progress)
	- `duration_ms` (optional)
	- `payload_ref` (pointer to stored payload or minimal inline payload)

- Trace propagation rules:
	- Services must accept an incoming `correlation_id` header and forward it to downstream systems.
	- Gateways must inject `correlation_id` when missing and return it in responses.
	- For long-running workflows, update `progress_percentage` and write periodic trace checkpoints to `audit_logs`.

6) Boundary Enforcement & Governance Rules

- Non-negotiable rules (from Task18):
	- Do not convert intelligence into execution authority. Sampada surfaces intelligence; execution decisions remain within owning systems.
	- Do not introduce surveillance-driven scoring or dopamine gamification mechanisms.
	- Do not restart or re-negotiate settled ownership boundaries in this work.

- Specific enforcement measures:
	- RBAC & Auth: All API calls must be authenticated (API Key or JWT); Gateway enforces tenant isolation.
	- Data Minimization: Only expose payroll cues and sensitive fields when explicit signed participation is present; use hashing/ tokenization for identifiers.
	- Auditability: All cross-system actions must write audit events with correlation IDs; replayability is mandatory.
	- Opt-in Participation: Any system that provides telemetry or visibility must be registered in SETU ownership matrix and have a signed participation contract.

7) Gaps & Action Items

- Missing owner contacts for Niyantran/Artha/Logistics/CRM — request owner names and API docs.
- Confirm exact Artha payroll visibility API (endpoint, payload, auth). If unavailable, define a minimal visibility contract to request from Artha.
- Confirm Niyantran execution telemetry fields and desired frequency.

Next steps (Phase 2 execution):
1. Reach out to system owners (Rishabh to authorize outreach) to obtain integration contracts and signing of participation matrix.
2. Convert the examples above into machine-readable event schemas (JSON Schema) and place them under `docs/schemas/`.
3. Add signal routing examples and sample curl commands for each integration and include verification tests in `backend/handover/postman/`.

TODOs:
- Add owner contact details and concrete external API endpoints (Artha/Niyantran/Logistics/CRM).
- Produce JSON Schemas for key signals: `match_request`, `workflow_trigger`, `execution_telemetry`, `payroll_visibility`

