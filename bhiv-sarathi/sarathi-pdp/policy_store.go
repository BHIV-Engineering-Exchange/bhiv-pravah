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

// AuthorityMatrix is the JSON file structure.
type AuthorityMatrix struct {
	PolicyVersion           string            `json:"policy_version"`
	PolicyHash              string            `json:"policy_hash"`
	FrozenAt                string            `json:"frozen_at"`
	ResourceClassifications map[string]string `json:"resource_classifications"`
	Rules                   []AuthorityRule   `json:"rules"`
}

// PolicyStore loads and freezes the Authority Matrix.
// Immutable at runtime. No silent mutation.
type PolicyStore struct {
	PolicyVersion           string
	PolicyHash              string
	FrozenAt                string
	Rules                   []AuthorityRule
	ResourceClassifications map[string]string
}

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

	// Compute policy_hash from canonical rules JSON (6 required fields only)
	type hashRule struct {
		RuleID            string `json:"rule_id"`
		AgentRole         string `json:"agent_role"`
		ResourceType      string `json:"resource_type"`
		Action            string `json:"action"`
		ClassificationMax string `json:"classification_max"`
		Verdict           string `json:"verdict"`
	}
	hashRules := make([]hashRule, len(matrix.Rules))
	for i, r := range matrix.Rules {
		hashRules[i] = hashRule{r.RuleID, r.AgentRole, r.ResourceType,
			r.Action, r.ClassificationMax, r.Verdict}
	}
	rulesJSON, _ := json.Marshal(hashRules)
	hash := sha256.Sum256(rulesJSON)
	computedHash := hex.EncodeToString(hash[:])

	// Integrity verification
	if matrix.PolicyHash != "" && computedHash != matrix.PolicyHash {
		return nil, fmt.Errorf("POLICY INTEGRITY VIOLATION: stored=%s computed=%s",
			matrix.PolicyHash, computedHash)
	}

	// If hash was empty, this is first load — print computed hash for freezing
	if matrix.PolicyHash == "" {
		fmt.Printf("[PolicyStore] First load — computed policy_hash: %s\n", computedHash)
		fmt.Printf("[PolicyStore] To freeze: set policy_hash in authority_matrix_v1.json to this value\n")
	}

	return &PolicyStore{
		PolicyVersion:           matrix.PolicyVersion,
		PolicyHash:              computedHash,
		FrozenAt:                matrix.FrozenAt,
		Rules:                   rules,
		ResourceClassifications: matrix.ResourceClassifications,
	}, nil
}

// FindMatchingRules returns all rules matching the request. Deterministic order.
func (ps *PolicyStore) FindMatchingRules(agentRole, resourceType, action string) []AuthorityRule {
	var matches []AuthorityRule
	for _, r := range ps.Rules {
		if r.Matches(agentRole, resourceType, action) {
			matches = append(matches, r)
		}
	}
	return matches
}

// Sha256Hex computes SHA-256 of data and returns hex string.
func Sha256Hex(data []byte) string {
	h := sha256.Sum256(data)
	return hex.EncodeToString(h[:])
}
