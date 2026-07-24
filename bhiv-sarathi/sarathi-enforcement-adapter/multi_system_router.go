package main

// multi_system_router.go — Multi-System Routing for BHIV Ecosystem.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Multi-System Router (v5.0)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   Routes approved execution results to downstream BHIV systems.
//   Routing happens ONLY after Saarthi enforcement approval — there is no
//   path from this router to any system that bypasses enforcement.
//
// ARCHITECTURE:
//   GatedBridge → SaarthiService → Enforcement → Execution
//                                                    ↓
//                                              MultiSystemRouter
//                                              ├── Execution Engine (already executed)
//                                              ├── InsightFlow (observability)
//                                              └── Bucket (audit storage)
//
//   The router does NOT make authorization decisions. It only distributes
//   the RESULTS of authorized executions to systems that need them.
//
// ROUTING RULES:
//   1. Each target system has its own verdict filter (AcceptedVerdicts)
//   2. InsightFlow and Bucket receive ALL verdicts (ALLOW, DENY, ESCALATE)
//   3. Core Workflow and Intent Layer receive ALLOW + DENY for state tracking
//   4. Routing failures do NOT affect the enforcement verdict
//   5. All routing events are audit-logged
//
// DESIGN REFERENCES:
//   - Apache Kafka: Topic-based event routing with consumer groups
//   - AWS EventBridge: Rule-based event routing to multiple targets
//   - Google Cloud Pub/Sub: Fan-out messaging with per-subscription filters
//   - CNCF CloudEvents: Standardized event format for cross-system routing
//   - Netflix Zuul: API gateway with dynamic routing rules

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"sync"
	"sync/atomic"
	"time"

	"github.com/google/uuid"
)

// ================================================================
// ROUTING TARGETS
// ================================================================

// RoutingTarget represents a downstream system that receives execution results.
type RoutingTarget struct {
	// Identity
	Name        string `json:"name"`         // e.g., "insightflow", "bucket"
	DisplayName string `json:"display_name"` // e.g., "BHIV InsightFlow"
	Version     string `json:"version"`

	// Routing configuration
	Active       bool     `json:"active"`
	AcceptedActions []string `json:"accepted_actions,omitempty"` // nil = accept all
	AcceptedVerdicts []string `json:"accepted_verdicts,omitempty"` // nil = only ALLOW

	// Delivery
	DeliveryMode string `json:"delivery_mode"` // "sync", "async", "best_effort"
	TimeoutMs    int    `json:"timeout_ms"`
	RetryCount   int    `json:"retry_count"` // 0 = no retry

	// IntelligenceReadOnly marks the target as a digest-only consumer of the
	// propagation envelope (e.g., Sri Satya's Intelligence Layer). Digest-only
	// targets:
	//   - Receive an IntelligenceDigestEvent (fingerprint hashes ONLY) instead
	//     of the sealed canonical response bytes.
	//   - Are NOT part of the determinism chain: their ACK is not compared
	//     against response_hash, and their failure never stops propagation.
	// Defaults to false — all production targets (Core, InsightFlow, Bucket)
	// are in-chain.
	IntelligenceReadOnly bool `json:"intelligence_read_only,omitempty"`

	// InChain marks the target as part of the cross-system determinism chain.
	// When RoutePropagation encounters a PropagationStopError on an in-chain
	// target, remaining in-chain targets receive a synthetic CHAIN_HALTED
	// audit event. Off-chain targets (including IntelligenceReadOnly) are
	// unaffected by chain halt. Defaults to false; enabled by
	// WireDeterministicTargets for the standard in-chain set.
	InChain bool `json:"in_chain,omitempty"`

	// Handler
	Handler RoutingHandler `json:"-"`
}

// RoutingHandler processes a routed result for a specific target system.
type RoutingHandler func(event *RoutedEvent) error

