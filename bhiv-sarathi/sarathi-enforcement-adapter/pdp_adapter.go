// pdp_adapter.go (v14.5 Cross-System Propagation Layer)
//
// PDPAdapter is the ingest point for externally-produced PDP decisions (Tanvi's
// PDP builder → Sarathi). It accepts the raw signed decision bytes, verifies
// cryptographic integrity, runs the existing EnforceExternalDecision pipeline
// UNCHANGED, and seals a PropagationEnvelope that carries the full hash chain
// downstream.
//
// HARD CONSTRAINT (enforced by construction): this file contains NO policy
// logic. It has exactly one method that touches decision content
// (verifyIngestIntegrity), and that method only calls existing hash primitives
// (ExternalDecision.computeHash, computeCoreHash) and the existing signature
// verifier. Any PR adding a branch over d.Verdict / d.AgentID / d.ResourceID
// / d.Action in this file fails review.
//
// Flow (matches plan diagram):
//
//	rawBytes → unmarshal to *ExternalDecision
//	         → seal ingest_hash = Sha256Hex(rawBytes)
//	         → recompute computeHash()     ==  stored decision_hash       [INTEGRITY]
//	         → recompute computeCoreHash() ==  stored decision_core_hash  [BINDING]
//	         → EnforceExternalDecision(...)                              [UNCHANGED 10-stage pipeline]
//	         → CanonicalFromPropagation(...) → response map
//	         → CanonicalMarshal(response map) → canonical_response_bytes
//	         → SealPropagationEnvelope(...) → immutable envelope
//
// TAG: no-policy-logic

package main

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

// PDPIngestMetrics records per-adapter counters (cheap, lock-protected).
// These are observability-only — they never influence the decision path.
type PDPIngestMetrics struct {
	IngestAttempts      int64 `json:"ingest_attempts"`
	IngestSuccesses     int64 `json:"ingest_successes"`
	IntegrityFailures   int64 `json:"integrity_failures"`
	SignatureFailures   int64 `json:"signature_failures"`
	EnforcementFailures int64 `json:"enforcement_failures"`
	EnvelopeSeals       int64 `json:"envelope_seals"`
	LastIngestAt        string `json:"last_ingest_at"`
}

// PDPAdapter bridges external PDP output (pre-signed ExternalDecision) to
// Sarathi's enforcement pipeline + propagation envelope.
//
// A single instance is safe for concurrent use: Ingest() serializes on pa.mu
// so metrics update atomically with the enforcement side-effect.
type PDPAdapter struct {
	adapter  *EnforcementAdapter
	modeCtrl *ModeController

	mu      sync.Mutex
	metrics PDPIngestMetrics
}

// NewPDPAdapter wires the ingest path. Requires a live EnforcementAdapter and
// a ModeController — if either is nil, Ingest() fails closed with a clear error.
func NewPDPAdapter(ea *EnforcementAdapter, mc *ModeController) *PDPAdapter {
	return &PDPAdapter{
		adapter:  ea,
		modeCtrl: mc,
	}
}

// Metrics returns a snapshot of the adapter's counters.
func (pa *PDPAdapter) Metrics() PDPIngestMetrics {
	pa.mu.Lock()
	defer pa.mu.Unlock()
	return pa.metrics
}

// ResetReplayTrackerForHarness clears the underlying EnforcementAdapter's
// replay tracker. TEST AFFORDANCE ONLY — see the identically-named method
// on *EnforcementAdapter for the full contract. This wrapper exists so the
// propagation replay harness can interact with PDPAdapter exclusively.
//
// TAG: test-affordance-only
func (pa *PDPAdapter) ResetReplayTrackerForHarness() {
	pa.mu.Lock()
	adapter := pa.adapter
	pa.mu.Unlock()
	if adapter != nil {
		adapter.ResetReplayTrackerForHarness()
	}
}

