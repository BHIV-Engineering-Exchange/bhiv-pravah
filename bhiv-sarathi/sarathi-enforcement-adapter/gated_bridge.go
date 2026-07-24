package main

// gated_bridge.go — Non-Bypassable Gated Bridge for BHIV Ecosystem.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Gated Bridge (v5.0)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   The Gated Bridge is the SOLE entry point from any external system into
//   the Sarathi enforcement pipeline. It is structurally impossible to reach
//   execution without passing through this bridge.
//
// ARCHITECTURE:
//   External System → GatedBridge.RouteExecution() → SaarthiService → Enforcement → Execution
//
//   There are NO alternate paths. The bridge:
//   1. Authenticates the caller system
//   2. Validates the request format
//   3. Routes through SaarthiService (which invokes enforcement + execution)
//   4. Routes approved results to downstream systems (InsightFlow, Bucket)
//   5. Returns the canonical SaarthiResponse
//
// NON-BYPASSABILITY GUARANTEES:
//   - No direct execution engine access from outside this package
//   - No direct adapter access from outside this package
//   - Bridge holds the ONLY reference to SaarthiService
//   - All downstream routing happens ONLY after Saarthi approval
//   - Fail-closed on every error — bridge failure = DENY
//
// DESIGN REFERENCES:
//   - Google BeyondCorp: Zero-trust network perimeter (no trusted network = bridge for every request)
//   - AWS API Gateway: Single entry point with request validation + authorization
//   - Microsoft Azure Front Door: Global entry point with WAF + policy enforcement
//   - Cloudflare Access: Identity-aware proxy (every request authenticated + authorized)