// RoutedEvent is the standardized event format sent to downstream systems.
// Modeled after CNCF CloudEvents specification.
type RoutedEvent struct {
	// CloudEvents-style envelope
	EventID     string    `json:"event_id"`
	EventType   string    `json:"event_type"`   // "enforcement.executed", "enforcement.denied"
	Source      string    `json:"source"`        // "sarathi/gated-bridge"
	Timestamp   time.Time `json:"timestamp"`
	ContentType string    `json:"content_type"`  // "application/json"

	// Enforcement data
	CorrelationID   string `json:"correlation_id"`
	AgentID         string `json:"agent_id"`
	ResourceID      string `json:"resource_id"`
	Action          string `json:"action"`
	Verdict         string `json:"verdict"`
	Executed        bool   `json:"executed"`
	ExecutionState  string `json:"execution_state"`
	EnforcementHash string `json:"enforcement_hash"`
	PolicyVersion   string `json:"policy_version"`
	PolicyHash      string `json:"policy_hash"`
	ServiceVersion  string `json:"service_version"`

	// Caller context
	CallerSystem  string `json:"caller_system"`
	CallerVersion string `json:"caller_version"`
}

// RoutingResult captures the outcome of routing to a single target.
type RoutingResult struct {
	TargetName string        `json:"target_name"`
	Delivered  bool          `json:"delivered"`
	Error      string        `json:"error,omitempty"`
	LatencyNs  int64         `json:"latency_ns"`
	Retries    int           `json:"retries"`
}

// ================================================================
// MULTI-SYSTEM ROUTER
// ================================================================

// MultiSystemRouter routes approved execution results to downstream BHIV systems.
// It is called by the GatedBridge ONLY after successful enforcement + execution.
type MultiSystemRouter struct {
	mu      sync.RWMutex
	targets map[string]*RoutingTarget

	// Audit
	auditSink AuditSink

	// Metrics (atomic)
	totalRouted       uint64
	totalDelivered    uint64
	totalFailed       uint64
	totalSkipped      uint64

	// Per-target metrics
	targetMetricsMu sync.Mutex
	targetDelivered map[string]uint64
	targetFailed    map[string]uint64

	// Event log (in-memory ring buffer for recent events)
	eventLogMu sync.Mutex
	eventLog   []RoutingResult
	maxLogSize int
}

// NewMultiSystemRouter creates a router with default BHIV ecosystem targets.
func NewMultiSystemRouter(auditSink AuditSink) *MultiSystemRouter {
	if auditSink == nil {
		auditSink = NewInMemoryAuditSink()
	}

	router := &MultiSystemRouter{
		targets:         make(map[string]*RoutingTarget),
		auditSink:       auditSink,
		targetDelivered: make(map[string]uint64),
		targetFailed:    make(map[string]uint64),
		eventLog:        make([]RoutingResult, 0, 1000),
		maxLogSize:      1000,
	}

	// Register default BHIV ecosystem targets
	router.registerDefaultTargets()

	return router
}

// registerDefaultTargets sets up the standard BHIV downstream systems.
func (r *MultiSystemRouter) registerDefaultTargets() {
	// InsightFlow — Observability & Analytics
	// Receives ALL execution results (both ALLOW and DENY) for monitoring
	r.targets["insightflow"] = &RoutingTarget{
		Name:             "insightflow",
		DisplayName:      "BHIV InsightFlow",
		Version:          "1.0.0",
		Active:           true,
		AcceptedVerdicts: []string{"ALLOW", "DENY", "ESCALATE"}, // Observes everything
		DeliveryMode:     "async",
		TimeoutMs:        2000,
		RetryCount:       2,
		Handler:          insightFlowHandler,
	}

	// Bucket — Audit Storage
	// Receives ALL verdicts (ALLOW, DENY, ESCALATE) for immutable audit archival
	// and full decision reconstruction. Every enforcement outcome must be preserved.
	r.targets["bucket"] = &RoutingTarget{
		Name:             "bucket",
		DisplayName:      "BHIV Bucket",
		Version:          "1.0.0",
		Active:           true,
		AcceptedVerdicts: []string{"ALLOW", "DENY", "ESCALATE"}, // Full audit reconstruction
		DeliveryMode:     "sync",
		TimeoutMs:        5000,
		RetryCount:       3, // Critical — retry harder
		Handler:          bucketHandler,
	}

	// Raj's Enforcement Engine — Execution Feedback
	// Receives ALLOW results to update enforcement state
	r.targets["core_workflow"] = &RoutingTarget{
		Name:             "core_workflow",
		DisplayName:      "BHIV Enforcement Engine",
		Version:          "1.0.0",
		Active:           true,
		AcceptedVerdicts: []string{"ALLOW", "DENY"}, // Needs both for enforcement state
		DeliveryMode:     "async",
		TimeoutMs:        3000,
		RetryCount:       1,
		Handler:          coreWorkflowHandler,
	}

	// Ishan's Evaluator Layer — Evaluation Feedback
	// Receives results to close evaluation loops
	r.targets["intent_layer"] = &RoutingTarget{
		Name:             "intent_layer",
		DisplayName:      "BHIV Evaluator Layer",
		Version:          "1.0.0",
		Active:           true,
		AcceptedVerdicts: []string{"ALLOW", "DENY"},
		DeliveryMode:     "async",
		TimeoutMs:        2000,
		RetryCount:       1,
		Handler:          intentLayerHandler,
	}
}

