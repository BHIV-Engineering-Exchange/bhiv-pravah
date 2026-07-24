package main

// tantra_verifier_test.go — End-to-end TANTRA round-trip + mutation tests.
//
// Exercises the 12-step verifier under both providers (Ed25519, hybrid).
// Each test runs:
//
//   1. Build a fresh TANTRA decision in-memory.
//   2. Sign with a freshly-minted keypair, populate the signature object.
//   3. Marshal the wire bytes.
//   4. Register the corresponding TANTRA evaluator in an in-memory registry.
//   5. Run the verifier — assert accept or reject as expected.
//
// No HTTP, no disk except for the replay-store in-memory variant. Designed
// to run under `go test` quickly.
//
// TAG: tantra-v15.7

import (
	"encoding/base64"
	"strings"
	"testing"
	"time"
)

// mintTantraDecisionForTest builds a fully-signed TANTRA decision under the
// supplied provider + key material, with the registry populated to match.
//
// Returns the wire bytes the verifier will see + the registry it should use.
func mintTantraDecisionForTest(t *testing.T, provider CryptoProvider) ([]byte, *TantraTrustConsumer, *TantraDecision) {
	t.Helper()

	priv, pub, err := provider.Generate(nil)
	if err != nil {
		t.Fatalf("generate key: %v", err)
	}

	const evID = "bhiv.sovereign.decision.prod.v1"
	keyID := evID + "#" + algKeyIDSuffix(provider.Algorithm()) + "-test-2026-05"

	material := TantraDecisionMaterial{
		SchemaVersion:   TantraSchemaV1,
		TraceID:         "11111111-2222-3333-4444-555555555555",
		InputHash:       "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
		Verdict:         TantraVerdictAllow,
		PolicyReference: "bhiv.core.default_allow_policy@v1.0",
		EvaluatorID:     evID,
	}
	d := &TantraDecision{
		SchemaVersion:      TantraSchemaV1,
		TraceID:            material.TraceID,
		InputHash:          material.InputHash,
		DecisionHash:       ComputeTantraDecisionHash(material),
		Verdict:            material.Verdict,
		PolicyReference:    material.PolicyReference,
		EvaluatorID:        material.EvaluatorID,
		EnforcementBinding: "CLEARED:test enforcement record",
		Timestamp:          time.Now().UTC().Format(time.RFC3339Nano),
		Signature: TantraSignature{
			Alg:      string(provider.Algorithm()),
			KeyID:    keyID,
			Encoding: TantraSignatureEncoding,
		},
	}
	d.DecisionID = ComputeTantraDecisionID(d)

	signable, err := CanonicalSignableBytes(d)
	if err != nil {
		t.Fatalf("canonical signable: %v", err)
	}
	sig, err := provider.Sign(signable, priv)
	if err != nil {
		t.Fatalf("sign: %v", err)
	}
	d.Signature.Value = base64.RawURLEncoding.EncodeToString(sig)

	wire, err := CanonicalWireBytes(d)
	if err != nil {
		t.Fatalf("canonical wire: %v", err)
	}

	// Registry containing exactly this evaluator.
	entries := []TantraEvaluatorEntry{{
		EvaluatorID:   evID,
		Name:          "Test Sovereign",
		Status:        "ACTIVE",
		SchemaVersion: TantraSchemaV1,
		Algorithm:     string(provider.Algorithm()),
		KeyID:         keyID,
		PublicKey:     provider.EncodePublicKey(pub),
		RegisteredAt:  time.Now().UTC().Format(time.RFC3339Nano),
	}}
	tc, accepted, err := NewTantraTrustConsumer(entries, provider)
	if err != nil {
		t.Fatalf("registry: %v", err)
	}
	if accepted != 1 {
		t.Fatalf("registry accepted %d, want 1", accepted)
	}
	return wire, tc, d
}

func newVerifierForTest(provider CryptoProvider, tc *TantraTrustConsumer) *TantraVerifier {
	return &TantraVerifier{
		Provider:    provider,
		Registry:    tc,
		ReplayStore: NewMemoryTantraReplayStore(),
		Now:         func() time.Time { return time.Now().UTC() },
	}
}

func TestTantraVerifier_HappyPath_Ed25519(t *testing.T) {
	provider := NewEd25519Provider()
	SetActiveProviderForTest(provider)
	wire, tc, d := mintTantraDecisionForTest(t, provider)
	v := newVerifierForTest(provider, tc)
	result, err := v.Verify(wire)
	if err != nil {
		t.Fatalf("Verify: %v", err)
	}
	if result.Decision.DecisionID != d.DecisionID {
		t.Errorf("decision_id round-trip mismatch: got %s, want %s",
			result.Decision.DecisionID, d.DecisionID)
	}
}

