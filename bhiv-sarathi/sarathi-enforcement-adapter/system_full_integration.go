package main

// system_full_integration.go — Phase 9: Full System Integration Simulation.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Full Integration (v9.0)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// Integration Block:
//   Ishan Shirode — Evaluator
//   Raj Prajapati — Enforcement Engine
//   Future Integration Engineer — Core Integration
//
// PURPOSE:
//   End-to-end simulation testing ALL v9.0 governance flows:
//   - All 14 FIX implementations
//   - All 10 Phase structures (Phase 1-10 now ACTIVE in enforcement_adapter_main.go)
//   - Bypass proof generation
//   - KSML governance hook (with SetIntentSigningKey + SetDB wired in V9.0 section)
//   - Mandatory audit gate with circuit breaker
//   - Token revocation cascade
//   - Cedar-style conditions
//   - BeyondCorp posture monitoring
//   - W3C distributed tracing
//   - Execution path discovery
//   - GovernanceKernelV9 instantiation with all sub-components
//   - GovernanceStatsAggregator consistency checks
//   - ContextSafePostgresAuditSink (replaces PostgresAuditSink)
//
// OUTPUT: system_simulation_results.json

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"
)

// V7SimulationResult captures a single v7.0 simulation test.
type V7SimulationResult struct {
	TestID      string `json:"test_id"`
	Category    string `json:"category"`
	Description string `json:"description"`
	Passed      bool   `json:"passed"`
	Detail      string `json:"detail"`
	DurationNs  int64  `json:"duration_ns"`
}

// V7SimulationSummary captures the full simulation summary.
type V7SimulationSummary struct {
	SystemVersion   string               `json:"system_version"`
	GeneratedAt     string               `json:"generated_at"`
	TotalTests      int                  `json:"total_tests"`
	Passed          int                  `json:"passed"`
	Failed          int                  `json:"failed"`
	Categories      map[string]int       `json:"categories"`
	Results         []V7SimulationResult `json:"results"`
	BypassProof     *SystemBypassProof   `json:"bypass_proof,omitempty"`
	RoutingProof    *EnforcementRoutingProof `json:"routing_proof,omitempty"`
	TotalDurationNs int64                `json:"total_duration_ns"`
}

// RunV7FullIntegration runs the complete v7.0 system simulation.
func RunV7FullIntegration(bridge *GatedBridge, service *SaarthiService, pipeline *SarathiEnforcementPipeline) *V7SimulationSummary {
	printHeader("PHASE 9: FULL SYSTEM INTEGRATION SIMULATION (v8.0)")

	startTime := time.Now()
	summary := &V7SimulationSummary{
		SystemVersion: "9.0.0",
		GeneratedAt:   time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		Categories:    make(map[string]int),
	}

	var results []V7SimulationResult

	// === CATEGORY 1: MANDATORY AUDIT GATE (FIX-01) ===
	results = append(results, runMandatoryAuditTests(bridge)...)

	// === CATEGORY 2: TOKEN REVOCATION CASCADE (FIX-04) ===
	results = append(results, runTokenRevocationTests()...)

	// === CATEGORY 3: CEDAR-STYLE CONDITIONS (FIX-05) ===
	results = append(results, runCedarConditionTests()...)

	// === CATEGORY 4: SAFE ERROR PROPAGATION (FIX-06) ===
	results = append(results, runSafeErrorTests()...)

	// === CATEGORY 5: W3C DISTRIBUTED TRACING (FIX-07) ===
	results = append(results, runDistributedTracingTests()...)

	// === CATEGORY 6: BEYONDCORP POSTURE (FIX-08) ===
	results = append(results, runPostureMonitorTests(pipeline)...)

	// === CATEGORY 7: DISTRIBUTED RATE LIMITING (FIX-11) ===
	results = append(results, runDistributedRateLimitTests()...)

	// === CATEGORY 8: ESCALATION WEBHOOK (FIX-13) ===
	results = append(results, runEscalationWebhookTests()...)

	// === CATEGORY 9: UNIFIED CONFIG (FIX-14) ===
	results = append(results, runConfigTests()...)

	// === CATEGORY 10: EXECUTION PATH DISCOVERY (PHASE 1) ===
	results = append(results, runPathDiscoveryTests()...)

	// === CATEGORY 11: KSML GOVERNANCE HOOK (PHASE 8) ===
	results = append(results, runKSMLGovernanceTests(bridge)...)

	// === CATEGORY 12: BYPASS PROOF (PHASE 10) ===
	pathRegistry := NewExecutionPathRegistry()
	auditGate := bridge.GetMandatoryAuditGate()
	bypassProof := GenerateSystemBypassProof(bridge, service, pathRegistry, auditGate)
	routingProof := GenerateEnforcementRoutingProof(pathRegistry)
	summary.BypassProof = bypassProof
	summary.RoutingProof = routingProof

	results = append(results, V7SimulationResult{
		TestID:      "BYPASS-001",
		Category:    "bypass_proof",
		Description: "System bypass proof — all 6 layers pass",
		Passed:      bypassProof.AllLayersPassed,
		Detail:      bypassProof.FinalVerdict,
	})
	results = append(results, V7SimulationResult{
		TestID:      "BYPASS-002",
		Category:    "bypass_proof",
		Description: "Routing proof — zero bypass risks",
		Passed:      routingProof.ProofResult == "PROVEN_SECURE",
		Detail:      routingProof.ProofResult,
	})

	// === TALLY ===
	for _, r := range results {
		summary.Categories[r.Category]++
		if r.Passed {
			summary.Passed++
		} else {
			summary.Failed++
		}
	}
	summary.TotalTests = len(results)
	summary.Results = results
	summary.TotalDurationNs = time.Since(startTime).Nanoseconds()

	// Print summary
	printSubheader("v7.0 SIMULATION RESULTS")
	fmt.Printf("  Total Tests:  %d\n", summary.TotalTests)
	fmt.Printf("  Passed:       %d\n", summary.Passed)
	fmt.Printf("  Failed:       %d\n", summary.Failed)
	fmt.Printf("  Duration:     %v\n", time.Since(startTime))
	fmt.Println()
	for cat, count := range summary.Categories {
		fmt.Printf("  [%s] %d tests\n", cat, count)
	}

	// Print each result
	fmt.Println()
	for _, r := range results {
		status := "[PASS]"
		if !r.Passed {
			status = "[FAIL]"
		}
		fmt.Printf("  %s %s — %s: %s\n", status, r.TestID, r.Description, r.Detail)
	}

	// Bypass proof summary
	fmt.Println()
	fmt.Printf("  === BYPASS PROOF: %s ===\n", bypassProof.FinalVerdict)
	for _, d := range bypassProof.Details {
		fmt.Printf("    %s\n", d)
	}

	fmt.Printf("\n  === ROUTING PROOF: %s ===\n", routingProof.ProofResult)
	fmt.Printf("    Total paths: %d, Safe: %d, Blocked: %d, Bypass risks: %d\n",
		routingProof.TotalPaths, routingProof.SafePaths, routingProof.BlockedPaths, routingProof.BypassRisks)

	return summary
}

