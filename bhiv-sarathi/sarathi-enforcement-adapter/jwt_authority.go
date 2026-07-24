package main

// jwt_authority.go — v15.6 External JWT Authority Layer.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Outbound Token Authority
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   Today Sarathi mints Ed25519 capability tokens internally (capability_token.go)
//   but the token is a Go struct held in process memory — it never serializes
//   onto the wire. External verifiers like the BHIV Bridge cannot consume it.
//
//   This file adds a PARALLEL outbound JWT authority layer:
//     * Same Ed25519 cryptography (RFC 8032 / RFC 8037)
//     * Compact JWT wire format (RFC 7519 / 7515) so any standard verifier works
//     * Persistent signing key with grace-period rotation (Auth0 / AWS Cognito
//       pattern — old private key is destroyed immediately, only public stays
//       in JWKS for verification of outstanding tokens)
//     * RFC 7638 thumbprint as the kid
//     * Pluggable Signer interface so a future HSM/KMS implementation drops in
//       without touching the mint code
//
// COEXISTENCE WITH EXISTING CRYPTO:
//   * capability_token.go::TokenAuthority remains unchanged. Its in-process
//     gate is still load-bearing for ExecutionEngine.ExecuteWithToken.
//   * service_inbound_auth.go inbound Ed25519 (caller -> Sarathi) is unchanged.
//   * propagation_envelope.go receipt signatures (peer ack gate) are unchanged.
//   * The new JWT layer ONLY mints outbound, externally-verifiable tokens.
//
// SECURITY POSTURE:
//   * alg pinning to "EdDSA" (RFC 8725 §3.1). alg=none is rejected by the
//     parser via jwt.WithValidMethods.
//   * kid derived from RFC 7638 thumbprint over the canonical JWK {crv,kty,x}.
//     A Bridge can independently recompute the kid from the public bytes and
//     cross-check the JWKS.
//   * Rotation drops the old private key from disk immediately; the old
//     public stays in JWKS as source="grace-period" until grace_expires.
//   * Private key file refuses to load with non-0600 permissions on POSIX.
//   * Production boot gates (in service_runtime_cli.go) refuse to start with
//     ephemeral keys.
//
// TAG: jwt-authority-v15.6

import (
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"sync"
	"time"
)

// JWTAuthoritySchemaVersion pins the wire schema of every artefact this layer
// emits (JWKS, discovery, introspection, audit log). Tied to KB_16.
const JWTAuthoritySchemaVersion = "sarathi.jwt-authority/v15.6"

// JWTCapabilityTokenSchema is the schema-version private claim placed inside
// every minted JWT so Bridge can pin behaviour to a stable mint contract.
const JWTCapabilityTokenSchema = "sarathi.capability-jwt/v1.0"

// DefaultJWTAuthorityKeysDir is the conventional disk layout under live/.
// Overridable via env (SARATHI_JWT_AUTHORITY_KEYS_DIR) or the explicit
// SARATHI_JWT_AUTHORITY_PRIV_PATH (which wins over both).
const DefaultJWTAuthorityKeysDir = "live/keys/jwt_authority"

// Environment knobs (mirrored in ecosystem_endpoints.go for discoverability).
const (
	EnvJWTAuthorityKeysDir         = "SARATHI_JWT_AUTHORITY_KEYS_DIR"
	EnvJWTAuthorityPrivPath        = "SARATHI_JWT_AUTHORITY_PRIV_PATH"
	EnvJWTAuthorityPubPath         = "SARATHI_JWT_AUTHORITY_PUB_PATH"
	EnvJWTAuthorityKid             = "SARATHI_JWT_AUTHORITY_KID"
	EnvTokenIssuer                 = "SARATHI_TOKEN_ISSUER"
	EnvTokenAudience               = "SARATHI_TOKEN_AUDIENCE"
	EnvJWTTokenTTLSeconds          = "SARATHI_JWT_TOKEN_TTL_S"
	EnvJWTIntrospectionAPIKey      = "SARATHI_JWT_INTROSPECTION_API_KEY"
	EnvJWTAuthorityIssuanceLog     = "SARATHI_JWT_ISSUANCE_LOG"
)

