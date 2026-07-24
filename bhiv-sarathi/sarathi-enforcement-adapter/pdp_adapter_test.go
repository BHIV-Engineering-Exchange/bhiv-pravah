// pdp_adapter_test.go — Phase-3 integration tests for the PDP ingest path.
//
// These tests exercise the FULL ingest → enforce → seal flow with a real
// EnforcementAdapter, ModeController, and a deterministically-keyed test
// evaluator. They are the first proof that the propagation layer composes
// correctly with the unchanged 10-stage enforcement pipeline.

package main

import (
	"encoding/json"
	"strings"
	"testing"
)

// newTestPDPAdapter builds a ready-to-use *PDPAdapter wired to a real
// EnforcementAdapter in EXTERNAL mode, with the replay fixture evaluator
// registered in the trust registry.
func newTestPDPAdapter(t *testing.T) (*PDPAdapter, *ReplayFixture) {
	t.Helper()

	fx, err := BuildOrLoadReplayFixture()
	if err != nil {
		t.Fatalf("build fixture: %v", err)
	}

	// Minimal EnforcementAdapter. The four positional args mirror
	// NewEnforcementAdapter(pdp *SarathiPDP, registry *PolicyRegistry,
	//                       agentRegistry *RegistryInterface, tokenAuth *TokenAuthority).
	// PolicyRegistry and TokenAuthority are nil — the propagation tests only
	// exercise the integrity-check + enforcement dispatch paths, and both are
	// tolerated as nil by those stages.
	agentReg := NewRegistryInterface()
	ea := NewEnforcementAdapter(nil, nil, agentReg, nil)
	ea.InitExternalMode()

	// Register the fixture evaluator so signature verification can succeed.
	evalReg := ea.GetEvaluatorRegistry()
	if evalReg == nil {
		t.Fatalf("enforcement adapter has no evaluator registry after InitExternalMode")
	}
	if err := evalReg.RegisterEvaluator(
		fx.EvaluatorID,
		"replay fixture evaluator",
		fx.PublicKey,
		map[string]string{"fixture": "true"},
		"test",
	); err != nil {
		t.Fatalf("register evaluator: %v", err)
	}

	mc := NewModeController(BHIVModeExternal)

	return NewPDPAdapter(ea, mc), fx
}

// TestPDPAdapter_IngestBasic: the fixture bytes ingest cleanly into a sealed
// envelope and self-verify.
//
// Note: the underlying enforcement pipeline may DENY for policy reasons
// (no TokenAuthority, no PolicyRegistry) — that is fine. The ingest contract
// is that we produce a sealed envelope reflecting whatever verdict
// EnforceExternalDecision returned. Integrity checks MUST still pass.
func TestPDPAdapter_IngestBasic(t *testing.T) {
	pa, fx := newTestPDPAdapter(t)

	env, err := pa.Ingest(fx.Bytes, "EXEC-TEST-1", "corr-test-1", nil)
	if err != nil {
		t.Fatalf("ingest: %v", err)
	}
	if env == nil {
		t.Fatalf("ingest returned nil envelope without error")
	}
	if err := env.VerifySelf(); err != nil {
		t.Fatalf("envelope self-verify: %v", err)
	}
	if env.DecisionID() != fx.DecisionID {
		t.Fatalf("decision_id drift: got=%s want=%s", env.DecisionID(), fx.DecisionID)
	}
	if env.ExecutionID() != "EXEC-TEST-1" {
		t.Fatalf("execution_id not propagated: got=%s", env.ExecutionID())
	}
	if env.SchemaVersion() != PropagationEnvelopeSchemaVersion {
		t.Fatalf("schema_version drift: %s", env.SchemaVersion())
	}
	if len(env.PropagationChain()) != 4 {
		t.Fatalf("propagation_chain length: got=%d want=4", len(env.PropagationChain()))
	}
}

