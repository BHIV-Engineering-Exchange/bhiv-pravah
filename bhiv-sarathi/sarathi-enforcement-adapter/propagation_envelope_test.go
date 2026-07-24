// propagation_envelope_test.go — Sealing, immutability, and chain-binding tests.

package main

import (
	"testing"
	"time"
)

// mkTestDecision builds a minimal ExternalDecision for envelope tests.
// It does NOT exercise the full evaluator-signature path — the envelope
// accepts any ExternalDecision whose hashes are already computed.
func mkTestDecision(t *testing.T) *ExternalDecision {
	t.Helper()
	d := NewExternalDecision(
		"test-evaluator",
		"agent-1",
		"resource-1",
		"read",
		ExternalVerdictAllow,
		[]string{},
		map[string]string{"test": "true"},
		"integration test",
		30*time.Second,
	)
	return d
}

// mkTestEnforcementResult builds a minimal ExternalEnforcementResult.
func mkTestEnforcementResult(d *ExternalDecision) *ExternalEnforcementResult {
	return &ExternalEnforcementResult{
		Decision:           d,
		Enforced:           true,
		Verdict:            string(d.Verdict),
		EnforcementHash:    Sha256Hex([]byte("test-enforcement-" + d.DecisionID)),
		CorrelationID:      "corr-test-1",
		EnforcedAt:         time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		Mode:               "EXTERNAL",
		DecisionCoreHash:   d.DecisionCoreHash,
		RequestBindingHash: Sha256Hex([]byte("binding-" + d.DecisionID)),
	}
}

// mkCanonicalResponse builds canonical response bytes for testing.
func mkCanonicalResponse(t *testing.T, extra map[string]interface{}) []byte {
	t.Helper()
	m := map[string]interface{}{
		"verdict":        "ALLOW",
		"error_code":     "",
		"schema_version": "sarathi.response/v13.0",
	}
	for k, v := range extra {
		m[k] = v
	}
	b, err := CanonicalMarshal(m)
	if err != nil {
		t.Fatalf("canonical marshal: %v", err)
	}
	return b
}

// TestSealPropagationEnvelope_BasicSeal: a minimal seal succeeds.
func TestSealPropagationEnvelope_BasicSeal(t *testing.T) {
	d := mkTestDecision(t)
	r := mkTestEnforcementResult(d)
	raw := []byte(`{"decision_id":"` + d.DecisionID + `"}`)
	canonical := mkCanonicalResponse(t, nil)
	tc := NewTraceContext()

	env, err := SealPropagationEnvelope(raw, d, r, canonical, "EXEC-TEST-1", tc, "corr-test-1")
	if err != nil {
		t.Fatalf("seal: %v", err)
	}
	if env.DecisionID() != d.DecisionID {
		t.Fatalf("decision_id drift: %s vs %s", env.DecisionID(), d.DecisionID)
	}
	if env.ResponseHash() != Sha256Hex(canonical) {
		t.Fatalf("response_hash drift")
	}
	if env.ChainBindingHash() == "" {
		t.Fatalf("chain_binding_hash empty")
	}
	if env.TraceID() != tc.TraceID {
		t.Fatalf("trace_id drift")
	}
	if env.SchemaVersion() != PropagationEnvelopeSchemaVersion {
		t.Fatalf("schema_version drift: %s", env.SchemaVersion())
	}
	if len(env.PropagationChain()) != 4 {
		t.Fatalf("propagation_chain length %d, want 4", len(env.PropagationChain()))
	}
}

// TestSealPropagationEnvelope_VerifySelf: freshly sealed envelope passes VerifySelf.
func TestSealPropagationEnvelope_VerifySelf(t *testing.T) {
	d := mkTestDecision(t)
	r := mkTestEnforcementResult(d)
	raw := []byte(`{"decision_id":"` + d.DecisionID + `"}`)
	canonical := mkCanonicalResponse(t, nil)

	env, err := SealPropagationEnvelope(raw, d, r, canonical, "EXEC-1", nil, "c1")
	if err != nil {
		t.Fatalf("seal: %v", err)
	}
	if err := env.VerifySelf(); err != nil {
		t.Fatalf("VerifySelf failed: %v", err)
	}
}

// TestSealPropagationEnvelope_DefensiveCopy: mutating returned slices does
// not affect envelope internal state.
func TestSealPropagationEnvelope_DefensiveCopy(t *testing.T) {
	d := mkTestDecision(t)
	r := mkTestEnforcementResult(d)
	raw := []byte(`{"decision_id":"` + d.DecisionID + `"}`)
	canonical := mkCanonicalResponse(t, nil)

	env, err := SealPropagationEnvelope(raw, d, r, canonical, "EXEC-1", nil, "c1")
	if err != nil {
		t.Fatalf("seal: %v", err)
	}

	// Mutate the returned slices
	resp := env.CanonicalResponseBytes()
	if len(resp) > 0 {
		resp[0] = 'X'
	}
	rawBack := env.RawDecisionBytes()
	if len(rawBack) > 0 {
		rawBack[0] = 'X'
	}
	chain := env.PropagationChain()
	if len(chain) > 0 {
		chain[0] = "MUTATED"
	}

	// Envelope must still verify
	if err := env.VerifySelf(); err != nil {
		t.Fatalf("VerifySelf failed after external mutation: %v", err)
	}
	// Re-accessing must return un-mutated values
	resp2 := env.CanonicalResponseBytes()
	if resp2[0] == 'X' {
		t.Fatalf("canonical_response_bytes was mutated via external reference")
	}
	chain2 := env.PropagationChain()
	if chain2[0] == "MUTATED" {
		t.Fatalf("propagation_chain was mutated via external reference")
	}
}

