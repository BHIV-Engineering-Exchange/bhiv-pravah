// multi_system_router_propagation.go (v14.5 Cross-System Propagation Layer)
//
// Adds two sibling methods to *MultiSystemRouter — strictly additive, no
// existing code paths are modified:
//
//   - WireDeterministicTargets(env) — replaces each in-chain target's handler
//     with a DeterministicHTTPRoutingHandler bound to the sealed envelope.
//     intent_layer is wired in digest-only mode (IntelligenceReadOnly=true)
//     so Sri Satya's Intelligence Layer receives fingerprint hashes only and
//     is NEVER part of the determinism chain.
//
//   - RoutePropagation(env) — iterates in-chain targets in a fixed order
//     (core_workflow → insightflow → bucket → intent_layer), invokes their
//     handlers in sequence, and enforces byte-equality via the handler's
//     returned *PropagationStopError. On the first chain break, remaining
//     in-chain targets receive a synthetic CHAIN_HALTED audit event and are
//     NOT invoked. Intent Layer failure is observed but does NOT halt the
//     chain (digest-only hop).
//
// This file does NOT touch the legacy RouteResult path — v13/v14.4 behavior
// is preserved. Callers opt into propagation semantics by calling
// RoutePropagation instead of RouteResult.

package main

import (
	"errors"
	"fmt"
	"os"
	"sort"
	"sync/atomic"
	"time"

	"github.com/google/uuid"
)

// PropagationChainOrder is the deterministic dispatch order for in-chain
// targets. The order is canonical so replay harness results are byte-stable
// across runs. core_workflow goes first (Raj's enforcement state), then
// insightflow (observability), then bucket (audit archival).
var PropagationChainOrder = []string{
	"core_workflow",
	"insightflow",
	"bucket",
}

// PropagationOffChainOrder is the dispatch order for off-chain targets. Its
// failures never halt the chain. Intent Layer is the only default entry.
var PropagationOffChainOrder = []string{
	"intent_layer",
}

// PropagationHopResult is the per-hop outcome record surfaced in the final
// PropagationResult. It is JSON-stable — suitable for the replay harness's
// proof_logs/propagation_replay_results.jsonl file.
type PropagationHopResult struct {
	Target        string `json:"target"`
	InChain       bool   `json:"in_chain"`
	DigestOnly    bool   `json:"digest_only,omitempty"`
	Delivered     bool   `json:"delivered"`
	ChainHalted   bool   `json:"chain_halted,omitempty"`
	Skipped       bool   `json:"skipped,omitempty"`
	ErrorCode     string `json:"error_code,omitempty"`
	Error         string `json:"error,omitempty"`
	LatencyNs     int64  `json:"latency_ns"`
	EventID       string `json:"event_id"`
	AttemptedAt   string `json:"attempted_at"`
	// v14.7: RetryAttempts = number of attempts performed for this hop
	// (1 = first attempt succeeded; >1 = transport retry was exercised).
	// PropagationStopError is never retried; this field distinguishes
	// benign transport jitter from hard determinism halts.
	RetryAttempts int `json:"retry_attempts,omitempty"`
}

// PropagationResult is returned by RoutePropagation. It describes the
// overall byte-equality outcome of a single envelope propagation pass.
type PropagationResult struct {
	TraceID          string                 `json:"trace_id"`
	CorrelationID    string                 `json:"correlation_id"`
	DecisionID       string                 `json:"decision_id"`
	ExecutionID      string                 `json:"execution_id"`
	ResponseHash     string                 `json:"response_hash"`
	ChainBindingHash string                 `json:"chain_binding_hash"`
	ChainHalted      bool                   `json:"chain_halted"`
	HaltHop          string                 `json:"halt_hop,omitempty"`
	HaltCode         string                 `json:"halt_code,omitempty"`
	Hops             []PropagationHopResult `json:"hops"`
	StartedAt        string                 `json:"started_at"`
	CompletedAt      string                 `json:"completed_at"`
	DurationNs       int64                  `json:"duration_ns"`
}

// AllInChainDelivered returns true iff every in-chain hop delivered
// successfully. Intent Layer (digest-only) delivery is not considered.
func (pr *PropagationResult) AllInChainDelivered() bool {
	if pr == nil {
		return false
	}
	for _, h := range pr.Hops {
		if !h.InChain {
			continue
		}
		if !h.Delivered || h.Skipped || h.ChainHalted {
			return false
		}
	}
	return true
}

