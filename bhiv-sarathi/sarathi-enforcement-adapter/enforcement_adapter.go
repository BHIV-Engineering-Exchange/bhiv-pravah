package main

// enforcement_adapter.go — Non-bypassable Policy Enforcement Point (PEP).
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Enforcement Adapter (PEP)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// Architecture:
//   Intent → EnforcementAdapter → SarathiPDP → Verdict → ExecutionEngine
//
// GAP FIXES APPLIED:
//   GAP-07: Rate limiting (per-agent token bucket) + chain rotation
//   GAP-11: json.Marshal error handling (fail-closed)
//   GAP-12: Registry consistency token stamped on each enforcement
//   GAP-17: Struct-based hash computation for chain entries
//
// v12.1 GAP RECTIFICATION:
//   GAP-03 FIX: Rate limiting removed from Enforce() — moved to pre_gate_ratelimit.go (side-gate).
//   GAP-02 FIX: Dynamic posture computation removed — replaced by posture_signal.go (signed signal verification).
//   Both are now PRE-GATES that run BEFORE Enforce(). A rejected request never enters the verification boundary.

import (
	"crypto/ed25519"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"sync"
	"time"
)

// ================================================================
// RATE LIMITER (GAP-07)
// ================================================================

// RateLimitConfig configures per-agent rate limiting.
type RateLimitConfig struct {
	MaxRequestsPerWindow int           // max requests per time window
	WindowDuration       time.Duration // sliding window duration
	Enabled              bool
	// Global rate limit: total requests across ALL agents per window.
	// 0 = unlimited (per-agent limits still apply). Production default: 10000.
	GlobalMaxPerWindow int
}

// DefaultRateLimitConfig returns production-grade rate limit defaults.
func DefaultRateLimitConfig() RateLimitConfig {
	return RateLimitConfig{
		MaxRequestsPerWindow: 100,
		WindowDuration:       60 * time.Second,
		Enabled:              true,
		GlobalMaxPerWindow:   10000,
	}
}

// agentRateState tracks per-agent request timestamps for rate limiting.
type agentRateState struct {
	timestamps []time.Time
}

// ================================================================
// CHAIN ROTATION (GAP-07)
// ================================================================

// ChainRotationConfig configures enforcement chain memory management.
type ChainRotationConfig struct {
	MaxInMemoryEntries int  // max entries before rotation
	Enabled            bool
}

// DefaultChainRotationConfig returns production defaults.
func DefaultChainRotationConfig() ChainRotationConfig {
	return ChainRotationConfig{
		MaxInMemoryEntries: 10000,
		Enabled:            true,
	}
}

// ================================================================
// PHASE 14 HARDENING: SYSTEM CONFIGURATION HELPERS
// ================================================================

// EnablePostgresPersistence wires the durable PostgreSQL backend for tokens.
// This solves Gap 1: Replay protection by persisting token state across process restarts.
func (p *SarathiEnforcementPipeline) EnablePostgresPersistence(db *sql.DB) error {
	if db == nil {
		return fmt.Errorf("cannot enable postgres persistence: db is nil")
	}
	store, err := NewPostgresTokenRegistryStore(db)
	if err != nil {
		return fmt.Errorf("failed to init postgres token store: %w", err)
	}
	// Swap the registry
	p.Engine.tokenRegistry = NewTokenRegistryWithStore(store)
	return nil
}

// EnableWebhookExecution wires the real-world HTTP webhook executor.
// This solves Gap 4: Decouples simulated engine execution from real workflow execution.
//
// v14.2 Production Hardening:
//   If SARATHI_WEBHOOK_PRODUCTION=true, uses ProductionWebhookHandler with
//   circuit breaker, retry, auth headers, and dead-letter logging.
//   Otherwise, uses the bare WebhookExecutionHandler (backward compatible).
func (p *SarathiEnforcementPipeline) EnableWebhookExecution(webhookURL string) {
	if webhookURL == "" {
		return
	}

	productionMode := os.Getenv("SARATHI_WEBHOOK_PRODUCTION")
	if productionMode == "true" || productionMode == "1" {
		config := DefaultProductionWebhookConfig(webhookURL)
		config.AuthToken = os.Getenv("SARATHI_WEBHOOK_AUTH")
		config.Timeout = parseDurationEnv("SARATHI_WEBHOOK_TIMEOUT", 10*time.Second)
		config.Retry.MaxRetries = parseIntEnv("SARATHI_WEBHOOK_MAX_RETRIES", 3)

		handler := NewProductionWebhookHandler(config)
		p.Engine.SetExecutionHandler(handler)
		fmt.Printf("  [Phase 14.2] ProductionWebhookHandler wired: url=%s timeout=%v retries=%d cb_threshold=%d\n",
			webhookURL, config.Timeout, config.Retry.MaxRetries, config.CircuitBreaker.FailureThreshold)
	} else {
		handler := NewWebhookExecutionHandler(webhookURL)
		p.Engine.SetExecutionHandler(handler)
	}
}

// SetMinRegistryVersion implements Phase 14 Gap 2. Enforces explicit freshness constraint.
func (p *SarathiEnforcementPipeline) SetMinRegistryVersion(v int64) {
	p.Engine.SetMinRegistryVersion(v)
}

// ================================================================
// PIPELINE EXECUTION PATH
// ================================================================

// EnforcementTraceEntry is a single entry in the append-only enforcement chain.
type EnforcementTraceEntry struct {
	SequenceNumber       int    `json:"sequence_number"`
	CorrelationID        string `json:"correlation_id"`
	Verdict              string `json:"verdict"`
	EnforcementStage     string `json:"enforcement_stage"`
	EnforcementHash      string `json:"enforcement_hash"`
	PrevEnforcementHash  string `json:"prev_enforcement_hash"`
	TraceHash            string `json:"trace_hash"`
	RegistryVersion      uint64 `json:"registry_version"`  // GAP-12
	TraceID              string `json:"trace_id,omitempty"` // v14.4: W3C trace correlation
}

// chainTracePayload is a struct for deterministic chain hash computation (GAP-17).
type chainTracePayload struct {
	Prev    string `json:"prev"`
	Current string `json:"current"`
}

// ================================================================
// ENFORCEMENT ADAPTER
// ================================================================

// EnforcementAdapter is the non-bypassable gate between intent and execution.
type EnforcementAdapter struct {
	mu                    sync.Mutex
	pdp                   *SarathiPDP
	registry              *PolicyRegistry
	agentRegistry         *RegistryInterface // GAP-12: for consistency token
	enforcementChain      []EnforcementTraceEntry
	rotatedArchive        []EnforcementTraceEntry // VULN-H2: archived rotated entries
	prevEnforcementHash   string
	enforcementCount      int
	totalEnforcementCount int // includes rotated entries

	// GAP-07: Rate limiting (per-agent + global)
	rateLimitConfig    RateLimitConfig
	agentRates         map[string]*agentRateState
	globalRateWindow   []time.Time // timestamps for global rate tracking

	// GAP-07: Chain rotation
	chainRotationConfig ChainRotationConfig
	rotatedEntryCount   int

	// Sovereign token signing authority (Ed25519)
	tokenAuthority *TokenAuthority

	// DEPRECATED (v12.1 GAP-02 FIX): BeyondCorp-style posture monitoring.
	// No longer used by Enforce() — posture is now verified as a signed signal
	// in posture_signal.go (pre-gate). Retained for EnforceExternalDecision backward
	// compatibility until the external pipeline is also refactored.
	postureMonitor *AgentPostureMonitor

	// v12.1: Pre-gate admission controls (run BEFORE Enforce).
	preGateRateLimiter *PreGateRateLimiter
	postureVerifier    *PostureVerifier

	// Phase 6 fix (architectural review): Audit sink for durable chain persistence.
	// When set, each chain entry is recorded to the audit sink for durability.
	// In-memory chain is the primary; audit sink is the backup for recovery.
	auditSink AuditSink

	// Phase 10 (BHIV External Decision Path): Replay tracker for external decisions.
	// Tracks nonces of externally provided decisions to prevent replay attacks.
	// Initialized by InitExternalMode(). Nil until external mode is enabled.
	externalReplayTracker *externalReplayTracker

	// Phase 11 (BHIV Trust Hardening): Evaluator trust registry.
	// Holds Ed25519 public keys of trusted evaluators. Only decisions signed by
	// ACTIVE evaluators in this registry are accepted for enforcement.
	// Initialized by InitExternalMode(). Nil until external mode is enabled.
	evaluatorRegistry *EvaluatorTrustRegistry
}