func TestTantraVerifier_HappyPath_Hybrid(t *testing.T) {
	provider := NewHybridProvider()
	SetActiveProviderForTest(provider)
	wire, tc, d := mintTantraDecisionForTest(t, provider)
	v := newVerifierForTest(provider, tc)
	result, err := v.Verify(wire)
	if err != nil {
		t.Fatalf("Verify: %v", err)
	}
	if result.Decision.DecisionID != d.DecisionID {
		t.Errorf("decision_id round-trip mismatch: got %s, want %s",
			result.Decision.DecisionID, d.DecisionID)
	}
	if len(result.SignedBytes) == 0 {
		t.Errorf("SignedBytes empty")
	}
}

func TestTantraVerifier_ReplayRejected(t *testing.T) {
	provider := NewEd25519Provider()
	SetActiveProviderForTest(provider)
	wire, tc, _ := mintTantraDecisionForTest(t, provider)
	v := newVerifierForTest(provider, tc)
	if _, err := v.Verify(wire); err != nil {
		t.Fatalf("first verify: %v", err)
	}
	_, err := v.Verify(wire)
	if err == nil {
		t.Fatal("second verify should have failed (replay)")
	}
	tve, ok := err.(*TantraValidationError)
	if !ok || tve.Code != ErrTantraReplay {
		t.Fatalf("expected ErrTantraReplay, got %v", err)
	}
}

func TestTantraVerifier_MutatedField_RejectsSignature(t *testing.T) {
	provider := NewEd25519Provider()
	SetActiveProviderForTest(provider)
	wire, tc, _ := mintTantraDecisionForTest(t, provider)
	// Flip one byte of the wire (enforcement_binding string). The signature
	// MUST fail because the signed bytes change.
	mutated := make([]byte, len(wire))
	copy(mutated, wire)
	// Find the enforcement_binding value and flip the first letter (C -> D).
	idx := strings.Index(string(mutated), `"enforcement_binding":"CLEARED`)
	if idx < 0 {
		t.Fatalf("could not find enforcement_binding in wire: %s", string(mutated))
	}
	mutated[idx+len(`"enforcement_binding":"`)] = 'D'
	v := newVerifierForTest(provider, tc)
	_, err := v.Verify(mutated)
	if err == nil {
		t.Fatal("verify should have failed (mutated payload)")
	}
}

func TestTantraVerifier_BadSchemaVersion(t *testing.T) {
	provider := NewEd25519Provider()
	SetActiveProviderForTest(provider)
	wire, tc, _ := mintTantraDecisionForTest(t, provider)
	bad := strings.Replace(string(wire), "tantra.decision.v1", "tantra.decision.v2", 1)
	v := newVerifierForTest(provider, tc)
	_, err := v.Verify([]byte(bad))
	if err == nil {
		t.Fatal("verify should have failed (bad schema)")
	}
	tve, ok := err.(*TantraValidationError)
	if !ok || tve.Code != ErrTantraSchemaVersionUnknown {
		t.Fatalf("expected ErrTantraSchemaVersionUnknown, got %v", err)
	}
}

func TestTantraVerifier_KeyIDMismatch(t *testing.T) {
	provider := NewEd25519Provider()
	SetActiveProviderForTest(provider)
	wire, tc, _ := mintTantraDecisionForTest(t, provider)
	bad := strings.Replace(string(wire),
		`-test-2026-05"`, `-test-2099-12"`, 1)
	v := newVerifierForTest(provider, tc)
	_, err := v.Verify([]byte(bad))
	if err == nil {
		t.Fatal("verify should have failed (key_id mismatch)")
	}
}

func TestTantraVerifier_TimestampSkewed(t *testing.T) {
	provider := NewEd25519Provider()
	SetActiveProviderForTest(provider)
	wire, tc, _ := mintTantraDecisionForTest(t, provider)
	v := newVerifierForTest(provider, tc)
	// Advance "now" by 1 hour. The decision's timestamp is "now" at mint
	// time, so checking it against now+1h must fail with skew.
	v.Now = func() time.Time { return time.Now().UTC().Add(1 * time.Hour) }
	_, err := v.Verify(wire)
	if err == nil {
		t.Fatal("verify should have failed (skewed)")
	}
	tve, ok := err.(*TantraValidationError)
	if !ok || tve.Code != ErrTantraTimestampSkewed {
		t.Fatalf("expected ErrTantraTimestampSkewed, got %v", err)
	}
}

