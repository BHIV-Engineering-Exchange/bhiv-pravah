package main

// execution_request.go — Immutable, hash-bound execution request.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Enforcement Adapter (PEP)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// IMMUTABILITY CONTRACT:
//   - All fields are unexported — no external write access.
//   - requestHash is computed at construction and never recomputed.
//   - No SetXxx() or ModifyXxx() methods exist.
//   - Read-only accessors return copies, not references.
//
// GAP FIXES APPLIED:
//   GAP-11: json.Marshal error handling (fail-closed)
//   GAP-14: Input sanitization (length limits, charset validation, format checks)

import (
	"encoding/json"
	"fmt"
	"regexp"
	"unicode/utf8"
)

// Input validation constants (GAP-14)
const (
	MaxFieldLength  = 256 // Maximum length for any single field
	MaxActionLength = 32  // Maximum length for action field
)

// idPattern matches safe identifiers: alphanumeric, hyphens, underscores, dots.
// Rejects injection characters, control characters, and whitespace.
var idPattern = regexp.MustCompile(`^[a-zA-Z0-9][a-zA-Z0-9._-]*$`)

// ================================================================
// ── v12.1/v12.2 SIGNED POSTURE SIGNAL (GAP-02 FIX) ──
// ================================================================
// SignedPostureSignal is the externally-produced, Ed25519-signed posture
// assertion attached to an ExecutionRequest. Sarathi only VERIFIES this —
// it NEVER computes posture, scores trust, or interprets behavior.
//
// v12.2 BOUNDARY PURIFICATION:
//   Originally declared in posture_signal.go (v12.1). Folded into
//   execution_request.go in v12.2 so the data structure lives next to
//   the request that carries it. The PostureVerifier and its errors live
//   in enforcement_adapter.go (next to the adapter that uses them).
//
// INVARIANT (INV-34):
//   Posture is NEVER computed inside Sarathi. The boolean Posture field
//   is set by the external issuer and signed as part of the canonical
//   payload — Sarathi's only action is cryptographic verification.
type SignedPostureSignal struct {
	AgentID   string `json:"agent_id"`
	Posture   bool   `json:"posture"`     // true = OK, false = denied
	IssuedAt  int64  `json:"issued_at"`   // Unix seconds UTC
	ExpiresAt int64  `json:"expires_at"`  // Unix seconds UTC
	Nonce     string `json:"nonce"`       // Single-use UUID
	IssuerID  string `json:"issuer_id"`   // Identifies the posture issuer
	Signature []byte `json:"signature"`   // Ed25519 over canonical payload
}

// postureSignPayload returns the canonical bytes that the issuer signs.
// Field order is fixed and pipe-separated for deterministic verification.
func (s *SignedPostureSignal) postureSignPayload() []byte {
	postureStr := "false"
	if s.Posture {
		postureStr = "true"
	}
	canonical := fmt.Sprintf("BHIV-POSTURE|%s|%s|%d|%d|%s|%s",
		s.AgentID, postureStr, s.IssuedAt, s.ExpiresAt, s.Nonce, s.IssuerID)
	return []byte(canonical)
}

// validActions defines the set of permitted action verbs.
var validActions = map[string]bool{
	"read":    true,
	"write":   true,
	"execute": true,
	"delete":  true,
}

// ExecutionRequest is an immutable, hash-bound request to the enforcement gate.
type ExecutionRequest struct {
	agentID          string
	resourceID       string
	action           string
	correlationID    string
	policyVersion    string
	requestHash      string
	isValid          bool
	validationErrors []string

	// v12.1 GAP-02 FIX: Optional signed posture signal. When present, the
	// PostureVerifier pre-gate verifies its signature, expiry, and nonce
	// BEFORE Enforce() is called. Sarathi NEVER computes posture — it only
	// verifies a signed, immutable signal produced externally. See INV-34
	// and posture_signal.go.
	postureSignal *SignedPostureSignal
}

// NewExecutionRequest constructs an immutable ExecutionRequest.
func NewExecutionRequest(agentID, resourceID, action, correlationID string, policyVersion ...string) *ExecutionRequest {
	req := &ExecutionRequest{
		agentID:       agentID,
		resourceID:    resourceID,
		action:        action,
		correlationID: correlationID,
	}
	if len(policyVersion) > 0 {
		req.policyVersion = policyVersion[0]
	}

	req.validationErrors = req.validate()
	req.isValid = len(req.validationErrors) == 0
	req.requestHash = req.computeHash()

	return req
}