// ================================================================
// ROUTING LOGIC
// ================================================================

// RouteResult routes an execution result to all applicable downstream systems.
// Called by GatedBridge ONLY after enforcement + execution.
// Returns the list of systems that received the result.
func (r *MultiSystemRouter) RouteResult(req *SaarthiRequest, resp *SaarthiResponse) []string {
	r.mu.RLock()
	targets := make(map[string]*RoutingTarget, len(r.targets))
	for k, v := range r.targets {
		targets[k] = v
	}
	r.mu.RUnlock()

	// Build the routed event
	event := &RoutedEvent{
		EventID:         uuid.New().String(),
		EventType:       r.classifyEventType(resp),
		Source:          "sarathi/gated-bridge",
		Timestamp:       time.Now().UTC(),
		ContentType:     "application/json",
		CorrelationID:   resp.CorrelationID,
		AgentID:         req.AgentID,
		ResourceID:      req.ResourceID,
		Action:          req.Action,
		Verdict:         resp.Verdict,
		Executed:        resp.Executed,
		ExecutionState:  resp.ExecutionState,
		EnforcementHash: resp.EnforcementHash,
		PolicyVersion:   resp.PolicyVersion,
		PolicyHash:      resp.PolicyHash,
		ServiceVersion:  resp.ServiceVersion,
		CallerSystem:    req.CallerSystem,
		CallerVersion:   req.CallerVersion,
	}

	var routedTo []string
	atomic.AddUint64(&r.totalRouted, 1)

	for name, target := range targets {
		if !target.Active {
			atomic.AddUint64(&r.totalSkipped, 1)
			continue
		}

		// Check verdict filter
		if !r.matchesVerdictFilter(target, resp.Verdict) {
			atomic.AddUint64(&r.totalSkipped, 1)
			continue
		}

		// Check action filter
		if !r.matchesActionFilter(target, req.Action) {
			atomic.AddUint64(&r.totalSkipped, 1)
			continue
		}

		// Deliver
		result := r.deliverToTarget(target, event)

		// Record result
		r.recordRoutingResult(result)

		if result.Delivered {
			routedTo = append(routedTo, name)
			atomic.AddUint64(&r.totalDelivered, 1)
			r.targetMetricsMu.Lock()
			r.targetDelivered[name]++
			r.targetMetricsMu.Unlock()
			// Audit: record successful delivery
			_ = r.auditSink.RecordSystemEvent("ROUTING_DELIVERED",
				fmt.Sprintf("target=%s event=%s corr=%s verdict=%s",
					name, event.EventID, event.CorrelationID, event.Verdict))
		} else {
			atomic.AddUint64(&r.totalFailed, 1)
			r.targetMetricsMu.Lock()
			r.targetFailed[name]++
			r.targetMetricsMu.Unlock()
			// Audit: record delivery failure for investigation
			_ = r.auditSink.RecordSystemEvent("ROUTING_FAILED",
				fmt.Sprintf("target=%s event=%s corr=%s error=%s",
					name, event.EventID, event.CorrelationID, result.Error))
		}
	}

	return routedTo
}

// classifyEventType determines the CloudEvents event_type.
func (r *MultiSystemRouter) classifyEventType(resp *SaarthiResponse) string {
	if resp.Executed {
		return "enforcement.executed"
	}
	if resp.Verdict == "DENY" {
		return "enforcement.denied"
	}
	if resp.Verdict == "ESCALATE" {
		return "enforcement.escalated"
	}
	return "enforcement.blocked"
}