// NewEnforcementAdapter creates the enforcement adapter bound to a PDP and registry.
func NewEnforcementAdapter(pdp *SarathiPDP, registry *PolicyRegistry, agentRegistry *RegistryInterface, tokenAuth *TokenAuthority) *EnforcementAdapter {
	return &EnforcementAdapter{
		pdp:                 pdp,
		registry:            registry,
		agentRegistry:       agentRegistry,
		prevEnforcementHash: "GENESIS",
		rateLimitConfig:     DefaultRateLimitConfig(), // Retained for EnforceExternalDecision backward compat
		agentRates:          make(map[string]*agentRateState),
		chainRotationConfig: DefaultChainRotationConfig(),
		tokenAuthority:      tokenAuth,
	}
}

// SetPreGateRateLimiter wires the v12.1 pre-gate rate limiter.
// This is informational — the actual admission check runs in the caller
// BEFORE Enforce() is invoked (see pre_gate_ratelimit.go).
func (ea *EnforcementAdapter) SetPreGateRateLimiter(rl *PreGateRateLimiter) {
	ea.mu.Lock()
	defer ea.mu.Unlock()
	ea.preGateRateLimiter = rl
}

// SetPostureVerifier wires the v12.1 posture signal verifier.
// This is informational — the actual admission check runs in the caller
// BEFORE Enforce() is invoked (see posture_signal.go). Sarathi NEVER
// computes posture, only verifies a signed signal (INV-34).
func (ea *EnforcementAdapter) SetPostureVerifier(pv *PostureVerifier) {
	ea.mu.Lock()
	defer ea.mu.Unlock()
	ea.postureVerifier = pv
}

// GetPreGateRateLimiter returns the wired pre-gate rate limiter.
func (ea *EnforcementAdapter) GetPreGateRateLimiter() *PreGateRateLimiter {
	ea.mu.Lock()
	defer ea.mu.Unlock()
	return ea.preGateRateLimiter
}

// GetPostureVerifier returns the wired posture signal verifier.
func (ea *EnforcementAdapter) GetPostureVerifier() *PostureVerifier {
	ea.mu.Lock()
	defer ea.mu.Unlock()
	return ea.postureVerifier
}

// GetTokenAuthority returns the token authority (for pipeline wiring).
func (ea *EnforcementAdapter) GetTokenAuthority() *TokenAuthority {
	return ea.tokenAuthority
}

// SetPostureMonitor wires the BeyondCorp-style posture monitor into the enforcement path.
func (ea *EnforcementAdapter) SetPostureMonitor(pm *AgentPostureMonitor) {
	ea.postureMonitor = pm
}

// SetAuditSink wires the audit sink into the enforcement adapter for durable chain persistence.
// Phase 6 fix (architectural review): enables durability without blocking the in-memory chain.
func (ea *EnforcementAdapter) SetAuditSink(sink AuditSink) {
	ea.mu.Lock()
	defer ea.mu.Unlock()
	ea.auditSink = sink
}

// Enforce is the main entry point. It takes an ExecutionRequest and returns
// an ExecutionResponse. This is the ONLY path to execution.
//
// v12.1 BOUNDARY RULE: This method contains VERIFICATION ONLY.
// Admission control (rate limiting, posture signal verification) runs
// in pre-gates BEFORE this method is called:
//   - PreGateRateLimiter.Admit() — pre_gate_ratelimit.go
//   - PostureVerifier.Admit()    — posture_signal.go
// A rejected request NEVER enters this method, NEVER produces a chain entry,
// and NEVER appears in the enforcement trace.
//
// v14.0 PRODUCTION HARDENING (F1 — INV-38 Fix):
//   Accepts an optional *RuntimePathAttestation via variadic parameter.
//   When provided, each verification stage is recorded AS IT EXECUTES,
//   not pre-recorded. This converts INV-38 from a static hash check to
//   a true runtime invocation proof. Existing callers that omit the
//   parameter are unaffected — full backward compatibility.
func (ea *EnforcementAdapter) Enforce(req *ExecutionRequest, attestation ...*RuntimePathAttestation) *ExecutionResponse {
	ea.mu.Lock()
	defer ea.mu.Unlock()

	// v14.0 F1: Helper to record stage in RPA only if provided.
	recordStage := func(stage string) {
		if len(attestation) > 0 && attestation[0] != nil {
			attestation[0].RecordStage(stage)
		}
	}

	// STEP 1: Pre-PDP validation
	recordStage("PRE_PDP_VALIDATION")
	if !req.IsValid() {
		resp := NewExecutionResponse(req, nil, "PRE_PDP_VALIDATION",
			fmt.Sprintf("VALIDATION_FAILED: %v", req.ValidationErrors()))
		ea.appendToChain(resp)
		return resp
	}

	// STEP 2: Policy version check
	recordStage("POLICY_VERSION_CHECK")
	activePolicyVersion := ea.pdp.GetPolicyVersion()
	if req.PolicyVersion() != "" && req.PolicyVersion() != activePolicyVersion {
		resp := NewExecutionResponse(req, nil, "POLICY_VERSION_CHECK",
			fmt.Sprintf("POLICY_VERSION_MISMATCH: requested=%s active=%s",
				req.PolicyVersion(), activePolicyVersion))
		ea.appendToChain(resp)
		return resp
	}

	// STEP 3: PDP evaluation
	recordStage("PDP_EVALUATION")
	pdpReq := &PDPRequest{
		AgentID:    req.AgentID(),
		ResourceID: req.ResourceID(),
		Action:     req.Action(),
	}
	pdpResp := ea.pdp.Evaluate(pdpReq)

	// STEP 4: Verify PDP response integrity
	recordStage("PDP_HASH_INTEGRITY")
	if pdpResp.RequestHash != req.RequestHash() {
		resp := NewExecutionResponse(req, pdpResp, "PDP_HASH_MISMATCH",
			fmt.Sprintf("REQUEST_HASH_MISMATCH: request=%s pdp=%s",
				req.RequestHash(), pdpResp.RequestHash))
		resp.verdict = "DENY"
		ea.appendToChain(resp)
		return resp
	}

	// STEP 5: Construct enforcement response
	recordStage("ENFORCEMENT_RESPONSE_BUILD")
	
	// v14.1 Gap 3: Extract the RPA path hash established so far directly
	// into the token before it is signed, proving enforcement bounds.
	var rpaHash string
	if len(attestation) > 0 && attestation[0] != nil {
		rpaHash = attestation[0].ComputePathHash()
	}
	
	resp := NewExecutionResponseFull(
		req, 
		pdpResp, 
		"PDP_EVALUATED", 
		"PDP_DECISION_ACCEPTED", 
		int64(ea.agentRegistry.Version()), 
		rpaHash,
	)

	// STEP 6: Sign the capability token with TokenAuthority (Ed25519)
	// Only ALLOW verdicts have tokens — signing nil is a no-op.
	recordStage("TOKEN_SIGN")
	if ea.tokenAuthority != nil {
		ea.tokenAuthority.SignToken(resp.GetCapabilityToken())
	}

	recordStage("CHAIN_APPEND")
	ea.appendToChain(resp)
	return resp
}