// validate checks all required fields with comprehensive sanitization (GAP-14).
func (r *ExecutionRequest) validate() []string {
	var errors []string

	// --- agent_id ---
	if r.agentID == "" {
		errors = append(errors, "MISSING_AGENT_ID")
	} else {
		if len(r.agentID) > MaxFieldLength {
			errors = append(errors, fmt.Sprintf("AGENT_ID_TOO_LONG_%d", len(r.agentID)))
		}
		if !utf8.ValidString(r.agentID) {
			errors = append(errors, "AGENT_ID_INVALID_ENCODING")
		} else if !idPattern.MatchString(r.agentID) {
			errors = append(errors, "AGENT_ID_INVALID_CHARS")
		}
	}

	// --- resource_id ---
	if r.resourceID == "" {
		errors = append(errors, "MISSING_RESOURCE_ID")
	} else {
		if len(r.resourceID) > MaxFieldLength {
			errors = append(errors, fmt.Sprintf("RESOURCE_ID_TOO_LONG_%d", len(r.resourceID)))
		}
		if !utf8.ValidString(r.resourceID) {
			errors = append(errors, "RESOURCE_ID_INVALID_ENCODING")
		} else if !idPattern.MatchString(r.resourceID) {
			errors = append(errors, "RESOURCE_ID_INVALID_CHARS")
		}
	}

	// --- action ---
	if r.action == "" {
		errors = append(errors, "MISSING_ACTION")
	} else if len(r.action) > MaxActionLength {
		errors = append(errors, fmt.Sprintf("ACTION_TOO_LONG_%d", len(r.action)))
	} else if !validActions[r.action] {
		errors = append(errors, fmt.Sprintf("INVALID_ACTION_%s", r.action))
	}

	// --- correlation_id ---
	if r.correlationID == "" {
		errors = append(errors, "MISSING_CORRELATION_ID")
	} else if len(r.correlationID) > MaxFieldLength {
		errors = append(errors, fmt.Sprintf("CORRELATION_ID_TOO_LONG_%d", len(r.correlationID)))
	}

	// --- policy_version (optional but validated if present) ---
	if r.policyVersion != "" && len(r.policyVersion) > MaxFieldLength {
		errors = append(errors, fmt.Sprintf("POLICY_VERSION_TOO_LONG_%d", len(r.policyVersion)))
	}

	return errors
}

// computeHash computes SHA-256 of canonical JSON for the request core fields.
// Uses the same PDPRequest struct as the PDP engine for byte-identical serialization.
func (r *ExecutionRequest) computeHash() string {
	req := PDPRequest{
		AgentID:    r.agentID,
		ResourceID: r.resourceID,
		Action:     r.action,
	}
	// GAP-11: handle marshal error
	data, err := json.Marshal(req)
	if err != nil {
		return fmt.Sprintf("HASH_ERROR:%v", err)
	}
	return Sha256Hex(data)
}

// --- Read-only accessors ---

func (r *ExecutionRequest) AgentID() string       { return r.agentID }
func (r *ExecutionRequest) ResourceID() string     { return r.resourceID }
func (r *ExecutionRequest) Action() string         { return r.action }
func (r *ExecutionRequest) CorrelationID() string  { return r.correlationID }
func (r *ExecutionRequest) PolicyVersion() string  { return r.policyVersion }
func (r *ExecutionRequest) RequestHash() string    { return r.requestHash }
func (r *ExecutionRequest) IsValid() bool          { return r.isValid }

// PostureSignal returns the optional signed posture signal attached to the
// request (v12.1). May be nil. The request hash does NOT cover this field
// so that attaching a signal at admission time does not invalidate a hash
// computed at construction.
func (r *ExecutionRequest) PostureSignal() *SignedPostureSignal {
	return r.postureSignal
}

// AttachPostureSignal attaches a signed posture signal to the request.
// This is a controlled exception to immutability: the signal itself is
// Ed25519-signed (tamper-evident), and it is excluded from the request
// hash so attaching it does not change identity. The pre-gate verifier
// is the only intended caller.
func (r *ExecutionRequest) AttachPostureSignal(signal *SignedPostureSignal) {
	r.postureSignal = signal
}

func (r *ExecutionRequest) ValidationErrors() []string {
	cp := make([]string, len(r.validationErrors))
	copy(cp, r.validationErrors)
	return cp
}

// ToMap returns a read-only map representation for trace/logging.
func (r *ExecutionRequest) ToMap() map[string]interface{} {
	return map[string]interface{}{
		"agent_id":          r.agentID,
		"resource_id":       r.resourceID,
		"action":            r.action,
		"correlation_id":    r.correlationID,
		"policy_version":    r.policyVersion,
		"request_hash":      r.requestHash,
		"is_valid":          r.isValid,
		"validation_errors": r.validationErrors,
	}
}
