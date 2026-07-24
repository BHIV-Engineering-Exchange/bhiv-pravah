package main

// cet_service_handler_test.go — live wire-path tests for POST /sarathi/cet/enforce.
//
// Proves the HTTP boundary (not just the offline driver) accepts a real signed
// SUM-SCRIPT, preserves the locked identity, and fails closed with a
// trace-bound rejection on mutation. Uses httptest — no network, no full
// pipeline boot (the handler only needs the active provider + TANTRA registry
// + replay store, which the helper wires).
//
// TAG: tantra-convergence-v1

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

// setupCETTestGlobals wires the process-wide active provider + TANTRA registry
// + replay store the live handler reads through NewCETBoundary().
func setupCETTestGlobals(t *testing.T) (CryptoProvider, PrivateKeyMaterial, string) {
	t.Helper()
	provider := NewEd25519Provider()
	SetActiveProviderForTest(provider)
	priv, pub, err := provider.Generate(nil)
	if err != nil {
		t.Fatalf("generate sovereign key: %v", err)
	}
	keyID := LockedSovereignEvalID + "#ed25519-cethandler-test"
	tc, n, err := NewTantraTrustConsumer([]TantraEvaluatorEntry{{
		EvaluatorID:   LockedSovereignEvalID,
		Name:          "handler-test",
		Status:        "ACTIVE",
		SchemaVersion: TantraSchemaV1,
		Algorithm:     string(provider.Algorithm()),
		KeyID:         keyID,
		PublicKey:     provider.EncodePublicKey(pub),
	}}, provider)
	if err != nil || n != 1 {
		t.Fatalf("registry build (n=%d): %v", n, err)
	}
	SetActiveTantraTrustForTest(tc)
	activeTantraReplayStore = NewMemoryTantraReplayStore()
	return provider, priv, keyID
}

func buildTestSumScriptBytes(t *testing.T, provider CryptoProvider, priv PrivateKeyMaterial, keyID, traceID string) []byte {
	t.Helper()
	_, wire, err := buildSignedConvergenceDecision(provider, priv, keyID, traceID, time.Now().UTC())
	if err != nil {
		t.Fatalf("build inner decision: %v", err)
	}
	sum := &CETSumScript{
		SchemaVersion:   CETConvergenceSchemaVersion,
		ContractVersion: CETConvergenceContractVersion,
		ExecutionID:     LockedExecutionID,
		TraceID:         traceID,
		CETHash:         LockedCETHash,
		BucketKey:       LockedBucketKey,
		DecisionB64:     base64.StdEncoding.EncodeToString(wire),
	}
	raw, err := json.Marshal(sum)
	if err != nil {
		t.Fatalf("marshal sum-script: %v", err)
	}
	return raw
}

func newCETTestBoundary() *ServiceBoundary {
	return &ServiceBoundary{config: ServiceBoundaryConfig{MaxRequestBodyBytes: 1 << 20}}
}

func TestCETHandler_AcceptsLockedChain(t *testing.T) {
	provider, priv, keyID := setupCETTestGlobals(t)
	raw := buildTestSumScriptBytes(t, provider, priv, keyID, LockedTraceID)

	req := httptest.NewRequest(http.MethodPost, CETEnforcePath, bytes.NewReader(raw))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	newCETTestBoundary().handleSarathiCETEnforce(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200; body=%s", w.Code, w.Body.String())
	}
	var art SarathiEnforcementDecisionArtifact
	if err := json.Unmarshal(w.Body.Bytes(), &art); err != nil {
		t.Fatalf("decode artifact: %v", err)
	}
	if art.Decision != "allow" {
		t.Errorf("decision = %q, want allow", art.Decision)
	}
	if art.ExecutionID != LockedExecutionID || art.TraceID != LockedTraceID || art.CETHash != LockedCETHash || art.BucketKey != LockedBucketKey {
		t.Errorf("locked identity not preserved: exec=%s trace=%s cet=%s bucket=%s",
			art.ExecutionID, art.TraceID, art.CETHash, art.BucketKey)
	}
	if art.SchemaVersion != CETConvergenceSchemaVersion || art.ContractVersion != CETConvergenceContractVersion {
		t.Errorf("envelope versions wrong: %s / %s", art.SchemaVersion, art.ContractVersion)
	}
	c := art.ContractContinuity
	if !c.SumScriptReceived || !c.CETHashVerified || !c.TraceIDPreserved || c.MutationDetected {
		t.Errorf("contract_continuity wrong: %+v", c)
	}
	if w.Header().Get("X-Sarathi-CET-Hash") != LockedCETHash {
		t.Errorf("response missing/incorrect X-Sarathi-CET-Hash header")
	}
}

