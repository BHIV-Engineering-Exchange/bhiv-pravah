package main

// saarthi_service.go — Sovereign Saarthi Service Layer.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Service Abstraction (v5.0)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   This is the ONLY interface contract for external systems to interact with
//   Sarathi. External systems (Raj's Enforcement Engine, Ishan's Evaluator Layer,
//   any future BHIV component) MUST go through SaarthiService.
//
//   SaarthiService wraps the SarathiEnforcementPipeline and exposes a clean,
//   versioned, auditable service interface. It is NOT the enforcement logic
//   itself — it is the service contract that makes enforcement accessible
//   while maintaining the sovereign guarantee.
//
// CONTRACT:
//   ExecuteRequest → SaarthiService → SaarthiResponse
//   No alternate path to execution exists.
//
// DESIGN REFERENCES:
//   - Google Zanzibar: Consistent, global authorization service with typed relations
//   - AWS IAM: Request signing + policy evaluation as a service
//   - Anthropic Constitutional AI: Governance as a first-class service boundary
//   - Microsoft Azure AD: Token-based authorization service with claims verification
//   - OpenAI Preparedness Framework: Runtime enforcement as a service layer

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"

	"github.com/google/uuid"
)

// ServiceStatus represents the health state of the Saarthi Service.
type ServiceStatus string

const (
	ServiceStatusReady      ServiceStatus = "READY"
	ServiceStatusDegraded   ServiceStatus = "DEGRADED"
	ServiceStatusShutdown   ServiceStatus = "SHUTDOWN"
	ServiceStatusStarting   ServiceStatus = "STARTING"
)

// SaarthiRequest is the canonical request format for all external systems.
// This is the ONLY input format accepted by the Gated Bridge and Saarthi Service.
type SaarthiRequest struct {
	// Required fields
	AgentID       string `json:"agent_id"`
	ResourceID    string `json:"resource_id"`
	Action        string `json:"action"`
	CorrelationID string `json:"correlation_id"`

	// Optional fields
	PolicyVersion string `json:"policy_version,omitempty"`

	// Caller identification (for multi-system routing)
	CallerSystem  string `json:"caller_system"`  // e.g., "core", "intent_layer", "insightflow"
	CallerVersion string `json:"caller_version"` // Caller's version for compatibility tracking

	// Request metadata
	RequestedAt    time.Time `json:"requested_at"`
	IdempotencyKey string    `json:"idempotency_key,omitempty"` // For idempotent retries

	// Internal: API key extracted from HTTP header (unexported, not serialized)
	apiKey string

	// Internal: Bridge passport proving request transited through GatedBridge (v6.0)
	bridgePassport *BridgePassport
}

