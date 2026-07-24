package main

// service_inbound_auth.go — v15.0 Sovereign Identity Closure.
//
// BOUNDARY MIDDLEWARE for inbound caller identity. This file CLOSES the
// last-remaining "only-API-key" gap at POST /v1/enforce by requiring callers
// to present a registered Ed25519 evaluator identity before the request is
// forwarded to the Gated Bridge.
//
// WIRE CONTRACT (active only when SARATHI_INBOUND_AUTH != "off"):
//
//   X-API-Key                <rate-limit scope key>                      always required
//   X-Sarathi-Issuer-Id      <registered evaluator id>                   required in {optional*, required}
//   X-Sarathi-Request-Nonce  <RFC 4122 UUID v4 or equivalent 128-bit>    required in {optional*, required}
//   X-Sarathi-Timestamp      <RFC 3339 UTC, within ±SARATHI_REQUEST_SKEW_S>
//   X-Sarathi-Body-Signature <base64 Ed25519 sig over signing payload>
//   X-Sarathi-Sig-Algorithm  ed25519
//
//   * In "optional" mode, the five Sarathi-specific headers are validated
//     only if any is present; if all are absent the request falls through
//     to the legacy API-key path (Stage B migration aid).
//
// SIGNING PAYLOAD (different from deep-pipeline decision_core_hash):
//
//   msg = canonical(body_json) || 0x1E || nonce || 0x1E || timestamp || 0x1E || issuer_id
//
//   0x1E is the ASCII record separator. Using an RS byte between fields
//   prevents ambiguity that a pure concatenation would allow.
//
// MODES:
//
//   SARATHI_INBOUND_AUTH=off        middleware NOT mounted (default, v14.9 identical)
//   SARATHI_INBOUND_AUTH=optional   mounted, headers validated only if present
//   SARATHI_INBOUND_AUTH=required   mounted, headers mandatory, fail-closed
//
// REJECTION PATHS (all append a row to proof_logs/inbound_auth_rejections.jsonl):
//
//   ERR_INBOUND_SIGNATURE_MISSING   400  — required headers absent in `required` mode
//   ERR_INBOUND_TIMESTAMP_SKEWED    401  — outside ±SARATHI_REQUEST_SKEW_S
//   ERR_INBOUND_NONCE_REPLAY        409  — seen within SARATHI_NONCE_WINDOW_S
//   ERR_EVALUATOR_NOT_REGISTERED    403  — issuer_id not in TrustConsumer
//   ERR_EVALUATOR_SUSPENDED         403  — issuer_id SUSPENDED
//   ERR_EVALUATOR_REVOKED           403  — issuer_id REVOKED
//   ERR_INBOUND_SIGNATURE_INVALID   401  — Ed25519 verify failed
//
// This middleware runs BEFORE the legacy API-key check — it is an additional
// gate, not a replacement. After it passes, the request body is restored so
// the existing handleEnforce code path continues unchanged.

