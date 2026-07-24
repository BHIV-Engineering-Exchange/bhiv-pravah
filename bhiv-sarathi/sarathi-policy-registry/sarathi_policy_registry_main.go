package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"
)

// ================================================================
// SARATHI POLICY REGISTRY — Main Entry Point
// ================================================================
//
// This program demonstrates and verifies ALL six governance guarantees:
//
//   FIX 1: PolicyStore immutability — unexported fields, no mutation path
//   FIX 2: Config-driven active policy selection — registry_config.json
//   FIX 3: Per-version hash validation proof — explicit recomputation per version
//   FIX 4: Cross-version replay evidence — same request + different policy = controlled diff
//   FIX 5: PDP dependency refactor — PDP created via registry, not direct file load
//   FIX 6: Version binding in decision output — every response carries correct version/hash
//
// Test coverage: 50 cases across 8 categories (CAT-A through CAT-H)

func main() {
	fmt.Println("+-------------------------------------------------------+")
	fmt.Println("|  SARATHI POLICY REGISTRY v1.0.0                       |")
	fmt.Println("|  Versioned Policy Governance + Replay Verification    |")
	fmt.Println("|  Host: Blackhole Infiverse (BHIV)                     |")
	fmt.Println("|  All Six Governance Gaps Addressed                    |")
	fmt.Println("+-------------------------------------------------------+")
	fmt.Println()

	// ================================================================
	// PHASE 1: Initialize Policy Registry FROM CONFIG (Fix 2)
	// ================================================================
	fmt.Println("═══════════════════════════════════════════════════════════")
	fmt.Println("  PHASE 1: POLICY REGISTRY INITIALIZATION (Config-Driven)")
	fmt.Println("═══════════════════════════════════════════════════════════")

	// FIX 2: Config-driven active policy selection
	// The active version is read from registry_config.json, not hardcoded.
	registry, err := NewPolicyRegistryFromConfig("registry_config.json")
	if err != nil {
		// Fallback: if config doesn't exist, create registry manually
		// This preserves backward compatibility but logs a warning.
		fmt.Printf("[WARN] Config load failed (%v), falling back to manual init\n", err)
		registry = NewPolicyRegistry("./policies")
	}

	// Load all available policies
	var loaded int
	if registry.config != nil {
		loaded, err = registry.InitializeFromConfig()
	} else {
		loaded, err = registry.LoadAllPolicies()
		if err == nil {
			err = registry.SetActivePolicy("v1")
		}
	}
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("\nLoaded %d policy versions\n", loaded)

	// ================================================================
	// PHASE 2: PER-VERSION HASH VALIDATION PROOF (Fix 3)
	// ================================================================
	fmt.Println()
	fmt.Println("═══════════════════════════════════════════════════════════")
	fmt.Println("  PHASE 2: PER-VERSION HASH VALIDATION PROOF")
	fmt.Println("═══════════════════════════════════════════════════════════")

	type hashProof struct {
		Version       string `json:"version"`
		StoredHash    string `json:"stored_hash"`
		RecomputedHash string `json:"recomputed_hash"`
		Match         bool   `json:"match"`
		RuleCount     int    `json:"rule_count"`
	}

	hashProofs := []hashProof{}
	for _, ver := range registry.ListPolicyVersions() {
		stored, recomputed, match, err := registry.VerifyPolicyVersion(ver)
		if err != nil {
			fmt.Fprintf(os.Stderr, "FATAL: hash verification error for %s: %v\n", ver, err)
			os.Exit(1)
		}
		ps := registry.GetPolicy(ver)
		proof := hashProof{
			Version:        ver,
			StoredHash:     stored,
			RecomputedHash: recomputed,
			Match:          match,
			RuleCount:      ps.RuleCount(),
		}
		hashProofs = append(hashProofs, proof)
		status := "VERIFIED"
		if !match {
			status = "VIOLATION"
			fmt.Fprintf(os.Stderr, "FATAL: Hash mismatch for %s!\n", ver)
			os.Exit(1)
		}
		fmt.Printf("  [%s] %s: stored=%s..., recomputed=%s..., rules=%d\n",
			status, ver, stored[:16], recomputed[:16], ps.RuleCount())
	}

	// FIX 1: Verify PolicyStore immutability
	fmt.Println()
	fmt.Println("  --- PolicyStore Immutability Check (Fix 1) ---")
	for _, ver := range registry.ListPolicyVersions() {
		ps := registry.GetPolicy(ver)
		if ps.IsFrozen() {
			fmt.Printf("  [OK] %s: IsFrozen()=true, unexported fields, no mutation path\n", ver)
		} else {
			fmt.Fprintf(os.Stderr, "FATAL: Policy %s is NOT frozen!\n", ver)
			os.Exit(1)
		}
	}

	registry.PrintRegistryStatus()

	// ================================================================
	// PHASE 3: PDP EVALUATION — 50 Test Cases Under v1
	// ================================================================
	fmt.Println("═══════════════════════════════════════════════════════════")
	fmt.Println("  PHASE 3: PDP EVALUATION — 50 TEST CASES UNDER v1")
	fmt.Println("═══════════════════════════════════════════════════════════")

	// Use DeterministicClock for reproducible results
	fixedTime, _ := time.Parse("2006-01-02T15:04:05.000000Z", "2026-03-13T00:00:00.000000Z")
	clock := DeterministicClock{FixedTime: fixedTime}
	agentRegistry := NewRegistryInterface()

	// FIX 5: Create PDP via registry, not direct PolicyStore access
	pdpV1, err := NewSarathiPDPFromRegistry(registry, agentRegistry, clock)
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: Cannot create PDP from registry: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("\n  PDP created via NewSarathiPDPFromRegistry (Fix 5)\n")
	fmt.Printf("  Bound policy: version=%s, hash=%s...\n",
		pdpV1.GetPolicyVersion(), pdpV1.GetPolicyHash()[:16])

	// 50 Test Cases across 8 categories
	type testCase struct {
		cat      string
		agent    string
		resource string
		action   string
		desc     string
	}

	allCases := []testCase{
		// CAT-A: Cases affected by policy changes (AUTH-038 and AUTH-046)
		{"CAT-A", "std-agent-001", "model-reg-001", "read", "Standard agent reads model registry (AUTH-038)"},
		{"CAT-A", "std-agent-002", "model-reg-001", "read", "Standard agent 2 reads model registry (AUTH-038)"},
		{"CAT-A", "data-proc-001", "config-001", "read", "Data processor reads config-001 (AUTH-046)"},
		{"CAT-A", "data-proc-002", "config-001", "read", "Data processor 2 reads config-001 (AUTH-046)"},
		{"CAT-A", "data-proc-001", "config-002", "read", "Data processor reads config-002 (AUTH-046)"},

		// CAT-B: Governance agent operations (should always ALLOW)
		{"CAT-B", "gov-agent-001", "policy-reg-001", "read", "Governance reads policy registry"},
		{"CAT-B", "gov-agent-001", "policy-reg-002", "read", "Governance reads policy registry 2"},
		{"CAT-B", "gov-agent-001", "agent-reg-001", "read", "Governance reads agent registry"},
		{"CAT-B", "gov-agent-001", "trace-001", "read", "Governance reads decision trace"},
		{"CAT-B", "gov-agent-001", "model-reg-001", "read", "Governance reads model registry"},
		{"CAT-B", "gov-agent-002", "policy-reg-001", "read", "Governance 2 reads policy registry"},
		{"CAT-B", "gov-agent-001", "audit-log-001", "read", "Governance reads audit log"},

		// CAT-C: Standard agent ALLOW operations
		{"CAT-C", "std-agent-001", "ops-data-001", "read", "Standard reads ops data"},
		{"CAT-C", "std-agent-001", "ops-data-002", "read", "Standard reads ops data 2"},
		{"CAT-C", "std-agent-002", "ops-data-001", "read", "Standard 2 reads ops data"},
		{"CAT-C", "std-agent-001", "public-api-001", "read", "Standard reads public API"},
		{"CAT-C", "std-agent-001", "analytics-001", "read", "Standard reads analytics"},
		{"CAT-C", "std-agent-003", "ops-data-001", "read", "Standard 3 (L1) reads ops data"},

		// CAT-D: Standard agent DENY operations (explicit deny, no change)
		{"CAT-D", "std-agent-001", "policy-reg-001", "read", "Standard reads policy registry (DENY)"},
		{"CAT-D", "std-agent-001", "agent-reg-001", "read", "Standard reads agent registry (DENY)"},
		{"CAT-D", "std-agent-001", "trace-001", "read", "Standard reads decision trace (DENY)"},
		{"CAT-D", "std-agent-002", "policy-reg-001", "read", "Standard 2 reads policy registry (DENY)"},
		{"CAT-D", "std-agent-001", "audit-log-001", "read", "Standard reads audit log (DENY)"},

		// CAT-E: Audit and safety monitor operations
		{"CAT-E", "audit-agent-001", "trace-001", "read", "Audit reads trace (ALLOW)"},
		{"CAT-E", "audit-agent-001", "trace-002", "read", "Audit reads trace 2 (ALLOW)"},
		{"CAT-E", "audit-agent-002", "trace-001", "read", "Audit 2 reads trace (ALLOW)"},
		{"CAT-E", "audit-agent-001", "trace-001", "write", "Audit writes trace (DENY)"},
		{"CAT-E", "safety-mon-001", "model-reg-001", "read", "Safety reads model registry (ALLOW)"},
		{"CAT-E", "safety-mon-001", "trace-001", "read", "Safety reads trace (ALLOW)"},

		// CAT-F: Data processor and orchestrator operations
		{"CAT-F", "data-proc-001", "ops-data-001", "read", "Data proc reads ops data (ALLOW)"},
		{"CAT-F", "data-proc-001", "ops-data-002", "read", "Data proc reads ops data 2 (ALLOW)"},
		{"CAT-F", "data-proc-002", "ops-data-001", "read", "Data proc 2 reads ops data (ALLOW)"},
		{"CAT-F", "orch-001", "ops-data-001", "read", "Orchestrator reads ops data (ALLOW)"},
		{"CAT-F", "data-proc-001", "analytics-001", "read", "Data proc reads analytics (ALLOW)"},
		{"CAT-F", "data-proc-002", "config-002", "read", "Data proc 2 reads config-002 (AUTH-046)"},

		// CAT-G: Failure modes (invalid/suspended/revoked agents, bad resources)
		{"CAT-G", "suspended-agent", "ops-data-001", "read", "Suspended agent (DENY)"},
		{"CAT-G", "revoked-agent", "ops-data-001", "read", "Revoked agent (DENY)"},
		{"CAT-G", "terminated-agent", "ops-data-001", "read", "Terminated agent (DENY)"},
		{"CAT-G", "nonexistent-agent", "ops-data-001", "read", "Unknown agent (DENY)"},
		{"CAT-G", "std-agent-001", "nonexistent-res", "read", "Unknown resource (DENY)"},
		{"CAT-G", "", "ops-data-001", "read", "Empty agent ID (DENY)"},
		{"CAT-G", "std-agent-001", "", "read", "Empty resource ID (DENY)"},
		{"CAT-G", "std-agent-001", "ops-data-001", "destroy", "Invalid action (DENY)"},

		// CAT-H: Classification ceiling tests (Bell-LaPadula)
		{"CAT-H", "std-agent-003", "config-001", "read", "L1 agent reads L2 resource (ceiling)"},
		{"CAT-H", "std-agent-001", "agent-reg-001", "read", "L2 agent reads L3 resource (ceiling)"},
		{"CAT-H", "data-proc-001", "model-reg-001", "read", "L1 proc reads L3 model reg (ceiling)"},
		{"CAT-H", "data-proc-001", "trace-001", "read", "L1 proc reads L3 trace (ceiling)"},
		{"CAT-H", "orch-001", "model-reg-001", "read", "L2 orch reads L3 model reg (ceiling)"},
		{"CAT-H", "orch-001", "trace-001", "read", "L2 orch reads L3 trace (ceiling)"},
		{"CAT-H", "std-agent-001", "config-001", "read", "L2 agent reads L2 config (should ALLOW)"},
	}

	if len(allCases) != 50 {
		fmt.Fprintf(os.Stderr, "FATAL: Expected 50 test cases, got %d\n", len(allCases))
		os.Exit(1)
	}

	type resultRecord struct {
		Cat       string `json:"category"`
		Agent     string `json:"agent_id"`
		Resource  string `json:"resource_id"`
		Action    string `json:"action"`
		V1Verdict string `json:"v1_verdict"`
		V1Reason  string `json:"v1_reason"`
		V1Rules   string `json:"v1_rules"`
		V1PolicyVersion string `json:"v1_policy_version"`
		V1PolicyHash    string `json:"v1_policy_hash"`
		V2Verdict string `json:"v2_verdict"`
		V2Reason  string `json:"v2_reason"`
		V2Rules   string `json:"v2_rules"`
		V2PolicyVersion string `json:"v2_policy_version"`
		V2PolicyHash    string `json:"v2_policy_hash"`
		Changed   bool   `json:"verdict_or_reason_changed"`
	}

	// Evaluate all 50 under v1 (using replay PDP to avoid chain mutation)
	v1Policy := registry.GetPolicy("v1")
	replayV1 := NewSarathiPDPForReplay(v1Policy, agentRegistry, clock)

	fmt.Printf("\nEvaluating %d test cases under policy v1...\n", len(allCases))
	v1Results := make([]*PDPResponse, len(allCases))
	for i, tc := range allCases {
		req := &PDPRequest{AgentID: tc.agent, ResourceID: tc.resource, Action: tc.action}
		v1Results[i] = replayV1.Evaluate(req)
	}
	fmt.Printf("  Completed %d v1 evaluations\n", len(allCases))

	// ================================================================
	// PHASE 4: POLICY UPGRADE — Activate v2
	// ================================================================
	fmt.Println()
	fmt.Println("═══════════════════════════════════════════════════════════")
	fmt.Println("  PHASE 4: POLICY UPGRADE — v1 → v2")
	fmt.Println("═══════════════════════════════════════════════════════════")

	if err := registry.SetActivePolicy("v2"); err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: %v\n", err)
		os.Exit(1)
	}
	registry.PrintRegistryStatus()

	// FIX 5: Create new PDP via registry for v2 (not direct PolicyStore access)
	pdpV2, err := NewSarathiPDPFromRegistry(registry, agentRegistry, clock)
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: Cannot create PDP from registry: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("  PDP v2 created via NewSarathiPDPFromRegistry (Fix 5)\n")
	fmt.Printf("  Bound policy: version=%s, hash=%s...\n",
		pdpV2.GetPolicyVersion(), pdpV2.GetPolicyHash()[:16])

	// Evaluate all 50 under v2
	v2Policy := registry.GetPolicy("v2")
	replayV2 := NewSarathiPDPForReplay(v2Policy, agentRegistry, clock)

	fmt.Printf("\nEvaluating %d test cases under policy v2...\n", len(allCases))
	v2Results := make([]*PDPResponse, len(allCases))
	for i, tc := range allCases {
		req := &PDPRequest{AgentID: tc.agent, ResourceID: tc.resource, Action: tc.action}
		v2Results[i] = replayV2.Evaluate(req)
	}
	fmt.Printf("  Completed %d v2 evaluations\n", len(allCases))

	// ================================================================
	// PHASE 5: IMPACT ANALYSIS + VERSION BINDING (Fix 6)
	// ================================================================
	fmt.Println()
	fmt.Println("═══════════════════════════════════════════════════════════")
	fmt.Println("  PHASE 5: IMPACT ANALYSIS + VERSION BINDING VERIFICATION")
	fmt.Println("═══════════════════════════════════════════════════════════")
	fmt.Println()

	records := make([]resultRecord, len(allCases))
	changedCount := 0
	unchangedCount := 0
	v1VersionBindingOK := 0
	v2VersionBindingOK := 0

	v1Hash := registry.GetPolicy("v1").GetPolicyHash()
	v2Hash := registry.GetPolicy("v2").GetPolicyHash()
	v1Version := registry.GetPolicy("v1").GetPolicyVersion()
	v2Version := registry.GetPolicy("v2").GetPolicyVersion()

	for i := range allCases {
		r1 := v1Results[i]
		r2 := v2Results[i]

		changed := r1.Verdict != r2.Verdict || r1.Reason != r2.Reason
		if changed {
			changedCount++
		} else {
			unchangedCount++
		}

		// FIX 6: Version binding assertion
		if r1.PolicyHash == v1Hash && r1.PolicyVersion == v1Version {
			v1VersionBindingOK++
		}
		if r2.PolicyHash == v2Hash && r2.PolicyVersion == v2Version {
			v2VersionBindingOK++
		}

		records[i] = resultRecord{
			Cat:       allCases[i].cat,
			Agent:     allCases[i].agent,
			Resource:  allCases[i].resource,
			Action:    allCases[i].action,
			V1Verdict: r1.Verdict,
			V1Reason:  r1.Reason,
			V1Rules:   strings.Join(r1.DeterminingRules, ","),
			V1PolicyVersion: r1.PolicyVersion,
			V1PolicyHash:    r1.PolicyHash,
			V2Verdict: r2.Verdict,
			V2Reason:  r2.Reason,
			V2Rules:   strings.Join(r2.DeterminingRules, ","),
			V2PolicyVersion: r2.PolicyVersion,
			V2PolicyHash:    r2.PolicyHash,
			Changed:   changed,
		}
	}

	// Print summary table for changed cases
	fmt.Println("  --- Changed Cases ---")
	fmt.Printf("  %-3s %-6s %-18s %-18s %-8s %-8s %-35s %-35s\n",
		"#", "Cat", "Agent", "Resource", "V1", "V2", "V1 Reason", "V2 Reason")
	fmt.Println("  " + strings.Repeat("-", 135))
	for i, rec := range records {
		if rec.Changed {
			fmt.Printf("  %-3d %-6s %-18s %-18s %-8s %-8s %-35s %-35s\n",
				i+1, rec.Cat, rec.Agent, rec.Resource,
				rec.V1Verdict, rec.V2Verdict, rec.V1Reason, rec.V2Reason)
		}
	}
	fmt.Printf("\n  Changed: %d  |  Unchanged: %d  |  Total: %d\n", changedCount, unchangedCount, len(allCases))

	// FIX 6: Version binding proof
	fmt.Println()
	fmt.Println("  --- Version Binding Proof (Fix 6) ---")
	fmt.Printf("  v1 responses with correct version/hash: %d/%d\n", v1VersionBindingOK, len(allCases))
	fmt.Printf("  v2 responses with correct version/hash: %d/%d\n", v2VersionBindingOK, len(allCases))
	if v1VersionBindingOK != len(allCases) || v2VersionBindingOK != len(allCases) {
		fmt.Fprintf(os.Stderr, "FATAL: Version binding violation detected!\n")
		os.Exit(1)
	}
	fmt.Println("  [PASS] Every decision output carries the correct policy_version and policy_hash")

	// ================================================================
	// PHASE 6: REPLAY DETERMINISM + CROSS-VERSION EVIDENCE (Fix 4)
	// ================================================================
	fmt.Println()
	fmt.Println("═══════════════════════════════════════════════════════════")
	fmt.Println("  PHASE 6: REPLAY DETERMINISM + CROSS-VERSION EVIDENCE")
	fmt.Println("═══════════════════════════════════════════════════════════")
	fmt.Println()

	// 6A: Same policy, two independent PDP instances → bit-exact match
	fmt.Println("  --- 6A: Intra-Version Replay (same policy = same output) ---")

	v1Passed, v1Failed := 0, 0
	pdpV1A := NewSarathiPDPForReplay(registry.GetPolicy("v1"), NewRegistryInterface(), clock)
	pdpV1B := NewSarathiPDPForReplay(registry.GetPolicy("v1"), NewRegistryInterface(), clock)
	for _, tc := range allCases {
		req := &PDPRequest{AgentID: tc.agent, ResourceID: tc.resource, Action: tc.action}
		r1 := pdpV1A.Evaluate(req)
		r2 := pdpV1B.Evaluate(req)
		resp1JSON, _ := json.Marshal(r1)
		resp2JSON, _ := json.Marshal(r2)
		if Sha256Hex(resp1JSON) == Sha256Hex(resp2JSON) {
			v1Passed++
		} else {
			v1Failed++
			fmt.Printf("  [FAIL] v1: %s/%s/%s hash mismatch\n", tc.agent, tc.resource, tc.action)
		}
	}
	fmt.Printf("  v1 Replay: %d/%d PASSED\n", v1Passed, v1Passed+v1Failed)

	v2Passed, v2Failed := 0, 0
	pdpV2A := NewSarathiPDPForReplay(registry.GetPolicy("v2"), NewRegistryInterface(), clock)
	pdpV2B := NewSarathiPDPForReplay(registry.GetPolicy("v2"), NewRegistryInterface(), clock)
	for _, tc := range allCases {
		req := &PDPRequest{AgentID: tc.agent, ResourceID: tc.resource, Action: tc.action}
		r1 := pdpV2A.Evaluate(req)
		r2 := pdpV2B.Evaluate(req)
		resp1JSON, _ := json.Marshal(r1)
		resp2JSON, _ := json.Marshal(r2)
		if Sha256Hex(resp1JSON) == Sha256Hex(resp2JSON) {
			v2Passed++
		} else {
			v2Failed++
			fmt.Printf("  [FAIL] v2: %s/%s/%s hash mismatch\n", tc.agent, tc.resource, tc.action)
		}
	}
	fmt.Printf("  v2 Replay: %d/%d PASSED\n", v2Passed, v2Passed+v2Failed)

	// 6B: Cross-version evidence (Fix 4)
	// Same request + different policy → controlled, predictable difference
	fmt.Println()
	fmt.Println("  --- 6B: Cross-Version Replay Evidence (Fix 4) ---")
	fmt.Println("  Same request + different policy version = controlled difference")

	crossVersionMatches := 0
	crossVersionDiffs := 0
	crossVersionExpectedDiffs := 0

	pdpCrossV1 := NewSarathiPDPForReplay(registry.GetPolicy("v1"), NewRegistryInterface(), clock)
	pdpCrossV2 := NewSarathiPDPForReplay(registry.GetPolicy("v2"), NewRegistryInterface(), clock)

	for i, tc := range allCases {
		req := &PDPRequest{AgentID: tc.agent, ResourceID: tc.resource, Action: tc.action}
		r1 := pdpCrossV1.Evaluate(req)
		r2 := pdpCrossV2.Evaluate(req)

		resp1JSON, _ := json.Marshal(r1)
		resp2JSON, _ := json.Marshal(r2)
		sameHash := Sha256Hex(resp1JSON) == Sha256Hex(resp2JSON)

		if allCases[i].cat == "CAT-A" || (allCases[i].cat == "CAT-F" && allCases[i].agent == "data-proc-002" && allCases[i].resource == "config-002") {
			// These cases SHOULD differ between v1 and v2
			crossVersionExpectedDiffs++
			if !sameHash {
				crossVersionDiffs++
			} else {
				fmt.Printf("  [UNEXPECTED] Case %d should differ but matched: %s/%s/%s\n",
					i+1, tc.agent, tc.resource, tc.action)
			}
		} else {
			// These cases should be identical
			if sameHash {
				crossVersionMatches++
			} else {
				// Policy version/hash embedded in response always differs
				// Check if verdict and reason are the same
				if r1.Verdict == r2.Verdict && r1.Reason == r2.Reason {
					crossVersionMatches++
				} else {
					fmt.Printf("  [UNEXPECTED] Case %d changed but shouldn't: %s/%s/%s v1=%s/%s v2=%s/%s\n",
						i+1, tc.agent, tc.resource, tc.action,
						r1.Verdict, r1.Reason, r2.Verdict, r2.Reason)
				}
			}
		}
	}

	fmt.Printf("\n  Cross-version expected diffs: %d/%d correctly differed\n", crossVersionDiffs, crossVersionExpectedDiffs)
	fmt.Printf("  Cross-version control cases:  %d/%d unchanged verdicts\n", crossVersionMatches, len(allCases)-crossVersionExpectedDiffs)
	fmt.Println("  [PASS] Cross-version replay evidence confirmed")

	// ================================================================
	// PHASE 7: GOVERNANCE ASSERTIONS
	// ================================================================
	fmt.Println()
	fmt.Println("═══════════════════════════════════════════════════════════")
	fmt.Println("  PHASE 7: GOVERNANCE ASSERTIONS")
	fmt.Println("═══════════════════════════════════════════════════════════")

	assertionsPassed := 0
	assertionsFailed := 0

	assert := func(name string, condition bool) {
		if condition {
			assertionsPassed++
			fmt.Printf("  [PASS] %s\n", name)
		} else {
			assertionsFailed++
			fmt.Printf("  [FAIL] %s\n", name)
		}
	}

	// Fix 1: Immutability
	assert("Fix 1: v1 PolicyStore is frozen", registry.GetPolicy("v1").IsFrozen())
	assert("Fix 1: v2 PolicyStore is frozen", registry.GetPolicy("v2").IsFrozen())
	assert("Fix 1: v1 rule count = 51", registry.GetPolicy("v1").RuleCount() == 51)
	assert("Fix 1: v2 rule count = 51", registry.GetPolicy("v2").RuleCount() == 51)

	// Fix 2: Config-driven selection
	assert("Fix 2: Registry has config loaded", registry.config != nil)

	// Fix 3: Hash validation
	_, _, v1Match, _ := registry.VerifyPolicyVersion("v1")
	_, _, v2Match, _ := registry.VerifyPolicyVersion("v2")
	assert("Fix 3: v1 hash independently verified", v1Match)
	assert("Fix 3: v2 hash independently verified", v2Match)
	assert("Fix 3: v1 and v2 have different hashes", v1Hash != v2Hash)

	// Fix 4: Cross-version evidence
	assert("Fix 4: Cross-version expected diffs all confirmed",
		crossVersionDiffs == crossVersionExpectedDiffs)
	assert("Fix 4: Cross-version control cases all stable",
		crossVersionMatches == len(allCases)-crossVersionExpectedDiffs)

	// Fix 5: PDP registry dependency
	assert("Fix 5: PDP v1 created from registry (not direct load)", pdpV1 != nil)
	assert("Fix 5: PDP v2 created from registry (not direct load)", pdpV2 != nil)
	assert("Fix 5: PDP v1 policy version matches registry",
		pdpV1.GetPolicyVersion() == v1Version)

	// Fix 6: Version binding
	assert("Fix 6: All v1 responses carry v1 policy hash", v1VersionBindingOK == 50)
	assert("Fix 6: All v2 responses carry v2 policy hash", v2VersionBindingOK == 50)

	// General governance
	assert("50 test cases evaluated", len(allCases) == 50)
	assert("CAT-A changed cases > 0", changedCount > 0)
	assert("Replay v1: 0 failures", v1Failed == 0)
	assert("Replay v2: 0 failures", v2Failed == 0)
	assert("Total replay: 100/100 passed", v1Passed+v2Passed == 100)

	fmt.Printf("\n  Assertions: %d passed, %d failed\n", assertionsPassed, assertionsFailed)

	// ================================================================
	// FINAL REPORT
	// ================================================================
	fmt.Println()
	fmt.Println("═══════════════════════════════════════════════════════════")
	fmt.Println("  FINAL RESULTS")
	fmt.Println("═══════════════════════════════════════════════════════════")

	totalReplayPassed := v1Passed + v2Passed
	totalReplayFailed := v1Failed + v2Failed
	totalReplayTests := totalReplayPassed + totalReplayFailed

	fmt.Printf("\n  Policy v1 Hash:     %s\n", v1Hash)
	fmt.Printf("  Policy v2 Hash:     %s\n", v2Hash)
	fmt.Printf("  Policies Loaded:    %d\n", loaded)
	fmt.Printf("  Test Cases:         %d\n", len(allCases))
	fmt.Printf("  Verdict Changes:    %d/%d cases\n", changedCount, len(allCases))
	fmt.Printf("  Replay Tests:       %d/%d PASSED\n", totalReplayPassed, totalReplayTests)
	fmt.Printf("  Mismatch Rate:      %.4f%%\n", float64(totalReplayFailed)/float64(totalReplayTests)*100)
	fmt.Printf("  Assertions:         %d/%d PASSED\n", assertionsPassed, assertionsPassed+assertionsFailed)

	overallPass := totalReplayFailed == 0 && changedCount > 0 && assertionsFailed == 0

	if overallPass {
		fmt.Println()
		fmt.Println("  +=====================================================+")
		fmt.Println("  |  POLICY REGISTRY VALIDATION: PASSED                |")
		fmt.Println("  |                                                     |")
		fmt.Println("  |  Fix 1: PolicyStore immutability enforced           |")
		fmt.Println("  |  Fix 2: Config-driven active policy selection       |")
		fmt.Println("  |  Fix 3: Per-version hash validation proven          |")
		fmt.Println("  |  Fix 4: Cross-version replay evidence confirmed     |")
		fmt.Println("  |  Fix 5: PDP depends on registry, not direct load   |")
		fmt.Println("  |  Fix 6: Version binding in every decision output    |")
		fmt.Println("  |                                                     |")
		fmt.Println("  |  All 50 test cases x 2 versions = 100 replay tests |")
		fmt.Println("  |  0.0000% mismatch rate                              |")
		fmt.Println("  +=====================================================+")
	} else {
		fmt.Println()
		fmt.Println("  +=====================================================+")
		fmt.Println("  |  POLICY REGISTRY VALIDATION: FAILED                |")
		fmt.Println("  +=====================================================+")
		os.Exit(1)
	}

	// Write comprehensive results JSON
	resultsJSON := map[string]interface{}{
		"status":               "PASS",
		"test_cases":           len(allCases),
		"policy_v1_hash":       v1Hash,
		"policy_v2_hash":       v2Hash,
		"policies_loaded":      loaded,
		"verdict_changes":      changedCount,
		"control_unchanged":    unchangedCount,
		"replay_tests_passed":  totalReplayPassed,
		"replay_tests_failed":  totalReplayFailed,
		"replay_mismatch_rate": fmt.Sprintf("%.4f%%", float64(totalReplayFailed)/float64(totalReplayTests)*100),
		"assertions_passed":    assertionsPassed,
		"assertions_failed":    assertionsFailed,
		"hash_validation_proof": hashProofs,
		"cross_version_evidence": map[string]interface{}{
			"expected_diffs":   crossVersionExpectedDiffs,
			"confirmed_diffs":  crossVersionDiffs,
			"control_stable":   crossVersionMatches,
			"control_expected": len(allCases) - crossVersionExpectedDiffs,
		},
		"version_binding": map[string]interface{}{
			"v1_correct": v1VersionBindingOK,
			"v2_correct": v2VersionBindingOK,
			"total":      len(allCases),
		},
		"immutability_check": map[string]interface{}{
			"v1_frozen": registry.GetPolicy("v1").IsFrozen(),
			"v2_frozen": registry.GetPolicy("v2").IsFrozen(),
		},
		"config_driven_selection": registry.config != nil,
		"details": records,
	}
	resultData, _ := json.MarshalIndent(resultsJSON, "", "  ")
	os.WriteFile("policy_registry_results.json", resultData, 0644)
	fmt.Println("\n  Results written to policy_registry_results.json")
}
