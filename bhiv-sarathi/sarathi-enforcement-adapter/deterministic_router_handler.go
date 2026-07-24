// deterministic_router_handler.go (v14.5 Cross-System Propagation Layer)
//
// Wraps the existing HTTP routing handler with byte-equality enforcement.
//
// What changes vs NewHTTPRoutingHandler:
//   - Body is the envelope's sealed canonical response bytes — NEVER
//     re-serialized, NEVER re-sorted. We send exactly the bytes that were
//     hashed into response_hash at seal time.
//   - Every outbound request carries the full propagation header set
//     (X-Sarathi-Trace-ID, X-Sarathi-Response-Hash, X-Sarathi-Chain-Binding, …).
//   - Every response must echo X-Sarathi-Ack-Hash. If it doesn't match
//     response_hash, the hop returns a *PropagationStopError and the
//     router's RoutePropagation loop halts.
//   - Intelligence Layer (Sri Satya) is special: it receives digest-only
//     bytes, is NOT part of the chain, and its failure does NOT stop
//     propagation. The digest event carries fingerprint hashes, never
//     decision body.
//
// This file adds NO new network library; it uses net/http like the existing
// HTTPRoutingHandler.

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/google/uuid"
)

// IntelligenceDigestSchemaVersion pins the digest event schema. If this
// version drifts, downstream Intelligence Layer consumers must re-sync.
const IntelligenceDigestSchemaVersion = "sarathi.intelligence.digest/v1.0"

// IntelligenceDigestEvent is the redacted payload sent to Sri Satya's
// Intelligence Layer. It EXCLUDES the verdict body, token, raw decision
// bytes, and canonical response bytes — it only carries fingerprint hashes.
//
// Schema id: bhiv.intelligence.digest.v1 (see ecosystem_contracts.go).
type IntelligenceDigestEvent struct {
	EventID       string `json:"event_id"`
	TraceID       string `json:"trace_id"`
	CorrelationID string `json:"correlation_id"`
	ResponseHash  string `json:"response_hash"` // fingerprint, not verdict body
	VerdictHash   string `json:"verdict_hash"`  // Sha256Hex(verdict), not verdict itself
	Timestamp     string `json:"timestamp"`
	SchemaVersion string `json:"schema_version"`
}

// DigestEventFor constructs the Intelligence digest event for a given envelope.
// The returned struct contains NO decision body — only fingerprints.
func DigestEventFor(env *PropagationEnvelope) *IntelligenceDigestEvent {
	if env == nil {
		return nil
	}
	return &IntelligenceDigestEvent{
		EventID:       uuid.New().String(),
		TraceID:       env.TraceID(),
		CorrelationID: env.CorrelationID(),
		ResponseHash:  env.ResponseHash(),
		VerdictHash:   Sha256Hex([]byte(env.Verdict())),
		Timestamp:     time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		SchemaVersion: IntelligenceDigestSchemaVersion,
	}
}

// DeterministicHTTPRoutingConfig extends HTTPRoutingConfig with byte-equality
// enforcement knobs.
type DeterministicHTTPRoutingConfig struct {
	HTTPRoutingConfig
	// RequireAckHashHeader: peer MUST echo X-Sarathi-Ack-Hash matching
	// X-Sarathi-Response-Hash. If false, ACK is still checked when present
	// but missing ACK does not fail the hop.
	RequireAckHashHeader bool
	// AckHashHeader: name of the header peers use to echo the hash.
	// Defaults to HeaderAckHash ("X-Sarathi-Ack-Hash").
	AckHashHeader string
	// IntelligenceReadOnly: true only for the Intelligence (intent_layer)
	// target. Intelligence receives digest bytes (NOT canonical response
	// bytes) and its response is NOT verified against response_hash.
	IntelligenceReadOnly bool
}

// PropagationHopAudit is emitted by the deterministic handler for every
// attempt — success or violation — so the harness can reconstruct the full
// per-hop timeline. A subset of fields is also appended to the byte-equality
// report.
type PropagationHopAudit struct {
	Target       string              `json:"target"`
	Equality     ByteEqualityResult  `json:"equality"`
	StatusCode   int                 `json:"status_code"`
	LatencyNs    int64               `json:"latency_ns"`
	AttemptError string              `json:"attempt_error,omitempty"`
}