// TestSealPropagationEnvelope_RejectsNonCanonical: response bytes that are
// not in canonical form are rejected at seal time.
func TestSealPropagationEnvelope_RejectsNonCanonical(t *testing.T) {
	d := mkTestDecision(t)
	r := mkTestEnforcementResult(d)
	raw := []byte(`{"decision_id":"` + d.DecisionID + `"}`)
	// Non-canonical: keys out of lexical order.
	nonCanonical := []byte(`{"verdict":"ALLOW","error_code":""}`)

	_, err := SealPropagationEnvelope(raw, d, r, nonCanonical, "EXEC-1", nil, "c1")
	if err == nil {
		t.Fatalf("seal should have rejected non-canonical response bytes")
	}
}

// TestSealPropagationEnvelope_RejectsNilInputs: nil arguments produce errors.
func TestSealPropagationEnvelope_RejectsNilInputs(t *testing.T) {
	d := mkTestDecision(t)
	r := mkTestEnforcementResult(d)
	canonical := mkCanonicalResponse(t, nil)

	cases := []struct {
		name string
		raw  []byte
		d    *ExternalDecision
		r    *ExternalEnforcementResult
		resp []byte
	}{
		{"nil raw", nil, d, r, canonical},
		{"nil decision", []byte(`x`), nil, r, canonical},
		{"nil result", []byte(`x`), d, nil, canonical},
		{"nil response", []byte(`x`), d, r, nil},
	}
	for _, c := range cases {
		_, err := SealPropagationEnvelope(c.raw, c.d, c.r, c.resp, "E1", nil, "c1")
		if err == nil {
			t.Fatalf("case %q: expected error, got nil", c.name)
		}
	}
}

// TestSealPropagationEnvelope_ChainBindingStability: identical inputs produce
// identical chain_binding_hash values.
func TestSealPropagationEnvelope_ChainBindingStability(t *testing.T) {
	d := mkTestDecision(t)
	r := mkTestEnforcementResult(d)
	raw := []byte(`{"decision_id":"` + d.DecisionID + `"}`)
	canonical := mkCanonicalResponse(t, nil)

	env1, err := SealPropagationEnvelope(raw, d, r, canonical, "EXEC-1", nil, "c1")
	if err != nil {
		t.Fatalf("seal 1: %v", err)
	}
	env2, err := SealPropagationEnvelope(raw, d, r, canonical, "EXEC-1", nil, "c1")
	if err != nil {
		t.Fatalf("seal 2: %v", err)
	}

	// Chain binding hash must be identical (derived from decision/enforcement/response hashes)
	if env1.ChainBindingHash() != env2.ChainBindingHash() {
		t.Fatalf("chain_binding_hash drift: %s vs %s", env1.ChainBindingHash(), env2.ChainBindingHash())
	}
	if env1.ResponseHash() != env2.ResponseHash() {
		t.Fatalf("response_hash drift: %s vs %s", env1.ResponseHash(), env2.ResponseHash())
	}
}

// TestPropagationEnvelope_ToHeaderMap: headers include expected keys.
func TestPropagationEnvelope_ToHeaderMap(t *testing.T) {
	d := mkTestDecision(t)
	r := mkTestEnforcementResult(d)
	raw := []byte(`{"decision_id":"` + d.DecisionID + `"}`)
	canonical := mkCanonicalResponse(t, nil)

	env, err := SealPropagationEnvelope(raw, d, r, canonical, "EXEC-1", nil, "c1")
	if err != nil {
		t.Fatalf("seal: %v", err)
	}
	h := env.ToHeaderMap()
	expectedKeys := []string{
		HeaderTraceID, HeaderResponseHash, HeaderChainBinding,
		HeaderDecisionID, HeaderExecutionID, HeaderSchemaVersion,
	}
	for _, k := range expectedKeys {
		if v, ok := h[k]; !ok || v == "" {
			t.Fatalf("header %s missing or empty", k)
		}
	}
	if h[HeaderResponseHash] != env.ResponseHash() {
		t.Fatalf("header response_hash drift")
	}
}

// TestPropagationEnvelope_EqualsBytes: verifies byte-equality oracle.
func TestPropagationEnvelope_EqualsBytes(t *testing.T) {
	d := mkTestDecision(t)
	r := mkTestEnforcementResult(d)
	raw := []byte(`{"x":1}`)
	canonical := mkCanonicalResponse(t, nil)

	env, err := SealPropagationEnvelope(raw, d, r, canonical, "EXEC-1", nil, "c1")
	if err != nil {
		t.Fatalf("seal: %v", err)
	}
	if !env.EqualsBytes(canonical) {
		t.Fatalf("EqualsBytes rejected identical bytes")
	}
	// Change one byte
	mutated := make([]byte, len(canonical))
	copy(mutated, canonical)
	mutated[0] = 'Z'
	if env.EqualsBytes(mutated) {
		t.Fatalf("EqualsBytes accepted mutated bytes")
	}
}
