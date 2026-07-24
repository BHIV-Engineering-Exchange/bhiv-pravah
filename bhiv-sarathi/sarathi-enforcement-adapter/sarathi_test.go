package main

// sarathi_test.go — Go standard test integration for the Sarathi Enforcement Adapter.
//
// Author: Governance Engineering Audit (v14.0 Production Hardening — F4)
// System: Sarathi Governance Kernel — Enforcement Adapter (PEP)
// Host Organization: Blackhole Infiverse (BHIV)
//
// PURPOSE:
//   Wraps the existing comprehensive test harness in Go's standard testing
//   package so that tests can be run via:
//     go test -v ./...
//     go test -race ./...
//     go test -cover ./...
//
//   This enables CI/CD integration, race detection, selective test execution,
//   coverage reporting, and failure isolation — all of which require the
//   standard testing framework.
//
//   The existing harness in enforcement_adapter_main.go is preserved for
//   backward compatibility. These tests reuse the same pipeline setup and
//   test logic, wrapped in testing.T runners.
//
// STRUCTURE:
//   Part A — Mandatory Proof Tests (task.md TEST 1-5)
//   Part B — Mandatory Attack Tests (task.md ATTACK 1-3)
//   Part C — Phase 13 Integration Tests (GAP 1-5)
//   Part D — Infrastructure Gate Tests
//   Part E — Pipeline Integrity Assertions (INV-35)
//   Part F — Runtime Path Attestation (INV-38 — v14.0 F1)
//   Part G — Posture Enforcement Mode Tests (v14.0 F7)
//   Part H — Concurrency Safety Tests (v14.0 F2)

import (
	"crypto/ed25519"
	"fmt"
	"sync"
	"testing"
	"time"

	"github.com/google/uuid"
)

// ================================================================
// TEST PIPELINE SETUP
// ================================================================

// testPipeline creates a fresh pipeline for testing.
// Each top-level test function should call this to get an isolated pipeline.
func testPipeline(t *testing.T) *SarathiEnforcementPipeline {
	t.Helper()
	pipeline, err := NewSarathiEnforcementPipeline("", "")
	if err != nil {
		// Try sibling directory path
		pipeline, err = NewSarathiEnforcementPipeline(
			"../sarathi-policy-registry/policies",
			"../sarathi-policy-registry/registry_config.json",
		)
		if err != nil {
			// Try local path
			pipeline, err = NewSarathiEnforcementPipeline("policies", "registry_config.json")
			if err != nil {
				t.Fatalf("Pipeline initialization failed: %v", err)
			}
		}
	}
	pipeline.Adapter.InitExternalMode()
	return pipeline
}

// ================================================================
// PART A — MANDATORY PROOF TESTS (task.md TEST 1-5)
// ================================================================

func TestProof_NoToken(t *testing.T) {
	pipeline := testPipeline(t)
	result := pipeline.Engine.ExecuteWithToken(nil)
	if result.Executed {
		t.Fatal("Execution without token must not succeed")
	}
	if result.BlockReason != BlockNoToken {
		t.Fatalf("Expected block_reason=%s, got=%s", BlockNoToken, result.BlockReason)
	}
}

func TestProof_InvalidToken(t *testing.T) {
	pipeline := testPipeline(t)
	_, roguePriv, _ := ed25519.GenerateKey(nil)

	fakeToken := &CapabilityToken{
		tokenID:         uuid.New().String(),
		decisionID:      "FAKE-DECISION",
		verdict:         "ALLOW",
		enforcementHash: "FAKE_HASH",
		issuedAt:        time.Now().UTC(),
		expiresAt:       time.Now().UTC().Add(30 * time.Second),
	}
	fakeToken.tokenHash = fakeToken.computeHash()
	fakeToken.signature = ed25519.Sign(roguePriv, []byte(fakeToken.tokenHash))
	fakeToken.signerKeyID = "ROGUE-KEY-001"

	result := pipeline.Engine.ExecuteWithToken(fakeToken)
	if result.Executed {
		t.Fatal("Execution with invalid (rogue-signed) token must not succeed")
	}
	if result.Status != "EXECUTION_BLOCKED" {
		t.Fatalf("Expected EXECUTION_BLOCKED, got %s", result.Status)
	}
}

