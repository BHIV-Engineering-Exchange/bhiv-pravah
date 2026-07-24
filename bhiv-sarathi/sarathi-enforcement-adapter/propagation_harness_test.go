// propagation_harness_test.go — end-to-end byte-equality proof.
//
// This is THE proof the plan calls for: SAME PDP input → SAME byte-identical
// output across iterations. The test runs 15 replay rounds through a real
// PDPAdapter + a real EnforcementAdapter with in-memory OK handlers standing
// in for Core/InsightFlow/Bucket/Intent Layer. It asserts:
//
//   - exactly one unique response_hash_stable across iterations
//   - exactly one unique chain_binding_hash_stable across iterations
//   - zero determinism violations
//   - proof_logs/propagation_replay_results.jsonl contains 15 rows
//   - propagation_byte_equality_report.json wraps the report via WriteCanonicalResults

package main

import (
	"encoding/json"
	"os"
	"strings"
	"testing"
)

// TestPropagationReplay_15Iterations: the hard proof. This must pass for
// v14.5 to be production-ready.
func TestPropagationReplay_15Iterations(t *testing.T) {
	pa, fx := newTestPDPAdapter(t)

	router := NewMultiSystemRouter(nil)
	// In-process handlers: always deliver successfully, always echo the
	// envelope's response_hash as the ACK. This is the "ideal" wire behaviour
	// we expect from a byte-compliant peer.
	for _, name := range []string{"core_workflow", "insightflow", "bucket"} {
		router.InstallPropagationHandler(name, func(event *RoutedEvent) error { return nil }, true, false)
	}
	router.InstallPropagationHandler("intent_layer",
		func(event *RoutedEvent) error { return nil }, false, true)

	// Use scratch paths so the test does not collide with production artefacts.
	logPath := t.TempDir() + "/propagation_replay_results.jsonl"
	reportPath := t.TempDir() + "/propagation_byte_equality_report.json"

	cfg := PropagationReplayConfig{
		Iterations:      15,
		StopOnFirstFail: false,
		LogFile:         logPath,
		ReportFile:      reportPath,
		Quiet:           true,
	}

	passed, failed, report, err := RunPropagationReplay(pa, router, fx.Bytes, cfg)
	if err != nil {
		t.Fatalf("RunPropagationReplay: %v", err)
	}
	if passed != 15 {
		t.Fatalf("expected 15/15 passed, got passed=%d failed=%d", passed, failed)
	}
	if report.DeterminismViolations != 0 {
		t.Fatalf("determinism_violations=%d, want 0", report.DeterminismViolations)
	}
	if len(report.UniqueResponseHashes) != 1 {
		t.Fatalf("unique response_hash_stable count=%d (want 1): %v",
			len(report.UniqueResponseHashes), report.UniqueResponseHashes)
	}
	if len(report.UniqueChainBindings) != 1 {
		t.Fatalf("unique chain_binding_stable count=%d (want 1): %v",
			len(report.UniqueChainBindings), report.UniqueChainBindings)
	}
	if !report.AllByteIdentical {
		t.Fatalf("AllByteIdentical=false — propagation chain is NOT byte-identical")
	}

	// JSONL log must have 15 rows.
	data, err := os.ReadFile(logPath)
	if err != nil {
		t.Fatalf("read log: %v", err)
	}
	lines := 0
	for _, b := range data {
		if b == '\n' {
			lines++
		}
	}
	if lines != 15 {
		t.Fatalf("expected 15 jsonl rows, got %d", lines)
	}

	// Summary report must parse as the canonical envelope.
	rdata, err := os.ReadFile(reportPath)
	if err != nil {
		t.Fatalf("read report: %v", err)
	}
	var envelope CanonicalResultEnvelope
	if err := json.Unmarshal(rdata, &envelope); err != nil {
		t.Fatalf("report envelope parse: %v", err)
	}
	if envelope.TestCategory != "propagation_byte_equality" {
		t.Fatalf("envelope test_category drift: %s", envelope.TestCategory)
	}
	if envelope.Passed != 15 {
		t.Fatalf("envelope passed drift: %d", envelope.Passed)
	}
}

// TestPropagationReplay_DetectsDeterminismDrift: inject a handler that
// mutates its assumptions across iterations. The harness must catch it
// (either via determinism_violations>0 or UniqueResponseHashes>1 — in this
// test we force an ACK mismatch on a specific iteration). This proves the
// oracle is not trivially "always passes".
func TestPropagationReplay_DetectsDeterminismDrift(t *testing.T) {
	pa, fx := newTestPDPAdapter(t)

	router := NewMultiSystemRouter(nil)
	// core returns success for first call, then PropagationStopError — the
	// harness must count the break as a determinism violation.
	call := 0
	router.InstallPropagationHandler("core_workflow", func(event *RoutedEvent) error {
		call++
		if call >= 3 {
			return &PropagationStopError{
				Code:    CodeResponseHashMismatch,
				Hop:     HopCore,
				TraceID: "t",
				Detail:  "simulated drift",
			}
		}
		return nil
	}, true, false)
	router.InstallPropagationHandler("insightflow", func(event *RoutedEvent) error { return nil }, true, false)
	router.InstallPropagationHandler("bucket", func(event *RoutedEvent) error { return nil }, true, false)
	router.InstallPropagationHandler("intent_layer", func(event *RoutedEvent) error { return nil }, false, true)

	cfg := PropagationReplayConfig{
		Iterations:      5,
		StopOnFirstFail: false,
		LogFile:         t.TempDir() + "/drift.jsonl",
		ReportFile:      t.TempDir() + "/drift.json",
		Quiet:           true,
	}

	_, failed, report, err := RunPropagationReplay(pa, router, fx.Bytes, cfg)
	if err != nil {
		t.Fatalf("RunPropagationReplay: %v", err)
	}
	if failed == 0 {
		t.Fatalf("expected at least one failure (drift injected on iter 3+)")
	}
	if report.DeterminismViolations == 0 {
		t.Fatalf("expected determinism_violations > 0")
	}
	if report.AllByteIdentical {
		t.Fatalf("AllByteIdentical must be false when drift is present")
	}
	if report.ChainHalts == 0 {
		t.Fatalf("expected at least one chain halt")
	}
}

// TestProduceStableEnvelope_NonEmpty: ProduceStableEnvelope returns non-empty
// bytes for a real sealed envelope and the result is byte-stable across calls.
func TestProduceStableEnvelope_NonEmpty(t *testing.T) {
	env, _ := mkEnvForValidator(t)
	a := ProduceStableEnvelope(env)
	b := ProduceStableEnvelope(env)
	if len(a) == 0 {
		t.Fatalf("empty stable envelope")
	}
	if string(a) != string(b) {
		t.Fatalf("stable envelope not byte-stable across calls")
	}
	// Should not contain the varying fields with non-empty values. Spot-check:
	s := string(a)
	if strings.Contains(s, "EXEC-V1") {
		t.Fatalf("stable envelope leaked execution_id: %s", s)
	}
}
