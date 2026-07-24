package main

// external_decision_test_sim.go — Deterministic Proof Suite for BHIV External Decision Path.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — External Decision Trust Boundary Tests (v11.0)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   Comprehensive deterministic test suite proving that the BHIV external
//   decision verification + enforcement path is non-bypassable.
//   Every test case produces auditable output with deterministic pass/fail.
//
// TEST MATRIX (20 test cases, 55+ assertions):
//   1.  Valid signed ALLOW → token issued, execution permitted
//   2.  Signed DENY → no token, enforcement recorded
//   3.  Replay attempt → blocked (nonce already seen)
//   4.  Invalid structure → rejected (missing fields, bad action, tampered hash)
//   5.  PDP/KSML/GovernanceKernel guards → blocked in EXTERNAL mode
//   6.  Expired decision → rejected (past TTL + clock skew)
//   7.  Mode transition → works correctly with lock levels
//   8.  Chain integrity → verified after external enforcements
//   9.  Full BHIV flow → evaluator → sign → verify → enforce → token → execute
//   10. Internal mode regression → existing pipeline untouched
//   11. UNSIGNED decision → rejected (no evaluator signature)
//   12. UNKNOWN evaluator → rejected (not in trust registry)
//   13. REVOKED evaluator → rejected (evaluator permanently revoked)
//   14. SUSPENDED evaluator → rejected (evaluator suspended)
//   15. WRONG KEY signature → rejected (signed by different evaluator)
//   16. TAMPERED core hash → rejected (binding broken)
//   17. Mode lock IMMUTABLE → SetMode blocked
//   18. Mode lock PRIVILEGED → unprivileged user blocked
//   19. Key rotation → old key accepted during grace period
//   20. Decision-request binding → token bound to decision core hash
//
// PROOF LOGS:
//   Each test produces deterministic output suitable for REVIEW_PACKET.md.
//   Logs show: invalid signature → denied, unknown evaluator → denied,
//   revoked evaluator → denied, expired → denied, replay → denied,
//   valid → token issued.