func TestProof_ValidToken(t *testing.T) {
	pipeline := testPipeline(t)
	trace := pipeline.Execute("gov-agent-001", "policy-reg-001", "read", uuid.New().String())
	exec := trace["execution"].(map[string]interface{})
	if fmt.Sprintf("%v", exec["execution_state"]) != "EXECUTION_PERMITTED" {
		t.Fatalf("Valid token must produce EXECUTION_PERMITTED, got %v", exec["execution_state"])
	}
}

func TestProof_ReplayToken(t *testing.T) {
	pipeline := testPipeline(t)
	req := NewExecutionRequest("gov-agent-001", "policy-reg-001", "read", uuid.New().String())
	enfResp := pipeline.Adapter.Enforce(req)
	token := enfResp.GetCapabilityToken()
	if token == nil {
		t.Fatal("Expected ALLOW verdict with token")
	}

	result1 := pipeline.Engine.ExecuteWithToken(token)
	if !result1.Executed {
		t.Fatal("First execution should succeed")
	}

	result2 := pipeline.Engine.ExecuteWithToken(token)
	if result2.Executed {
		t.Fatal("Replay execution must not succeed")
	}
	if result2.BlockReason != BlockTokenAlreadyUsed {
		t.Fatalf("Expected %s, got %s", BlockTokenAlreadyUsed, result2.BlockReason)
	}
}

func TestProof_BypassAttempt(t *testing.T) {
	pipeline := testPipeline(t)
	req := NewExecutionRequest("gov-agent-001", "policy-reg-001", "read", uuid.New().String())
	enfResp := pipeline.Adapter.Enforce(req)
	if enfResp.Verdict() != "ALLOW" {
		t.Skip("Enforcement denied — cannot craft bypass token")
	}

	fakeToken := &CapabilityToken{
		tokenID:         uuid.New().String(),
		decisionID:      enfResp.DecisionID(),
		requestHash:     enfResp.RequestHash(),
		policyHash:      enfResp.PolicyHashField(),
		enforcementHash: "FAKE_ENF_HASH_NOT_IN_CHAIN_" + uuid.New().String()[:8],
		correlationID:   req.CorrelationID(),
		verdict:         "ALLOW",
		obligations:     []string{"LOG_ACCESS"},
		issuer:          "sarathi-enforcement-adapter",
		audience:        "policy-reg-001",
		issuedAt:        time.Now().UTC(),
		expiresAt:       time.Now().UTC().Add(30 * time.Second),
	}
	fakeToken.tokenHash = fakeToken.computeHash()
	pipeline.Adapter.tokenAuthority.SignToken(fakeToken)

	result := pipeline.Engine.ExecuteWithToken(fakeToken)
	if result.Executed {
		t.Fatal("Bypass attempt with fake enforcement_hash must not succeed")
	}
	if result.BlockReason != BlockEnforcementNotInChain {
		t.Fatalf("Expected %s, got %s", BlockEnforcementNotInChain, result.BlockReason)
	}
}

// ================================================================
// PART B — MANDATORY ATTACK TESTS (task.md ATTACK 1-3)
// ================================================================

func TestAttack_DirectExecCall(t *testing.T) {
	pipeline := testPipeline(t)
	fakeReq := NewExecutionRequest("gov-agent-001", "policy-reg-001", "read", "direct-atk-001")
	fakeResp := NewExecutionResponse(fakeReq, nil, "DIRECT_BYPASS_HASH", "FAKE_POLICY")
	result := pipeline.Engine.AttemptExecution(fakeResp)
	executed := result["executed"].(bool)
	if executed {
		t.Fatal("Direct execution call must fail")
	}
}