// DefaultJWTTokenTTL caps every minted JWT at this lifetime (mirrors the
// existing MaxTokenTTL from capability_token.go). Operators may shrink via
// SARATHI_JWT_TOKEN_TTL_S; values larger than the existing capability-token
// TTL are clamped to 60s.
const DefaultJWTTokenTTL = 60 * time.Second

// DefaultJWTIssuer is a fail-loud placeholder. The operator MUST set
// SARATHI_TOKEN_ISSUER; production gates refuse to start without it.
const DefaultJWTIssuer = "https://sarathi.bhiv.local/authority"

// DefaultJWTAudience is the suggested audience for BHIV Core when no env is
// set. Bridge SHOULD verify aud matches what it expects per deployment.
const DefaultJWTAudience = "bhiv-core-runtime"

// DefaultJWTIssuanceLog is the append-only audit trail of mints. Each row is
// a single JSON object on its own line (JSONL).
const DefaultJWTIssuanceLog = "proof_logs/jwt_issuance.jsonl"

// ============================================================================
// SIGNER INTERFACE (HSM/KMS ready)
// ============================================================================

// Signer abstracts the bytes-in / signature-out primitive. A LocalEd25519Signer
// is the only implementation shipped in v15.6; future KMSSigner / VaultSigner
// drop in without touching the JWT mint path because nothing else reaches into
// the private key.
//
// The interface deliberately exposes the kid and the public key — they are
// constant for the lifetime of a Signer and are needed by JWKS publication
// and by parsers consulting the kid header.
type Signer interface {
	// Sign returns the 64-byte Ed25519 signature over message.
	Sign(message []byte) ([]byte, error)
	// PublicKey returns the Ed25519 public key for verification + JWKS.
	PublicKey() ed25519.PublicKey
	// Kid returns the RFC 7638 thumbprint of the public key, hex-encoded.
	Kid() string
	// CreatedAt is the wall-clock time the key was generated. Used by JWKS
	// `iat` and by operator banners.
	CreatedAt() time.Time
}

// LocalEd25519Signer holds the private key in memory. Construction is the only
// path that touches the private bytes; rotation re-constructs a brand new
// signer and discards the old one (Go GC handles the wipe; for HSM-class
// erasure use a KMSSigner).
type LocalEd25519Signer struct {
	priv      ed25519.PrivateKey
	pub       ed25519.PublicKey
	kid       string
	createdAt time.Time
}

// NewLocalEd25519Signer wraps an existing keypair. The kid is computed via
// RFC 7638 from the public bytes — deterministic, length-checked, hex-encoded.
func NewLocalEd25519Signer(priv ed25519.PrivateKey, pub ed25519.PublicKey, createdAt time.Time) (*LocalEd25519Signer, error) {
	if len(priv) != ed25519.PrivateKeySize {
		return nil, fmt.Errorf("jwt_authority: priv key length=%d want=%d", len(priv), ed25519.PrivateKeySize)
	}
	if len(pub) != ed25519.PublicKeySize {
		return nil, fmt.Errorf("jwt_authority: pub key length=%d want=%d", len(pub), ed25519.PublicKeySize)
	}
	kid, err := ComputeRFC7638Thumbprint(pub)
	if err != nil {
		return nil, fmt.Errorf("jwt_authority: thumbprint: %w", err)
	}
	if createdAt.IsZero() {
		createdAt = time.Now().UTC()
	}
	return &LocalEd25519Signer{priv: priv, pub: pub, kid: kid, createdAt: createdAt.UTC()}, nil
}

// GenerateLocalEd25519Signer creates a fresh keypair using crypto/rand.
// Used by --bootstrap-jwt-authority and by tests.
func GenerateLocalEd25519Signer() (*LocalEd25519Signer, error) {
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return nil, fmt.Errorf("jwt_authority: keygen: %w", err)
	}
	return NewLocalEd25519Signer(priv, pub, time.Now().UTC())
}

// Sign implements Signer.
func (s *LocalEd25519Signer) Sign(message []byte) ([]byte, error) {
	if s == nil || len(s.priv) != ed25519.PrivateKeySize {
		return nil, fmt.Errorf("jwt_authority: signer not initialized")
	}
	return ed25519.Sign(s.priv, message), nil
}

// PublicKey implements Signer.
func (s *LocalEd25519Signer) PublicKey() ed25519.PublicKey {
	if s == nil {
		return nil
	}
	return s.pub
}

