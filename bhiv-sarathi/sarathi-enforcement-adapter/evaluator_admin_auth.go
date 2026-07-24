package main

// ═══════════════════════════════════════════════════════════════════
// FROZEN — v12.1 GAP-01 RECTIFICATION
// ═══════════════════════════════════════════════════════════════════
// This file is FROZEN: it compiles but is NOT WIRED into the default
// bootstrap path. Admin auth for evaluator lifecycle belongs to the
// trust-service domain, not the Sarathi enforcement boundary.
// See KB_06 GAP 1.
// ═══════════════════════════════════════════════════════════════════

// evaluator_admin_auth.go — Ed25519 admin authenticator for evaluator
// registry lifecycle operations.
//
// Author: Hemanth B (Phase 12 — External Evaluator Hardening)
// System: Sarathi Governance Kernel — Zero-Trust Verification Boundary
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   The v11 registry took an `initiator string` on Suspend/Revoke/Rotate
//   and only logged it — never verified. Anyone with code or API reach
//   could call RevokeEvaluator("ishan-evaluator-v1", ..., "root") and
//   tear down production trust. This file closes that gap (CRITICAL #C4)
//   with an Ed25519-signed admin request envelope, replay protection,
//   timestamp skew bounds, and per-admin token-bucket rate limiting.
//
// THREAT MODEL:
//   - Stolen request body → mitigated by Ed25519 signature over canonical bytes
//   - Replayed request → mitigated by single-use nonce + timestamp window
//   - Cross-endpoint signature reuse → mitigated by binding op+target into the canonical body
//   - DoS via auth churn → mitigated by per-admin rate limiter and exponential
//     back-off on repeated rejections (matches gated_bridge.go pattern)
//   - Default keys leaked from source → SecureConfig refuses to start in
//     production with default admin keys (governance_hardening.go extension)
//
// DESIGN REFERENCES:
//   - AWS SigV4 (signed request envelope with canonical bytes)
//   - JWT RFC 7519 (jti = nonce, exp = timestamp window)
//   - HashiCorp Vault sudo policies (admin auth on lifecycle ops)
//   - Kubernetes RBAC (admin verb auth on cluster resources)
//   - SPIFFE SPIRE Registration API (mTLS-equivalent identity assertion)