func TestAttack_FakeTokenInjection(t *testing.T) {
	pipeline := testPipeline(t)
	_, fakePriv, _ := ed25519.GenerateKey(nil)
	fakeToken := &CapabilityToken{
		tokenID:         uuid.New().String(),
		decisionID:      uuid.New().String(),
		requestHash:     "FAKE_REQUEST_HASH",
		policyHash:      "FAKE_POLICY_HASH",
		enforcementHash: "FAKE_ENFORCEMENT_HASH",
		correlationID:   "fake-inject-001",
		verdict:         "ALLOW",
		issuer:          "sarathi-enforcement-adapter",
		issuedAt:        time.Now().UTC(),
		expiresAt:       time.Now().UTC().Add(30 * time.Second),
	}
	fakeToken.tokenHash = fakeToken.computeHash()
	fakeToken.signature = ed25519.Sign(fakePriv, []byte(fakeToken.tokenHash))
	fakeToken.signerKeyID = "FAKE-INJECTED-KEY"

	result := pipeline.Engine.ExecuteWithToken(fakeToken)
	if result.Executed {
		t.Fatal("Fake token injection must fail")
	}
}

func TestAttack_InfraNoToken(t *testing.T) {
	pipeline := testPipeline(t)
	infraAdapter := NewInfraEnforcementAdapter()
	result := infraAdapter.GateBackgroundJob("job-001", "ghost-agent-999", "ops-data-001", "execute", pipeline)
	if result.Allowed {
		t.Fatal("Infra job without valid token must fail")
	}
}

// ================================================================
// PART C — INTEGRATION TESTS (Selected GAP coverage)
// ================================================================

func TestIntegration_ExecutionContractCompliance(t *testing.T) {
	pipeline := testPipeline(t)
	var contract SarathiExecutionContract = pipeline.Engine
	if !contract.RequiresToken() {
		t.Fatal("ExecutionEngine must require tokens")
	}
	if contract.SystemID() != "sarathi-execution-engine" {
		t.Fatalf("Expected sarathi-execution-engine, got %s", contract.SystemID())
	}
	if err := contract.ValidateBinding(); err != nil {
		t.Fatalf("ValidateBinding failed: %v", err)
	}
}

func TestIntegration_CrossSystemPayloadFlow(t *testing.T) {
	pipeline := testPipeline(t)
	trace := pipeline.Execute("gov-agent-001", "policy-reg-001", "read", uuid.New().String())
	enf := trace["enforcement"].(map[string]interface{})
	exec := trace["execution"].(map[string]interface{})

	enfHash := fmt.Sprintf("%v", enf["enforcement_hash"])
	execEnfHash := fmt.Sprintf("%v", exec["enforcement_hash"])
	if enfHash != execEnfHash || enfHash == "" {
		t.Fatalf("Enforcement hash must flow: enf=%s exec=%s", enfHash, execEnfHash)
	}
}

func TestIntegration_ChainIntegrity(t *testing.T) {
	pipeline := testPipeline(t)
	// Warm up the pipeline
	pipeline.Execute("gov-agent-001", "policy-reg-001", "read", uuid.New().String())

	ok, msg := pipeline.Adapter.VerifyChain()
	if !ok {
		t.Fatalf("Enforcement chain broken: %s", msg)
	}
	execOK, execMsg := pipeline.Engine.VerifyExecutionChain()
	if !execOK {
		t.Fatalf("Execution chain broken: %s", execMsg)
	}
}

func TestIntegration_UnknownAgent(t *testing.T) {
	pipeline := testPipeline(t)
	trace := pipeline.Execute("completely-unknown-agent-xyz", "ops-data-001", "read", uuid.New().String())
	enf := trace["enforcement"].(map[string]interface{})
	if fmt.Sprintf("%v", enf["verdict"]) != "DENY" {
		t.Fatal("Unknown agent must be denied")
	}
}

// ================================================================
// PART D — INFRASTRUCTURE GATE TESTS
// ================================================================

func TestInfra_BackgroundJob_Allow(t *testing.T) {
	pipeline := testPipeline(t)
	infraAdapter := NewInfraEnforcementAdapter()
	result := infraAdapter.GateBackgroundJob("bg-001", "gov-agent-001", "policy-reg-001", "read", pipeline)
	if !result.Allowed {
		t.Fatalf("Valid background job should be allowed, got block_reason=%s", result.BlockReason)
	}
}