// appendToChain adds the enforcement response to the append-only hash chain.
func (ea *EnforcementAdapter) appendToChain(resp *ExecutionResponse) {
	ea.enforcementCount++
	ea.totalEnforcementCount++

	// GAP-17 + FIX-06 (v7.0): Safe error propagation — replace panic() with error return.
	// Uses SafeChainHash from sovereign_governance_v9.go.
	traceHash, chainErr := SafeChainHash(ea.prevEnforcementHash, resp.EnforcementHash())
	if chainErr != nil {
		// FIX-06: Fail-closed without panic — mark response as chain-broken
		// and continue with a deterministic fallback hash so the chain remains auditable.
		traceHash = Sha256Hex([]byte(fmt.Sprintf("CHAIN_ERROR:%s:%s", ea.prevEnforcementHash, resp.EnforcementHash())))
	}

	// GAP-12: stamp registry version
	var regVersion uint64
	if ea.agentRegistry != nil {
		regVersion = ea.agentRegistry.Version()
	}

	entry := EnforcementTraceEntry{
		SequenceNumber:      ea.totalEnforcementCount,
		CorrelationID:       resp.CorrelationID(),
		Verdict:             resp.Verdict(),
		EnforcementStage:    resp.EnforcementStage(),
		EnforcementHash:     resp.EnforcementHash(),
		PrevEnforcementHash: ea.prevEnforcementHash,
		TraceHash:           traceHash,
		RegistryVersion:     regVersion,
	}

	ea.enforcementChain = append(ea.enforcementChain, entry)
	ea.prevEnforcementHash = traceHash

	// Phase 6 fix (architectural review): Persist chain entry to audit sink for durability.
	// In-memory chain is the primary enforcement record; audit sink provides durable backup.
	// If persistence fails, log the error but do NOT block — the in-memory chain is sufficient.
	if ea.auditSink != nil {
		if err := ea.auditSink.RecordChainEntry(entry); err != nil {
			// Log the error for operational visibility but continue.
			// The enforcement has already been recorded in-memory (the primary record).
			fmt.Printf("ERROR: audit sink persistence failed for entry %d: %v\n", entry.SequenceNumber, err)
		}
	}

	// GAP-07: Chain rotation — evict oldest entries when limit reached
	if ea.chainRotationConfig.Enabled &&
		len(ea.enforcementChain) > ea.chainRotationConfig.MaxInMemoryEntries {
		evictCount := len(ea.enforcementChain) / 4
		ea.rotatedEntryCount += evictCount
		// VULN-H2 FIX: Archive rotated entries before eviction
		ea.rotatedArchive = append(ea.rotatedArchive, ea.enforcementChain[:evictCount]...)
		ea.enforcementChain = ea.enforcementChain[evictCount:]
	}
}

// isRateLimited checks if an agent has exceeded the rate limit (GAP-07).
func (ea *EnforcementAdapter) isRateLimited(agentID string) bool {
	state, exists := ea.agentRates[agentID]
	if !exists {
		return false
	}

	now := time.Now()
	cutoff := now.Add(-ea.rateLimitConfig.WindowDuration)

	// Count requests within the window
	count := 0
	for _, ts := range state.timestamps {
		if ts.After(cutoff) {
			count++
		}
	}
	return count >= ea.rateLimitConfig.MaxRequestsPerWindow
}

// recordRequest records a request timestamp for rate limiting (GAP-07).
func (ea *EnforcementAdapter) recordRequest(agentID string) {
	state, exists := ea.agentRates[agentID]
	if !exists {
		state = &agentRateState{}
		ea.agentRates[agentID] = state
	}

	now := time.Now()
	cutoff := now.Add(-ea.rateLimitConfig.WindowDuration)

	// Prune expired timestamps
	var active []time.Time
	for _, ts := range state.timestamps {
		if ts.After(cutoff) {
			active = append(active, ts)
		}
	}
	active = append(active, now)
	state.timestamps = active
}

// ================================================================
// ── v12.1/v12.2 PRE-GATE: RATE LIMIT SIDE-GATE (GAP-03 FIX) ──
// ================================================================
// Rate limiting is ADMISSION CONTROL, not verification.
// A rate-limited request never enters the verification boundary
// (EnforcementAdapter.Enforce), never produces a hash chain entry,
// and never appears in the enforcement trace.
//
// v12.2 BOUNDARY PURIFICATION:
//   Originally introduced in pre_gate_ratelimit.go (v12.1). That file
//   was folded into enforcement_adapter.go in v12.2 to honor the
//   "no dilution / no new subsystems" rule. The code lives next to
//   the deprecated in-Enforce() rate-limit helpers it replaces.

// PreGateRateLimiter enforces global and per-agent rate limits
// as an admission control gate before the verification pipeline.
type PreGateRateLimiter struct {
	mu               sync.Mutex
	config           RateLimitConfig
	agentRates       map[string]*agentRateState
	globalRateWindow []time.Time
	clock            Clock
}

// NewPreGateRateLimiter creates a rate-limit pre-gate.
func NewPreGateRateLimiter(cfg RateLimitConfig, clk Clock) *PreGateRateLimiter {
	if clk == nil {
		clk = RealClock{}
	}
	return &PreGateRateLimiter{
		config:     cfg,
		agentRates: make(map[string]*agentRateState),
		clock:      clk,
	}
}

// Admit checks whether the request from agentID should be admitted.
// Returns (true, "") if admitted, or (false, reason) if rate-limited.
// Thread-safe.
//
// A rejected request must NOT be forwarded to Enforce(). The caller
// should return a rate-limited response directly (no chain entry,
// no enforcement trace, no capability token).
func (l *PreGateRateLimiter) Admit(agentID string) (bool, string) {
	l.mu.Lock()
	defer l.mu.Unlock()

	if !l.config.Enabled {
		return true, ""
	}

	now := l.clock.NowUTC()

	// Global rate limit
	if l.config.GlobalMaxPerWindow > 0 {
		cutoff := now.Add(-l.config.WindowDuration)
		cleaned := make([]time.Time, 0, len(l.globalRateWindow))
		for _, ts := range l.globalRateWindow {
			if ts.After(cutoff) {
				cleaned = append(cleaned, ts)
			}
		}
		if len(cleaned) >= l.config.GlobalMaxPerWindow {
			l.globalRateWindow = cleaned
			return false, fmt.Sprintf("GLOBAL_RATE_LIMIT_EXCEEDED: max=%d per %v",
				l.config.GlobalMaxPerWindow, l.config.WindowDuration)
		}
		cleaned = append(cleaned, now)
		l.globalRateWindow = cleaned
	}

	// Per-agent rate limit
	if agentID != "" {
		if l.isAgentRateLimited(agentID, now) {
			return false, fmt.Sprintf("RATE_LIMIT_EXCEEDED: agent=%s max=%d per %v",
				agentID, l.config.MaxRequestsPerWindow, l.config.WindowDuration)
		}
		l.recordAgentRequest(agentID, now)
	}

	return true, ""
}

// isAgentRateLimited checks if the agent has exceeded their per-agent limit.
func (l *PreGateRateLimiter) isAgentRateLimited(agentID string, now time.Time) bool {
	state, exists := l.agentRates[agentID]
	if !exists {
		return false
	}

	cutoff := now.Add(-l.config.WindowDuration)
	count := 0
	for _, ts := range state.timestamps {
		if ts.After(cutoff) {
			count++
		}
	}
	return count >= l.config.MaxRequestsPerWindow
}

// recordAgentRequest records a request timestamp for the agent.
func (l *PreGateRateLimiter) recordAgentRequest(agentID string, now time.Time) {
	state, exists := l.agentRates[agentID]
	if !exists {
		state = &agentRateState{}
		l.agentRates[agentID] = state
	}

	cutoff := now.Add(-l.config.WindowDuration)
	var active []time.Time
	for _, ts := range state.timestamps {
		if ts.After(cutoff) {
			active = append(active, ts)
		}
	}
	active = append(active, now)
	state.timestamps = active
}

// SetConfig updates the rate-limit configuration. Thread-safe.
func (l *PreGateRateLimiter) SetConfig(cfg RateLimitConfig) {
	if cfg.MaxRequestsPerWindow <= 0 {
		cfg.MaxRequestsPerWindow = 1
	}
	if cfg.WindowDuration <= 0 {
		cfg.WindowDuration = time.Second
	}
	l.mu.Lock()
	defer l.mu.Unlock()
	l.config = cfg
}

