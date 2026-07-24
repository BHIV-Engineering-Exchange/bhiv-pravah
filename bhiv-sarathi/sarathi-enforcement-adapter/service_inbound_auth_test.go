package main

// service_inbound_auth_test.go — v15.0 Sovereign Identity Closure tests.
//
// Tables cover every rejection branch and the happy path against a real
// InMemoryTrustConsumer (no mocks). The test constructs actual Ed25519
// keypairs, signs real payloads, and exercises the live middleware through
// net/http/httptest.

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

// buildTestMiddleware wires a real trust consumer around a freshly-generated
// Ed25519 keypair and returns the middleware plus the priv/pub material.
func buildTestMiddleware(t *testing.T, issuerID string, mode InboundAuthMode) (*InboundAuthMiddleware, ed25519.PrivateKey, TrustConsumer) {
	t.Helper()
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("keygen: %v", err)
	}
	snap := &TrustSnapshotFile{
		Version: "test",
		Evaluators: []EvaluatorTrustSnapshot{
			{EvaluatorID: issuerID, Name: "test", Status: "ACTIVE", PublicKeyHex: hex.EncodeToString(pub)},
		},
	}
	tc, err := NewInMemoryTrustConsumer(snap)
	if err != nil {
		t.Fatalf("trust consumer: %v", err)
	}
	dir := t.TempDir()
	cfg := InboundAuthConfig{
		Mode:          mode,
		Trust:         tc,
		MaxSkew:       2 * time.Minute,
		NonceCapacity: 1000,
		NonceWindow:   5 * time.Minute,
		NonceOverflow: dir + "/nonces.jsonl",
		RejectLog:     dir + "/rejects.jsonl",
	}
	m, err := NewInboundAuthMiddleware(cfg)
	if err != nil {
		t.Fatalf("middleware: %v", err)
	}
	return m, priv, tc
}

// signedRequest assembles a signed POST against /v1/enforce using the given
// overrides. When any override is "", the test uses a correct value so only
// the changed field is wrong.
type overrides struct {
	issuerID  string
	nonce     string
	timestamp string
	signature string
	algorithm string
	body      []byte
}

func makeSignedRequest(issuer string, priv ed25519.PrivateKey, body []byte, ov overrides) *http.Request {
	nonce := ov.nonce
	if nonce == "" {
		var b [16]byte
		_, _ = rand.Read(b[:])
		nonce = hex.EncodeToString(b[:])
	}
	timestamp := ov.timestamp
	if timestamp == "" {
		timestamp = time.Now().UTC().Format(time.RFC3339)
	}
	issuerID := ov.issuerID
	if issuerID == "" {
		issuerID = issuer
	}
	algo := ov.algorithm
	if algo == "" {
		algo = "ed25519"
	}
	payloadBody := body
	if ov.body != nil {
		payloadBody = ov.body
	}
	canonical, _ := CanonicalMarshalBytes(body)
	sig := ov.signature
	if sig == "" {
		payload := buildInboundSigningPayload(canonical, nonce, timestamp, issuerID)
		sig = base64.StdEncoding.EncodeToString(ed25519.Sign(priv, payload))
	}

	req := httptest.NewRequest(http.MethodPost, "/v1/enforce", bytes.NewReader(payloadBody))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", "test-api-key")
	req.Header.Set(HeaderSarathiIssuerID, issuerID)
	req.Header.Set(HeaderSarathiRequestNonce, nonce)
	req.Header.Set(HeaderSarathiTimestamp, timestamp)
	req.Header.Set(HeaderSarathiBodySignature, sig)
	req.Header.Set(HeaderSarathiSigAlgorithm, algo)
	return req
}

// nextOK is a stand-in for the downstream handler. It just echoes.
func nextOK(w http.ResponseWriter, r *http.Request) {
	b, _ := io.ReadAll(r.Body)
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(b)
}

func decodeError(t *testing.T, body *bytes.Buffer) map[string]string {
	t.Helper()
	var m map[string]string
	if err := json.Unmarshal(body.Bytes(), &m); err != nil {
		t.Fatalf("error decode: %v raw=%q", err, body.String())
	}
	return m
}