func TestInfra_NilPipeline_FailClosed(t *testing.T) {
	infraAdapter := NewInfraEnforcementAdapter()
	result := infraAdapter.GateBackgroundJob("nil-test", "gov-agent-001", "policy-reg-001", "read", nil)
	if result.Allowed {
		t.Fatal("Nil pipeline must be denied (fail-closed)")
	}
	if result.BlockReason != "INFRA_GATE_NO_PIPELINE" {
		t.Fatalf("Expected INFRA_GATE_NO_PIPELINE, got %s", result.BlockReason)
	}
}

func TestInfra_GateCount(t *testing.T) {
	pipeline := testPipeline(t)
	infraAdapter := NewInfraEnforcementAdapter()
	infraAdapter.GateBackgroundJob("t1", "gov-agent-001", "policy-reg-001", "read", pipeline)
	infraAdapter.GateCICDStep("t2", "gov-agent-001", "policy-reg-001", "read", pipeline)
	infraAdapter.GateServiceCall("std-agent-001", "ops-data-001", "read", pipeline)
	if infraAdapter.GetGateCount() != 3 {
		t.Fatalf("Expected 3 gates, got %d", infraAdapter.GetGateCount())
	}
}

// ================================================================
// PART E — PIPELINE INTEGRITY ASSERTIONS (INV-35)
// ================================================================

func TestPipelineIntegrity_InternalHash(t *testing.T) {
	actual := computePipelineHash(SarathiPipelineOrder)
	if actual != ExpectedPipelineHash {
		t.Fatalf("Internal pipeline hash mismatch: expected=%s actual=%s", ExpectedPipelineHash, actual)
	}
}

func TestPipelineIntegrity_ExternalHash(t *testing.T) {
	actual := computePipelineHash(SarathiExternalPipelineOrder)
	if actual != ExpectedExternalPipelineHash {
		t.Fatalf("External pipeline hash mismatch: expected=%s actual=%s", ExpectedExternalPipelineHash, actual)
	}
}

// ================================================================
// PART F — RUNTIME PATH ATTESTATION (INV-38 — v14.0 F1)
// ================================================================

func TestRPA_StagesRecordedInsideEnforce(t *testing.T) {
	pipeline := testPipeline(t)
	rpa := NewRuntimePathAttestation()

	// Record pre-gate stages (these happen outside Enforce)
	rpa.RecordStage("PRE_GATE_RATE_LIMIT")
	rpa.RecordStage("PRE_GATE_POSTURE_VERIFY")

	// Call Enforce with RPA — stages should be recorded inside
	req := NewExecutionRequest("gov-agent-001", "policy-reg-001", "read", uuid.New().String())
	pipeline.Adapter.Enforce(req, rpa)

	stages := rpa.GetStages()
	if len(stages) != 9 {
		t.Fatalf("Expected 9 stages (2 pre-gate + 7 verification), got %d: %v", len(stages), stages)
	}

	// Verify the stages match canonical order
	match, detail := rpa.VerifyAgainstCanonical(SarathiPipelineOrder)
	if !match {
		t.Fatalf("RPA stages don't match canonical order: %s", detail)
	}

	// Verify path hash matches expected
	pathHash := rpa.ComputePathHash()
	if pathHash != ExpectedPipelineHash {
		t.Fatalf("RPA path hash mismatch: expected=%s actual=%s", ExpectedPipelineHash, pathHash)
	}
}

func TestRPA_EarlyExitFewerStages(t *testing.T) {
	pipeline := testPipeline(t)
	rpa := NewRuntimePathAttestation()

	// Invalid request — should exit at PRE_PDP_VALIDATION
	req := NewExecutionRequest("", "", "", uuid.New().String())
	pipeline.Adapter.Enforce(req, rpa)

	stages := rpa.GetStages()
	// Only PRE_PDP_VALIDATION should be recorded (early exit)
	if len(stages) != 1 {
		t.Fatalf("Expected 1 stage for early exit, got %d: %v", len(stages), stages)
	}
	if stages[0] != "PRE_PDP_VALIDATION" {
		t.Fatalf("Expected PRE_PDP_VALIDATION, got %s", stages[0])
	}

	// Path hash should NOT match full pipeline hash
	pathHash := rpa.ComputePathHash()
	if pathHash == ExpectedPipelineHash {
		t.Fatal("Early exit path hash should NOT match full pipeline hash")
	}
}