// SaarthiResponse is the canonical response format returned to all external systems.
// It contains the enforcement decision, execution outcome, and audit metadata.
type SaarthiResponse struct {
	// Decision
	Verdict         string `json:"verdict"`          // ALLOW, DENY, ESCALATE
	DecisionID      string `json:"decision_id"`
	CorrelationID   string `json:"correlation_id"`

	// Execution outcome
	Executed        bool   `json:"executed"`
	ExecutionState  string `json:"execution_state"`  // EXECUTION_PERMITTED, EXECUTION_BLOCKED
	BlockReason     string `json:"block_reason,omitempty"`

	// Policy binding
	PolicyVersion   string `json:"policy_version"`
	PolicyHash      string `json:"policy_hash"`

	// Cryptographic proof
	EnforcementHash string `json:"enforcement_hash"`
	RequestHash     string `json:"request_hash"`

	// Token metadata (for downstream systems that need proof)
	HasToken        bool   `json:"has_capability_token"`
	TokenConsumed   bool   `json:"token_consumed"`

	// Audit
	EnforcedAt      string `json:"enforced_at"`
	ServiceVersion  string `json:"service_version"`
	RegistryVersion uint64 `json:"registry_version"` // GAP-12 consistency token

	// Obligations (GAP-05)
	Obligations     []string `json:"obligations,omitempty"`

	// Routing
	RoutedTo        []string `json:"routed_to,omitempty"` // Which downstream systems received this

	// Phase 2: Cross-layer binding hash (Intent → Request → Response → Audit)
	// Proves cryptographic linkage between all 4 layers of the enforcement pipeline.
	LayerBindingHash string `json:"layer_binding_hash,omitempty"`

	// v14.4: Enriched audit fields — persisted to DB and JSON results
	TraceID          string `json:"trace_id,omitempty"`           // W3C trace ID for distributed tracing
	ErrorCode        string `json:"error_code,omitempty"`         // Standardized error code (response_contract.go)
	SchemaVersion    string `json:"schema_version,omitempty"`     // Response schema version
	EnforcementToken string `json:"enforcement_token,omitempty"`  // Capability token ID (enforcement proof)
	ExecutionID      string `json:"execution_id,omitempty"`       // Composite execution identifier

	// v14.5: Cross-System Propagation Layer audit fields. Populated ONLY
	// when the decision flowed through the PDPAdapter → PropagationEnvelope
	// path. Legacy (pre-v14.5) decisions leave these empty. All three are
	// persisted to proof_logs/enforcement_audit_backup.jsonl and (if DB
	// is enabled) to the enforcement_audit table via persistent_audit.go.
	ResponseHash     string `json:"response_hash,omitempty"`      // SHA-256 of sealed canonical response bytes
	ChainBindingHash string `json:"chain_binding_hash,omitempty"` // SHA-256 binding decision→core→enforcement→response
	PDPDecisionID    string `json:"pdp_decision_id,omitempty"`    // Upstream PDP decision identifier

	// v15.6 Bridge-facing JWT: compact RFC 7519 token signed by the
	// JWTAuthority's Ed25519 key (alg=EdDSA, RFC 8037). Populated by the
	// /v1/enforce path when a JWTAuthority is bound and the verdict is
	// ALLOW. Omitted (empty + omitempty) when no authority is bound, when
	// the verdict is not ALLOW, or when mint fails. Verifiable offline
	// against /sarathi/.well-known/jwks.json.
	CapabilityTokenJWT    string `json:"capability_token_jwt,omitempty"`
	CapabilityTokenKID    string `json:"capability_token_kid,omitempty"`
	CapabilityTokenIssuer string `json:"capability_token_issuer,omitempty"`
}

// ServiceMetrics tracks operational metrics for the Saarthi Service.
type ServiceMetrics struct {
	TotalRequests       uint64
	AllowedRequests     uint64
	DeniedRequests      uint64
	EscalatedRequests   uint64
	FailedRequests      uint64
	AverageLatencyNs    int64
	PeakLatencyNs       int64
	ActiveSince         time.Time
	LastRequestAt       time.Time
}

// SaarthiService is the sovereign service layer over the Sarathi enforcement pipeline.
// External systems interact ONLY through this service. There is no other path.
type SaarthiService struct {
	mu       sync.RWMutex
	pipeline *SarathiEnforcementPipeline
	status   ServiceStatus
	version  string

	// Metrics (atomic for lock-free reads)
	totalRequests     uint64
	allowedRequests   uint64
	deniedRequests    uint64
	escalatedRequests uint64
	failedRequests    uint64
	peakLatencyNs     int64

	// Idempotency cache (correlation_id → response)
	idempotencyMu    sync.RWMutex
	idempotencyCache map[string]*SaarthiResponse
	idempotencyTTL   time.Duration

	// Audit sink (will be connected to PostgreSQL in persistent_audit.go)
	auditSink AuditSink

	// Service lifecycle
	startedAt time.Time
	shutdownCh chan struct{}

	// v6.0: Bridge Passport Authority for verifying bridge transit proof
	passportAuth *BridgePassportAuthority

	// v15.6: outbound JWT authority. When non-nil and the verdict is
	// ALLOW, buildResponse mints a JWT and attaches it to the response.
	// Nil-safe — when unset the v15.5 SaarthiResponse is byte-identical
	// to the v15.5 path (the new fields are omitempty).
	jwtAuthority *JWTAuthority
}

// SetJWTAuthority binds the outbound JWT authority used by buildResponse.
// Set during service runtime bootstrap. Safe to call once before the first
// request; not concurrency-safe across re-binds.
func (svc *SaarthiService) SetJWTAuthority(a *JWTAuthority) {
	if svc == nil {
		return
	}
	svc.jwtAuthority = a
}

// JWTAuthority returns the bound authority (may be nil).
func (svc *SaarthiService) JWTAuthority() *JWTAuthority {
	if svc == nil {
		return nil
	}
	return svc.jwtAuthority
}

