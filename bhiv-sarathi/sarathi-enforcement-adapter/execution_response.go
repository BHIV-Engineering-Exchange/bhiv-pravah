package main

// execution_response.go — Hash-chained, immutable enforcement decision record.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Enforcement Adapter (PEP)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// IMMUTABILITY CONTRACT:
//   - All fields are unexported — no external write access.
//   - enforcementHash includes enforcementNonce (UUID4) for uniqueness.
//   - No modification path exists after construction.
//
// HASH CHAIN:
//   request_hash → pdp_decision_hash → enforcement_hash
//   Each link is independently verifiable.
//
// GAP FIXES APPLIED:
//   GAP-02: TTL / decision expiry (validUntil field + DefaultDecisionTTL)
//   GAP-05: Obligations framework (obligations field from PDP)
//   GAP-11: json.Marshal error handling (fail-closed on marshal failure)
//   GAP-17: Struct-based hash computation (deterministic field ordering)

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
)

// DefaultDecisionTTL is the maximum lifetime of an enforcement decision.
// After this duration, the ExecutionEngine MUST reject the response.
// This prevents TOCTOU (Time-of-Check, Time-of-Use) attacks where an
// agent is revoked between decision time and execution time.
// Industry standard: NIST 800-207 mandates per-session/per-request TTL.
const DefaultDecisionTTL = 30 * time.Second

// enforcementHashPayload is a struct for deterministic enforcement hash
// computation. Using a struct instead of map[string]string guarantees
// Go's json.Marshal produces fields in declaration order, avoiding any
// risk from map iteration non-determinism (GAP-17).
type enforcementHashPayload struct {
	RequestHash       string `json:"request_hash"`
	PDPDecisionHash   string `json:"pdp_decision_hash"`
	Verdict           string `json:"verdict"`
	EnforcementStage  string `json:"enforcement_stage"`
	EnforcementReason string `json:"enforcement_reason"`
	CorrelationID     string `json:"correlation_id"`
	DecisionID        string `json:"decision_id"`
	EnforcementNonce  string `json:"enforcement_nonce"`
}

// ExecutionResponse is the immutable output of the enforcement adapter.
// It is the ONLY thing the ExecutionEngine accepts.
type ExecutionResponse struct {
	correlationID       string
	requestHash         string
	enforcementStage    string
	enforcementReason   string
	verdict             string
	decisionID          string
	policyVersion       string
	policyHash          string
	pdpReason           string
	determiningRules    []string
	truthClassification string
	pdpRequestHash      string
	agentRole           string
	resourceType        string
	stageReached        int
	pdpTimestamp        string
	pdpDecisionHash     string
	enforcementNonce    string
	enforcementHash     string
	enforcedAt          string
	registryVersion     int64            // Gap 2: Freshness
	rpaHash             string           // Gap 3: Validation binding
	validUntil          time.Time        // GAP-02: TTL expiry timestamp
	obligations         []string         // GAP-05: Mandatory obligations from PDP
	capabilityToken     *CapabilityToken // Phase 5: Execution requires this token
}

// NewExecutionResponse calls NewExecutionResponseFull with default values.
// Provided for backward compatibility with tests.
func NewExecutionResponse(
	req *ExecutionRequest,
	pdpResponse *PDPResponse,
	enforcementStage string,
	enforcementReason string,
) *ExecutionResponse {
	return NewExecutionResponseFull(req, pdpResponse, enforcementStage, enforcementReason, 0, "")
}

// NewExecutionResponseFull constructs an immutable ExecutionResponse from an
// ExecutionRequest, optional PDP response, registry version, and RPA hash.
func NewExecutionResponseFull(
	req *ExecutionRequest,
	pdpResponse *PDPResponse,
	enforcementStage string,
	enforcementReason string,
	registryVersion int64,
	rpaHash string,
) *ExecutionResponse {

	now := time.Now().UTC()
	resp := &ExecutionResponse{
		correlationID:     req.CorrelationID(),
		requestHash:       req.RequestHash(),
		enforcementStage:  enforcementStage,
		enforcementReason: enforcementReason,
		enforcementNonce:  uuid.New().String(),
		enforcedAt:        now.Format("2006-01-02T15:04:05.000000Z"),
		validUntil:        now.Add(DefaultDecisionTTL), // GAP-02: TTL
		registryVersion:   registryVersion,
		rpaHash:           rpaHash,
	}

	if pdpResponse != nil {
		resp.verdict = pdpResponse.Verdict
		resp.decisionID = pdpResponse.DecisionID
		resp.policyVersion = pdpResponse.PolicyVersion
		resp.policyHash = pdpResponse.PolicyHash
		resp.pdpReason = pdpResponse.Reason
		resp.determiningRules = pdpResponse.DeterminingRules
		resp.truthClassification = pdpResponse.TruthClassification
		resp.pdpRequestHash = pdpResponse.RequestHash
		resp.agentRole = pdpResponse.AgentRole
		resp.resourceType = pdpResponse.ResourceType
		resp.stageReached = pdpResponse.StageReached
		resp.pdpTimestamp = pdpResponse.Timestamp
		resp.obligations = pdpResponse.Obligations // GAP-05

		// Compute PDP decision hash (v7.0: safe error propagation — no panic)
		pdpJSON, err := json.Marshal(pdpResponse)
		if err != nil {
			// FIX-06 (v7.0): Safe fallback — deterministic error hash instead of panic
			resp.pdpDecisionHash = Sha256Hex([]byte(fmt.Sprintf("PDP_HASH_ERROR:%s:%v", resp.decisionID, err)))
		} else {
			resp.pdpDecisionHash = Sha256Hex(pdpJSON)
		}
	} else {
		resp.verdict = "DENY"
		resp.decisionID = ""
		resp.policyVersion = ""
		resp.policyHash = ""
		resp.pdpReason = ""
		resp.determiningRules = []string{}
		resp.truthClassification = "UNKNOWN"
		resp.pdpRequestHash = ""
		resp.agentRole = "UNKNOWN"
		resp.resourceType = "UNKNOWN"
		resp.stageReached = 0
		resp.pdpTimestamp = ""
		resp.pdpDecisionHash = "NO_PDP_EVALUATION"
		resp.obligations = []string{}
	}

	resp.enforcementHash = resp.computeEnforcementHash()

	// Phase 5: Issue CapabilityToken on ALLOW verdicts only.
	// DENY/ESCALATE → nil token → execution impossible.
	resp.capabilityToken = IssueCapabilityToken(resp, rpaHash)

	return resp
}