func TestCETHandler_RejectsMutatedInner(t *testing.T) {
	provider, priv, keyID := setupCETTestGlobals(t)
	raw := buildTestSumScriptBytes(t, provider, priv, keyID, LockedTraceID)

	var sum CETSumScript
	if err := json.Unmarshal(raw, &sum); err != nil {
		t.Fatalf("unmarshal: %v", err)
	}
	inner, err := base64.StdEncoding.DecodeString(sum.DecisionB64)
	if err != nil {
		t.Fatalf("decode inner: %v", err)
	}
	marker := []byte(`"enforcement_binding":"CLEARED`)
	idx := bytes.Index(inner, marker)
	if idx < 0 {
		t.Fatalf("could not find enforcement_binding to mutate")
	}
	inner[idx+len(`"enforcement_binding":"`)] = 'X' // flip a signed byte
	sum.DecisionB64 = base64.StdEncoding.EncodeToString(inner)
	raw2, _ := json.Marshal(&sum)

	req := httptest.NewRequest(http.MethodPost, CETEnforcePath, bytes.NewReader(raw2))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	newCETTestBoundary().handleSarathiCETEnforce(w, req)

	if w.Code == http.StatusOK {
		t.Fatalf("mutated chain accepted (status 200); body=%s", w.Body.String())
	}
	if got := w.Header().Get("X-Sarathi-Error-Code"); got != ErrCETInnerDecisionInvalid {
		t.Errorf("X-Sarathi-Error-Code = %q, want %q", got, ErrCETInnerDecisionInvalid)
	}
	var rej SarathiTraceBoundRejectionArtifact
	if err := json.Unmarshal(w.Body.Bytes(), &rej); err != nil {
		t.Fatalf("decode rejection: %v", err)
	}
	if rej.ValidationStatus != "rejected" || !rej.FailClosed {
		t.Errorf("rejection not fail-closed: %+v", rej)
	}
	if rej.TraceID != LockedTraceID {
		t.Errorf("rejection did not echo locked trace_id: %q", rej.TraceID)
	}
}

func TestCETHandler_RejectsWrongContractVersion(t *testing.T) {
	provider, priv, keyID := setupCETTestGlobals(t)
	raw := buildTestSumScriptBytes(t, provider, priv, keyID, LockedTraceID)
	var sum CETSumScript
	_ = json.Unmarshal(raw, &sum)
	sum.ContractVersion = "TANTRA-CONVERGENCE-v2" // not the locked version
	raw2, _ := json.Marshal(&sum)

	req := httptest.NewRequest(http.MethodPost, CETEnforcePath, bytes.NewReader(raw2))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	newCETTestBoundary().handleSarathiCETEnforce(w, req)

	if w.Code != http.StatusBadRequest {
		t.Fatalf("status = %d, want 400; body=%s", w.Code, w.Body.String())
	}
	if got := w.Header().Get("X-Sarathi-Error-Code"); got != ErrCETContractVersionUnknown {
		t.Errorf("X-Sarathi-Error-Code = %q, want %q", got, ErrCETContractVersionUnknown)
	}
}
