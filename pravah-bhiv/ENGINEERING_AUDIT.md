# BHIV Pravah — Deep Engineering Audit

> **Evidence Standard**: All findings derive from direct source-code inspection, call-chain tracing, and live test execution (pytest 9.0.2 / Python 3.14.3 / Windows). Documentation claims are explicitly distinguished from verified code behaviour.

---

## 0. Repository File Structure

> Captured from live filesystem. __pycache__ and .pyc files omitted for clarity.

`
pravah-bhiv/                                        ← REPO ROOT
|
+-- ENGINEERING_AUDIT.md                            ← This file
+-- PHASE12_CROSS_GROUP_CONTRACT_AUDIT.md           ← Phase report (documentation debt)
+-- (other phase-report .md files)
|
\-- backend/                                        ← ENTIRE BACKEND HERE
    |
    |-- agent_runtime.py                            ← Flask-based agent runtime (port 7000)
    |-- autonomy_loop.py                            ← 904 bytes — not connected to main path
    |-- auto_scaler.py
    |-- observer_server.py                          ← Observer server (~44 KB, port 8600)
    |-- config.py                                   ← Global thresholds (CPU_SCALE_UP_THRESHOLD etc.)
    |-- wsgi.py
    |-- requirements.txt                            ← numpy<2.0.0 — BREAKS on Python 3.14
    |-- requirements-deploy.txt
    |-- requirements_core.txt
    |-- docker-compose.yml                          ← 500 lines; NO executor service on port 5003
    |-- docker-compose.local.yaml
    |-- Dockerfile
    |-- Procfile
    |-- trace_log.jsonl                             ← COMMITTED LOG FILE — should be gitignored
    |-- payload_integrity.log                       ← COMMITTED LOG FILE
    |-- runtime_rl_proof.log                        ← COMMITTED LOG FILE
    |-- executer.log                                ← COMMITTED LOG FILE
    |-- mcp_inbox.json                              ← EMPTY [] — stale artifact
    |-- mcp_messages.json                           ← EMPTY [] — stale artifact
    |-- mcp_outbox.json                             ← EMPTY [] — stale artifact
    |-- runtime_payload_schema.json
    |-- e2e_integration_test.py
    |-- e2e_persistence_test.py
    |-- integration_client.py
    |-- interactive_demo.py
    |-- validate_demo_lock.py
    |-- validate_env.py
    |-- onboarding_entry.py
    |-- deploy.py / deploy_orchestrator.py / deploy_pravah.py
    |-- (30+ Markdown phase-report .md files — documentation debt)
    |
    |-- .github/
    |   \-- workflows/
    |       \-- cicd.yml                            ← CI/CD pipeline
    |
    |-- contracts/                                  ← PRESERVE — Pydantic v2 contract models
    |   |-- decision_contract.py                    ← DecisionContract schema
    |   |-- execution_contract.py                   ← ExecutionContract + FSM state machine
    |   |-- execution_state.py
    |   |-- policy_snapshot.py
    |   |-- runtime_attestation.py
    |   |-- runtime_contract.py
    |   \-- semantic_transition_validator.py
    |
    |-- control_plane/                              ← CORE SYSTEM
    |   |-- multi_app_control_plane.py              ← App registry + decision history + Sarathi emit
    |   |-- app_override_manager.py                 ← Manual freeze management
    |   |
    |   |-- apps/registry/*.json                    ← 28 registered applications (JSON specs)
    |   |
    |   |-- backend/                                ← FastAPI application
    |   |   |-- run.py
    |   |   \-- app/
    |   |       |-- main.py                         ← ⚠️ 1401 LINES — all routes here
    |   |       |-- decision_engine.py              ← PRESERVE — pure function, correct
    |   |       |-- runtime_adapter.py              ← ⚠️ BROKEN — NameError (decision undefined)
    |   |       |-- execution_simulator.py          ← DELETE — dead/commented-out code
    |   |       |-- integration_bridge.py           ← Flask-FastAPI bridge
    |   |       |-- config.py                       ← CPU_SCALE_UP_THRESHOLD=95 (ignored!)
    |   |       |-- schemas.py                      ← Pydantic schemas (Environment, EventType etc.)
    |   |       |-- dashboard_api.py
    |   |       \-- runtime.py
    |   |
    |   |-- capabilities/                           ← Capability system — MOSTLY WORKING
    |   |   |-- execution_rights_adapter.py         ← ⚠️ DO NOT TOUCH — VERIFIED_CAPABILITY_MAPPINGS
    |   |   |-- capability_registry_manager.py      ← PRESERVE — reads registry JSON
    |   |   |-- capability_discovery.py             ← PRESERVE — discovery API
    |   |   \-- registry/                           ← 8 capability JSON definitions
    |   |       |-- bucket-evidence.json
    |   |       |-- governed-execution.json         ← Only one that can execute (governance OK)
    |   |       |-- group1-observation-api.json     ← Has live endpoint; NO execution rights mapping
    |   |       |-- group2-scientific-context.json  ← NO execution rights mapping
    |   |       |-- group3-field-edge.json          ← service_hosted: false; NO execution rights
    |   |       |-- replay-runtime.json             ← NO execution rights mapping
    |   |       |-- svacs-runtime.json              ← NO execution rights mapping
    |   |       \-- vana-environmental_observation.json  ← mapping exists; BLOCKED by governance
    |   |
    |   |-- core/                                   ← Runtime core modules
    |   |   |-- action_governance.py                ← ⚠️ DO NOT TOUCH — 734 lines, crypto verify
    |   |   |-- execution_lineage.py                ← ⚠️ DO NOT TOUCH — signed hash-chain
    |   |   |-- trace_logger.py                     ← ⚠️ RACE CONDITION — module global _last_stage
    |   |   |-- redis_event_bus.py                  ← DISCONNECTED — Redis not used in main path
    |   |   |-- rl_orchestrator_safe.py
    |   |   |-- decision_arbitrator.py
    |   |   |-- agent_state.py / agent_memory.py / agent_logger.py / base_agent.py
    |   |   |-- event_bus.py / event_schema.py / sovereign_bus.py / realtime_bus.py
    |   |   |-- perception.py / perception_adapters.py
    |   |   |-- metrics_collector.py / metrics_aggregator.py / unified_metrics_schema.py
    |   |   |-- mcp_adapter.py / mcp_bridge.py / mcp_manager.py / mcp_schema.py
    |   |   |-- stage_determinism.py / verification.py / guaranteed_events.py
    |   |   |-- runtime_event_validator.py / runtime_event_lock.py
    |   |   |-- env_config.py / env_validator.py / input_validator.py
    |   |   |-- self_restraint.py / resilience.py / filesystem_stability.py / windows_compat.py
    |   |   |-- prod_logging.py / prod_safety.py / proof_logger.py / log_utils.py / logger.py
    |   |   |-- rl_decision_layer.py / rl_orchestrator_safe.py / rl_remote_client.py
    |   |   |-- rl_response_validator.py / rl_wiring.py / runtime_rl_pipe.py
    |   |   |-- state_adapter.py / memory_snapshot.py
    |   |   |-- contracts.py / registry_manager.py / text_input_onboarding.py
    |   |   \-- rl/                                 ← RL training artifacts (not inspected deeply)
    |   |       |-- external_api/rl_decision_brain.py
    |   |       \-- rityadani_decision_layer/decision.py
    |   |
    |   |-- security/                               ← Security layer
    |   |   |-- deterministic_policy_engine.py      ← ⚠️ DO NOT TOUCH — 668 lines, policy admission
    |   |   |-- semantic_guard_engine.py            ← Semantic validation (not fully inspected)
    |   |   \-- legitimacy_doctrine.py
    |   |
    |   |-- persistence/                            ← PRESERVE — real integrity guarantees
    |   |   |-- append_only_log.py                  ← HMAC hash-chain, append-only
    |   |   |-- hash_lineage_verifier.py
    |   |   \-- replay_index.py
    |   |
    |   |-- executor/                               ← DISCONNECTED / DEPRECATED
    |   |   |-- executor.py                         ← DELETE — "docker action svc" broken syntax
    |   |   |-- safe_executor.py                    ← DISCONNECTED — only via broken runtime_adapter
    |   |   \-- governance_gate.py                  ← DISCONNECTED — not called from main path
    |   |
    |   |-- deployment/                             ← Deployment validators
    |   |   |-- deployment_proof.py / healthcheck_replay.py
    |   |   |-- readiness_validator.py / recovery_validator.py / startup_validator.py
    |   |   \-- json_logger.py
    |   |
    |   |-- agents/                                 ← Agent implementations
    |   |   |-- auto_heal_agent.py / deploy_agent.py / multi_deploy_agent.py
    |   |   |-- issue_detector.py / uptime_monitor.py / rl_optimizer.py
    |   |   \-- decision/rl_brain/engine.py
    |   |
    |   |-- api/                                    ← Flask API endpoints
    |   |   \-- agent_api.py
    |   |
    |   |-- ml/                                     ← ML feature extraction
    |   |   |-- ml_feature_extractor.py
    |   |   \-- feature_schema.py
    |   |
    |   \-- telemetry/
    |       \-- telemetry_collector.py
    |
    |-- contracts/ (same as above, at backend root)
    |
    |-- security/                                   ← Service-level signing layer
    |   |-- signed_trace.py                         ← ⚠️ DO NOT TOUCH — HMAC signing, default keys
    |   |-- signing.py                              ← Service request signing
    |   |-- internal_requests.py                    ← Builds signed HTTP headers
    |   \-- nonce_store.py / nonce_store.json       ← ⚠️ File-based nonce store (race condition)
    |
    |-- executer/                                   ← "Sarathi Executer" service (in-memory only)
    |   |-- runner.py                               ← validate_caller + signal["status"]="success"
    |   |-- guard.py                                ← Nonce + signature + execution contract check
    |   \-- executor.py                             ← 253 bytes — stub
    |
    |-- sarathi/                                    ← Sarathi header builder
    |   |-- router.py                               ← build_sarathi_headers()
    |   \-- headers.py                              ← 141 bytes — stub only
    |
    |-- pravah_stream/                              ← ⚠️ In-memory event stream (NOT Redis)
    |   |-- stream.py                               ← _STREAM_BUFFER: list[dict] — lost on restart
    |   \-- rules.py                                ← validate_signal_passthrough()
    |
    |-- core_hooks/                                 ← Signal building + middleware hooks
    |   |-- signal_builder.py                       ← build_base_signal() — called by MultiAppCP
    |   |-- middleware.py / service_auth.py
    |   |-- contract_validator.py / rules.py
    |   \-- trace.py / context.py
    |
    |-- tests/                                      ← Phase-based pytest test files
    |   |-- test_phase8_execution_closure.py        ← PASSED 5/5 — core execution rejection paths
    |   |-- test_phase14_vana_bootstrap.py          ← PASSED 7/7 — VANA capability bootstrap
    |   |-- test_phase10_group1_integration.py      ← PASSED 1/1 — live HTTP to group1
    |   |-- test_unified_discovery.py               ← ⚠️ FAILS — assert 0 == 8
    |   |-- test_phase1_signed_lineage.py           ← Signed trace creation/verification
    |   |-- test_phase2_deterministic_policy_engine.py
    |   |-- test_phase3_persistence_sovereignty.py
    |   |-- test_phase4_semantic_guards.py
    |   |-- test_phase5_deployment_validators.py
    |   |-- test_phase6_vm_deployment.py
    |   |-- test_replay_sovereignty.py
    |   \-- test_semantic_transition_validator.py
    |
    |-- decision_brain/
    |   \-- decision_engine/decision_with_control_plane.py
    |
    |-- docs/
    |   |-- mermaid_diagrams.md
    |   \-- phase7/ (architecture diagrams: .png + .md)
    |
    |-- data/
    |   |-- evidence_bundles.json
    |   \-- onboarding_requests.jsonl
    |
    |-- deployment_verification_packet/             ← JSON evidence artifacts
    |   |-- constitutional_boundary_audit.json
    |   |-- ecosystem_summary.json
    |   |-- integration_evidence_packet.json
    |   |-- phase6_summary.json
    |   \-- prod_runtime_health.json
    |
    \-- frontend/                                   ← Next.js 14 + Tailwind CSS dashboard
        |-- package.json / next.config.js / tailwind.config.js
        \-- src/
            |-- app/                                ← Next.js App Router pages
            |-- components/                         ← React components
            \-- services/
                \-- api.ts                          ← Axios client for 3 backends (ports 8000, 7000, 8600)
`

