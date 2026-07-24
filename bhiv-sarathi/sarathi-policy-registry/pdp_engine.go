package main

// pdp_engine.go contains all Sarathi PDP types and evaluation logic.
// No main() function here — this is shared by sarathi_policy_registry_main.go.
//
// IMMUTABILITY CONTRACT:
//   - policyStore is unexported — external code cannot replace it.
//   - No SetPolicyStore() or SwapPolicy() methods exist.
//   - The only way to change the active policy is to create a new PDP instance
//     via the PolicyRegistry.
//   - Read-only accessors GetPolicyVersion() and GetPolicyHash() are provided.

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/google/uuid"
)

// ================================================================
// PDP REQUEST & RESPONSE
// ================================================================

type PDPRequest struct {
	AgentID    string `json:"agent_id"`
	ResourceID string `json:"resource_id"`
	Action     string `json:"action"`
}

type PDPResponse struct {
	DecisionID          string   `json:"decision_id"`
	Verdict             string   `json:"verdict"`
	PolicyVersion       string   `json:"policy_version"`
	PolicyHash          string   `json:"policy_hash"`
	DeterminingRules    []string `json:"determining_rules"`
	TruthClassification string   `json:"truth_classification"`
	RequestHash         string   `json:"request_hash"`
	Timestamp           string   `json:"timestamp"`
	Reason              string   `json:"reason"`
	AgentRole           string   `json:"agent_role"`
	ResourceType        string   `json:"resource_type"`
	StageReached        int      `json:"stage_reached"`
}

// ================================================================
// DECISION TRACE — Hash-chained, append-only
// ================================================================

type DecisionTrace struct {
	DecisionID          string   `json:"decision_id"`
	PolicyHash          string   `json:"policy_hash"`
	PolicyVersion       string   `json:"policy_version"`
	RequestHash         string   `json:"request_hash"`
	Verdict             string   `json:"verdict"`
	DeterminingRules    []string `json:"determining_rules"`
	TruthClassification string   `json:"truth_classification"`
	Reason              string   `json:"reason"`
	Timestamp           string   `json:"timestamp"`
	AgentID             string   `json:"agent_id"`
	ResourceID          string   `json:"resource_id"`
	Action              string   `json:"action"`
	PrevTraceHash       string   `json:"prev_trace_hash"`
	TraceHash           string   `json:"trace_hash"`
}

type DecisionTraceStore struct {
	Traces     []DecisionTrace
	prevHash   string
	ReplayMode bool
}

func NewDecisionTraceStore() *DecisionTraceStore {
	return &DecisionTraceStore{prevHash: "GENESIS"}
}

// LoadExistingChain reads the trace file and resumes the hash chain.
func (dts *DecisionTraceStore) LoadExistingChain(filename string) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return // File doesn't exist, start fresh with GENESIS
	}
	var existing []DecisionTrace
	if err := json.Unmarshal(data, &existing); err != nil {
		fmt.Printf("[TraceStore] WARNING: Could not parse existing trace file, starting fresh\n")
		return
	}
	dts.Traces = existing
	if len(existing) > 0 {
		dts.prevHash = existing[len(existing)-1].TraceHash
		fmt.Printf("[TraceStore] Loaded %d existing trace entries, chain continues\n", len(existing))
	}
}

// Emit creates a new hash-chained trace entry.
// When ReplayMode is true, traces are stored in memory only — no persistent chain mutation.
func (dts *DecisionTraceStore) Emit(resp *PDPResponse, req *PDPRequest) DecisionTrace {
	trace := DecisionTrace{
		DecisionID:          resp.DecisionID,
		PolicyHash:          resp.PolicyHash,
		PolicyVersion:       resp.PolicyVersion,
		RequestHash:         resp.RequestHash,
		Verdict:             resp.Verdict,
		DeterminingRules:    resp.DeterminingRules,
		TruthClassification: resp.TruthClassification,
		Reason:              resp.Reason,
		Timestamp:           resp.Timestamp,
		AgentID:             req.AgentID,
		ResourceID:          req.ResourceID,
		Action:              req.Action,
		PrevTraceHash:       dts.prevHash,
	}
	traceJSON, _ := json.Marshal(trace)
	trace.TraceHash = Sha256Hex(traceJSON)

	if !dts.ReplayMode {
		// Production mode: chain to persistent store
		dts.prevHash = trace.TraceHash
		dts.Traces = append(dts.Traces, trace)
	}
	// Replay mode: trace is returned but not appended to the persistent chain
	return trace
}