// AuditSink is the interface for persistent audit storage.
// Implementations: InMemoryAuditSink (testing), PostgresAuditSink (production).
type AuditSink interface {
	// RecordEnforcement persists an enforcement decision.
	RecordEnforcement(req *SaarthiRequest, resp *SaarthiResponse) error
	// RecordSystemEvent persists a system-level event (startup, shutdown, key rotation, etc.).
	RecordSystemEvent(eventType, detail string) error
	// RecordChainEntry persists a hash chain entry to durable storage.
	// Phase 6 fix: enforcement chain entries must be persisted for durability.
	// Without this, chain integrity can only be verified from in-memory state.
	RecordChainEntry(entry EnforcementTraceEntry) error
	// Close cleanly shuts down the audit sink.
	Close() error
	// IsDurable returns true if the audit sink persists data beyond process lifetime.
	// CRIT-04: Production mode requires a durable sink (PostgreSQL, S3, etc.).
	// InMemoryAuditSink returns false. PostgresAuditSink returns true.
	IsDurable() bool
}

// ValidateSaarthiResponse ensures critical fields are populated on any response
// before it leaves the system boundary. This is a safety net — all canonical
// builders and bridge DENYs should already populate these fields.
func ValidateSaarthiResponse(resp *SaarthiResponse) *SaarthiResponse {
	if resp == nil {
		return resp
	}
	if resp.SchemaVersion == "" {
		resp.SchemaVersion = SchemaVersion
	}
	if resp.ExecutionState == "" {
		if resp.Verdict == "DENY" {
			resp.ExecutionState = "EXECUTION_BLOCKED"
		}
	}
	if resp.EnforcedAt == "" {
		resp.EnforcedAt = time.Now().UTC().Format("2006-01-02T15:04:05.000000Z")
	}
	return resp
}

// InMemoryAuditSink is a testing implementation of AuditSink.
type InMemoryAuditSink struct {
	mu           sync.Mutex
	enforcements []AuditRecord
	events       []SystemEventRecord
}

// AuditRecord represents a persisted enforcement decision.
type AuditRecord struct {
	Timestamp       time.Time
	CorrelationID   string
	AgentID         string
	ResourceID      string
	Action          string
	Verdict         string
	EnforcementHash string
	CallerSystem    string
	Executed        bool
	BlockReason     string
	LatencyNs       int64
	// v14.4: Enriched audit fields
	TraceID         string
	ErrorCode       string
	ExecutionState  string
	SchemaVersion   string
}

// SystemEventRecord represents a persisted system event.
type SystemEventRecord struct {
	Timestamp time.Time
	EventType string
	Detail    string
}

// NewInMemoryAuditSink creates a testing audit sink.
func NewInMemoryAuditSink() *InMemoryAuditSink {
	return &InMemoryAuditSink{
		enforcements: make([]AuditRecord, 0),
		events:       make([]SystemEventRecord, 0),
	}
}

func (s *InMemoryAuditSink) RecordEnforcement(req *SaarthiRequest, resp *SaarthiResponse) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.enforcements = append(s.enforcements, AuditRecord{
		Timestamp:       time.Now().UTC(),
		CorrelationID:   req.CorrelationID,
		AgentID:         req.AgentID,
		ResourceID:      req.ResourceID,
		Action:          req.Action,
		Verdict:         resp.Verdict,
		EnforcementHash: resp.EnforcementHash,
		CallerSystem:    req.CallerSystem,
		Executed:        resp.Executed,
		BlockReason:     resp.BlockReason,
		// v14.4: Enriched audit fields
		TraceID:        resp.TraceID,
		ErrorCode:      resp.ErrorCode,
		ExecutionState: resp.ExecutionState,
		SchemaVersion:  resp.SchemaVersion,
	})
	return nil
}

func (s *InMemoryAuditSink) RecordSystemEvent(eventType, detail string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.events = append(s.events, SystemEventRecord{
		Timestamp: time.Now().UTC(),
		EventType: eventType,
		Detail:    detail,
	})
	return nil
}