// Kid implements Signer.
func (s *LocalEd25519Signer) Kid() string {
	if s == nil {
		return ""
	}
	return s.kid
}

// CreatedAt implements Signer.
func (s *LocalEd25519Signer) CreatedAt() time.Time {
	if s == nil {
		return time.Time{}
	}
	return s.createdAt
}

// PrivateKey returns the raw 64-byte Ed25519 private. ONLY used by the
// rotation CLI when it has to overwrite the on-disk file; production code
// should never call this.
func (s *LocalEd25519Signer) PrivateKey() ed25519.PrivateKey {
	if s == nil {
		return nil
	}
	return s.priv
}

// ============================================================================
// RFC 7638 JWK THUMBPRINT
// ============================================================================

// ComputeRFC7638Thumbprint returns hex(SHA-256(canonical JWK members)) for an
// Ed25519 public key. The canonical JWK for an OKP/Ed25519 key has exactly
// three members in lexicographic order: crv, kty, x.
//
// Spec: RFC 7638 §3 — JSON Web Key (JWK) Thumbprint.
// Note: hex (not base64url) is used so the kid is human-printable and matches
// the existing fingerprint conventions in evaluator_registry_store.go.
func ComputeRFC7638Thumbprint(pub ed25519.PublicKey) (string, error) {
	if len(pub) != ed25519.PublicKeySize {
		return "", fmt.Errorf("RFC7638: pub key length=%d want=%d", len(pub), ed25519.PublicKeySize)
	}
	// Canonical members in lexicographic order: "crv", "kty", "x".
	// Member values are quoted JSON strings per RFC 7638 §3.2.
	canonical := fmt.Sprintf(
		`{"crv":"Ed25519","kty":"OKP","x":"%s"}`,
		base64UrlEncode(pub),
	)
	sum := sha256.Sum256([]byte(canonical))
	return hex.EncodeToString(sum[:]), nil
}

// ============================================================================
// GRACE-PERIOD KEY ENTRY
// ============================================================================

// graceKey holds a previously-active public key that is still publishable in
// the JWKS for verifying outstanding tokens. The private bytes are NOT held.
type graceKey struct {
	Kid          string
	Pub          ed25519.PublicKey
	CreatedAt    time.Time
	GraceExpires time.Time
}

// IsExpired reports whether the grace window has elapsed (with a 1s margin).
func (g *graceKey) IsExpired(now time.Time) bool {
	return now.After(g.GraceExpires.Add(time.Second))
}

// ============================================================================
// JWTAuthority — the top-level signer registry
// ============================================================================

// JWTAuthority is the single source of truth for JWT signing and JWKS
// publication. It is constructed once at service boot, attached to the
// ServiceBoundary, and read by every minter / handler.
//
// Concurrency model: every method takes the RWMutex. Signing is a fast read;
// rotation is the only writer.
type JWTAuthority struct {
	mu sync.RWMutex

	// signer is the current Ed25519 signer.
	signer Signer

	// grace holds previous public keys until their grace_expires time.
	grace []graceKey

	// issuer is the URL placed in the iss claim. Configurable via
	// SARATHI_TOKEN_ISSUER. Production gates enforce https://.
	issuer string

	// audience is the default aud claim. Override per-mint by passing a
	// non-empty Audience in MintRequest.
	audience string

	// tokenTTL caps the minted JWT lifetime.
	tokenTTL time.Duration

	// introspectionAPIKey is required for POST /sarathi/v1/token/introspect.
	// Empty disables the endpoint (handler returns 503).
	introspectionAPIKey string

	// keysDir is the on-disk root for persistence / rotation.
	keysDir string

	// issuanceLogPath points at the JSONL audit log of mints.
	issuanceLogPath string

	// ephemeral records whether the current key was generated in memory.
	// Banners + production gates use this.
	ephemeral bool

	// clock is injectable for tests. Production uses time.Now().UTC().
	clock func() time.Time

	// schemaVersion is fixed at construction.
	schemaVersion string

	// registryVersion increments on every rotation (matches the trust-bundle
	// pattern in evaluator_registry_extension.go).
	registryVersion uint64
}

