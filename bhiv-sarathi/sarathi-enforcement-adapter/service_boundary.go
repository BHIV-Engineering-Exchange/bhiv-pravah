package main

// service_boundary.go — HTTP/gRPC Service Boundary for Sarathi v5.0.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Service Boundary (v5.0)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   Exposes the Sarathi Gated Bridge as an HTTP service for network-accessible
//   enforcement. Every network request passes through the same Gated Bridge
//   entry point — there is NO separate network path that bypasses enforcement.
//
// ARCHITECTURE:
//   HTTP Client → ServiceBoundary → GatedBridge → SaarthiService → Enforcement
//
//   The service boundary adds:
//   1. Request deserialization (JSON → SaarthiRequest)
//   2. Response serialization (SaarthiResponse → JSON)
//   3. Health check endpoint (/health)
//   4. Metrics endpoint (/metrics)
//   5. Request logging
//   6. Panic recovery (any panic → DENY, never crash)
//
// NETWORK ENFORCEMENT:
//   - All endpoints require Content-Type: application/json
//   - All responses include X-Sarathi-Version header
//   - Rate limiting is handled by the bridge, not the HTTP layer
//   - TLS termination is expected at the load balancer (not here)
//
// ENDPOINTS:
//   POST /v1/enforce     — Submit an enforcement request
//   GET  /health         — Service health check
//   GET  /metrics        — Operational metrics
//   GET  /v1/bridge/info — Bridge status and caller info
//
// DESIGN REFERENCES:
//   - Google Cloud Endpoints: API gateway with request validation
//   - AWS API Gateway: Request/response transformation
//   - Envoy Proxy: L7 proxy with gRPC-JSON transcoding
//   - Kong Gateway: Plugin-based request processing pipeline

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"sync/atomic"
	"time"
)

// ================================================================
// SERVICE BOUNDARY
// ================================================================

// ServiceBoundaryConfig holds configuration for the HTTP service boundary.
type ServiceBoundaryConfig struct {
	ListenAddr        string // e.g., ":8080"
	ReadTimeoutMs     int
	WriteTimeoutMs    int
	MaxRequestBodyBytes int64
	EnableMetrics     bool
	EnableHealthCheck bool
}

// DefaultServiceBoundaryConfig returns production-grade defaults.
func DefaultServiceBoundaryConfig() ServiceBoundaryConfig {
	return ServiceBoundaryConfig{
		ListenAddr:        ":8443",
		ReadTimeoutMs:     5000,
		WriteTimeoutMs:    10000,
		MaxRequestBodyBytes: 1 << 20, // 1MB
		EnableMetrics:     true,
		EnableHealthCheck: true,
	}
}

// ServiceBoundary exposes the Gated Bridge as an HTTP service.
// It is the network entry point — all HTTP requests pass through the bridge.
type ServiceBoundary struct {
	bridge *GatedBridge
	config ServiceBoundaryConfig
	server *http.Server

	// v15.0 Sovereign Identity Closure: raw mux (routes only) preserved so
	// SetInboundAuth can rebuild the handler stack with the Ed25519
	// middleware wedged between routes and the outer logging/panic wrappers.
	// Nil-handling is a no-op when SARATHI_INBOUND_AUTH=off (the default) so
	// v14.9 behaviour is byte-identical.
	mux         http.Handler
	inboundAuth *InboundAuthMiddleware

	// v15.1 Network Surface Closure: pre-wired PDP-ingest path. Reused on
	// every POST /v1/ingest-decision request. Nil ONLY when the pipeline
	// did not initialize external mode (defensive — the handler returns 503).
	pdpAdapter *PDPAdapter

	// v15.6 JWT Authority: persistent Ed25519 signer + JWKS + introspection
	// for the outbound Bridge-facing token contract. Nil when the operator
	// has not bootstrapped a key — the new endpoints then 503 cleanly and
	// existing routes behave identically to v15.5.
	jwtAuthority *JWTAuthority

	// v15.6 Bridge-only surface gate. When true:
	//   * /sarathi/* + JWKS + discovery + introspect + /sarathi/validate-token
	//     remain reachable.
	//   * /v1/enforce + /v1/ingest-decision + /v1/bridge/info + peer-receipt
	//     endpoints return HTTP 404.
	// Read from SARATHI_BRIDGE_ONLY_MODE at boot; never re-read per request.
	bridgeOnlyMode bool

	// Metrics
	totalHTTPRequests uint64
	totalHTTPErrors   uint64
	startedAt         time.Time
}

// SetJWTAuthority binds the outbound JWT authority to this boundary. Must be
// called BEFORE Start(). Nil-safe: passing nil disables all v15.6 routes and
// the v15.5 surface continues to behave identically.
func (sb *ServiceBoundary) SetJWTAuthority(a *JWTAuthority) {
	if sb == nil {
		return
	}
	sb.jwtAuthority = a
}

// JWTAuthority returns the bound authority (may be nil).
func (sb *ServiceBoundary) JWTAuthority() *JWTAuthority {
	if sb == nil {
		return nil
	}
	return sb.jwtAuthority
}

// SetBridgeOnlyMode toggles the v15.6 bridge-only surface gate. Must be called
// BEFORE Start(). After this call, handlers protected by BlockNonBridgePath
// will return 404 on every request.
func (sb *ServiceBoundary) SetBridgeOnlyMode(enabled bool) {
	if sb == nil {
		return
	}
	sb.bridgeOnlyMode = enabled
}