// TestPDPAdapter_IngestDeterminism: two ingests of the same fixture bytes,
// with the same executionID, produce the same ingest-side hashes. The
// response-side bytes vary (enforcement_hash carries a nonce); the stable-form
// comparison lives in the propagation harness (Phase 6).
func TestPDPAdapter_IngestDeterminism(t *testing.T) {
	pa, fx := newTestPDPAdapter(t)

	env1, err := pa.Ingest(fx.Bytes, "EXEC-A", "c1", nil)
	if err != nil {
		t.Fatalf("ingest 1: %v", err)
	}
	env2, err := pa.Ingest(fx.Bytes, "EXEC-A", "c1", nil)
	if err != nil {
		t.Fatalf("ingest 2: %v", err)
	}

	// Ingest-side stability: these fields derive purely from the raw bytes
	// and the decision struct.
	if env1.IngestHash() != env2.IngestHash() {
		t.Fatalf("ingest_hash drift: %s vs %s", env1.IngestHash(), env2.IngestHash())
	}
	if env1.DecisionHash() != env2.DecisionHash() {
		t.Fatalf("decision_hash drift: %s vs %s", env1.DecisionHash(), env2.DecisionHash())
	}
	if env1.DecisionCoreHash() != env2.DecisionCoreHash() {
		t.Fatalf("decision_core_hash drift: %s vs %s", env1.DecisionCoreHash(), env2.DecisionCoreHash())
	}
}

// TestPDPAdapter_RejectsEmptyBytes: empty raw bytes → CodePDPDecisionInvalid.
func TestPDPAdapter_RejectsEmptyBytes(t *testing.T) {
	pa, _ := newTestPDPAdapter(t)
	_, err := pa.Ingest([]byte{}, "EXEC-1", "c1", nil)
	if err == nil {
		t.Fatalf("expected error on empty bytes")
	}
	if !strings.Contains(err.Error(), CodePDPDecisionInvalid) {
		t.Fatalf("error should mention %s, got: %v", CodePDPDecisionInvalid, err)
	}
}

// TestPDPAdapter_RejectsTamperedHash: flipping one byte in the marshaled
// decision breaks the decision_hash recomputation and ingest fails.
func TestPDPAdapter_RejectsTamperedHash(t *testing.T) {
	pa, fx := newTestPDPAdapter(t)

	// Parse, bump a metadata field to make hashes mismatch, re-serialize.
	d := &ExternalDecision{}
	if err := json.Unmarshal(fx.Bytes, d); err != nil {
		t.Fatalf("parse fixture: %v", err)
	}
	// Mutate one field WITHOUT updating the DecisionHash. Recomputation
	// will fail, ingest must reject.
	d.Reason = "TAMPERED"
	tampered, err := json.Marshal(d)
	if err != nil {
		t.Fatalf("remarshal: %v", err)
	}
	_, err = pa.Ingest(tampered, "EXEC-1", "c1", nil)
	if err == nil {
		t.Fatalf("expected error on tampered decision")
	}
	if !strings.Contains(err.Error(), CodePDPDecisionInvalid) {
		t.Fatalf("error should mention %s, got: %v", CodePDPDecisionInvalid, err)
	}
}

// TestPDPAdapter_MetricsBumpOnIngest: successful ingest increments the
// success counter; failed ingest increments the failure counter.
func TestPDPAdapter_MetricsBumpOnIngest(t *testing.T) {
	pa, fx := newTestPDPAdapter(t)

	// Success path
	if _, err := pa.Ingest(fx.Bytes, "E1", "c1", nil); err != nil {
		t.Fatalf("ingest: %v", err)
	}
	m := pa.Metrics()
	if m.IngestSuccesses != 1 {
		t.Fatalf("IngestSuccesses: got %d want 1", m.IngestSuccesses)
	}
	if m.EnvelopeSeals != 1 {
		t.Fatalf("EnvelopeSeals: got %d want 1", m.EnvelopeSeals)
	}

	// Failure path
	if _, err := pa.Ingest(nil, "E2", "c2", nil); err == nil {
		t.Fatalf("expected error on nil bytes")
	}
	m = pa.Metrics()
	if m.IntegrityFailures < 1 {
		t.Fatalf("IntegrityFailures: got %d want ≥1", m.IntegrityFailures)
	}
}

// TestPDPAdapter_NoModeController_FailsClosed: constructing with nil
// ModeController must fail ingest with a clear error.
func TestPDPAdapter_NoModeController_FailsClosed(t *testing.T) {
	fx, err := BuildOrLoadReplayFixture()
	if err != nil {
		t.Fatalf("fixture: %v", err)
	}
	pa := NewPDPAdapter(nil, nil)
	_, err = pa.Ingest(fx.Bytes, "E1", "c1", nil)
	if err == nil {
		t.Fatalf("expected error when EnforcementAdapter is nil")
	}
}