// JWTAuthorityConfig is the constructor input.
type JWTAuthorityConfig struct {
	Signer              Signer
	GraceKeys           []graceKey
	Issuer              string
	Audience            string
	TokenTTL            time.Duration
	IntrospectionAPIKey string
	KeysDir             string
	IssuanceLogPath     string
	Ephemeral           bool
	Clock               func() time.Time
}

// NewJWTAuthority constructs a JWTAuthority from explicit config. Used by
// tests and by the service runtime once it has resolved the signer.
func NewJWTAuthority(cfg JWTAuthorityConfig) (*JWTAuthority, error) {
	if cfg.Signer == nil {
		return nil, fmt.Errorf("jwt_authority: signer required")
	}
	iss := strings.TrimSpace(cfg.Issuer)
	if iss == "" {
		iss = DefaultJWTIssuer
	}
	aud := strings.TrimSpace(cfg.Audience)
	if aud == "" {
		aud = DefaultJWTAudience
	}
	ttl := cfg.TokenTTL
	if ttl <= 0 || ttl > DefaultJWTTokenTTL {
		ttl = DefaultJWTTokenTTL
	}
	logPath := strings.TrimSpace(cfg.IssuanceLogPath)
	if logPath == "" {
		logPath = DefaultJWTIssuanceLog
	}
	keysDir := strings.TrimSpace(cfg.KeysDir)
	if keysDir == "" {
		keysDir = DefaultJWTAuthorityKeysDir
	}
	clk := cfg.Clock
	if clk == nil {
		clk = func() time.Time { return time.Now().UTC() }
	}
	return &JWTAuthority{
		signer:              cfg.Signer,
		grace:               cloneGraceKeys(cfg.GraceKeys),
		issuer:              iss,
		audience:            aud,
		tokenTTL:            ttl,
		introspectionAPIKey: cfg.IntrospectionAPIKey,
		keysDir:             keysDir,
		issuanceLogPath:     logPath,
		ephemeral:           cfg.Ephemeral,
		clock:               clk,
		schemaVersion:       JWTAuthoritySchemaVersion,
		registryVersion:     1,
	}, nil
}

// LoadJWTAuthorityFromEnv resolves the authority from environment variables.
// Boot loading order documented in the plan:
//  1. SARATHI_JWT_AUTHORITY_PRIV_PATH (explicit) → load or fatal.
//  2. SARATHI_JWT_AUTHORITY_KEYS_DIR / current.key → load if present.
//  3. Ephemeral keypair in memory (banner warns).
//
// Production callers MUST additionally enforce the production boot gates
// (see service_runtime_cli.go). This helper does NOT enforce them — it
// returns a JWTAuthority along with `ephemeral=true` so the caller can
// decide.
func LoadJWTAuthorityFromEnv() (*JWTAuthority, error) {
	keysDir := strings.TrimSpace(os.Getenv(EnvJWTAuthorityKeysDir))
	if keysDir == "" {
		keysDir = DefaultJWTAuthorityKeysDir
	}
	privPath := strings.TrimSpace(os.Getenv(EnvJWTAuthorityPrivPath))
	pubPath := strings.TrimSpace(os.Getenv(EnvJWTAuthorityPubPath))
	if privPath == "" {
		privPath = filepath.Join(keysDir, "current.key")
	}
	if pubPath == "" {
		pubPath = filepath.Join(keysDir, "current.pub")
	}

	cfg := JWTAuthorityConfig{
		Issuer:              os.Getenv(EnvTokenIssuer),
		Audience:            os.Getenv(EnvTokenAudience),
		TokenTTL:            parseDurationSecondsEnv(EnvJWTTokenTTLSeconds, DefaultJWTTokenTTL),
		IntrospectionAPIKey: os.Getenv(EnvJWTIntrospectionAPIKey),
		KeysDir:             keysDir,
		IssuanceLogPath:     os.Getenv(EnvJWTAuthorityIssuanceLog),
	}

	signer, ephemeral, grace, err := loadOrGenerateSigner(privPath, pubPath, keysDir)
	if err != nil {
		return nil, err
	}
	cfg.Signer = signer
	cfg.Ephemeral = ephemeral
	cfg.GraceKeys = grace
	return NewJWTAuthority(cfg)
}