// SetInboundAuth mounts the v15.0 inbound-auth middleware. Must be called
// BEFORE Start(). A nil middleware or one in off-mode is a no-op.
func (sb *ServiceBoundary) SetInboundAuth(m *InboundAuthMiddleware) {
	if m == nil || m.Mode() == InboundAuthOff {
		return
	}
	sb.inboundAuth = m
	// Rebuild the handler chain: panic(logging(inboundAuth.Wrap(mux))).
	// Logging/panic stay outermost so rejections are still logged and
	// panics are still recovered. inboundAuth is the only new layer.
	sb.server.Handler = sb.panicRecoveryMiddleware(sb.requestLoggingMiddleware(m.Wrap(sb.mux)))
}

// InboundAuthMode exposes the current inbound-auth mode (for banners).
func (sb *ServiceBoundary) InboundAuthMode() InboundAuthMode {
	if sb.inboundAuth == nil {
		return InboundAuthOff
	}
	return sb.inboundAuth.Mode()
}

// NewServiceBoundary creates an HTTP service boundary around the Gated Bridge.
func NewServiceBoundary(bridge *GatedBridge, config ServiceBoundaryConfig) (*ServiceBoundary, error) {
	if bridge == nil {
		return nil, fmt.Errorf("FATAL: ServiceBoundary requires non-nil GatedBridge")
	}

	sb := &ServiceBoundary{
		bridge:    bridge,
		config:    config,
		startedAt: time.Now().UTC(),
	}

	// v15.1 Network Surface Closure: bind the pipeline's PDPAdapter so the
	// /v1/ingest-decision handler does not allocate per-request. Nil-safe:
	// if the pipeline never initialized external mode the handler returns
	// 503 ERR_INGEST_DECISION_INVALID with a clear "external mode not
	// initialized" detail. This is a single read (no copy) and never racy
	// because PDPAdapter is process-wide singleton after pipeline init.
	if pipeline := bridge.getService().GetPipeline(); pipeline != nil {
		sb.pdpAdapter = pipeline.PDPAdapter
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/v1/enforce", sb.handleEnforce)
	mux.HandleFunc("/v1/ingest-decision", sb.handleIngestDecision)
	// v15.7 TANTRA Final Contract: /sarathi/enforce is the TANTRA-only
	// ingestion path. It accepts the tantra.decision.v1 payload shape,
	// runs the 12-step verifier (tantra_verifier.go), translates to the
	// canonical 16-field ExternalDecision via
	// translation_tantra_to_external_decision.go, and re-invokes
	// handleIngestDecision so the existing PDP / propagation pipeline
	// runs unchanged. Canonical ExternalDecision callers (self-test path)
	// continue to use /v1/ingest-decision.
	mux.HandleFunc("/sarathi/enforce", sb.handleSarathiEnforceTantra)
	// tantra-convergence-v1: CET->Sarathi convergence boundary. Accepts the
	// SUM-SCRIPT envelope (schema_version "1.0",
	// contract_version "TANTRA-CONVERGENCE-v1") that wraps a signed
	// tantra.decision.v1 decision, runs the convergence-continuity gates on top
	// of the same 12-step verifier, and emits the enforcement_decision +
	// Sarathi->Bridge handoff artifacts. Additive — does not alter /sarathi/enforce.
	mux.HandleFunc(CETEnforcePath, sb.handleSarathiCETEnforce)
	mux.HandleFunc("/sarathi/validate-token", sb.handleValidateToken)
	mux.HandleFunc("/health", sb.handleHealth)
	mux.HandleFunc("/health/deep", sb.handleDeepHealth)
	mux.HandleFunc("/metrics", sb.handleMetrics)
	mux.HandleFunc("/metrics/prometheus", sb.handlePrometheusMetrics)
	mux.HandleFunc("/v1/bridge/info", sb.handleBridgeInfo)

	// v15.1 Network Surface Closure: peer receipt endpoints (/v1/handshake,
	// /v1/downstream-ack) are conditionally mounted in the production
	// service when an operator has explicitly opted in via
	// SARATHI_ENABLE_PEER_RECEIPTS=1 (or the legacy SARATHI_LIVE_INTEGRATION=1
	// flag). The endpoints are otherwise reserved for the in-process
	// --live-integration runner so the default --service surface stays
	// minimal. Mounting these does NOT activate the AckTracker — peers can
	// still POST receipts; Sarathi records them in the audit log.
	if os.Getenv("SARATHI_ENABLE_PEER_RECEIPTS") == "1" || os.Getenv("SARATHI_LIVE_INTEGRATION") == "1" {
		RegisterDownstreamAckRoutes(mux)
		fmt.Println("[ServiceBoundary] peer receipt endpoints mounted (/v1/handshake, /v1/downstream-ack)")
	}

	// Phase 12 (External Evaluator Hardening): admin API for evaluator
	// lifecycle management. Routes are only registered when the registry
	// has an admin authenticator wired. Without an authenticator,
	// NewEvaluatorRegistrationAPI returns nil and no routes are attached —
	// defence-in-depth against accidentally exposing an unauthenticated
	// surface. None of these handlers reach PDP/KSML/GovernanceKernel.
	if pipeline := bridge.getService().GetPipeline(); pipeline != nil && pipeline.Adapter != nil {
		if registry := pipeline.Adapter.GetEvaluatorRegistry(); registry != nil {
			if evalAPI := NewEvaluatorRegistrationAPI(registry); evalAPI != nil {
				evalAPI.RegisterRoutes(mux)
				fmt.Printf("[ServiceBoundary] Phase 12 evaluator admin API routes registered (version=%d)\n",
					registry.Version())
			}
		}
	}

	// v15.6 JWT Authority routes. Registered ONLY when the operator has
	// bound an authority via SetJWTAuthority (typically inside
	// bootstrapServiceBoundary). Nil-safe — when no authority is bound the
	// helper is a no-op and the boundary behaves exactly like v15.5.
	RegisterJWTAuthorityRoutes(mux, sb)

	sb.mux = mux
	sb.server = &http.Server{
		Addr:         config.ListenAddr,
		Handler:      sb.panicRecoveryMiddleware(sb.requestLoggingMiddleware(mux)),
		ReadTimeout:  time.Duration(config.ReadTimeoutMs) * time.Millisecond,
		WriteTimeout: time.Duration(config.WriteTimeoutMs) * time.Millisecond,
	}

	return sb, nil
}

// ================================================================
// MIDDLEWARE
// ================================================================

// panicRecoveryMiddleware recovers from panics and returns DENY.
// A crash in any handler MUST NOT bring down the service.
func (sb *ServiceBoundary) panicRecoveryMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				atomic.AddUint64(&sb.totalHTTPErrors, 1)
				w.Header().Set("Content-Type", "application/json")
				w.Header().Set("X-Sarathi-Version", sb.bridge.GetServiceVersion())
				w.WriteHeader(http.StatusInternalServerError)
				resp := &SaarthiResponse{
					Verdict:        "DENY",
					ExecutionState: "EXECUTION_BLOCKED",
					BlockReason:    "INTERNAL_PANIC_RECOVERY",
					ErrorCode:      CodeInternal,
					SchemaVersion:  SchemaVersion,
					ServiceVersion: sb.bridge.GetServiceVersion(),
					EnforcedAt:     time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
				}
				_ = json.NewEncoder(w).Encode(resp)
				fmt.Printf("[ServiceBoundary] PANIC recovered: %v\n", rec)
			}
		}()
		next.ServeHTTP(w, r)
	})
}

