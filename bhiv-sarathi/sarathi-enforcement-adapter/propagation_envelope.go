// propagation_envelope.go (v14.5 Cross-System Propagation Layer)
//
// PropagationEnvelope is the sealed, immutable cross-system artifact that
// carries the full enforcement chain from Sarathi to BHIV Core, InsightFlow,
// and Bucket. Once sealed, the envelope is treated as read-only: all fields
// are unexported, mutation is a compile-time error, slice accessors return
// defensive copies.
//
// The envelope carries a four-element propagation chain:
//   [decision_hash, decision_core_hash, enforcement_hash, response_hash]
// and a chain_binding_hash over that chain. Any drift at any hop breaks
// the chain_binding_hash and fires CodePropagationChainBroken.
//
// Pattern mirrors execution_response.go:57-231 (unexported fields + accessors
// + defensive copies for slices). The result is that Sarathi's canonical
// response bytes, once sealed, cannot be re-serialized, re-sorted, or
// re-shaped by any downstream caller without detection.

package main

import (
	"bytes"
	"fmt"
	"time"
)

// PropagationEnvelopeSchemaVersion identifies the wire format of this envelope.
// Downstream systems pin to this version; incompatibility → PDP_DECISION_INVALID.
const PropagationEnvelopeSchemaVersion = "sarathi.propagation/v1.0"

// PropagationEnvelope is the sealed cross-system artifact. ALL fields are
// UNEXPORTED. Access only through read-only accessors.
type PropagationEnvelope struct {
	// Ingest anchors (from PDPAdapter.Ingest — the raw bytes Tanvi sent)
	rawDecisionBytes []byte // SEALED — original signed bytes
	ingestHash       string // Sha256Hex(rawDecisionBytes)

	// Decision anchors (from ExternalDecision, verified in verifyIngestIntegrity)
	decisionID       string
	decisionHash     string // from ExternalDecision.DecisionHash
	decisionCoreHash string // from ExternalDecision.DecisionCoreHash
	verdict          string // from ExternalDecision.Verdict (string-converted)

	// Enforcement anchors (from ExternalEnforcementResult — Sarathi's output)
	enforcementHash    string
	requestBindingHash string
	correlationID      string
	executionID        string // Raj's downstream execution identifier
	enforcedAt         string // RFC3339-ish timestamp
	mode               string // always "EXTERNAL"

	// Response envelope (canonical bytes frozen at seal time)
	canonicalResponseBytes []byte // SEALED — the exact bytes propagated downstream
	responseHash           string // Sha256Hex(canonicalResponseBytes)

	// Trace continuity
	traceID       string
	spanID        string
	schemaVersion string // PropagationEnvelopeSchemaVersion

	// Chain binding
	propagationChain []string // ordered: [decision_hash, core_hash, enforcement_hash, response_hash]
	chainBindingHash string   // Sha256Hex(CanonicalJoinChain(propagationChain))

	// Seal timestamp
	sealedAt string
}