// matchesVerdictFilter checks if a target accepts this verdict.
func (r *MultiSystemRouter) matchesVerdictFilter(target *RoutingTarget, verdict string) bool {
	if len(target.AcceptedVerdicts) == 0 {
		// Default: only ALLOW
		return verdict == "ALLOW"
	}
	for _, v := range target.AcceptedVerdicts {
		if v == verdict {
			return true
		}
	}
	return false
}

// matchesActionFilter checks if a target accepts this action.
func (r *MultiSystemRouter) matchesActionFilter(target *RoutingTarget, action string) bool {
	if len(target.AcceptedActions) == 0 {
		return true // Accept all actions
	}
	for _, a := range target.AcceptedActions {
		if a == action {
			return true
		}
	}
	return false
}

// deliverToTarget attempts to deliver an event to a target with retries.
func (r *MultiSystemRouter) deliverToTarget(target *RoutingTarget, event *RoutedEvent) RoutingResult {
	start := time.Now()
	result := RoutingResult{
		TargetName: target.Name,
	}

	if target.Handler == nil {
		result.Delivered = false
		result.Error = "NO_HANDLER"
		result.LatencyNs = time.Since(start).Nanoseconds()
		return result
	}

	var lastErr error
	maxAttempts := 1 + target.RetryCount
	for attempt := 0; attempt < maxAttempts; attempt++ {
		result.Retries = attempt

		err := target.Handler(event)
		if err == nil {
			result.Delivered = true
			result.LatencyNs = time.Since(start).Nanoseconds()
			return result
		}

		lastErr = err

		// Wait before retry (exponential backoff: 100ms, 200ms, 400ms...)
		if attempt < maxAttempts-1 {
			backoff := time.Duration(100*(1<<uint(attempt))) * time.Millisecond
			time.Sleep(backoff)
		}
	}

	result.Delivered = false
	result.Error = lastErr.Error()
	result.LatencyNs = time.Since(start).Nanoseconds()
	return result
}

// recordRoutingResult appends a routing result to the ring buffer.
func (r *MultiSystemRouter) recordRoutingResult(result RoutingResult) {
	r.eventLogMu.Lock()
	defer r.eventLogMu.Unlock()

	if len(r.eventLog) >= r.maxLogSize {
		// Shift: drop oldest entry
		r.eventLog = r.eventLog[1:]
	}
	r.eventLog = append(r.eventLog, result)
}

// ================================================================
// TARGET MANAGEMENT
// ================================================================

// RegisterTarget adds a new downstream routing target.
func (r *MultiSystemRouter) RegisterTarget(target *RoutingTarget) error {
	if target.Name == "" {
		return fmt.Errorf("target name is required")
	}

	r.mu.Lock()
	defer r.mu.Unlock()

	if _, exists := r.targets[target.Name]; exists {
		return fmt.Errorf("target %q already registered", target.Name)
	}

	r.targets[target.Name] = target
	return nil
}

// DeactivateTarget deactivates a target. It will no longer receive routed events.
func (r *MultiSystemRouter) DeactivateTarget(name string) bool {
	r.mu.Lock()
	defer r.mu.Unlock()

	target, exists := r.targets[name]
	if !exists {
		return false
	}
	target.Active = false
	return true
}

// ReactivateTarget reactivates a previously deactivated target.
func (r *MultiSystemRouter) ReactivateTarget(name string) bool {
	r.mu.Lock()
	defer r.mu.Unlock()

	target, exists := r.targets[name]
	if !exists {
		return false
	}
	target.Active = true
	return true
}

// GetTarget returns a target by name, or nil if not found.
func (r *MultiSystemRouter) GetTarget(name string) *RoutingTarget {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.targets[name]
}

// ListTargets returns all registered targets.
func (r *MultiSystemRouter) ListTargets() []*RoutingTarget {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make([]*RoutingTarget, 0, len(r.targets))
	for _, t := range r.targets {
		cp := *t
		cp.Handler = nil // Don't expose handler functions
		result = append(result, &cp)
	}
	return result
}

// ================================================================
// METRICS
// ================================================================