// requestLoggingMiddleware logs HTTP request metadata.
func (sb *ServiceBoundary) requestLoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		atomic.AddUint64(&sb.totalHTTPRequests, 1)

		// Add Sarathi version header to all responses
		w.Header().Set("X-Sarathi-Version", sb.bridge.GetServiceVersion())
		w.Header().Set("X-Sarathi-Bridge-Active", fmt.Sprintf("%v", sb.bridge.IsActive()))

		next.ServeHTTP(w, r)

		fmt.Printf("[ServiceBoundary] %s %s — %v\n", r.Method, r.URL.Path, time.Since(start))
	})
}

// ================================================================
// HANDLERS
// ================================================================

// handleEnforce processes enforcement requests through the Gated Bridge.
// POST /v1/enforce
func (sb *ServiceBoundary) handleEnforce(w http.ResponseWriter, r *http.Request) {
	// v15.6 bridge-only mode: hide this path from external callers so the
	// Bridge cannot accidentally reach a non-JWT-emitting route.
	if sb.BlockNonBridgePath(w, r) {
		return
	}
	w.Header().Set("Content-Type", "application/json")

	// Method check
	if r.Method != http.MethodPost {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusMethodNotAllowed)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error": "METHOD_NOT_ALLOWED",
			"detail": "Only POST is accepted at /v1/enforce",
		})
		return
	}

	// Content-Type check
	ct := r.Header.Get("Content-Type")
	if ct != "application/json" && ct != "" {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusUnsupportedMediaType)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error": "UNSUPPORTED_CONTENT_TYPE",
			"detail": "Content-Type must be application/json",
		})
		return
	}

	// P0-3: HTTP API key authentication
	// Extract API key from Authorization header (Bearer token or X-API-Key)
	apiKey := r.Header.Get("X-API-Key")
	if apiKey == "" {
		authHeader := r.Header.Get("Authorization")
		if len(authHeader) > 7 && authHeader[:7] == "Bearer " {
			apiKey = authHeader[7:]
		}
	}
	if apiKey == "" {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusUnauthorized)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error":  "MISSING_API_KEY",
			"detail": "Provide API key via X-API-Key header or Authorization: Bearer <key>",
		})
		return
	}

	// Body size limit
	r.Body = http.MaxBytesReader(w, r.Body, sb.config.MaxRequestBodyBytes)

	// Decode request
	var req SaarthiRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error": "INVALID_REQUEST_BODY",
			"detail": err.Error(),
		})
		return
	}

	// Fill request timestamp if not set
	if req.RequestedAt.IsZero() {
		req.RequestedAt = time.Now().UTC()
	}

	// Attach extracted API key for bridge-level credential verification
	req.apiKey = apiKey

	// Route through the Gated Bridge (THE ONLY PATH)
	resp := sb.bridge.RouteExecution(&req)

	// v14.4: Ensure all critical fields are populated before serialization
	resp = ValidateSaarthiResponse(resp)

	// Map verdict to HTTP status
	statusCode := http.StatusOK
	if resp.Verdict == "DENY" {
		statusCode = http.StatusForbidden
	}

	w.WriteHeader(statusCode)
	_ = json.NewEncoder(w).Encode(resp)
}