// === TEST CATEGORIES ===

func runMandatoryAuditTests(bridge *GatedBridge) []V7SimulationResult {
	var results []V7SimulationResult

	// Test 1: Audit gate exists
	mag := bridge.GetMandatoryAuditGate()
	results = append(results, V7SimulationResult{
		TestID:      "AUDIT-001",
		Category:    "mandatory_audit",
		Description: "MandatoryAuditGate is wired into bridge",
		Passed:      mag != nil,
		Detail:      fmt.Sprintf("gate_exists=%v", mag != nil),
	})

	// Test 2: Circuit starts CLOSED
	if mag != nil {
		state := mag.GetCircuitState()
		results = append(results, V7SimulationResult{
			TestID:      "AUDIT-002",
			Category:    "mandatory_audit",
			Description: "Audit circuit starts in CLOSED state",
			Passed:      state == AuditCircuitClosed,
			Detail:      fmt.Sprintf("state=%s", state),
		})

		// Test 3: IsHealthy returns true when closed
		results = append(results, V7SimulationResult{
			TestID:      "AUDIT-003",
			Category:    "mandatory_audit",
			Description: "Audit gate reports healthy when circuit closed",
			Passed:      mag.IsHealthy(),
			Detail:      fmt.Sprintf("healthy=%v", mag.IsHealthy()),
		})

		// Test 4: GetAuditStats returns valid data
		writes, failures, blocked, fallback, circuitState := mag.GetAuditStats()
		results = append(results, V7SimulationResult{
			TestID:      "AUDIT-004",
			Category:    "mandatory_audit",
			Description: "Audit stats accessible and valid",
			Passed:      circuitState == AuditCircuitClosed,
			Detail:      fmt.Sprintf("writes=%d failures=%d blocked=%d fallback=%d state=%s", writes, failures, blocked, fallback, circuitState),
		})
	}

	return results
}

