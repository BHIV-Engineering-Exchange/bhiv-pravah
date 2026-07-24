package main

// pdp_engine.go contains all Sarathi PDP types and evaluation logic.
//
// IMMUTABILITY CONTRACT:
//   - policyStore is unexported — external code cannot replace it.
//   - No SetPolicyStore() or SwapPolicy() methods exist.
//   - The only way to change the active policy is to create a new PDP instance
//     via the PolicyRegistry.
//   - Read-only accessors GetPolicyVersion() and GetPolicyHash() are provided.
//
// GAP FIXES APPLIED:
//   GAP-05: Obligations field added to PDPResponse + collection from rules
//   GAP-11: json.Marshal error handling (fail-closed)
//   GAP-13: Deprecated constructors removed (NewSarathiPDP, NewSarathiPDPFresh)

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
	Obligations         []string `json:"obligations"` // GAP-05: mandatory side-effects
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
	// GAP-11: handle marshal error
	traceJSON, err := json.Marshal(trace)
	if err != nil {
		trace.TraceHash = fmt.Sprintf("TRACE_MARSHAL_ERROR:%v", err)
	} else {
		trace.TraceHash = Sha256Hex(traceJSON)
	}

	if !dts.ReplayMode {
		dts.prevHash = trace.TraceHash
		dts.Traces = append(dts.Traces, trace)
	}
	return trace
}

// WriteToFile persists all traces.
func (dts *DecisionTraceStore) WriteToFile(filename string) error {
	data, err := json.MarshalIndent(dts.Traces, "", "  ")
	if err != nil {
		return fmt.Errorf("trace marshal failed: %w", err)
	}
	return os.WriteFile(filename, data, 0644)
}