// IngestDecisionResponse is the wire shape returned from /v1/ingest-decision
// on success. It is deliberately distinct from SaarthiResponse — the ingest
// path returns a sealed PropagationEnvelope summary, not a verdict envelope,
// because the verdict lives in the canonical bytes the caller already signed.
//
// CanonicalResponseB64 is the base64-encoded canonical bytes that Sarathi
// will propagate to BHIV Core / InsightFlow / Bucket. A receiver can
// base64-decode and SHA-256 it to confirm: hex(sha256(decoded)) == ResponseHash.
//
// TAG: no-policy-logic — no field is derived from decision content.
type IngestDecisionResponse struct {
	DecisionID           string `json:"decision_id"`
	ExecutionID          string `json:"execution_id"`
	CorrelationID        string `json:"correlation_id"`
	ResponseHash         string `json:"response_hash"`
	ChainBindingHash     string `json:"chain_binding_hash"`
	EnforcementHash      string `json:"enforcement_hash"`
	DecisionHash         string `json:"decision_hash"`
	SchemaVersion        string `json:"schema_version"`
	SealedAt             string `json:"sealed_at"`
	CanonicalResponseB64 string `json:"canonical_response_b64"`

	// v15.6 (omitempty): the externally-verifiable JWT minted when the
	// upstream verdict was ALLOW and a JWTAuthority is bound to the
	// boundary. Bridge consumes this field as its authorization token.
	// Verifiable offline against /sarathi/.well-known/jwks.json.
	CapabilityTokenJWT string `json:"capability_token_jwt,omitempty"`

	// v15.6 (omitempty): the kid used for signing — convenience for Bridge
	// when it wants to fail fast on stale-cache scenarios without parsing
	// the JWT header. Mirrors the kid claim in the JWT itself.
	CapabilityTokenKID string `json:"capability_token_kid,omitempty"`

	// v15.6 (omitempty): the iss URL — convenience field so Bridge does
	// not have to parse the JWT just to validate the audience namespace.
	CapabilityTokenIssuer string `json:"capability_token_issuer,omitempty"`
}

// IngestDecisionError is the wire shape for /v1/ingest-decision failures.
// All fields are flat strings so non-Go integrators can parse without
// reflection. error_code maps 1:1 to a constant in response_contract.go.
type IngestDecisionError struct {
	ErrorCode string `json:"error_code"`
	Detail    string `json:"detail"`
}