// loadOrGenerateSigner returns a Signer + ephemeral flag + grace keys.
// Refuses to load with unsafe file permissions on POSIX (mode & 0077 != 0).
func loadOrGenerateSigner(privPath, pubPath, keysDir string) (Signer, bool, []graceKey, error) {
	if privPath == "" {
		s, err := GenerateLocalEd25519Signer()
		return s, true, nil, err
	}
	st, err := os.Stat(privPath)
	if err != nil {
		if errIs(err, fs.ErrNotExist) {
			s, gerr := GenerateLocalEd25519Signer()
			return s, true, nil, gerr
		}
		return nil, false, nil, fmt.Errorf("jwt_authority: stat priv: %w", err)
	}
	if runtime.GOOS != "windows" {
		if st.Mode().Perm()&0o077 != 0 {
			return nil, false, nil, fmt.Errorf(
				"jwt_authority: refuse to load %s — permission mode %o is group/other readable; chmod 0600 first",
				privPath, st.Mode().Perm(),
			)
		}
	}
	privRaw, err := os.ReadFile(privPath)
	if err != nil {
		return nil, false, nil, fmt.Errorf("jwt_authority: read priv: %w", err)
	}
	privBytes, err := decodeHexKey(privRaw, ed25519.PrivateKeySize)
	if err != nil {
		return nil, false, nil, fmt.Errorf("jwt_authority: decode priv (%s): %w", privPath, err)
	}
	priv := ed25519.PrivateKey(privBytes)
	pub, ok := priv.Public().(ed25519.PublicKey)
	if !ok {
		return nil, false, nil, fmt.Errorf("jwt_authority: priv.Public() not ed25519.PublicKey")
	}
	// If a sibling pub file exists, cross-check that it matches the derived
	// public bytes. A mismatch indicates a stale pub file from an earlier
	// rotation and is operator-visible.
	if pubRaw, e2 := os.ReadFile(pubPath); e2 == nil {
		if pubBytes, e3 := decodeHexKey(pubRaw, ed25519.PublicKeySize); e3 == nil {
			if string(pubBytes) != string(pub) {
				return nil, false, nil, fmt.Errorf(
					"jwt_authority: pub file at %s does not match priv-derived public key; rotation likely incomplete",
					pubPath,
				)
			}
		}
	}
	createdAt := st.ModTime().UTC()
	signer, err := NewLocalEd25519Signer(priv, pub, createdAt)
	if err != nil {
		return nil, false, nil, err
	}
	// Load grace keys from <keysDir>/grace/*.pub if present.
	grace, _ := loadGraceKeys(filepath.Join(keysDir, "grace"))
	return signer, false, grace, nil
}

// loadGraceKeys reads every `<kid>.pub` + `<kid>.expires` pair under the grace
// directory. Files with parse errors or in-the-past expiries are skipped.
func loadGraceKeys(graceDir string) ([]graceKey, error) {
	out := []graceKey{}
	entries, err := os.ReadDir(graceDir)
	if err != nil {
		return out, nil // grace dir is optional
	}
	now := time.Now().UTC()
	for _, ent := range entries {
		if ent.IsDir() {
			continue
		}
		name := ent.Name()
		if !strings.HasSuffix(name, ".pub") {
			continue
		}
		kid := strings.TrimSuffix(name, ".pub")
		pubPath := filepath.Join(graceDir, name)
		expPath := filepath.Join(graceDir, kid+".expires")
		pubRaw, err := os.ReadFile(pubPath)
		if err != nil {
			continue
		}
		pubBytes, err := decodeHexKey(pubRaw, ed25519.PublicKeySize)
		if err != nil {
			continue
		}
		expRaw, err := os.ReadFile(expPath)
		if err != nil {
			continue
		}
		expTime, err := time.Parse(time.RFC3339, strings.TrimSpace(string(expRaw)))
		if err != nil {
			continue
		}
		if expTime.Before(now) {
			// Sweep stale entries on the way in.
			_ = os.Remove(pubPath)
			_ = os.Remove(expPath)
			continue
		}
		stat, _ := os.Stat(pubPath)
		createdAt := now
		if stat != nil {
			createdAt = stat.ModTime().UTC()
		}
		out = append(out, graceKey{
			Kid:          kid,
			Pub:          ed25519.PublicKey(pubBytes),
			CreatedAt:    createdAt,
			GraceExpires: expTime.UTC(),
		})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Kid < out[j].Kid })
	return out, nil
}