func TestInboundAuth_HappyPath(t *testing.T) {
	issuer := "evaluator-happy"
	m, priv, _ := buildTestMiddleware(t, issuer, InboundAuthRequired)
	defer m.Close()

	body := []byte(`{"decision_id":"D1","verdict":"ALLOW"}`)
	req := makeSignedRequest(issuer, priv, body, overrides{})
	rec := httptest.NewRecorder()
	m.Wrap(http.HandlerFunc(nextOK)).ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("want 200, got %d body=%s", rec.Code, rec.Body.String())
	}
	if got := rec.Header().Get("X-Sarathi-Verified-Issuer"); got != issuer {
		t.Fatalf("verified issuer header missing/wrong: %q", got)
	}
}

func TestInboundAuth_MissingHeaders(t *testing.T) {
	m, _, _ := buildTestMiddleware(t, "evaluator-mh", InboundAuthRequired)
	defer m.Close()

	req := httptest.NewRequest(http.MethodPost, "/v1/enforce", bytes.NewReader([]byte(`{}`)))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", "k")
	rec := httptest.NewRecorder()
	m.Wrap(http.HandlerFunc(nextOK)).ServeHTTP(rec, req)

	if rec.Code != http.StatusBadRequest {
		t.Fatalf("want 400, got %d", rec.Code)
	}
	if got := decodeError(t, rec.Body)["error"]; got != CodeInboundSignatureMissing {
		t.Fatalf("want %s, got %s", CodeInboundSignatureMissing, got)
	}
}

func TestInboundAuth_TimestampSkew(t *testing.T) {
	issuer := "evaluator-skew"
	m, priv, _ := buildTestMiddleware(t, issuer, InboundAuthRequired)
	defer m.Close()

	old := time.Now().UTC().Add(-1 * time.Hour).Format(time.RFC3339)
	body := []byte(`{"k":"v"}`)
	req := makeSignedRequest(issuer, priv, body, overrides{timestamp: old})
	rec := httptest.NewRecorder()
	m.Wrap(http.HandlerFunc(nextOK)).ServeHTTP(rec, req)

	if rec.Code != http.StatusUnauthorized {
		t.Fatalf("want 401, got %d", rec.Code)
	}
	if got := decodeError(t, rec.Body)["error"]; got != CodeInboundTimestampSkewed {
		t.Fatalf("want %s, got %s", CodeInboundTimestampSkewed, got)
	}
}

func TestInboundAuth_NonceReplay(t *testing.T) {
	issuer := "evaluator-nonce"
	m, priv, _ := buildTestMiddleware(t, issuer, InboundAuthRequired)
	defer m.Close()

	body := []byte(`{"k":"v"}`)
	nonce := "fixed-nonce-abc"
	ts := time.Now().UTC().Format(time.RFC3339)

	// First call — success.
	req1 := makeSignedRequest(issuer, priv, body, overrides{nonce: nonce, timestamp: ts})
	rec1 := httptest.NewRecorder()
	m.Wrap(http.HandlerFunc(nextOK)).ServeHTTP(rec1, req1)
	if rec1.Code != http.StatusOK {
		t.Fatalf("first call want 200, got %d", rec1.Code)
	}

	// Second call with same nonce — must reject.
	req2 := makeSignedRequest(issuer, priv, body, overrides{nonce: nonce, timestamp: ts})
	rec2 := httptest.NewRecorder()
	m.Wrap(http.HandlerFunc(nextOK)).ServeHTTP(rec2, req2)
	if rec2.Code != http.StatusConflict {
		t.Fatalf("replay want 409, got %d body=%s", rec2.Code, rec2.Body.String())
	}
	if got := decodeError(t, rec2.Body)["error"]; got != CodeInboundNonceReplay {
		t.Fatalf("want %s, got %s", CodeInboundNonceReplay, got)
	}
}