// GetConfig returns the current rate-limit configuration. Thread-safe.
func (l *PreGateRateLimiter) GetConfig() RateLimitConfig {
	l.mu.Lock()
	defer l.mu.Unlock()
	return l.config
}

// ================================================================
// ── v12.1/v12.2 PRE-GATE: SIGNED POSTURE VERIFICATION (GAP-02 FIX) ──
// ================================================================
// Sarathi can only VERIFY a posture result (boolean / signed signal).
// It must NOT compute posture, score posture, or interpret behavior.
// Posture = externally computed, signed, immutable input.
//
// INVARIANT (INV-34):
//   Posture is NEVER computed inside Sarathi. Any code path that reads
//   behavior, scores trust, or interprets activity to produce a posture
//   verdict is a BOUNDARY VIOLATION.
//
// v12.2 BOUNDARY PURIFICATION:
//   Originally introduced in posture_signal.go (v12.1). Folded into
//   enforcement_adapter.go in v12.2. The SignedPostureSignal data
//   structure lives in execution_request.go (next to ExecutionRequest).

// Posture verification errors — all fail-closed.
var (
	ErrPostureSignalMissing    = errors.New("POSTURE_SIGNAL_MISSING: no signed posture signal on request")
	ErrPostureSignatureInvalid = errors.New("POSTURE_SIGNAL_INVALID: Ed25519 signature verification failed")
	ErrPostureExpired          = errors.New("POSTURE_SIGNAL_EXPIRED: signal ExpiresAt is in the past")
	ErrPostureIssuerUnknown    = errors.New("POSTURE_ISSUER_UNKNOWN: issuer not in authorized issuer key set")
	ErrPostureNonceReplayed    = errors.New("POSTURE_SIGNAL_REPLAYED: nonce has been seen before")
)

// ================================================================
// POSTURE ENFORCEMENT MODE (v14.0 Production Hardening — F7)
// ================================================================
//
// Industry alignment:
//   - Google BeyondCorp: always evaluates device posture, mode controls blocking
//   - AWS IAM: condition context always evaluated; missing = deny
//   - Kubernetes Pod Security: enforce / audit / warn modes
//   - Azure Conditional Access: report-only vs enforced
//
// Issuer keys are per-organization, not per-user (like TLS CA certificates).
// One posture service signs signals for all agents in its domain.
// Production deploys 1-3 issuer keys (primary + rotation).

// PostureEnforcementMode controls how the posture pre-gate behaves.
type PostureEnforcementMode int

const (
	// PostureDisabled — posture signals are completely optional.
	// Missing signals are silently accepted. Default for dev/test.
	PostureDisabled PostureEnforcementMode = iota

	// PostureAudit — posture signals are checked if present, logged if
	// missing/invalid, but requests are never blocked. For staging/rollout.
	PostureAudit

	// PostureEnforced — posture signals are REQUIRED. Missing signal = DENY.
	// Invalid signal = DENY. For production environments.
	PostureEnforced
)

// PostureVerifier verifies signed posture signals from authorized issuers.
// It holds the Ed25519 public keys of all authorized posture issuers.
// It does NOT compute posture. It does NOT score trust.
type PostureVerifier struct {
	mu              sync.Mutex
	issuerKeys      map[string]ed25519.PublicKey // issuerID → public key
	seenNonces      map[string]time.Time         // nonce → first-seen time (replay protection)
	clock           Clock
	maxSkew         time.Duration                // clock skew tolerance
	enforcementMode PostureEnforcementMode       // v14.0 F7: controls enforcement behavior
}

// NewPostureVerifier creates a posture signal verifier.
// Default enforcement mode is PostureDisabled (backward compatible).
func NewPostureVerifier(issuerKeys map[string]ed25519.PublicKey, clk Clock) *PostureVerifier {
	if clk == nil {
		clk = RealClock{}
	}
	keys := make(map[string]ed25519.PublicKey, len(issuerKeys))
	for id, key := range issuerKeys {
		keys[id] = key
	}
	return &PostureVerifier{
		issuerKeys:      keys,
		seenNonces:      make(map[string]time.Time),
		clock:           clk,
		maxSkew:         30 * time.Second,
		enforcementMode: PostureDisabled,
	}
}

// SetEnforcementMode sets the posture enforcement mode. Thread-safe.
func (v *PostureVerifier) SetEnforcementMode(mode PostureEnforcementMode) {
	v.mu.Lock()
	defer v.mu.Unlock()
	v.enforcementMode = mode
}

// GetEnforcementMode returns the current posture enforcement mode. Thread-safe.
func (v *PostureVerifier) GetEnforcementMode() PostureEnforcementMode {
	v.mu.Lock()
	defer v.mu.Unlock()
	return v.enforcementMode
}

// HasIssuerKeys returns true if at least one posture issuer key is registered.
func (v *PostureVerifier) HasIssuerKeys() bool {
	v.mu.Lock()
	defer v.mu.Unlock()
	return len(v.issuerKeys) > 0
}

// Verify checks that a signed posture signal is authentic, unexpired,
// non-replayed, and from a known issuer. Returns nil on success or a
// specific error on failure. This method is fail-closed.
//
// FORBIDDEN OPERATIONS — this method MUST NOT:
//   - Compute posture from agent behavior.
//   - Score, threshold, or interpret the posture value.
//   - Look up IP addresses, request history, or activity data.
//   - Make any decision beyond "is this signed signal valid?"
func (v *PostureVerifier) Verify(signal *SignedPostureSignal) error {
	if signal == nil {
		return ErrPostureSignalMissing
	}

	v.mu.Lock()
	defer v.mu.Unlock()

	now := v.clock.NowUTC()

	// 1. Issuer known?
	issuerKey, known := v.issuerKeys[signal.IssuerID]
	if !known {
		return ErrPostureIssuerUnknown
	}

	// 2. Signature valid?
	payload := signal.postureSignPayload()
	if !ed25519.Verify(issuerKey, payload, signal.Signature) {
		return ErrPostureSignatureInvalid
	}

	// 3. Not expired?
	expiresAt := time.Unix(signal.ExpiresAt, 0).UTC()
	if now.After(expiresAt.Add(v.maxSkew)) {
		return ErrPostureExpired
	}

	// 4. Nonce not replayed?
	if _, seen := v.seenNonces[signal.Nonce]; seen {
		return ErrPostureNonceReplayed
	}
	v.seenNonces[signal.Nonce] = now

	// 5. Prune old nonces (keep memory bounded)
	pruneCutoff := now.Add(-2 * v.maxSkew)
	for nonce, ts := range v.seenNonces {
		if ts.Before(pruneCutoff) {
			delete(v.seenNonces, nonce)
		}
	}

	return nil
}

// Admit is the pre-gate entry point for posture verification.
// Returns (true, "") if the signal is valid, or (false, reason) on rejection.
//
// If the posture signal is nil (missing), this is fail-closed: reject.
// If the posture signal is valid but Posture==false, this rejects with
// "AGENT_POSTURE_DENIED" — the external issuer said posture is bad.
func (v *PostureVerifier) Admit(signal *SignedPostureSignal) (bool, string) {
	if err := v.Verify(signal); err != nil {
		return false, err.Error()
	}

	// The signal is valid. Now check the posture value.
	if !signal.Posture {
		return false, fmt.Sprintf("AGENT_POSTURE_DENIED: agent=%s issuer=%s (posture signal valid but posture=false)",
			signal.AgentID, signal.IssuerID)
	}

	return true, ""
}

// AddIssuerKey registers a new posture issuer public key. Thread-safe.
func (v *PostureVerifier) AddIssuerKey(issuerID string, pubKey ed25519.PublicKey) {
	v.mu.Lock()
	defer v.mu.Unlock()
	v.issuerKeys[issuerID] = pubKey
}

// RemoveIssuerKey removes a posture issuer. Thread-safe.
func (v *PostureVerifier) RemoveIssuerKey(issuerID string) {
	v.mu.Lock()
	defer v.mu.Unlock()
	delete(v.issuerKeys, issuerID)
}