func cloneGraceKeys(in []graceKey) []graceKey {
	if len(in) == 0 {
		return nil
	}
	cp := make([]graceKey, len(in))
	copy(cp, in)
	return cp
}

// decodeHexKey trims whitespace, decodes hex, asserts length.
func decodeHexKey(raw []byte, want int) ([]byte, error) {
	s := strings.TrimSpace(string(raw))
	b, err := hex.DecodeString(s)
	if err != nil {
		return nil, fmt.Errorf("hex decode: %w", err)
	}
	if len(b) != want {
		return nil, fmt.Errorf("length=%d want=%d", len(b), want)
	}
	return b, nil
}

// errIs is a thin shim around errors.Is (kept local to avoid an extra import
// in a tiny helper; functionally identical for fs.ErrNotExist).
func errIs(err, target error) bool {
	if err == nil || target == nil {
		return err == target
	}
	return err.Error() == target.Error() ||
		strings.Contains(err.Error(), target.Error()) ||
		os.IsNotExist(err)
}

// parseDurationSecondsEnv reads a positive integer (seconds) env var, falling
// back to def on parse error or non-positive.
func parseDurationSecondsEnv(key string, def time.Duration) time.Duration {
	v := strings.TrimSpace(os.Getenv(key))
	if v == "" {
		return def
	}
	var secs float64
	_, err := fmt.Sscanf(v, "%f", &secs)
	if err != nil || secs <= 0 {
		return def
	}
	return time.Duration(secs * float64(time.Second))
}

// ============================================================================
// ACCESSORS (concurrency-safe, snapshot-like)
// ============================================================================

// Issuer returns the configured iss URL.
func (a *JWTAuthority) Issuer() string {
	if a == nil {
		return ""
	}
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.issuer
}

// Audience returns the default aud claim.
func (a *JWTAuthority) Audience() string {
	if a == nil {
		return ""
	}
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.audience
}

// TokenTTL returns the configured per-token lifetime.
func (a *JWTAuthority) TokenTTL() time.Duration {
	if a == nil {
		return 0
	}
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.tokenTTL
}

// CurrentKid returns the kid of the active signer.
func (a *JWTAuthority) CurrentKid() string {
	if a == nil {
		return ""
	}
	a.mu.RLock()
	defer a.mu.RUnlock()
	if a.signer == nil {
		return ""
	}
	return a.signer.Kid()
}

// IsEphemeral reports whether the current signer was generated in memory.
func (a *JWTAuthority) IsEphemeral() bool {
	if a == nil {
		return false
	}
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.ephemeral
}

// IntrospectionEnabled reports whether the introspection API key is set.
func (a *JWTAuthority) IntrospectionEnabled() bool {
	if a == nil {
		return false
	}
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.introspectionAPIKey != ""
}

// IntrospectionAPIKey returns the configured key (for constant-time compare).
// Use only inside the introspect handler.
func (a *JWTAuthority) IntrospectionAPIKey() string {
	if a == nil {
		return ""
	}
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.introspectionAPIKey
}

// KeysDir returns the on-disk root directory.
func (a *JWTAuthority) KeysDir() string {
	if a == nil {
		return ""
	}
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.keysDir
}

// IssuanceLogPath returns the audit log path.
func (a *JWTAuthority) IssuanceLogPath() string {
	if a == nil {
		return ""
	}
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.issuanceLogPath
}

// SchemaVersion returns the schema-version constant.
func (a *JWTAuthority) SchemaVersion() string {
	if a == nil {
		return JWTAuthoritySchemaVersion
	}
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.schemaVersion
}

// RegistryVersion returns the monotonic key-set version. Incremented on
// every rotation.
func (a *JWTAuthority) RegistryVersion() uint64 {
	if a == nil {
		return 0
	}
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.registryVersion
}

// CurrentSigner returns the active signer (read-only). Used by mint.
func (a *JWTAuthority) CurrentSigner() Signer {
	if a == nil {
		return nil
	}
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.signer
}

// ============================================================================
// KEY LOOKUP (for verification across current + grace)
// ============================================================================

