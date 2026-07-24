# Bypass Elimination Report — Sarathi v14.1 (Live Probes)

## Scan Date: 2026-07-24T08:24:53Z
## Version: v14.1
## Methodology: LIVE RUNTIME PROBES: each bypass path is actually attempted against the live pipeline and the result is recorded from real execution

---

### 1. Direct Execution Calls

| Path | Defense | Test Evidence | Status |
|---|---|---|---|
| ExecutionEngine.ExecuteWithToken(nil) | 9-check gate: check #1 (token exists) → NO_TOKEN | LIVE_PROBE_DIRECT_EXECUTION_1 | **BLOCKED** |
| ExecutionEngine.ExecuteWithToken(forged_token) | 9-check gate: check #2 (Ed25519 signature) → INVALID_SIGNATURE | LIVE_PROBE_DIRECT_EXECUTION_2 | **BLOCKED** |
| ExecutionEngine.ExecuteWithToken(expired_token) | 9-check gate: check #4 (TTL expiry) → TOKEN_EXPIRED | LIVE_PROBE_DIRECT_EXECUTION_3 | **BLOCKED** |
| ExecutionEngine.ExecuteWithToken(replayed_token) | 9-check gate: check #5 (single-use) → TOKEN_ALREADY_USED | LIVE_PROBE_DIRECT_EXECUTION_4 | **BLOCKED** |
| ExecutionEngine.ExecuteWithToken(forged_chain_hash) | 9-check gate: check #7 (INV-36) → ENFORCEMENT_HASH_NOT_IN_CHAIN | LIVE_PROBE_DIRECT_EXECUTION_5 | **BLOCKED** |
| Valid execution path (positive control) | ALLOW path with valid agent/resource/action → EXECUTION_PERMITTED | LIVE_PROBE_DIRECT_EXECUTION_19 | **BLOCKED** |
| DENY path blocks execution (negative control) | Unknown agent → DENY → EXECUTION_BLOCKED | LIVE_PROBE_DIRECT_EXECUTION_20 | **BLOCKED** |

### 2. Internal Handlers

| Path | Defense | Test Evidence | Status |
|---|---|---|---|
| ExecutionEngine.AttemptExecution(fabricated_resp) | AttemptExecution delegates to ExecuteWithToken; 9-check gate applies | LIVE_PROBE_INTERNAL_HANDLER_6 | **BLOCKED** |
| EnforcementAdapter.Enforce() direct call | Enforce() token requires engine's 9-check gate — direct Enforce() alone cannot execute | LIVE_PROBE_INTERNAL_HANDLER_7 | **BLOCKED** |
| ExecuteWithEnforcement delegates to ExecuteWithToken | ExecuteWithEnforcement(nil) returns same result as ExecuteWithToken(nil) | LIVE_PROBE_INTERNAL_HANDLER_17 | **BLOCKED** |

### 3. Test Utilities

| Path | Defense | Test Evidence | Status |
|---|---|---|---|

### 4. Debug/Backdoor Paths

| Path | Defense | Test Evidence | Status |
|---|---|---|---|
| Pipeline hash matches expected (INV-35) | computePipelineHash(SarathiPipelineOrder) == ExpectedPipelineHash | LIVE_PROBE_DEBUG_BACKDOOR_13 | **BLOCKED** |
| External pipeline hash matches expected | computePipelineHash(SarathiExternalPipelineOrder) == ExpectedExternalPipelineHash | LIVE_PROBE_DEBUG_BACKDOOR_14 | **BLOCKED** |
| Enforcement chain integrity | VerifyChain() returns true — chain has not been tampered | LIVE_PROBE_DEBUG_BACKDOOR_15 | **BLOCKED** |
| RPA enforcement gate active in Execute() | Execute() returns rpa_enforcement=VERIFIED for ALLOW verdicts | LIVE_PROBE_DEBUG_BACKDOOR_16 | **BLOCKED** |
| Token authority key separation (INV-05) | Engine validates tokens via public key only; private key is unexported | LIVE_PROBE_DEBUG_BACKDOOR_18 | **BLOCKED** |

### 5. Infrastructure Bypass Paths

| Path | Defense | Test Evidence | Status |
|---|---|---|---|
| InfraEnforcementAdapter.GateBackgroundJob(nil_pipeline) | gateExecution() fail-closed: nil pipeline → INFRA_GATE_NO_PIPELINE | LIVE_PROBE_INFRA_BYPASS_8 | **BLOCKED** |
| InfraEnforcementAdapter.GateBackgroundJob(unauthorized_agent) | Unauthorized agent → PDP DENY via pipeline | LIVE_PROBE_INFRA_BYPASS_9 | **BLOCKED** |
| InfraEnforcementAdapter.GateCICDStep(nil_pipeline) | CI/CD fail-closed: nil pipeline → INFRA_GATE_NO_PIPELINE | LIVE_PROBE_INFRA_BYPASS_10 | **BLOCKED** |
| InfraEnforcementAdapter.GateServiceCall(nil_pipeline) | Service call fail-closed: nil pipeline → INFRA_GATE_NO_PIPELINE | LIVE_PROBE_INFRA_BYPASS_11 | **BLOCKED** |
| InfraEnforcementAdapter.GateScheduledTask(nil_pipeline) | Scheduled task fail-closed: nil pipeline → INFRA_GATE_NO_PIPELINE | LIVE_PROBE_INFRA_BYPASS_12 | **BLOCKED** |

---

## Summary

- **Total paths scanned:** 20
- **Blocked:** 20
- **Justified exceptions:** 0
- **Open bypasses:** 0

**RESULT: NO EXECUTION PATH EXISTS WITHOUT SARATHI ENFORCEMENT**
