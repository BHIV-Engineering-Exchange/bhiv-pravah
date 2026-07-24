package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
)

type testCase struct {
	agent, resource, action, desc string
}

func main() {
	fmt.Println("+-------------------------------------------------------+")
	fmt.Println("|  SARATHI PDP CORE ENGINE v1.0.0 (Go)                  |")
	fmt.Println("|  Constitutional Policy Decision Point                  |")
	fmt.Println("|  Host: Blackhole Infiverse (BHIV)                      |")
	fmt.Println("+-------------------------------------------------------+")
	fmt.Println()

	ps, err := NewPolicyStore("authority_matrix_v1.json")
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: %v\n", err)
		os.Exit(1)
	}
	registry := NewRegistryInterface()
	pdp := NewSarathiPDP(ps, registry, RealClock{})

	fmt.Printf("Policy Version:  %s\n", ps.PolicyVersion)
	fmt.Printf("Policy Hash:     %s\n", ps.PolicyHash)
	fmt.Printf("Rules Loaded:    %d\n", len(ps.Rules))
	fmt.Println()

	tests := []testCase{
		// ALLOW - Governance agent (L4 clearance)
		{"gov-agent-001", "policy-reg-001", "read", "Governance reads policy registry (L4)"},
		{"gov-agent-001", "policy-reg-001", "write", "Governance writes policy registry (L4)"},
		{"gov-agent-001", "agent-reg-001", "read", "Governance reads agent registry (L3)"},
		{"gov-agent-001", "model-reg-001", "write", "Governance writes model registry (L3)"},
		{"gov-agent-001", "config-001", "write", "Governance writes configuration (L2)"},
		{"gov-agent-001", "trace-001", "read", "Governance reads decision trace (L3)"},
		{"gov-agent-001", "audit-log-001", "read", "Governance reads audit log (L3)"},
		// ALLOW - Standard agent (L2 clearance)
		{"std-agent-001", "ops-data-001", "read", "Standard reads operational data (L1)"},
		{"std-agent-001", "ops-data-001", "write", "Standard writes operational data (L1)"},
		{"std-agent-001", "public-api-001", "read", "Standard reads public API (L0)"},
		{"std-agent-001", "public-api-001", "write", "Standard writes public API (L0)"},
		{"std-agent-001", "config-001", "read", "Standard reads configuration (L2)"},
		{"std-agent-001", "analytics-001", "read", "Standard reads analytics (L1)"},
		// ALLOW - Audit agent (L4 clearance)
		{"audit-agent-001", "trace-001", "read", "Audit reads decision trace (L3)"},
		{"audit-agent-001", "audit-log-001", "read", "Audit reads audit log (L3)"},
		{"audit-agent-001", "policy-reg-001", "read", "Audit reads policy registry (L4)"},
		{"audit-agent-001", "model-reg-001", "read", "Audit reads model registry (L3)"},
		// ALLOW - Safety monitor (L3 clearance)
		{"safety-mon-001", "model-reg-001", "read", "Safety monitor reads model registry (L3)"},
		{"safety-mon-001", "trace-001", "read", "Safety monitor reads decision trace (L3)"},
		{"safety-mon-001", "ops-data-001", "read", "Safety monitor reads operational data (L1)"},
		// ALLOW - Data processor (L1 clearance)
		{"data-proc-001", "ops-data-001", "read", "Data processor reads operational data (L1)"},
		{"data-proc-001", "analytics-001", "write", "Data processor writes analytics (L1)"},
		{"data-proc-001", "public-api-001", "read", "Data processor reads public API (L0)"},
		// ALLOW - Orchestrator (L2 clearance)
		{"orch-001", "ops-data-001", "read", "Orchestrator reads operational data (L1)"},
		// DENY - Explicit rule deny
		{"std-agent-001", "policy-reg-001", "read", "Standard DENIED policy registry (L4>L2)"},
		{"std-agent-001", "policy-reg-001", "write", "Standard DENIED policy write"},
		{"std-agent-001", "agent-reg-001", "read", "Standard DENIED agent registry (L3>L2)"},
		{"std-agent-001", "config-001", "write", "Standard DENIED config write"},
		{"std-agent-001", "analytics-001", "write", "Standard DENIED analytics write"},
		{"std-agent-001", "model-reg-001", "read", "Standard DENIED model registry (L3>L2)"},
		{"std-agent-001", "audit-log-001", "read", "Standard DENIED audit log (L3>L2)"},
		{"audit-agent-001", "trace-001", "write", "Audit DENIED trace write (immutability)"},
		{"audit-agent-001", "audit-log-001", "write", "Audit DENIED audit log write"},
		{"safety-mon-001", "model-reg-001", "write", "Safety DENIED model write (SoD)"},
		{"gov-agent-001", "audit-log-001", "write", "Governance DENIED audit log write"},
		{"data-proc-001", "config-001", "read", "Data processor DENIED config (L2>L1)"},
		{"data-proc-001", "agent-reg-001", "read", "Data processor DENIED agent reg (L3>L1)"},
		{"orch-001", "agent-reg-001", "read", "Orchestrator DENIED agent registry (L3>L2)"},
		{"orch-001", "policy-reg-001", "read", "Orchestrator DENIED policy registry (L4>L2)"},
		// DENY - Agent lifecycle
		{"nonexistent-agent", "ops-data-001", "read", "Agent not found -> DENY"},
		{"suspended-agent", "ops-data-001", "read", "Suspended agent -> DENY"},
		{"revoked-agent", "ops-data-001", "read", "Revoked agent -> DENY"},
		{"terminated-agent", "ops-data-001", "read", "Terminated agent -> DENY"},
		// DENY - Invalid request
		{"std-agent-001", "ops-data-001", "delete", "Invalid action -> DENY"},
		{"", "ops-data-001", "read", "Empty agent ID -> DENY"},
		{"std-agent-001", "", "read", "Empty resource ID -> DENY"},
		{"std-agent-001", "nonexistent-resource", "read", "Resource not found -> DENY"},
	}

	fmt.Println(strings.Repeat("=", 105))
	fmt.Printf("%-3s %-8s %-38s %-22s %s\n", "#", "Verdict", "Reason", "Rules", "Description")
	fmt.Println(strings.Repeat("=", 105))

	allowCount, denyCount := 0, 0
	for i, tc := range tests {
		req := &PDPRequest{AgentID: tc.agent, ResourceID: tc.resource, Action: tc.action}
		resp := pdp.Evaluate(req)

		rulesStr := strings.Join(resp.DeterminingRules, ",")
		if rulesStr == "" {
			rulesStr = "-"
		}
		fmt.Printf("%-3d %-8s %-38s %-22s %s\n",
			i+1, resp.Verdict, resp.Reason, rulesStr, tc.desc)

		if resp.Verdict == "ALLOW" {
			allowCount++
		} else {
			denyCount++
		}
	}

	fmt.Println(strings.Repeat("=", 105))
	fmt.Printf("ALLOW: %d  |  DENY: %d  |  Total: %d\n\n", allowCount, denyCount, allowCount+denyCount)

	// Write decision trace (APPENDS to existing chain from previous runs)
	if err := pdp.TraceStore.WriteToFile("decision_trace.json"); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR writing trace: %v\n", err)
	} else {
		fmt.Printf("Decision trace written: %d total entries\n", len(pdp.TraceStore.Traces))
		pdp.TraceStore.VerifyChain()
		fmt.Println("Decision trace chain integrity verified.")
	}

	// Write sample decision output
	sampleReq := &PDPRequest{AgentID: "gov-agent-001", ResourceID: "policy-reg-001", Action: "read"}
	sampleResp := pdp.Evaluate(sampleReq)
	sampleJSON, _ := json.MarshalIndent(sampleResp, "", "  ")
	os.WriteFile("sample_decision_output.json", sampleJSON, 0644)
	fmt.Println("Sample decision output written to sample_decision_output.json")
}