// LookupPublicKey returns the public key associated with kid, or nil. Used by
// the JWT verifier (jwt_authority_verify.go) when resolving the keyfunc.
func (a *JWTAuthority) LookupPublicKey(kid string) ed25519.PublicKey {
	if a == nil || kid == "" {
		return nil
	}
	a.mu.RLock()
	defer a.mu.RUnlock()
	if a.signer != nil && a.signer.Kid() == kid {
		return a.signer.PublicKey()
	}
	now := a.clock()
	for i := range a.grace {
		if a.grace[i].Kid == kid && !a.grace[i].IsExpired(now) {
			return a.grace[i].Pub
		}
	}
	return nil
}

// SnapshotKeys returns a read-only view of the publishable key set, sweeping
// expired grace entries along the way. Order: current first, then graces by
// kid for stable JWKS output.
func (a *JWTAuthority) SnapshotKeys() (current Signer, grace []graceKey, registryVersion uint64, ephemeral bool) {
	if a == nil {
		return nil, nil, 0, false
	}
	a.mu.Lock()
	defer a.mu.Unlock()
	now := a.clock()
	live := make([]graceKey, 0, len(a.grace))
	for _, g := range a.grace {
		if !g.IsExpired(now) {
			live = append(live, g)
		} else {
			// Sweep stale entries from disk too.
			_ = os.Remove(filepath.Join(a.keysDir, "grace", g.Kid+".pub"))
			_ = os.Remove(filepath.Join(a.keysDir, "grace", g.Kid+".expires"))
		}
	}
	if len(live) != len(a.grace) {
		a.grace = live
	}
	out := make([]graceKey, len(live))
	copy(out, live)
	return a.signer, out, a.registryVersion, a.ephemeral
}

// ============================================================================
// PERSISTENCE (bootstrap + rotate write paths)
// ============================================================================

// PersistSignerToDisk writes the signer's keypair under keysDir.
// Files: current.key (0600), current.pub (0644), current.kid (0644).
// Used by --bootstrap-jwt-authority and --rotate-jwt-authority.
func PersistSignerToDisk(s Signer, keysDir string) error {
	if s == nil {
		return fmt.Errorf("PersistSignerToDisk: nil signer")
	}
	if keysDir == "" {
		keysDir = DefaultJWTAuthorityKeysDir
	}
	if err := os.MkdirAll(keysDir, 0o700); err != nil {
		return fmt.Errorf("mkdir keys: %w", err)
	}
	local, ok := s.(*LocalEd25519Signer)
	if !ok {
		return fmt.Errorf("PersistSignerToDisk: signer is not *LocalEd25519Signer (HSM/KMS signers persist via their own provider)")
	}
	privHex := hex.EncodeToString(local.PrivateKey())
	pubHex := hex.EncodeToString(local.PublicKey())
	if err := os.WriteFile(filepath.Join(keysDir, "current.key"), []byte(privHex+"\n"), 0o600); err != nil {
		return fmt.Errorf("write priv: %w", err)
	}
	if err := os.WriteFile(filepath.Join(keysDir, "current.pub"), []byte(pubHex+"\n"), 0o644); err != nil {
		return fmt.Errorf("write pub: %w", err)
	}
	if err := os.WriteFile(filepath.Join(keysDir, "current.kid"), []byte(local.Kid()+"\n"), 0o644); err != nil {
		return fmt.Errorf("write kid: %w", err)
	}
	return nil
}