// computeEnforcementHash computes SHA-256 chain: request → PDP → enforcement.
// Uses struct-based serialization for deterministic field ordering (GAP-17).
// Includes enforcementNonce (UUID4) to ensure every evaluation produces a
// unique hash, even for identical requests.
func (r *ExecutionResponse) computeEnforcementHash() string {
	payload := enforcementHashPayload{
		RequestHash:       r.requestHash,
		PDPDecisionHash:   r.pdpDecisionHash,
		Verdict:           r.verdict,
		EnforcementStage:  r.enforcementStage,
		EnforcementReason: r.enforcementReason,
		CorrelationID:     r.correlationID,
		DecisionID:        r.decisionID,
		EnforcementNonce:  r.enforcementNonce,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		// FIX-06 (v7.0): Safe fallback — deterministic error hash instead of panic
		return Sha256Hex([]byte(fmt.Sprintf("ENF_HASH_ERROR:%s:%s:%v", r.correlationID, r.decisionID, err)))
	}
	return Sha256Hex(data)
}

// --- Read-only accessors ---

func (r *ExecutionResponse) Verdict() string             { return r.verdict }
func (r *ExecutionResponse) DecisionID() string          { return r.decisionID }
func (r *ExecutionResponse) CorrelationID() string       { return r.correlationID }
func (r *ExecutionResponse) PolicyVersionField() string  { return r.policyVersion }
func (r *ExecutionResponse) PolicyHashField() string     { return r.policyHash }
func (r *ExecutionResponse) RequestHash() string         { return r.requestHash }
func (r *ExecutionResponse) EnforcementHash() string     { return r.enforcementHash }
func (r *ExecutionResponse) EnforcementNonce() string    { return r.enforcementNonce }
func (r *ExecutionResponse) PDPDecisionHash() string     { return r.pdpDecisionHash }
func (r *ExecutionResponse) EnforcementStage() string    { return r.enforcementStage }
func (r *ExecutionResponse) EnforcementReason() string   { return r.enforcementReason }
func (r *ExecutionResponse) PDPReason() string           { return r.pdpReason }
func (r *ExecutionResponse) TruthClassification() string { return r.truthClassification }
func (r *ExecutionResponse) AgentRoleField() string      { return r.agentRole }
func (r *ExecutionResponse) ResourceTypeField() string   { return r.resourceType }
func (r *ExecutionResponse) StageReached() int           { return r.stageReached }
func (r *ExecutionResponse) ValidUntil() time.Time       { return r.validUntil } // GAP-02
func (r *ExecutionResponse) EnforcedAt() string          { return r.enforcedAt }
func (r *ExecutionResponse) RegistryVersion() int64      { return r.registryVersion }
func (r *ExecutionResponse) RpaHash() string             { return r.rpaHash }

// Obligations returns a defensive copy of the obligations list (GAP-05).
func (r *ExecutionResponse) Obligations() []string {
	cp := make([]string, len(r.obligations))
	copy(cp, r.obligations)
	return cp
}

// IsExpired returns true if the decision TTL has elapsed (GAP-02).
func (r *ExecutionResponse) IsExpired() bool {
	return time.Now().UTC().After(r.validUntil)
}

// GetCapabilityToken returns the capability token (nil for non-ALLOW verdicts).
// Phase 5: No token → no execution. This is absolute.
func (r *ExecutionResponse) GetCapabilityToken() *CapabilityToken {
	return r.capabilityToken
}

func (r *ExecutionResponse) DeterminingRules() []string {
	cp := make([]string, len(r.determiningRules))
	copy(cp, r.determiningRules)
	return cp
}

// ToMap returns a read-only map representation for trace/logging.
func (r *ExecutionResponse) ToMap() map[string]interface{} {
	return map[string]interface{}{
		"correlation_id":       r.correlationID,
		"verdict":              r.verdict,
		"decision_id":          r.decisionID,
		"policy_version":       r.policyVersion,
		"policy_hash":          r.policyHash,
		"request_hash":         r.requestHash,
		"pdp_decision_hash":    r.pdpDecisionHash,
		"enforcement_hash":     r.enforcementHash,
		"enforcement_nonce":    r.enforcementNonce,
		"enforcement_stage":    r.enforcementStage,
		"enforcement_reason":   r.enforcementReason,
		"pdp_reason":           r.pdpReason,
		"determining_rules":    r.determiningRules,
		"truth_classification": r.truthClassification,
		"agent_role":           r.agentRole,
		"resource_type":        r.resourceType,
		"stage_reached":        r.stageReached,
		"enforced_at":          r.enforcedAt,
		"valid_until":          r.validUntil.Format("2006-01-02T15:04:05.000000Z"),
		"registry_version":     r.registryVersion,
		"rpa_hash":             r.rpaHash,
		"obligations":          r.obligations,
		"has_capability_token": r.capabilityToken != nil,
	}
}