import (
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

// AdminOperation enumerates the lifecycle ops protected by admin auth.
// Binding the operation into the canonical signing payload prevents an
// attacker from re-using a captured SUSPEND signature to issue a REVOKE.
type AdminOperation string

const (
	AdminOpRegisterInit     AdminOperation = "REGISTER_INIT"
	AdminOpRegisterComplete AdminOperation = "REGISTER_COMPLETE"
	AdminOpSuspend          AdminOperation = "SUSPEND"
	AdminOpReactivate       AdminOperation = "REACTIVATE"
	AdminOpRevoke           AdminOperation = "REVOKE"
	AdminOpRotateKey        AdminOperation = "ROTATE_KEY"
	AdminOpList             AdminOperation = "LIST"
	AdminOpGet              AdminOperation = "GET"
)

// AdminRequest is the signed envelope every admin lifecycle call must
// present. The signature covers the canonical bytes — see Canonical().
type AdminRequest struct {
	AdminID   string         `json:"admin_id"`   // logical admin identifier (matches env-loaded key name)
	Operation AdminOperation `json:"operation"`  // bound into canonical bytes — no cross-op reuse
	Target    string         `json:"target"`     // evaluator_id (or empty for LIST)
	Nonce     string         `json:"nonce"`      // single-use UUID, replay-protected
	Timestamp time.Time      `json:"timestamp"`  // wall-clock; checked against skew window
	BodyHash  string         `json:"body_hash"`  // hex SHA-256 over the canonical request body bytes
	Signature []byte         `json:"signature"`  // Ed25519 over Canonical() output
}

// Canonical returns the deterministic byte sequence the signature covers.
// Field order is fixed; any drift produces a different hash and fails Verify.
func (r *AdminRequest) Canonical() []byte {
	// Pipe-separated, fixed order. We do NOT JSON-encode the canonical form
	// because Go map iteration is non-deterministic and we want byte stability
	// across platforms (Windows/POSIX, big/little endian — irrelevant since
	// these are all ASCII strings, but the discipline matters).
	canonical := fmt.Sprintf(
		"v1|%s|%s|%s|%s|%s|%s",
		r.AdminID,
		string(r.Operation),
		r.Target,
		r.Nonce,
		r.Timestamp.UTC().Format(time.RFC3339Nano),
		r.BodyHash,
	)
	return []byte(canonical)
}

// AdminAuthError is the typed error surface so HTTP handlers can map
// reject reasons to 401 / 403 / 410 / 429 without string inspection.
type AdminAuthError struct {
	Code    string // e.g., ADMIN_NONCE_REPLAY
	Message string
}

func (e *AdminAuthError) Error() string { return e.Code + ": " + e.Message }

// Common admin auth error codes — surfaced in the proof logs.
const (
	AdminErrUnknownAdmin     = "ADMIN_UNKNOWN"
	AdminErrSigInvalid       = "ADMIN_SIG_INVALID"
	AdminErrNonceReplay      = "ADMIN_NONCE_REPLAY"
	AdminErrTimestampSkew    = "ADMIN_TIMESTAMP_SKEW"
	AdminErrRateLimited      = "ADMIN_RATE_LIMITED"
	AdminErrOpMismatch       = "ADMIN_OP_MISMATCH"
	AdminErrTargetMismatch   = "ADMIN_TARGET_MISMATCH"
	AdminErrBodyHashMismatch = "ADMIN_BODY_HASH_MISMATCH"
	AdminErrSigEmpty         = "ADMIN_SIG_EMPTY"
)

// adminRateBucket is a token-bucket for per-admin rate limiting. Failed
// authentications drain the bucket faster than successes (exponential
// back-off effect via burstFloor). This mirrors the gated_bridge caller
// rate-limit pattern already used in this repo.
type adminRateBucket struct {
	tokens     float64
	lastRefill time.Time
	failures   int
}

// EvaluatorAdminAuthenticator verifies signed admin requests and enforces
// nonce uniqueness, timestamp freshness, and rate limits. Safe for
// concurrent use.
type EvaluatorAdminAuthenticator struct {
	mu sync.Mutex

	// admin_id → registered Ed25519 public key
	adminKeys map[string]ed25519.PublicKey

	// Replay protection: nonce → first-seen timestamp.
	// Old entries are pruned during Verify based on maxSkew*2.
	seenNonces map[string]time.Time

	// Per-admin rate buckets.
	buckets map[string]*adminRateBucket

	// Configuration.
	maxSkew     time.Duration
	refillRate  float64 // tokens per second
	burstSize   float64
	clock       Clock
}

// NewEvaluatorAdminAuthenticator constructs an authenticator from a map of
// admin_id → hex-encoded Ed25519 public keys. Keys with empty or invalid
// hex are skipped with a warning log; production validation
// (governance_hardening.go) ensures the map is non-empty before reaching
// production boot.
func NewEvaluatorAdminAuthenticator(adminKeysHex map[string]string) *EvaluatorAdminAuthenticator {
	auth := &EvaluatorAdminAuthenticator{
		adminKeys:  make(map[string]ed25519.PublicKey),
		seenNonces: make(map[string]time.Time),
		buckets:    make(map[string]*adminRateBucket),
		maxSkew:    5 * time.Minute,
		refillRate: 5.0,  // 5 ops/second steady-state
		burstSize:  20.0, // 20-op burst
		clock:      RealClock{},
	}
	for adminID, hexKey := range adminKeysHex {
		raw, err := hex.DecodeString(hexKey)
		if err != nil || len(raw) != ed25519.PublicKeySize {
			fmt.Printf("[EvalAdminAuth] WARN: skipping admin '%s' — invalid public key (len=%d, err=%v)\n",
				adminID, len(raw), err)
			continue
		}
		auth.adminKeys[adminID] = ed25519.PublicKey(raw)
	}
	return auth
}

// SetClock injects a test clock. Production uses RealClock.
func (a *EvaluatorAdminAuthenticator) SetClock(c Clock) {
	a.mu.Lock()
	defer a.mu.Unlock()
	if c != nil {
		a.clock = c
	}
}

// AdminCount returns the number of registered admin keys.
func (a *EvaluatorAdminAuthenticator) AdminCount() int {
	a.mu.Lock()
	defer a.mu.Unlock()
	return len(a.adminKeys)
}

// HashRequestBody returns the hex-encoded SHA-256 over the request body.
// HTTP handlers compute this over the raw bytes BEFORE JSON-decoding so
// any whitespace mutation invalidates the signature.
func HashRequestBody(body []byte) string {
	sum := sha256.Sum256(body)
	return hex.EncodeToString(sum[:])
}

// RequireAdminAuth verifies a signed admin request envelope. Returns an
// *AdminAuthError on rejection so callers can map to HTTP status codes.
//
// Verification order (fail-fast):
//  1. Admin known
//  2. Rate limit (drains bucket regardless of outcome)
//  3. Signature non-empty
//  4. Timestamp within ±maxSkew
//  5. Operation matches expected (binding)
//  6. Target matches expected (binding)
//  7. Body hash matches the actual request body (anti-tamper)
//  8. Nonce unseen
//  9. Ed25519 signature valid over Canonical()
//
// On success, the nonce is recorded so a replay of this exact envelope is
// rejected on the next call. Stale nonces are pruned opportunistically.
func (a *EvaluatorAdminAuthenticator) RequireAdminAuth(
	req *AdminRequest,
	expectedOp AdminOperation,
	expectedTarget string,
	rawBody []byte,
) error {
	if req == nil {
		return &AdminAuthError{Code: AdminErrSigEmpty, Message: "nil admin request"}
	}

	a.mu.Lock()
	defer a.mu.Unlock()

	now := time.Now().UTC()
	if a.clock != nil {
		now = a.clock.NowUTC()
	}

	// 1. Admin known
	pubKey, ok := a.adminKeys[req.AdminID]
	if !ok {
		a.touchBucket(req.AdminID, now, false)
		return &AdminAuthError{Code: AdminErrUnknownAdmin, Message: "admin_id=" + req.AdminID}
	}

	// 2. Rate limit
	if !a.consumeToken(req.AdminID, now) {
		return &AdminAuthError{Code: AdminErrRateLimited, Message: "admin_id=" + req.AdminID}
	}

	// 3. Signature presence
	if len(req.Signature) == 0 {
		a.touchBucket(req.AdminID, now, false)
		return &AdminAuthError{Code: AdminErrSigEmpty, Message: "admin signature is empty"}
	}

	// 4. Timestamp window
	delta := now.Sub(req.Timestamp.UTC())
	if delta < 0 {
		delta = -delta
	}
	if delta > a.maxSkew {
		a.touchBucket(req.AdminID, now, false)
		return &AdminAuthError{
			Code:    AdminErrTimestampSkew,
			Message: fmt.Sprintf("delta=%s max_skew=%s", delta, a.maxSkew),
		}
	}

	// 5. Operation binding
	if req.Operation != expectedOp {
		a.touchBucket(req.AdminID, now, false)
		return &AdminAuthError{
			Code:    AdminErrOpMismatch,
			Message: fmt.Sprintf("got=%s want=%s", req.Operation, expectedOp),
		}
	}

	// 6. Target binding (only enforced if expected non-empty)
	if expectedTarget != "" && req.Target != expectedTarget {
		a.touchBucket(req.AdminID, now, false)
		return &AdminAuthError{
			Code:    AdminErrTargetMismatch,
			Message: fmt.Sprintf("got=%s want=%s", req.Target, expectedTarget),
		}
	}

	// 7. Body hash anti-tamper
	if rawBody != nil {
		actual := HashRequestBody(rawBody)
		if actual != req.BodyHash {
			a.touchBucket(req.AdminID, now, false)
			return &AdminAuthError{
				Code:    AdminErrBodyHashMismatch,
				Message: fmt.Sprintf("got=%s want=%s", actual, req.BodyHash),
			}
		}
	}

	// 8. Nonce replay check
	if req.Nonce == "" {
		a.touchBucket(req.AdminID, now, false)
		return &AdminAuthError{Code: AdminErrNonceReplay, Message: "nonce is empty"}
	}
	if seenAt, replay := a.seenNonces[req.Nonce]; replay {
		a.touchBucket(req.AdminID, now, false)
		return &AdminAuthError{
			Code:    AdminErrNonceReplay,
			Message: fmt.Sprintf("nonce=%s first_seen=%s", req.Nonce, seenAt.Format(time.RFC3339)),
		}
	}

	// 9. Ed25519 verify over canonical bytes
	if !ed25519.Verify(pubKey, req.Canonical(), req.Signature) {
		a.touchBucket(req.AdminID, now, false)
		return &AdminAuthError{
			Code:    AdminErrSigInvalid,
			Message: fmt.Sprintf("admin_id=%s op=%s target=%s", req.AdminID, req.Operation, req.Target),
		}
	}

	// Success: record the nonce, refill the bucket, prune old nonces.
	a.seenNonces[req.Nonce] = now
	a.touchBucket(req.AdminID, now, true)
	a.pruneNoncesLocked(now)
	return nil
}

// pruneNoncesLocked removes nonces older than 2*maxSkew. Callers must hold
// the mutex. Pruning is opportunistic (called from RequireAdminAuth).
func (a *EvaluatorAdminAuthenticator) pruneNoncesLocked(now time.Time) {
	cutoff := now.Add(-2 * a.maxSkew)
	for n, seenAt := range a.seenNonces {
		if seenAt.Before(cutoff) {
			delete(a.seenNonces, n)
		}
	}
}

// consumeToken tries to remove one token from the admin's bucket.
// Returns false if the bucket is empty (rate-limited).
func (a *EvaluatorAdminAuthenticator) consumeToken(adminID string, now time.Time) bool {
	bucket, ok := a.buckets[adminID]
	if !ok {
		bucket = &adminRateBucket{tokens: a.burstSize, lastRefill: now}
		a.buckets[adminID] = bucket
	}
	// Refill based on elapsed time
	elapsed := now.Sub(bucket.lastRefill).Seconds()
	if elapsed > 0 {
		bucket.tokens += elapsed * a.refillRate
		if bucket.tokens > a.burstSize {
			bucket.tokens = a.burstSize
		}
		bucket.lastRefill = now
	}
	if bucket.tokens < 1.0 {
		return false
	}
	bucket.tokens -= 1.0
	return true
}

// touchBucket records success/failure for back-off accounting. Failures
// drain an extra token to discourage credential-stuffing.
func (a *EvaluatorAdminAuthenticator) touchBucket(adminID string, now time.Time, success bool) {
	bucket, ok := a.buckets[adminID]
	if !ok {
		bucket = &adminRateBucket{tokens: a.burstSize, lastRefill: now}
		a.buckets[adminID] = bucket
	}
	if success {
		bucket.failures = 0
		return
	}
	bucket.failures++
	// Exponential drain: each consecutive failure drains an extra token,
	// capped so a sustained attacker can't underflow the bucket.
	drain := float64(bucket.failures)
	if drain > 8.0 {
		drain = 8.0
	}
	bucket.tokens -= drain
	if bucket.tokens < 0 {
		bucket.tokens = 0
	}
}

// SignAdminRequest is a test/CLI helper that builds a signed admin request
// envelope from a private key. Production admin clients should implement
// this themselves so private keys never live inside the Sarathi binary.
func SignAdminRequest(
	adminID string,
	op AdminOperation,
	target string,
	body []byte,
	priv ed25519.PrivateKey,
	clock Clock,
) (*AdminRequest, error) {
	if len(priv) != ed25519.PrivateKeySize {
		return nil, fmt.Errorf("invalid admin private key size")
	}
	now := time.Now().UTC()
	if clock != nil {
		now = clock.NowUTC()
	}
	req := &AdminRequest{
		AdminID:   adminID,
		Operation: op,
		Target:    target,
		Nonce:     newAdminNonce(),
		Timestamp: now,
		BodyHash:  HashRequestBody(body),
	}
	sig := ed25519.Sign(priv, req.Canonical())
	req.Signature = sig
	return req, nil
}

// newAdminNonce returns a 128-bit random hex string. Uses the same uuid
// dependency the rest of the codebase uses (already imported indirectly
// via external_decision.go).
func newAdminNonce() string {
	// Reuse the package-local random by piggybacking on Go's crypto/rand
	// indirectly: SHA-256 of (now-nanos || pid-ish) would also work, but
	// the rest of the codebase uses uuid.New() so we match for consistency.
	return uuidNewString()
}

// uuidNewString is a thin shim so we don't need to import uuid in this file.
// The shim resolves to github.com/google/uuid via external_decision.go which
// already imports it. We declare a local helper to keep imports tidy.
func uuidNewString() string {
	// Defer to a helper defined in evaluator_registration_challenge.go to
	// avoid duplicate uuid imports across phase-12 files.
	return generatePhase12UUID()
}

// MarshalAdminRequest is a convenience wrapper used by HTTP clients/tests.
func MarshalAdminRequest(req *AdminRequest) ([]byte, error) {
	return json.Marshal(req)
}

// UnmarshalAdminRequest parses an admin request envelope.
func UnmarshalAdminRequest(data []byte) (*AdminRequest, error) {
	var req AdminRequest
	if err := json.Unmarshal(data, &req); err != nil {
		return nil, fmt.Errorf("ADMIN_REQUEST_DECODE: %w", err)
	}
	return &req, nil
}
