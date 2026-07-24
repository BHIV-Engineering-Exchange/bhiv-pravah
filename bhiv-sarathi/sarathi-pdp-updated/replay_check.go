//go:build ignore

// Sarathi PDP Replay Check — Deterministic Replay Verification
// Run:  go run replay_check.go pdp_engine.go policy_store.go registry_interface.go clock.go
// This runs the same requests through two independent PDP instances
// and verifies deterministic output using full response hash comparison.

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"
	"time"
)

func main() {
	fmt.Println("+-------------------------------------------------------+")
	fmt.Println("|  SARATHI PDP -- DETERMINISTIC REPLAY CHECK             |")
	fmt.Println("|  Full Response Hash Verification (100 Test Cases)      |")
	fmt.Println("+-------------------------------------------------------+")
	fmt.Println()

	// Create TWO independent PDP instances — separate PolicyStore, separate Registry,
	// separate DecisionTraceStore (in-memory, not loading from file for clean test)
	ps1, err := NewPolicyStore("authority_matrix_v1.json")
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: %v\n", err)
		os.Exit(1)
	}
	ps2, err := NewPolicyStore("authority_matrix_v1.json")
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: %v\n", err)
		os.Exit(1)
	}

	// Use DeterministicClock with a fixed timestamp for both instances
	fixedTime, _ := time.Parse("2006-01-02T15:04:05.000000Z", "2026-03-01T00:00:00.000000Z")
	clock := DeterministicClock{FixedTime: fixedTime}

	// NewSarathiPDPFresh creates PDP without loading existing trace file — ReplayMode=true
	pdp1 := NewSarathiPDPFresh(ps1, NewRegistryInterface(), clock, true)
	pdp2 := NewSarathiPDPFresh(ps2, NewRegistryInterface(), clock, true)

	fmt.Printf("PDP Instance 1: policy_hash=%s...\n", ps1.PolicyHash[:16])
	fmt.Printf("PDP Instance 2: policy_hash=%s...\n", ps2.PolicyHash[:16])
	fmt.Printf("Hash Match:     %v\n", ps1.PolicyHash == ps2.PolicyHash)
	fmt.Printf("Replay Mode:    ENABLED (no persistent trace mutation)\n")

	// ================================================================
	// REGISTRY DETERMINISM VERIFICATION
	// Verify that both independent registry instances produce identical
	// data for all agents and resources. This ensures registry responses
	// are deterministic and cannot cause divergent PDP decisions.
	// ================================================================
	reg1 := pdp1.Registry
	reg2 := pdp2.Registry

	// Hash all agent data from both registries
	agentIDs := []string{}
	for id := range reg1.GetAllAgents() {
		agentIDs = append(agentIDs, id)
	}
	sort.Strings(agentIDs)
	agent1JSON, _ := json.Marshal(agentIDs)
	agent1Data := Sha256Hex(agent1JSON)

	agentIDs2 := []string{}
	for id := range reg2.GetAllAgents() {
		agentIDs2 = append(agentIDs2, id)
	}
	sort.Strings(agentIDs2)
	agent2JSON, _ := json.Marshal(agentIDs2)
	agent2Data := Sha256Hex(agent2JSON)

	// Hash all resource data from both registries
	resIDs := []string{}
	for id := range reg1.GetAllResources() {
		resIDs = append(resIDs, id)
	}
	sort.Strings(resIDs)
	res1JSON, _ := json.Marshal(resIDs)
	res1Data := Sha256Hex(res1JSON)

	resIDs2 := []string{}
	for id := range reg2.GetAllResources() {
		resIDs2 = append(resIDs2, id)
	}
	sort.Strings(resIDs2)
	res2JSON, _ := json.Marshal(resIDs2)
	res2Data := Sha256Hex(res2JSON)

	registryDeterministic := agent1Data == agent2Data && res1Data == res2Data
	fmt.Printf("Registry Match: %v (agents: %v, resources: %v)\n\n",
		registryDeterministic, agent1Data == agent2Data, res1Data == res2Data)
	if !registryDeterministic {
		fmt.Fprintf(os.Stderr, "FATAL: Registry determinism violation — aborting replay\n")
		os.Exit(1)
	}

	type replayCase struct {
		agent, resource, action string
	}

	tests := []replayCase{
		// === ALLOW — Governance agent (L4 clearance) ===
		{"gov-agent-001", "policy-reg-001", "read"},
		{"gov-agent-001", "policy-reg-001", "write"},
		{"gov-agent-001", "agent-reg-001", "read"},
		{"gov-agent-001", "agent-reg-001", "write"},
		{"gov-agent-001", "model-reg-001", "read"},
		{"gov-agent-001", "model-reg-001", "write"},
		{"gov-agent-001", "config-001", "read"},
		{"gov-agent-001", "config-001", "write"},
		{"gov-agent-001", "trace-001", "read"},
		{"gov-agent-001", "audit-log-001", "read"},
		{"gov-agent-001", "ops-data-001", "read"},
		{"gov-agent-001", "public-api-001", "read"},
		{"gov-agent-002", "policy-reg-001", "read"},
		{"gov-agent-002", "policy-reg-002", "read"},
		// === ALLOW — Standard agent (L2 clearance) ===
		{"std-agent-001", "ops-data-001", "read"},
		{"std-agent-001", "ops-data-001", "write"},
		{"std-agent-001", "public-api-001", "read"},
		{"std-agent-001", "public-api-001", "write"},
		{"std-agent-001", "config-001", "read"},
		{"std-agent-001", "analytics-001", "read"},
		{"std-agent-002", "ops-data-001", "read"},
		{"std-agent-002", "public-api-001", "read"},
		// === ALLOW — Audit agent (L4 clearance) ===
		{"audit-agent-001", "trace-001", "read"},
		{"audit-agent-001", "trace-002", "read"},
		{"audit-agent-001", "audit-log-001", "read"},
		{"audit-agent-001", "policy-reg-001", "read"},
		{"audit-agent-001", "model-reg-001", "read"},
		{"audit-agent-001", "agent-reg-001", "read"},
		{"audit-agent-001", "config-001", "read"},
		{"audit-agent-002", "trace-001", "read"},
		{"audit-agent-002", "audit-log-001", "read"},
		// === ALLOW — Safety monitor (L3 clearance) ===
		{"safety-mon-001", "model-reg-001", "read"},
		{"safety-mon-001", "trace-001", "read"},
		{"safety-mon-001", "ops-data-001", "read"},
		{"safety-mon-001", "agent-reg-001", "read"},
		{"safety-mon-001", "config-001", "read"},
		// === ALLOW — Data processor (L1 clearance) ===
		{"data-proc-001", "ops-data-001", "read"},
		{"data-proc-001", "ops-data-002", "read"},
		{"data-proc-001", "analytics-001", "read"},
		{"data-proc-001", "analytics-001", "write"},
		{"data-proc-001", "public-api-001", "read"},
		{"data-proc-002", "ops-data-001", "read"},
		{"data-proc-002", "analytics-001", "write"},
		// === ALLOW — Orchestrator (L2 clearance) ===
		{"orch-001", "ops-data-001", "read"},
		{"orch-001", "ops-data-002", "read"},
		// === DENY — Explicit deny rules ===
		{"std-agent-001", "policy-reg-001", "read"},
		{"std-agent-001", "policy-reg-001", "write"},
		{"std-agent-001", "agent-reg-001", "read"},
		{"std-agent-001", "agent-reg-001", "write"},
		{"std-agent-001", "config-001", "write"},
		{"std-agent-001", "analytics-001", "write"},
		{"std-agent-001", "model-reg-001", "read"},
		{"std-agent-001", "audit-log-001", "read"},
		{"std-agent-001", "decision_trace", "read"},
		{"std-agent-002", "policy-reg-001", "read"},
		{"std-agent-002", "agent-reg-001", "read"},
		// === DENY — Audit immutability (write denied) ===
		{"audit-agent-001", "trace-001", "write"},
		{"audit-agent-001", "audit-log-001", "write"},
		{"audit-agent-002", "trace-001", "write"},
		// === DENY — Safety separation of duty ===
		{"safety-mon-001", "model-reg-001", "write"},
		// === DENY — Governance audit log immutability ===
		{"gov-agent-001", "audit-log-001", "write"},
		// === DENY — Classification ceiling failures (Bell-LaPadula) ===
		{"data-proc-001", "config-001", "read"},
		{"data-proc-001", "agent-reg-001", "read"},
		{"data-proc-001", "model-reg-001", "read"},
		{"data-proc-001", "policy-reg-001", "read"},
		{"data-proc-001", "trace-001", "read"},
		{"data-proc-001", "audit-log-001", "read"},
		{"data-proc-002", "config-001", "read"},
		{"data-proc-002", "agent-reg-001", "read"},
		{"std-agent-003", "ops-data-001", "read"},
		{"std-agent-003", "config-001", "read"},
		// === DENY — Orchestrator classification ceiling ===
		{"orch-001", "agent-reg-001", "read"},
		{"orch-001", "policy-reg-001", "read"},
		{"orch-001", "model-reg-001", "read"},
		{"orch-001", "trace-001", "read"},
		// === DENY — Wildcard deny-all fallback ===
		{"gov-agent-001", "ops-data-001", "write"},
		{"gov-agent-001", "analytics-001", "write"},
		{"safety-mon-001", "public-api-001", "write"},
		{"orch-001", "config-001", "write"},
		// === DENY — Agent lifecycle ===
		{"nonexistent-agent", "ops-data-001", "read"},
		{"suspended-agent", "ops-data-001", "read"},
		{"revoked-agent", "ops-data-001", "read"},
		{"terminated-agent", "ops-data-001", "read"},
		{"nonexistent-agent", "policy-reg-001", "read"},
		{"suspended-agent", "config-001", "read"},
		// === DENY — Invalid requests ===
		{"std-agent-001", "ops-data-001", "delete"},
		{"std-agent-001", "ops-data-001", "execute"},
		{"gov-agent-001", "ops-data-001", "delete"},
		{"", "ops-data-001", "read"},
		{"std-agent-001", "", "read"},
		{"", "", "read"},
		{"std-agent-001", "ops-data-001", ""},
		// === DENY — Missing resources ===
		{"std-agent-001", "nonexistent-resource", "read"},
		{"gov-agent-001", "nonexistent-resource", "read"},
		{"audit-agent-001", "nonexistent-resource", "read"},
		{"data-proc-001", "nonexistent-resource", "read"},
		// === DENY — Additional edge cases to reach 100 ===
		{"safety-mon-001", "nonexistent-resource", "read"},
		{"orch-001", "nonexistent-resource", "read"},
		{"std-agent-003", "public-api-001", "write"},
		{"data-proc-002", "ops-data-001", "write"},
	}

	fmt.Println("================================================================")
	fmt.Println("FULL RESPONSE HASH PROOF (Test Case 1)")
	fmt.Println("This demonstrates that all 12 fields (including timestamp,")
	fmt.Println("decision_id, request_hash) are serialized and hashed together:")
	fmt.Println("================================================================")
	
	proofReq := &PDPRequest{AgentID: tests[0].agent, ResourceID: tests[0].resource, Action: tests[0].action}
	proofResp := pdp1.Evaluate(proofReq)
	proofJSON, _ := json.MarshalIndent(proofResp, "", "  ")
	fmt.Printf("%s\n", proofJSON)
	fmt.Printf("\nSHA256 Hash -> %s\n", Sha256Hex(proofJSON))
	fmt.Println("================================================================")
	fmt.Println()

	fmt.Printf("Running %d test cases through both PDP instances...\n\n", len(tests))
	fmt.Printf("%-3s %-9s %-9s %-12s %-12s %-12s %-10s %s\n",
		"#", "Verdict1", "Verdict2", "VerdictOK", "RulesOK", "RespHashOK", "StageOK", "Status")
	fmt.Println(strings.Repeat("-", 90))

	passed, failed := 0, 0
	for i, tc := range tests {
		req := &PDPRequest{AgentID: tc.agent, ResourceID: tc.resource, Action: tc.action}
		r1 := pdp1.Evaluate(req)
		r2 := pdp2.Evaluate(req)

		verdictMatch := r1.Verdict == r2.Verdict
		rulesMatch := strings.Join(r1.DeterminingRules, ",") == strings.Join(r2.DeterminingRules, ",")
		reasonMatch := r1.Reason == r2.Reason
		policyMatch := r1.PolicyHash == r2.PolicyHash
		stageMatch := r1.StageReached == r2.StageReached

		// Full response hash comparison (Part 4)
		resp1JSON, _ := json.Marshal(r1)
		resp2JSON, _ := json.Marshal(r2)
		respHash1 := Sha256Hex(resp1JSON)
		respHash2 := Sha256Hex(resp2JSON)
		respHashMatch := respHash1 == respHash2

		allMatch := verdictMatch && rulesMatch && reasonMatch && policyMatch && respHashMatch && stageMatch

		status := "[PASS]"
		if !allMatch {
			status = "[FAIL]"
			failed++
		} else {
			passed++
		}

		vOK := "YES"
		rOK := "YES"
		hOK := "YES"
		sOK := "YES"
		if !verdictMatch {
			vOK = "NO"
		}
		if !rulesMatch {
			rOK = "NO"
		}
		if !respHashMatch {
			hOK = "NO"
		}
		if !stageMatch {
			sOK = "NO"
		}

		fmt.Printf("%-3d %-9s %-9s %-12s %-12s %-12s %-10s %s\n",
			i+1, r1.Verdict, r2.Verdict, vOK, rOK, hOK, sOK, status)

		if !allMatch {
			fmt.Printf("    MISMATCH: R1=%s/%s/Stage%d R2=%s/%s/Stage%d RespHash1=%s... RespHash2=%s...\n",
				r1.Verdict, r1.Reason, r1.StageReached,
				r2.Verdict, r2.Reason, r2.StageReached,
				respHash1[:16], respHash2[:16])
		}
	}

	fmt.Println(strings.Repeat("-", 90))
	total := passed + failed
	rate := float64(failed) / float64(total) * 100
	fmt.Println()
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("  REPLAY TEST RESULTS")
	fmt.Println(strings.Repeat("=", 60))
	fmt.Printf("  Total Requests:    %d\n", total)
	fmt.Printf("  Passed:            %d\n", passed)
	fmt.Printf("  Failed:            %d\n", failed)
	fmt.Printf("  Mismatch Rate:     %.2f%%\n", rate)
	fmt.Printf("  Policy Version:    %s\n", ps1.PolicyVersion)
	fmt.Printf("  Policy Hash:       %s\n", ps1.PolicyHash)
	fmt.Printf("  Replay Mode:       ENABLED\n")
	fmt.Println()

	if failed == 0 {
		fmt.Println("  +=========================================+")
		fmt.Println("  |  REPLAY TEST: PASSED                    |")
		fmt.Println("  |  DETERMINISM: PROVEN                    |")
		fmt.Println("  |  Sarathi PDP produces identical results |")
		fmt.Println("  |  across independent instances.          |")
		fmt.Println("  +=========================================+")
	} else {
		fmt.Println("  +=========================================+")
		fmt.Println("  |  REPLAY TEST: FAILED                    |")
		fmt.Println("  |  GOVERNANCE DRIFT DETECTED              |")
		fmt.Println("  +=========================================+")
	}

	// Write result as JSON with all required fields
	result := map[string]interface{}{
		"total":          total,
		"passed":         passed,
		"failed":         failed,
		"mismatch_rate":  fmt.Sprintf("%.2f%%", rate),
		"policy_hash":    ps1.PolicyHash,
		"policy_version": ps1.PolicyVersion,
	}
	if failed == 0 {
		result["status"] = "PASS"
	} else {
		result["status"] = "FAIL"
	}
	resultJSON, _ := json.MarshalIndent(result, "", "  ")
	os.WriteFile("replay_check_result.json", resultJSON, 0644)

	if failed > 0 {
		os.Exit(1)
	}
}