// WriteToFile persists all traces (appended from previous runs).
func (dts *DecisionTraceStore) WriteToFile(filename string) error {
	data, _ := json.MarshalIndent(dts.Traces, "", "  ")
	return os.WriteFile(filename, data, 0644)
}

// VerifyChain recomputes every trace_hash and validates prev_trace_hash linkage.
// Returns an error on integrity violation instead of calling os.Exit(1).
// This is a governance-grade design: callers decide how to handle violations.
func (dts *DecisionTraceStore) VerifyChain() error {
	expectedPrev := "GENESIS"
	for i, trace := range dts.Traces {
		if trace.PrevTraceHash != expectedPrev {
			return fmt.Errorf(
				"TRACE CHAIN INTEGRITY VIOLATION at index %d: expected prev_trace_hash=%s, got=%s",
				i, expectedPrev, trace.PrevTraceHash)
		}
		// Recompute hash: marshal the trace without its trace_hash field
		verify := trace
		verify.TraceHash = ""
		verifyJSON, _ := json.Marshal(verify)
		recomputed := Sha256Hex(verifyJSON)
		if trace.TraceHash != recomputed {
			return fmt.Errorf(
				"TRACE HASH INTEGRITY VIOLATION at index %d: stored=%s, recomputed=%s",
				i, trace.TraceHash, recomputed)
		}
		expectedPrev = trace.TraceHash
	}
	return nil
}

// ================================================================
// SARATHI PDP CORE — 5-Stage Deterministic Pipeline
// ================================================================
//
// IMMUTABILITY CONTRACT:
//   - policyStore is unexported — no external mutation path.
//   - No SetPolicyStore(), SwapPolicy(), or ReloadPolicy() methods exist.
//   - The only way to change the active policy is to create a NEW PDP
//     instance via NewSarathiPDPFromRegistry() or NewSarathiPDPForReplay().
//   - Read-only accessors GetPolicyVersion() and GetPolicyHash() are provided.

type SarathiPDP struct {
	policyStore *PolicyStore        // unexported — immutable after construction
	Registry    *RegistryInterface
	TraceStore  *DecisionTraceStore
	Clock       Clock
	ReplayMode  bool
}

// --- Read-only accessors for policy metadata ---

// GetPolicyVersion returns the policy version bound to this PDP instance.
func (pdp *SarathiPDP) GetPolicyVersion() string {
	return pdp.policyStore.GetPolicyVersion()
}

// GetPolicyHash returns the SHA-256 hash of the policy bound to this PDP instance.
func (pdp *SarathiPDP) GetPolicyHash() string {
	return pdp.policyStore.GetPolicyHash()
}

// GetPolicyStore returns the underlying PolicyStore (read-only — PolicyStore itself is immutable).
func (pdp *SarathiPDP) GetPolicyStore() *PolicyStore {
	return pdp.policyStore
}

// NewSarathiPDPFromRegistry creates a PDP bound to the registry's active policy.
// This is the ONLY production constructor — it ensures:
//   1. The PDP always uses a registry-managed, hash-verified policy.
//   2. No direct PolicyStore file loading bypasses the registry.
//   3. The active policy must be frozen (governance invariant).
//
// Returns error if:
//   - No active policy is set in the registry
//   - The active policy is not frozen
func NewSarathiPDPFromRegistry(registry *PolicyRegistry, agentReg *RegistryInterface, clock Clock) (*SarathiPDP, error) {
	ps := registry.GetActivePolicy()
	if ps == nil {
		return nil, fmt.Errorf("no active policy in registry — cannot create PDP")
	}
	if !ps.IsFrozen() {
		return nil, fmt.Errorf("active policy is not frozen — governance violation")
	}
	ts := NewDecisionTraceStore()
	ts.LoadExistingChain("decision_trace.json")
	return &SarathiPDP{policyStore: ps, Registry: agentReg, TraceStore: ts, Clock: clock}, nil
}