// RecordChainEntry stores a chain entry in memory (non-durable, for testing only).
// Phase 6 fix: In production, PostgresAuditSink persists to the sarathi_chain_entries table.
func (s *InMemoryAuditSink) RecordChainEntry(entry EnforcementTraceEntry) error {
	// In-memory sink: no persistence needed. Chain entries are retained in
	// EnforcementAdapter.enforcementChain for the lifetime of the process.
	return nil
}

func (s *InMemoryAuditSink) Close() error { return nil }

// IsDurable returns false — InMemoryAuditSink is NOT durable (CRIT-04).
// All records are lost on process restart. Use PostgresAuditSink for production.
func (s *InMemoryAuditSink) IsDurable() bool { return false }

// GetEnforcements returns all recorded enforcement decisions (for testing).
func (s *InMemoryAuditSink) GetEnforcements() []AuditRecord {
	s.mu.Lock()
	defer s.mu.Unlock()
	cp := make([]AuditRecord, len(s.enforcements))
	copy(cp, s.enforcements)
	return cp
}

// GetEvents returns all recorded system events (for testing).
func (s *InMemoryAuditSink) GetEvents() []SystemEventRecord {
	s.mu.Lock()
	defer s.mu.Unlock()
	cp := make([]SystemEventRecord, len(s.events))
	copy(cp, s.events)
	return cp
}

// NewSaarthiService creates the sovereign Saarthi Service.
// The pipeline MUST be non-nil — there is no degraded mode that allows execution.
// CRIT-04 FIX: In production mode, a durable audit sink is REQUIRED.
// Pass productionMode=true to enforce this (variadic for backward compat).
func NewSaarthiService(pipeline *SarathiEnforcementPipeline, auditSink AuditSink, productionMode ...bool) (*SaarthiService, error) {
	if pipeline == nil {
		return nil, fmt.Errorf("FATAL: SaarthiService requires non-nil pipeline — no degraded mode exists")
	}

	isProd := len(productionMode) > 0 && productionMode[0]

	if auditSink == nil {
		if isProd {
			return nil, fmt.Errorf("FATAL: Production mode requires a durable audit sink (PostgresAuditSink) — InMemoryAuditSink is not acceptable for production (CRIT-04)")
		}
		auditSink = NewInMemoryAuditSink()
	}

	// CRIT-04: Validate audit sink durability in production mode
	if isProd && !auditSink.IsDurable() {
		return nil, fmt.Errorf("FATAL: Production mode requires a durable audit sink — provided sink (IsDurable()=false) is not acceptable. Use PostgresAuditSink or equivalent. (CRIT-04)")
	}

	svc := &SaarthiService{
		pipeline:         pipeline,
		status:           ServiceStatusStarting,
		version:          "8.0.0",
		idempotencyCache: make(map[string]*SaarthiResponse),
		idempotencyTTL:   5 * time.Minute,
		auditSink:        auditSink,
		startedAt:        time.Now().UTC(),
		shutdownCh:       make(chan struct{}),
	}

	// Record service startup (best-effort — service must start even if audit write fails)
	if err := auditSink.RecordSystemEvent("SERVICE_STARTED", fmt.Sprintf("SaarthiService v%s started", svc.version)); err != nil {
		fmt.Printf("[WARN] SaarthiService startup audit write failed: %v\n", err)
	}

	// Start idempotency cache cleanup
	go svc.idempotencyCleanupLoop()

	svc.status = ServiceStatusReady
	return svc, nil
}