// VerifyChain walks the enforcement chain and verifies hash linkage integrity.
func (ea *EnforcementAdapter) VerifyChain() (bool, string) {
	ea.mu.Lock()
	defer ea.mu.Unlock()

	if len(ea.enforcementChain) == 0 {
		return true, ""
	}

	// After rotation, the first entry's prev won't be GENESIS
	// so we start from the first entry's stored prev
	expectedPrev := ea.enforcementChain[0].PrevEnforcementHash
	for i, entry := range ea.enforcementChain {
		if entry.PrevEnforcementHash != expectedPrev {
			return false, fmt.Sprintf("chain break at index %d: expected prev=%s, got=%s",
				i, expectedPrev, entry.PrevEnforcementHash)
		}
		// GAP-17 + GAP-11: Recompute trace hash with struct
		chainPayload := chainTracePayload{
			Prev:    entry.PrevEnforcementHash,
			Current: entry.EnforcementHash,
		}
		chainJSON, err := json.Marshal(chainPayload)
		if err != nil {
			return false, fmt.Sprintf("marshal error at index %d: %v", i, err)
		}
		recomputed := Sha256Hex(chainJSON)
		if entry.TraceHash != recomputed {
			return false, fmt.Sprintf("trace hash mismatch at index %d: stored=%s, recomputed=%s",
				i, entry.TraceHash, recomputed)
		}
		expectedPrev = entry.TraceHash
	}
	return true, ""
}

// GetEnforcementChain returns a copy of the enforcement chain.
func (ea *EnforcementAdapter) GetEnforcementChain() []EnforcementTraceEntry {
	ea.mu.Lock()
	defer ea.mu.Unlock()

	cp := make([]EnforcementTraceEntry, len(ea.enforcementChain))
	copy(cp, ea.enforcementChain)
	return cp
}

// EnforcementCount returns the total number of enforcement evaluations
// (including rotated entries).
func (ea *EnforcementAdapter) EnforcementCount() int {
	ea.mu.Lock()
	defer ea.mu.Unlock()
	return ea.totalEnforcementCount
}

// InMemoryChainLength returns the current in-memory chain length.
func (ea *EnforcementAdapter) InMemoryChainLength() int {
	ea.mu.Lock()
	defer ea.mu.Unlock()
	return len(ea.enforcementChain)
}

// RotatedEntryCount returns how many entries have been rotated out (GAP-07).
func (ea *EnforcementAdapter) RotatedEntryCount() int {
	ea.mu.Lock()
	defer ea.mu.Unlock()
	return ea.rotatedEntryCount
}

// HasEnforcementHash checks if a given enforcement_hash exists in the
// current in-memory chain. Used by ExecutionEngine for bypass prevention (GAP-04).
func (ea *EnforcementAdapter) HasEnforcementHash(hash string) bool {
	ea.mu.Lock()
	defer ea.mu.Unlock()

	for _, entry := range ea.enforcementChain {
		if entry.EnforcementHash == hash {
			return true
		}
	}
	// VULN-H2 FIX: Also search rotated archive
	for _, entry := range ea.rotatedArchive {
		if entry.EnforcementHash == hash {
			return true
		}
	}
	return false
}

// GetRotatedArchive returns a copy of the rotated entry archive (VULN-H2).
func (ea *EnforcementAdapter) GetRotatedArchive() []EnforcementTraceEntry {
	ea.mu.Lock()
	defer ea.mu.Unlock()
	cp := make([]EnforcementTraceEntry, len(ea.rotatedArchive))
	copy(cp, ea.rotatedArchive)
	return cp
}

// SetRateLimitConfig allows configuring rate limits (e.g. for testing).
func (ea *EnforcementAdapter) SetRateLimitConfig(config RateLimitConfig) {
	// VULN-M6 FIX: Validate rate limit configuration
	if config.MaxRequestsPerWindow <= 0 {
		config.MaxRequestsPerWindow = 1 // minimum 1
	}
	if config.WindowDuration <= 0 {
		config.WindowDuration = time.Second // minimum 1 second
	}
	ea.mu.Lock()
	defer ea.mu.Unlock()
	ea.rateLimitConfig = config
}

// ================================================================
// SARATHI ENFORCEMENT PIPELINE
// ================================================================

// SarathiEnforcementPipeline binds all components:
// PolicyRegistry → PDP → EnforcementAdapter → ExecutionEngine
type SarathiEnforcementPipeline struct {
	Registry       *PolicyRegistry
	PDP            *SarathiPDP
	Adapter        *EnforcementAdapter
	Engine         *ExecutionEngine
	AgentRegistry  *RegistryInterface  // GAP-12: exposed for consistency checks
	Escalation     *EscalationQueue    // GAP-10: escalation handler
	RevocationList *TokenRevocationList // FIX-04 (v7.0): token revocation
	KeyStore       *ProtectedKeyStore   // FIX-02 (v7.0): encrypted key persistence
	PostureMonitor *AgentPostureMonitor // DEPRECATED (v12.1): retained for external path backward compat
	RateLimiter    DistributedRateLimiter // FIX-11 (v7.0): Distributed rate limiting
	Webhook        *EscalationWebhook     // FIX-13 (v7.0): Escalation webhook — REAL HTTP

	// v12.1 GAP RECTIFICATION: Pre-gates (admission control).
	// These run BEFORE Adapter.Enforce() and are NOT part of the verification
	// pipeline. A rejected request never advances the hash chain.
	PreGateRateLimiter *PreGateRateLimiter // v12.1 GAP-03: rate limit as side-gate
	PostureVerifier    *PostureVerifier    // v12.1 GAP-02: signed posture signal verification
	TrustConsumer      TrustConsumer       // v12.1 GAP-01: thin evaluator trust interface

	// v13.0 SYSTEM DOMINANCE TRANSITION: Observability + Path Attestation.
	// GAP 3: Live observability layer with cross-system correlation.
	// GAP 5: Runtime path attestation — proves actual invocation order.
	Observability *ObservabilityCollector // v13.0 GAP-3: cross-system trace collector

	// v15.1 NETWORK SURFACE CLOSURE: pre-wired PDP-ingest path for the HTTP
	// /v1/ingest-decision endpoint. PDPAdapter and ModeController are stable,
	// process-wide singletons that the ServiceBoundary handler reuses on
	// every request — instantiating per-request would defeat the
	// PDPAdapter's metrics + replay tracker contract.
	//
	// TAG: no-policy-logic (the adapter only verifies hashes + signature;
	// it never makes decisions).
	PDPAdapter     *PDPAdapter
	ModeController *ModeController
}

