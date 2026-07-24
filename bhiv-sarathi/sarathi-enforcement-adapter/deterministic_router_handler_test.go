// deterministic_router_handler_test.go — unit tests for the byte-equality
// enforcing routing handler. Uses httptest.Server to stand in for downstream
// systems; asserts the exact bytes sent, the full propagation header set,
// the ACK echo semantics, and the Intelligence digest isolation.

package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

// mkEnvForRouter returns a sealed envelope and its canonical bytes. Reuses
// the helpers from propagation_envelope_test.go.
func mkEnvForRouter(t *testing.T) (*PropagationEnvelope, []byte) {
	t.Helper()
	d := mkTestDecision(t)
	r := mkTestEnforcementResult(d)
	raw := []byte(`{"decision_id":"` + d.DecisionID + `"}`)
	canonical := mkCanonicalResponse(t, nil)
	env, err := SealPropagationEnvelope(raw, d, r, canonical, "EXEC-DR-1", nil, "corr-dr-1")
	if err != nil {
		t.Fatalf("seal: %v", err)
	}
	return env, canonical
}

// TestDeterministicHandler_Success_AckMatches: normal in-chain flow —
// server echoes X-Sarathi-Ack-Hash correctly, handler returns nil.
func TestDeterministicHandler_Success_AckMatches(t *testing.T) {
	env, canonical := mkEnvForRouter(t)

	var gotBody []byte
	var gotHeaders http.Header
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		gotBody, _ = io.ReadAll(req.Body)
		gotHeaders = req.Header.Clone()
		// Echo the response_hash back — this is the byte-equality contract.
		w.Header().Set(HeaderAckHash, req.Header.Get(HeaderResponseHash))
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	cfg := DeterministicHTTPRoutingConfig{
		HTTPRoutingConfig: HTTPRoutingConfig{
			TargetURL: srv.URL,
			Timeout:   2 * time.Second,
		},
		RequireAckHashHeader: true,
	}
	handler := NewDeterministicHTTPRoutingHandler("core", env, cfg)

	if err := handler(&RoutedEvent{EventID: "e1"}); err != nil {
		t.Fatalf("expected success, got: %v", err)
	}

	// Body must be exactly the sealed canonical bytes — no re-serialization.
	if !bytes.Equal(gotBody, canonical) {
		t.Fatalf("body mismatch:\n got=%q\nwant=%q", gotBody, canonical)
	}

	// Full propagation header set must be present.
	for _, h := range []string{
		HeaderTraceID, HeaderResponseHash, HeaderChainBinding,
		HeaderDecisionID, HeaderExecutionID, HeaderCorrelationID,
		HeaderSchemaVersion, HeaderEnforcementHash,
	} {
		if gotHeaders.Get(h) == "" {
			t.Fatalf("missing propagation header: %s", h)
		}
	}
	if got := gotHeaders.Get(HeaderResponseHash); got != env.ResponseHash() {
		t.Fatalf("response-hash header drift: got=%s want=%s", got, env.ResponseHash())
	}
}

// TestDeterministicHandler_AckMismatch_ReturnsStopError: server returns 200
// but echoes the WRONG hash. The handler must return *PropagationStopError
// with a byte-equality code so RoutePropagation can halt the chain.
func TestDeterministicHandler_AckMismatch_ReturnsStopError(t *testing.T) {
	env, _ := mkEnvForRouter(t)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		w.Header().Set(HeaderAckHash, "0000000000000000000000000000000000000000000000000000000000000000")
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	cfg := DeterministicHTTPRoutingConfig{
		HTTPRoutingConfig: HTTPRoutingConfig{
			TargetURL: srv.URL, Timeout: 2 * time.Second,
		},
		RequireAckHashHeader: true,
	}
	handler := NewDeterministicHTTPRoutingHandler("core", env, cfg)

	err := handler(&RoutedEvent{EventID: "e2"})
	if err == nil {
		t.Fatalf("expected *PropagationStopError")
	}
	var pse *PropagationStopError
	if !errors.As(err, &pse) {
		t.Fatalf("error type: got %T (%v)", err, err)
	}
	if pse.Code != CodeResponseHashMismatch {
		t.Fatalf("code: got %s want %s", pse.Code, CodeResponseHashMismatch)
	}
}