// MoveCurrentToGrace moves current.{pub} into <keysDir>/grace/<kid>.pub and
// writes <kid>.expires. Deletes current.key (the private bytes are GONE) so
// the old key becomes verify-only for the grace window.
// This is the second step of --rotate-jwt-authority.
func MoveCurrentToGrace(keysDir string, oldKid string, graceUntil time.Time) error {
	if keysDir == "" || oldKid == "" {
		return fmt.Errorf("MoveCurrentToGrace: keysDir + oldKid required")
	}
	graceDir := filepath.Join(keysDir, "grace")
	if err := os.MkdirAll(graceDir, 0o700); err != nil {
		return fmt.Errorf("mkdir grace: %w", err)
	}
	srcPub := filepath.Join(keysDir, "current.pub")
	dstPub := filepath.Join(graceDir, oldKid+".pub")
	pubRaw, err := os.ReadFile(srcPub)
	if err != nil {
		return fmt.Errorf("read current.pub: %w", err)
	}
	if err := os.WriteFile(dstPub, pubRaw, 0o644); err != nil {
		return fmt.Errorf("write grace pub: %w", err)
	}
	dstExp := filepath.Join(graceDir, oldKid+".expires")
	if err := os.WriteFile(dstExp, []byte(graceUntil.UTC().Format(time.RFC3339)+"\n"), 0o644); err != nil {
		return fmt.Errorf("write grace expires: %w", err)
	}
	// Update / append manifest.
	if err := appendGraceManifest(keysDir, oldKid, graceUntil); err != nil {
		// Non-fatal — the .expires file is the source of truth.
		fmt.Fprintf(os.Stderr, "[jwt_authority] WARN grace manifest append: %v\n", err)
	}
	// Destroy private key.
	srcPriv := filepath.Join(keysDir, "current.key")
	if err := os.Remove(srcPriv); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("remove current.key: %w", err)
	}
	return nil
}

func appendGraceManifest(keysDir, kid string, expires time.Time) error {
	path := filepath.Join(keysDir, "grace_manifest.json")
	m := map[string]string{}
	if raw, err := os.ReadFile(path); err == nil {
		_ = json.Unmarshal(raw, &m)
	}
	m[kid] = expires.UTC().Format(time.RFC3339)
	out, err := json.MarshalIndent(m, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, out, 0o644)
}

// AdoptRotatedSigner replaces the current signer atomically and pushes the
// previous public key into grace with the given expiry. Used by tests and by
// the in-process rotation harness (cmd_jwt_authority.go runs the on-disk
// move and then calls this on the live JWTAuthority).
func (a *JWTAuthority) AdoptRotatedSigner(newSigner Signer, graceUntil time.Time) error {
	if a == nil {
		return fmt.Errorf("nil JWTAuthority")
	}
	if newSigner == nil {
		return fmt.Errorf("AdoptRotatedSigner: nil newSigner")
	}
	if newSigner.Kid() == "" {
		return fmt.Errorf("AdoptRotatedSigner: newSigner has empty kid")
	}
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.signer != nil {
		a.grace = append(a.grace, graceKey{
			Kid:          a.signer.Kid(),
			Pub:          a.signer.PublicKey(),
			CreatedAt:    a.signer.CreatedAt(),
			GraceExpires: graceUntil.UTC(),
		})
		// Drop expired grace entries.
		now := a.clock()
		live := a.grace[:0]
		for _, g := range a.grace {
			if !g.IsExpired(now) {
				live = append(live, g)
			}
		}
		a.grace = live
	}
	a.signer = newSigner
	a.ephemeral = false
	a.registryVersion++
	return nil
}

// ============================================================================
// SUMMARY (for banners + --inspect-jwt-authority)
// ============================================================================

// Summary returns a human-printable map of the authority state. Safe to log.
func (a *JWTAuthority) Summary() map[string]interface{} {
	if a == nil {
		return map[string]interface{}{"present": false}
	}
	cur, grace, ver, eph := a.SnapshotKeys()
	out := map[string]interface{}{
		"present":           true,
		"schema_version":    a.SchemaVersion(),
		"registry_version":  ver,
		"issuer":            a.Issuer(),
		"audience":          a.Audience(),
		"token_ttl_seconds": int(a.TokenTTL() / time.Second),
		"introspection_enabled": a.IntrospectionEnabled(),
		"keys_dir":          a.KeysDir(),
		"issuance_log":      a.IssuanceLogPath(),
		"ephemeral":         eph,
	}
	if cur != nil {
		out["current_kid"] = cur.Kid()
		out["current_pub_hex"] = hex.EncodeToString(cur.PublicKey())
		out["current_created_at"] = cur.CreatedAt().Format(time.RFC3339)
	}
	graceList := make([]map[string]string, 0, len(grace))
	for _, g := range grace {
		graceList = append(graceList, map[string]string{
			"kid":           g.Kid,
			"pub_hex":       hex.EncodeToString(g.Pub),
			"created_at":    g.CreatedAt.Format(time.RFC3339),
			"grace_expires": g.GraceExpires.Format(time.RFC3339),
		})
	}
	out["grace_keys"] = graceList
	return out
}