// SealPropagationEnvelope constructs a sealed envelope from the PDP ingest bytes,
// the parsed+verified ExternalDecision, Sarathi's ExternalEnforcementResult, and
// the canonical response bytes. Failure modes:
//   - rawDecisionBytes is empty → CodePDPDecisionInvalid
//   - canonicalResponseBytes is empty → CodeResponseHashMismatch (treated as upstream error)
//   - Either d or r is nil → construction error
//   - TraceContext is nil → a new one is generated (trace must never be absent)
//
// Contract: the caller is responsible for ensuring canonicalResponseBytes are
// in canonical form. This constructor does NOT re-canonicalize — it hashes the
// bytes as-provided so the envelope's response_hash == Sha256Hex of the exact
// bytes that will be sent downstream.
func SealPropagationEnvelope(
	rawDecisionBytes []byte,
	d *ExternalDecision,
	r *ExternalEnforcementResult,
	canonicalResponseBytes []byte,
	executionID string,
	traceCtx *TraceContext,
	correlationID string,
) (*PropagationEnvelope, error) {
	if len(rawDecisionBytes) == 0 {
		return nil, fmt.Errorf("propagation_envelope: rawDecisionBytes is empty (CodePDPDecisionInvalid)")
	}
	if d == nil {
		return nil, fmt.Errorf("propagation_envelope: ExternalDecision is nil")
	}
	if r == nil {
		return nil, fmt.Errorf("propagation_envelope: ExternalEnforcementResult is nil")
	}
	if len(canonicalResponseBytes) == 0 {
		return nil, fmt.Errorf("propagation_envelope: canonicalResponseBytes is empty")
	}

	// Defensive: reject non-canonical response bytes. This catches the case
	// where a caller accidentally hands over bytes from json.Marshal on a
	// map[string]interface{} (non-deterministic key order).
	if ok, detail := VerifyCanonicalBytes(canonicalResponseBytes); !ok {
		return nil, fmt.Errorf("propagation_envelope: response bytes are not canonical: %s", detail)
	}

	// Ensure trace continuity — envelope must carry a trace_id end-to-end.
	// v15.5: when SARATHI_TRACE_ID_REQUIRE_INBOUND=true, NewTraceContext()
	// returns nil; we then fail-closed because trace_id is upstream Core's
	// property and must never be minted by Sarathi in production.
	if traceCtx == nil {
		traceCtx = NewTraceContext()
	}
	if traceCtx == nil {
		return nil, fmt.Errorf("propagation_envelope: trace_id required: caller must propagate inbound X-Sarathi-Trace-ID; SARATHI_TRACE_ID_REQUIRE_INBOUND=true")
	}

	// Defensive copy of raw decision bytes (caller may reuse buffer)
	rawCopy := make([]byte, len(rawDecisionBytes))
	copy(rawCopy, rawDecisionBytes)

	// Defensive copy of canonical response bytes (caller may reuse buffer)
	respCopy := make([]byte, len(canonicalResponseBytes))
	copy(respCopy, canonicalResponseBytes)

	ingestHash := Sha256Hex(rawCopy)
	responseHash := Sha256Hex(respCopy)

	// Build the four-element propagation chain in deterministic order:
	//   decision_hash → decision_core_hash → enforcement_hash → response_hash
	chain := []string{
		d.DecisionHash,
		d.DecisionCoreHash,
		r.EnforcementHash,
		responseHash,
	}
	chainBindingHash := Sha256Hex(CanonicalJoinChain(chain))

	env := &PropagationEnvelope{
		rawDecisionBytes:       rawCopy,
		ingestHash:             ingestHash,
		decisionID:             d.DecisionID,
		decisionHash:           d.DecisionHash,
		decisionCoreHash:       d.DecisionCoreHash,
		verdict:                string(d.Verdict),
		enforcementHash:        r.EnforcementHash,
		requestBindingHash:     r.RequestBindingHash,
		correlationID:          correlationID,
		executionID:            executionID,
		enforcedAt:             r.EnforcedAt,
		mode:                   r.Mode,
		canonicalResponseBytes: respCopy,
		responseHash:           responseHash,
		traceID:                traceCtx.TraceID,
		spanID:                 traceCtx.SpanID,
		schemaVersion:          PropagationEnvelopeSchemaVersion,
		propagationChain:       chain,
		chainBindingHash:       chainBindingHash,
		sealedAt:               time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
	}

	// Self-check: VerifySelf must succeed immediately after seal.
	if err := env.VerifySelf(); err != nil {
		return nil, fmt.Errorf("propagation_envelope: self-verification failed post-seal: %w", err)
	}
	return env, nil
}

// --- Read-only accessors ---

// IngestHash returns Sha256Hex(rawDecisionBytes).
func (e *PropagationEnvelope) IngestHash() string { return e.ingestHash }

// DecisionID is the upstream PDP decision identifier.
func (e *PropagationEnvelope) DecisionID() string { return e.decisionID }

// DecisionHash is the full-integrity SHA-256 hash of the PDP decision.
func (e *PropagationEnvelope) DecisionHash() string { return e.decisionHash }