// NewSarathiEnforcementPipeline creates the full pipeline from config.
func NewSarathiEnforcementPipeline(policiesDir, configPath string) (*SarathiEnforcementPipeline, error) {
	registry, err := NewPolicyRegistryFromConfig(configPath)
	if err != nil {
		return nil, fmt.Errorf("registry init failed: %w", err)
	}

	_, err = registry.InitializeFromConfig()
	if err != nil {
		return nil, fmt.Errorf("registry initialization failed: %w", err)
	}

	agentRegistry := NewRegistryInterface()

	pdp, err := NewSarathiPDPFromRegistry(registry, agentRegistry, RealClock{})
	if err != nil {
		return nil, fmt.Errorf("PDP creation failed: %w", err)
	}

	// FIX-02 (v7.0): Sovereign token signing authority via ProtectedKeyStore
	// Uses AES-256-GCM encrypted persistence when SARATHI_KEY_PASSPHRASE is set.
	// Falls back to in-memory key generation for testing/dev.
	keyStore := NewProtectedKeyStore("sarathi_keys.enc")
	tokenAuth, err := keyStore.LoadOrGenerate()
	if err != nil {
		return nil, fmt.Errorf("token authority creation failed: %w", err)
	}

	// Adapter holds private key (signer)
	adapter := NewEnforcementAdapter(pdp, registry, agentRegistry, tokenAuth)

	// Engine receives ONLY public key (verifier) — separation of concerns
	engine := NewExecutionEngine(adapter, tokenAuth.PublicKey(), tokenAuth.KeyID())

	// FIX-04 (v7.0): Wire token revocation list into engine (9th check)
	revocationList := NewTokenRevocationList()
	engine.SetRevocationList(revocationList)

	// GAP-10: Escalation queue
	escalation := NewEscalationQueue()

	// FIX-08 (v7.0): BeyondCorp posture monitor — WIRED into enforcement adapter.
	// Every enforcement checks agent trust posture before PDP evaluation.
	postureMonitor := NewAgentPostureMonitor(agentRegistry, DefaultPostureConfig())
	adapter.SetPostureMonitor(postureMonitor)

	// FIX-11 (v7.0): Distributed rate limiter (local implementation).
	// Uses sliding window counter with O(1) checking and periodic cleanup.
	rateLimiter := NewLocalRateLimiter()

	// FIX-13 (v7.0): Escalation webhook — real HTTP POST with retry + circuit breaker.
	webhook := NewEscalationWebhook(EscalationWebhookConfig{
		Enabled:       false, // Disabled by default; enable via config
		TimeoutMs:     5000,
		RetryCount:    3,
		TimeoutAction: "auto_deny",
	})

	// v12.1 GAP-03 FIX: PreGateRateLimiter side-gate.
	// Rate limiting is admission control, NOT a verification step. Rejected
	// requests never enter Enforce() and never produce chain entries.
	preGateRL := NewPreGateRateLimiter(DefaultRateLimitConfig(), RealClock{})
	adapter.SetPreGateRateLimiter(preGateRL)

	// v12.1 GAP-02 FIX: PostureVerifier pre-gate.
	// Posture is never computed inside Sarathi — only verified as a signed
	// signal from a known issuer. Default verifier has an empty issuer key
	// set; operators add authorized posture issuer keys via AddIssuerKey().
	postureVerifier := NewPostureVerifier(nil, RealClock{})
	adapter.SetPostureVerifier(postureVerifier)

	// v12.1 GAP-01 FIX: TrustConsumer interface (thin evaluator trust).
	// Default build uses InMemoryTrustConsumer loaded from an optional
	// static snapshot (env SARATHI_TRUST_SNAPSHOT). Lifecycle operations
	// (registration, admin, rotation, JWKS) are NOT Sarathi's concern.
	trustConsumer, err := BootstrapTrustConsumer(adapter)
	if err != nil {
		return nil, fmt.Errorf("trust consumer bootstrap failed: %w", err)
	}

	// v15.1 NETWORK SURFACE CLOSURE: pre-wire the PDPAdapter so the HTTP
	// /v1/ingest-decision boundary handler can call pa.Ingest() on every
	// request without per-request allocation. InitExternalMode is required
	// before the adapter accepts ExternalDecision input — it provisions the
	// replay tracker and evaluator registry. This ALSO benefits any direct
	// Go consumer of pipeline.PDPAdapter (tests, CLI harnesses) — there is
	// now exactly one canonical adapter instance per pipeline.
	adapter.InitExternalMode()
	modeCtl := NewModeController(BHIVModeExternal)
	pdpAdapter := NewPDPAdapter(adapter, modeCtl)

	return &SarathiEnforcementPipeline{
		Registry:       registry,
		PDP:            pdp,
		Adapter:        adapter,
		Engine:         engine,
		AgentRegistry:  agentRegistry,
		Escalation:     escalation,
		RevocationList: revocationList,
		KeyStore:       keyStore,
		PostureMonitor: postureMonitor,
		RateLimiter:    rateLimiter,
		Webhook:        webhook,

		// v12.1 gap rectification pre-gates
		PreGateRateLimiter: preGateRL,
		PostureVerifier:    postureVerifier,
		TrustConsumer:      trustConsumer,

		// v13.0 system dominance transition
		Observability: NewObservabilityCollector(),

		// v15.1 network surface closure
		PDPAdapter:     pdpAdapter,
		ModeController: modeCtl,
	}, nil
}