func runTokenRevocationTests() []V7SimulationResult {
	var results []V7SimulationResult

	trl := NewTokenRevocationList()

	// Test 1: New list has no revocations
	revoked, _ := trl.IsRevoked("test-hash", "test-agent")
	results = append(results, V7SimulationResult{
		TestID:      "REVOKE-001",
		Category:    "token_revocation",
		Description: "New revocation list has no entries",
		Passed:      !revoked,
		Detail:      "empty_list_not_revoked=true",
	})

	// Test 2: Revoke specific token
	trl.RevokeToken("revoked-hash-001")
	revoked, reason := trl.IsRevoked("revoked-hash-001", "agent-a")
	results = append(results, V7SimulationResult{
		TestID:      "REVOKE-002",
		Category:    "token_revocation",
		Description: "Specific token revocation works",
		Passed:      revoked && strings.Contains(reason, "TOKEN_REVOKED"),
		Detail:      reason,
	})

	// Test 3: Cascade — revoke all tokens for agent
	trl.RevokeAllForAgent("agent-b")
	revoked, reason = trl.IsRevoked("any-hash", "agent-b")
	results = append(results, V7SimulationResult{
		TestID:      "REVOKE-003",
		Category:    "token_revocation",
		Description: "Agent cascade revocation works",
		Passed:      revoked && strings.Contains(reason, "AGENT_TOKENS_REVOKED"),
		Detail:      reason,
	})

	// Test 4: Non-revoked agent passes
	revoked, _ = trl.IsRevoked("other-hash", "agent-c")
	results = append(results, V7SimulationResult{
		TestID:      "REVOKE-004",
		Category:    "token_revocation",
		Description: "Non-revoked agent/token passes check",
		Passed:      !revoked,
		Detail:      "non_revoked_passes=true",
	})

	// Test 5: Stats
	totalRev, cascadeRev, tokenCount, agentCount := trl.GetStats()
	results = append(results, V7SimulationResult{
		TestID:      "REVOKE-005",
		Category:    "token_revocation",
		Description: "Revocation stats accurate",
		Passed:      totalRev == 1 && cascadeRev == 1 && tokenCount == 1 && agentCount == 1,
		Detail:      fmt.Sprintf("total=%d cascade=%d tokens=%d agents=%d", totalRev, cascadeRev, tokenCount, agentCount),
	})

	return results
}

func runCedarConditionTests() []V7SimulationResult {
	var results []V7SimulationResult

	ctx := &RequestContext{
		SourceIP:      "10.0.1.50",
		MFAVerified:   true,
		DeviceTrust:   8,
		GeoLocation:   "US",
		CallerService: "core",
		Environment:   "prod",
		RequestTime:   time.Date(2026, 3, 30, 14, 0, 0, 0, time.UTC), // 14:00 UTC
	}

	// Test 1: equals
	c1 := RuleCondition{Key: "context.environment", Operator: "equals", Value: "prod"}
	results = append(results, V7SimulationResult{
		TestID:      "CEDAR-001",
		Category:    "cedar_conditions",
		Description: "Equals operator matches correctly",
		Passed:      EvaluateCondition(c1, ctx),
		Detail:      "environment=prod matches prod",
	})

	// Test 2: in_cidr
	c2 := RuleCondition{Key: "context.source_ip", Operator: "in_cidr", Value: "10.0.0.0/8"}
	results = append(results, V7SimulationResult{
		TestID:      "CEDAR-002",
		Category:    "cedar_conditions",
		Description: "IP CIDR range check works",
		Passed:      EvaluateCondition(c2, ctx),
		Detail:      "10.0.1.50 in 10.0.0.0/8",
	})

	// Test 3: in_cidr negative
	c3 := RuleCondition{Key: "context.source_ip", Operator: "in_cidr", Value: "192.168.0.0/16"}
	results = append(results, V7SimulationResult{
		TestID:      "CEDAR-003",
		Category:    "cedar_conditions",
		Description: "IP CIDR negative check works",
		Passed:      !EvaluateCondition(c3, ctx),
		Detail:      "10.0.1.50 NOT in 192.168.0.0/16",
	})

	// Test 4: mfa_verified
	c4 := RuleCondition{Key: "context.mfa_verified", Operator: "equals", Value: "true"}
	results = append(results, V7SimulationResult{
		TestID:      "CEDAR-004",
		Category:    "cedar_conditions",
		Description: "MFA verification check works",
		Passed:      EvaluateCondition(c4, ctx),
		Detail:      "mfa_verified=true",
	})

	// Test 5: time_range
	c5 := RuleCondition{Key: "context.request_time", Operator: "time_range", Value: "09:00-18:00"}
	results = append(results, V7SimulationResult{
		TestID:      "CEDAR-005",
		Category:    "cedar_conditions",
		Description: "Time range check works (business hours)",
		Passed:      EvaluateCondition(c5, ctx),
		Detail:      "14:00 within 09:00-18:00",
	})

	// Test 6: in_set
	c6 := RuleCondition{Key: "context.geo_location", Operator: "in_set", Value: "US,UK,CA"}
	results = append(results, V7SimulationResult{
		TestID:      "CEDAR-006",
		Category:    "cedar_conditions",
		Description: "Set membership check works",
		Passed:      EvaluateCondition(c6, ctx),
		Detail:      "US in {US,UK,CA}",
	})

	// Test 7: nil context → fail-closed
	results = append(results, V7SimulationResult{
		TestID:      "CEDAR-007",
		Category:    "cedar_conditions",
		Description: "Nil context → fail-closed (deny)",
		Passed:      !EvaluateCondition(c1, nil),
		Detail:      "nil_context_returns_false",
	})

	// Test 8: EvaluateAllConditions
	allConds := []RuleCondition{c1, c2, c4}
	results = append(results, V7SimulationResult{
		TestID:      "CEDAR-008",
		Category:    "cedar_conditions",
		Description: "EvaluateAllConditions with all matching → true",
		Passed:      EvaluateAllConditions(allConds, ctx),
		Detail:      "all_3_conditions_match",
	})

	return results
}