// NewSarathiPDPForReplay creates a PDP for replay verification.
// This constructor is used ONLY by the replay harness:
//   - It accepts a specific PolicyStore (for historical version replay)
//   - It sets ReplayMode=true (traces are not persisted to chain)
//   - It does NOT load existing chain (clean evaluation)
//
// This is separate from NewSarathiPDPFromRegistry to maintain a clear
// boundary between production and verification paths.
func NewSarathiPDPForReplay(ps *PolicyStore, reg *RegistryInterface, clock Clock) *SarathiPDP {
	ts := NewDecisionTraceStore()
	ts.ReplayMode = true
	return &SarathiPDP{policyStore: ps, Registry: reg, TraceStore: ts, Clock: clock, ReplayMode: true}
}

// Deprecated: NewSarathiPDP loads traces from file and creates a PDP.
// Use NewSarathiPDPFromRegistry for production, NewSarathiPDPForReplay for testing.
// This constructor is retained ONLY for backward compatibility during migration.
func NewSarathiPDP(ps *PolicyStore, reg *RegistryInterface, clock Clock) *SarathiPDP {
	ts := NewDecisionTraceStore()
	ts.LoadExistingChain("decision_trace.json")
	return &SarathiPDP{policyStore: ps, Registry: reg, TraceStore: ts, Clock: clock}
}

// Deprecated: NewSarathiPDPFresh creates a PDP without loading existing traces.
// Use NewSarathiPDPForReplay instead.
// This constructor is retained ONLY for backward compatibility during migration.
func NewSarathiPDPFresh(ps *PolicyStore, reg *RegistryInterface, clock Clock, replayMode bool) *SarathiPDP {
	ts := NewDecisionTraceStore()
	ts.ReplayMode = replayMode
	return &SarathiPDP{policyStore: ps, Registry: reg, TraceStore: ts, Clock: clock, ReplayMode: replayMode}
}

