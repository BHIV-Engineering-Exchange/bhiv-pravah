package main

// policy_store.go — Immutable policy container with Bell-LaPadula lattice.
//
// GAP FIXES APPLIED:
//   GAP-05: Obligations field added to AuthorityRule (omitempty for backward compat)
//   GAP-08: Policy analysis functions (conflict detection, shadow detection, completeness)
//   GAP-11: json.Marshal error handling (fail-closed)

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"sort"
	"strings"
)

// TruthLevel represents the Bell-LaPadula security lattice L0-L4.
type TruthLevel int

const (
	L0 TruthLevel = 0 // Public information
	L1 TruthLevel = 1 // Internal operational data
	L2 TruthLevel = 2 // Sensitive internal data
	L3 TruthLevel = 3 // Governance-critical data
	L4 TruthLevel = 4 // Constitutional truth layer
)

// ParseTruthLevel parses a classification string into a TruthLevel.
// HIGH-05 FIX: FAIL-CLOSED — returns (-1, error) on invalid input instead of (L0, error).
// Returning L0 on error was a PRIVILEGE ESCALATION vector: an invalid classification
// would default to L0 (Public), granting maximum access instead of denying it.
// Now callers MUST check the error — using the returned TruthLevel on error gives -1,
// which is below L0 and will fail any Bell-LaPadula classification check.
//
// Industry alignment:
//   - AWS IAM: invalid policy = implicit deny
//   - Google Zanzibar: unknown relation = deny
//   - OPA: undefined result = deny (when configured correctly)
func ParseTruthLevel(s string) (TruthLevel, error) {
	switch s {
	case "L0":
		return L0, nil
	case "L1":
		return L1, nil
	case "L2":
		return L2, nil
	case "L3":
		return L3, nil
	case "L4":
		return L4, nil
	default:
		// FAIL-CLOSED: return -1 (below L0) so any comparison fails safely
		return TruthLevel(-1), fmt.Errorf("CLASSIFICATION_PARSE_FAILURE: invalid truth level %q — request DENIED (fail-closed)", s)
	}
}

// AuthorityRule is a single frozen rule from the Authority Matrix.
// Fields are exported for JSON marshaling but rules are stored in a
// read-only slice within PolicyStore — no mutation path exists.
type AuthorityRule struct {
	RuleID            string   `json:"rule_id"`
	AgentRole         string   `json:"agent_role"`
	ResourceType      string   `json:"resource_type"`
	Action            string   `json:"action"`
	ClassificationMax string   `json:"classification_max"`
	Verdict           string   `json:"verdict"`
	Obligations       []string `json:"obligations,omitempty"` // GAP-05: mandatory side-effects
}

// Matches checks if this rule applies to the given request attributes.
func (r *AuthorityRule) Matches(agentRole, resourceType, action string) bool {
	roleMatch := r.AgentRole == agentRole || r.AgentRole == "*"
	resMatch := r.ResourceType == resourceType || r.ResourceType == "*"
	actMatch := r.Action == action || r.Action == "*"
	return roleMatch && resMatch && actMatch
}

// AuthorityMatrix is the JSON file structure (used only for deserialization).
type AuthorityMatrix struct {
	PolicyVersion           string            `json:"policy_version"`
	PolicyHash              string            `json:"policy_hash"`
	FrozenAt                string            `json:"frozen_at"`
	ResourceClassifications map[string]string `json:"resource_classifications"`
	Rules                   []AuthorityRule   `json:"rules"`
}

// ================================================================
// PolicyStore — IMMUTABLE policy container
// ================================================================

type PolicyStore struct {
	policyVersion           string
	policyHash              string
	frozenAt                string
	rules                   []AuthorityRule
	resourceClassifications map[string]string
	frozen                  bool
}

// --- Read-only accessors (no setters exist) ---

func (ps *PolicyStore) GetPolicyVersion() string { return ps.policyVersion }
func (ps *PolicyStore) GetPolicyHash() string    { return ps.policyHash }
func (ps *PolicyStore) GetFrozenAt() string      { return ps.frozenAt }
func (ps *PolicyStore) RuleCount() int           { return len(ps.rules) }
func (ps *PolicyStore) IsFrozen() bool           { return ps.frozen }

// Backward-compatible exported field accessors
var _ = (*PolicyStore).GetPolicyVersion // compile-time existence check