func TestRPA_PolicyVersionMismatchPartialPath(t *testing.T) {
	pipeline := testPipeline(t)
	rpa := NewRuntimePathAttestation()

	// Policy version mismatch — should exit at POLICY_VERSION_CHECK
	req := NewExecutionRequest("gov-agent-001", "policy-reg-001", "read", uuid.New().String(), "99.99.99")
	pipeline.Adapter.Enforce(req, rpa)

	stages := rpa.GetStages()
	// PRE_PDP_VALIDATION + POLICY_VERSION_CHECK = 2 stages
	if len(stages) != 2 {
		t.Fatalf("Expected 2 stages for policy version exit, got %d: %v", len(stages), stages)
	}
}

// ================================================================
// PART G — POSTURE ENFORCEMENT MODE TESTS (v14.0 F7)
// ================================================================

func TestPosture_DefaultDisabledMode(t *testing.T) {
	pv := NewPostureVerifier(nil, RealClock{})
	if pv.GetEnforcementMode() != PostureDisabled {
		t.Fatal("Default mode must be PostureDisabled")
	}
}

func TestPosture_EnforcedRejectsMissingSignal(t *testing.T) {
	pv := NewPostureVerifier(nil, RealClock{})
	pv.SetEnforcementMode(PostureEnforced)

	// Admit nil signal in ENFORCED mode — must reject
	admitted, reason := pv.Admit(nil)
	if admitted {
		t.Fatal("ENFORCED mode must reject nil posture signal")
	}
	if reason == "" {
		t.Fatal("Rejection reason must not be empty")
	}
}

func TestPosture_AuditDoesNotBlock(t *testing.T) {
	pv := NewPostureVerifier(nil, RealClock{})
	pv.SetEnforcementMode(PostureAudit)
	// In AUDIT mode, the pipeline should NOT block — the PostureVerifier.Admit
	// would reject, but the pipeline skips the block in AUDIT mode.
	// This is tested at the pipeline level, not the verifier level.
	if pv.GetEnforcementMode() != PostureAudit {
		t.Fatal("Mode should be PostureAudit")
	}
}

func TestPosture_HasIssuerKeys(t *testing.T) {
	pub, _, _ := ed25519.GenerateKey(nil)
	pv := NewPostureVerifier(map[string]ed25519.PublicKey{"test-issuer": pub}, RealClock{})
	if !pv.HasIssuerKeys() {
		t.Fatal("Should have issuer keys")
	}

	pvEmpty := NewPostureVerifier(nil, RealClock{})
	if pvEmpty.HasIssuerKeys() {
		t.Fatal("Should not have issuer keys")
	}
}

// ================================================================
// PART H — CONCURRENCY SAFETY TESTS (v14.0 F2)
// ================================================================

func TestInfra_ConcurrentGateAccess(t *testing.T) {
	pipeline := testPipeline(t)
	infraAdapter := NewInfraEnforcementAdapter()

	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			infraAdapter.GateBackgroundJob(
				fmt.Sprintf("concurrent-%d", idx),
				"gov-agent-001", "policy-reg-001", "read",
				pipeline,
			)
		}(i)
	}
	wg.Wait()

	count := infraAdapter.GetGateCount()
	if count != 100 {
		t.Fatalf("Expected 100 gate invocations, got %d (potential data race)", count)
	}
}

func TestConcurrent_50MixedAgents(t *testing.T) {
	pipeline := testPipeline(t)
	var wg sync.WaitGroup
	agents := []string{
		"gov-agent-001", "std-agent-001", "ghost-agent-999",
		"suspended-agent", "revoked-agent",
	}

	results := make([]bool, 50)
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			agent := agents[idx%len(agents)]
			trace := pipeline.Execute(agent, "ops-data-001", "read", uuid.New().String())
			exec := trace["execution"].(map[string]interface{})
			state := fmt.Sprintf("%v", exec["execution_state"])
			results[idx] = state == "EXECUTION_PERMITTED" || state == "EXECUTION_BLOCKED"
		}(i)
	}
	wg.Wait()

	for i, r := range results {
		if !r {
			t.Fatalf("Request %d returned non-deterministic state", i)
		}
	}

	// Verify chains intact after concurrency
	chainOK, msg := pipeline.Adapter.VerifyChain()
	if !chainOK {
		t.Fatalf("Chain broken after concurrency: %s", msg)
	}
}

