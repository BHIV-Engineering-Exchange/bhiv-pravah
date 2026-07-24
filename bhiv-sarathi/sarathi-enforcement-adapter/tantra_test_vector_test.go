package main

// tantra_test_vector_test.go — emits authoritative canonical-bytes + hash test
// vectors straight from Sarathi's real canonicalizer, so an upstream producer
// (Core) can compare byte-for-byte. Run with:
//
//	go test -run TestTantraInteropVectors -v .
//
// TAG: tantra-convergence-v1

import (
	"encoding/base64"
	"fmt"
	"testing"
)

func TestTantraInteropVectors(t *testing.T) {
	const (
		schemaVersion   = "tantra.decision.v1"
		traceID         = "550e8400-e29b-41d4-a716-446655440000"
		inputHash       = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
		verdict         = "ALLOW"
		policyReference = "bhiv.core.default_allow_policy@v1.0"
		evaluatorID     = "bhiv.sovereign.decision.prod.v1"
	)

	// --- decision_hash: 6-field material, fixed order ---
	mat := TantraDecisionMaterial{
		SchemaVersion:   schemaVersion,
		TraceID:         traceID,
		InputHash:       inputHash,
		Verdict:         TantraVerdictAllow,
		PolicyReference: policyReference,
		EvaluatorID:     evaluatorID,
	}
	matBytes := CanonicalDecisionMaterialBytes(mat)
	decisionHash := ComputeTantraDecisionHash(mat)
	t.Logf("decision_hash material bytes:\n%s", string(matBytes))
	t.Logf("decision_hash = %s", decisionHash)

	// --- decision_id: 3-field material, fixed order ---
	d := &TantraDecision{
		SchemaVersion:      schemaVersion,
		TraceID:            traceID,
		InputHash:          inputHash,
		DecisionHash:       decisionHash,
		Verdict:            TantraVerdictAllow,
		PolicyReference:    policyReference,
		EvaluatorID:        evaluatorID,
		EnforcementBinding: "CLEARED:core decision",
		Timestamp:          "2026-06-01T00:00:00Z",
		Signature: TantraSignature{
			Alg:      "Ed25519",
			KeyID:    "bhiv.sovereign.decision.prod.v1#ed25519-2026-05",
			Encoding: TantraSignatureEncoding,
		},
	}
	decisionID := ComputeTantraDecisionID(d)
	d.DecisionID = decisionID
	t.Logf("decision_id = %s", decisionID)

	// --- signing bytes: full 10-field canonical payload, signature OMITTED ---
	signable, err := CanonicalSignableBytes(d)
	if err != nil {
		t.Fatalf("signable: %v", err)
	}
	t.Logf("signing bytes (Ed25519 input, signature object OMITTED):\n%s", string(signable))
	t.Logf("signing bytes base64-std (for unambiguous transport):\n%s", base64.StdEncoding.EncodeToString(signable))

	// Assert the hand-computed reference vectors match the real canonicalizer.
	if got, want := decisionHash, "eb1a0d58f2a624ebde3a6adc21f9ffb2c19b8f654ccb94eea251a144d517ffbe"; got != want {
		t.Errorf("decision_hash drift: got %s want %s", got, want)
	}
	if got, want := decisionID, "f5816bed-aeee-7d9f-f397-0074cdbb0687"; got != want {
		t.Errorf("decision_id drift: got %s want %s", got, want)
	}
	fmt.Println("[interop] vectors emitted")
}

// TestLiveSnapshotLoadsCore confirms Core's registered evaluator loads from the
// live trust snapshot and passes the 5-gate lookup — i.e. Core's signed
// decisions will verify on /sarathi/enforce.
func TestLiveSnapshotLoadsCore(t *testing.T) {
	provider := NewEd25519Provider()
	SetActiveProviderForTest(provider)

	entries, err := LoadTantraTrustExtension("live/trust_snapshot.json")
	if err != nil {
		t.Fatalf("load snapshot: %v", err)
	}
	tc, n, err := NewTantraTrustConsumer(entries, provider)
	if err != nil || n < 1 {
		t.Fatalf("build registry (accepted=%d): %v", n, err)
	}
	res, lerr := tc.Lookup(
		"bhiv.sovereign.decision.prod.v1",
		"tantra.decision.v1",
		"bhiv.sovereign.decision.prod.v1#ed25519-2026-05",
		"Ed25519",
	)
	if lerr != nil {
		t.Fatalf("Core evaluator 5-gate lookup failed: %v", lerr)
	}
	if res.Entry.PublicKey != "ca087b33d011dadfef89c2df05301c420766f29ba369d12ff2c601ab637171dc" {
		t.Errorf("Core public_key mismatch: %s", res.Entry.PublicKey)
	}
	t.Logf("Core evaluator loaded + 5-gate lookup OK (pubkey %s…)", res.Entry.PublicKey[:16])
}