// VerifyChain recomputes every trace_hash and validates prev_trace_hash linkage.
func (dts *DecisionTraceStore) VerifyChain() error {
	expectedPrev := "GENESIS"
	for i, trace := range dts.Traces {
		if trace.PrevTraceHash != expectedPrev {
			return fmt.Errorf(
				"TRACE CHAIN INTEGRITY VIOLATION at index %d: expected prev_trace_hash=%s, got=%s",
				i, expectedPrev, trace.PrevTraceHash)
		}
		verify := trace
		verify.TraceHash = ""
		verifyJSON, err := json.Marshal(verify)
		if err != nil {
			return fmt.Errorf("TRACE MARSHAL ERROR at index %d: %v", i, err)
		}
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

type SarathiPDP struct {
	policyStore *PolicyStore
	Registry    *RegistryInterface
	TraceStore  *DecisionTraceStore
	Clock       Clock
	ReplayMode  bool
}

// --- Read-only accessors for policy metadata ---

func (pdp *SarathiPDP) GetPolicyVersion() string {
	return pdp.policyStore.GetPolicyVersion()
}

func (pdp *SarathiPDP) GetPolicyHash() string {
	return pdp.policyStore.GetPolicyHash()
}

func (pdp *SarathiPDP) GetPolicyStore() *PolicyStore {
	return pdp.policyStore
}

// NewSarathiPDPFromRegistry creates a PDP bound to the registry's active policy.
// This is the ONLY production constructor.
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
func NewSarathiPDPForReplay(ps *PolicyStore, reg *RegistryInterface, clock Clock) *SarathiPDP {
	ts := NewDecisionTraceStore()
	ts.ReplayMode = true
	return &SarathiPDP{policyStore: ps, Registry: reg, TraceStore: ts, Clock: clock, ReplayMode: true}
}

// GAP-13: Deprecated constructors NewSarathiPDP and NewSarathiPDPFresh have been
// REMOVED. They bypassed the registry governance path, allowing direct file-based
// policy loading without registry validation. All production code MUST use
// NewSarathiPDPFromRegistry. Replay code MUST use NewSarathiPDPForReplay.

// Evaluate is the main PDP entry point: Evaluate(request) -> PDPResponse
func (pdp *SarathiPDP) Evaluate(req *PDPRequest) *PDPResponse {
	// GAP-11: handle marshal error
	reqJSON, err := json.Marshal(req)
	if err != nil {
		return &PDPResponse{
			DecisionID:  uuid.New().String(),
			Verdict:     "DENY",
			Reason:      fmt.Sprintf("REQUEST_MARSHAL_ERROR: %v", err),
			RequestHash: fmt.Sprintf("MARSHAL_ERROR:%v", err),
			Obligations: []string{},
		}
	}
	requestHash := Sha256Hex(reqJSON)
	decisionID := uuid.NewSHA1(uuid.NameSpaceOID,
		[]byte(requestHash+pdp.policyStore.GetPolicyHash())).String()
	timestamp := pdp.Clock.NowUTC().Format("2006-01-02T15:04:05.000000Z")

	emit := func(verdict, reason string, rules []string,
		truthClass, agentRole, resType string, stage int, obligations []string) *PDPResponse {
		if rules == nil {
			rules = []string{}
		}
		if obligations == nil {
			obligations = []string{}
		}
		resp := &PDPResponse{
			DecisionID: decisionID, Verdict: verdict,
			PolicyVersion: pdp.policyStore.GetPolicyVersion(),
			PolicyHash:    pdp.policyStore.GetPolicyHash(),
			DeterminingRules: rules, TruthClassification: truthClass,
			RequestHash: requestHash, Timestamp: timestamp,
			Reason: reason, AgentRole: agentRole,
			ResourceType: resType, StageReached: stage,
			Obligations: obligations,
		}
		pdp.TraceStore.Emit(resp, req)
		return resp
	}

	// STAGE 1: REQUEST VALIDATION
	if req.AgentID == "" {
		return emit("DENY", "INVALID_AGENT_ID", nil, "UNKNOWN", "UNKNOWN", "UNKNOWN", 1, nil)
	}
	if req.ResourceID == "" {
		return emit("DENY", "INVALID_RESOURCE_ID", nil, "UNKNOWN", "UNKNOWN", "UNKNOWN", 1, nil)
	}
	validActions := map[string]bool{"read": true, "write": true, "delete": true, "execute": true}
	if !validActions[req.Action] {
		return emit("DENY", "INVALID_ACTION", nil, "UNKNOWN", "UNKNOWN", "UNKNOWN", 1, nil)
	}

	// STAGE 2: REGISTRY LOOKUP
	agent := pdp.Registry.GetAgent(req.AgentID)
	if agent == nil {
		return emit("DENY", "AGENT_NOT_FOUND", nil, "UNKNOWN", "UNKNOWN", "UNKNOWN", 2, nil)
	}
	if agent.Status != "ACTIVE" {
		return emit("DENY", "AGENT_"+agent.Status, nil, "UNKNOWN", agent.AgentRole, "UNKNOWN", 2, nil)
	}
	resource := pdp.Registry.GetResource(req.ResourceID)
	if resource == nil {
		return emit("DENY", "RESOURCE_NOT_FOUND", nil, "UNKNOWN", agent.AgentRole, "UNKNOWN", 2, nil)
	}

	// STAGE 3: POLICY EVALUATION
	matchingRules := pdp.policyStore.FindMatchingRules(
		agent.AgentRole, resource.ResourceType, req.Action)

	// STAGE 4: AUTHORITY DECISION
	if len(matchingRules) == 0 {
		return emit("DENY", "NO_MATCHING_RULE", []string{"AUTH-DENY-ALL"},
			resource.Classification, agent.AgentRole, resource.ResourceType, 4, nil)
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
			resource.Classification, agent.AgentRole, resource.ResourceType, 5, nil)
	}
	if len(allowRules) == 0 {
		return emit("DENY", "NO_ALLOW_RULE", []string{"AUTH-DENY-ALL"},
			resource.Classification, agent.AgentRole, resource.ResourceType, 4, nil)
	}

	// Bell-LaPadula classification ceiling
	// HIGH-05 + MED: Explicit error handling for ParseTruthLevel.
	// With the fail-closed fix, parse errors return TruthLevel(-1), which
	// causes comparisons to fail safely. We add explicit checks for clarity.
	agentClear, agentErr := ParseTruthLevel(agent.ClassificationMax)
	if agentErr != nil {
		return emit("DENY", "AGENT_CLASSIFICATION_PARSE_FAILURE", nil,
			resource.Classification, agent.AgentRole, resource.ResourceType, 5, nil)
	}
	resLevel, resErr := ParseTruthLevel(resource.Classification)
	if resErr != nil {
		return emit("DENY", "RESOURCE_CLASSIFICATION_PARSE_FAILURE", nil,
			resource.Classification, agent.AgentRole, resource.ResourceType, 5, nil)
	}
	if agentClear < resLevel {
		return emit("DENY", "CLASSIFICATION_CEILING_EXCEEDED", extractIDs(allowRules),
			resource.Classification, agent.AgentRole, resource.ResourceType, 5, nil)
	}
	for _, rule := range allowRules {
		ruleCeil, ruleErr := ParseTruthLevel(rule.ClassificationMax)
		if ruleErr != nil {
			return emit("DENY", "RULE_CLASSIFICATION_PARSE_FAILURE",
				[]string{rule.RuleID},
				resource.Classification, agent.AgentRole, resource.ResourceType, 5, nil)
		}
		if ruleCeil < resLevel {
			return emit("DENY", "RULE_CLASSIFICATION_CEILING_EXCEEDED",
				[]string{rule.RuleID},
				resource.Classification, agent.AgentRole, resource.ResourceType, 5, nil)
		}
	}

	// GAP-05: Collect obligations from matching ALLOW rules
	obligations := collectObligations(allowRules)

	// STAGE 5: ALLOW
	return emit("ALLOW", "EXPLICIT_ALLOW", extractIDs(allowRules),
		resource.Classification, agent.AgentRole, resource.ResourceType, 5, obligations)
}

func extractIDs(rules []AuthorityRule) []string {
	ids := make([]string, len(rules))
	for i, r := range rules {
		ids[i] = r.RuleID
	}
	sort.Strings(ids)
	return ids
}

// collectObligations gathers all obligations from matching ALLOW rules (GAP-05).
func collectObligations(rules []AuthorityRule) []string {
	seen := make(map[string]bool)
	var obligations []string
	for _, r := range rules {
		for _, o := range r.Obligations {
			if !seen[o] {
				seen[o] = true
				obligations = append(obligations, o)
			}
		}
	}
	sort.Strings(obligations)
	return obligations
}