### Key Counts
| Item | Count |
|------|-------|
| Registered applications (control_plane/apps/registry/) | 28 |
| Registered capabilities (control_plane/capabilities/registry/) | 8 |
| Capabilities with execution rights mappings | 2 |
| Test files | 13+ |
| Passing test files (verified) | 3 of 4 inspected |
| Failing test files | 1 (test_unified_discovery.py) |
| Lines in main.py | 1401 |
| Lines in action_governance.py | 734 |
| Lines in deterministic_policy_engine.py | 668 |
| Committed log files (should be gitignored) | 4+ |
| Empty JSON stubs committed | 3 |
| Markdown phase-report files in backend/ root | 30+ |

---

## 1. Executive Summary

**Overall Maturity: Early-Integration / Pre-Production**

BHIV Pravah is a multi-component control-plane intended to autonomously observe, decide, govern, and execute actions on managed services. The governance subsystem is architecturally solid. The execution subsystem is broken.

| Domain | Assessment |
|--------|-----------|
| Overall maturity | Early-Integration — not production-ready |
| End-to-end control loop | **OPEN-LOOP** — ingest->decision->governance VERIFIED; governance->executor **ALWAYS FAILS** |
| Security posture | HMAC-chain solid; zero API authentication — CRITICAL gap |
| Test suite | Key unit tests pass; integration broken; no E2E exists |