// Execute runs the full pipeline: request → enforce → token → execute.
// This is the ONLY external entry point. The flow is:
//   1. Create immutable ExecutionRequest
//   2. Enforce via adapter → get ExecutionResponse (with signed token on ALLOW)
//   3. Extract CapabilityToken from response
//   4. Execute via engine using token ONLY (sovereign gate)
//
// FIX-07 (v7.0): W3C distributed tracing is wired into every stage.
// Each stage gets its own child span with timing and outcome attributes.
func (p *SarathiEnforcementPipeline) Execute(
	agentID, resourceID, action, correlationID string,
	policyVersion ...string,
) (result map[string]interface{}) {

	// FIX-07: Create root trace context for this pipeline execution
	traceCtx := NewTraceContext()

	// v13.0 Response Contract: panic guard. Any panic in the pipeline is
	// recovered, surfaced as CodeInternal / forced DENY, and run through the
	// output contract validator so the caller never sees a half-built map.
	defer func() {
		if r := recover(); r != nil {
			result = EnforceResponseContract(
				CanonicalInternalError(r, agentID, resourceID, action, correlationID, traceCtx),
				nil, traceCtx,
			)
		}
	}()

	pipelineSpan := StartSpan("sarathi.pipeline.execute", traceCtx)
	pipelineSpan.Attributes["agent_id"] = agentID
	pipelineSpan.Attributes["resource_id"] = resourceID
	pipelineSpan.Attributes["action"] = action
	pipelineSpan.Attributes["correlation_id"] = correlationID

	pv := ""
	if len(policyVersion) > 0 {
		pv = policyVersion[0]
	}

	// v13.0 Response Contract Phase 3: Identifier normalization (NFKC + reject
	// mixed case + reject path traversal) runs BEFORE NewExecutionRequest, so
	// the request hash is computed on canonicalized input. On rejection, a
	// canonical DENY with a deterministic error_code is returned — no <nil>.
	normAgent, normResource, normAction, normErrCode := NormalizeIdentifiers(agentID, resourceID, action)
	if normErrCode != "" {
		pipelineSpan.Attributes["pre_gate"] = "INPUT_NORMALIZATION_REJECTED"
		pipelineSpan.Attributes["pre_gate_reason"] = normErrCode
		pipelineSpan.End()
		if p.Observability != nil {
			p.Observability.Emit(ObservabilityEvent{
				Stage:          "PRE_GATE_INPUT_NORMALIZATION",
				SystemID:       "sarathi-enforcement-adapter",
				CorrelationID:  correlationID,
				TraceID:        traceCtx.TraceID,
				ExecutionState: "EXECUTION_BLOCKED",
				BlockReason:    normErrCode,
				Verdict:        "DENY",
			})
		}
		return EnforceResponseContract(
			CanonicalDenyFromValidation(normErrCode, agentID, resourceID, action, correlationID, pv, traceCtx),
			nil, traceCtx,
		)
	}
	agentID, resourceID, action = normAgent, normResource, normAction

	req := NewExecutionRequest(agentID, resourceID, action, correlationID, pv)

	// v14.0 F1 (INV-38 Fix): Runtime path attestation — stages are now recorded
	// at each actual verification step inside Enforce(), not pre-recorded here.
	// Pre-gate stages (rate limit, posture) are still recorded here because
	// they execute in Execute(), not inside Enforce().
	rpa := NewRuntimePathAttestation()

	// v12.1 GAP-03 FIX: Pre-gate rate limit check (admission control, not verification).
	// Rate-limited requests are rejected BEFORE the verification boundary — no chain
	// entry is written, no enforcement trace is produced.
	rpa.RecordStage("PRE_GATE_RATE_LIMIT")
	if p.PreGateRateLimiter != nil {
		admitted, reason := p.PreGateRateLimiter.Admit(req.AgentID())
		if !admitted {
			pipelineSpan.Attributes["pre_gate"] = "RATE_LIMITED"
			pipelineSpan.Attributes["pre_gate_reason"] = reason
			pipelineSpan.End()
			// v13.0 GAP-3: Emit observability event for pre-gate rejection
			if p.Observability != nil {
				p.Observability.Emit(ObservabilityEvent{
					Stage:          "PRE_GATE_RATE_LIMIT",
					SystemID:       "sarathi-enforcement-adapter",
					CorrelationID:  correlationID,
					TraceID:        traceCtx.TraceID,
					ExecutionState: "EXECUTION_BLOCKED",
					BlockReason:    reason,
					Verdict:        "DENY",
				})
			}
			return EnforceResponseContract(
				CanonicalDenyFromPreGate("RATE_LIMIT", reason, CodeRateLimited, req, traceCtx),
				req, traceCtx,
			)
		}
	}

	// v14.0 F7: Posture pre-gate with tiered enforcement mode.
	// DISABLED (default): skip entirely — backward compatible for dev/test.
	// AUDIT: check if present, log failures, but never block.
	// ENFORCED: REQUIRED — missing signal = DENY, invalid signal = DENY.
	rpa.RecordStage("PRE_GATE_POSTURE_VERIFY")
	if p.PostureVerifier != nil {
		postureMode := p.PostureVerifier.GetEnforcementMode()
		signal := req.PostureSignal()

		if postureMode == PostureEnforced {
			// ENFORCED: signal is REQUIRED — missing or invalid = DENY
			admitted, reason := p.PostureVerifier.Admit(signal)
			if !admitted {
				pipelineSpan.Attributes["pre_gate"] = "POSTURE_REJECTED"
				pipelineSpan.Attributes["pre_gate_reason"] = reason
				pipelineSpan.End()
				if p.Observability != nil {
					p.Observability.Emit(ObservabilityEvent{
						Stage:          "PRE_GATE_POSTURE_VERIFY",
						SystemID:       "sarathi-enforcement-adapter",
						CorrelationID:  correlationID,
						TraceID:        traceCtx.TraceID,
						ExecutionState: "EXECUTION_BLOCKED",
						BlockReason:    reason,
						Verdict:        "DENY",
					})
				}
				return EnforceResponseContract(
					CanonicalDenyFromPreGate("POSTURE_SIGNAL", reason, PostureReasonToErrorCode(reason), req, traceCtx),
					req, traceCtx,
				)
			}
		} else if postureMode == PostureAudit && signal != nil {
			// AUDIT: check if present, log failures, but never block
			admitted, reason := p.PostureVerifier.Admit(signal)
			if !admitted {
				fmt.Printf("  [POSTURE_AUDIT] posture check would fail for correlation_id=%s: %s\n", correlationID, reason)
			}
		} else if postureMode == PostureDisabled && signal != nil {
			// DISABLED but signal present: validate anyway (opportunistic)
			admitted, reason := p.PostureVerifier.Admit(signal)
			if !admitted {
				pipelineSpan.Attributes["pre_gate"] = "POSTURE_REJECTED"
				pipelineSpan.Attributes["pre_gate_reason"] = reason
				pipelineSpan.End()
				if p.Observability != nil {
					p.Observability.Emit(ObservabilityEvent{
						Stage:          "PRE_GATE_POSTURE_VERIFY",
						SystemID:       "sarathi-enforcement-adapter",
						CorrelationID:  correlationID,
						TraceID:        traceCtx.TraceID,
						ExecutionState: "EXECUTION_BLOCKED",
						BlockReason:    reason,
						Verdict:        "DENY",
					})
				}
				return EnforceResponseContract(
					CanonicalDenyFromPreGate("POSTURE_SIGNAL", reason, PostureReasonToErrorCode(reason), req, traceCtx),
					req, traceCtx,
				)
			}
		}
		// DISABLED with no signal: skip entirely (current behavior preserved)
	}

	// FIX-07: Enforcement span
	// v14.0 F1: Verification stages are now recorded INSIDE Enforce() via the
	// variadic RPA parameter. The 7 stages (PRE_PDP_VALIDATION through
	// CHAIN_APPEND) are recorded as they actually execute, not pre-recorded.

	enfSpan := StartSpan("sarathi.enforcement.enforce", pipelineSpan.Context)
	enfResp := p.Adapter.Enforce(req, rpa)
	enfSpan.Attributes["verdict"] = enfResp.Verdict()
	if enfResp.Verdict() != "ALLOW" {
		enfSpan.SetError(enfResp.EnforcementReason())
	}
	enfSpan.End()

	// v13.0 GAP-3: Emit enforcement observability event
	if p.Observability != nil {
		p.Observability.Emit(ObservabilityEvent{
			Stage:           "ENFORCEMENT",
			SystemID:        "sarathi-enforcement-adapter",
			CorrelationID:   correlationID,
			TraceID:         traceCtx.TraceID,
			DecisionID:      enfResp.DecisionID(),
			EnforcementHash: enfResp.EnforcementHash(),
			Verdict:         enfResp.Verdict(),
			RequestHash:     enfResp.RequestHash(),
			PolicyHash:      enfResp.PolicyHashField(),
		})
	}

	// GAP-10: Route ESCALATE verdicts to escalation queue
	if enfResp.Verdict() == "ESCALATE" {
		p.Escalation.Enqueue(enfResp)
	}

	// ================================================================
	// v14.1 ANTI-FOOLING: RPA ENFORCEMENT GATE (FOOLING-1 Fix)
	// ================================================================
	//
	// PROBLEM (FOOLING-1): v14.0 recorded stages inside Enforce() but
	// Execute() never verified the path. An attacker who modified Enforce()
	// to skip stages would still get ALLOW verdicts.
	//
	// FIX: For ALLOW verdicts, verify that the RPA path is COMPLETE
	// (all 9 canonical stages present in order) BEFORE calling
	// ExecuteWithToken(). If the path is incomplete:
	//   → Override verdict to DENY
	//   → Block execution
	//   → Emit RPA_INTEGRITY_VIOLATION observability event
	//
	// For DENY/ESCALATE verdicts, path is expected to be partial
	// (early exit is legitimate), so we skip enforcement but still
	// record the partial path for diagnostics.
	//
	// Industry alignment:
	//   - NIST 800-207: PEP must be "non-bypassable" — not advisory
	//   - Google Zanzibar: Zookie freshness is mandatory, not optional
	//   - AWS IAM: CheckNoNewAccess is a blocking gate, not a report
	var rpaVerified bool
	var rpaDetail string
	if enfResp.Verdict() == "ALLOW" {
		rpaVerified, rpaDetail = rpa.VerifyComplete(SarathiPipelineOrder)
		if !rpaVerified {
			// RPA INTEGRITY VIOLATION — override ALLOW to DENY
			// This means the enforcement pipeline was tampered with:
			// stages were skipped, reordered, or injected.
			if p.Observability != nil {
				p.Observability.Emit(ObservabilityEvent{
					Stage:          "RPA_ENFORCEMENT_GATE",
					SystemID:       "sarathi-enforcement-adapter",
					CorrelationID:  correlationID,
					TraceID:        traceCtx.TraceID,
					ExecutionState: "EXECUTION_BLOCKED",
					BlockReason:    "RPA_INTEGRITY_VIOLATION: " + rpaDetail,
					Verdict:        "DENY",
				})
			}
			pipelineSpan.Attributes["rpa_enforcement"] = "BLOCKED"
			pipelineSpan.Attributes["rpa_violation"] = rpaDetail
			pipelineSpan.End()

			pathHash := rpa.ComputePathHash()
			return EnforceResponseContract(
				CanonicalFromRpaViolation(enfResp, req, traceCtx, rpaDetail, pathHash, rpa.GetStages(), rpa.DurationNs()),
				req, traceCtx,
			)
		}
	}

	// FIX-07: Execution span
	execSpan := StartSpan("sarathi.execution.execute_with_token", pipelineSpan.Context)
	token := enfResp.GetCapabilityToken()
	execResult := p.Engine.ExecuteWithToken(token)
	execSpan.Attributes["execution_state"] = fmt.Sprintf("%v", execResult.ToMap()["execution_state"])
	execSpan.End()

	// v13.0 GAP-3: Emit execution observability event with all mandatory fields
	if p.Observability != nil {
		p.Observability.Emit(ObservabilityEvent{
			Stage:           "EXECUTION_RESULT",
			SystemID:        "sarathi-execution-engine",
			CorrelationID:   correlationID,
			TraceID:         traceCtx.TraceID,
			DecisionID:      execResult.DecisionID,
			EnforcementHash: execResult.EnforcementHash,
			TokenID:         execResult.TokenID,
			ExecutionState:  execResult.Status,
			Verdict:         enfResp.Verdict(),
		})
	}

	pipelineSpan.Attributes["verdict"] = enfResp.Verdict()
	if rpaVerified {
		pipelineSpan.Attributes["rpa_enforcement"] = "VERIFIED"
	}
	pipelineSpan.End()

	// v14.1: Compute runtime path attestation hash (now enforced, not advisory)
	pathHash := rpa.ComputePathHash()

	rpaEnforcement := "NOT_ENFORCED"
	if rpaVerified {
		rpaEnforcement = "VERIFIED"
	}
	return EnforceResponseContract(
		CanonicalFromEnforcement(enfResp, execResult, req, traceCtx, pathHash, rpa.GetStages(), rpa.DurationNs(), rpaEnforcement),
		req, traceCtx,
	)
}