// RouterMetrics holds operational metrics for the multi-system router.
type RouterMetrics struct {
	TotalRouted    uint64            `json:"total_routed"`
	TotalDelivered uint64            `json:"total_delivered"`
	TotalFailed    uint64            `json:"total_failed"`
	TotalSkipped   uint64            `json:"total_skipped"`
	PerTarget      map[string]TargetMetrics `json:"per_target"`
	ActiveTargets  int               `json:"active_targets"`
	TotalTargets   int               `json:"total_targets"`
}

// TargetMetrics holds per-target delivery metrics.
type TargetMetrics struct {
	Delivered uint64 `json:"delivered"`
	Failed    uint64 `json:"failed"`
}

// GetMetrics returns current router metrics.
func (r *MultiSystemRouter) GetMetrics() RouterMetrics {
	r.mu.RLock()
	activeCount := 0
	totalCount := len(r.targets)
	for _, t := range r.targets {
		if t.Active {
			activeCount++
		}
	}
	r.mu.RUnlock()

	r.targetMetricsMu.Lock()
	perTarget := make(map[string]TargetMetrics, len(r.targetDelivered))
	for name, delivered := range r.targetDelivered {
		perTarget[name] = TargetMetrics{
			Delivered: delivered,
			Failed:    r.targetFailed[name],
		}
	}
	r.targetMetricsMu.Unlock()

	return RouterMetrics{
		TotalRouted:    atomic.LoadUint64(&r.totalRouted),
		TotalDelivered: atomic.LoadUint64(&r.totalDelivered),
		TotalFailed:    atomic.LoadUint64(&r.totalFailed),
		TotalSkipped:   atomic.LoadUint64(&r.totalSkipped),
		PerTarget:      perTarget,
		ActiveTargets:  activeCount,
		TotalTargets:   totalCount,
	}
}

// GetRecentRoutingResults returns the most recent routing results.
func (r *MultiSystemRouter) GetRecentRoutingResults(limit int) []RoutingResult {
	r.eventLogMu.Lock()
	defer r.eventLogMu.Unlock()

	if limit <= 0 || limit > len(r.eventLog) {
		limit = len(r.eventLog)
	}

	// Return most recent entries
	start := len(r.eventLog) - limit
	result := make([]RoutingResult, limit)
	copy(result, r.eventLog[start:])
	return result
}

// ================================================================
// DEFAULT HANDLERS (SIMULATED)
// ================================================================
//
// These handlers simulate delivery to downstream BHIV systems.
// In production, these would be replaced with actual gRPC/HTTP clients.

// insightFlowHandler simulates delivery to InsightFlow (observability).
func insightFlowHandler(event *RoutedEvent) error {
	fmt.Printf("  [InsightFlow] Received event: correlation=%s verdict=%s action=%s agent=%s\n",
		event.CorrelationID, event.Verdict, event.Action, event.AgentID)
	return nil
}

// bucketHandler simulates delivery to Bucket (audit storage).
func bucketHandler(event *RoutedEvent) error {
	fmt.Printf("  [Bucket] Archived: correlation=%s enforcement_hash=%s...\n",
		event.CorrelationID, event.EnforcementHash[:min(16, len(event.EnforcementHash))])
	return nil
}

// coreWorkflowHandler simulates delivery to Raj's Enforcement Engine.
func coreWorkflowHandler(event *RoutedEvent) error {
	fmt.Printf("  [EnforcementEngine] State update: correlation=%s verdict=%s executed=%v\n",
		event.CorrelationID, event.Verdict, event.Executed)
	return nil
}

// intentLayerHandler simulates delivery to Ishan's Evaluator Layer.
func intentLayerHandler(event *RoutedEvent) error {
	fmt.Printf("  [EvaluatorLayer] Evaluation feedback: correlation=%s verdict=%s\n",
		event.CorrelationID, event.Verdict)
	return nil
}

// ================================================================
// PRODUCTION HTTP ROUTING HANDLER (v14.2 PHASE C)
// ================================================================
//
// HTTPRoutingHandler provides real HTTP delivery to downstream systems,
// replacing the fmt.Printf simulation stubs for production deployment.
//
// Features:
//   - Real HTTP POST delivery to downstream system endpoints
//   - Per-target circuit breaker (independent: one slow target doesn't
//     affect others)
//   - Bulkhead isolation (semaphore-based concurrency limiter per target)
//   - Backpressure detection (HTTP 429 Too Many Requests)
//   - Auth headers (Bearer token)
//   - Structured error classification
//
// SECURITY INVARIANTS:
//   - Routing happens ONLY after enforcement approval. The router
//     distributes RESULTS — it does not make authorization decisions.
//   - Routing failures do NOT affect the enforcement verdict.
//   - The enforcement chain and execution chain are already committed
//     before routing begins.
//
// Industry alignment:
//   - AWS EventBridge: Rule-based event routing with DLQ
//   - Google Pub/Sub: Per-subscription backpressure handling
//   - Netflix Zuul: Per-route circuit breakers
//   - Envoy Proxy: Per-upstream circuit breaking + outlier detection