**Biggest Strengths**
- ActionGovernance + DeterministicPolicyEngine — cryptographic, deterministic, well-engineered
- ExecutionRightsAdapter — properly fail-closed with evidence-based capability mappings
- AppendOnlyLog + execution_lineage.py — real signed hash-chain integrity, not a placeholder
- DecisionEngine.decide() — pure stateless function, fully correct

**Top 5 Risks**
1. **Executor always fails** — main.py:701 POSTs to localhost:5003; no service runs there anywhere
2. **runtime_adapter.py NameError** — decision variable used after DecisionEngine.decide() was commented out
3. **No API authentication** — /control-plane/runtime-ingest is completely open
4. **VANA trust gap** — vana-environmental_observation passes execution rights but governance blocks it
5. **test_unified_discovery.py FAILS** — list_runtime_entities() returns 0 capabilities in test context

---

## 2. Actual Control Loop (Verified)

`
POST /control-plane/runtime-ingest
  |
  v
RuntimeIngestPayload (Pydantic) -> INGESTED_RUNTIME_STATE[service_id]  [IN-MEMORY]
  |
  v
DecisionEngine.decide()  [PURE FUNCTION, CORRECT]
  |
  +-- noop -> return immediately
  +-- capability empty -> CAPABILITY_REQUIRED
  |
  v
authorize_execution(capability_id, action)  [execution_rights_adapter.py]
  | CapabilityNotFound -> rejected
  | MappingNotFound -> rejected
  | -> sign_trace(HMAC auth_payload)  [VERIFIED]
  |
  v
ActionGovernance.evaluate_contract()  [VERIFIED]
  | signature invalid -> blocked
  | source_id not in trusted_signers -> blocked
  |   trusted_signers = {sarathi, governance, policy-authority}
  |   VANA NOT IN SET -> VANA always blocked
  | cooldown/repetition/eligibility -> blocked
  | DeterministicPolicyEngine.admit() -> final gate
  |
  v (governance passes)
requests.post("http://localhost:5003/execute-action")
  |
  X  ConnectionRefusedError ALWAYS -- NO SERVICE ON PORT 5003
  |
  v
Exception -> (False, str(exception))  [ACTION SILENTLY DROPPED]
  |
  v
MultiAppControlPlane.append_decision_history() -> JSONL [PERSISTENT]
  |
  +-> Sarathi signal -> in-memory buffer only [NOT a real executor]
`