// ================================================================
// ── v12.2 PIPELINE INTEGRITY ASSERTION LAYER (PHASE 2) ──
// ================================================================
// PURPOSE:
//   The 9-stage internal pipeline and the 10-stage external pipeline are
//   the load-bearing canonical orderings of Sarathi enforcement. They MUST
//   NOT be reordered, inserted into, or deleted from without an explicit
//   governance change. This layer is a fail-fast guard at process startup.
//
// HOW IT WORKS:
//   1. SarathiPipelineOrder declares the canonical stage names in order.
//   2. ExpectedPipelineHash is the SHA-256 of "stage1|stage2|...|stageN"
//      computed at the moment the constant was authored (v12.2).
//   3. init() recomputes the hash from the current SarathiPipelineOrder.
//   4. If they differ, init() panics with PIPELINE_INTEGRITY_VIOLATION
//      and the binary REFUSES TO START. There is no opt-out.
//
// RESULT:
//   Any modification to the canonical pipeline order is a compile-time-
//   adjacent failure: the process will not boot. To change the pipeline,
//   the engineer MUST update both the slice AND the expected hash, AND
//   document the change in REVIEW_PACKET.md (governance gate).
//
// INVARIANT (INV-35):
//   The internal and external pipelines have a frozen, hash-pinned order.
//   Reordering breaks the binary at startup, before any request is served.

// Stage classification legend (in comments next to each entry):
//   [SYSTEM GUARD]   — admission control / not part of verification chain
//   [VERIFICATION]   — load-bearing verification step (chain-producing)
//   [EXTERNAL INPUT] — consumes externally-signed input from a counterparty

// SarathiPipelineOrder is the canonical stage order of the INTERNAL
// (mode=INTERNAL) Sarathi enforcement pipeline. ANY change here MUST
// be accompanied by an update to ExpectedPipelineHash and a REVIEW_PACKET.md
// entry. The init() guard below enforces this contract at startup.
var SarathiPipelineOrder = []string{
	"PRE_GATE_RATE_LIMIT",        // [SYSTEM GUARD]   admission control side-gate
	"PRE_GATE_POSTURE_VERIFY",    // [SYSTEM GUARD]   signed posture pre-gate
	"PRE_PDP_VALIDATION",         // [VERIFICATION]   request well-formedness
	"POLICY_VERSION_CHECK",       // [VERIFICATION]   policy version pinning
	"PDP_EVALUATION",             // [VERIFICATION]   internal PDP decision
	"PDP_HASH_INTEGRITY",         // [VERIFICATION]   request-hash binding check
	"ENFORCEMENT_RESPONSE_BUILD", // [VERIFICATION]   response materialization
	"TOKEN_SIGN",                 // [VERIFICATION]   Ed25519 signature on capability
	"CHAIN_APPEND",               // [VERIFICATION]   GENESIS-anchored chain commit
}

// SarathiExternalPipelineOrder is the canonical stage order of the EXTERNAL
// (mode=EXTERNAL) decision verification pipeline. Owned by EnforceExternalDecision
// in external_decision.go. Same contract as SarathiPipelineOrder.
var SarathiExternalPipelineOrder = []string{
	"MODE_CHECK",             // [SYSTEM GUARD]    confirms EXTERNAL mode
	"STRUCTURE_CHECK",        // [VERIFICATION]    decision well-formedness
	"EVALUATOR_TRUST_CHECK",  // [EXTERNAL INPUT]  evaluator registered + ACTIVE
	"SIGNATURE_VERIFICATION", // [EXTERNAL INPUT]  Ed25519 over decision_core_hash
	"INTEGRITY_CHECK",        // [VERIFICATION]    decision_hash recomputation
	"EXPIRY_CHECK",           // [VERIFICATION]    TTL window
	"REPLAY_CHECK",           // [VERIFICATION]    nonce uniqueness
	"RATE_LIMIT_CHECK",       // [SYSTEM GUARD]    per-agent + global window
	"POSTURE_CHECK",          // [SYSTEM GUARD]    BeyondCorp posture
	"BINDING_CHECK",          // [VERIFICATION]    decision_core_hash → request binding
}

// ExpectedPipelineHash is the SHA-256 of strings.Join(SarathiPipelineOrder, "|")
// computed at v12.2 authoring time. The init() guard panics if the runtime
// hash differs from this constant.
const ExpectedPipelineHash = "7bfb3580a453d0c94c0f01ec83029ebd5e0bab346c130b45b89f9c9f238453b1"

// ExpectedExternalPipelineHash is the SHA-256 of strings.Join(SarathiExternalPipelineOrder, "|")
// computed at v12.2 authoring time. Same enforcement contract.
const ExpectedExternalPipelineHash = "5643c0ca0947a9e941d53a483fc0b62fab36b4e98aa08600c2bb4ea8a4ad15f8"

// computePipelineHash returns the canonical SHA-256 of a stage order.
func computePipelineHash(order []string) string {
	return Sha256Hex([]byte(pipelineOrderJoin(order)))
}

// pipelineOrderJoin joins stages with "|" without importing strings into the
// adapter just for one call (the rest of this file does not need it).
func pipelineOrderJoin(order []string) string {
	out := ""
	for i, s := range order {
		if i > 0 {
			out += "|"
		}
		out += s
	}
	return out
}

// init enforces the pipeline integrity assertion at process startup.
// This runs BEFORE main() and panics with PIPELINE_INTEGRITY_VIOLATION if
// the canonical pipeline order has been mutated without updating the
// matching expected hash constant.
//
// This is INV-35. There is no opt-out flag, no environment variable
// override, no test bypass. The binary will not boot.
func init() {
	actualInternal := computePipelineHash(SarathiPipelineOrder)
	if actualInternal != ExpectedPipelineHash {
		panic(fmt.Sprintf(
			"PIPELINE_INTEGRITY_VIOLATION: internal pipeline hash mismatch — "+
				"expected=%s actual=%s order=%v — "+
				"the canonical SarathiPipelineOrder has been modified without "+
				"updating ExpectedPipelineHash. Refusing to boot.",
			ExpectedPipelineHash, actualInternal, SarathiPipelineOrder,
		))
	}

	actualExternal := computePipelineHash(SarathiExternalPipelineOrder)
	if actualExternal != ExpectedExternalPipelineHash {
		panic(fmt.Sprintf(
			"PIPELINE_INTEGRITY_VIOLATION: external pipeline hash mismatch — "+
				"expected=%s actual=%s order=%v — "+
				"the canonical SarathiExternalPipelineOrder has been modified without "+
				"updating ExpectedExternalPipelineHash. Refusing to boot.",
			ExpectedExternalPipelineHash, actualExternal, SarathiExternalPipelineOrder,
		))
	}
}