// DecisionCoreHash is the request-binding SHA-256 hash of the PDP decision.
func (e *PropagationEnvelope) DecisionCoreHash() string { return e.decisionCoreHash }

// Verdict is the PDP's verdict (ALLOW / DENY / ESCALATE).
func (e *PropagationEnvelope) Verdict() string { return e.verdict }

// EnforcementHash is the post-enforcement SHA-256 hash of Sarathi's decision.
func (e *PropagationEnvelope) EnforcementHash() string { return e.enforcementHash }

// RequestBindingHash binds the decision to the exact request fields.
func (e *PropagationEnvelope) RequestBindingHash() string { return e.requestBindingHash }

// CorrelationID is the per-request correlation identifier.
func (e *PropagationEnvelope) CorrelationID() string { return e.correlationID }

// ExecutionID is the downstream execution identifier (Raj's Execution Engine).
func (e *PropagationEnvelope) ExecutionID() string { return e.executionID }

// EnforcedAt is the enforcement timestamp (RFC3339-ish).
func (e *PropagationEnvelope) EnforcedAt() string { return e.enforcedAt }

// Mode is always "EXTERNAL" for PDP-ingested decisions.
func (e *PropagationEnvelope) Mode() string { return e.mode }

// ResponseHash is Sha256Hex of the canonical response bytes.
// This is the header value sent as X-Sarathi-Response-Hash on every propagation hop.
func (e *PropagationEnvelope) ResponseHash() string { return e.responseHash }

// ChainBindingHash is Sha256Hex of the four-element propagation chain.
// This is the header value sent as X-Sarathi-Chain-Binding on every propagation hop.
func (e *PropagationEnvelope) ChainBindingHash() string { return e.chainBindingHash }

// TraceID is the W3C trace identifier, constant across all hops.
func (e *PropagationEnvelope) TraceID() string { return e.traceID }

// SpanID is the W3C span identifier at envelope creation.
func (e *PropagationEnvelope) SpanID() string { return e.spanID }

// SchemaVersion pins the envelope's wire format (PropagationEnvelopeSchemaVersion).
func (e *PropagationEnvelope) SchemaVersion() string { return e.schemaVersion }

// SealedAt is the RFC3339-ish timestamp of envelope creation.
func (e *PropagationEnvelope) SealedAt() string { return e.sealedAt }

// CanonicalResponseBytes returns a defensive COPY of the sealed response bytes.
// Mutation of the returned slice does NOT affect the envelope.
// Callers send these bytes UNCHANGED to downstream systems.
func (e *PropagationEnvelope) CanonicalResponseBytes() []byte {
	cp := make([]byte, len(e.canonicalResponseBytes))
	copy(cp, e.canonicalResponseBytes)
	return cp
}

// RawDecisionBytes returns a defensive COPY of the original PDP input bytes.
// These are the bytes Tanvi emitted — useful for audit + signature re-verification.
func (e *PropagationEnvelope) RawDecisionBytes() []byte {
	cp := make([]byte, len(e.rawDecisionBytes))
	copy(cp, e.rawDecisionBytes)
	return cp
}

// PropagationChain returns a defensive COPY of the ordered chain:
//   [decision_hash, decision_core_hash, enforcement_hash, response_hash]
func (e *PropagationEnvelope) PropagationChain() []string {
	cp := make([]string, len(e.propagationChain))
	copy(cp, e.propagationChain)
	return cp
}

// --- Integrity methods ---