func TestTantraVerifier_UnknownField(t *testing.T) {
	provider := NewEd25519Provider()
	SetActiveProviderForTest(provider)
	wire, tc, _ := mintTantraDecisionForTest(t, provider)
	// Inject an extra field before the closing brace.
	bad := strings.Replace(string(wire),
		`,"signature":`,
		`,"extra_field":"x","signature":`, 1)
	v := newVerifierForTest(provider, tc)
	_, err := v.Verify([]byte(bad))
	if err == nil {
		t.Fatal("verify should have failed (unknown field)")
	}
	tve, ok := err.(*TantraValidationError)
	if !ok || tve.Code != ErrTantraUnknownField {
		t.Fatalf("expected ErrTantraUnknownField, got %v", err)
	}
}

func TestTantraEvaluatorID_Format(t *testing.T) {
	good := []string{
		"bhiv.sovereign.decision.prod.v1",
		"bhiv.sarathi.enforcement.prod.v1",
		"bhiv.core.local.dev.v1",
		"bhiv.x.y.z.v999",
	}
	for _, s := range good {
		if _, err := ParseTantraEvaluatorID(s); err != nil {
			t.Errorf("good id %q rejected: %v", s, err)
		}
	}
	bad := []string{
		"",
		"sovereign_bhiv_core",
		"bhiv.sovereign.decision.prod",         // missing version
		"BHIV.sovereign.decision.prod.v1",      // uppercase prefix
		"bhiv..decision.prod.v1",               // empty segment
		"bhiv.sovereign.decision.prod.v0",      // v0 forbidden
		"bhiv.sovereign.decision.prod.v1.foo",  // trailing segment
		"bhiv.sovereign-decision.prod.v1",      // missing component
	}
	for _, s := range bad {
		if _, err := ParseTantraEvaluatorID(s); err == nil {
			t.Errorf("bad id %q accepted", s)
		}
	}
}

func TestTantraEvaluatorID_SplitKeyID(t *testing.T) {
	id, suffix, err := SplitKeyID("bhiv.sovereign.decision.prod.v1#ed25519-2026-05")
	if err != nil {
		t.Fatalf("split: %v", err)
	}
	if id.Raw != "bhiv.sovereign.decision.prod.v1" {
		t.Errorf("id: got %q", id.Raw)
	}
	if suffix != "ed25519-2026-05" {
		t.Errorf("suffix: got %q", suffix)
	}
	if _, _, err := SplitKeyID("no-hash-suffix"); err == nil {
		t.Error("missing # not rejected")
	}
	if _, _, err := SplitKeyID("bhiv.sovereign.decision.prod.v1#a#b"); err == nil {
		t.Error("double # not rejected")
	}
}

func TestCanonicalDecisionMaterialBytes_Stable(t *testing.T) {
	m := TantraDecisionMaterial{
		SchemaVersion:   TantraSchemaV1,
		TraceID:         "abc",
		InputHash:       "def",
		Verdict:         TantraVerdictAllow,
		PolicyReference: "p",
		EvaluatorID:     "bhiv.sovereign.decision.prod.v1",
	}
	a := CanonicalDecisionMaterialBytes(m)
	b := CanonicalDecisionMaterialBytes(m)
	if string(a) != string(b) {
		t.Errorf("non-deterministic encoding:\n a=%s\n b=%s", a, b)
	}
	expected := `{"schema_version":"tantra.decision.v1","trace_id":"abc","input_hash":"def","verdict":"ALLOW","policy_reference":"p","evaluator_id":"bhiv.sovereign.decision.prod.v1"}`
	if string(a) != expected {
		t.Errorf("unexpected canonical bytes:\n got=%s\n want=%s", a, expected)
	}
}

func TestHybridProvider_RoundTripAndCompositeAND(t *testing.T) {
	provider := NewHybridProvider()
	priv, pub, err := provider.Generate(nil)
	if err != nil {
		t.Fatalf("generate: %v", err)
	}
	message := []byte("the quick brown fox jumps over the lazy dog")
	sig, err := provider.Sign(message, priv)
	if err != nil {
		t.Fatalf("sign: %v", err)
	}
	ok, reason := provider.Verify(message, sig, pub)
	if !ok {
		t.Fatalf("verify failed: %s", reason)
	}
	// Mutate the ed25519 component (first 64 bytes of sig payload — offset 7
	// past version+tag1+length). Verify must fail composite-AND.
	mutated := make([]byte, len(sig))
	copy(mutated, sig)
	if len(mutated) > 10 {
		mutated[7] ^= 0xFF
	}
	ok, _ = provider.Verify(message, mutated, pub)
	if ok {
		t.Error("verify accepted mutated ed25519 component (composite-AND violated)")
	}
	// Mutate the ml-dsa component (last bytes of sig).
	copy(mutated, sig)
	mutated[len(mutated)-1] ^= 0xFF
	ok, _ = provider.Verify(message, mutated, pub)
	if ok {
		t.Error("verify accepted mutated ml-dsa component (composite-AND violated)")
	}
}