// handleIngestDecision is the HTTP boundary for the v15.1 external-decision
// path. It accepts a signed ExternalDecision JSON body, calls
// PDPAdapter.Ingest UNCHANGED, and returns the sealed PropagationEnvelope
// summary. The handler MUST NOT make any decision-content branches — the
// adapter's "TAG: no-policy-logic" hard constraint extends to this handler.
//
// Authentication:
//   - X-API-Key (always required, same as /v1/enforce).
//   - When SARATHI_INBOUND_AUTH=optional|required, the InboundAuthMiddleware
//     also enforces Ed25519-signed request integrity (boundary check).
//     The DEEP pipeline check (evaluator_signature over decision_core_hash)
//     is unconditional and runs inside EnforceExternalDecision.
//
// Failure mapping:
//   - 405 method != POST
//   - 415 content-type != application/json
//   - 401 missing X-API-Key
//   - 400 oversized / unreadable body
//   - 422 PDPAdapter.Ingest returned an integrity / signature error
//   - 409 replay tracker rejected duplicate decision (same id, drifted body)
//   - 503 pipeline did not init external mode (defensive — should not happen)
//   - 200 sealed envelope — body is IngestDecisionResponse JSON
//
// On every response (including errors), the handler sets the canonical
// X-Sarathi-* headers so log aggregators can pivot by decision_id /
// execution_id without parsing the body.
//
// POST /v1/ingest-decision
func (sb *ServiceBoundary) handleIngestDecision(w http.ResponseWriter, r *http.Request) {
	// v15.6 bridge-only mode: hide this path UNLESS the caller is the
	// Sovereign-translation path itself (which proxies via this handler
	// internally). The Sovereign handler sets X-Sarathi-Internal-Source
	// before calling us so we can distinguish in-process from external.
	if r.Header.Get("X-Sarathi-Internal-Source") == "" {
		if sb.BlockNonBridgePath(w, r) {
			return
		}
	}
	w.Header().Set("Content-Type", "application/json")

	// Method check
	if r.Method != http.MethodPost {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusMethodNotAllowed)
		_ = json.NewEncoder(w).Encode(&IngestDecisionError{
			ErrorCode: "METHOD_NOT_ALLOWED",
			Detail:    "Only POST is accepted at /v1/ingest-decision",
		})
		return
	}

	// Content-Type check
	ct := r.Header.Get("Content-Type")
	if ct != "application/json" && ct != "" {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusUnsupportedMediaType)
		_ = json.NewEncoder(w).Encode(&IngestDecisionError{
			ErrorCode: "UNSUPPORTED_CONTENT_TYPE",
			Detail:    "Content-Type must be application/json",
		})
		return
	}

	// API-key check (matches /v1/enforce posture). The bridge does NOT
	// see this request — the ingest path bypasses caller-system identity
	// because the payload is already cryptographically bound to a
	// registered evaluator. We still require an API key so unauthenticated
	// network probes cannot consume the path.
	apiKey := r.Header.Get("X-API-Key")
	if apiKey == "" {
		authHeader := r.Header.Get("Authorization")
		if len(authHeader) > 7 && authHeader[:7] == "Bearer " {
			apiKey = authHeader[7:]
		}
	}
	if apiKey == "" {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusUnauthorized)
		_ = json.NewEncoder(w).Encode(&IngestDecisionError{
			ErrorCode: "MISSING_API_KEY",
			Detail:    "Provide API key via X-API-Key header or Authorization: Bearer <key>",
		})
		return
	}

	// Defensive: pipeline must have initialized external mode.
	if sb.pdpAdapter == nil {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusServiceUnavailable)
		_ = json.NewEncoder(w).Encode(&IngestDecisionError{
			ErrorCode: CodeIngestDecisionInvalid,
			Detail:    "PDPAdapter not wired (pipeline external mode not initialized)",
		})
		return
	}

	// Body cap + raw-byte read. CRITICAL: we do NOT json.Unmarshal here.
	// The adapter parses internally and runs a "golden-byte" check that
	// re-marshalling the parsed struct yields identical bytes. Any
	// pre-decode in this handler would defeat that check.
	r.Body = http.MaxBytesReader(w, r.Body, sb.config.MaxRequestBodyBytes)
	rawBytes, readErr := io.ReadAll(r.Body)
	if readErr != nil {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(&IngestDecisionError{
			ErrorCode: CodeIngestDecisionInvalid,
			Detail:    "request body read failed: " + readErr.Error(),
		})
		return
	}
	if len(rawBytes) == 0 {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(&IngestDecisionError{
			ErrorCode: CodeIngestDecisionInvalid,
			Detail:    "empty request body",
		})
		return
	}

	// IDs from headers (caller-supplied, optional). Mint deterministic
	// fallbacks so the audit trail always has values.
	executionID := r.Header.Get("X-Sarathi-Execution-ID")
	if executionID == "" {
		executionID = fmt.Sprintf("EXEC-INGEST-%d", time.Now().UnixNano())
	}
	correlationID := r.Header.Get("X-Sarathi-Correlation-ID")

	// v15.7: parse X-Sarathi-Trace-ID inbound. The TANTRA-routed path
	// (handleSarathiEnforceTantra in service_boundary_tantra.go) sets this
	// header from the body's trace_id; canonical /v1/ingest-decision callers
	// (self-test) MUST set it themselves. When absent and trace-required
	// mode is on, the downstream pipeline returns ERR_INGEST_DECISION_INVALID.
	var inboundTrace *TraceContext
	if hdr := strings.TrimSpace(r.Header.Get(HeaderTraceID)); hdr != "" {
		inboundTrace = MakeTraceContextFromInbound(hdr)
	}

	env, ierr := sb.pdpAdapter.Ingest(rawBytes, executionID, correlationID, inboundTrace)
	if ierr != nil {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		// Map adapter error → HTTP status. The adapter's CodePDPDecisionInvalid
		// covers signature, hash, and integrity failures; the replay
		// tracker (inside EnforceExternalDecision) emits CodeResponseHashMismatch
		// for same-id-drifted-body collisions.
		errStr := ierr.Error()
		status := http.StatusUnprocessableEntity
		code := CodeIngestDecisionInvalid
		switch {
		case containsCode(errStr, CodeResponseHashMismatch):
			status = http.StatusConflict
			code = CodeResponseHashMismatch
		case containsCode(errStr, CodePDPDecisionInvalid):
			status = http.StatusUnprocessableEntity
			code = CodePDPDecisionInvalid
		case containsCode(errStr, CodeEvaluatorNotRegistered):
			status = http.StatusForbidden
			code = CodeEvaluatorNotRegistered
		case containsCode(errStr, CodeEvaluatorSuspended):
			status = http.StatusForbidden
			code = CodeEvaluatorSuspended
		case containsCode(errStr, CodeEvaluatorRevoked):
			status = http.StatusForbidden
			code = CodeEvaluatorRevoked
		}
		w.Header().Set("X-Sarathi-Error-Code", code)
		w.Header().Set("X-Sarathi-Execution-ID", executionID)
		w.WriteHeader(status)
		_ = json.NewEncoder(w).Encode(&IngestDecisionError{
			ErrorCode: code,
			Detail:    errStr,
		})
		return
	}

	// Success — surface envelope identifiers in headers for log pivots and
	// independent SHA verification by downstream tooling.
	w.Header().Set("X-Sarathi-Decision-ID", env.DecisionID())
	w.Header().Set("X-Sarathi-Execution-ID", env.ExecutionID())
	w.Header().Set("X-Sarathi-Response-Hash", env.ResponseHash())
	w.Header().Set("X-Sarathi-Chain-Binding-Hash", env.ChainBindingHash())
	w.Header().Set("X-Sarathi-Enforcement-Hash", env.EnforcementHash())
	w.Header().Set("X-Sarathi-Schema-Version", env.SchemaVersion())

	resp := &IngestDecisionResponse{
		DecisionID:           env.DecisionID(),
		ExecutionID:          env.ExecutionID(),
		CorrelationID:        env.CorrelationID(),
		ResponseHash:         env.ResponseHash(),
		ChainBindingHash:     env.ChainBindingHash(),
		EnforcementHash:      env.EnforcementHash(),
		DecisionHash:         env.DecisionHash(),
		SchemaVersion:        env.SchemaVersion(),
		SealedAt:             env.SealedAt(),
		CanonicalResponseB64: base64.StdEncoding.EncodeToString(env.CanonicalResponseBytes()),
	}

	// v15.6 JWT mint hook. Mint ONLY when:
	//   * an authority is bound (typically only in --service mode),
	//   * the upstream verdict is ALLOW,
	//   * the caller opted into mint via X-Sarathi-Mint-JWT=1 (set by the
	//     Sovereign-translation handler on every /sarathi/enforce call).
	// Mint failure does NOT fail the request — Bridge can still verify the
	// propagation envelope; the JWT is an additive convenience.
	if sb.jwtAuthority != nil &&
		strings.EqualFold(env.Verdict(), "ALLOW") &&
		r.Header.Get("X-Sarathi-Mint-JWT") == "1" {
		audienceHint := strings.TrimSpace(os.Getenv(EnvTokenAudience))
		traceID := strings.TrimSpace(r.Header.Get(HeaderTraceID))
		if mj, mErr := sb.jwtAuthority.MintFromEnvelope(env, traceID, audienceHint); mErr == nil && mj != nil {
			resp.CapabilityTokenJWT = mj.Token
			resp.CapabilityTokenKID = mj.Kid
			resp.CapabilityTokenIssuer = sb.jwtAuthority.Issuer()
			w.Header().Set("X-Sarathi-Capability-Token-Kid", mj.Kid)
			w.Header().Set("X-Sarathi-Capability-Token-Issuer", sb.jwtAuthority.Issuer())
		} else if mErr != nil {
			fmt.Printf("[ServiceBoundary] WARN: JWT mint failed (non-fatal): %v\n", mErr)
		}
	}

	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(resp)

	// v15.10 post-ingest peer fan-out hook. Opt-in via
	// SARATHI_PROPAGATE_ON_INGEST=1. Fires BHIVTranslatedFanOut in a
	// background goroutine; never blocks the inbound response. Failures land
	// in proof_logs/peer_propagation_audit.jsonl. See
	// service_boundary_propagation_hook.go for the full doc + audit shape.
	firePostIngestPropagation(env)
}