// VerifySelf re-derives chain_binding_hash from the stored chain and compares
// it to the stored value. Must succeed immediately after SealPropagationEnvelope
// and remain true for the envelope's lifetime. A mismatch indicates memory
// corruption or a bug — a propagated envelope that fails self-verification
// must be rejected with CodePropagationChainBroken.
func (e *PropagationEnvelope) VerifySelf() error {
	expected := Sha256Hex(CanonicalJoinChain(e.propagationChain))
	if expected != e.chainBindingHash {
		return fmt.Errorf("chain_binding_hash mismatch: expected=%s stored=%s", expected, e.chainBindingHash)
	}
	// Re-hash canonical response bytes — catches any mutation attempt.
	respRehash := Sha256Hex(e.canonicalResponseBytes)
	if respRehash != e.responseHash {
		return fmt.Errorf("response_hash mismatch: expected=%s stored=%s", respRehash, e.responseHash)
	}
	// Re-hash raw decision bytes.
	ingestRehash := Sha256Hex(e.rawDecisionBytes)
	if ingestRehash != e.ingestHash {
		return fmt.Errorf("ingest_hash mismatch: expected=%s stored=%s", ingestRehash, e.ingestHash)
	}
	// Chain must include response_hash as the final element.
	if len(e.propagationChain) != 4 {
		return fmt.Errorf("propagation_chain must have 4 elements, got %d", len(e.propagationChain))
	}
	if e.propagationChain[3] != e.responseHash {
		return fmt.Errorf("propagation_chain[3] must equal response_hash: chain=%s hash=%s",
			e.propagationChain[3], e.responseHash)
	}
	return nil
}

// EqualsBytes returns true if data matches the sealed canonical response bytes.
// Used by deterministic router handler on ACK from downstream.
func (e *PropagationEnvelope) EqualsBytes(data []byte) bool {
	return bytes.Equal(e.canonicalResponseBytes, data)
}

// --- HTTP propagation header set ---

// Header name constants used by deterministic router handler.
const (
	HeaderTraceID         = "X-Sarathi-Trace-ID"
	HeaderSpanID          = "X-Sarathi-Span-ID"
	HeaderResponseHash    = "X-Sarathi-Response-Hash"
	HeaderChainBinding    = "X-Sarathi-Chain-Binding"
	HeaderDecisionID      = "X-Sarathi-Decision-ID"
	HeaderExecutionID     = "X-Sarathi-Execution-ID"
	HeaderCorrelationID   = "X-Sarathi-Correlation-ID"
	HeaderSchemaVersion   = "X-Sarathi-Schema-Version"
	HeaderEnforcementHash = "X-Sarathi-Enforcement-Hash"
	HeaderAckHash         = "X-Sarathi-Ack-Hash"
)

// ToHeaderMap produces the HTTP header set for propagation. The returned map
// is a fresh allocation — safe to mutate without affecting the envelope.
// Every outbound hop in DeterministicHTTPRoutingHandler sets these headers;
// the peer echoes X-Sarathi-Ack-Hash back with its received response_hash.
func (e *PropagationEnvelope) ToHeaderMap() map[string]string {
	return map[string]string{
		HeaderTraceID:         e.traceID,
		HeaderSpanID:          e.spanID,
		HeaderResponseHash:    e.responseHash,
		HeaderChainBinding:    e.chainBindingHash,
		HeaderDecisionID:      e.decisionID,
		HeaderExecutionID:     e.executionID,
		HeaderCorrelationID:   e.correlationID,
		HeaderSchemaVersion:   e.schemaVersion,
		HeaderEnforcementHash: e.enforcementHash,
	}
}

// ToSummaryMap produces an audit-friendly map (sorted keys, canonical values).
// Used by proof_logs/propagation_replay_results.jsonl and audit sinks.
func (e *PropagationEnvelope) ToSummaryMap() map[string]interface{} {
	return map[string]interface{}{
		"schema_version":       e.schemaVersion,
		"decision_id":          e.decisionID,
		"decision_hash":        e.decisionHash,
		"decision_core_hash":   e.decisionCoreHash,
		"enforcement_hash":     e.enforcementHash,
		"request_binding_hash": e.requestBindingHash,
		"response_hash":        e.responseHash,
		"chain_binding_hash":   e.chainBindingHash,
		"propagation_chain":    append([]string(nil), e.propagationChain...),
		"trace_id":             e.traceID,
		"span_id":              e.spanID,
		"correlation_id":       e.correlationID,
		"execution_id":         e.executionID,
		"verdict":              e.verdict,
		"mode":                 e.mode,
		"enforced_at":          e.enforcedAt,
		"sealed_at":            e.sealedAt,
		"ingest_hash":          e.ingestHash,
	}
}