// Evaluate is the main PDP entry point: Evaluate(request) -> PDPResponse
// Every response is stamped with the exact policy_version and policy_hash
// from the bound PolicyStore — this is the version binding guarantee.
func (pdp *SarathiPDP) Evaluate(req *PDPRequest) *PDPResponse {
	reqJSON, _ := json.Marshal(req)
	requestHash := Sha256Hex(reqJSON)
	decisionID := uuid.NewSHA1(uuid.NameSpaceOID,
		[]byte(requestHash+pdp.policyStore.GetPolicyHash())).String()
	timestamp := pdp.Clock.NowUTC().Format("2006-01-02T15:04:05.000000Z")

	emit := func(verdict, reason string, rules []string,
		truthClass, agentRole, resType string, stage int) *PDPResponse {
		if rules == nil {
			rules = []string{}
		}
		resp := &PDPResponse{
			DecisionID: decisionID, Verdict: verdict,
			PolicyVersion: pdp.policyStore.GetPolicyVersion(),
			PolicyHash:    pdp.policyStore.GetPolicyHash(),
			DeterminingRules: rules, TruthClassification: truthClass,
			RequestHash: requestHash, Timestamp: timestamp,
			Reason: reason, AgentRole: agentRole,
			ResourceType: resType, StageReached: stage,
		}
		pdp.TraceStore.Emit(resp, req)
		return resp
	}

	// STAGE 1: REQUEST VALIDATION
	if req.AgentID == "" {
		return emit("DENY", "INVALID_AGENT_ID", nil, "UNKNOWN", "UNKNOWN", "UNKNOWN", 1)
	}
	if req.ResourceID == "" {
		return emit("DENY", "INVALID_RESOURCE_ID", nil, "UNKNOWN", "UNKNOWN", "UNKNOWN", 1)
	}
	validActions := map[string]bool{"read": true, "write": true, "delete": true, "execute": true}
	if !validActions[req.Action] {
		return emit("DENY", "INVALID_ACTION", nil, "UNKNOWN", "UNKNOWN", "UNKNOWN", 1)
	}

	// STAGE 2: REGISTRY LOOKUP
	agent := pdp.Registry.GetAgent(req.AgentID)
	if agent == nil {
		return emit("DENY", "AGENT_NOT_FOUND", nil, "UNKNOWN", "UNKNOWN", "UNKNOWN", 2)
	}
	if agent.Status != "ACTIVE" {
		return emit("DENY", "AGENT_"+agent.Status, nil, "UNKNOWN", agent.AgentRole, "UNKNOWN", 2)
	}
	resource := pdp.Registry.GetResource(req.ResourceID)
	if resource == nil {
		return emit("DENY", "RESOURCE_NOT_FOUND", nil, "UNKNOWN", agent.AgentRole, "UNKNOWN", 2)
	}

	// STAGE 3: POLICY EVALUATION
	matchingRules := pdp.policyStore.FindMatchingRules(
		agent.AgentRole, resource.ResourceType, req.Action)

	// STAGE 4: AUTHORITY DECISION
	if len(matchingRules) == 0 {
		return emit("DENY", "NO_MATCHING_RULE", []string{"AUTH-DENY-ALL"},
			resource.Classification, agent.AgentRole, resource.ResourceType, 4)
	}

	var specific, wildcards []AuthorityRule
	for _, r := range matchingRules {
		if r.AgentRole != "*" && r.ResourceType != "*" && r.Action != "*" {
			specific = append(specific, r)
		} else {
			wildcards = append(wildcards, r)
		}
	}
	evalRules := specific
	if len(evalRules) == 0 {
		evalRules = wildcards
	}

	var denyRules, allowRules []AuthorityRule
	for _, r := range evalRules {
		if r.Verdict == "DENY" {
			denyRules = append(denyRules, r)
		} else if r.Verdict == "ALLOW" {
			allowRules = append(allowRules, r)
		}
	}

	if len(denyRules) > 0 {
		return emit("DENY", "EXPLICIT_DENY", extractIDs(denyRules),
			resource.Classification, agent.AgentRole, resource.ResourceType, 5)
	}
	if len(allowRules) == 0 {
		return emit("DENY", "NO_ALLOW_RULE", []string{"AUTH-DENY-ALL"},
			resource.Classification, agent.AgentRole, resource.ResourceType, 4)
	}

	// Bell-LaPadula classification ceiling
	agentClear, _ := ParseTruthLevel(agent.ClassificationMax)
	resLevel, _ := ParseTruthLevel(resource.Classification)
	if agentClear < resLevel {
		return emit("DENY", "CLASSIFICATION_CEILING_EXCEEDED", extractIDs(allowRules),
			resource.Classification, agent.AgentRole, resource.ResourceType, 5)
	}
	for _, rule := range allowRules {
		ruleCeil, _ := ParseTruthLevel(rule.ClassificationMax)
		if ruleCeil < resLevel {
			return emit("DENY", "RULE_CLASSIFICATION_CEILING_EXCEEDED",
				[]string{rule.RuleID},
				resource.Classification, agent.AgentRole, resource.ResourceType, 5)
		}
	}

	// STAGE 5: ALLOW
	return emit("ALLOW", "EXPLICIT_ALLOW", extractIDs(allowRules),
		resource.Classification, agent.AgentRole, resource.ResourceType, 5)
}

func extractIDs(rules []AuthorityRule) []string {
	ids := make([]string, len(rules))
	for i, r := range rules {
		ids[i] = r.RuleID
	}
	sort.Strings(ids)
	return ids
}