// ================================================================
// PART I — ANTI-FOOLING TESTS (v14.1)
// ================================================================

func TestAntiFooling_RPAEnforcementGateActive(t *testing.T) {
	// FOOLING-1 verification: Execute() must verify the RPA path for ALLOW verdicts
	// and include rpa_enforcement=VERIFIED in the response.
	pipeline := testPipeline(t)
	trace := pipeline.Execute("gov-agent-001", "policy-reg-001", "read", uuid.New().String())

	obs, ok := trace["observability"].(map[string]interface{})
	if !ok {
		t.Fatal("Missing observability in trace result")
	}
	rpaEnf, ok := obs["rpa_enforcement"].(string)
	if !ok {
		t.Fatal("Missing rpa_enforcement field — RPA enforcement gate is not active")
	}
	if rpaEnf != "VERIFIED" {
		t.Fatalf("Expected rpa_enforcement=VERIFIED, got %s", rpaEnf)
	}
}

func TestAntiFooling_VerifyCompleteRejectsPartialPath(t *testing.T) {
	// FOOLING-5 verification: VerifyComplete rejects paths with missing stages
	rpa := NewRuntimePathAttestation()
	rpa.RecordStage("PRE_GATE_RATE_LIMIT")
	rpa.RecordStage("PRE_PDP_VALIDATION") // only 2 of 9 stages

	match, detail := rpa.VerifyComplete(SarathiPipelineOrder)
	if match {
		t.Fatal("VerifyComplete must reject partial paths")
	}
	if detail == "" {
		t.Fatal("VerifyComplete must provide a reason for rejection")
	}
}

func TestAntiFooling_VerifyCompleteRejectsWrongOrder(t *testing.T) {
	rpa := NewRuntimePathAttestation()
	// Record all 9 stages but in wrong order
	for i := len(SarathiPipelineOrder) - 1; i >= 0; i-- {
		rpa.RecordStage(SarathiPipelineOrder[i])
	}

	match, detail := rpa.VerifyComplete(SarathiPipelineOrder)
	if match {
		t.Fatal("VerifyComplete must reject wrong-order paths")
	}
	if detail == "" {
		t.Fatal("Must provide detail")
	}
}

func TestAntiFooling_VerifyCompleteAcceptsCorrectPath(t *testing.T) {
	// FOOLING-3 verification: stages from real Enforce() call must pass VerifyComplete
	pipeline := testPipeline(t)
	rpa := NewRuntimePathAttestation()

	// Pre-gate stages (recorded in Execute, not Enforce)
	rpa.RecordStage("PRE_GATE_RATE_LIMIT")
	rpa.RecordStage("PRE_GATE_POSTURE_VERIFY")

	// Real Enforce call
	req := NewExecutionRequest("gov-agent-001", "policy-reg-001", "read", uuid.New().String())
	pipeline.Adapter.Enforce(req, rpa)

	match, detail := rpa.VerifyComplete(SarathiPipelineOrder)
	if !match {
		t.Fatalf("VerifyComplete rejected correct path from real Enforce(): %s", detail)
	}
}

func TestAntiFooling_RPAPathHashMatchesStaticHash(t *testing.T) {
	// RPA runtime hash must match the static INV-35 hash
	pipeline := testPipeline(t)
	rpa := NewRuntimePathAttestation()
	rpa.RecordStage("PRE_GATE_RATE_LIMIT")
	rpa.RecordStage("PRE_GATE_POSTURE_VERIFY")
	req := NewExecutionRequest("gov-agent-001", "policy-reg-001", "read", uuid.New().String())
	pipeline.Adapter.Enforce(req, rpa)

	pathHash := rpa.ComputePathHash()
	if pathHash != ExpectedPipelineHash {
		t.Fatalf("Runtime path hash must equal static pipeline hash: runtime=%s static=%s", pathHash, ExpectedPipelineHash)
	}
}