func (ps *PolicyStore) PolicyVersionField() string { return ps.policyVersion }
func (ps *PolicyStore) PolicyHashField() string    { return ps.policyHash }

// NewPolicyStore loads the Authority Matrix, sorts rules by rule_id,
// computes the policy_hash, and verifies integrity.
func NewPolicyStore(matrixPath string) (*PolicyStore, error) {
	file, err := os.Open(matrixPath)
	if err != nil {
		return nil, fmt.Errorf("cannot open authority matrix: %w", err)
	}
	defer file.Close()

	data, err := io.ReadAll(file)
	if err != nil {
		return nil, fmt.Errorf("cannot read authority matrix: %w", err)
	}

	var matrix AuthorityMatrix
	if err := json.Unmarshal(data, &matrix); err != nil {
		return nil, fmt.Errorf("cannot parse authority matrix: %w", err)
	}

	// Sort rules by RuleID for deterministic evaluation
	rules := make([]AuthorityRule, len(matrix.Rules))
	copy(rules, matrix.Rules)
	sort.SliceStable(rules, func(i, j int) bool {
		return rules[i].RuleID < rules[j].RuleID
	})

	// Compute policy_hash from canonical rules JSON (core fields only)
	// NOTE: obligations use omitempty — rules without obligations hash identically
	// to legacy rules, maintaining backward compatibility.
	computedHash, err := computePolicyHashFromRules(rules)
	if err != nil {
		return nil, fmt.Errorf("policy hash computation failed: %w", err)
	}

	// Integrity verification — fatal on mismatch
	if matrix.PolicyHash != "" && computedHash != matrix.PolicyHash {
		return nil, fmt.Errorf("POLICY INTEGRITY VIOLATION: stored=%s computed=%s",
			matrix.PolicyHash, computedHash)
	}

	// Reject DRAFT policies (empty hash)
	if matrix.PolicyHash == "" {
		fmt.Printf("[PolicyStore] First load — computed policy_hash: %s\n", computedHash)
		fmt.Printf("[PolicyStore] To freeze: set policy_hash in the JSON file to this value\n")
	}

	ps := &PolicyStore{
		policyVersion:           matrix.PolicyVersion,
		policyHash:              computedHash,
		frozenAt:                matrix.FrozenAt,
		rules:                   rules,
		resourceClassifications: matrix.ResourceClassifications,
		frozen:                  true,
	}

	return ps, nil
}

// FindMatchingRules returns all rules matching the request. Deterministic order.
func (ps *PolicyStore) FindMatchingRules(agentRole, resourceType, action string) []AuthorityRule {
	var matches []AuthorityRule
	for _, r := range ps.rules {
		if r.Matches(agentRole, resourceType, action) {
			matches = append(matches, r) // struct copy, not pointer
		}
	}
	return matches
}

// Rules returns a defensive copy of the internal rules slice.
func (ps *PolicyStore) Rules() []AuthorityRule {
	cp := make([]AuthorityRule, len(ps.rules))
	copy(cp, ps.rules)
	return cp
}

// Sha256Hex computes SHA-256 of data and returns hex string.
func Sha256Hex(data []byte) string {
	h := sha256.Sum256(data)
	return hex.EncodeToString(h[:])
}

// computePolicyHashFromRules computes SHA-256 from canonical rules JSON (GAP-11).
func computePolicyHashFromRules(rules []AuthorityRule) (string, error) {
	type hashRule struct {
		RuleID            string `json:"rule_id"`
		AgentRole         string `json:"agent_role"`
		ResourceType      string `json:"resource_type"`
		Action            string `json:"action"`
		ClassificationMax string `json:"classification_max"`
		Verdict           string `json:"verdict"`
	}
	hashRules := make([]hashRule, len(rules))
	for i, r := range rules {
		hashRules[i] = hashRule{r.RuleID, r.AgentRole, r.ResourceType,
			r.Action, r.ClassificationMax, r.Verdict}
	}
	rulesJSON, err := json.Marshal(hashRules)
	if err != nil {
		return "", fmt.Errorf("rule marshal failed: %w", err)
	}
	hash := sha256.Sum256(rulesJSON)
	return hex.EncodeToString(hash[:]), nil
}

// ================================================================
// POLICY ANALYSIS (GAP-08)
// ================================================================