// ================================================================
// DETERMINISTIC WIRING
// ================================================================

// WireDeterministicTargets replaces each target's handler with a
// DeterministicHTTPRoutingHandler bound to the given sealed envelope. The
// handler sends the envelope's canonical response bytes (for in-chain
// targets) or an IntelligenceDigestEvent (for digest-only targets) and
// verifies byte-equality via the ACK header.
//
// Target-to-env URL environment map mirrors WireProductionTargets. Targets
// without a configured URL are skipped (their existing simulation stub
// handler is preserved).
//
// The method also marks in-chain targets with InChain=true and the
// intent_layer target with IntelligenceReadOnly=true, so RoutePropagation
// can dispatch correctly.
//
// Returns the count of wired targets.
func (r *MultiSystemRouter) WireDeterministicTargets(env *PropagationEnvelope) int {
	if env == nil {
		return 0
	}

	authToken := os.Getenv("SARATHI_ROUTE_AUTH_TOKEN")
	maxConcurrency := parseIntEnv("SARATHI_ROUTE_MAX_CONCURRENT", 10)
	cbThreshold := parseIntEnv("SARATHI_ROUTE_CB_THRESHOLD", 5)
	requireAck := parseBoolEnv("SARATHI_ROUTE_REQUIRE_ACK", true)

	cbConfig := CircuitBreakerConfig{
		FailureThreshold:  cbThreshold,
		ResetTimeout:      30 * time.Second,
		HalfOpenMaxProbes: 2,
	}

	// targetEnvMap tells us where each downstream lives.
	// digestOnlyTargets selects which targets receive IntelligenceDigestEvent.
	targetEnvMap := map[string]string{
		"insightflow":   "SARATHI_ROUTE_INSIGHTFLOW_URL",
		"bucket":        "SARATHI_ROUTE_BUCKET_URL",
		"core_workflow": "SARATHI_ROUTE_CORE_URL",
		"intent_layer":  "SARATHI_ROUTE_INTENT_URL",
	}
	digestOnlyTargets := map[string]bool{
		"intent_layer": true,
	}
	// In-chain set = all targets except digest-only ones.
	inChainTargets := map[string]bool{
		"core_workflow": true,
		"insightflow":   true,
		"bucket":        true,
	}

	wired := 0
	r.mu.Lock()
	defer r.mu.Unlock()

	for targetName, envVar := range targetEnvMap {
		url := os.Getenv(envVar)
		if url == "" {
			continue
		}
		target, exists := r.targets[targetName]
		if !exists {
			continue
		}

		cfg := DeterministicHTTPRoutingConfig{
			HTTPRoutingConfig: HTTPRoutingConfig{
				TargetURL:      url,
				AuthToken:      authToken,
				Timeout:        time.Duration(target.TimeoutMs) * time.Millisecond,
				CircuitBreaker: cbConfig,
				MaxConcurrency: maxConcurrency,
			},
			RequireAckHashHeader: requireAck,
			AckHashHeader:        HeaderAckHash,
			IntelligenceReadOnly: digestOnlyTargets[targetName],
		}

		target.Handler = NewDeterministicHTTPRoutingHandler(targetName, env, cfg)
		target.InChain = inChainTargets[targetName]
		target.IntelligenceReadOnly = digestOnlyTargets[targetName]
		wired++
		fmt.Printf("  [Phase 14.5] Route-det '%s' → %s (in_chain=%t digest_only=%t)\n",
			targetName, url, target.InChain, target.IntelligenceReadOnly)
	}

	return wired
}