import (
	"bytes"
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// ============================================================================
// MODE
// ============================================================================

type InboundAuthMode string

const (
	InboundAuthOff      InboundAuthMode = "off"
	InboundAuthOptional InboundAuthMode = "optional"
	InboundAuthRequired InboundAuthMode = "required"
)

// ParseInboundAuthMode reads SARATHI_INBOUND_AUTH. Unknown values default to
// "off" with a stderr warning so a typo cannot silently weaken the gate.
func ParseInboundAuthMode(raw string) InboundAuthMode {
	switch strings.ToLower(strings.TrimSpace(raw)) {
	case "", "off":
		return InboundAuthOff
	case "optional":
		return InboundAuthOptional
	case "required":
		return InboundAuthRequired
	default:
		fmt.Fprintf(os.Stderr, "[InboundAuth] WARN: unknown SARATHI_INBOUND_AUTH=%q, defaulting to off\n", raw)
		return InboundAuthOff
	}
}

// ============================================================================
// HEADERS
// ============================================================================

const (
	HeaderSarathiIssuerID      = "X-Sarathi-Issuer-Id"
	HeaderSarathiRequestNonce  = "X-Sarathi-Request-Nonce"
	HeaderSarathiTimestamp     = "X-Sarathi-Timestamp"
	HeaderSarathiBodySignature = "X-Sarathi-Body-Signature"
	HeaderSarathiSigAlgorithm  = "X-Sarathi-Sig-Algorithm"
)

// ASCII record separator; see signing payload above.
const sigFieldSep byte = 0x1E

// ============================================================================
// CONFIG
// ============================================================================

// InboundAuthConfig bundles the knobs the middleware needs at construction.
// Zero values resolve to production-grade defaults.
type InboundAuthConfig struct {
	Mode          InboundAuthMode
	Trust         TrustConsumer
	MaxSkew       time.Duration // default 300s (5 min)
	NonceCapacity int           // default 100000
	NonceWindow   time.Duration // default 900s (15 min)
	NonceOverflow string        // default "live/inbound_nonces.jsonl" (set "" to disable)
	RejectLog     string        // default "proof_logs/inbound_auth_rejections.jsonl"
	Clock         Clock

	// v15.1 Network Surface Closure: list of POST paths whose Ed25519
	// signature is verified. Default covers /v1/enforce (v15.0 surface) AND
	// /v1/ingest-decision (v15.1 external-decision surface). Operators may
	// add custom POST endpoints here to extend Stage C protection without
	// editing the middleware. Comparison is case-sensitive exact match.
	ProtectedPaths []string
}

// DefaultInboundAuthConfig pulls every knob from the environment.
func DefaultInboundAuthConfig(trust TrustConsumer) InboundAuthConfig {
	return InboundAuthConfig{
		Mode:           ParseInboundAuthMode(os.Getenv("SARATHI_INBOUND_AUTH")),
		Trust:          trust,
		MaxSkew:        parseDurationSeconds(os.Getenv("SARATHI_REQUEST_SKEW_S"), 300*time.Second),
		NonceCapacity:  parseIntEnvDefault("SARATHI_NONCE_LRU_SIZE", 100_000),
		NonceWindow:    parseDurationSeconds(os.Getenv("SARATHI_NONCE_WINDOW_S"), 15*time.Minute),
		NonceOverflow:  envDefault("SARATHI_NONCE_OVERFLOW_PATH", "live/inbound_nonces.jsonl"),
		RejectLog:      envDefault("SARATHI_INBOUND_REJECT_LOG", "proof_logs/inbound_auth_rejections.jsonl"),
		ProtectedPaths: []string{"/v1/enforce", "/v1/ingest-decision", "/sarathi/enforce"},
	}
}

func parseDurationSeconds(raw string, def time.Duration) time.Duration {
	if raw == "" {
		return def
	}
	v := parseIntEnvDefault("__NEVER_REAL_ENV__", 0)
	_ = v // silence linter via helper fallback
	if secs, err := parseFloat(raw); err == nil && secs > 0 {
		return time.Duration(secs * float64(time.Second))
	}
	return def
}

func parseFloat(s string) (float64, error) {
	var f float64
	_, err := fmt.Sscanf(strings.TrimSpace(s), "%f", &f)
	return f, err
}

func parseIntEnvDefault(key string, def int) int {
	raw := os.Getenv(key)
	if raw == "" {
		return def
	}
	var v int
	_, err := fmt.Sscanf(strings.TrimSpace(raw), "%d", &v)
	if err != nil || v <= 0 {
		return def
	}
	return v
}

func envDefault(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

// ============================================================================
// MIDDLEWARE
// ============================================================================

// InboundAuthMiddleware verifies caller identity on /v1/enforce.
type InboundAuthMiddleware struct {
	cfg      InboundAuthConfig
	nonces   *InboundNonceStore
	rejectMu sync.Mutex
	rejectFh *os.File
	clock    Clock
}

// NewInboundAuthMiddleware constructs the middleware. Returns a nil middleware
// when cfg.Mode == off so callers can conditionally skip Wrap().
func NewInboundAuthMiddleware(cfg InboundAuthConfig) (*InboundAuthMiddleware, error) {
	if cfg.Mode == InboundAuthOff {
		return nil, nil
	}
	if cfg.Trust == nil {
		return nil, fmt.Errorf("inbound auth requires a non-nil TrustConsumer")
	}
	if cfg.MaxSkew <= 0 {
		cfg.MaxSkew = 5 * time.Minute
	}
	if cfg.NonceWindow <= 0 {
		cfg.NonceWindow = 15 * time.Minute
	}
	if cfg.NonceCapacity <= 0 {
		cfg.NonceCapacity = 100_000
	}
	// v15.1: backward-compat default. Callers constructing InboundAuthConfig
	// directly (older tests / external integrators) get the v15.0 surface
	// PLUS the new /v1/ingest-decision path. Callers using
	// DefaultInboundAuthConfig already see this list explicitly.
	if len(cfg.ProtectedPaths) == 0 {
		cfg.ProtectedPaths = []string{"/v1/enforce", "/v1/ingest-decision", "/sarathi/enforce"}
	}
	store, err := NewInboundNonceStore(cfg.NonceCapacity, cfg.NonceWindow, cfg.NonceOverflow)
	if err != nil {
		return nil, fmt.Errorf("inbound nonce store: %w", err)
	}
	clk := cfg.Clock
	if clk == nil {
		clk = RealClock{}
	}
	store.SetClock(clk)

	var rejectFh *os.File
	if cfg.RejectLog != "" {
		if dir := filepath.Dir(cfg.RejectLog); dir != "" && dir != "." {
			if err := os.MkdirAll(dir, 0o755); err != nil {
				return nil, fmt.Errorf("inbound reject-log dir: %w", err)
			}
		}
		f, err := os.OpenFile(cfg.RejectLog, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
		if err != nil {
			return nil, fmt.Errorf("inbound reject-log: %w", err)
		}
		rejectFh = f
	}

	return &InboundAuthMiddleware{
		cfg:      cfg,
		nonces:   store,
		rejectFh: rejectFh,
		clock:    clk,
	}, nil
}

// Close flushes and closes any open files. Safe to call multiple times.
func (m *InboundAuthMiddleware) Close() error {
	if m == nil {
		return nil
	}
	var firstErr error
	if m.nonces != nil {
		if err := m.nonces.Close(); err != nil {
			firstErr = err
		}
	}
	m.rejectMu.Lock()
	defer m.rejectMu.Unlock()
	if m.rejectFh != nil {
		_ = m.rejectFh.Sync()
		if err := m.rejectFh.Close(); err != nil && firstErr == nil {
			firstErr = err
		}
		m.rejectFh = nil
	}
	return firstErr
}

// Mode returns the configured mode (for banner/logging).
func (m *InboundAuthMiddleware) Mode() InboundAuthMode {
	if m == nil {
		return InboundAuthOff
	}
	return m.cfg.Mode
}

// Wrap returns a handler that runs the boundary auth check before `next`.
// In "optional" mode, if no Sarathi headers are present the request passes
// through untouched; if any are present, all are required and validated.
//
// The middleware preserves the body bytes so handleEnforce can decode them
// normally.
func (m *InboundAuthMiddleware) Wrap(next http.Handler) http.Handler {
	if m == nil || m.cfg.Mode == InboundAuthOff {
		return next
	}
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// v15.1: protected POST paths come from cfg.ProtectedPaths so the
		// /v1/ingest-decision surface added by Network Surface Closure is
		// signature-verified the same way /v1/enforce is. Other paths
		// (health, metrics, admin) are protected by their own
		// authenticators and are intentionally not in the list.
		if r.Method != http.MethodPost || !pathInList(r.URL.Path, m.cfg.ProtectedPaths) {
			next.ServeHTTP(w, r)
			return
		}
		if err := m.authenticate(w, r); err != nil {
			return // authenticate already wrote the response
		}
		next.ServeHTTP(w, r)
	})
}

// pathInList reports whether `target` matches any entry in `paths` exactly.
// Used by the inbound-auth middleware to decide whether a POST path is in
// the v15.1 protected-path allowlist.
func pathInList(target string, paths []string) bool {
	for _, p := range paths {
		if p == target {
			return true
		}
	}
	return false
}

// authenticate runs the 7-step verification. On rejection it writes the HTTP
// response and returns a non-nil error; on success it returns nil and leaves
// r.Body positioned at the start of the preserved bytes.
func (m *InboundAuthMiddleware) authenticate(w http.ResponseWriter, r *http.Request) error {
	issuerID := r.Header.Get(HeaderSarathiIssuerID)
	nonce := r.Header.Get(HeaderSarathiRequestNonce)
	tsRaw := r.Header.Get(HeaderSarathiTimestamp)
	sigB64 := r.Header.Get(HeaderSarathiBodySignature)
	algo := r.Header.Get(HeaderSarathiSigAlgorithm)

	anyPresent := issuerID != "" || nonce != "" || tsRaw != "" || sigB64 != "" || algo != ""

	if m.cfg.Mode == InboundAuthOptional && !anyPresent {
		// Stage-B passthrough: no Sarathi headers → legacy API-key path.
		return nil
	}

	// Step 1: all five headers present.
	if issuerID == "" || nonce == "" || tsRaw == "" || sigB64 == "" || algo == "" {
		m.rejectAndLog(w, r, "", CodeInboundSignatureMissing,
			"one or more X-Sarathi-* headers missing", http.StatusBadRequest, nonce, tsRaw)
		return fmt.Errorf("headers missing")
	}
	if !strings.EqualFold(algo, "ed25519") {
		m.rejectAndLog(w, r, issuerID, CodeInboundSignatureInvalid,
			fmt.Sprintf("unsupported signature algorithm %q", algo),
			http.StatusUnauthorized, nonce, tsRaw)
		return fmt.Errorf("bad algo")
	}

	// Step 2: timestamp skew.
	ts, err := time.Parse(time.RFC3339, tsRaw)
	if err != nil {
		// Try RFC3339Nano as a convenience fallback.
		if t2, err2 := time.Parse(time.RFC3339Nano, tsRaw); err2 == nil {
			ts = t2
		} else {
			m.rejectAndLog(w, r, issuerID, CodeInboundTimestampSkewed,
				fmt.Sprintf("timestamp parse failed: %v", err),
				http.StatusUnauthorized, nonce, tsRaw)
			return err
		}
	}
	now := m.clock.NowUTC()
	delta := now.Sub(ts.UTC())
	if delta < 0 {
		delta = -delta
	}
	if delta > m.cfg.MaxSkew {
		m.rejectAndLog(w, r, issuerID, CodeInboundTimestampSkewed,
			fmt.Sprintf("delta=%s max=%s", delta, m.cfg.MaxSkew),
			http.StatusUnauthorized, nonce, tsRaw)
		return fmt.Errorf("timestamp skew")
	}

	// Step 3: body read + canonicalise. We buffer the raw bytes so both the
	// signature verification and the downstream JSON decoder see identical
	// input. We canonicalise to ensure caller-side whitespace/order does not
	// break verification.
	r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
	rawBody, err := io.ReadAll(r.Body)
	if err != nil {
		m.rejectAndLog(w, r, issuerID, CodeInboundSignatureInvalid,
			fmt.Sprintf("body read failed: %v", err),
			http.StatusBadRequest, nonce, tsRaw)
		return err
	}
	// Restore body for the next handler.
	r.Body = io.NopCloser(bytes.NewReader(rawBody))

	canonical, cerr := CanonicalMarshalBytes(rawBody)
	if cerr != nil {
		m.rejectAndLog(w, r, issuerID, CodeInboundSignatureInvalid,
			fmt.Sprintf("canonicalise failed: %v", cerr),
			http.StatusBadRequest, nonce, tsRaw)
		return cerr
	}

	// Step 4: nonce replay — done BEFORE registry/sig so an attacker cannot
	// mine the cache via signature failures.
	if seen, firstAt := m.nonces.Seen(nonce, issuerID); seen {
		m.rejectAndLog(w, r, issuerID, CodeInboundNonceReplay,
			fmt.Sprintf("nonce=%s first_seen=%s", nonce, firstAt.Format(time.RFC3339)),
			http.StatusConflict, nonce, tsRaw)
		return fmt.Errorf("nonce replay")
	}

	// Step 5: registry lookup.
	record, terr := m.cfg.Trust.GetActiveEvaluator(issuerID)
	if terr != nil {
		code := CodeEvaluatorNotRegistered
		status := http.StatusForbidden
		switch {
		case strings.Contains(terr.Error(), "EVALUATOR_SUSPENDED"):
			code = CodeEvaluatorSuspended
		case strings.Contains(terr.Error(), "EVALUATOR_REVOKED"):
			code = CodeEvaluatorRevoked
		}
		m.rejectAndLog(w, r, issuerID, code, terr.Error(), status, nonce, tsRaw)
		return terr
	}

	// Step 6: Ed25519 verify over the signing payload.
	sigBytes, err := base64.StdEncoding.DecodeString(sigB64)
	if err != nil || len(sigBytes) != ed25519.SignatureSize {
		m.rejectAndLog(w, r, issuerID, CodeInboundSignatureInvalid,
			fmt.Sprintf("signature decode failed (size=%d, err=%v)", len(sigBytes), err),
			http.StatusUnauthorized, nonce, tsRaw)
		return fmt.Errorf("sig decode")
	}
	payload := buildInboundSigningPayload(canonical, nonce, tsRaw, issuerID)
	if !ed25519.Verify(record.PublicKey, payload, sigBytes) {
		m.rejectAndLog(w, r, issuerID, CodeInboundSignatureInvalid,
			"ed25519 verify failed",
			http.StatusUnauthorized, nonce, tsRaw)
		return fmt.Errorf("sig invalid")
	}

	// Success: expose the issuer on a response header so downstream logs
	// can correlate without parsing the request body a second time.
	w.Header().Set("X-Sarathi-Verified-Issuer", issuerID)
	return nil
}

// buildInboundSigningPayload concatenates the signing fields with an ASCII
// record separator so the caller and server agree byte-for-byte.
func buildInboundSigningPayload(canonicalBody []byte, nonce, timestamp, issuerID string) []byte {
	buf := bytes.NewBuffer(make([]byte, 0, len(canonicalBody)+len(nonce)+len(timestamp)+len(issuerID)+3))
	buf.Write(canonicalBody)
	buf.WriteByte(sigFieldSep)
	buf.WriteString(nonce)
	buf.WriteByte(sigFieldSep)
	buf.WriteString(timestamp)
	buf.WriteByte(sigFieldSep)
	buf.WriteString(issuerID)
	return buf.Bytes()
}

// BuildInboundSigningPayload is the exported helper used by the signing CLI.
func BuildInboundSigningPayload(canonicalBody []byte, nonce, timestamp, issuerID string) []byte {
	return buildInboundSigningPayload(canonicalBody, nonce, timestamp, issuerID)
}

// rejectAndLog writes a JSON error body AND appends a row to the reject log.
func (m *InboundAuthMiddleware) rejectAndLog(
	w http.ResponseWriter, r *http.Request,
	issuerID, code, detail string, status int,
	nonce, timestamp string,
) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{
		"error":     code,
		"detail":    detail,
		"issuer_id": issuerID,
	})

	if m.rejectFh == nil {
		return
	}
	row := map[string]interface{}{
		"ts":          m.clock.NowUTC().Format(time.RFC3339Nano),
		"remote_ip":   remoteIPOnly(r.RemoteAddr),
		"issuer_id":   issuerID,
		"reason":      code,
		"detail":      detail,
		"nonce":       nonce,
		"timestamp":   timestamp,
		"http_status": status,
	}
	line, err := json.Marshal(row)
	if err != nil {
		return
	}
	line = append(line, '\n')
	m.rejectMu.Lock()
	defer m.rejectMu.Unlock()
	if _, werr := m.rejectFh.Write(line); werr == nil {
		_ = m.rejectFh.Sync()
	}
}

func remoteIPOnly(addr string) string {
	if idx := strings.LastIndex(addr, ":"); idx > 0 {
		return addr[:idx]
	}
	return addr
}
