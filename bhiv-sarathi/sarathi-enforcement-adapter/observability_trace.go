package main

// observability_trace.go — Live Observability Layer + Runtime Path Attestation.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Enforcement Adapter (PEP)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
// Version: v13.0 — System Dominance Transition
//
// PURPOSE:
//   Provides cross-system real-time observability for every enforcement
//   decision and execution. Every execution produces a standardized trace:
//     decision_id + enforcement_hash + token_id + execution_state
//
//   Also implements RuntimePathAttestation — proving that the actual runtime
//   invocation path matches the canonical pipeline order. This extends the
//   static pipeline hash lock (INV-35) to a runtime verification that
//   external systems MUST respect.
//
// GAP COVERAGE:
//   GAP 3: Live observability layer with cross-system correlation
//   GAP 5: Pipeline lock runtime verification across services
//
// INDUSTRY ALIGNMENT:
//   - W3C Trace Context: distributed tracing propagation headers
//   - OpenTelemetry: standardized observability signals (traces, metrics, logs)
//   - AWS X-Ray: cross-service trace correlation
//   - Google Cloud Trace: distributed trace collection
//   - Anthropic: governance event observability for AI execution

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
)

// ================================================================
// OBSERVABILITY EVENT — Standardized Trace Signal
// ================================================================

// ObservabilityEvent is the canonical observability signal emitted at every
// stage of the enforcement pipeline. Each event carries the full set of
// fields required for cross-system correlation and audit.
//
// Required fields for every execution (GAP 3):
//   - DecisionID:      unique PDP decision identifier
//   - EnforcementHash: enforcement chain entry hash
//   - TokenID:         capability token identifier
//   - ExecutionState:  EXECUTION_PERMITTED or EXECUTION_BLOCKED
type ObservabilityEvent struct {
	EventID         string    `json:"event_id"`
	Timestamp       time.Time `json:"timestamp"`
	DecisionID      string    `json:"decision_id"`
	EnforcementHash string    `json:"enforcement_hash"`
	TokenID         string    `json:"token_id"`
	ExecutionState  string    `json:"execution_state"`
	CorrelationID   string    `json:"correlation_id"`
	TraceID         string    `json:"trace_id"`
	SpanID          string    `json:"span_id"`
	SystemID        string    `json:"system_id"`
	Stage           string    `json:"stage"`
	Verdict         string    `json:"verdict"`
	BlockReason     string    `json:"block_reason,omitempty"`
	RequestHash     string    `json:"request_hash,omitempty"`
	PolicyHash      string    `json:"policy_hash,omitempty"`
	PipelinePathHash string   `json:"pipeline_path_hash,omitempty"`
	DurationNs      int64     `json:"duration_ns"`
}

// NewObservabilityEvent creates a new event with auto-generated ID and timestamp.
func NewObservabilityEvent(stage, systemID, correlationID, traceID string) *ObservabilityEvent {
	return &ObservabilityEvent{
		EventID:       fmt.Sprintf("OBS-%s", uuid.New().String()[:12]),
		Timestamp:     time.Now().UTC(),
		Stage:         stage,
		SystemID:      systemID,
		CorrelationID: correlationID,
		TraceID:       traceID,
		SpanID:        uuid.New().String()[:8],
	}
}

// ================================================================
// OBSERVABILITY COLLECTOR — Thread-Safe Event Aggregator
// ================================================================

// ObservabilityCollector aggregates observability events across the pipeline.
// Thread-safe for concurrent pipeline executions.
type ObservabilityCollector struct {
	mu     sync.Mutex
	events []ObservabilityEvent
}

// NewObservabilityCollector creates a new collector.
func NewObservabilityCollector() *ObservabilityCollector {
	return &ObservabilityCollector{
		events: make([]ObservabilityEvent, 0, 1024),
	}
}

// Emit records an observability event.
func (oc *ObservabilityCollector) Emit(event ObservabilityEvent) {
	oc.mu.Lock()
	defer oc.mu.Unlock()
	if event.EventID == "" {
		event.EventID = fmt.Sprintf("OBS-%s", uuid.New().String()[:12])
	}
	if event.Timestamp.IsZero() {
		event.Timestamp = time.Now().UTC()
	}
	oc.events = append(oc.events, event)
}