// InstallPropagationHandler forcibly installs a user-supplied handler for a
// given target (bypassing the URL-based wiring of WireDeterministicTargets).
// Used exclusively by the replay harness and fault-injection sim, which
// provide in-memory handlers rather than real HTTP endpoints.
//
// Returns true if the target existed and was updated.
func (r *MultiSystemRouter) InstallPropagationHandler(
	targetName string, handler RoutingHandler, inChain, digestOnly bool,
) bool {
	if handler == nil {
		return false
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	t, ok := r.targets[targetName]
	if !ok {
		return false
	}
	t.Handler = handler
	t.InChain = inChain
	t.IntelligenceReadOnly = digestOnly
	return true
}

// ================================================================
// PROPAGATION ROUTING
// ================================================================

// RoutePropagation dispatches the sealed envelope to all in-chain targets
// in PropagationChainOrder, then to all off-chain digest-only targets in
// PropagationOffChainOrder. It enforces byte-equality via the handler's
// returned *PropagationStopError.
//
// Chain-halt semantics:
//   - On first *PropagationStopError from an in-chain target, remaining
//     in-chain targets are marked chain_halted and NOT invoked.
//   - Off-chain (digest-only) targets are ALWAYS invoked regardless of
//     chain halt; their failures never halt the chain.
//
// Every hop — success, failure, skipped, halted — is recorded in the
// returned *PropagationResult and delivered to the router's AuditSink as a
// RoutingResult. The router's in-memory event log and per-target metrics
// are updated identically to the legacy RouteResult path.
func (r *MultiSystemRouter) RoutePropagation(env *PropagationEnvelope) (*PropagationResult, error) {
	if env == nil {
		return nil, fmt.Errorf("propagation: envelope is nil")
	}

	started := time.Now().UTC()
	result := &PropagationResult{
		TraceID:          env.TraceID(),
		CorrelationID:    env.CorrelationID(),
		DecisionID:       env.DecisionID(),
		ExecutionID:      env.ExecutionID(),
		ResponseHash:     env.ResponseHash(),
		ChainBindingHash: env.ChainBindingHash(),
		StartedAt:        started.Format("2006-01-02T15:04:05.000000Z"),
		Hops:             make([]PropagationHopResult, 0, 8),
	}

	// Snapshot targets under read lock; we dispatch without holding the
	// router-wide lock to avoid blocking other callers.
	r.mu.RLock()
	snapshot := make(map[string]*RoutingTarget, len(r.targets))
	for k, v := range r.targets {
		snapshot[k] = v
	}
	r.mu.RUnlock()

	atomic.AddUint64(&r.totalRouted, 1)

	// Phase A: In-chain dispatch. Halt on first *PropagationStopError.
	chainHalted := false
	for _, name := range PropagationChainOrder {
		target, ok := snapshot[name]
		if !ok || !target.Active {
			result.Hops = append(result.Hops, PropagationHopResult{
				Target:      name,
				InChain:     true,
				Skipped:     true,
				ErrorCode:   "TARGET_MISSING_OR_INACTIVE",
				EventID:     uuid.New().String(),
				AttemptedAt: time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
			})
			continue
		}

		if chainHalted {
			// Remaining in-chain targets get a synthetic CHAIN_HALTED event
			// rather than being silently dropped — downstream audit must see
			// that propagation stopped here.
			hop := PropagationHopResult{
				Target:      name,
				InChain:     true,
				ChainHalted: true,
				ErrorCode:   CodePropagationChainBroken,
				Error:       fmt.Sprintf("chain halted at hop=%s code=%s", result.HaltHop, result.HaltCode),
				EventID:     uuid.New().String(),
				AttemptedAt: time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
			}
			result.Hops = append(result.Hops, hop)
			r.emitRoutingAudit(name, false, hop.Error, 0, 0)
			atomic.AddUint64(&r.totalSkipped, 1)
			continue
		}

		hop := r.invokePropagationHop(name, target, env, true, false)
		result.Hops = append(result.Hops, hop)
		r.bumpTargetMetrics(name, hop.Delivered)
		r.emitRoutingAudit(name, hop.Delivered, hop.Error, hop.LatencyNs, 0)

		if hop.Delivered {
			atomic.AddUint64(&r.totalDelivered, 1)
			continue
		}
		// In-chain failure — check whether it's a determinism break.
		if hop.ErrorCode == CodeDeterminismViolation ||
			hop.ErrorCode == CodeResponseHashMismatch ||
			hop.ErrorCode == CodePropagationByteMismatch ||
			hop.ErrorCode == CodePropagationChainBroken {
			chainHalted = true
			result.ChainHalted = true
			result.HaltHop = name
			result.HaltCode = hop.ErrorCode
		}
		atomic.AddUint64(&r.totalFailed, 1)
	}

	// Phase B: Off-chain (digest-only) dispatch. Always runs regardless of
	// chain halt; failures are observed but never mutate chainHalted.
	for _, name := range PropagationOffChainOrder {
		target, ok := snapshot[name]
		if !ok || !target.Active {
			continue
		}
		hop := r.invokePropagationHop(name, target, env, false, target.IntelligenceReadOnly)
		result.Hops = append(result.Hops, hop)
		r.bumpTargetMetrics(name, hop.Delivered)
		r.emitRoutingAudit(name, hop.Delivered, hop.Error, hop.LatencyNs, 0)

		if hop.Delivered {
			atomic.AddUint64(&r.totalDelivered, 1)
		} else {
			atomic.AddUint64(&r.totalFailed, 1)
		}
	}

	// Any extra active targets not in either canonical list — dispatch in a
	// stable (sorted) order so audit records are reproducible. They are
	// classified as off-chain since the canonical lists are the source of
	// truth for in-chain membership.
	extraNames := make([]string, 0)
	known := map[string]bool{}
	for _, n := range PropagationChainOrder {
		known[n] = true
	}
	for _, n := range PropagationOffChainOrder {
		known[n] = true
	}
	for name, t := range snapshot {
		if known[name] || !t.Active {
			continue
		}
		extraNames = append(extraNames, name)
	}
	sort.Strings(extraNames)
	for _, name := range extraNames {
		target := snapshot[name]
		hop := r.invokePropagationHop(name, target, env, target.InChain, target.IntelligenceReadOnly)
		result.Hops = append(result.Hops, hop)
		r.bumpTargetMetrics(name, hop.Delivered)
		r.emitRoutingAudit(name, hop.Delivered, hop.Error, hop.LatencyNs, 0)
		if hop.Delivered {
			atomic.AddUint64(&r.totalDelivered, 1)
		} else {
			atomic.AddUint64(&r.totalFailed, 1)
		}
	}

	completed := time.Now().UTC()
	result.CompletedAt = completed.Format("2006-01-02T15:04:05.000000Z")
	result.DurationNs = completed.Sub(started).Nanoseconds()
	return result, nil
}

// invokePropagationHop runs a single target's handler and maps its error
// (if any) to a *PropagationHopResult. This helper centralises the
// error-code extraction so both in-chain and off-chain dispatch produce
// identical record shapes.
func (r *MultiSystemRouter) invokePropagationHop(
	name string, target *RoutingTarget, env *PropagationEnvelope,
	inChain, digestOnly bool,
) PropagationHopResult {
	hop := PropagationHopResult{
		Target:      name,
		InChain:     inChain,
		DigestOnly:  digestOnly,
		EventID:     uuid.New().String(),
		AttemptedAt: time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
	}
	if target == nil || target.Handler == nil {
		hop.ErrorCode = "HANDLER_MISSING"
		hop.Error = fmt.Sprintf("target '%s' has no handler", name)
		return hop
	}

	// Build a minimal RoutedEvent for logging parity with RouteResult.
	// The deterministic handler reads the envelope directly — this
	// event carries the bookkeeping fields.
	event := &RoutedEvent{
		EventID:         hop.EventID,
		EventType:       r.classifyPropagationEventType(digestOnly),
		Source:          "sarathi/propagation",
		Timestamp:       time.Now().UTC(),
		ContentType:     "application/json",
		CorrelationID:   env.CorrelationID(),
		Verdict:         env.Verdict(),
		EnforcementHash: env.EnforcementHash(),
	}

	// v14.7 Phase 3: honour target.RetryCount for transport-level failures
	// ONLY. A PropagationStopError is a deterministic halt (byte mismatch,
	// hash mismatch, decision drift) and MUST NOT be retried — retrying
	// would mask real divergence and violate INV-PROP-04. Retries apply
	// only to the generic, non-stop error branch below.
	maxAttempts := target.RetryCount
	if maxAttempts < 0 {
		maxAttempts = 0
	}
	start := time.Now()
	var err error
	var pse *PropagationStopError
	attempt := 0
	for attempt = 0; attempt <= maxAttempts; attempt++ {
		err = target.Handler(event)
		if err == nil {
			break
		}
		if errors.As(err, &pse) {
			break
		}
		if attempt < maxAttempts {
			// Linear backoff, capped at 250ms * attempt.
			sleep := time.Duration(attempt+1) * 50 * time.Millisecond
			if sleep > 250*time.Millisecond {
				sleep = 250 * time.Millisecond
			}
			time.Sleep(sleep)
		}
	}
	hop.LatencyNs = time.Since(start).Nanoseconds()
	hop.RetryAttempts = attempt

	if err == nil {
		hop.Delivered = true
		return hop
	}

	// Error taxonomy: recover *PropagationStopError if present, else parse
	// the error string prefix (same shape as NewHTTPRoutingHandler emits).
	if errors.As(err, &pse) {
		hop.ErrorCode = pse.Code
		hop.Error = pse.Error()
		return hop
	}
	hop.ErrorCode = extractErrorCodePrefix(err.Error())
	hop.Error = err.Error()
	return hop
}

// classifyPropagationEventType mirrors the legacy classifyEventType shape
// but emits a propagation-aware type string. Digest-only hops get a distinct
// type so the Intelligence Layer can filter on it without parsing the body.
func (r *MultiSystemRouter) classifyPropagationEventType(digestOnly bool) string {
	if digestOnly {
		return "sarathi.propagation.digest"
	}
	return "sarathi.propagation.hop"
}

// bumpTargetMetrics updates per-target delivered/failed counters using the
// same mutex the legacy path uses, so metrics remain consistent whether a
// target is routed via RouteResult or RoutePropagation.
func (r *MultiSystemRouter) bumpTargetMetrics(name string, delivered bool) {
	r.targetMetricsMu.Lock()
	defer r.targetMetricsMu.Unlock()
	if delivered {
		r.targetDelivered[name]++
	} else {
		r.targetFailed[name]++
	}
}

// emitRoutingAudit pushes a RoutingResult record onto the router's audit
// sink and ring-buffer log — parity with RouteResult's internal bookkeeping
// so proof logs reconcile cleanly.
func (r *MultiSystemRouter) emitRoutingAudit(name string, delivered bool, errStr string, latencyNs int64, retries int) {
	rr := RoutingResult{
		TargetName: name,
		Delivered:  delivered,
		Error:      errStr,
		LatencyNs:  latencyNs,
		Retries:    retries,
	}
	r.eventLogMu.Lock()
	if len(r.eventLog) >= r.maxLogSize {
		r.eventLog = r.eventLog[1:]
	}
	r.eventLog = append(r.eventLog, rr)
	r.eventLogMu.Unlock()

	if r.auditSink != nil {
		// AuditSink is best-effort — never surface its error.
		_ = r.emitToAuditSink(rr)
	}
}

// emitToAuditSink wraps auditSink.Write with a defensive no-panic bound.
// Kept separate so behaviour can evolve without touching the hot path.
func (r *MultiSystemRouter) emitToAuditSink(rr RoutingResult) (retErr error) {
	defer func() {
		if rec := recover(); rec != nil {
			retErr = fmt.Errorf("audit sink panic: %v", rec)
		}
	}()
	// NOTE: the audit sink interface varies across versions; we only call
	// it here in the few shapes that are always present. If neither shape
	// is implemented, the write is silently skipped — parity with legacy
	// RouteResult.
	if typed, ok := interface{}(r.auditSink).(interface {
		WriteRoutingResult(RoutingResult) error
	}); ok {
		return typed.WriteRoutingResult(rr)
	}
	return nil
}

// extractErrorCodePrefix returns the leading all-caps identifier of an error
// message, e.g. "BULKHEAD_FULL" from "BULKHEAD_FULL: target 'x' ...". If no
// prefix matches, returns "".
func extractErrorCodePrefix(s string) string {
	if s == "" {
		return ""
	}
	// Scan for the first ':' and check if everything before is A-Z0-9_.
	end := -1
	for i := 0; i < len(s); i++ {
		c := s[i]
		if c == ':' {
			end = i
			break
		}
		if !(c == '_' || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')) {
			return ""
		}
	}
	if end <= 0 {
		return ""
	}
	return s[:end]
}

// parseBoolEnv reads a boolean from an environment variable. "1", "true",
// "yes" (case-insensitive) → true; unset or empty → dflt. Any other value
// → false.
func parseBoolEnv(name string, dflt bool) bool {
	v := os.Getenv(name)
	if v == "" {
		return dflt
	}
	switch v {
	case "1", "true", "TRUE", "True", "yes", "YES", "Yes":
		return true
	}
	return false
}