**VERDICT: OPEN-LOOP. Governance is real. Execution always fails.**

---

## 3. Control Loop Step-by-Step Evidence

| Stage | File:Line | Status | Evidence |
|-------|-----------|--------|---------|
| Ingestion | main.py:1155 | VERIFIED | Pydantic schema, Phase 8 tests |
| Runtime state | main.py:1167 | PARTIAL | In-memory dict, lost on restart |
| Decision | decision_engine.py:20 | VERIFIED | Pure function, correct; CPU threshold bug |
| Execution rights | execution_rights_adapter.py:203 | VERIFIED | Phase 8+14 PASSED |
| Governance | action_governance.py:293 | VERIFIED | Crypto sig, cooldowns; VANA blocked |
| Executor dispatch | main.py:701 | **BROKEN** | localhost:5003 — no service |
| Execution result | — | **NOT IMPLEMENTED** | No feedback from HTTP response |
| State update | — | **NOT IMPLEMENTED** | INGESTED_RUNTIME_STATE never updated post-exec |
| Telemetry feedback | — | **NOT IMPLEMENTED** | No loop closure |

---

## 4. Trace Sovereignty Matrix

| Claim | Code Location | Status |
|-------|--------------|--------|
| Traces HMAC-signed | signed_trace.py:41 | VERIFIED |
| Signature verified before execution | action_governance.py:332-336 hmac.compare_digest | VERIFIED (code path) |
| Unsigned authorization rejected | action_governance.py:320 | VERIFIED |
| LINEAGE_SIGNING_KEY required in prod | signed_trace.py:14 | VERIFIED |
| Default dev key hardcoded | signed_trace.py:16 "pravah-sovereign-lineage-key" | SECURITY RISK |
| Nonce replay protection | executer/guard.py:33 check_nonce() | VERIFIED (code, not in main path) |
| Two disconnected trace systems | trace_logger.py vs execution_lineage.py | FRAGMENTATION |
| No trace_id in ingest payload | RuntimeIngestPayload schema | UNTRACED |