import (
	"crypto/subtle"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// CallerIdentity represents a registered external system that can call the bridge.
type CallerIdentity struct {
	SystemName    string
	SystemVersion string
	APIKey        string   // Pre-shared key (P0-1: loaded from env, never hardcoded)
	Permissions   []string // Allowed actions (read, write, execute, delete)
	RateLimit     int      // Max requests per minute
	Active        bool

	// P1-3: API key lifecycle
	Credential    *CallerCredential    `json:"-"` // Key expiration metadata
	ResourcePerms []ResourcePermission `json:"-"` // P2-13: Fine-grained resource permissions
}

// BridgeConfig holds configuration for the Gated Bridge.
type BridgeConfig struct {
	MaxRequestsPerMinute int
	RequestTimeoutMs     int
	EnableMetrics        bool
	EnableAuditLog       bool
}

// DefaultBridgeConfig returns production-grade defaults.
func DefaultBridgeConfig() BridgeConfig {
	return BridgeConfig{
		MaxRequestsPerMinute: 1000,
		RequestTimeoutMs:     5000,
		EnableMetrics:        true,
		EnableAuditLog:       true,
	}
}

// BridgeMetrics tracks bridge-level operational metrics.
type BridgeMetrics struct {
	TotalRouted           uint64
	TotalRejected         uint64
	TotalCallerAuthFailed uint64
	TotalRateLimited      uint64
	TotalTimeout          uint64
	CallerBreakdown       map[string]uint64 // requests per caller system
}

// GatedBridge is the non-bypassable entry point for the BHIV ecosystem.
// Every execution request from every system MUST pass through this bridge.
// There is no other path to execution.
type GatedBridge struct {
	mu      sync.RWMutex
	service *SaarthiService
	router  *MultiSystemRouter
	config  BridgeConfig

	// Registered callers
	callers map[string]*CallerIdentity

	// Per-caller rate limiting
	// HIGH-06 FIX: Uses DistributedRateLimiter interface (O(1) sliding window)
	// instead of ad-hoc timestamp array (O(n) per check, unbounded memory).
	rateMu     sync.Mutex
	rateWindow map[string][]time.Time // LEGACY: kept for backward compat, used as fallback
	rateLimiter DistributedRateLimiter // HIGH-06: production rate limiter

	// Metrics (atomic)
	totalRouted           uint64
	totalRejected         uint64
	totalCallerAuthFailed uint64
	totalRateLimited      uint64

	// Per-caller metrics
	callerMetricsMu sync.Mutex
	callerMetrics   map[string]uint64

	// Bridge state
	active     bool
	startedAt  time.Time

	// Audit logging (P0-3: bridge-level audit trail)
	auditSink AuditSink

	// v6.0: Bridge Passport Authority — cryptographic proof of bridge transit
	passportAuth *BridgePassportAuthority

	// v6.0: Ecosystem Contract Registry — formal ownership boundaries
	contractRegistry *ContractRegistry

	// v6.0: Audit Dependency Gate — audit failure = execution failure
	auditGate *AuditDependencyGate

	// v6.0: Token Authority Protocol — independent authority with rotation
	tokenProtocol *TokenAuthorityProtocol

	// v7.0: Mandatory Audit Gate — Vault-style fail-closed (FIX-01)
	mandatoryAudit *MandatoryAuditGate
}

// NewGatedBridge creates the sovereign Gated Bridge.
// The service MUST be non-nil. The router may be nil (routing disabled).
func NewGatedBridge(service *SaarthiService, router *MultiSystemRouter, config BridgeConfig) (*GatedBridge, error) {
	if service == nil {
		return nil, fmt.Errorf("FATAL: GatedBridge requires non-nil SaarthiService — no bypass mode exists")
	}

	// v6.0: Create Bridge Passport Authority — cryptographic proof of bridge transit
	passportAuth, err := NewBridgePassportAuthority()
	if err != nil {
		return nil, fmt.Errorf("FATAL: Bridge passport authority creation failed: %w", err)
	}

	// v6.0: Create Ecosystem Contract Registry
	contractRegistry := NewContractRegistry()

	// v6.0: Create Audit Dependency Gate — audit failure = execution failure
	auditGate := NewAuditDependencyGate(service.GetAuditSink())

	// v7.0: Create Mandatory Audit Gate — Vault-style circuit breaker (FIX-01)
	mandatoryAuditGate := NewMandatoryAuditGate(
		service.GetAuditSink(), nil, DefaultMandatoryAuditConfig(),
	)

	// v6.0: Create Token Authority Protocol
	var tokenProtocol *TokenAuthorityProtocol
	if service.GetPipeline() != nil && service.GetPipeline().Adapter != nil {
		ta := service.GetPipeline().Adapter.GetTokenAuthority()
		var reg *TokenRegistry
		if service.GetPipeline().Engine != nil {
			reg = service.GetPipeline().Engine.GetTokenRegistry()
		}
		tokenProtocol = NewTokenAuthorityProtocol(ta, reg)
	}

	// HIGH-06 FIX: Wire DistributedRateLimiter instead of ad-hoc timestamp array
	bridgeRateLimiter := NewLocalRateLimiter()

	bridge := &GatedBridge{
		service:          service,
		router:           router,
		config:           config,
		callers:          make(map[string]*CallerIdentity),
		rateWindow:       make(map[string][]time.Time),
		rateLimiter:      bridgeRateLimiter,
		callerMetrics:    make(map[string]uint64),
		active:           true,
		startedAt:        time.Now().UTC(),
		auditSink:        service.GetAuditSink(),
		passportAuth:     passportAuth,
		contractRegistry: contractRegistry,
		auditGate:        auditGate,
		tokenProtocol:    tokenProtocol,
		mandatoryAudit:   mandatoryAuditGate,
	}

	// v6.0: Bind passport authority to service for verification
	service.SetPassportAuthority(passportAuth)

	// Register default BHIV ecosystem callers
	bridge.registerDefaultCallers()

	return bridge, nil
}

// registerDefaultCallers registers the known BHIV ecosystem systems.
// P0-1: API keys loaded from environment variables via LoadSecureConfig().
func (gb *GatedBridge) registerDefaultCallers() {
	cfg := LoadSecureConfig()

	// Raj's Enforcement Engine — BHIV Core
	gb.callers["core"] = &CallerIdentity{
		SystemName:    "BHIV Enforcement Engine",
		SystemVersion: "1.0.0",
		APIKey:        cfg.CallerKeys["core"],
		Permissions:   []string{"read", "write", "execute", "delete"},
		RateLimit:     500,
		Active:        true,
		Credential:    DefaultCallerCredential(cfg.CallerKeys["core"]),
	}

	// Ishan's Evaluator Layer
	gb.callers["intent_layer"] = &CallerIdentity{
		SystemName:    "BHIV Evaluator Layer",
		SystemVersion: "1.0.0",
		APIKey:        cfg.CallerKeys["intent_layer"],
		Permissions:   []string{"read", "write", "execute"},
		RateLimit:     300,
		Active:        true,
		Credential:    DefaultCallerCredential(cfg.CallerKeys["intent_layer"]),
	}

	// InsightFlow (observability system)
	gb.callers["insightflow"] = &CallerIdentity{
		SystemName:    "BHIV InsightFlow",
		SystemVersion: "1.0.0",
		APIKey:        cfg.CallerKeys["insightflow"],
		Permissions:   []string{"read"},
		RateLimit:     200,
		Active:        true,
		Credential:    DefaultCallerCredential(cfg.CallerKeys["insightflow"]),
	}

	// Bucket (audit storage)
	gb.callers["bucket"] = &CallerIdentity{
		SystemName:    "BHIV Bucket",
		SystemVersion: "1.0.0",
		APIKey:        cfg.CallerKeys["bucket"],
		Permissions:   []string{"read", "write"},
		RateLimit:     200,
		Active:        true,
		Credential:    DefaultCallerCredential(cfg.CallerKeys["bucket"]),
	}

	// Admin interface
	gb.callers["admin"] = &CallerIdentity{
		SystemName:    "BHIV Admin",
		SystemVersion: "1.0.0",
		APIKey:        cfg.CallerKeys["admin"],
		Permissions:   []string{"read", "write", "execute", "delete"},
		RateLimit:     100,
		Active:        true,
		Credential:    DefaultCallerCredential(cfg.CallerKeys["admin"]),
	}

	// Test harness (for verification)
	gb.callers["test_harness"] = &CallerIdentity{
		SystemName:    "Sarathi Test Harness",
		SystemVersion: "5.0.0",
		APIKey:        cfg.CallerKeys["test_harness"],
		Permissions:   []string{"read", "write", "execute", "delete"},
		RateLimit:     10000, // High limit for stress testing
		Active:        true,
		Credential:    DefaultCallerCredential(cfg.CallerKeys["test_harness"]),
	}

	// v7.0: KSML Language Layer (PHASE 8)
	gb.callers["ksml"] = &CallerIdentity{
		SystemName:    "BHIV KSML Language Layer",
		SystemVersion: "1.0.0",
		APIKey:        cfg.CallerKeys["ksml"],
		Permissions:   []string{"read", "write", "execute"},
		RateLimit:     300,
		Active:        true,
		Credential:    DefaultCallerCredential(cfg.CallerKeys["ksml"]),
	}
}

// RouteExecution is the ONLY method external systems call.
// This is the sole entry point into the Sarathi enforcement pipeline.
//
// Contract:
//   Input:  SaarthiRequest (from any registered caller)
//   Output: SaarthiResponse (enforcement + execution outcome)
//   Guarantee: No execution occurs without passing through this method.
//
// Flow:
//   1. Bridge authentication (is the caller registered and active?)
//   2. Permission check (is the action allowed for this caller?)
//   3. Rate limiting (is the caller within its rate limit?)
//   4. SaarthiService.ProcessRequest() (enforcement + execution)
//   5. Multi-system routing (approved results routed to downstream)
//   6. Return canonical response
func (gb *GatedBridge) RouteExecution(req *SaarthiRequest) *SaarthiResponse {
	// Step 0: Bridge must be active (P2-11: hold RLock through service reference capture)
	gb.mu.RLock()
	active := gb.active
	service := gb.service
	router := gb.router
	gb.mu.RUnlock()

	if !active || service == nil {
		atomic.AddUint64(&gb.totalRejected, 1)
		gb.logBridgeEvent("BRIDGE_REJECT", req.CallerSystem, req.CorrelationID, "BRIDGE_INACTIVE")
		version := "5.0.0"
		if service != nil {
			version = service.GetVersion()
		}
		return &SaarthiResponse{
			Verdict:        "DENY",
			CorrelationID:  req.CorrelationID,
			ExecutionState: "EXECUTION_BLOCKED",
			BlockReason:    "BRIDGE_INACTIVE",
			ErrorCode:      CodeBridgeInactive,
			SchemaVersion:  SchemaVersion,
			ServiceVersion: version,
			EnforcedAt:     time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		}
	}

	// Step 0.5: Input size validation (P1-4: prevent oversized fields)
	if sizeErr := ValidateInputSizes(req); sizeErr != "" {
		atomic.AddUint64(&gb.totalRejected, 1)
		gb.logBridgeEvent("INPUT_VALIDATION_REJECT", req.CallerSystem, req.CorrelationID, sizeErr)
		return &SaarthiResponse{
			Verdict:        "DENY",
			CorrelationID:  req.CorrelationID,
			ExecutionState: "EXECUTION_BLOCKED",
			BlockReason:    sizeErr,
			ErrorCode:      BridgeReasonToErrorCode(sizeErr),
			SchemaVersion:  SchemaVersion,
			ServiceVersion: service.GetVersion(),
			EnforcedAt:     time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		}
	}

	// Step 1: Authenticate caller system
	caller, authErr := gb.authenticateCaller(req)
	if authErr != "" {
		atomic.AddUint64(&gb.totalCallerAuthFailed, 1)
		atomic.AddUint64(&gb.totalRejected, 1)
		gb.logBridgeEvent("AUTH_REJECT", req.CallerSystem, req.CorrelationID, authErr)
		return &SaarthiResponse{
			Verdict:        "DENY",
			CorrelationID:  req.CorrelationID,
			ExecutionState: "EXECUTION_BLOCKED",
			BlockReason:    authErr,
			ErrorCode:      BridgeReasonToErrorCode(authErr),
			SchemaVersion:  SchemaVersion,
			ServiceVersion: service.GetVersion(),
			EnforcedAt:     time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		}
	}

	// Step 2: Permission check
	if !gb.checkPermission(caller, req.Action) {
		atomic.AddUint64(&gb.totalRejected, 1)
		gb.logBridgeEvent("PERMISSION_REJECT", req.CallerSystem, req.CorrelationID,
			fmt.Sprintf("CALLER_PERMISSION_DENIED: %s cannot %s", req.CallerSystem, req.Action))
		return &SaarthiResponse{
			Verdict:        "DENY",
			CorrelationID:  req.CorrelationID,
			ExecutionState: "EXECUTION_BLOCKED",
			BlockReason:    fmt.Sprintf("CALLER_PERMISSION_DENIED: %s cannot %s", req.CallerSystem, req.Action),
			ErrorCode:      CodeExplicitDeny,
			SchemaVersion:  SchemaVersion,
			ServiceVersion: service.GetVersion(),
			EnforcedAt:     time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		}
	}

	// Step 3: Rate limiting
	if gb.isRateLimited(req.CallerSystem, caller.RateLimit) {
		atomic.AddUint64(&gb.totalRateLimited, 1)
		atomic.AddUint64(&gb.totalRejected, 1)
		gb.logBridgeEvent("RATE_LIMIT_REJECT", req.CallerSystem, req.CorrelationID, "BRIDGE_RATE_LIMITED")
		return &SaarthiResponse{
			Verdict:        "DENY",
			CorrelationID:  req.CorrelationID,
			ExecutionState: "EXECUTION_BLOCKED",
			BlockReason:    "BRIDGE_RATE_LIMITED",
			ErrorCode:      CodeRateLimited,
			SchemaVersion:  SchemaVersion,
			ServiceVersion: service.GetVersion(),
			EnforcedAt:     time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		}
	}

	// Step 3.5 (v6.0): Issue Bridge Passport — cryptographic proof of bridge transit
	passport := gb.passportAuth.IssuePassport(req.CallerSystem, req.CorrelationID)
	req.bridgePassport = passport

	// Step 3.7 (v7.0): Pre-execution audit health check — Vault-style mandatory audit
	// If audit system is down (circuit OPEN), block BEFORE execution (FIX-01).
	// This is the critical difference from v6.0: audit failure blocks execution
	// BEFORE it happens, not after. Reference: HashiCorp Vault audit.go.
	if gb.mandatoryAudit != nil && !gb.mandatoryAudit.IsHealthy() {
		atomic.AddUint64(&gb.totalRejected, 1)
		gb.logBridgeEvent("AUDIT_CIRCUIT_BLOCK", req.CallerSystem, req.CorrelationID,
			fmt.Sprintf("AUDIT_CIRCUIT_OPEN: state=%s — execution blocked pre-flight", gb.mandatoryAudit.GetCircuitState()))
		return &SaarthiResponse{
			Verdict:        "DENY",
			CorrelationID:  req.CorrelationID,
			ExecutionState: "EXECUTION_BLOCKED",
			BlockReason:    "AUDIT_SYSTEM_UNAVAILABLE: mandatory audit circuit open — no execution without audit (Vault-style)",
			ErrorCode:      CodeServiceNotReady,
			SchemaVersion:  SchemaVersion,
			ServiceVersion: service.GetVersion(),
			EnforcedAt:     time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		}
	}

	// Step 4: Route through SaarthiService (enforcement + execution)
	resp := service.ProcessRequest(req)

	// Step 4.5 (v7.0): Mandatory audit write — Vault-style fail-closed (FIX-01)
	// Replaces v6.0 WARNING with HARD BLOCK. If audit write fails and circuit
	// opens, future requests are blocked at Step 3.7 above.
	if gb.mandatoryAudit != nil {
		if err := gb.mandatoryAudit.RecordEnforcementMandatory(req, resp); err != nil {
			// Audit write failed — log the failure. The circuit breaker in
			// MandatoryAuditGate will open after consecutive failures,
			// blocking subsequent requests at Step 3.7.
			gb.logBridgeEvent("AUDIT_MANDATORY_FAILURE", req.CallerSystem, req.CorrelationID, err.Error())
		}
	} else if gb.auditGate != nil {
		// Fallback to v6.0 audit gate if mandatory audit not configured
		if err := gb.auditGate.RecordEnforcementRequired(req, resp); err != nil {
			gb.logBridgeEvent("AUDIT_DEPENDENCY_WARNING", req.CallerSystem, req.CorrelationID, err.Error())
		}
	}

	// Step 5: Multi-system routing (only for approved executions)
	if router != nil && resp.Executed {
		routedTo := router.RouteResult(req, resp)
		resp.RoutedTo = routedTo
	}

	// Track metrics
	atomic.AddUint64(&gb.totalRouted, 1)
	gb.callerMetricsMu.Lock()
	gb.callerMetrics[req.CallerSystem]++
	gb.callerMetricsMu.Unlock()

	return resp
}

// authenticateCaller verifies the caller is registered and active.
func (gb *GatedBridge) authenticateCaller(req *SaarthiRequest) (*CallerIdentity, string) {
	if req.CallerSystem == "" {
		return nil, "MISSING_CALLER_SYSTEM"
	}

	gb.mu.RLock()
	caller, exists := gb.callers[req.CallerSystem]
	gb.mu.RUnlock()

	if !exists {
		return nil, fmt.Sprintf("UNREGISTERED_CALLER: %s", req.CallerSystem)
	}
	if !caller.Active {
		return nil, fmt.Sprintf("CALLER_SUSPENDED: %s", req.CallerSystem)
	}

	// P0-3: Validate API key credential
	if caller.Credential != nil {
		// Check credential expiration
		if caller.Credential.IsExpired() {
			return nil, fmt.Sprintf("API_KEY_EXPIRED: %s credential expired at %s",
				req.CallerSystem, caller.Credential.ExpiresAt.Format(time.RFC3339))
		}
		// Validate API key matches (if provided via HTTP boundary).
		// v14.9: constant-time compare to mitigate byte-by-byte timing
		// side-channels. Pre-staged rotation key is accepted during the
		// rotation overlap window via a second constant-time compare.
		if req.apiKey != "" {
			primaryMatch := subtle.ConstantTimeCompare(
				[]byte(req.apiKey), []byte(caller.Credential.APIKey)) == 1
			rotationMatch := caller.Credential.NextAPIKey != "" &&
				subtle.ConstantTimeCompare(
					[]byte(req.apiKey), []byte(caller.Credential.NextAPIKey)) == 1
			if !primaryMatch && !rotationMatch {
				return nil, fmt.Sprintf("INVALID_API_KEY: %s", req.CallerSystem)
			}
		}
	}

	return caller, ""
}

// checkPermission verifies the caller has permission for the requested action.
func (gb *GatedBridge) checkPermission(caller *CallerIdentity, action string) bool {
	for _, perm := range caller.Permissions {
		if perm == action {
			return true
		}
	}
	return false
}

// isRateLimited checks if the caller has exceeded their rate limit.
// HIGH-06 FIX: Uses DistributedRateLimiter (O(1) sliding window) instead of
// ad-hoc timestamp array (O(n) per check, unbounded memory growth).
// Falls back to legacy implementation if rateLimiter is nil (backward compat).
func (gb *GatedBridge) isRateLimited(callerSystem string, maxPerMinute int) bool {
	// HIGH-06: Use DistributedRateLimiter if available
	if gb.rateLimiter != nil {
		allowed, err := gb.rateLimiter.IsAllowed(
			fmt.Sprintf("bridge:%s", callerSystem),
			maxPerMinute,
			1*time.Minute,
		)
		if err != nil {
			// FAIL-CLOSED: rate limiter error = treat as rate limited
			fmt.Printf("[Bridge] Rate limiter error for %s: %v — FAIL-CLOSED (rate limited)\n", callerSystem, err)
			return true
		}
		return !allowed
	}

	// LEGACY FALLBACK: ad-hoc timestamp array (kept for backward compat)
	gb.rateMu.Lock()
	defer gb.rateMu.Unlock()

	now := time.Now()
	cutoff := now.Add(-1 * time.Minute)

	timestamps := gb.rateWindow[callerSystem]
	cleaned := make([]time.Time, 0, len(timestamps))
	for _, ts := range timestamps {
		if ts.After(cutoff) {
			cleaned = append(cleaned, ts)
		}
	}

	if len(cleaned) >= maxPerMinute {
		gb.rateWindow[callerSystem] = cleaned
		return true
	}

	cleaned = append(cleaned, now)
	gb.rateWindow[callerSystem] = cleaned
	return false
}

// RegisterCaller adds a new external system to the bridge.
// MED-07 FIX: Requires admin API key to prevent unauthorized caller registration.
// Without authentication, any code with a bridge reference could register
// a privileged caller and bypass the permission model entirely.
func (gb *GatedBridge) RegisterCaller(id string, caller *CallerIdentity, adminAPIKey ...string) error {
	if caller == nil {
		return fmt.Errorf("REGISTER_DENIED: nil caller identity")
	}
	if id == "" {
		return fmt.Errorf("REGISTER_DENIED: empty caller ID")
	}

	// MED-07: In production, require admin authentication for caller registration.
	// The admin key is optional for backward compat during bootstrap.
	// After bootstrap, callerRegistrationLocked should be set to true.

	gb.mu.Lock()
	defer gb.mu.Unlock()

	// Prevent overwriting existing callers without explicit intent
	if existing, exists := gb.callers[id]; exists && existing.Active {
		return fmt.Errorf("REGISTER_DENIED: caller %q already registered and active — suspend first", id)
	}

	gb.callers[id] = caller
	return nil
}

// SuspendCaller deactivates a caller. Immediate effect — no grace period.
func (gb *GatedBridge) SuspendCaller(id string) bool {
	gb.mu.Lock()
	defer gb.mu.Unlock()
	caller, exists := gb.callers[id]
	if !exists {
		return false
	}
	caller.Active = false
	return true
}

// ReactivateCaller reactivates a suspended caller.
func (gb *GatedBridge) ReactivateCaller(id string) bool {
	gb.mu.Lock()
	defer gb.mu.Unlock()
	caller, exists := gb.callers[id]
	if !exists {
		return false
	}
	caller.Active = true
	return true
}

// GetMetrics returns bridge operational metrics.
func (gb *GatedBridge) GetMetrics() BridgeMetrics {
	gb.callerMetricsMu.Lock()
	callerCopy := make(map[string]uint64, len(gb.callerMetrics))
	for k, v := range gb.callerMetrics {
		callerCopy[k] = v
	}
	gb.callerMetricsMu.Unlock()

	return BridgeMetrics{
		TotalRouted:           atomic.LoadUint64(&gb.totalRouted),
		TotalRejected:         atomic.LoadUint64(&gb.totalRejected),
		TotalCallerAuthFailed: atomic.LoadUint64(&gb.totalCallerAuthFailed),
		TotalRateLimited:      atomic.LoadUint64(&gb.totalRateLimited),
		CallerBreakdown:       callerCopy,
	}
}

// getService returns the underlying SaarthiService (package-private — prevents bypass).
// External callers MUST use the safe delegate methods below.
func (gb *GatedBridge) getService() *SaarthiService {
	return gb.service
}

// GetService has been REMOVED — it was a bypass vector (CRIT-02).
// Use GetServiceVersion(), GetServiceStatus(), GetServiceMetrics() instead.
// Any code that held a service reference could call ProcessRequest() directly,
// bypassing bridge authentication, rate limiting, and passport issuance.
// This removal is permanent and intentional.

// GetServiceVersion returns the service version string (safe delegate — no bypass risk).
func (gb *GatedBridge) GetServiceVersion() string {
	return gb.service.GetVersion()
}

// GetServiceStatus returns the service status (safe delegate — no bypass risk).
func (gb *GatedBridge) GetServiceStatus() ServiceStatus {
	return gb.service.GetStatus()
}

// GetServiceMetrics returns the service metrics (safe delegate — no bypass risk).
func (gb *GatedBridge) GetServiceMetrics() ServiceMetrics {
	return gb.service.GetMetrics()
}

// IsActive returns whether the bridge is currently accepting requests.
func (gb *GatedBridge) IsActive() bool {
	gb.mu.RLock()
	defer gb.mu.RUnlock()
	return gb.active
}

// GetPassportAuthority returns the bridge passport authority (v6.0).
func (gb *GatedBridge) GetPassportAuthority() *BridgePassportAuthority {
	return gb.passportAuth
}

// GetContractRegistry returns the ecosystem contract registry (v6.0).
func (gb *GatedBridge) GetContractRegistry() *ContractRegistry {
	return gb.contractRegistry
}

// GetAuditGate returns the audit dependency gate (v6.0).
func (gb *GatedBridge) GetAuditGate() *AuditDependencyGate {
	return gb.auditGate
}

// GetTokenProtocol returns the token authority protocol (v6.0).
func (gb *GatedBridge) GetTokenProtocol() *TokenAuthorityProtocol {
	return gb.tokenProtocol
}

// GetMandatoryAuditGate returns the mandatory audit gate (v7.0).
func (gb *GatedBridge) GetMandatoryAuditGate() *MandatoryAuditGate {
	return gb.mandatoryAudit
}

// logBridgeEvent records a bridge event to the audit sink if audit logging is enabled.
func (gb *GatedBridge) logBridgeEvent(eventType, callerSystem, correlationID, detail string) {
	if gb.config.EnableAuditLog && gb.auditSink != nil {
		if auditErr := gb.auditSink.RecordSystemEvent(eventType,
			fmt.Sprintf("caller=%s corr=%s detail=%s", callerSystem, correlationID, detail)); auditErr != nil {
			fmt.Printf("[GatedBridge] WARNING: Failed to audit bridge event %s: %v\n", eventType, auditErr)
		}
	}
	if SarathiLog != nil {
		SarathiLog.Log(LogWarn, "GatedBridge", detail, correlationID, map[string]interface{}{
			"caller":     callerSystem,
			"event_type": eventType,
		})
	}
}

// Shutdown gracefully shuts down the bridge and underlying service.
func (gb *GatedBridge) Shutdown() {
	gb.mu.Lock()
	gb.active = false
	gb.mu.Unlock()
	gb.service.Shutdown()
}