// GetTrace returns all events for a given correlation ID, ordered by timestamp.
func (oc *ObservabilityCollector) GetTrace(correlationID string) *EndToEndTrace {
	oc.mu.Lock()
	defer oc.mu.Unlock()

	trace := &EndToEndTrace{
		CorrelationID:          correlationID,
		Events:                 make([]ObservabilityEvent, 0),
		CrossSystemCorrelation: make(map[string]string),
	}

	for _, e := range oc.events {
		if e.CorrelationID == correlationID {
			trace.Events = append(trace.Events, e)
			if e.SystemID != "" {
				trace.CrossSystemCorrelation[e.SystemID] = e.EventID
			}
		}
	}

	// Compute pipeline path hash from events
	if len(trace.Events) > 0 {
		stages := make([]string, 0, len(trace.Events))
		for _, e := range trace.Events {
			stages = append(stages, e.Stage)
		}
		trace.PipelinePathHash = computeStagesHash(stages)
	}

	return trace
}

// GetAllEvents returns a copy of all events.
func (oc *ObservabilityCollector) GetAllEvents() []ObservabilityEvent {
	oc.mu.Lock()
	defer oc.mu.Unlock()
	cp := make([]ObservabilityEvent, len(oc.events))
	copy(cp, oc.events)
	return cp
}

// VerifyTraceCompleteness checks that a trace has all required fields for every execution.
// Returns (complete, missingFields).
func (oc *ObservabilityCollector) VerifyTraceCompleteness(correlationID string) (bool, []string) {
	trace := oc.GetTrace(correlationID)
	if len(trace.Events) == 0 {
		return false, []string{"no events found for correlation_id"}
	}

	var missing []string

	// Find the terminal event (execution result)
	var terminalEvent *ObservabilityEvent
	for i := range trace.Events {
		if trace.Events[i].Stage == "EXECUTION" || trace.Events[i].Stage == "EXECUTION_RESULT" {
			terminalEvent = &trace.Events[i]
			break
		}
	}

	if terminalEvent == nil {
		// Check if there's a pre-gate rejection or enforcement denial
		for i := range trace.Events {
			if trace.Events[i].ExecutionState != "" {
				terminalEvent = &trace.Events[i]
				break
			}
		}
	}

	if terminalEvent == nil {
		missing = append(missing, "no terminal event (execution or denial)")
		return false, missing
	}

	// GAP 3 mandatory fields: decision_id, enforcement_hash, token_id, execution_state
	if terminalEvent.ExecutionState == "" {
		missing = append(missing, "execution_state")
	}

	// For ALLOW verdicts, all four fields must be present
	if terminalEvent.Verdict == "ALLOW" || terminalEvent.ExecutionState == "EXECUTION_PERMITTED" {
		if terminalEvent.DecisionID == "" {
			missing = append(missing, "decision_id")
		}
		if terminalEvent.EnforcementHash == "" {
			missing = append(missing, "enforcement_hash")
		}
		if terminalEvent.TokenID == "" {
			missing = append(missing, "token_id")
		}
	}

	return len(missing) == 0, missing
}

// EventCount returns the total number of events collected.
func (oc *ObservabilityCollector) EventCount() int {
	oc.mu.Lock()
	defer oc.mu.Unlock()
	return len(oc.events)
}

// ExportJSON exports all events as indented JSON.
func (oc *ObservabilityCollector) ExportJSON() ([]byte, error) {
	oc.mu.Lock()
	defer oc.mu.Unlock()
	return json.MarshalIndent(oc.events, "", "  ")
}

// ================================================================
// END-TO-END TRACE — Complete Pipeline Trace
// ================================================================

// EndToEndTrace represents the complete trace of a single request through
// the entire enforcement pipeline: Decision → Bridge → Sarathi → Token → Execution → Audit.
type EndToEndTrace struct {
	CorrelationID          string                       `json:"correlation_id"`
	Events                 []ObservabilityEvent         `json:"events"`
	PipelinePathHash       string                       `json:"pipeline_path_hash"`
	CrossSystemCorrelation map[string]string            `json:"cross_system_correlation"`
}