**Key finding**: trace_logger.py uses module-global _last_stage — RACE CONDITION under concurrent requests. execution_lineage.py uses proper signed JSONL. These two systems are NOT connected — a runtime-ingest call creates trace_logger entries but ZERO lineage records.

---

## 5. Decision Engine Audit

| Decision | Trigger | Config Read? | Status |
|---------|---------|-------------|--------|
| scale_up | cpu >= 90 (HARDCODED) | NO — config.py says 95 | **BUG** |
| scale_down | cpu < 30 | YES | CORRECT |
| scale_up (mem) | memory > 85 | YES | CORRECT |
| noop | no threshold | — | CORRECT |
| env override | action not in ACTION_SCOPE[env] | YES | CORRECT |

CPU_SCALE_UP_THRESHOLD=95 in config.py is silently ignored; decision_engine.py hardcodes >= 90.

---

## 6. Capability Mapping Coverage

| Capability | Registry Entry | Execution Rights Mapping | Can Execute? |
|-----------|---------------|------------------------|-------------|
| governed-execution | YES | YES (source_id: governance) | YES (exec fails at port 5003) |
| vana-environmental_observation | YES | YES (source_id: VANA) | **NO — VANA not in trusted_signers** |
| group1-observation-api | YES (live endpoint) | **NO** | NO |
| group2-scientific-context | YES | **NO** | NO |
| group3-field-edge | YES | **NO** | NO |
| bucket-evidence | YES | **NO** | NO |
| replay-runtime | YES | **NO** | NO |
| svacs-runtime | YES | **NO** | NO |

6 of 8 capabilities cannot execute. trusted_signers = {sarathi, governance, policy-authority} — VANA not included.

---

## 7. API & Endpoint Audit

ALL endpoints: ZERO authentication required.

| Endpoint | Status |
|----------|--------|
| POST /control-plane/runtime-ingest | ACTIVE, unauthenticated — core ingest |
| POST /process-runtime | ACTIVE, disconnected from governance |
| GET /live-dashboard | PARTIAL — synthetic + psutil data |
| GET /autonomous-status | MOCK — loop_running:True hardcoded, no loop |
| POST /pravah/events | PLACEHOLDER — returns CONNECTED, does nothing |
| POST /api/control-plane/override | **BROKEN — route not implemented** |
| GET /api/lineage/:id | REAL — reads signed JSONL |
| GET /control-plane/apps | REAL — reads registry JSON |
| GET /control-plane/health | REAL — reads decision_history.jsonl |