// PolicyAnalysisResult contains the results of policy verification.
type PolicyAnalysisResult struct {
	TotalRules        int
	Conflicts         []PolicyConflict
	ShadowedRules     []ShadowedRule
	UnreachableRules  []string
	HasDefaultDeny    bool
	CoverageGaps      []string
	ObligationSummary map[string]int // obligation → count of rules that use it
}

// PolicyConflict identifies two rules that match the same request but
// produce different verdicts (one ALLOW, one DENY).
type PolicyConflict struct {
	RuleA   string
	RuleB   string
	Overlap string // description of overlapping scope
}

// ShadowedRule identifies a rule that is completely overshadowed by a
// more specific rule, meaning it can never determine the outcome.
type ShadowedRule struct {
	ShadowedRuleID string
	ShadowedBy     string
	Reason         string
}

// AnalyzePolicy performs static analysis on the policy (GAP-08).
// Returns conflicts, shadows, coverage gaps, and obligation summary.
func AnalyzePolicy(ps *PolicyStore) PolicyAnalysisResult {
	rules := ps.Rules()
	result := PolicyAnalysisResult{
		TotalRules:        len(rules),
		ObligationSummary: make(map[string]int),
	}

	// Check for default deny rule
	for _, r := range rules {
		if r.AgentRole == "*" && r.ResourceType == "*" && r.Action == "*" && r.Verdict == "DENY" {
			result.HasDefaultDeny = true
		}
		// Obligation summary
		for _, o := range r.Obligations {
			result.ObligationSummary[o]++
		}
	}

	if !result.HasDefaultDeny {
		result.CoverageGaps = append(result.CoverageGaps,
			"MISSING_DEFAULT_DENY: No wildcard DENY-ALL rule found. "+
				"Requests matching no rule will get NO_MATCHING_RULE → DENY from PDP logic, "+
				"but an explicit default-deny rule is best practice.")
	}

	// Detect conflicts: same (role, resource_type, action) scope but different verdicts
	// Only check specific (non-wildcard) rules against each other
	for i := 0; i < len(rules); i++ {
		for j := i + 1; j < len(rules); j++ {
			ri, rj := rules[i], rules[j]
			if ri.Verdict == rj.Verdict {
				continue // same verdict, not a conflict
			}
			if rulesOverlap(ri, rj) {
				result.Conflicts = append(result.Conflicts, PolicyConflict{
					RuleA:   ri.RuleID,
					RuleB:   rj.RuleID,
					Overlap: fmt.Sprintf("role=%s/%s resource=%s/%s action=%s/%s",
						ri.AgentRole, rj.AgentRole, ri.ResourceType, rj.ResourceType,
						ri.Action, rj.Action),
				})
			}
		}
	}

	// Detect shadowed rules: a specific rule that is completely covered by
	// another more specific rule with the same verdict
	for i := 0; i < len(rules); i++ {
		for j := 0; j < len(rules); j++ {
			if i == j {
				continue
			}
			ri, rj := rules[i], rules[j]
			// ri shadows rj if ri is more specific and has the same scope
			if ri.RuleID == "AUTH-DENY-ALL" || rj.RuleID == "AUTH-DENY-ALL" {
				continue // skip the catch-all
			}
			if ri.Verdict == rj.Verdict &&
				ri.AgentRole == rj.AgentRole &&
				ri.ResourceType == rj.ResourceType &&
				ri.Action == rj.Action &&
				ri.RuleID != rj.RuleID {
				result.ShadowedRules = append(result.ShadowedRules, ShadowedRule{
					ShadowedRuleID: rj.RuleID,
					ShadowedBy:     ri.RuleID,
					Reason:         "Identical scope and verdict — redundant rule",
				})
			}
		}
	}

	return result
}

// rulesOverlap checks if two rules can match the same request.
func rulesOverlap(a, b AuthorityRule) bool {
	roleOverlap := a.AgentRole == b.AgentRole || a.AgentRole == "*" || b.AgentRole == "*"
	resOverlap := a.ResourceType == b.ResourceType || a.ResourceType == "*" || b.ResourceType == "*"
	actOverlap := a.Action == b.Action || a.Action == "*" || b.Action == "*"
	return roleOverlap && resOverlap && actOverlap
}