// TestDeterministicHandler_IntelligenceDigest_BodyIsDigest: when
// IntelligenceReadOnly=true, the handler sends an IntelligenceDigestEvent
// (NOT the canonical response bytes) and does not enforce ACK.
func TestDeterministicHandler_IntelligenceDigest_BodyIsDigest(t *testing.T) {
	env, canonical := mkEnvForRouter(t)

	var gotBody []byte
	var gotDigestFlag string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		gotBody, _ = io.ReadAll(req.Body)
		gotDigestFlag = req.Header.Get("X-Sarathi-Digest-Only")
		// Intentionally do NOT set X-Sarathi-Ack-Hash — digest-only hops
		// must not require ACK.
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	cfg := DeterministicHTTPRoutingConfig{
		HTTPRoutingConfig: HTTPRoutingConfig{
			TargetURL: srv.URL, Timeout: 2 * time.Second,
		},
		IntelligenceReadOnly: true,
	}
	handler := NewDeterministicHTTPRoutingHandler("intent_layer", env, cfg)

	if err := handler(&RoutedEvent{EventID: "e3"}); err != nil {
		t.Fatalf("expected success for digest-only, got: %v", err)
	}
	if gotDigestFlag != "true" {
		t.Fatalf("X-Sarathi-Digest-Only not set on digest-only request")
	}
	// Body must NOT equal canonical bytes — it must be a digest event.
	if bytes.Equal(gotBody, canonical) {
		t.Fatalf("digest hop must not send canonical response bytes")
	}
	// Body must decode as an IntelligenceDigestEvent with fingerprint hashes only.
	var de IntelligenceDigestEvent
	if err := json.Unmarshal(gotBody, &de); err != nil {
		t.Fatalf("digest event parse: %v", err)
	}
	if de.SchemaVersion != IntelligenceDigestSchemaVersion {
		t.Fatalf("digest schema drift: %s", de.SchemaVersion)
	}
	if de.ResponseHash != env.ResponseHash() {
		t.Fatalf("digest response_hash drift")
	}
	if de.VerdictHash == "" {
		t.Fatalf("digest verdict_hash missing")
	}
}

// TestDeterministicHandler_NilEnvelope: handler must reject a nil envelope
// rather than panic.
func TestDeterministicHandler_NilEnvelope(t *testing.T) {
	cfg := DeterministicHTTPRoutingConfig{
		HTTPRoutingConfig: HTTPRoutingConfig{TargetURL: "http://127.0.0.1:0"},
	}
	handler := NewDeterministicHTTPRoutingHandler("x", nil, cfg)
	if err := handler(&RoutedEvent{}); err == nil {
		t.Fatalf("expected error on nil envelope")
	}
}

// TestDeterministicHandler_5xx_Failure: HTTP 500 must return a SERVER_ERROR
// (not a propagation stop — it's a transient fault, not a determinism break).
func TestDeterministicHandler_5xx_Failure(t *testing.T) {
	env, _ := mkEnvForRouter(t)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer srv.Close()

	cfg := DeterministicHTTPRoutingConfig{
		HTTPRoutingConfig: HTTPRoutingConfig{TargetURL: srv.URL, Timeout: 2 * time.Second},
	}
	handler := NewDeterministicHTTPRoutingHandler("core", env, cfg)
	err := handler(&RoutedEvent{})
	if err == nil {
		t.Fatalf("expected error on 500")
	}
	// Must NOT be *PropagationStopError — a 5xx is a transient fault.
	var pse *PropagationStopError
	if errors.As(err, &pse) {
		t.Fatalf("5xx should not be PropagationStopError, got code=%s", pse.Code)
	}
}

// TestIsValidDigestPayload_Happy: a properly-built digest event validates.
func TestIsValidDigestPayload_Happy(t *testing.T) {
	env, _ := mkEnvForRouter(t)
	de := DigestEventFor(env)
	b, err := CanonicalMarshal(de)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	ok, detail := IsValidDigestPayload(b)
	if !ok {
		t.Fatalf("expected valid digest, got: %s", detail)
	}
}

// TestIsValidDigestPayload_ForbiddenField: payload carrying a forbidden
// top-level field (e.g. "verdict") must be rejected. This is the
// Intelligence-side defense in depth against accidental body leakage.
func TestIsValidDigestPayload_ForbiddenField(t *testing.T) {
	env, _ := mkEnvForRouter(t)
	de := DigestEventFor(env)
	// Inject forbidden "verdict" field into the marshaled form.
	m := map[string]interface{}{
		"event_id":       de.EventID,
		"trace_id":       de.TraceID,
		"correlation_id": de.CorrelationID,
		"response_hash":  de.ResponseHash,
		"verdict_hash":   de.VerdictHash,
		"timestamp":      de.Timestamp,
		"schema_version": de.SchemaVersion,
		"verdict":        "ALLOW", // forbidden
	}
	b, err := CanonicalMarshal(m)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	ok, detail := IsValidDigestPayload(b)
	if ok {
		t.Fatalf("expected rejection, got valid")
	}
	if detail == "" {
		t.Fatalf("missing rejection detail")
	}
}

// TestIsValidDigestPayload_WrongSchemaVersion: the gate must reject a
// payload with a drifted schema version even if every other field is valid.
func TestIsValidDigestPayload_WrongSchemaVersion(t *testing.T) {
	env, _ := mkEnvForRouter(t)
	de := DigestEventFor(env)
	de.SchemaVersion = "sarathi.intelligence.digest/v99.0"
	b, err := CanonicalMarshal(de)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	ok, _ := IsValidDigestPayload(b)
	if ok {
		t.Fatalf("expected rejection on schema drift")
	}
}