frontend/src/services/api.ts:146 calls POST /api/control-plane/override — gets 404.

---

## 8. Broken Functionality (Evidence-Based)

### P0: Executor dispatch always fails (localhost:5003)
- main.py:701: requests.post("http://localhost:5003/execute-action")
- docker-compose.yml: 500 lines, services=redis/control-plane/decision-brain/observer/nginx
- Port 5003: NOT DEFINED ANYWHERE
- Every non-noop action is silently dropped

### P0: runtime_adapter.py NameError
- Line 68 COMMENTED OUT: # decision = DecisionEngine.decide(decision_request)
- Lines 74+: decision.selected_action — NameError at runtime
- runtime_decision_cycle() and run_autonomous_control_plane() both crash

### P0: No API authentication
- main.py: no auth middleware, no JWT, no API key on any route
- /control-plane/runtime-ingest triggers real governance evaluation — completely open

### P1: VANA blocked by governance trust model
- execution_rights_adapter.py: authorized_source_id = "VANA"
- deterministic_policy_engine.py:143: trusted_signers = {sarathi, governance, policy-authority}
- VANA NOT in trusted_signers -> governance blocks execution
- Architecture mismatch between capability registry and governance model

### P1: test_unified_discovery.py FAILS
- Test output: assert 0 == 8 — list_runtime_entities() returns 0 capabilities
- MultiAppControlPlane cannot find registry JSON files from test instantiation path

### P1: Override endpoint missing
- frontend/src/services/api.ts:146: POST /api/control-plane/override
- main.py: NO handler for this route

### P2: CPU threshold config bug
- config.py:9: CPU_SCALE_UP_THRESHOLD = 95
- decision_engine.py:27: if request.cpu >= 90 — HARDCODED, config ignored

### P2: Module-global race condition in trace_logger
- trace_logger.py:43: _last_stage = None — module global
- Concurrent requests corrupt each other's stage tracking

---

## 9. Data & Persistence

| Data | Persistent? | Signed? | Race-safe? |
|------|------------|---------|-----------|
| INGESTED_RUNTIME_STATE | NO — in-memory | No | No |
| _RECENT_DECISIONS deque | NO — in-memory | No | No |
| decision_history.jsonl | YES | No | Partial |
| execution_lineage.jsonl | YES | YES (HMAC) | YES (locked) |
| governance_state.json | YES | No | YES (locked) |
| append_only_log.jsonl | YES | YES (HMAC) | YES (locked) |
| trace_log.jsonl | YES (in CWD!) | No | NO (module global) |
| pravah_stream buffer | NO — in-memory | No | YES (locked) |

trace_log.jsonl written to CWD (wherever uvicorn launches), not logs/ directory.
Redis declared in docker-compose; redis_event_bus.py exists; Redis NOT used in main path.

---

## 10. Security Audit

| Finding | Severity | Evidence |
|---------|---------|---------|
| No authentication on any endpoint | CRITICAL | No auth middleware in main.py |
| Default HMAC keys in dev/stage | HIGH | signed_trace.py:16 "pravah-sovereign-lineage-key" |
| VANA not in trusted_signers | MEDIUM | deterministic_policy_engine.py:143 |
| Executor port hardcoded | MEDIUM | main.py:701 localhost:5003 |
| Nonce store is a JSON file | MEDIUM | security/nonce_store.json — not atomic |
| CORS allows all localhost ports | LOW | main.py:110 localhost:\d+ |

---

## 11. Test Suite Results

| Test File | Result | Real Code? |
|-----------|--------|-----------|
| test_phase8_execution_closure.py (5 tests) | PASSED 5/5 | YES for A,B; PARTIAL for C,D |
| test_phase14_vana_bootstrap.py (7 tests) | PASSED 7/7 | YES |
| test_phase10_group1_integration.py (1 test) | PASSED | YES (requires live service) |
| test_unified_discovery.py (1 test) | **FAILED** | YES — broken integration |

Critical gaps: No test for executor dispatch, no E2E test, no negative security tests.

---

## 12. Feature Maturity Matrix