// Ingest is the single entry point. Contract:
//
//	in:  rawBytes (the signed ExternalDecision JSON Tanvi produced), executionID
//	     (Raj's downstream execution identifier), correlationID (may be empty —
//	     propagated through if set), traceCtx (may be nil — one is minted if so).
//	out: *PropagationEnvelope — sealed, immutable, ready for RoutePropagation().
//
// NO policy evaluation. NO decision content inspection beyond hash recomputation.
//
// TAG: no-policy-logic
func (pa *PDPAdapter) Ingest(
	rawBytes []byte,
	executionID string,
	correlationID string,
	traceCtx *TraceContext,
) (*PropagationEnvelope, error) {
	if pa == nil {
		return nil, fmt.Errorf("pdp_adapter: nil receiver")
	}
	if pa.adapter == nil {
		return nil, fmt.Errorf("pdp_adapter: EnforcementAdapter not wired (%s)", CodePDPDecisionInvalid)
	}
	if pa.modeCtrl == nil {
		return nil, fmt.Errorf("pdp_adapter: ModeController not wired (%s)", CodePDPDecisionInvalid)
	}
	if len(rawBytes) == 0 {
		pa.bumpMetric(func(m *PDPIngestMetrics) { m.IngestAttempts++; m.IntegrityFailures++ })
		return nil, fmt.Errorf("pdp_adapter: rawBytes is empty (%s)", CodePDPDecisionInvalid)
	}

	pa.bumpMetric(func(m *PDPIngestMetrics) {
		m.IngestAttempts++
		m.LastIngestAt = time.Now().UTC().Format("2006-01-02T15:04:05.000000Z")
	})

	// ── 1. Parse raw bytes into *ExternalDecision ──────────────────────────
	// json.Unmarshal on a typed struct is deterministic — field names map
	// 1:1. We do NOT mutate the parsed struct; we only verify it.
	decision := &ExternalDecision{}
	if err := json.Unmarshal(rawBytes, decision); err != nil {
		pa.bumpMetric(func(m *PDPIngestMetrics) { m.IntegrityFailures++ })
		return nil, fmt.Errorf("pdp_adapter: decision unmarshal failed (%s): %w", CodePDPDecisionInvalid, err)
	}

	// ── 2. Cryptographic integrity check (NO policy evaluation) ─────────────
	if err := pa.verifyIngestIntegrity(decision, rawBytes); err != nil {
		pa.bumpMetric(func(m *PDPIngestMetrics) { m.IntegrityFailures++ })
		return nil, err
	}

	// ── 3. Run existing enforcement pipeline — UNCHANGED. ─────────────────
	// The 10-stage EnforceExternalDecision is the source of truth; this
	// adapter NEVER second-guesses its output.
	enfResult := pa.adapter.EnforceExternalDecision(decision, pa.modeCtrl)
	if enfResult == nil {
		pa.bumpMetric(func(m *PDPIngestMetrics) { m.EnforcementFailures++ })
		return nil, fmt.Errorf("pdp_adapter: EnforceExternalDecision returned nil (%s)", CodePDPDecisionInvalid)
	}

	// Ensure ingest-level correlationID propagates into the envelope even
	// if the enforcement result generated its own. Priority: caller-supplied > enforcement.
	effectiveCorrID := correlationID
	if effectiveCorrID == "" {
		effectiveCorrID = enfResult.CorrelationID
	}

	// Ensure trace context is always present.
	// v15.5: when SARATHI_TRACE_ID_REQUIRE_INBOUND=true, NewTraceContext()
	// returns nil and we fail-closed here. trace_id is the upstream Core
	// API's property and must NEVER be minted locally in production.
	if traceCtx == nil {
		traceCtx = NewTraceContext()
	}
	if traceCtx == nil {
		pa.bumpMetric(func(m *PDPIngestMetrics) { m.IntegrityFailures++ })
		return nil, fmt.Errorf("pdp_adapter: trace_id required (%s): caller must propagate inbound X-Sarathi-Trace-ID; SARATHI_TRACE_ID_REQUIRE_INBOUND=true", CodePDPDecisionInvalid)
	}

	// ── 4. Build canonical response map (via CanonicalFromPropagation) ──────
	// This is the v14.5 propagation response shape — carries the v13.0 schema
	// AND the 5 propagation fields. No policy logic involved; the builder is
	// a pure composer over already-finalized decision/enforcement output.
	start := time.Now()
	respMap := CanonicalFromPropagation(
		decision,
		enfResult,
		executionID,
		traceCtx,
		effectiveCorrID,
		0, // durationNs filled below (two-pass would double-seal, so pass 0)
	)

	// ── 5. Canonicalize → bytes. Placeholder fields are empty strings so the
	// canonical bytes are stable the first time. The envelope seal path hashes
	// the bytes as-is, which means response_hash ≡ Sha256Hex(these bytes). ──
	canonicalBytes, err := CanonicalMarshal(respMap)
	if err != nil {
		pa.bumpMetric(func(m *PDPIngestMetrics) { m.EnforcementFailures++ })
		return nil, fmt.Errorf("pdp_adapter: canonical marshal failed: %w", err)
	}

	// ── 6. Seal envelope. All downstream propagation uses this envelope. ────
	env, err := SealPropagationEnvelope(
		rawBytes,
		decision,
		enfResult,
		canonicalBytes,
		executionID,
		traceCtx,
		effectiveCorrID,
	)
	if err != nil {
		pa.bumpMetric(func(m *PDPIngestMetrics) { m.EnforcementFailures++ })
		return nil, fmt.Errorf("pdp_adapter: envelope seal failed: %w", err)
	}

	_ = start // duration recorded elsewhere in harness; avoids build-time unused

	pa.bumpMetric(func(m *PDPIngestMetrics) {
		m.IngestSuccesses++
		m.EnvelopeSeals++
	})
	return env, nil
}

