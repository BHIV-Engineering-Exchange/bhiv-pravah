// live_audit_wiring.go (v15.2 — fixes the proof_logs/enforcement_audit_backup.jsonl
// generation bug that VC_CALL_VALIDATION_SCRIPT3 §3 surfaced).
//
// THE BUG (v15.1 and earlier):
//   live_integration_runner.go, parallel_execution_runner.go,
//   distributed_integration_runner.go, and failure_demo_runner.go all create
//   EnforcementAdapter via NewEnforcementAdapter(...) but never wire an
//   AuditSink. The FallbackAuditSink that produces enforcement_audit_backup.jsonl
//   is built only inside enforcement_adapter_main.go's --service boot path
//   (line ~2274). Result: every flag that uses --live-integration / parallel /
//   distributed / failure-demo runs without writing the JSONL backup, and §3
//   trace validation cannot proceed.
//
// THE FIX:
//   This file exposes WireFallbackAuditSink(ea) which:
//     1. constructs a FallbackAuditSink (creates proof_logs/ + opens 3 files)
//     2. calls ea.SetAuditSink(sink) — uses the existing setter
//     3. returns the sink so callers defer Close()
//
//   Plus RecordHarnessEnforcement(sink, env, ad, corrID) which translates an
//   ExternalDecision + PropagationEnvelope into the SaarthiRequest/Response
//   shape the FallbackAuditSink expects, preserving every trace-relevant
//   field VC_CALL_VALIDATION_SCRIPT3 §3 inspects (trace_id, decision_id,
//   verdict, response_hash, chain_binding_hash, enforcement_hash, error_code,
//   schema_version).
//
// DESIGN CHOICE:
//   The wiring is per-harness-call (not global) because:
//     - the --service boot already wires its own sink and we MUST NOT
//       double-init
//     - failures here are best-effort: a disk-full audit failure should not
//       break the deterministic propagation flow (which has its own
//       fail-closed audit gate via MandatoryAuditGate)
//     - the helper is invoked once per --live-integration invocation; the
//       runner defers Close()
//
// TAG: v15.2-audit-fix

package main

import (
	"fmt"
	"time"
)

// WireFallbackAuditSink constructs a FallbackAuditSink (in-memory + JSONL) and
// attaches it to the supplied EnforcementAdapter. Safe to call once per
// harness invocation; multiple calls overwrite the previous sink so callers
// must defer Close() on the returned sink.
//
// Returns the sink + error. On error the sink is nil and the adapter is
// left untouched.
func WireFallbackAuditSink(ea *EnforcementAdapter) (*FallbackAuditSink, error) {
	if ea == nil {
		return nil, fmt.Errorf("live_audit_wiring: nil EnforcementAdapter")
	}
	sink, err := NewFallbackAuditSink()
	if err != nil {
		return nil, fmt.Errorf("live_audit_wiring: NewFallbackAuditSink: %w", err)
	}
	ea.SetAuditSink(sink)
	// Record a system event so the events JSONL has a marker that lets the
	// reviewer identify which harness produced which records.
	_ = sink.RecordSystemEvent("harness_audit_sink_wired",
		fmt.Sprintf("ts=%s pid=process", time.Now().UTC().Format(time.RFC3339Nano)))
	return sink, nil
}

// RecordHarnessEnforcement translates a successful PDPAdapter.Ingest result
// into a SaarthiRequest/SaarthiResponse pair and persists it via sink. This
// is what produces the proof_logs/enforcement_audit_backup.jsonl entries
// VC_CALL_VALIDATION_SCRIPT3 §3 reads.
//
// Inputs:
//   - sink: from WireFallbackAuditSink (must be non-nil; no-op otherwise)
//   - env: sealed propagation envelope returned by PDPAdapter.Ingest
//   - decisionBytes: raw signed ExternalDecision bytes (used only for
//     decision_hash logging — the hash is already in the envelope)
//   - executionID, correlationID: harness-supplied identifiers
//   - errorCode: optional. Empty for ALLOW; the harness fills this in for
//     the failure-demo gates.
//
// Returns nil on success, or the error returned by sink.RecordEnforcement.
// All errors are best-effort: callers may discard the error since the
// deterministic propagation chain is the fail-closed gate, not this audit
// trail.
func RecordHarnessEnforcement(
	sink AuditSink,
	env *PropagationEnvelope,
	decisionBytes []byte,
	executionID string,
	correlationID string,
	errorCode string,
) error {
	if sink == nil || env == nil {
		return nil
	}

	// Reconstruct a SaarthiRequest from envelope-visible fields. Agent /
	// resource / action come from the envelope's verdict-bearing summary.
	summary := env.ToSummaryMap()
	agentID := stringFromSummary(summary, "agent_id")
	resourceID := stringFromSummary(summary, "resource_id")
	action := stringFromSummary(summary, "action")
	if agentID == "" {
		agentID = "external"
	}
	if resourceID == "" {
		resourceID = "external"
	}
	if action == "" {
		action = "external"
	}
	if correlationID == "" {
		correlationID = env.CorrelationID()
	}

	req := &SaarthiRequest{
		AgentID:       agentID,
		ResourceID:    resourceID,
		Action:        action,
		CorrelationID: correlationID,
		CallerSystem:  "harness",
		CallerVersion: "v15.2",
		RequestedAt:   time.Now().UTC(),
	}

	verdict := env.Verdict()
	if verdict == "" {
		verdict = "ALLOW"
	}
	executionState := "EXECUTION_PERMITTED"
	if verdict == "DENY" {
		executionState = "EXECUTION_BLOCKED"
	}

	resp := &SaarthiResponse{
		Verdict:          verdict,
		DecisionID:       env.DecisionID(),
		CorrelationID:    correlationID,
		Executed:         verdict == "ALLOW",
		ExecutionState:   executionState,
		EnforcementHash:  env.EnforcementHash(),
		EnforcedAt:       time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		ServiceVersion:   "v15.2",
		TraceID:          env.TraceID(),
		ErrorCode:        errorCode,
		SchemaVersion:    SchemaVersion,
		EnforcementToken: stringFromSummary(summary, "enforcement_token"),
		ExecutionID:      executionID,
		ResponseHash:     env.ResponseHash(),
		ChainBindingHash: env.ChainBindingHash(),
		PDPDecisionID:    env.DecisionID(),
	}

	_ = decisionBytes // currently unused — kept in the signature so harnesses
	// can pass it without rebuilding the call site if we ever add raw-body
	// hashing here.

	return sink.RecordEnforcement(req, resp)
}

// stringFromSummary safely reads a string value out of a summary map. Returns
// "" on missing keys or non-string values.
func stringFromSummary(m map[string]interface{}, key string) string {
	v, ok := m[key]
	if !ok {
		return ""
	}
	s, ok := v.(string)
	if !ok {
		return ""
	}
	return s
}