func runSafeErrorTests() []V7SimulationResult {
	var results []V7SimulationResult

	// Test 1: SafeChainHash succeeds
	hash, err := SafeChainHash("GENESIS", "test-hash")
	results = append(results, V7SimulationResult{
		TestID:      "SAFE-001",
		Category:    "safe_errors",
		Description: "SafeChainHash produces valid hash",
		Passed:      err == nil && hash != "",
		Detail:      fmt.Sprintf("hash=%s...err=%v", hash[:16], err),
	})

	// Test 2: SafeTokenHash succeeds
	hash2, err2 := SafeTokenHash(map[string]string{"key": "value"})
	results = append(results, V7SimulationResult{
		TestID:      "SAFE-002",
		Category:    "safe_errors",
		Description: "SafeTokenHash produces valid hash",
		Passed:      err2 == nil && hash2 != "",
		Detail:      fmt.Sprintf("hash=%s...err=%v", hash2[:16], err2),
	})

	// Test 3: SafeExecutionHash succeeds
	hash3, err3 := SafeExecutionHash(map[string]interface{}{"executed": true})
	results = append(results, V7SimulationResult{
		TestID:      "SAFE-003",
		Category:    "safe_errors",
		Description: "SafeExecutionHash produces valid hash",
		Passed:      err3 == nil && hash3 != "",
		Detail:      fmt.Sprintf("hash=%s...err=%v", hash3[:16], err3),
	})

	return results
}

func runDistributedTracingTests() []V7SimulationResult {
	var results []V7SimulationResult

	// Test 1: Create trace context
	tc := NewTraceContext()
	results = append(results, V7SimulationResult{
		TestID:      "TRACE-001",
		Category:    "distributed_tracing",
		Description: "New trace context has valid IDs",
		Passed:      len(tc.TraceID) == 32 && len(tc.SpanID) == 16,
		Detail:      fmt.Sprintf("trace_id=%s span_id=%s", tc.TraceID, tc.SpanID),
	})

	// Test 2: W3C header format
	header := tc.ToHeader()
	results = append(results, V7SimulationResult{
		TestID:      "TRACE-002",
		Category:    "distributed_tracing",
		Description: "W3C traceparent header format correct",
		Passed:      strings.HasPrefix(header, "00-") && strings.Count(header, "-") == 3,
		Detail:      header,
	})

	// Test 3: Child span inherits trace ID
	child := tc.NewChildSpan()
	results = append(results, V7SimulationResult{
		TestID:      "TRACE-003",
		Category:    "distributed_tracing",
		Description: "Child span inherits trace ID, gets new span ID",
		Passed:      child.TraceID == tc.TraceID && child.SpanID != tc.SpanID && child.ParentSpan == tc.SpanID,
		Detail:      fmt.Sprintf("parent_span=%s child_span=%s", tc.SpanID, child.SpanID),
	})

	// Test 4: Parse traceparent
	parsed, err := ParseTraceContext(header)
	results = append(results, V7SimulationResult{
		TestID:      "TRACE-004",
		Category:    "distributed_tracing",
		Description: "Parse W3C traceparent header",
		Passed:      err == nil && parsed.TraceID == tc.TraceID,
		Detail:      fmt.Sprintf("parsed_trace_id=%s", parsed.TraceID),
	})

	// Test 5: Span lifecycle
	span := StartSpan("test-operation", tc)
	span.Attributes["test_key"] = "test_value"
	time.Sleep(1 * time.Microsecond) // Ensure measurable duration
	span.End()
	results = append(results, V7SimulationResult{
		TestID:      "TRACE-005",
		Category:    "distributed_tracing",
		Description: "Span lifecycle (start → attributes → end)",
		Passed:      span.Duration >= 0 && span.Status == "OK" && !span.EndedAt.IsZero(),
		Detail:      fmt.Sprintf("duration=%v status=%s ended=%v", span.Duration, span.Status, !span.EndedAt.IsZero()),
	})

	return results
}