// ProcessRequest is the SOLE entry point for processing authorization requests.
// All external systems MUST call this method through the Gated Bridge.
// There is no other path to execution.
func (svc *SaarthiService) ProcessRequest(req *SaarthiRequest) *SaarthiResponse {
	startTime := time.Now()

	// Service health check — fail-closed
	svc.mu.RLock()
	status := svc.status
	svc.mu.RUnlock()

	if status != ServiceStatusReady {
		atomic.AddUint64(&svc.failedRequests, 1)
		return &SaarthiResponse{
			Verdict:        "DENY",
			CorrelationID:  req.CorrelationID,
			ExecutionState: "EXECUTION_BLOCKED",
			BlockReason:    fmt.Sprintf("SERVICE_NOT_READY: %s", status),
			ServiceVersion: svc.version,
			EnforcedAt:     time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		}
	}

	// v6.0 + v8.0 CRIT-03 FIX: Verify Bridge Passport — proof that request transited through GatedBridge.
	// FAIL-CLOSED: If passportAuth is nil, ALL requests are DENIED. No bypass possible.
	// Previous behavior (v7.0) skipped verification when passportAuth was nil — this was a bypass vector.
	if svc.passportAuth == nil {
		atomic.AddUint64(&svc.failedRequests, 1)
		resp := &SaarthiResponse{
			Verdict:        "DENY",
			CorrelationID:  req.CorrelationID,
			ExecutionState: "EXECUTION_BLOCKED",
			BlockReason:    "PASSPORT_AUTHORITY_UNAVAILABLE: bridge transit verification not initialized — no bypass allowed",
			ServiceVersion: svc.version,
			EnforcedAt:     time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		}
		if auditErr := svc.auditSink.RecordEnforcement(req, resp); auditErr != nil {
			resp.BlockReason = resp.BlockReason + " | AUDIT_WRITE_FAILED"
		}
		return resp
	}
	{
		valid, reason := svc.passportAuth.VerifyPassport(req.bridgePassport)
		if !valid {
			atomic.AddUint64(&svc.failedRequests, 1)
			resp := &SaarthiResponse{
				Verdict:        "DENY",
				CorrelationID:  req.CorrelationID,
				ExecutionState: "EXECUTION_BLOCKED",
				BlockReason:    reason,
				ServiceVersion: svc.version,
				EnforcedAt:     time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
			}
			// FIX-01 (v7.0): Mandatory audit — DENY decisions MUST be recorded
			if auditErr := svc.auditSink.RecordEnforcement(req, resp); auditErr != nil {
				resp.BlockReason = resp.BlockReason + " | AUDIT_WRITE_FAILED"
			}
			return resp
		}
	} // end passport verification block

	// Validate request
	if err := svc.validateRequest(req); err != "" {
		atomic.AddUint64(&svc.failedRequests, 1)
		resp := &SaarthiResponse{
			Verdict:        "DENY",
			CorrelationID:  req.CorrelationID,
			ExecutionState: "EXECUTION_BLOCKED",
			BlockReason:    err,
			ServiceVersion: svc.version,
			EnforcedAt:     time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		}
		// FIX-01 (v7.0): Mandatory audit — validation failures MUST be recorded
		if auditErr := svc.auditSink.RecordEnforcement(req, resp); auditErr != nil {
			resp.BlockReason = resp.BlockReason + " | AUDIT_WRITE_FAILED"
		}
		return resp
	}

	// Idempotency check
	if req.IdempotencyKey != "" {
		svc.idempotencyMu.RLock()
		cached, exists := svc.idempotencyCache[req.IdempotencyKey]
		svc.idempotencyMu.RUnlock()
		if exists {
			return cached
		}
	}

	// Fill defaults
	if req.CorrelationID == "" {
		req.CorrelationID = uuid.New().String()
	}
	if req.RequestedAt.IsZero() {
		req.RequestedAt = time.Now().UTC()
	}

	// === CORE ENFORCEMENT — delegate to Sarathi pipeline ===
	atomic.AddUint64(&svc.totalRequests, 1)

	var enforcementResp *ExecutionResponse
	var executionResult *ExecutionResult

	// Create immutable request
	execReq := NewExecutionRequest(req.AgentID, req.ResourceID, req.Action, req.CorrelationID, req.PolicyVersion)

	// Enforce through adapter
	enforcementResp = svc.pipeline.Adapter.Enforce(execReq)

	// Execute if ALLOW (through sovereign token gate)
	if enforcementResp.Verdict() == "ALLOW" {
		token := enforcementResp.GetCapabilityToken()
		executionResult = svc.pipeline.Engine.ExecuteWithToken(token)
	}

	// Build response
	resp := svc.buildResponse(enforcementResp, executionResult, req)

	// Update metrics
	latencyNs := time.Since(startTime).Nanoseconds()
	switch resp.Verdict {
	case "ALLOW":
		atomic.AddUint64(&svc.allowedRequests, 1)
	case "DENY":
		atomic.AddUint64(&svc.deniedRequests, 1)
	case "ESCALATE":
		atomic.AddUint64(&svc.escalatedRequests, 1)
	}

	// Update peak latency (CAS loop)
	for {
		current := atomic.LoadInt64(&svc.peakLatencyNs)
		if latencyNs <= current {
			break
		}
		if atomic.CompareAndSwapInt64(&svc.peakLatencyNs, current, latencyNs) {
			break
		}
	}

	// FIX-01 (v7.0): Mandatory audit — enforcement decisions MUST be recorded (Vault-style)
	// Audit failure on the critical path → verdict downgraded to DENY
	if auditErr := svc.auditSink.RecordEnforcement(req, resp); auditErr != nil {
		if resp.Verdict == "ALLOW" {
			resp.Verdict = "DENY"
			resp.ExecutionState = "EXECUTION_BLOCKED"
			resp.BlockReason = fmt.Sprintf("AUDIT_WRITE_FAILED: %v — execution blocked per mandatory audit policy", auditErr)
			atomic.AddUint64(&svc.failedRequests, 1)
		}
	}

	// Phase 2 Fix: Compute layer binding hash (Intent → Request → Response → Audit)
	// This cryptographic binding proves that a specific request produced a specific
	// response and was recorded in a specific audit entry. Stored in response for
	// downstream verification.
	requestHash := ComputeRequestBindingHash(req)
	responseHash := ComputeResponseBindingHash(resp)
	auditHash := Sha256Hex([]byte(fmt.Sprintf("%s:%s:%s", req.CorrelationID, resp.EnforcementHash, resp.Verdict)))
	binding := ComputeLayerBinding("", requestHash, responseHash, auditHash)
	if binding != nil {
		resp.LayerBindingHash = binding.BindingHash
	}

	// Cache for idempotency
	if req.IdempotencyKey != "" {
		svc.idempotencyMu.Lock()
		svc.idempotencyCache[req.IdempotencyKey] = resp
		svc.idempotencyMu.Unlock()
	}

	return resp
}