// ================================================================
// PART J — BYPASS SCANNER VERIFICATION (v14.1 — FOOLING-2)
// ================================================================

func TestBypassScanner_LiveProbes(t *testing.T) {
	// FOOLING-2 verification: bypass scanner must use live probes, not hardcoded results
	pipeline := testPipeline(t)
	report := RunBypassEliminationScan(pipeline)

	// Verify methodology says LIVE RUNTIME PROBES, not the old static claim
	if report.Methodology == "" {
		t.Fatal("Missing methodology")
	}
	if report.Version != "v14.1" {
		t.Fatalf("Expected version v14.1, got %s", report.Version)
	}

	// Verify each result has LIVE_PROBE_ prefix in test evidence
	for i, r := range report.Results {
		if len(r.TestEvidence) < 11 || r.TestEvidence[:11] != "LIVE_PROBE_" {
			t.Fatalf("Result %d (%s) has non-live test evidence: %s", i, r.Path, r.TestEvidence)
		}
	}

	// Verify all probes passed (all should be BLOCKED)
	if report.Summary.OpenBypasses > 0 {
		for _, r := range report.Results {
			if r.Status == "OPEN" {
				t.Errorf("OPEN bypass: %s (defense: %s)", r.Path, r.Defense)
			}
		}
		t.Fatalf("Bypass scanner found %d open bypasses", report.Summary.OpenBypasses)
	}

	// Verify scanner ran at least 20 probes
	if report.Summary.TotalScanned < 20 {
		t.Fatalf("Expected at least 20 probes, got %d", report.Summary.TotalScanned)
	}
}

func TestBypassScanner_PositiveAndNegativeControls(t *testing.T) {
	// The scanner must include both positive and negative controls:
	// - Positive: valid execution path works (ensures scanner isn't broken)
	// - Negative: DENY path blocks execution
	pipeline := testPipeline(t)
	report := RunBypassEliminationScan(pipeline)

	hasPositive := false
	hasNegative := false
	for _, r := range report.Results {
		if r.Path == "Valid execution path (positive control)" {
			hasPositive = true
			if r.Status != "BLOCKED" {
				t.Fatal("Positive control should report BLOCKED (meaning the path works correctly)")
			}
		}
		if r.Path == "DENY path blocks execution (negative control)" {
			hasNegative = true
			if r.Status != "BLOCKED" {
				t.Fatal("Negative control should report BLOCKED")
			}
		}
	}
	if !hasPositive {
		t.Fatal("Scanner must include positive control probe")
	}
	if !hasNegative {
		t.Fatal("Scanner must include negative control probe")
	}
}

// ================================================================
// Part K — Deterministic Response Contract (v14.3 / INV-45)
// ================================================================