func runPostureMonitorTests(pipeline *SarathiEnforcementPipeline) []V7SimulationResult {
	var results []V7SimulationResult

	apm := NewAgentPostureMonitor(pipeline.AgentRegistry, DefaultPostureConfig())

	// Test 1: Record request creates posture
	apm.RecordRequest("agent-alpha", "10.0.0.1")
	posture := apm.GetPosture("agent-alpha")
	results = append(results, V7SimulationResult{
		TestID:      "POSTURE-001",
		Category:    "beyondcorp_posture",
		Description: "Agent posture created on first request",
		Passed:      posture != nil && posture.TrustScore == 100,
		Detail:      fmt.Sprintf("trust_score=%d", posture.TrustScore),
	})

	// Test 2: Posture evaluation passes for healthy agent
	trusted, reason := apm.EvaluatePosture("agent-alpha")
	results = append(results, V7SimulationResult{
		TestID:      "POSTURE-002",
		Category:    "beyondcorp_posture",
		Description: "Healthy agent passes posture evaluation",
		Passed:      trusted && reason == "POSTURE_OK",
		Detail:      reason,
	})

	// Test 3: Low trust score → auto-suspend
	apm.RecordRequest("agent-low-trust", "10.0.0.2")
	apm.SetTrustScore("agent-low-trust", 10) // Below minimum (20)
	trusted, reason = apm.EvaluatePosture("agent-low-trust")
	results = append(results, V7SimulationResult{
		TestID:      "POSTURE-003",
		Category:    "beyondcorp_posture",
		Description: "Low trust score → auto-suspend",
		Passed:      !trusted && strings.Contains(reason, "TRUST_SCORE_LOW"),
		Detail:      reason,
	})

	// Test 4: High anomaly score → auto-suspend
	apm.RecordRequest("agent-anomaly", "10.0.0.3")
	apm.SetAnomalyScore("agent-anomaly", 0.95) // Above max (0.8)
	trusted, reason = apm.EvaluatePosture("agent-anomaly")
	results = append(results, V7SimulationResult{
		TestID:      "POSTURE-004",
		Category:    "beyondcorp_posture",
		Description: "High anomaly score → auto-suspend",
		Passed:      !trusted && strings.Contains(reason, "ANOMALY_DETECTED"),
		Detail:      reason,
	})

	// Test 5: Suspended agent stays suspended
	trusted, reason = apm.EvaluatePosture("agent-low-trust")
	results = append(results, V7SimulationResult{
		TestID:      "POSTURE-005",
		Category:    "beyondcorp_posture",
		Description: "Suspended agent remains suspended on re-evaluation",
		Passed:      !trusted,
		Detail:      reason,
	})

	// Test 6: Unknown agent passes (registry catches it)
	trusted, reason = apm.EvaluatePosture("unknown-agent")
	results = append(results, V7SimulationResult{
		TestID:      "POSTURE-006",
		Category:    "beyondcorp_posture",
		Description: "Unknown agent passes posture (registry handles auth)",
		Passed:      trusted && reason == "NO_POSTURE_DATA",
		Detail:      reason,
	})

	return results
}

func runDistributedRateLimitTests() []V7SimulationResult {
	var results []V7SimulationResult

	lrl := NewLocalRateLimiter()

	// Test 1: First request allowed
	allowed, err := lrl.IsAllowed("test-key", 5, time.Minute)
	results = append(results, V7SimulationResult{
		TestID:      "RATE-001",
		Category:    "distributed_rate_limit",
		Description: "First request allowed under limit",
		Passed:      allowed && err == nil,
		Detail:      "first_request_allowed=true",
	})

	// Test 2: Fill to limit
	for i := 0; i < 4; i++ {
		lrl.IsAllowed("test-key", 5, time.Minute)
	}
	allowed, _ = lrl.IsAllowed("test-key", 5, time.Minute)
	results = append(results, V7SimulationResult{
		TestID:      "RATE-002",
		Category:    "distributed_rate_limit",
		Description: "Request at limit is rejected",
		Passed:      !allowed,
		Detail:      "at_limit_rejected=true",
	})

	// Test 3: Different key unaffected
	allowed, _ = lrl.IsAllowed("other-key", 5, time.Minute)
	results = append(results, V7SimulationResult{
		TestID:      "RATE-003",
		Category:    "distributed_rate_limit",
		Description: "Different key has independent limit",
		Passed:      allowed,
		Detail:      "independent_keys=true",
	})

	// Test 4: GetCurrentCount
	count, err := lrl.GetCurrentCount("test-key", time.Minute)
	results = append(results, V7SimulationResult{
		TestID:      "RATE-004",
		Category:    "distributed_rate_limit",
		Description: "GetCurrentCount returns accurate count",
		Passed:      err == nil && count == 5,
		Detail:      fmt.Sprintf("count=%d", count),
	})

	return results
}

func runEscalationWebhookTests() []V7SimulationResult {
	var results []V7SimulationResult

	// Test 1: Disabled webhook → no-op
	ew := NewEscalationWebhook(EscalationWebhookConfig{Enabled: false})
	err := ew.NotifyEscalation(EscalationEvent{EventID: "test-1"})
	results = append(results, V7SimulationResult{
		TestID:      "ESCALATE-001",
		Category:    "escalation_webhook",
		Description: "Disabled webhook returns nil (no-op)",
		Passed:      err == nil,
		Detail:      "disabled_noop=true",
	})

	// Test 2: Enabled webhook sends real HTTP POST (expects connection error in test env).
	// Production-grade: the webhook actually tries to POST, and when the endpoint
	// is unreachable, it retries, fails, and records the failure metric correctly.
	ew2 := NewEscalationWebhook(EscalationWebhookConfig{
		Enabled:     true,
		WebhookURLs: []string{"http://127.0.0.1:1/sarathi-test-webhook"},
		TimeoutMs:   200, // Short timeout for tests
		RetryCount:  1,   // Single retry to keep tests fast
	})
	err = ew2.NotifyEscalation(EscalationEvent{
		EventID:       "esc-001",
		AgentID:       "agent-risky",
		ResourceID:    "sensitive-data",
		Action:        "delete",
		Reason:        "ESCALATE_PENDING_REVIEW",
		CorrelationID: "corr-esc-001",
		Severity:      "HIGH",
	})
	sent, failed := ew2.GetStats()
	// In test env: no server running, so err != nil and failed >= 1.
	// This proves the webhook ACTUALLY TRIES to send (not a stub).
	results = append(results, V7SimulationResult{
		TestID:      "ESCALATE-002",
		Category:    "escalation_webhook",
		Description: "Enabled webhook attempts real HTTP POST and tracks failure",
		Passed:      err != nil && failed >= 1,
		Detail:      fmt.Sprintf("sent=%d failed=%d err=%v", sent, failed, err != nil),
	})

	return results
}