// IsComplete returns true if the trace contains events from all required stages.
func (t *EndToEndTrace) IsComplete() bool {
	if len(t.Events) == 0 {
		return false
	}

	requiredStages := map[string]bool{
		"ENFORCEMENT": false,
		"EXECUTION_RESULT": false,
	}

	for _, e := range t.Events {
		if _, ok := requiredStages[e.Stage]; ok {
			requiredStages[e.Stage] = true
		}
	}

	for _, found := range requiredStages {
		if !found {
			return false
		}
	}
	return true
}

// ToJSON returns the trace as indented JSON.
func (t *EndToEndTrace) ToJSON() ([]byte, error) {
	return json.MarshalIndent(t, "", "  ")
}

// ================================================================
// RUNTIME PATH ATTESTATION (GAP 5)
// ================================================================

// RuntimePathAttestation records and verifies the actual runtime invocation
// path through the enforcement pipeline. This extends INV-35 (static pipeline
// hash lock) to runtime verification: the actual stages traversed MUST match
// the canonical pipeline order.
//
// Why this matters (GAP 5):
//   - Pipeline hash (INV-35) protects ORDER at compile/init time
//   - But does NOT verify that every stage was actually INVOKED at runtime
//   - An attacker who modifies runtime flow (skip a stage, reorder) would
//     not be caught by the static hash alone
//   - RuntimePathAttestation proves the actual invocation path matches canonical order
type RuntimePathAttestation struct {
	mu          sync.Mutex
	stages      []string
	timestamps  []time.Time
	startTime   time.Time
}

// NewRuntimePathAttestation creates a new attestation for a single pipeline execution.
func NewRuntimePathAttestation() *RuntimePathAttestation {
	return &RuntimePathAttestation{
		stages:    make([]string, 0, 10),
		timestamps: make([]time.Time, 0, 10),
		startTime: time.Now().UTC(),
	}
}

// RecordStage records that a pipeline stage was invoked at the current time.
func (rpa *RuntimePathAttestation) RecordStage(stage string) {
	rpa.mu.Lock()
	defer rpa.mu.Unlock()
	rpa.stages = append(rpa.stages, stage)
	rpa.timestamps = append(rpa.timestamps, time.Now().UTC())
}

// ComputePathHash returns the SHA-256 hash of the actual stages traversed,
// joined with "|" (same format as the static pipeline hash computation).
func (rpa *RuntimePathAttestation) ComputePathHash() string {
	rpa.mu.Lock()
	defer rpa.mu.Unlock()
	return computeStagesHash(rpa.stages)
}

// GetStages returns a copy of the recorded stages.
func (rpa *RuntimePathAttestation) GetStages() []string {
	rpa.mu.Lock()
	defer rpa.mu.Unlock()
	cp := make([]string, len(rpa.stages))
	copy(cp, rpa.stages)
	return cp
}

// VerifyAgainstCanonical checks that the recorded stages match the canonical
// pipeline order. Returns (match, detail).
//
// The verification checks:
//  1. All canonical stages are present (no skipped stages)
//  2. The order matches (no reordering)
//  3. No extra stages were injected
//
// Note: Pre-gate stages (RATE_LIMIT, POSTURE) may not appear if the request
// was not rejected at that stage. The verification only checks stages that
// were actually recorded against the canonical order.
func (rpa *RuntimePathAttestation) VerifyAgainstCanonical(canonical []string) (bool, string) {
	rpa.mu.Lock()
	defer rpa.mu.Unlock()

	if len(rpa.stages) == 0 {
		return false, "no stages recorded"
	}

	// Build a position map of canonical stages
	canonicalPos := make(map[string]int, len(canonical))
	for i, s := range canonical {
		canonicalPos[s] = i
	}

	// Verify recorded stages appear in canonical order
	lastPos := -1
	for _, stage := range rpa.stages {
		pos, exists := canonicalPos[stage]
		if !exists {
			return false, fmt.Sprintf("stage %q not in canonical pipeline", stage)
		}
		if pos < lastPos {
			return false, fmt.Sprintf("stage %q out of order (position %d < previous %d)", stage, pos, lastPos)
		}
		lastPos = pos
	}

	return true, "runtime path matches canonical order"
}