func TestInboundAuth_UnknownIssuer(t *testing.T) {
	issuer := "evaluator-known"
	m, priv, _ := buildTestMiddleware(t, issuer, InboundAuthRequired)
	defer m.Close()

	body := []byte(`{"k":"v"}`)
	req := makeSignedRequest(issuer, priv, body, overrides{issuerID: "ghost-evaluator"})
	rec := httptest.NewRecorder()
	m.Wrap(http.HandlerFunc(nextOK)).ServeHTTP(rec, req)

	if rec.Code != http.StatusForbidden {
		t.Fatalf("want 403, got %d", rec.Code)
	}
	if got := decodeError(t, rec.Body)["error"]; got != CodeEvaluatorNotRegistered {
		t.Fatalf("want %s, got %s", CodeEvaluatorNotRegistered, got)
	}
}

func TestInboundAuth_BadSignature(t *testing.T) {
	issuer := "evaluator-badsig"
	m, priv, _ := buildTestMiddleware(t, issuer, InboundAuthRequired)
	defer m.Close()

	body := []byte(`{"k":"v"}`)
	// Forge a valid-length signature that is cryptographically wrong.
	fake := base64.StdEncoding.EncodeToString(make([]byte, ed25519.SignatureSize))
	req := makeSignedRequest(issuer, priv, body, overrides{signature: fake})
	rec := httptest.NewRecorder()
	m.Wrap(http.HandlerFunc(nextOK)).ServeHTTP(rec, req)

	if rec.Code != http.StatusUnauthorized {
		t.Fatalf("want 401, got %d", rec.Code)
	}
	if got := decodeError(t, rec.Body)["error"]; got != CodeInboundSignatureInvalid {
		t.Fatalf("want %s, got %s", CodeInboundSignatureInvalid, got)
	}
}

func TestInboundAuth_OptionalPassthrough(t *testing.T) {
	// In optional mode, a request with no Sarathi headers must pass through.
	m, _, _ := buildTestMiddleware(t, "evaluator-opt", InboundAuthOptional)
	defer m.Close()

	req := httptest.NewRequest(http.MethodPost, "/v1/enforce", bytes.NewReader([]byte(`{"ok":1}`)))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", "k")
	rec := httptest.NewRecorder()
	m.Wrap(http.HandlerFunc(nextOK)).ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("optional passthrough want 200, got %d body=%s", rec.Code, rec.Body.String())
	}
}

func TestInboundAuth_OffReturnsNilMiddleware(t *testing.T) {
	pub, _, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("keygen: %v", err)
	}
	snap := &TrustSnapshotFile{Evaluators: []EvaluatorTrustSnapshot{
		{EvaluatorID: "x", Status: "ACTIVE", PublicKeyHex: hex.EncodeToString(pub)},
	}}
	tc, _ := NewInMemoryTrustConsumer(snap)
	m, err := NewInboundAuthMiddleware(InboundAuthConfig{Mode: InboundAuthOff, Trust: tc})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if m != nil {
		t.Fatalf("mode=off must return nil middleware, got %T", m)
	}
}

func TestParseInboundAuthMode(t *testing.T) {
	cases := []struct {
		in   string
		want InboundAuthMode
	}{
		{"", InboundAuthOff},
		{"off", InboundAuthOff},
		{"OFF", InboundAuthOff},
		{"optional", InboundAuthOptional},
		{"Required", InboundAuthRequired},
		{"garbage", InboundAuthOff},
	}
	for _, c := range cases {
		got := ParseInboundAuthMode(c.in)
		if got != c.want {
			t.Errorf("ParseInboundAuthMode(%q) = %q, want %q", c.in, got, c.want)
		}
	}
}

func TestInboundSigningPayload_Stable(t *testing.T) {
	// Two identical inputs must produce byte-identical payloads so the
	// middleware and CLI agree exactly.
	a := BuildInboundSigningPayload([]byte(`{"a":1}`), "n1", "t1", "i1")
	b := BuildInboundSigningPayload([]byte(`{"a":1}`), "n1", "t1", "i1")
	if !bytes.Equal(a, b) {
		t.Fatalf("signing payload not stable: %q vs %q", a, b)
	}
	// Field separator must be present.
	if !strings.Contains(string(a), string([]byte{sigFieldSep})) {
		t.Fatalf("field separator missing from payload")
	}
}