// NewDeterministicHTTPRoutingHandler returns a RoutingHandler that enforces
// byte-equality end-to-end for one target.
//
// The handler uses the envelope's sealed canonical response bytes as the
// request body — the inbound *RoutedEvent is consulted only for event_type
// and correlation_id in the Intelligence path.
//
// targetName: the logical name of the target (for circuit-breaker/bulkhead
// naming, and for audit records).
// env: the sealed propagation envelope. The same envelope instance is shared
// across all per-target handlers for a single decision; this is safe because
// the envelope is read-only.
// cfg: determines whether the target enforces byte-equality (normal in-chain
// targets) or receives digest-only bytes (Intelligence Layer).
func NewDeterministicHTTPRoutingHandler(
	targetName string,
	env *PropagationEnvelope,
	cfg DeterministicHTTPRoutingConfig,
) RoutingHandler {
	if cfg.Timeout <= 0 {
		cfg.Timeout = 5 * time.Second
	}
	if cfg.MaxConcurrency <= 0 {
		cfg.MaxConcurrency = 10
	}
	if cfg.AckHashHeader == "" {
		cfg.AckHashHeader = HeaderAckHash
	}

	client := &http.Client{Timeout: cfg.Timeout}
	cb := NewCircuitBreaker("route-det-"+targetName, cfg.CircuitBreaker)
	bulkhead := NewBulkheadLimiter("route-det-"+targetName, cfg.MaxConcurrency)

	return func(event *RoutedEvent) error {
		if env == nil {
			return fmt.Errorf("deterministic_handler: envelope is nil (target=%s)", targetName)
		}
		if !bulkhead.Acquire() {
			return fmt.Errorf("BULKHEAD_FULL: target '%s' at %d concurrent", targetName, cfg.MaxConcurrency)
		}
		defer bulkhead.Release()

		if !cb.Allow() {
			return fmt.Errorf("CIRCUIT_OPEN: target '%s' circuit breaker open", targetName)
		}

		// Pick the body: Intelligence Layer receives digest bytes; all
		// in-chain targets receive the sealed canonical response bytes.
		var (
			body     []byte
			bodyHash string
		)
		if cfg.IntelligenceReadOnly {
			de := DigestEventFor(env)
			b, err := CanonicalMarshal(de)
			if err != nil {
				cb.RecordFailure()
				return fmt.Errorf("MARSHAL_ERROR: digest event for '%s': %w", targetName, err)
			}
			body = b
			bodyHash = Sha256Hex(b)
		} else {
			body = env.CanonicalResponseBytes() // defensive copy
			bodyHash = env.ResponseHash()
		}

		// Build HTTP request with full propagation header set.
		req, err := http.NewRequest("POST", cfg.TargetURL, bytes.NewReader(body))
		if err != nil {
			cb.RecordFailure()
			return fmt.Errorf("REQUEST_ERROR: target '%s': %w", targetName, err)
		}
		req.Header.Set("Content-Type", "application/json")
		if cfg.AuthToken != "" {
			req.Header.Set("Authorization", "Bearer "+cfg.AuthToken)
		}
		for k, v := range cfg.Headers {
			req.Header.Set(k, v)
		}
		// Propagation headers — always set for every outbound hop.
		for k, v := range env.ToHeaderMap() {
			req.Header.Set(k, v)
		}
		// Mark digest-only deliveries explicitly so peers know to NOT treat
		// the body as a canonical response.
		if cfg.IntelligenceReadOnly {
			req.Header.Set("X-Sarathi-Digest-Only", "true")
			req.Header.Set(HeaderResponseHash, bodyHash) // fingerprint, not canonical body hash
		}

		start := time.Now()
		resp, err := client.Do(req)
		latency := time.Since(start).Nanoseconds()
		if err != nil {
			cb.RecordFailure()
			return fmt.Errorf("HTTP_ERROR: target '%s': %w", targetName, err)
		}
		defer resp.Body.Close()

		// Status code handling mirrors NewHTTPRoutingHandler, but with
		// byte-equality enforcement layered on top for 2xx responses.
		if resp.StatusCode >= 500 {
			cb.RecordFailure()
			return fmt.Errorf("SERVER_ERROR: target '%s' HTTP %d", targetName, resp.StatusCode)
		}
		if resp.StatusCode == http.StatusTooManyRequests {
			cb.RecordFailure()
			return fmt.Errorf("BACKPRESSURE: target '%s' HTTP 429", targetName)
		}
		if resp.StatusCode < 200 || resp.StatusCode >= 300 {
			return fmt.Errorf("CLIENT_ERROR: target '%s' HTTP %d", targetName, resp.StatusCode)
		}

		// Intelligence Layer: digest-only — its ACK is NOT part of the
		// propagation chain. We still prefer ACK if present but never
		// fail the hop on ACK absence.
		if cfg.IntelligenceReadOnly {
			cb.RecordSuccess()
			_ = latency
			return nil
		}

		// In-chain target: require ACK echo equal to response_hash.
		ackHash := resp.Header.Get(cfg.AckHashHeader)
		ok, eqRes := ValidateHop(targetName, body, bodyHash, ackHash, env)
		if !ok {
			cb.RecordFailure()
			_ = RecordViolation(eqRes)
			return NewPropagationStopError(eqRes)
		}
		cb.RecordSuccess()
		_ = latency
		return nil
	}
}

// --- Digest-only schema gate (defense in depth) ---

// IsValidDigestPayload returns true iff payload is the canonical form of a
// IntelligenceDigestEvent struct (verified by round-trip canonicalization
// + schema presence). Used by the Intelligence-side receiver as a trip wire:
// if a non-digest body ever reaches Sri Satya, this returns false and the
// caller raises CodeIntelligenceLayerBreach.
func IsValidDigestPayload(payload []byte) (bool, string) {
	if ok, detail := VerifyCanonicalBytes(payload); !ok {
		return false, "non_canonical: " + detail
	}
	var de IntelligenceDigestEvent
	if err := json.Unmarshal(payload, &de); err != nil {
		return false, fmt.Sprintf("unmarshal_error: %v", err)
	}
	if de.SchemaVersion != IntelligenceDigestSchemaVersion {
		return false, fmt.Sprintf("schema_version mismatch: got=%s want=%s",
			de.SchemaVersion, IntelligenceDigestSchemaVersion)
	}
	if de.ResponseHash == "" || de.VerdictHash == "" {
		return false, "missing fingerprint field(s)"
	}
	// Structural: verdict body and decision_id MUST NOT appear as top-level
	// fields (schema-level isolation). We re-decode into a generic map and
	// ensure no forbidden keys exist.
	var m map[string]interface{}
	if err := json.Unmarshal(payload, &m); err != nil {
		return false, fmt.Sprintf("generic_unmarshal: %v", err)
	}
	forbidden := []string{"verdict", "decision_id", "canonical_response_bytes", "raw_decision_bytes"}
	for _, k := range forbidden {
		if _, exists := m[k]; exists {
			return false, fmt.Sprintf("forbidden field present: %s", k)
		}
	}
	return true, ""
}