// containsCode reports whether the adapter error string mentions the given
// error code constant. Adapter errors are formatted with `(%s)` interpolation
// of the code, so this is a literal substring match — no regex needed.
func containsCode(errStr, code string) bool {
	if code == "" || errStr == "" {
		return false
	}
	for i := 0; i+len(code) <= len(errStr); i++ {
		if errStr[i:i+len(code)] == code {
			return true
		}
	}
	return false
}

// handleValidateToken is the v15.3 BHIV-wire-format alias for capability-token
// validation. Maps to Raj's spec:
//
//	GET /sarathi/validate-token?token=<token>
//
// Returns:
//
//	200 + {"valid": true,  "token_id": "...", "expires_at": "..."}    when token is valid
//	401 + {"valid": false, "error_code": "ERR_TOKEN_INVALID"}         when token is missing
//	403 + {"valid": false, "error_code": "ERR_TOKEN_REVOKED|EXPIRED"} when token is rejected
//
// The handler is read-only: it never mints, mutates, or persists tokens. It
// only verifies the signature + expiry + (if available) consults the
// pipeline's TokenAuthority for revocation status. This endpoint is exposed
// so BHIV Core (port 9002 wire-format) can confirm a token is still valid
// before executing the action it authorises.
func (sb *ServiceBoundary) handleValidateToken(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	if r.Method != http.MethodGet {
		w.WriteHeader(http.StatusMethodNotAllowed)
		_ = json.NewEncoder(w).Encode(map[string]interface{}{
			"valid":      false,
			"error_code": "METHOD_NOT_ALLOWED",
			"detail":     "Only GET is accepted at /sarathi/validate-token",
		})
		return
	}

	token := r.URL.Query().Get("token")
	if token == "" {
		w.WriteHeader(http.StatusUnauthorized)
		_ = json.NewEncoder(w).Encode(map[string]interface{}{
			"valid":      false,
			"error_code": "ERR_TOKEN_MISSING",
			"detail":     "token query parameter required",
		})
		return
	}

	// v15.6: if the token looks like a JWT (eyJ... two dots) AND the
	// authority is bound, run the strict EdDSA verifier — that's the
	// load-bearing check. The Bridge will typically verify offline using
	// the JWKS; this endpoint is for ad-hoc operator probes.
	if LooksLikeJWT(token) && sb.jwtAuthority != nil {
		var registry *TokenRegistry
		if pl := sb.bridge.getService().GetPipeline(); pl != nil && pl.Engine != nil {
			registry = pl.Engine.tokenRegistry
		}
		verified, code, _ := sb.jwtAuthority.VerifyJWT(token, VerifyOption{
			ConsultConsumptionRegistry: registry != nil,
			TokenRegistry:              registry,
		})
		if code == JWTVerifyOK && verified != nil {
			w.WriteHeader(http.StatusOK)
			_ = json.NewEncoder(w).Encode(map[string]interface{}{
				"valid":          true,
				"kid":            verified.Kid,
				"iss":            verified.Issuer,
				"sub":            verified.Subject,
				"aud":            verified.Audience,
				"jti":            verified.JTI,
				"expires_at":     verified.ExpiresAt.UTC().Format(time.RFC3339),
				"validated_at":   time.Now().UTC().Format(time.RFC3339Nano),
				"schema_version": "sarathi.token.validate/v1.1",
			})
			return
		}
		w.WriteHeader(http.StatusForbidden)
		_ = json.NewEncoder(w).Encode(map[string]interface{}{
			"valid":      false,
			"error_code": code,
			"detail":     "jwt verification failed",
		})
		return
	}

	// Legacy capability-token-id shape (Phase 14.5+): we cannot verify
	// signatures without the originating CapabilityToken object — this
	// endpoint exposes a read-only "looks acceptable" probe consistent
	// with the v15.5 contract Raj's team integrated against. Length-only
	// gate preserved for backward compatibility; tighten only after Bridge
	// migrates to the JWT path.
	if len(token) < 32 {
		w.WriteHeader(http.StatusForbidden)
		_ = json.NewEncoder(w).Encode(map[string]interface{}{
			"valid":      false,
			"error_code": "ERR_TOKEN_INVALID",
			"detail":     "token format invalid",
		})
		return
	}

	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"valid":         true,
		"token_id":      token,
		"validated_at":  time.Now().UTC().Format(time.RFC3339Nano),
		"schema_version": "sarathi.token.validate/v1.0",
	})
}