// VerifyComplete checks that the recorded stages EXACTLY match the canonical
// pipeline order — ALL stages present, in correct order, no extras.
//
// v14.1 ANTI-FOOLING (FOOLING-5 Fix):
//   VerifyAgainstCanonical allows partial paths (e.g., early exit on DENY).
//   VerifyComplete is stricter — it requires EVERY canonical stage to be
//   present. This is the method used by Execute() for ALLOW verdicts.
//
//   A request that receives an ALLOW verdict MUST have traversed every
//   verification stage. If any stage is missing, the enforcement was
//   incomplete and the ALLOW verdict must be overridden to DENY.
//
// Industry alignment:
//   - NIST 800-207: "All communication must be authenticated and authorized"
//   - Google Zanzibar: Zookie ensures complete freshness, not partial
//   - AWS IAM: CheckNoNewAccess uses formal reasoning for completeness
func (rpa *RuntimePathAttestation) VerifyComplete(canonical []string) (bool, string) {
	rpa.mu.Lock()
	defer rpa.mu.Unlock()

	if len(rpa.stages) == 0 {
		return false, "INCOMPLETE: no stages recorded"
	}

	if len(rpa.stages) != len(canonical) {
		return false, fmt.Sprintf("INCOMPLETE: expected %d stages, recorded %d stages", len(canonical), len(rpa.stages))
	}

	// Check exact match — every stage must be present at the correct position
	for i, expected := range canonical {
		if rpa.stages[i] != expected {
			return false, fmt.Sprintf("MISMATCH: stage[%d] expected=%q actual=%q", i, expected, rpa.stages[i])
		}
	}

	return true, "runtime path is complete and matches canonical order"
}

// DurationNs returns the total attestation duration in nanoseconds.
func (rpa *RuntimePathAttestation) DurationNs() int64 {
	rpa.mu.Lock()
	defer rpa.mu.Unlock()
	if len(rpa.timestamps) == 0 {
		return 0
	}
	return rpa.timestamps[len(rpa.timestamps)-1].Sub(rpa.startTime).Nanoseconds()
}

// ================================================================
// HELPERS
// ================================================================

// computeStagesHash computes SHA-256 of stages joined with "|".
// Same format as the static pipeline hash for comparability.
func computeStagesHash(stages []string) string {
	joined := ""
	for i, s := range stages {
		if i > 0 {
			joined += "|"
		}
		joined += s
	}
	hash := sha256.Sum256([]byte(joined))
	return hex.EncodeToString(hash[:])
}

// ================================================================
// END-TO-END TRACE SAMPLE GENERATOR
// ================================================================

// GenerateE2ETraceSample creates a sample end-to-end trace from a pipeline
// execution result. This is used for deliverable generation.
func GenerateE2ETraceSample(trace map[string]interface{}, collector *ObservabilityCollector) map[string]interface{} {
	sample := make(map[string]interface{})

	// Extract core fields
	if req, ok := trace["request"]; ok {
		sample["request"] = req
	}

	// Extract enforcement fields
	if enf, ok := trace["enforcement"]; ok {
		enfMap := enf.(map[string]interface{})
		sample["enforcement"] = map[string]interface{}{
			"decision_id":      enfMap["decision_id"],
			"enforcement_hash": enfMap["enforcement_hash"],
			"verdict":          enfMap["verdict"],
			"enforcement_stage": enfMap["enforcement_stage"],
			"policy_hash":      enfMap["policy_hash"],
		}
	}

	// Extract execution fields
	if exec, ok := trace["execution"]; ok {
		execMap := exec.(map[string]interface{})
		sample["execution"] = map[string]interface{}{
			"token_id":         execMap["token_id"],
			"execution_state":  execMap["execution_state"],
			"execution_hash":   execMap["execution_hash"],
			"execution_sequence": execMap["execution_sequence"],
			"block_reason":     execMap["block_reason"],
		}
	}

	// Extract trace ID
	if traceID, ok := trace["trace_id"]; ok {
		sample["trace_id"] = traceID
	}

	// Extract observability data
	if obs, ok := trace["observability"]; ok {
		sample["observability"] = obs
	}

	return sample
}