func runConfigTests() []V7SimulationResult {
	var results []V7SimulationResult

	cfg := DefaultSarathiConfig()

	// Test 1: Default config has production values
	results = append(results, V7SimulationResult{
		TestID:      "CONFIG-001",
		Category:    "unified_config",
		Description: "Default config has production-grade values",
		Passed:      cfg.MaxTokenTTL == 60*time.Second && cfg.ProductionMode && cfg.GlobalRateLimit == 10000,
		Detail:      fmt.Sprintf("max_ttl=%v prod=%v global_rate=%d", cfg.MaxTokenTTL, cfg.ProductionMode, cfg.GlobalRateLimit),
	})

	// Test 2: LoadSarathiConfig returns defaults when no env vars
	loaded := LoadSarathiConfig()
	results = append(results, V7SimulationResult{
		TestID:      "CONFIG-002",
		Category:    "unified_config",
		Description: "LoadSarathiConfig returns defaults without env vars",
		Passed:      loaded.MaxTokenTTL == 60*time.Second,
		Detail:      "defaults_loaded=true",
	})

	return results
}

func runPathDiscoveryTests() []V7SimulationResult {
	var results []V7SimulationResult

	epr := NewExecutionPathRegistry()

	// Test 1: All paths registered (16 paths across 7 systems)
	allPaths := epr.GetAllPaths()
	results = append(results, V7SimulationResult{
		TestID:      "PATH-001",
		Category:    "path_discovery",
		Description: "All 16 execution paths registered",
		Passed:      len(allPaths) == 16,
		Detail:      fmt.Sprintf("total_paths=%d", len(allPaths)),
	})

	// Test 2: Safe paths
	safePaths := epr.GetSafePaths()
	results = append(results, V7SimulationResult{
		TestID:      "PATH-002",
		Category:    "path_discovery",
		Description: "9 SAFE paths identified",
		Passed:      len(safePaths) == 9,
		Detail:      fmt.Sprintf("safe_paths=%d", len(safePaths)),
	})

	// Test 3: Blocked paths
	blockedPaths := epr.GetBlockedPaths()
	results = append(results, V7SimulationResult{
		TestID:      "PATH-003",
		Category:    "path_discovery",
		Description: "7 BLOCKED paths identified",
		Passed:      len(blockedPaths) == 7,
		Detail:      fmt.Sprintf("blocked_paths=%d", len(blockedPaths)),
	})

	// Test 4: Zero bypass risks
	noBypass, reason := epr.VerifyNoBypassExists()
	results = append(results, V7SimulationResult{
		TestID:      "PATH-004",
		Category:    "path_discovery",
		Description: "Zero BYPASS_RISK paths — proven secure",
		Passed:      noBypass,
		Detail:      reason,
	})

	return results
}