| Feature | Exists | Integrated | Working | Prod-Ready | Classification |
|---------|--------|-----------|---------|-----------|---------------|
| Runtime ingestion | YES | YES | YES | NO (no auth) | Partially Working |
| HMAC signing | YES | YES | YES | NO (default keys) | Mostly Working |
| Decision engine | YES | YES | YES | NO (CPU bug) | Mostly Working |
| Governance | YES | YES | YES | NO (no endpoint auth) | Mostly Working |
| Execution rights | YES | YES | YES | NO (2/8 mapped) | Mostly Working |
| Capability registry | YES | YES | YES | NO | Mostly Working |
| Executor dispatch | YES | BROKEN | NO | NO | **BROKEN** |
| Execution feedback | NO | NO | NO | NO | **Not Implemented** |
| Closed-loop control | NO | NO | NO | NO | **Not Implemented** |
| Autonomous loop | NO | NO | NO | NO | **Not Implemented** (NameError) |
| Execution lineage | YES | YES | YES | NO | Mostly Working |
| Unified discovery | NO | NO | NO | NO | **BROKEN** |
| API authentication | NO | NO | NO | NO | **Not Implemented** |
| Override endpoint | NO | NO | NO | NO | **Not Implemented** |

---

## 13. Prioritized Backlog

### P0 — Critical
1. **Executor missing (localhost:5003)** — main.py:701 — create service OR add EXECUTOR_URL env var
2. **No API authentication** — main.py — add JWT/API-key middleware
3. **NameError in runtime_adapter.py** — runtime_adapter.py:68 — uncomment or delete

### P1 — High
4. **VANA not in trusted_signers** — deterministic_policy_engine.py:143 — add "VANA" or make configurable
5. **Override endpoint missing** — main.py — implement POST /api/control-plane/override
6. **CPU threshold config ignored** — decision_engine.py:27 — use CPU_SCALE_UP_THRESHOLD
7. **trace_logger race condition** — trace_logger.py:43 — use thread-local or request-scoped context
8. **test_unified_discovery FAILS** — tests/test_unified_discovery.py — fix path issue
9. **numpy Python 3.14 incompatibility** — requirements.txt — pin numpy>=2.0.0 or Python<=3.12

### P2 — Medium
10. **No feedback loop after execution** — main.py:runtime_ingest — update state post-execution
11. **Missing execution rights for 6 capabilities** — execution_rights_adapter.py — add mappings
12. **Refactor 1401-line main.py** — split into routes/ package
13. **Make executor URL configurable** — main.py:701 — EXECUTOR_URL env var

### P3 — Low
14. Remove committed log files + multi.txt artifact
15. Replace datetime.utcnow() with datetime.now(timezone.utc)
16. Replace on_event("startup") with lifespan
17. Move 30+ Markdown reports from backend/ to docs/

---

## 14. Preserve / Refactor / Delete

### PRESERVE
- ExecutionRightsAdapter + authorize_execution — fail-closed, HMAC-signed, correct
- DeterministicPolicyEngine — deterministic, auditable
- ActionGovernance.evaluate_contract() — cryptographic verification chain
- AppendOnlyLog + HashLineageVerifier — real integrity
- execution_lineage.py — proper signed hash-chain
- contracts/ package — clean Pydantic v2 models
- signed_trace.py — correct HMAC, compare_digest used
- DecisionEngine.decide() — pure function

### REFACTOR
- main.py (1401 lines) -> routes/ package
- action_governance.py (734 lines) -> separate persistence
- trace_logger.py -> request-scoped context
- execute_action() -> EXECUTOR_URL env var

### REWRITE
- Executor dispatch layer (add retry, circuit breaker, service discovery)
- pravah_stream (replace in-memory with Redis Streams)

### DELETE
- execution_simulator.py — dead code
- control_plane/executor/executor.py — deprecated + broken
- multi.txt, committed log files, empty JSON stubs
- All 30+ Markdown phase reports from backend/ root

---

## 15. DO NOT TOUCH List