// HTTPRoutingConfig configures a production HTTP routing handler.
type HTTPRoutingConfig struct {
	TargetURL        string            // downstream system endpoint
	AuthToken        string            // Bearer token for authentication
	Timeout          time.Duration     // per-request timeout
	Headers          map[string]string // custom headers
	CircuitBreaker   CircuitBreakerConfig // circuit breaker settings
	MaxConcurrency   int               // bulkhead concurrency limit
}

// NewHTTPRoutingHandler creates a production-grade HTTP routing handler.
// Returns a RoutingHandler closure that performs real HTTP delivery with
// circuit breaker, bulkhead isolation, and backpressure detection.
//
// The returned handler is wire-compatible with the existing RoutingHandler
// function type — it can directly replace any fmt.Printf stub handler.
func NewHTTPRoutingHandler(name string, config HTTPRoutingConfig) RoutingHandler {
	if config.Timeout <= 0 {
		config.Timeout = 5 * time.Second
	}
	if config.MaxConcurrency <= 0 {
		config.MaxConcurrency = 10
	}

	client := &http.Client{
		Timeout: config.Timeout,
	}
	cb := NewCircuitBreaker("route-"+name, config.CircuitBreaker)
	bulkhead := NewBulkheadLimiter("route-"+name, config.MaxConcurrency)

	return func(event *RoutedEvent) error {
		// Step 1: Bulkhead isolation — prevent one slow target from starving others
		if !bulkhead.Acquire() {
			return fmt.Errorf("BULKHEAD_FULL: target '%s' has %d concurrent requests — rejecting",
				name, config.MaxConcurrency)
		}
		defer bulkhead.Release()

		// Step 2: Circuit breaker check
		if !cb.Allow() {
			return fmt.Errorf("CIRCUIT_OPEN: target '%s' circuit breaker is open — failing closed", name)
		}

		// Step 3: Marshal event to JSON
		payload, err := json.Marshal(event)
		if err != nil {
			return fmt.Errorf("MARSHAL_ERROR: failed to marshal event for '%s': %w", name, err)
		}

		// Step 4: HTTP POST to downstream system
		req, err := http.NewRequest("POST", config.TargetURL, bytes.NewBuffer(payload))
		if err != nil {
			cb.RecordFailure()
			return fmt.Errorf("REQUEST_ERROR: failed to create request for '%s': %w", name, err)
		}

		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("X-Sarathi-Event-ID", event.EventID)
		req.Header.Set("X-Sarathi-Correlation-ID", event.CorrelationID)
		req.Header.Set("X-Sarathi-Event-Type", event.EventType)
		if config.AuthToken != "" {
			req.Header.Set("Authorization", "Bearer "+config.AuthToken)
		}
		for k, v := range config.Headers {
			req.Header.Set(k, v)
		}

		resp, err := client.Do(req)
		if err != nil {
			cb.RecordFailure()
			return fmt.Errorf("HTTP_ERROR: delivery to '%s' failed: %w", name, err)
		}
		defer resp.Body.Close()

		// Step 5: Handle response codes with backpressure awareness
		if resp.StatusCode >= 200 && resp.StatusCode < 300 {
			cb.RecordSuccess()
			return nil // Success
		}

		// 429 = backpressure signal — target is overwhelmed
		if resp.StatusCode == http.StatusTooManyRequests {
			cb.RecordFailure()
			return fmt.Errorf("BACKPRESSURE: target '%s' returned HTTP 429 (Too Many Requests) — backpressure detected",
				name)
		}

		// 5xx = transient server error
		if resp.StatusCode >= 500 {
			cb.RecordFailure()
			return fmt.Errorf("SERVER_ERROR: target '%s' returned HTTP %d", name, resp.StatusCode)
		}

		// 4xx = permanent client error (don't trip circuit breaker — it's our problem)
		return fmt.Errorf("CLIENT_ERROR: target '%s' returned HTTP %d", name, resp.StatusCode)
	}
}

