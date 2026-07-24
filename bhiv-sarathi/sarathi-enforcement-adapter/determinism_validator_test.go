// determinism_validator_test.go — Unit tests for the byte-equality oracle.

package main

import (
	"errors"
	"os"
	"strings"
	"testing"
)

// mkEnvForValidator returns a sealed envelope usable for validator tests.
func mkEnvForValidator(t *testing.T) (*PropagationEnvelope, []byte) {
	t.Helper()
	d := mkTestDecision(t)
	r := mkTestEnforcementResult(d)
	raw := []byte(`{"decision_id":"` + d.DecisionID + `"}`)
	canonical := mkCanonicalResponse(t, nil)
	env, err := SealPropagationEnvelope(raw, d, r, canonical, "EXEC-V1", nil, "corr-v1")
	if err != nil {
		t.Fatalf("seal: %v", err)
	}
	return env, canonical
}

// TestValidateHop_Success: identical sent/ack hashes → bytes_match = true.
func TestValidateHop_Success(t *testing.T) {
	env, canonical := mkEnvForValidator(t)
	h := Sha256Hex(canonical)
	ok, res := ValidateHop(HopCore, canonical, h, h, env)
	if !ok {
		t.Fatalf("expected success, got violation=%s detail=%s", res.ViolationCode, res.Detail)
	}
	if res.Hop != HopCore {
		t.Fatalf("hop mismatch: %s", res.Hop)
	}
	if res.TraceID != env.TraceID() {
		t.Fatalf("trace_id not copied into result")
	}
}

// TestValidateHop_AckMismatch: ACK hash differs → CodeResponseHashMismatch.
func TestValidateHop_AckMismatch(t *testing.T) {
	env, canonical := mkEnvForValidator(t)
	sentHash := Sha256Hex(canonical)
	ackHash := Sha256Hex([]byte("wrong"))
	ok, res := ValidateHop(HopInsightFlow, canonical, sentHash, ackHash, env)
	if ok {
		t.Fatalf("expected violation")
	}
	if res.ViolationCode != CodeResponseHashMismatch {
		t.Fatalf("code mismatch: got %s want %s", res.ViolationCode, CodeResponseHashMismatch)
	}
}

// TestValidateHop_SentBytesMutated: bytes don't hash to sent_hash →
// CodePropagationByteMismatch.
func TestValidateHop_SentBytesMutated(t *testing.T) {
	env, canonical := mkEnvForValidator(t)
	sentHash := Sha256Hex(canonical)
	mutated := append([]byte{}, canonical...)
	mutated[0] = 'X'
	ok, res := ValidateHop(HopBucket, mutated, sentHash, sentHash, env)
	if ok {
		t.Fatalf("expected violation")
	}
	if res.ViolationCode != CodePropagationByteMismatch {
		t.Fatalf("code mismatch: got %s want %s", res.ViolationCode, CodePropagationByteMismatch)
	}
}

// TestValidateHop_EnvelopeDivergence: sent bytes valid but diverge from
// envelope's sealed bytes → CodePropagationByteMismatch.
func TestValidateHop_EnvelopeDivergence(t *testing.T) {
	env, _ := mkEnvForValidator(t)
	// Build a completely different canonical payload — different content.
	alt := mkCanonicalResponse(t, map[string]interface{}{"x": 1})
	altHash := Sha256Hex(alt)
	ok, res := ValidateHop(HopCore, alt, altHash, altHash, env)
	if ok {
		t.Fatalf("expected violation")
	}
	if res.ViolationCode != CodePropagationByteMismatch {
		t.Fatalf("code mismatch: got %s want %s", res.ViolationCode, CodePropagationByteMismatch)
	}
}

// TestValidateHop_EmptySentHash: empty declared hash → CodeDeterminismViolation.
func TestValidateHop_EmptySentHash(t *testing.T) {
	env, canonical := mkEnvForValidator(t)
	ok, res := ValidateHop(HopCore, canonical, "", "doesntmatter", env)
	if ok {
		t.Fatalf("expected violation")
	}
	if res.ViolationCode != CodeDeterminismViolation {
		t.Fatalf("code mismatch: got %s want %s", res.ViolationCode, CodeDeterminismViolation)
	}
}

// TestValidateChain_Success: a freshly sealed envelope passes.
func TestValidateChain_Success(t *testing.T) {
	env, _ := mkEnvForValidator(t)
	ok, detail := ValidateChain(env)
	if !ok {
		t.Fatalf("expected success, got %s", detail)
	}
}

// TestValidateChain_NilEnv: nil envelope fails gracefully.
func TestValidateChain_NilEnv(t *testing.T) {
	ok, detail := ValidateChain(nil)
	if ok {
		t.Fatalf("nil envelope should not validate")
	}
	if detail == "" {
		t.Fatalf("validation failure must carry detail")
	}
}

// TestPropagationStopError_ErrorString: error string contains hop and code.
func TestPropagationStopError_ErrorString(t *testing.T) {
	res := ByteEqualityResult{
		Hop:           HopBucket,
		ViolationCode: CodeDeterminismViolation,
		TraceID:       "trace-1",
		Detail:        "ack_hash mismatch",
	}
	err := NewPropagationStopError(res)
	if err == nil {
		t.Fatalf("error is nil")
	}
	s := err.Error()
	if !strings.Contains(s, HopBucket) {
		t.Fatalf("error should contain hop: %s", s)
	}
	if !strings.Contains(s, CodeDeterminismViolation) {
		t.Fatalf("error should contain code: %s", s)
	}
	// IsPropagationStop must recognize it.
	if !IsPropagationStop(err) {
		t.Fatalf("IsPropagationStop returned false for *PropagationStopError")
	}
	// errors.As must recover the concrete type.
	var pse *PropagationStopError
	if !errors.As(err, &pse) {
		t.Fatalf("errors.As did not recover type")
	}
	if pse.Code != CodeDeterminismViolation {
		t.Fatalf("Code drift: %s", pse.Code)
	}
}

// TestRecordViolation_AppendOnly: two violations produce two lines in the log.
func TestRecordViolation_AppendOnly(t *testing.T) {
	// Clean slate for this test's scope.
	_ = os.Remove(DeterminismViolationLogPath)
	CloseViolationLog()

	res1 := ByteEqualityResult{
		Hop:           HopCore,
		ViolationCode: CodeResponseHashMismatch,
		TraceID:       "t1",
		Detail:        "first",
		BytesMatch:    false,
	}
	res2 := ByteEqualityResult{
		Hop:           HopBucket,
		ViolationCode: CodePropagationByteMismatch,
		TraceID:       "t2",
		Detail:        "second",
		BytesMatch:    false,
	}
	if err := RecordViolation(res1); err != nil {
		t.Fatalf("record 1: %v", err)
	}
	if err := RecordViolation(res2); err != nil {
		t.Fatalf("record 2: %v", err)
	}
	// Passing result must be a no-op.
	if err := RecordViolation(ByteEqualityResult{BytesMatch: true}); err != nil {
		t.Fatalf("record passing: %v", err)
	}
	CloseViolationLog()

	data, err := os.ReadFile(DeterminismViolationLogPath)
	if err != nil {
		t.Fatalf("read log: %v", err)
	}
	lines := 0
	for _, b := range data {
		if b == '\n' {
			lines++
		}
	}
	if lines != 2 {
		t.Fatalf("expected 2 lines, got %d (content=%s)", lines, data)
	}
}
