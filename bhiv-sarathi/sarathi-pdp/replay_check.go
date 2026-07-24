//go:build ignore

// Sarathi PDP Replay Check
// Run:  go run replay_check.go pdp_engine.go policy_store.go registry_interface.go
// This runs the same requests through two independent PDP instances
// and verifies deterministic output.

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
)

func main() {
	fmt.Println("+-------------------------------------------------------+")
	fmt.Println("|  SARATHI PDP -- DETERMINISTIC REPLAY CHECK             |")
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

	// NewSarathiPDPFresh creates PDP without loading existing trace file
	pdp1 := NewSarathiPDPFresh(ps1, NewRegistryInterface())
	pdp2 := NewSarathiPDPFresh(ps2, NewRegistryInterface())

	fmt.Printf("PDP Instance 1: policy_hash=%s...\n", ps1.PolicyHash[:16])
	fmt.Printf("PDP Instance 2: policy_hash=%s...\n", ps2.PolicyHash[:16])
	fmt.Printf("Hash Match:     %v\n\n", ps1.PolicyHash == ps2.PolicyHash)

	type replayCase struct {
		agent, resource, action string
	}

	tests := []replayCase{
		{"gov-agent-001", "policy-reg-001", "read"},
		{"gov-agent-001", "policy-reg-001", "write"},
		{"gov-agent-001", "agent-reg-001", "read"},
		{"gov-agent-001", "model-reg-001", "write"},
		{"std-agent-001", "ops-data-001", "read"},
		{"std-agent-001", "ops-data-001", "write"},
		{"std-agent-001", "public-api-001", "read"},
		{"std-agent-001", "config-001", "read"},
		{"audit-agent-001", "trace-001", "read"},
		{"audit-agent-001", "policy-reg-001", "read"},
		{"safety-mon-001", "model-reg-001", "read"},
		{"safety-mon-001", "trace-001", "read"},
		{"data-proc-001", "ops-data-001", "read"},
		{"data-proc-001", "analytics-001", "write"},
		{"orch-001", "ops-data-001", "read"},
		{"std-agent-001", "policy-reg-001", "read"},
		{"std-agent-001", "agent-reg-001", "read"},
		{"audit-agent-001", "trace-001", "write"},
		{"safety-mon-001", "model-reg-001", "write"},
		{"data-proc-001", "config-001", "read"},
		{"orch-001", "policy-reg-001", "read"},
		{"nonexistent-agent", "ops-data-001", "read"},
		{"suspended-agent", "ops-data-001", "read"},
		{"revoked-agent", "ops-data-001", "read"},
		{"terminated-agent", "ops-data-001", "read"},
		{"std-agent-001", "ops-data-001", "delete"},
		{"", "ops-data-001", "read"},
		{"std-agent-001", "", "read"},
		{"std-agent-001", "nonexistent-resource", "read"},
		{"gov-agent-001", "audit-log-001", "write"},
	}

	fmt.Printf("Running %d test cases through both PDP instances...\n\n", len(tests))
	fmt.Printf("%-3s %-9s %-9s %-12s %-12s %s\n",
		"#", "Verdict1", "Verdict2", "VerdictOK", "RulesOK", "Status")
	fmt.Println(strings.Repeat("-", 70))

	passed, failed := 0, 0
	for i, tc := range tests {
		req := &PDPRequest{AgentID: tc.agent, ResourceID: tc.resource, Action: tc.action}
		r1 := pdp1.Evaluate(req)
		r2 := pdp2.Evaluate(req)

		verdictMatch := r1.Verdict == r2.Verdict
		rulesMatch := strings.Join(r1.DeterminingRules, ",") == strings.Join(r2.DeterminingRules, ",")
		reasonMatch := r1.Reason == r2.Reason
		policyMatch := r1.PolicyHash == r2.PolicyHash
		allMatch := verdictMatch && rulesMatch && reasonMatch && policyMatch

		status := "[PASS]"
		if !allMatch {
			status = "[FAIL]"
			failed++
		} else {
			passed++
		}

		vOK := "YES"
		rOK := "YES"
		if !verdictMatch {
			vOK = "NO"
		}
		if !rulesMatch {
			rOK = "NO"
		}

		fmt.Printf("%-3d %-9s %-9s %-12s %-12s %s\n",
			i+1, r1.Verdict, r2.Verdict, vOK, rOK, status)

		if !allMatch {
			fmt.Printf("    MISMATCH: R1=%s/%s R2=%s/%s\n",
				r1.Verdict, r1.Reason, r2.Verdict, r2.Reason)
		}
	}

	fmt.Println(strings.Repeat("-", 70))
	total := passed + failed
	rate := float64(failed) / float64(total) * 100
	fmt.Println()
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("  REPLAY TEST RESULTS")
	fmt.Println(strings.Repeat("=", 60))
	fmt.Printf("  Total Requests:    %d\n", total)
	fmt.Printf("  Passed:            %d\n", passed)
	fmt.Printf("  Failed:            %d\n", failed)
	fmt.Printf("  Mismatch Rate:     %.4f%%\n", rate)
	fmt.Printf("  Policy Version:    %s\n", ps1.PolicyVersion)
	fmt.Printf("  Policy Hash:       %s\n", ps1.PolicyHash)
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

	// Write result as JSON
	result := map[string]interface{}{
		"total": total, "passed": passed, "failed": failed,
		"mismatch_rate": rate,
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