// ================================================================
// PRODUCTION ROUTING WIRING (v14.2)
// ================================================================

// WireProductionTargets replaces simulation stub handlers with real HTTP
// handlers based on environment configuration. Called from main() after
// router creation. Only targets with configured URLs are upgraded —
// unconfigured targets keep their simulation handlers.
//
// Environment variables:
//   SARATHI_ROUTE_INSIGHTFLOW_URL — InsightFlow endpoint
//   SARATHI_ROUTE_BUCKET_URL      — Bucket endpoint
//   SARATHI_ROUTE_CORE_URL        — Core Workflow endpoint
//   SARATHI_ROUTE_INTENT_URL      — Intent Layer endpoint
//   SARATHI_ROUTE_AUTH_TOKEN       — Shared auth token for all targets
//   SARATHI_ROUTE_MAX_CONCURRENT  — Bulkhead concurrency per target
//   SARATHI_ROUTE_CB_THRESHOLD    — Circuit breaker failure threshold
func (r *MultiSystemRouter) WireProductionTargets() int {
	authToken := os.Getenv("SARATHI_ROUTE_AUTH_TOKEN")
	maxConcurrency := parseIntEnv("SARATHI_ROUTE_MAX_CONCURRENT", 10)
	cbThreshold := parseIntEnv("SARATHI_ROUTE_CB_THRESHOLD", 5)

	cbConfig := CircuitBreakerConfig{
		FailureThreshold:  cbThreshold,
		ResetTimeout:      30 * time.Second,
		HalfOpenMaxProbes: 2,
	}

	targetEnvMap := map[string]string{
		"insightflow":   "SARATHI_ROUTE_INSIGHTFLOW_URL",
		"bucket":        "SARATHI_ROUTE_BUCKET_URL",
		"core_workflow": "SARATHI_ROUTE_CORE_URL",
		"intent_layer":  "SARATHI_ROUTE_INTENT_URL",
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

		config := HTTPRoutingConfig{
			TargetURL:      url,
			AuthToken:      authToken,
			Timeout:        time.Duration(target.TimeoutMs) * time.Millisecond,
			CircuitBreaker: cbConfig,
			MaxConcurrency: maxConcurrency,
		}

		target.Handler = NewHTTPRoutingHandler(targetName, config)
		wired++
		fmt.Printf("  [Phase 14.2] Route '%s' → %s (cb_threshold=%d, bulkhead=%d)\n",
			targetName, url, cbThreshold, maxConcurrency)
	}

	return wired
}

// ================================================================
// PRINT UTILITIES
// ================================================================

// PrintRoutingTable prints a human-readable summary of routing targets.
func (r *MultiSystemRouter) PrintRoutingTable() {
	targets := r.ListTargets()
	fmt.Println("\n  ┌─── MULTI-SYSTEM ROUTING TABLE ───")
	fmt.Printf("  │ Targets: %d\n", len(targets))
	fmt.Println("  │")

	for _, t := range targets {
		status := "ACTIVE"
		if !t.Active {
			status = "INACTIVE"
		}
		fmt.Printf("  │ [%s] %s (%s) — %s\n", status, t.DisplayName, t.Name, t.Version)
		fmt.Printf("  │   delivery=%s  timeout=%dms  retries=%d\n",
			t.DeliveryMode, t.TimeoutMs, t.RetryCount)
		if len(t.AcceptedVerdicts) > 0 {
			fmt.Printf("  │   verdicts=%v\n", t.AcceptedVerdicts)
		}
		if len(t.AcceptedActions) > 0 {
			fmt.Printf("  │   actions=%v\n", t.AcceptedActions)
		}
	}

	metrics := r.GetMetrics()
	fmt.Println("  │")
	fmt.Printf("  │ Total routed: %d  Delivered: %d  Failed: %d  Skipped: %d\n",
		metrics.TotalRouted, metrics.TotalDelivered, metrics.TotalFailed, metrics.TotalSkipped)
	fmt.Println("  └───────────────────────────────────")
}