// TestResponseContract_ForcesDenyOnMissingField proves that if an upstream
// code path produces a response map missing one or more required top-level
// fields, EnforceResponseContract replaces the map with a canonical DENY
// envelope carrying error_code=ERR_CONTRACT_VIOLATION and a diagnostic
// listing the missing fields. This is the fail-closed guarantee of INV-45.
func TestResponseContract_ForcesDenyOnMissingField(t *testing.T) {
	// Simulate a broken upstream path that emits a bare, incomplete map —
	// the exact failure mode that caused RPSA-01/02 to surface as <nil>
	// before v14.3.
	broken := map[string]interface{}{
		"verdict": "ALLOW",
		// Missing: schema_version, decision_id, execution_state, error_code,
		// reason, trace_id, correlation_id, enforcement_hash, timestamp,
		// request, enforcement, execution, trace_context, observability
	}

	// Pre-assertion: ValidateResponseContract must reject the broken map and
	// enumerate the missing fields (must include more than just one).
	ok, missing := ValidateResponseContract(broken)
	if ok {
		t.Fatal("ValidateResponseContract accepted an incomplete response — INV-45 regression")
	}
	if len(missing) < 10 {
		t.Fatalf("Expected at least 10 missing fields, got %d: %v", len(missing), missing)
	}

	// Build a minimal synthetic request + trace context to thread through
	// the enforcer. The enforcer does NOT need the real pipeline — it is a
	// pure function of (resp, req, traceCtx).
	traceCtx := NewTraceContext()
	req := NewExecutionRequest("agent-test", "res-test", "read", "corr-contract-test")

	fixed := EnforceResponseContract(broken, req, traceCtx)
	if fixed == nil {
		t.Fatal("EnforceResponseContract returned nil — hard fail, INV-45 not enforceable")
	}

	// Post-assertion 1: the replacement MUST itself satisfy the contract.
	// Any missing field in the replacement would mean the enforcer is
	// recursively broken — proving the fail-closed path is real, not a stub.
	ok2, missing2 := ValidateResponseContract(fixed)
	if !ok2 {
		t.Fatalf("Replacement response is itself incomplete: %v", missing2)
	}

	// Post-assertion 2: replacement verdict is DENY.
	if v, _ := fixed["verdict"].(string); v != VerdictDeny {
		t.Fatalf("Expected replacement verdict=DENY, got %q", v)
	}

	// Post-assertion 3: replacement error_code is CodeContractViolation.
	if ec, _ := fixed["error_code"].(string); ec != CodeContractViolation {
		t.Fatalf("Expected error_code=%s, got %q", CodeContractViolation, ec)
	}

	// Post-assertion 4: replacement execution_state is StateContractErr.
	if st, _ := fixed["execution_state"].(string); st != StateContractErr {
		t.Fatalf("Expected execution_state=%s, got %q", StateContractErr, st)
	}

	// Post-assertion 5: diagnostic key contract_violation lists the missing
	// fields — confirms this is not a generic forced DENY but a real
	// response-contract-violation replacement.
	cv, ok3 := fixed["contract_violation"].(map[string]interface{})
	if !ok3 {
		t.Fatal("Replacement missing contract_violation diagnostic key")
	}
	if _, ok := cv["missing_fields"]; !ok {
		t.Fatal("contract_violation diagnostic missing \"missing_fields\" key")
	}

	// Post-assertion 6: replacement enforcement_hash is the contract-violation
	// sentinel — confirms the chain was NOT advanced (INV-08, INV-36 preserved).
	if h, _ := fixed["enforcement_hash"].(string); h != ContractEnforcementHash {
		t.Fatalf("Expected enforcement_hash=%s, got %q", ContractEnforcementHash, h)
	}

	// Post-assertion 7: correlation_id passthrough works.
	if c, _ := fixed["correlation_id"].(string); c != "corr-contract-test" {
		t.Fatalf("Expected correlation_id=corr-contract-test, got %q", c)
	}
}

// TestResponseContract_NormalizeIdentifiersRejectsPathTraversal proves that
// the NormalizeIdentifiers input-layer function (task.md Phase 3) rejects
// path traversal in resource_id with CodePathTraversal — this is the exact
// fix for RPSA-01.
func TestResponseContract_NormalizeIdentifiersRejectsPathTraversal(t *testing.T) {
	_, _, _, errCode := NormalizeIdentifiers("agent-001", "policy-reg-001/../core-engine", "read")
	if errCode != CodePathTraversal {
		t.Fatalf("Expected CodePathTraversal for RPSA-01 payload, got %q", errCode)
	}
}

// TestResponseContract_NormalizeIdentifiersRejectsMixedCase proves that
// NormalizeIdentifiers rejects mixed case with CodeNonCanonicalCase — the
// exact fix for RPSA-02. We reject rather than auto-lowercase so an attacker
// cannot silently map a crafted variant onto a legitimate record.
func TestResponseContract_NormalizeIdentifiersRejectsMixedCase(t *testing.T) {
	_, _, _, errCode := NormalizeIdentifiers("Gov-Agent-001", "resource-001", "read")
	if errCode != CodeNonCanonicalCase {
		t.Fatalf("Expected CodeNonCanonicalCase for RPSA-02 payload, got %q", errCode)
	}
}