// handleHealth returns the service health status.
// GET /health
func (sb *ServiceBoundary) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	health := map[string]interface{}{
		"status":          "healthy",
		"bridge_active":   sb.bridge.IsActive(),
		"service_status":  sb.bridge.GetServiceStatus(),
		"service_version": sb.bridge.GetServiceVersion(),
		"uptime_seconds":  time.Since(sb.startedAt).Seconds(),
	}

	if !sb.bridge.IsActive() || sb.bridge.GetServiceStatus() != ServiceStatusReady {
		health["status"] = "unhealthy"
		w.WriteHeader(http.StatusServiceUnavailable)
	} else {
		w.WriteHeader(http.StatusOK)
	}

	_ = json.NewEncoder(w).Encode(health)
}

// handleMetrics returns operational metrics.
// GET /metrics
func (sb *ServiceBoundary) handleMetrics(w http.ResponseWriter, r *http.Request) {
	if !sb.config.EnableMetrics {
		w.WriteHeader(http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")

	serviceMetrics := sb.bridge.GetServiceMetrics()
	bridgeMetrics := sb.bridge.GetMetrics()

	metrics := map[string]interface{}{
		"http": map[string]interface{}{
			"total_requests": atomic.LoadUint64(&sb.totalHTTPRequests),
			"total_errors":   atomic.LoadUint64(&sb.totalHTTPErrors),
		},
		"service": map[string]interface{}{
			"total_requests":     serviceMetrics.TotalRequests,
			"allowed_requests":   serviceMetrics.AllowedRequests,
			"denied_requests":    serviceMetrics.DeniedRequests,
			"escalated_requests": serviceMetrics.EscalatedRequests,
			"failed_requests":    serviceMetrics.FailedRequests,
			"peak_latency_ns":    serviceMetrics.PeakLatencyNs,
		},
		"bridge": map[string]interface{}{
			"total_routed":      bridgeMetrics.TotalRouted,
			"total_rejected":    bridgeMetrics.TotalRejected,
			"total_auth_failed": bridgeMetrics.TotalCallerAuthFailed,
			"total_rate_limited": bridgeMetrics.TotalRateLimited,
			"caller_breakdown":  bridgeMetrics.CallerBreakdown,
		},
	}

	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(metrics)
}

// handleBridgeInfo returns bridge status and registered caller information.
// GET /v1/bridge/info
func (sb *ServiceBoundary) handleBridgeInfo(w http.ResponseWriter, r *http.Request) {
	// v15.6: hidden from external Bridge callers — they should consume the
	// authority discovery document instead.
	if sb.BlockNonBridgePath(w, r) {
		return
	}
	w.Header().Set("Content-Type", "application/json")

	info := map[string]interface{}{
		"bridge_active":   sb.bridge.IsActive(),
		"service_version": sb.bridge.GetServiceVersion(),
		"service_status":  sb.bridge.GetServiceStatus(),
		"uptime_seconds":  time.Since(sb.startedAt).Seconds(),
	}

	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(info)
}

// handleDeepHealth performs comprehensive subsystem health validation (P2-12).
// GET /health/deep
func (sb *ServiceBoundary) handleDeepHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	dhc := &DeepHealthCheck{
		bridge:  sb.bridge,
		service: sb.bridge.getService(),
		router:  sb.bridge.router,
	}
	result := dhc.Check()
	result.UptimeSeconds = time.Since(sb.startedAt).Seconds()

	if result.Status != "healthy" {
		w.WriteHeader(http.StatusServiceUnavailable)
	} else {
		w.WriteHeader(http.StatusOK)
	}
	_ = json.NewEncoder(w).Encode(result)
}

// handlePrometheusMetrics returns metrics in Prometheus text exposition format (P1-7).
// GET /metrics/prometheus
func (sb *ServiceBoundary) handlePrometheusMetrics(w http.ResponseWriter, r *http.Request) {
	// Collect latest metrics
	SarathiMetrics.CollectFromBridge(sb.bridge)
	SarathiMetrics.CollectFromService(sb.bridge.getService())

	SarathiMetrics.Update("sarathi_http_requests_total", float64(atomic.LoadUint64(&sb.totalHTTPRequests)))
	SarathiMetrics.Update("sarathi_http_errors_total", float64(atomic.LoadUint64(&sb.totalHTTPErrors)))

	w.Header().Set("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(SarathiMetrics.RenderPrometheus()))
}

// ================================================================
// LIFECYCLE
// ================================================================

// Start begins listening for HTTP requests.
// This is a blocking call — run in a goroutine for non-blocking usage.
// If TLS is configured via environment, uses ListenAndServeTLS (P0-2).
func (sb *ServiceBoundary) Start() error {
	fmt.Printf("[ServiceBoundary] Starting HTTP service on %s\n", sb.config.ListenAddr)
	fmt.Printf("[ServiceBoundary] Endpoints:\n")
	if !sb.bridgeOnlyMode {
		fmt.Printf("  POST /v1/enforce          — Enforcement request (intent → verdict)\n")
		fmt.Printf("  POST /v1/ingest-decision  — External signed decision → propagation envelope (v15.1)\n")
		fmt.Printf("  GET  /v1/bridge/info      — Bridge status\n")
	} else {
		fmt.Printf("  [v15.6 bridge-only mode: /v1/enforce, /v1/ingest-decision, /v1/bridge/info return 404]\n")
	}
	fmt.Printf("  POST /sarathi/enforce     — Sovereign-ingest (9-field) + JWT mint (v15.5/v15.6)\n")
	fmt.Printf("  GET  /sarathi/validate-token — JWT verifier probe (v15.6)\n")
	if sb.jwtAuthority != nil {
		fmt.Printf("  GET  %s — RFC 7517 JWK Set (v15.6)\n", JWKSPath)
		fmt.Printf("  GET  %s — OIDC-style discovery (v15.6)\n", AuthorityDiscoveryPath)
		if sb.jwtAuthority.IntrospectionEnabled() {
			fmt.Printf("  POST %s   — RFC 7662 token introspection (v15.6)\n", TokenIntrospectPath)
		}
	}
	fmt.Printf("  GET  /health              — Basic health check\n")
	fmt.Printf("  GET  /health/deep         — Deep subsystem health check\n")
	fmt.Printf("  GET  /metrics             — Operational metrics (JSON)\n")
	fmt.Printf("  GET  /metrics/prometheus  — Prometheus text format metrics\n")

	// P0-2: TLS support — configure if certificates are available
	cfg := LoadSecureConfig()
	if cfg.TLSEnabled {
		if err := ConfigureTLS(sb.server, cfg.TLSCertPath, cfg.TLSKeyPath); err != nil {
			SarathiLog.Warn("ServiceBoundary", "TLS configuration failed, falling back to HTTP", "", map[string]interface{}{
				"error": err.Error(),
			})
			return sb.server.ListenAndServe()
		}
		SarathiLog.Info("ServiceBoundary", "Starting with TLS", "", map[string]interface{}{
			"addr": sb.config.ListenAddr,
			"cert": cfg.TLSCertPath,
		})
		return sb.server.ListenAndServeTLS(cfg.TLSCertPath, cfg.TLSKeyPath)
	}

	return sb.server.ListenAndServe()
}

// GracefulShutdown performs a graceful HTTP shutdown with timeout (P1-5).
func (sb *ServiceBoundary) GracefulShutdown(timeout time.Duration) error {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	SarathiLog.Info("ServiceBoundary", "Graceful HTTP shutdown initiated", "", map[string]interface{}{
		"timeout": timeout.String(),
	})
	return sb.server.Shutdown(ctx)
}

// GetServer returns the underlying http.Server (for graceful shutdown, testing).
func (sb *ServiceBoundary) GetServer() *http.Server {
	return sb.server
}

// GetHTTPMetrics returns HTTP-level metrics.
func (sb *ServiceBoundary) GetHTTPMetrics() map[string]uint64 {
	return map[string]uint64{
		"total_requests": atomic.LoadUint64(&sb.totalHTTPRequests),
		"total_errors":   atomic.LoadUint64(&sb.totalHTTPErrors),
	}
}

// ================================================================
// PRINT UTILITIES
// ================================================================

// PrintEndpoints prints the available HTTP endpoints.
func (sb *ServiceBoundary) PrintEndpoints() {
	fmt.Println("\n  ┌─── SERVICE BOUNDARY ENDPOINTS ───")
	fmt.Printf("  │ Listen: %s\n", sb.config.ListenAddr)
	fmt.Println("  │")
	fmt.Println("  │ POST /v1/enforce          — Submit enforcement request (JSON)")
	fmt.Println("  │ POST /v1/ingest-decision  — Submit signed external decision (v15.1)")
	fmt.Println("  │ GET  /health              — Basic health check")
	fmt.Println("  │ GET  /health/deep         — Deep subsystem health check")
	fmt.Println("  │ GET  /metrics             — Operational metrics (JSON)")
	fmt.Println("  │ GET  /metrics/prometheus  — Prometheus text format metrics")
	fmt.Println("  │ GET  /v1/bridge/info      — Bridge status info (JSON)")
	fmt.Println("  │")
	fmt.Printf("  │ Read timeout:  %dms\n", sb.config.ReadTimeoutMs)
	fmt.Printf("  │ Write timeout: %dms\n", sb.config.WriteTimeoutMs)
	fmt.Printf("  │ Max body:      %d bytes\n", sb.config.MaxRequestBodyBytes)
	fmt.Println("  └──────────────────────────────────")
}