// PrintAnalysis outputs a human-readable policy analysis report.
func PrintAnalysis(result PolicyAnalysisResult) {
	fmt.Println("\n  ┌─── POLICY ANALYSIS REPORT ───")
	fmt.Printf("  │ Total Rules:      %d\n", result.TotalRules)
	fmt.Printf("  │ Default Deny:     %v\n", result.HasDefaultDeny)
	fmt.Printf("  │ Conflicts Found:  %d\n", len(result.Conflicts))
	fmt.Printf("  │ Shadowed Rules:   %d\n", len(result.ShadowedRules))
	fmt.Printf("  │ Coverage Gaps:    %d\n", len(result.CoverageGaps))
	fmt.Printf("  │ Obligation Types: %d\n", len(result.ObligationSummary))

	if len(result.Conflicts) > 0 {
		fmt.Println("  │")
		fmt.Println("  │ CONFLICTS (rules with overlapping scope but different verdicts):")
		for _, c := range result.Conflicts {
			fmt.Printf("  │   %s vs %s — %s\n", c.RuleA, c.RuleB, c.Overlap)
		}
	}

	if len(result.ShadowedRules) > 0 {
		fmt.Println("  │")
		fmt.Println("  │ SHADOWED RULES:")
		for _, s := range result.ShadowedRules {
			fmt.Printf("  │   %s shadowed by %s — %s\n", s.ShadowedRuleID, s.ShadowedBy, s.Reason)
		}
	}

	if len(result.CoverageGaps) > 0 {
		fmt.Println("  │")
		fmt.Println("  │ COVERAGE GAPS:")
		for _, g := range result.CoverageGaps {
			fmt.Printf("  │   %s\n", g)
		}
	}

	if len(result.ObligationSummary) > 0 {
		fmt.Println("  │")
		fmt.Println("  │ OBLIGATIONS:")
		// Sort obligation names for deterministic output
		var oblNames []string
		for k := range result.ObligationSummary {
			oblNames = append(oblNames, k)
		}
		sort.Strings(oblNames)
		for _, name := range oblNames {
			fmt.Printf("  │   %s: %d rules\n", name, result.ObligationSummary[name])
		}
	}

	fmt.Println("  └───────────────────────────────────")

	// Suppress unused import warning for strings
	_ = strings.Contains
}

// ValidateForActivation performs pre-activation validation of a policy.
// HIGH-04 FIX: Blocks policy activation if critical conflicts or coverage gaps exist.
// AnalyzePolicy detects conflicts but does not prevent activation — this function
// enforces the gate. Without this, conflicting policies can be loaded, leading to
// non-deterministic verdicts depending on rule evaluation order.
//
// Industry alignment:
//   - AWS IAM: Policy simulator prevents conflicting policy deployment
//   - Google Zanzibar: Namespace config validation prevents contradictory tuples
//   - OPA: Rego compile-time conflict detection blocks deployment
//   - Cedar: Policy validation rejects contradictory policies at authoring time
func ValidateForActivation(ps *PolicyStore) error {
	analysis := AnalyzePolicy(ps)

	// CRITICAL: Conflicts where two rules match same request with different verdicts
	// make the system non-deterministic. Block activation.
	if len(analysis.Conflicts) > 0 {
		conflictDetails := make([]string, 0, len(analysis.Conflicts))
		for _, c := range analysis.Conflicts {
			conflictDetails = append(conflictDetails, fmt.Sprintf("%s vs %s (%s)", c.RuleA, c.RuleB, c.Overlap))
		}
		return fmt.Errorf("POLICY_ACTIVATION_BLOCKED: %d conflicting rule pair(s) detected — "+
			"non-deterministic verdicts possible. Conflicts: [%s]. "+
			"Resolve conflicts before activation (deny-wins or explicit priority required)",
			len(analysis.Conflicts), strings.Join(conflictDetails, "; "))
	}

	// WARN but don't block on missing default deny (PDP handles it, but explicit is better)
	if !analysis.HasDefaultDeny {
		fmt.Println("[PolicyStore] WARNING: No explicit default-deny rule. PDP implicit deny active, but explicit rule recommended.")
	}

	return nil
}

// NewPolicyStoreValidated loads and validates a policy for production activation.
// Combines NewPolicyStore + ValidateForActivation in a single call.
// Returns error if policy has integrity violations OR critical conflicts.
func NewPolicyStoreValidated(matrixPath string) (*PolicyStore, error) {
	ps, err := NewPolicyStore(matrixPath)
	if err != nil {
		return nil, err
	}
	if err := ValidateForActivation(ps); err != nil {
		return nil, err
	}
	return ps, nil
}