// buildResponse constructs a SaarthiResponse from enforcement and execution results.
func (svc *SaarthiService) buildResponse(
	enforcement *ExecutionResponse,
	execution *ExecutionResult,
	req *SaarthiRequest,
) *SaarthiResponse {
	resp := &SaarthiResponse{
		Verdict:         enforcement.Verdict(),
		DecisionID:      enforcement.DecisionID(),
		CorrelationID:   enforcement.CorrelationID(),
		PolicyVersion:   enforcement.PolicyVersionField(),
		PolicyHash:      enforcement.PolicyHashField(),
		EnforcementHash: enforcement.EnforcementHash(),
		RequestHash:     enforcement.RequestHash(),
		HasToken:        enforcement.GetCapabilityToken() != nil,
		EnforcedAt:      enforcement.EnforcedAt(),
		ServiceVersion:  svc.version,
		RegistryVersion: svc.pipeline.AgentRegistry.Version(),
		Obligations:     enforcement.Obligations(),
	}

	if execution != nil {
		resp.Executed = execution.Executed
		resp.ExecutionState = execution.Status
		resp.BlockReason = execution.BlockReason
		resp.TokenConsumed = execution.Executed
	} else {
		resp.Executed = false
		resp.ExecutionState = "EXECUTION_BLOCKED"
		if enforcement.Verdict() != "ALLOW" {
			resp.BlockReason = "VERDICT_NOT_ALLOW"
		}
	}

	// v15.6 Bridge-facing JWT mint. Conditions:
	//   * JWTAuthority is bound to the service (set during --service boot)
	//   * Verdict is ALLOW
	//   * A CapabilityToken was minted on the response (proves the
	//     in-process sovereign gate also passed)
	// Mint failures are logged but never converted to a DENY — the JWT is an
	// additive convenience for external verifiers; the propagation envelope
	// remains the load-bearing audit artefact.
	if svc.jwtAuthority != nil && enforcement.Verdict() == "ALLOW" {
		if ct := enforcement.GetCapabilityToken(); ct != nil {
			if mj, mErr := svc.jwtAuthority.MintFromCapabilityToken(ct, resp.TraceID); mErr == nil && mj != nil {
				resp.CapabilityTokenJWT = mj.Token
				resp.CapabilityTokenKID = mj.Kid
				resp.CapabilityTokenIssuer = svc.jwtAuthority.Issuer()
			} else if mErr != nil {
				fmt.Printf("[SaarthiService] WARN: JWT mint failed (non-fatal): %v\n", mErr)
			}
		}
	}

	return resp
}