| Component | Why |
|-----------|-----|
| execution_rights_adapter.py:VERIFIED_CAPABILITY_MAPPINGS | Evidence file path checked on disk |
| deterministic_policy_engine.py:trusted_signers | Gatekeeper for execution; wrong values = privilege escalation |
| action_governance.py:evaluate_contract() | Crypto signature verification — breaking enables governance bypass |
| execution_lineage.py | Signed hash-chain — changing serialization invalidates all records |
| contracts/execution_contract.py | FSM transitions — changes break lineage replay |
| security/signed_trace.py:sign_trace() | Changing canonicalization breaks all existing signatures |

---

## 16. New Contributor Quick Start

### What Pravah Does
1. Receives telemetry via POST /control-plane/runtime-ingest
2. Decides action (scale_up/scale_down/restart/noop) deterministically
3. Validates via capability-based HMAC-signed execution rights
4. Gates through governance (cooldowns, repetition, policy engine, crypto)
5. Dispatches to executor (currently broken — localhost:5003)
6. Records decisions in JSONL files; provides Next.js dashboard

### Safe to Modify
- decision_engine.py — pure function, tested
- contracts/*.py — Pydantic models
- control_plane/capabilities/registry/*.json — adding capabilities
- frontend/src/ — dashboard
- tests/ — adding tests

### Required Environment Variables
| Var | Default | Required in Prod? |
|-----|---------|-----------------|
| LINEAGE_SIGNING_KEY | "pravah-sovereign-lineage-key" | YES — ValueError if missing |
| POLICY_SIGNING_KEY | "pravah-deterministic-policy-key" | Should be required |
| ENVIRONMENT | "dev" | YES |
| EXECUTOR_URL | NOT YET IMPLEMENTED | Must be added |

### To Run (Python 3.12 required for numpy compat)
`ash
cd backend/
pip install fastapi pydantic uvicorn requests psutil pytest
python -m uvicorn control_plane.backend.app.main:app --port 8000 --reload
python -m pytest tests/test_phase8_execution_closure.py tests/test_phase14_vana_bootstrap.py -v
`

---

## 17. Final Scorecard

| Area | Score | Reason |
|------|------:|--------|
| Architecture design | 5/10 | Thoughtful; dual-service confusion; executor missing |
| Governance | 7/10 | Well-engineered; VANA trust gap |
| Execution rights | 7/10 | Fail-closed; only 2/8 mapped |
| Decision engine | 7/10 | Pure function; CPU config bug |
| Executor integration | 1/10 | Always fails; port 5003 non-existent |
| Closed-loop control | 1/10 | No feedback; no post-execution state update |
| Trace sovereignty | 6/10 | HMAC chain correct; two disconnected systems |
| Security | 2/10 | Crypto solid; zero API auth; default keys |
| Test suite | 5/10 | Unit tests pass; integration broken; no E2E |
| Frontend | 5/10 | Mostly connected; missing override; synthetic data |
| Persistence | 5/10 | JSONL durable; in-memory state lost on restart |
| Reliability | 3/10 | Race conditions; no retry; no circuit breaker |
| Deployment | 3/10 | Docker compose partial; missing executor; dep conflicts |
| Docs accuracy | 3/10 | Phase reports overclaim; closed-loop falsely claimed |
| Dev experience | 3/10 | Dep install fails; no working E2E guide |
| **Overall** | **4/10** | Promising governance architecture; critical execution and security gaps |

---

## 18. Final Verdict

**Is the control loop genuinely closed?** NO. Governance boundary is real and enforced. Execution dispatch always fails (localhost:5003). No feedback loop exists. The system decides and validates — it cannot act.

**What works?** DecisionEngine, ExecutionRightsAdapter, ActionGovernance, DeterministicPolicyEngine, AppendOnlyLog, execution lineage, capability registry, dashboard read endpoints.

**What is broken?** Executor dispatch, runtime_adapter.py autonomous loop, VANA governance integration, unified discovery, override endpoint.

**What is not implemented?** API authentication, execution feedback loop, closed-loop control, execution rights for 6/8 capabilities.

**What is falsely claimed?** Closed-loop control. Autonomous loop running. test_unified_discovery passing. Full runtime integration.

**What must be fixed before production?** P0: executor service/URL, API authentication, runtime_adapter NameError. Then P1: VANA trust, override endpoint, CPU threshold bug, trace_logger race.

**What is production-ready?** Nothing. Core components are well-implemented but the system is not secure, not complete, and not end-to-end integrated.