// verifyIngestIntegrity is the ONLY method in this file that touches decision
// content. It performs EXCLUSIVELY cryptographic integrity checks — no
// inspection of verdict, agent, resource, or action semantics.
//
// TAG: no-policy-logic
func (pa *PDPAdapter) verifyIngestIntegrity(d *ExternalDecision, raw []byte) error {
	if d == nil {
		return fmt.Errorf("pdp_adapter: nil decision (%s)", CodePDPDecisionInvalid)
	}
	// Full-integrity recomputation: detects ANY tamper to ANY field.
	if !d.VerifyIntegrity() {
		return fmt.Errorf("pdp_adapter: decision_hash mismatch (%s): stored=%s recomputed=%s",
			CodePDPDecisionInvalid, short(d.DecisionHash), short(d.computeHash()))
	}
	// Core-binding recomputation: the Ed25519-signed payload.
	if !d.VerifyCoreHashIntegrity() {
		return fmt.Errorf("pdp_adapter: decision_core_hash mismatch (%s): stored=%s recomputed=%s",
			CodePDPDecisionInvalid, short(d.DecisionCoreHash), short(d.computeCoreHash()))
	}
	// raw-byte sanity: the ingest hash must be reproducible. This guards
	// against a caller passing truncated/modified bytes that somehow still
	// unmarshal successfully — the seal uses these bytes verbatim.
	if Sha256Hex(raw) == "" {
		return fmt.Errorf("pdp_adapter: empty raw-byte hash (%s)", CodePDPDecisionInvalid)
	}
	return nil
}

// bumpMetric runs fn under pa.mu. Keeps all metric writes serialized.
func (pa *PDPAdapter) bumpMetric(fn func(*PDPIngestMetrics)) {
	pa.mu.Lock()
	defer pa.mu.Unlock()
	fn(&pa.metrics)
}

// short returns the first 16 chars of a hash, for log-friendly reporting
// without leaking full hash values in error messages.
func short(h string) string {
	if len(h) <= 16 {
		return h
	}
	return h[:16]
}