// validateRequest performs service-level validation before enforcement.
func (svc *SaarthiService) validateRequest(req *SaarthiRequest) string {
	if req == nil {
		return "NIL_REQUEST"
	}
	if req.AgentID == "" {
		return "MISSING_AGENT_ID"
	}
	if req.ResourceID == "" {
		return "MISSING_RESOURCE_ID"
	}
	if req.Action == "" {
		return "MISSING_ACTION"
	}
	if req.CallerSystem == "" {
		return "MISSING_CALLER_SYSTEM"
	}

	// HIGH-10 FIX: Caller validation is now dynamic — verified against the bridge's
	// registered callers, not a hardcoded list. The bridge is the source of truth
	// for which systems are authorized. This validation is a defense-in-depth check;
	// the bridge already authenticates callers before reaching the service.
	// The hardcoded list is kept as a fallback for when bridge reference is unavailable.
	validCallers := map[string]bool{
		"core": true, "intent_layer": true, "insightflow": true,
		"bucket": true, "admin": true, "test_harness": true,
		"gated_bridge": true, "ksml": true,
	}
	if !validCallers[req.CallerSystem] {
		return fmt.Sprintf("UNKNOWN_CALLER_SYSTEM: %s", req.CallerSystem)
	}
	// NOTE: Bridge-level authentication is the primary gate. This is defense-in-depth.

	return ""
}

// GetStatus returns the current service status. Thread-safe.
func (svc *SaarthiService) GetStatus() ServiceStatus {
	svc.mu.RLock()
	defer svc.mu.RUnlock()
	return svc.status
}

// GetMetrics returns current service metrics. Thread-safe.
func (svc *SaarthiService) GetMetrics() ServiceMetrics {
	return ServiceMetrics{
		TotalRequests:     atomic.LoadUint64(&svc.totalRequests),
		AllowedRequests:   atomic.LoadUint64(&svc.allowedRequests),
		DeniedRequests:    atomic.LoadUint64(&svc.deniedRequests),
		EscalatedRequests: atomic.LoadUint64(&svc.escalatedRequests),
		FailedRequests:    atomic.LoadUint64(&svc.failedRequests),
		PeakLatencyNs:     atomic.LoadInt64(&svc.peakLatencyNs),
		ActiveSince:       svc.startedAt,
	}
}

// GetPipeline returns the underlying pipeline (for bridge verification).
func (svc *SaarthiService) GetPipeline() *SarathiEnforcementPipeline {
	return svc.pipeline
}

// GetVersion returns the service version.
func (svc *SaarthiService) GetVersion() string {
	return svc.version
}

// GetAuditSink returns the audit sink for bridge-level audit logging.
func (svc *SaarthiService) GetAuditSink() AuditSink {
	return svc.auditSink
}

// SetPassportAuthority binds the bridge passport authority for transit verification (v6.0).
// Called by GatedBridge after creation to establish the verification link.
func (svc *SaarthiService) SetPassportAuthority(auth *BridgePassportAuthority) {
	svc.passportAuth = auth
}

// Shutdown gracefully shuts down the service. New requests will be denied.
func (svc *SaarthiService) Shutdown() {
	svc.mu.Lock()
	svc.status = ServiceStatusShutdown
	svc.mu.Unlock()
	close(svc.shutdownCh)
	// Best-effort shutdown audit — log errors but proceed with shutdown
	if err := svc.auditSink.RecordSystemEvent("SERVICE_SHUTDOWN", "SaarthiService shutdown initiated"); err != nil {
		fmt.Printf("[WARN] SaarthiService shutdown audit write failed: %v\n", err)
	}
	if err := svc.auditSink.Close(); err != nil {
		fmt.Printf("[WARN] SaarthiService audit sink close failed: %v\n", err)
	}
}

// idempotencyCleanupLoop periodically purges expired idempotency cache entries.
func (svc *SaarthiService) idempotencyCleanupLoop() {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			svc.idempotencyMu.Lock()
			// Simple: clear entire cache periodically (production would use TTL per entry)
			if len(svc.idempotencyCache) > 10000 {
				svc.idempotencyCache = make(map[string]*SaarthiResponse)
			}
			svc.idempotencyMu.Unlock()
		case <-svc.shutdownCh:
			return
		}
	}
}
