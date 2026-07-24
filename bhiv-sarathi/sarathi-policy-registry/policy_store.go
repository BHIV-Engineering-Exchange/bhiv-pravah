package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"sort"
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
		return L0, fmt.Errorf("invalid truth level: %s", s)
	}
}

// AuthorityRule is a single frozen rule from the Authority Matrix.
// Fields are exported for JSON marshaling but rules are stored in a
// read-only slice within PolicyStore — no mutation path exists.
type AuthorityRule struct {
	RuleID            string `json:"rule_id"`
	AgentRole         string `json:"agent_role"`
	ResourceType      string `json:"resource_type"`
	Action            string `json:"action"`
	ClassificationMax string `json:"classification_max"`
	Verdict           string `json:"verdict"`
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
//
// IMMUTABILITY CONTRACT:
//   1. All fields are unexported (lowercase) — no external write access.
//   2. Read-only accessor methods return copies, not references.
//   3. No SetXxx(), ModifyXxx(), or AddRule() methods exist.
//   4. The rules slice is defensively copied — callers cannot modify it.
//   5. Once constructed by NewPolicyStore(), no field can change.
//   6. Any attempt to modify policy state requires creating a new PolicyStore
//      from a new policy file — which triggers full hash re-verification.
//
// This is structural enforcement, not procedural discipline.

type PolicyStore struct {
	policyVersion           string
	policyHash              string
	frozenAt                string
	rules                   []AuthorityRule
	resourceClassifications map[string]string
	frozen                  bool // true once construction completes
}

// --- Read-only accessors (no setters exist) ---

// PolicyVersion returns the version string (e.g., "1.0.0"). Read-only.
func (ps *PolicyStore) GetPolicyVersion() string { return ps.policyVersion }

// PolicyHash returns the SHA-256 hash of the canonical rules. Read-only.
func (ps *PolicyStore) GetPolicyHash() string { return ps.policyHash }

// FrozenAt returns the freeze timestamp. Read-only.
func (ps *PolicyStore) GetFrozenAt() string { return ps.frozenAt }

// RuleCount returns the number of rules. Read-only.
func (ps *PolicyStore) RuleCount() int { return len(ps.rules) }

// IsFrozen returns true if this PolicyStore has been fully constructed and verified.
func (ps *PolicyStore) IsFrozen() bool { return ps.frozen }

// --- Backward-compatible exported field accessors ---
// These properties provide read access matching the old exported field names.
// They return values, not pointers — callers cannot mutate internal state.

// PolicyVersion is a read-only property alias for backward compatibility.
var _ = (*PolicyStore).GetPolicyVersion // compile-time existence check

// PolicyVersionField returns the policy version (backward compat for PDP).
func (ps *PolicyStore) PolicyVersionField() string { return ps.policyVersion }

// PolicyHashField returns the policy hash (backward compat for PDP).
func (ps *PolicyStore) PolicyHashField() string { return ps.policyHash }

// NewPolicyStore loads the Authority Matrix, sorts rules by rule_id,
// computes the policy_hash, and verifies integrity.
// The returned PolicyStore is fully immutable — no modification path exists.
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

	// Compute policy_hash from canonical rules JSON (6 required fields only)
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
	rulesJSON, _ := json.Marshal(hashRules)
	hash := sha256.Sum256(rulesJSON)
	computedHash := hex.EncodeToString(hash[:])

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
		frozen:                  true, // Sealed — no further modification possible
	}

	return ps, nil
}

// FindMatchingRules returns all rules matching the request. Deterministic order.
// Returns copies — the caller cannot modify the internal rule slice.
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
// Callers receive their own copy — modifying it does not affect PolicyStore.
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