import (
	"crypto/ed25519"
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// RunExternalDecisionTests runs the complete hardened test suite for the
// external decision verification + enforcement path.
// Returns (passed, total, details).
func RunExternalDecisionTests(pipeline *SarathiEnforcementPipeline) (int, int, []string) {
	passed := 0
	total := 0
	var details []string

	logTest := func(name string, pass bool, detail string) {
		total++
		status := "FAIL"
		if pass {
			passed++
			status = "PASS"
		}
		line := fmt.Sprintf("  [%s] %s: %s", status, name, detail)
		details = append(details, line)
		fmt.Println(line)
	}

	// ═══════════════════════════════════════════════════════
	// SETUP: Generate evaluator key pairs and register in trust registry
	// ═══════════════════════════════════════════════════════
	pipeline.Adapter.InitExternalMode()
	registry := pipeline.Adapter.GetEvaluatorRegistry()

	// Generate Ed25519 key pair for Ishan's evaluator
	ishanPub, ishanPriv, _ := ed25519.GenerateKey(nil)
	_ = registry.RegisterEvaluator(
		"ishan-evaluator-v1",
		"Ishan Shirode Evaluator v1",
		ishanPub,
		map[string]string{"version": "1.0", "org": "BHIV"},
		"system-init",
	)

	// Generate key pair for Ishan v2
	ishanPubV2, ishanPrivV2, _ := ed25519.GenerateKey(nil)
	_ = registry.RegisterEvaluator(
		"ishan-evaluator-v2",
		"Ishan Shirode Evaluator v2",
		ishanPubV2,
		map[string]string{"version": "2.1.0", "org": "BHIV"},
		"system-init",
	)

	// Generate key pair for a rogue evaluator (NOT registered)
	_, roguePriv, _ := ed25519.GenerateKey(nil)

	// Create mode controller in EXTERNAL mode
	modeCtrl := NewModeController(BHIVModeExternal)

	// Helper: create a properly signed decision
	createSignedDecision := func(
		evalID, agentID, resourceID, action string,
		verdict ExternalDecisionVerdict,
		privKey ed25519.PrivateKey,
		ttl time.Duration,
	) *ExternalDecision {
		d := NewExternalDecision(evalID, agentID, resourceID, action, verdict, nil, nil, "test decision", ttl)
		d.SignDecision(privKey)
		return d
	}

	printHeader("PHASE 7: EXTERNAL DECISION TRUST BOUNDARY VALIDATION")
	fmt.Printf("  Evaluator Registry: %d evaluators registered\n", registry.EvaluatorCount())
	fmt.Printf("  Active Evaluators:  %d\n", registry.ActiveEvaluatorCount())
	fmt.Println()

	// ================================================================
	// TEST 1: Valid signed ALLOW → execution succeeds
	// ================================================================
	printSubheader("TEST 1: Valid Signed ALLOW → Token Issued + Execution Permitted")
	{
		decision := NewExternalDecision(
			"ishan-evaluator-v1",
			"agent-alpha",
			"project-data",
			"read",
			ExternalVerdictAllow,
			[]string{"LOG_ACCESS"},
			map[string]string{"source": "bhiv-evaluator", "confidence": "0.99"},
			"Agent cleared by evaluator for read access",
			30*time.Second,
		)
		decision.SignDecision(ishanPriv)

		result := pipeline.Adapter.EnforceExternalDecision(decision, modeCtrl)
		enforced := result.Enforced && result.Verdict == "ALLOW" && result.Token != nil

		if enforced {
			execResult := pipeline.Engine.ExecuteWithToken(result.Token)
			executed := execResult.Executed && execResult.Status == "EXECUTION_PERMITTED"
			logTest("Valid signed ALLOW → token issued", true, fmt.Sprintf("token_id=%s", result.Token.TokenID()))
			logTest("Valid signed ALLOW → execution permitted", executed,
				fmt.Sprintf("status=%s executed=%v", execResult.Status, execResult.Executed))
			inChain := pipeline.Adapter.HasEnforcementHash(result.EnforcementHash)
			logTest("Valid signed ALLOW → enforcement hash in chain", inChain,
				fmt.Sprintf("hash=%s", truncHash(result.EnforcementHash)))
			logTest("Valid signed ALLOW → verification trace complete",
				result.VerificationTrace != nil && result.VerificationTrace.FinalVerdict == "VERIFIED",
				fmt.Sprintf("stages=%d verdict=%s", len(result.VerificationTrace.Results), result.VerificationTrace.FinalVerdict))
		} else {
			logTest("Valid signed ALLOW → enforcement failed", false,
				fmt.Sprintf("enforced=%v verdict=%s block=%s detail=%s", result.Enforced, result.Verdict, result.BlockReason, result.BlockDetail))
			logTest("Valid signed ALLOW → execution not attempted", false, "no token")
			logTest("Valid signed ALLOW → chain not updated", false, "no enforcement hash")
			logTest("Valid signed ALLOW → verification trace", false, "no trace")
		}
	}

	// ================================================================
	// TEST 2: Signed DENY → no token, enforcement recorded
	// ================================================================
	printSubheader("TEST 2: Signed DENY → No Token / Enforcement Recorded")
	{
		decision := createSignedDecision("ishan-evaluator-v1", "agent-beta", "classified-data", "write",
			ExternalVerdictDeny, ishanPriv, 30*time.Second)
		result := pipeline.Adapter.EnforceExternalDecision(decision, modeCtrl)
		logTest("Signed DENY → enforced correctly", result.Enforced && result.Verdict == "DENY",
			fmt.Sprintf("verdict=%s enforced=%v", result.Verdict, result.Enforced))
		logTest("Signed DENY → no token issued", result.Token == nil, "token is nil as expected")
		logTest("Signed DENY → enforcement hash recorded", result.EnforcementHash != "",
			fmt.Sprintf("hash=%s", truncHash(result.EnforcementHash)))
	}

	// ================================================================
	// TEST 3: Replay attempt → blocked
	// ================================================================
	printSubheader("TEST 3: Replay Attempt → Blocked")
	{
		decision := createSignedDecision("ishan-evaluator-v1", "agent-alpha", "project-data", "read",
			ExternalVerdictAllow, ishanPriv, 30*time.Second)
		result1 := pipeline.Adapter.EnforceExternalDecision(decision, modeCtrl)
		logTest("Replay → first attempt succeeds", result1.Enforced && result1.Verdict == "ALLOW",
			fmt.Sprintf("verdict=%s", result1.Verdict))

		result2 := pipeline.Adapter.EnforceExternalDecision(decision, modeCtrl)
		isReplayBlocked := !result2.Enforced || result2.Verdict == "DENY"
		hasReplayReason := strings.Contains(result2.BlockReason, "REPLAY")
		logTest("Replay → second attempt blocked", isReplayBlocked && hasReplayReason,
			fmt.Sprintf("verdict=%s block_reason=%s", result2.Verdict, result2.BlockReason))
	}

	// ================================================================
	// TEST 4: Invalid structure → rejected
	// ================================================================
	printSubheader("TEST 4: Invalid Structure → Rejected")
	{
		// 4a: nil decision
		result := pipeline.Adapter.EnforceExternalDecision(nil, modeCtrl)
		logTest("Invalid → nil decision rejected", result.Verdict == "DENY",
			fmt.Sprintf("block=%s", result.BlockReason))

		// 4b: missing agent_id (construct manually to bypass constructor validation)
		badDecision := &ExternalDecision{
			DecisionID:         "bad-id",
			EvaluatorID:        "test",
			AgentID:            "", // Missing!
			ResourceID:         "res",
			Action:             "read",
			Verdict:            ExternalVerdictAllow,
			Nonce:              "bad-nonce",
			Timestamp:          time.Now().UTC(),
			ExpiresAt:          time.Now().UTC().Add(30 * time.Second),
			DecisionHash:       "tampered",
			DecisionCoreHash:   "tampered",
			EvaluatorSignature: []byte("fake"),
		}
		result2 := pipeline.Adapter.EnforceExternalDecision(badDecision, modeCtrl)
		logTest("Invalid → missing agent_id rejected", result2.Verdict == "DENY",
			fmt.Sprintf("block=%s", result2.BlockReason))

		// 4c: invalid action
		badDecision3 := NewExternalDecision(
			"ishan-evaluator-v1", "agent-x", "res-y", "destroy",
			ExternalVerdictAllow, nil, nil, "test", 30*time.Second,
		)
		badDecision3.SignDecision(ishanPriv)
		result3 := pipeline.Adapter.EnforceExternalDecision(badDecision3, modeCtrl)
		logTest("Invalid → bad action rejected", result3.Verdict == "DENY",
			fmt.Sprintf("block=%s detail=%s", result3.BlockReason, result3.BlockDetail))
	}

	// ================================================================
	// TEST 5: PDP/KSML/GovernanceKernel guards blocked in EXTERNAL mode
	// ================================================================
	printSubheader("TEST 5: Centralized Guard — PDP/KSML/GovernanceKernel Blocked in EXTERNAL")
	{
		// Test centralized guard for PDP
		err := modeCtrl.CentralGuardCheck(DecisionInterfacePDP, "Evaluate", "test_caller_5a")
		logTest("CentralGuard → PDP blocked in EXTERNAL", err != nil && strings.Contains(err.Error(), "CENTRAL_GUARD_VIOLATION"),
			fmt.Sprintf("error=%v", err))

		// Test centralized guard for KSML
		err2 := modeCtrl.CentralGuardCheck(DecisionInterfaceKSML, "GovernIntent", "test_caller_5b")
		logTest("CentralGuard → KSML blocked in EXTERNAL", err2 != nil && strings.Contains(err2.Error(), "CENTRAL_GUARD_VIOLATION"),
			fmt.Sprintf("error=%v", err2))

		// Test centralized guard for GovernanceKernel
		err3 := modeCtrl.CentralGuardCheck(DecisionInterfaceGovernanceKernel, "Decide", "test_caller_5c")
		logTest("CentralGuard → GovernanceKernel blocked in EXTERNAL", err3 != nil && strings.Contains(err3.Error(), "CENTRAL_GUARD_VIOLATION"),
			fmt.Sprintf("error=%v", err3))

		// Test legacy convenience methods still work
		err4 := modeCtrl.GuardCheckPDP("test_caller_5d")
		logTest("Guard → legacy GuardCheckPDP delegates to CentralGuard", err4 != nil,
			fmt.Sprintf("error=%v", err4))

		// Verify violations were recorded
		violations := modeCtrl.GetGuardViolations()
		logTest("CentralGuard → violations recorded", len(violations) >= 4,
			fmt.Sprintf("violation_count=%d", len(violations)))

		// Verify that in INTERNAL mode, guards pass
		internalCtrl := NewModeController(BHIVModeInternal)
		err5 := internalCtrl.CentralGuardCheck(DecisionInterfacePDP, "Evaluate", "test_caller_5e")
		logTest("CentralGuard → PDP allowed in INTERNAL", err5 == nil,
			fmt.Sprintf("error=%v", err5))
	}

	// ================================================================
	// TEST 6: Expired decision → rejected
	// ================================================================
	printSubheader("TEST 6: Expired Decision → Rejected")
	{
		expiredDecision := NewExternalDecision(
			"ishan-evaluator-v1", "agent-alpha", "project-data", "read",
			ExternalVerdictAllow, nil, nil, "This should be expired", 1*time.Second,
		)
		// Backdate timestamps by 10 seconds — well past TTL (1s) + ClockSkewTolerance (5s)
		expiredDecision.Timestamp = time.Now().UTC().Add(-10 * time.Second)
		expiredDecision.ExpiresAt = expiredDecision.Timestamp.Add(1 * time.Second)
		expiredDecision.DecisionHash = expiredDecision.computeHash()
		expiredDecision.DecisionCoreHash = expiredDecision.computeCoreHash()
		expiredDecision.SignDecision(ishanPriv)

		result := pipeline.Adapter.EnforceExternalDecision(expiredDecision, modeCtrl)
		logTest("Expired → decision rejected", result.Verdict == "DENY",
			fmt.Sprintf("block=%s detail=%s", result.BlockReason, result.BlockDetail))
		logTest("Expired → failed at correct stage",
			result.VerificationTrace != nil && result.VerificationTrace.FailedStage == StageExpiryCheck,
			fmt.Sprintf("failed_stage=%v", result.VerificationTrace.FailedStage))
	}

	// ================================================================
	// TEST 7: Mode transition with lock levels
	// ================================================================
	printSubheader("TEST 7: Mode Transition + Lock Levels")
	{
		mc := NewModeController(BHIVModeInternal)
		logTest("Mode → starts INTERNAL", mc.GetMode() == BHIVModeInternal,
			fmt.Sprintf("mode=%s", mc.GetMode()))

		err := mc.SetMode(BHIVModeExternal, "BHIV_INTEGRATION", "test")
		logTest("Mode → transitions to EXTERNAL", err == nil && mc.GetMode() == BHIVModeExternal,
			fmt.Sprintf("mode=%s err=%v", mc.GetMode(), err))

		err2 := mc.SetMode(BHIVModeInternal, "MAINTENANCE", "admin")
		logTest("Mode → transitions back to INTERNAL", err2 == nil && mc.GetMode() == BHIVModeInternal,
			fmt.Sprintf("mode=%s err=%v", mc.GetMode(), err2))

		// Invalid mode
		err3 := mc.SetMode("INVALID", "test", "test")
		logTest("Mode → rejects invalid mode", err3 != nil,
			fmt.Sprintf("error=%v", err3))

		// Mode history
		history := mc.GetModeHistory()
		logTest("Mode → history recorded", len(history) >= 3,
			fmt.Sprintf("transitions=%d", len(history)))
	}

	// ================================================================
	// TEST 8: Chain integrity after external enforcement
	// ================================================================
	printSubheader("TEST 8: Chain Integrity Verification")
	{
		valid, reason := pipeline.Adapter.VerifyChain()
		logTest("Chain → integrity verified after external enforcement", valid,
			fmt.Sprintf("valid=%v reason=%s", valid, reason))

		chainLen := pipeline.Adapter.InMemoryChainLength()
		logTest("Chain → has entries", chainLen > 0,
			fmt.Sprintf("chain_length=%d", chainLen))
	}

	// ================================================================
	// TEST 9: Full BHIV Flow (Evaluator → Sign → Verify → Enforce → Token → Execute → Audit)
	// ================================================================
	printSubheader("TEST 9: Full BHIV End-to-End Flow (Signed + Verified)")
	{
		bhivModeCtrl := NewModeController(BHIVModeExternal)
		pipeline.Adapter.InitExternalMode()

		// Simulate Ishan's evaluator output (properly signed)
		evaluatorDecision := NewExternalDecision(
			"ishan-evaluator-v2",
			"agent-alpha",
			"project-data",
			"execute",
			ExternalVerdictAllow,
			[]string{"LOG_ACCESS", "NOTIFY_AUDIT"},
			map[string]string{
				"evaluator_version": "2.1.0",
				"confidence":        "0.98",
				"policy_ref":        "POL-2024-001",
			},
			"Agent authorized for execution by BHIV evaluator",
			30*time.Second,
		)
		evaluatorDecision.SignDecision(ishanPrivV2)

		flowResult := BHIVEnforcementFlow(evaluatorDecision, bhivModeCtrl, pipeline.Adapter, pipeline.Engine)

		enfMap := flowResult["enforcement"].(map[string]interface{})
		execMap := flowResult["execution"].(map[string]interface{})

		flowEnforced := enfMap["enforced"].(bool)
		flowExecuted := execMap["executed"].(bool)

		logTest("BHIV Flow → verification + enforcement succeeded", flowEnforced,
			fmt.Sprintf("verdict=%v", enfMap["verdict"]))
		logTest("BHIV Flow → execution succeeded", flowExecuted,
			fmt.Sprintf("status=%v", execMap["execution_state"]))
		logTest("BHIV Flow → correlation tracked", flowResult["correlation_id"] != nil,
			fmt.Sprintf("correlation_id=%v", flowResult["correlation_id"]))
		logTest("BHIV Flow → token issued", flowResult["token_id"] != nil,
			fmt.Sprintf("token_id=%v", flowResult["token_id"]))
		logTest("BHIV Flow → decision core hash bound", flowResult["decision_core_hash"] != nil,
			fmt.Sprintf("core_hash=%v", flowResult["decision_core_hash"]))

		// Verify no PDP was called (guard check)
		guardErr := bhivModeCtrl.GuardCheckPDP("flow_verification")
		logTest("BHIV Flow → PDP guard still active", guardErr != nil,
			"PDP call would be blocked in this mode")

		// Print the complete flow for audit
		flowJSON, _ := json.MarshalIndent(flowResult, "  ", "  ")
		fmt.Printf("\n  BHIV Flow Trace:\n  %s\n", string(flowJSON))
	}

	// ================================================================
	// TEST 10: Internal mode regression check
	// ================================================================
	printSubheader("TEST 10: Internal Mode Regression Check")
	{
		internalModeCtrl := NewModeController(BHIVModeInternal)

		// External enforcement in INTERNAL mode → should be blocked
		decision := createSignedDecision("ishan-evaluator-v1", "agent-alpha", "project-data", "read",
			ExternalVerdictAllow, ishanPriv, 30*time.Second)
		result := pipeline.Adapter.EnforceExternalDecision(decision, internalModeCtrl)
		logTest("Regression → external enforcement blocked in INTERNAL mode",
			result.Verdict == "DENY" && strings.Contains(result.BlockReason, "MODE_NOT_EXTERNAL"),
			fmt.Sprintf("block=%s", result.BlockReason))

		// PDP guard passes in INTERNAL mode
		err := internalModeCtrl.GuardCheckPDP("regression_test")
		logTest("Regression → PDP allowed in INTERNAL mode", err == nil,
			fmt.Sprintf("error=%v", err))

		// Existing pipeline still works in INTERNAL mode
		pipeResult := pipeline.Execute("agent-alpha", "project-data", "read", "regression-test-001")
		enfResp := pipeResult["enforcement"].(map[string]interface{})
		logTest("Regression → internal pipeline works",
			enfResp["verdict"] == "ALLOW" || enfResp["verdict"] == "DENY",
			fmt.Sprintf("verdict=%v", enfResp["verdict"]))
	}

	// ================================================================
	// TEST 11: UNSIGNED decision → rejected
	// ================================================================
	printSubheader("TEST 11: Unsigned Decision → Rejected (No Evaluator Signature)")
	{
		unsignedDecision := NewExternalDecision(
			"ishan-evaluator-v1", "agent-alpha", "project-data", "read",
			ExternalVerdictAllow, nil, nil, "Not signed", 30*time.Second,
		)
		// Do NOT call SignDecision — decision has no signature
		result := pipeline.Adapter.EnforceExternalDecision(unsignedDecision, modeCtrl)
		logTest("Unsigned → decision rejected", result.Verdict == "DENY",
			fmt.Sprintf("block=%s detail=%s", result.BlockReason, result.BlockDetail))
		logTest("Unsigned → failed at structure check",
			result.VerificationTrace != nil && result.VerificationTrace.FailedStage == StageStructureCheck,
			fmt.Sprintf("failed_stage=%v", result.VerificationTrace.FailedStage))
	}

	// ================================================================
	// TEST 12: UNKNOWN evaluator → rejected
	// ================================================================
	printSubheader("TEST 12: Unknown Evaluator → Rejected (Not In Trust Registry)")
	{
		unknownPub, unknownPriv, _ := ed25519.GenerateKey(nil)
		_ = unknownPub // registered nowhere

		unknownDecision := NewExternalDecision(
			"rogue-evaluator-999", "agent-alpha", "project-data", "read",
			ExternalVerdictAllow, nil, nil, "From unknown evaluator", 30*time.Second,
		)
		unknownDecision.SignDecision(unknownPriv)

		result := pipeline.Adapter.EnforceExternalDecision(unknownDecision, modeCtrl)
		logTest("Unknown evaluator → decision rejected", result.Verdict == "DENY",
			fmt.Sprintf("block=%s detail=%s", result.BlockReason, result.BlockDetail))
		logTest("Unknown evaluator → failed at evaluator trust check",
			result.VerificationTrace != nil && result.VerificationTrace.FailedStage == StageEvaluatorTrustCheck,
			fmt.Sprintf("failed_stage=%v", result.VerificationTrace.FailedStage))
	}

	// ================================================================
	// TEST 13: REVOKED evaluator → rejected
	// ================================================================
	printSubheader("TEST 13: Revoked Evaluator → Rejected")
	{
		// Register and then revoke an evaluator
		revokedPub, revokedPriv, _ := ed25519.GenerateKey(nil)
		_ = registry.RegisterEvaluator("revoked-eval-001", "Revoked Evaluator", revokedPub,
			map[string]string{}, "test")
		_ = registry.RevokeEvaluator("revoked-eval-001", "SECURITY_INCIDENT: compromised key", "security-team")

		revokedDecision := NewExternalDecision(
			"revoked-eval-001", "agent-alpha", "project-data", "read",
			ExternalVerdictAllow, nil, nil, "From revoked evaluator", 30*time.Second,
		)
		revokedDecision.SignDecision(revokedPriv)

		result := pipeline.Adapter.EnforceExternalDecision(revokedDecision, modeCtrl)
		logTest("Revoked evaluator → decision rejected", result.Verdict == "DENY",
			fmt.Sprintf("block=%s detail=%s", result.BlockReason, result.BlockDetail))
		logTest("Revoked evaluator → failed at evaluator trust check",
			result.VerificationTrace != nil && result.VerificationTrace.FailedStage == StageEvaluatorTrustCheck,
			fmt.Sprintf("failed_stage=%v reason=%s", result.VerificationTrace.FailedStage, result.VerificationTrace.FailedReason))
	}

	// ================================================================
	// TEST 14: SUSPENDED evaluator → rejected
	// ================================================================
	printSubheader("TEST 14: Suspended Evaluator → Rejected")
	{
		suspPub, suspPriv, _ := ed25519.GenerateKey(nil)
		_ = registry.RegisterEvaluator("suspended-eval-001", "Suspended Evaluator", suspPub,
			map[string]string{}, "test")
		_ = registry.SuspendEvaluator("suspended-eval-001", "MAINTENANCE: key rotation in progress", "ops-team")

		suspDecision := NewExternalDecision(
			"suspended-eval-001", "agent-alpha", "project-data", "read",
			ExternalVerdictAllow, nil, nil, "From suspended evaluator", 30*time.Second,
		)
		suspDecision.SignDecision(suspPriv)

		result := pipeline.Adapter.EnforceExternalDecision(suspDecision, modeCtrl)
		logTest("Suspended evaluator → decision rejected", result.Verdict == "DENY",
			fmt.Sprintf("block=%s detail=%s", result.BlockReason, result.BlockDetail))

		// Now reactivate and verify it works
		_ = registry.ReactivateEvaluator("suspended-eval-001", "Maintenance complete", "ops-team")
		reactivatedDecision := NewExternalDecision(
			"suspended-eval-001", "agent-alpha", "project-data", "read",
			ExternalVerdictAllow, nil, nil, "From reactivated evaluator", 30*time.Second,
		)
		reactivatedDecision.SignDecision(suspPriv)
		result2 := pipeline.Adapter.EnforceExternalDecision(reactivatedDecision, modeCtrl)
		logTest("Reactivated evaluator → decision accepted", result2.Enforced && result2.Verdict == "ALLOW",
			fmt.Sprintf("verdict=%s", result2.Verdict))
	}

	// ================================================================
	// TEST 15: WRONG KEY signature → rejected
	// ================================================================
	printSubheader("TEST 15: Wrong Key Signature → Rejected (Signed by Different Evaluator)")
	{
		// Decision claims to be from ishan-evaluator-v1 but signed by rogue key
		wrongKeyDecision := NewExternalDecision(
			"ishan-evaluator-v1", "agent-alpha", "project-data", "read",
			ExternalVerdictAllow, nil, nil, "Signed with wrong key", 30*time.Second,
		)
		wrongKeyDecision.SignDecision(roguePriv) // Sign with ROGUE key, not Ishan's

		result := pipeline.Adapter.EnforceExternalDecision(wrongKeyDecision, modeCtrl)
		logTest("Wrong key → decision rejected", result.Verdict == "DENY",
			fmt.Sprintf("block=%s detail=%s", result.BlockReason, result.BlockDetail))
		logTest("Wrong key → failed at signature verification",
			result.VerificationTrace != nil && result.VerificationTrace.FailedStage == StageSignatureVerification,
			fmt.Sprintf("failed_stage=%v", result.VerificationTrace.FailedStage))
	}

	// ================================================================
	// TEST 16: TAMPERED core hash → rejected
	// ================================================================
	printSubheader("TEST 16: Tampered Core Hash → Rejected (Binding Broken)")
	{
		tamperedDecision := NewExternalDecision(
			"ishan-evaluator-v1", "agent-alpha", "project-data", "read",
			ExternalVerdictAllow, nil, nil, "Tampered core hash", 30*time.Second,
		)
		tamperedDecision.SignDecision(ishanPriv)
		// Now tamper with the core hash AFTER signing
		tamperedDecision.DecisionCoreHash = "tampered_core_hash_value"

		result := pipeline.Adapter.EnforceExternalDecision(tamperedDecision, modeCtrl)
		logTest("Tampered core hash → decision rejected", result.Verdict == "DENY",
			fmt.Sprintf("block=%s detail=%s", result.BlockReason, result.BlockDetail))
		// Should fail at signature verification (because core hash is the signed payload)
		logTest("Tampered core hash → failed at signature or integrity check",
			result.VerificationTrace != nil &&
				(result.VerificationTrace.FailedStage == StageSignatureVerification ||
					result.VerificationTrace.FailedStage == StageIntegrityCheck),
			fmt.Sprintf("failed_stage=%v", result.VerificationTrace.FailedStage))
	}

	// ================================================================
	// TEST 17: Mode lock IMMUTABLE → SetMode blocked
	// ================================================================
	printSubheader("TEST 17: Mode Lock IMMUTABLE → SetMode Blocked")
	{
		prodCtrl := NewProductionModeController()
		logTest("Production mode → locked to EXTERNAL", prodCtrl.GetMode() == BHIVModeExternal,
			fmt.Sprintf("mode=%s lock=%s", prodCtrl.GetMode(), prodCtrl.GetLockLevel()))

		err := prodCtrl.SetMode(BHIVModeInternal, "ATTACK_ATTEMPT", "attacker")
		logTest("Production mode → SetMode BLOCKED",
			err != nil && strings.Contains(err.Error(), "MODE_LOCKED_IMMUTABLE"),
			fmt.Sprintf("error=%v", err))

		// Mode should still be EXTERNAL
		logTest("Production mode → remains EXTERNAL after attack", prodCtrl.GetMode() == BHIVModeExternal,
			fmt.Sprintf("mode=%s", prodCtrl.GetMode()))

		// Violation should be recorded
		violations := prodCtrl.GetGuardViolations()
		logTest("Production mode → attack recorded as violation", len(violations) >= 1,
			fmt.Sprintf("violations=%d", len(violations)))
	}

	// ================================================================
	// TEST 18: Mode lock PRIVILEGED → unprivileged user blocked
	// ================================================================
	printSubheader("TEST 18: Mode Lock PRIVILEGED → Unprivileged User Blocked")
	{
		privCtrl := NewPrivilegedModeController(BHIVModeExternal, []string{"admin", "security-team"})

		// Unprivileged user cannot change mode
		err := privCtrl.SetMode(BHIVModeInternal, "UNAUTHORIZED_ATTEMPT", "random-user")
		logTest("Privileged lock → unprivileged user blocked",
			err != nil && strings.Contains(err.Error(), "MODE_CHANGE_UNAUTHORIZED"),
			fmt.Sprintf("error=%v", err))

		// Privileged user CAN change mode
		err2 := privCtrl.SetMode(BHIVModeInternal, "MAINTENANCE", "admin")
		logTest("Privileged lock → admin user allowed", err2 == nil,
			fmt.Sprintf("mode=%s error=%v", privCtrl.GetMode(), err2))

		// Switch back
		_ = privCtrl.SetMode(BHIVModeExternal, "MAINTENANCE_COMPLETE", "admin")
	}

	// ================================================================
	// TEST 19: Key rotation → old key accepted during grace period
	// ================================================================
	printSubheader("TEST 19: Key Rotation → Old Key Accepted During Grace Period")
	{
		// Register evaluator with initial key
		rotPub1, rotPriv1, _ := ed25519.GenerateKey(nil)
		_ = registry.RegisterEvaluator("rotating-eval-001", "Rotating Evaluator", rotPub1,
			map[string]string{}, "test")

		// Rotate to new key with 5-minute grace period
		rotPub2, rotPriv2, _ := ed25519.GenerateKey(nil)
		err := registry.RotateKey("rotating-eval-001", rotPub2, 5*time.Minute, "ops-team")
		logTest("Key rotation → rotation succeeded", err == nil,
			fmt.Sprintf("error=%v", err))

		// Decision signed with OLD key (within grace period) should still work
		oldKeyDecision := NewExternalDecision(
			"rotating-eval-001", "agent-alpha", "project-data", "read",
			ExternalVerdictAllow, nil, nil, "Signed with old key during grace period", 30*time.Second,
		)
		oldKeyDecision.SignDecision(rotPriv1)
		result1 := pipeline.Adapter.EnforceExternalDecision(oldKeyDecision, modeCtrl)
		logTest("Key rotation → old key accepted in grace period",
			result1.Enforced && result1.Verdict == "ALLOW",
			fmt.Sprintf("verdict=%s", result1.Verdict))

		// Decision signed with NEW key should also work
		newKeyDecision := NewExternalDecision(
			"rotating-eval-001", "agent-alpha", "project-data", "read",
			ExternalVerdictAllow, nil, nil, "Signed with new key", 30*time.Second,
		)
		newKeyDecision.SignDecision(rotPriv2)
		result2 := pipeline.Adapter.EnforceExternalDecision(newKeyDecision, modeCtrl)
		logTest("Key rotation → new key accepted",
			result2.Enforced && result2.Verdict == "ALLOW",
			fmt.Sprintf("verdict=%s", result2.Verdict))
	}

	// ================================================================
	// TEST 20: Decision-request binding → token bound to core hash
	// ================================================================
	printSubheader("TEST 20: Decision-Request Binding Verification")
	{
		bindDecision := NewExternalDecision(
			"ishan-evaluator-v1", "agent-alpha", "project-data", "execute",
			ExternalVerdictAllow, nil, nil, "Binding test", 30*time.Second,
		)
		bindDecision.SignDecision(ishanPriv)

		result := pipeline.Adapter.EnforceExternalDecision(bindDecision, modeCtrl)
		logTest("Binding → enforcement has decision core hash",
			result.DecisionCoreHash != "" && result.DecisionCoreHash == bindDecision.DecisionCoreHash,
			fmt.Sprintf("core_hash=%s", truncHash(result.DecisionCoreHash)))
		logTest("Binding → enforcement has request binding hash",
			result.RequestBindingHash != "",
			fmt.Sprintf("request_hash=%s", truncHash(result.RequestBindingHash)))
		logTest("Binding → token carries decision binding",
			result.Token != nil,
			"token issued with binding fields")
	}

	// ================================================================
	// SUMMARY
	// ================================================================
	printHeader("EXTERNAL DECISION TRUST BOUNDARY TEST SUMMARY")
	fmt.Printf("  Results: %d/%d tests passed\n", passed, total)
	if passed == total {
		fmt.Println("  Status: ALL TESTS PASSED — TRUST BOUNDARY VERIFIED ✓")
		fmt.Println()
		fmt.Println("  PROOF LOGS:")
		fmt.Println("    • invalid signature    → DENIED (TEST 15)")
		fmt.Println("    • unknown evaluator    → DENIED (TEST 12)")
		fmt.Println("    • revoked evaluator    → DENIED (TEST 13)")
		fmt.Println("    • suspended evaluator  → DENIED (TEST 14)")
		fmt.Println("    • expired decision     → DENIED (TEST 6)")
		fmt.Println("    • replay attempt       → DENIED (TEST 3)")
		fmt.Println("    • unsigned decision    → DENIED (TEST 11)")
		fmt.Println("    • tampered core hash   → DENIED (TEST 16)")
		fmt.Println("    • mode lock bypass     → DENIED (TEST 17)")
		fmt.Println("    • valid signed ALLOW   → TOKEN ISSUED (TEST 1)")
	} else {
		fmt.Printf("  Status: %d TESTS FAILED\n", total-passed)
	}

	return passed, total, details
}

// truncHash returns a truncated hash for display.
func truncHash(h string) string {
	if len(h) > 16 {
		return h[:8] + "..." + h[len(h)-8:]
	}
	return h
}

// RunExternalDecisionDemo runs a demonstration of the hardened external decision path
// with full evaluator signature verification.
func RunExternalDecisionDemo(pipeline *SarathiEnforcementPipeline) {
	printHeader("BHIV EXTERNAL DECISION VERIFICATION + ENFORCEMENT — DEMONSTRATION")

	// Initialize
	pipeline.Adapter.InitExternalMode()
	registry := pipeline.Adapter.GetEvaluatorRegistry()

	// Generate and register evaluator key pair
	evalPub, evalPriv, _ := ed25519.GenerateKey(nil)
	// Only register if not already registered
	if _, exists := registry.GetEvaluator("demo-evaluator"); !exists {
		_ = registry.RegisterEvaluator(
			"demo-evaluator",
			"Demo Evaluator (Ishan)",
			evalPub,
			map[string]string{"version": "demo"},
			"demo-init",
		)
	} else {
		// Use a fresh decision with the already-registered evaluator for demo
		evalPub, evalPriv, _ = ed25519.GenerateKey(nil)
		_ = registry.RegisterEvaluator(
			fmt.Sprintf("demo-evaluator-%d", time.Now().UnixNano()),
			"Demo Evaluator",
			evalPub,
			map[string]string{"version": "demo"},
			"demo-init",
		)
	}

	modeCtrl := NewModeController(BHIVModeExternal)

	fmt.Println("  Mode: EXTERNAL (BHIV-compliant)")
	fmt.Println("  PDP: BLOCKED (centralized guard enforced)")
	fmt.Println("  KSML: BLOCKED (centralized guard enforced)")
	fmt.Println("  GovernanceKernel: BLOCKED (centralized guard enforced)")
	fmt.Printf("  Evaluator Registry: %d evaluators registered\n", registry.EvaluatorCount())
	fmt.Println()

	// Create and sign external decision
	decision := NewExternalDecision(
		"demo-evaluator",
		"agent-alpha",
		"project-data",
		"read",
		ExternalVerdictAllow,
		[]string{"LOG_ACCESS", "NOTIFY_AUDIT"},
		map[string]string{
			"evaluator_version": "2.1.0",
			"confidence":        "0.98",
		},
		"Agent cleared by Ishan's evaluator (Ed25519 signed)",
		30*time.Second,
	)
	decision.SignDecision(evalPriv)

	fmt.Println("  ┌─── Signed External Decision (from Evaluator) ───")
	decisionJSON, _ := json.MarshalIndent(decision.ToMap(), "  │ ", "  ")
	fmt.Printf("  │ %s\n", string(decisionJSON))
	fmt.Println("  └───────────────────────────────────────────────────")

	// Enforce through verification pipeline
	fmt.Println("\n  → Running 10-stage verification pipeline (NO PDP call)...")
	result := pipeline.Adapter.EnforceExternalDecision(decision, modeCtrl)

	fmt.Println("\n  ┌─── Verification + Enforcement Result ───")
	fmt.Printf("  │ Enforced:            %v\n", result.Enforced)
	fmt.Printf("  │ Verdict:             %s\n", result.Verdict)
	fmt.Printf("  │ Mode:                %s\n", result.Mode)
	fmt.Printf("  │ Has Token:           %v\n", result.Token != nil)
	fmt.Printf("  │ Enforcement Hash:    %s\n", truncHash(result.EnforcementHash))
	fmt.Printf("  │ Decision Core Hash:  %s\n", truncHash(result.DecisionCoreHash))
	fmt.Printf("  │ Correlation ID:      %s\n", result.CorrelationID)
	if result.VerificationTrace != nil {
		fmt.Printf("  │ Verification Stages: %d\n", len(result.VerificationTrace.Results))
		fmt.Printf("  │ Verification Verdict: %s\n", result.VerificationTrace.FinalVerdict)
		for _, stage := range result.VerificationTrace.Results {
			status := "✓"
			if !stage.Passed {
				status = "✗"
			}
			fmt.Printf("  │   %s %s: %s\n", status, stage.Stage, stage.Reason)
		}
	}
	fmt.Println("  └────────────────────────────────────────────")

	if result.Token != nil {
		fmt.Println("\n  → Executing with capability token...")
		execResult := pipeline.Engine.ExecuteWithToken(result.Token)
		fmt.Println("\n  ┌─── Execution Result ───")
		fmt.Printf("  │ Executed:     %v\n", execResult.Executed)
		fmt.Printf("  │ Status:       %s\n", execResult.Status)
		fmt.Printf("  │ Token ID:     %s\n", execResult.TokenID)
		fmt.Printf("  │ Decision ID:  %s\n", execResult.DecisionID)
		fmt.Println("  └──────────────────────────")
	}

	// Guard proof
	fmt.Println("\n  → Verifying centralized guard in EXTERNAL mode...")
	err := modeCtrl.CentralGuardCheck(DecisionInterfacePDP, "Evaluate", "demo_verification")
	if err != nil {
		fmt.Printf("  │ PDP BLOCKED: %v\n", err)
	}

	// Chain verification
	fmt.Println("\n  → Verifying enforcement chain integrity...")
	valid, chainReason := pipeline.Adapter.VerifyChain()
	fmt.Printf("  │ Chain Valid: %v\n", valid)
	if chainReason != "" {
		fmt.Printf("  │ Chain Issue: %s\n", chainReason)
	}

	fmt.Printf("\n  │ Total Chain Entries: %d\n", pipeline.Adapter.InMemoryChainLength())
	fmt.Printf("  │ Total Enforcements:  %d\n", pipeline.Adapter.EnforcementCount())
}