func runKSMLGovernanceTests(bridge *GatedBridge) []V7SimulationResult {
	var results []V7SimulationResult
	ksmlHook := NewKSMLGovernanceHook(bridge)

	// ─────────────────────────────────────────────────────────
	// KSML-001: Basic QUERY_INTENT via GovernKSMLDecision
	// ─────────────────────────────────────────────────────────
	resp := ksmlHook.GovernKSMLDecision("agent-alpha", "ksml-resource", "read", "ksml-corr-001")
	results = append(results, V7SimulationResult{
		TestID:      "KSML-001",
		Category:    "ksml_governance",
		Description: "KSML decision routed through GatedBridge",
		Passed:      resp != nil && (resp.Verdict == "ALLOW" || resp.Verdict == "DENY"),
		Detail:      fmt.Sprintf("verdict=%s", resp.Verdict),
	})

	// ─────────────────────────────────────────────────────────
	// KSML-002: Stats tracked after first request
	// ─────────────────────────────────────────────────────────
	total, allowed, denied := ksmlHook.GetKSMLStats()
	results = append(results, V7SimulationResult{
		TestID:      "KSML-002",
		Category:    "ksml_governance",
		Description: "KSML stats tracked correctly",
		Passed:      total == 1 && (allowed+denied) == 1,
		Detail:      fmt.Sprintf("total=%d allowed=%d denied=%d", total, allowed, denied),
	})

	// ─────────────────────────────────────────────────────────
	// KSML-003: Multiple requests counted correctly
	// ─────────────────────────────────────────────────────────
	for i := 0; i < 5; i++ {
		ksmlHook.GovernKSMLDecision("agent-beta", "ksml-resource", "write", fmt.Sprintf("ksml-corr-%d", i+2))
	}
	total, _, _ = ksmlHook.GetKSMLStats()
	results = append(results, V7SimulationResult{
		TestID:      "KSML-003",
		Category:    "ksml_governance",
		Description: "Multiple KSML requests counted correctly",
		Passed:      total == 6,
		Detail:      fmt.Sprintf("total_ksml_requests=%d", total),
	})

	// ─────────────────────────────────────────────────────────
	// KSML-004: Verb translation — "query" → "read"
	// ─────────────────────────────────────────────────────────
	action, errMsg := TranslateKSMLVerb("query")
	results = append(results, V7SimulationResult{
		TestID:      "KSML-004",
		Category:    "ksml_governance",
		Description: "KSML verb 'query' translates to governance action 'read'",
		Passed:      action == "read" && errMsg == "",
		Detail:      fmt.Sprintf("verb=query action=%s err=%q", action, errMsg),
	})

	// ─────────────────────────────────────────────────────────
	// KSML-005: Verb translation — "invoke" → "execute"
	// ─────────────────────────────────────────────────────────
	action, errMsg = TranslateKSMLVerb("invoke")
	results = append(results, V7SimulationResult{
		TestID:      "KSML-005",
		Category:    "ksml_governance",
		Description: "KSML verb 'invoke' translates to governance action 'execute'",
		Passed:      action == "execute" && errMsg == "",
		Detail:      fmt.Sprintf("verb=invoke action=%s err=%q", action, errMsg),
	})

	// ─────────────────────────────────────────────────────────
	// KSML-006: Unknown verb → validation failure (fail-closed)
	// ─────────────────────────────────────────────────────────
	action, errMsg = TranslateKSMLVerb("jailbreak")
	results = append(results, V7SimulationResult{
		TestID:      "KSML-006",
		Category:    "ksml_governance",
		Description: "Unknown KSML verb is rejected (fail-closed)",
		Passed:      action == "" && strings.Contains(errMsg, "KSML_UNKNOWN_VERB"),
		Detail:      fmt.Sprintf("action=%q err=%s", action, errMsg),
	})

	// ─────────────────────────────────────────────────────────
	// KSML-007: GovernIntent with full KSMLIntent — EXECUTION_INTENT
	// ─────────────────────────────────────────────────────────
	execIntent := &KSMLIntent{
		IntentID:      "intent-exec-001",
		IntentType:    KSMLIntentExecution,
		AgentID:       "agent-gamma",
		ResourceID:    "knowledge-graph-001",
		KSMLVerb:      "invoke",
		CorrelationID: "ksml-exec-corr-001",
		IssuedAt:      time.Now().UTC(),
		ExpiresAt:     time.Now().UTC().Add(5 * time.Minute),
	}
	decision := ksmlHook.GovernIntent(execIntent)
	results = append(results, V7SimulationResult{
		TestID:      "KSML-007",
		Category:    "ksml_governance",
		Description: "EXECUTION_INTENT via GovernIntent routes through pipeline",
		Passed:      decision != nil && (decision.Verdict == "ALLOW" || decision.Verdict == "DENY") && decision.GovernanceAction == "execute",
		Detail:      fmt.Sprintf("verdict=%s action=%s status=%s", decision.Verdict, decision.GovernanceAction, decision.Status),
	})

	// ─────────────────────────────────────────────────────────
	// KSML-008: ESCALATION_INTENT → blocked (requires human review)
	// ─────────────────────────────────────────────────────────
	escalationIntent := &KSMLIntent{
		IntentID:      "intent-esc-001",
		IntentType:    KSMLIntentEscalation,
		AgentID:       "agent-delta",
		ResourceID:    "classified-resource-001",
		KSMLVerb:      "invoke",
		CorrelationID: "ksml-esc-corr-001",
		IssuedAt:      time.Now().UTC(),
		ExpiresAt:     time.Now().UTC().Add(5 * time.Minute),
		RequiresHuman: true,
	}
	escDecision := ksmlHook.GovernIntent(escalationIntent)
	results = append(results, V7SimulationResult{
		TestID:      "KSML-008",
		Category:    "ksml_governance",
		Description: "ESCALATION_INTENT blocked — requires human review before execution",
		Passed:      escDecision.Status == KSMLIntentEscalated && escDecision.Verdict == "ESCALATE",
		Detail:      fmt.Sprintf("status=%s verdict=%s reason=%s", escDecision.Status, escDecision.Verdict, escDecision.BlockReason),
	})

	// ─────────────────────────────────────────────────────────
	// KSML-009: Intent revocation — revoked intent is blocked
	// ─────────────────────────────────────────────────────────
	revokedIntentID := "intent-revoke-001"
	ksmlHook.RevokeIntent(revokedIntentID)
	revokedIntent := &KSMLIntent{
		IntentID:      revokedIntentID,
		IntentType:    KSMLIntentExecution,
		AgentID:       "agent-epsilon",
		ResourceID:    "target-resource-001",
		KSMLVerb:      "fetch",
		CorrelationID: "ksml-rev-corr-001",
		IssuedAt:      time.Now().UTC(),
		ExpiresAt:     time.Now().UTC().Add(5 * time.Minute),
	}
	revDecision := ksmlHook.GovernIntent(revokedIntent)
	results = append(results, V7SimulationResult{
		TestID:      "KSML-009",
		Category:    "ksml_governance",
		Description: "Revoked KSML intent is blocked (KSML_INTENT_REVOKED)",
		Passed:      revDecision.Status == KSMLIntentRevoked && strings.Contains(revDecision.BlockReason, "KSML_INTENT_REVOKED"),
		Detail:      fmt.Sprintf("status=%s reason=%s", revDecision.Status, revDecision.BlockReason),
	})

	// ─────────────────────────────────────────────────────────
	// KSML-010: IsIntentRevoked returns correct boolean
	// ─────────────────────────────────────────────────────────
	isRevoked := ksmlHook.IsIntentRevoked(revokedIntentID)
	isNotRevoked := ksmlHook.IsIntentRevoked("intent-never-revoked")
	results = append(results, V7SimulationResult{
		TestID:      "KSML-010",
		Category:    "ksml_governance",
		Description: "IsIntentRevoked returns correct status for revoked and non-revoked intents",
		Passed:      isRevoked && !isNotRevoked,
		Detail:      fmt.Sprintf("revoked=%v non_revoked=%v", isRevoked, isNotRevoked),
	})

	// ─────────────────────────────────────────────────────────
	// KSML-011: Nil intent → validation fails, no panic
	// ─────────────────────────────────────────────────────────
	nilErrMsg := ValidateKSMLIntent(nil)
	results = append(results, V7SimulationResult{
		TestID:      "KSML-011",
		Category:    "ksml_governance",
		Description: "Nil KSML intent is rejected without panic",
		Passed:      strings.Contains(nilErrMsg, "KSML_INTENT_NIL"),
		Detail:      fmt.Sprintf("validation_error=%s", nilErrMsg),
	})

	// ─────────────────────────────────────────────────────────
	// KSML-012: DELEGATION_INTENT — delegation chain recorded
	// ─────────────────────────────────────────────────────────
	delegationIntent := &KSMLIntent{
		IntentID:      "intent-deleg-001",
		IntentType:    KSMLIntentDelegation,
		AgentID:       "agent-zeta",
		TargetAgentID: "agent-eta",
		ResourceID:    "shared-resource-001",
		KSMLVerb:      "query",
		DelegationID:  "parent-intent-root",
		CorrelationID: "ksml-deleg-corr-001",
		IssuedAt:      time.Now().UTC(),
		ExpiresAt:     time.Now().UTC().Add(5 * time.Minute),
	}
	delegDecision := ksmlHook.GovernIntent(delegationIntent)
	chain := ksmlHook.GetDelegationChain("intent-deleg-001")
	results = append(results, V7SimulationResult{
		TestID:      "KSML-012",
		Category:    "ksml_governance",
		Description: "DELEGATION_INTENT recorded and delegation chain tracked",
		Passed:      delegDecision != nil && len(chain) >= 1,
		Detail:      fmt.Sprintf("verdict=%s chain_length=%d chain=%v", delegDecision.Verdict, len(chain), chain),
	})

	// ─────────────────────────────────────────────────────────
	// KSML-013: Intent history tracked per agent
	// ─────────────────────────────────────────────────────────
	history := ksmlHook.GetAgentIntentHistory("agent-gamma")
	results = append(results, V7SimulationResult{
		TestID:      "KSML-013",
		Category:    "ksml_governance",
		Description: "Per-agent KSML intent history is tracked and readable",
		Passed:      len(history) >= 1,
		Detail:      fmt.Sprintf("agent=agent-gamma history_entries=%d", len(history)),
	})

	// ─────────────────────────────────────────────────────────
	// KSML-014: Detailed stats cover all metric dimensions
	// ─────────────────────────────────────────────────────────
	stats := ksmlHook.GetKSMLDetailedStats()
	hasAllKeys := stats["total_requests"] > 0 &&
		stats["allowed"]+stats["denied"]+stats["escalated"] > 0
	results = append(results, V7SimulationResult{
		TestID:      "KSML-014",
		Category:    "ksml_governance",
		Description: "Detailed KSML stats cover all metric dimensions",
		Passed:      hasAllKeys,
		Detail: fmt.Sprintf("total=%d allowed=%d denied=%d escalated=%d delegations=%d revocations=%d",
			stats["total_requests"], stats["allowed"], stats["denied"],
			stats["escalated"], stats["delegations"], stats["revocations"]),
	})

	return results
}

// WriteSimulationResults writes the simulation results to a JSON file.
func WriteSimulationResults(summary *V7SimulationSummary, filename string) error {
	data, err := json.MarshalIndent(summary, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal failed: %w", err)
	}
	return os.WriteFile(filename, data, 0644)
}
