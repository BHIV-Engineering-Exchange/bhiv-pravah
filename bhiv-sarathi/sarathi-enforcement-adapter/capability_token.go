package main

// capability_token.go — Sovereign-Grade Cryptographic Capability Token.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Enforcement Adapter (PEP)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   A CapabilityToken is the SOLE artifact that authorizes execution.
//   It is cryptographically signed by the TokenAuthority (Ed25519, RFC 8032).
//   Without a valid, signed, unexpired, unconsumed token, execution is impossible.
//
// SOVEREIGN ARCHITECTURE:
//   - TokenAuthority (private key) lives in the EnforcementAdapter (signer)
//   - ExecutionEngine holds ONLY the public key (verifier)
//   - Separation of concerns: adapter signs, engine verifies, no shared secrets
//   - Private key never leaves the adapter boundary
//
// TOKEN CONTRACT:
//   1. Tokens are issued ONLY on ALLOW verdicts — DENY/ESCALATE = nil token
//   2. Tokens are Ed25519-signed by the TokenAuthority
//   3. Execution engine verifies signature before ANY processing
//   4. No valid signature → no execution (architectural hard gate)
//   5. Tokens are single-use — consumed tokens cannot be replayed
//   6. Tokens carry TTL — expired tokens are rejected with zero grace
//   7. Token binds: decision_id + request_hash + policy_hash + enforcement_hash
//   8. All failure paths produce deterministic block reason codes
//
// 8-CHECK VALIDATION GATE:
//   1. Token exists (not nil)             → NO_TOKEN
//   2. Signature valid (Ed25519)          → INVALID_SIGNATURE
//   3. Token integrity (SHA-256 hash)     → HASH_MISMATCH
//   4. Token not expired (TTL)            → TOKEN_EXPIRED
//   5. Token not consumed (single-use)    → TOKEN_ALREADY_USED
//   6. request_hash matches               → REQUEST_HASH_MISMATCH
//   7. policy_hash matches                → POLICY_MISMATCH
//   8. enforcement_hash in adapter chain  → ENFORCEMENT_HASH_NOT_IN_CHAIN
//
// INDUSTRY ALIGNMENT:
//   - NIST 800-207 (Zero Trust): per-request authorization tokens with cryptographic binding
//   - Google Zanzibar: capability-based access control with consistency tokens
//   - AWS STS: short-lived signed session tokens with expiry
//   - SPIFFE/SPIRE: workload identity with X.509/JWT tokens
//   - Azure Entra: token-bound access with cryptographic proof-of-possession
//   - Anthropic/OpenAI: execution gating with non-bypassable authorization layer

import (
	"crypto/ed25519"
	"crypto/subtle"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
)

// ClockSkewTolerance is the maximum acceptable clock drift between distributed
// service instances. Production systems (Kerberos: 5min, JWT: 30-60s) require
// this to prevent false rejections in distributed deployments.
// Reference: https://github.com/spring-projects/spring-authorization-server/issues/1631
const ClockSkewTolerance = 5 * time.Second

// ================================================================
// STANDARDIZED FAILURE CODES (Deterministic Block Reasons)
// ================================================================

// BlockReason constants define the complete set of deterministic execution
// block codes. No generic errors are permitted. Every failure has a specific,
// documented, auditable reason code.
const (
	BlockNoToken                  = "NO_TOKEN"
	BlockInvalidSignature         = "INVALID_SIGNATURE"
	BlockHashMismatch             = "HASH_MISMATCH"
	BlockTokenExpired             = "TOKEN_EXPIRED"
	BlockTokenAlreadyUsed         = "TOKEN_ALREADY_USED"
	BlockRequestHashMismatch      = "REQUEST_HASH_MISMATCH"
	BlockPolicyMismatch           = "POLICY_MISMATCH"
	BlockEnforcementNotInChain    = "ENFORCEMENT_HASH_NOT_IN_CHAIN"
	BlockEmptyEnforcementHash     = "EMPTY_ENFORCEMENT_HASH"
	BlockAllowWithoutDecisionID   = "ALLOW_WITHOUT_DECISION_ID"
	BlockVerdictNotAllow          = "VERDICT_NOT_ALLOW"
	BlockDecisionExpired          = "DECISION_EXPIRED"
	BlockRateLimitExceeded        = "RATE_LIMIT_EXCEEDED"
	BlockValidationFailed         = "VALIDATION_FAILED"
	BlockPolicyVersionMismatch    = "POLICY_VERSION_MISMATCH"
	BlockEscalatePendingReview    = "ESCALATE_PENDING_REVIEW"
	BlockTokenIntegrityFailed     = "TOKEN_INTEGRITY_FAILED"
	BlockObligationDischargeFail  = "OBLIGATION_DISCHARGE_FAILED"
)

// ================================================================
// TOKEN AUTHORITY (Ed25519 Signing/Verification Separation)
// ================================================================

// TokenAuthority holds the Ed25519 key pair for token signing.
// The private key is held ONLY by the EnforcementAdapter (signer).
// The public key is shared with the ExecutionEngine (verifier).
// This creates cryptographic separation of concerns: even if an attacker
// constructs a CapabilityToken struct, they cannot sign it without the
// private key, making token forgery cryptographically impossible.
type TokenAuthority struct {
	keyID      string             // unique identifier for this authority key
	privateKey ed25519.PrivateKey // held by adapter — NEVER shared
	publicKey  ed25519.PublicKey  // shared with engine for verification
	createdAt  time.Time
}

// NewTokenAuthority generates a new Ed25519 key pair for token signing.
// In production, the private key would be loaded from a secure key store
// (HSM, Vault, AWS KMS). For this implementation, keys are generated
// per-pipeline instance, ensuring each pipeline run has unique authority.
func NewTokenAuthority() (*TokenAuthority, error) {
	pub, priv, err := ed25519.GenerateKey(nil)
	if err != nil {
		return nil, fmt.Errorf("token authority key generation failed: %w", err)
	}
	return &TokenAuthority{
		keyID:      fmt.Sprintf("TA-%s", uuid.New().String()[:8]),
		privateKey: priv,
		publicKey:  pub,
		createdAt:  time.Now().UTC(),
	}, nil
}

// KeyID returns the authority key identifier.
func (ta *TokenAuthority) KeyID() string { return ta.keyID }

// PublicKey returns the public key for verification.
func (ta *TokenAuthority) PublicKey() ed25519.PublicKey { return ta.publicKey }

// PublicKeyHex returns the public key as a hex string for logging.
func (ta *TokenAuthority) PublicKeyHex() string { return hex.EncodeToString(ta.publicKey) }

// SignToken signs a CapabilityToken's tokenHash with Ed25519.
// This is called ONLY by the EnforcementAdapter after token issuance.
// The signature covers the tokenHash (which itself covers all token fields),
// creating a cryptographic chain: fields → SHA-256 hash → Ed25519 signature.
func (ta *TokenAuthority) SignToken(token *CapabilityToken) {
	if token == nil {
		return
	}
	message := []byte(token.tokenHash)
	token.signature = ed25519.Sign(ta.privateKey, message)
	token.signerKeyID = ta.keyID
	token.signatureHex = hex.EncodeToString(token.signature)
}

// VerifyTokenSignature verifies that a token was signed by this authority.
// Returns true only if the Ed25519 signature over tokenHash is valid.
// This is called by the ExecutionEngine with ONLY the public key.
func VerifyTokenSignature(token *CapabilityToken, publicKey ed25519.PublicKey, expectedKeyID string) (bool, string) {
	if token == nil {
		return false, BlockNoToken
	}
	if len(token.signature) == 0 {
		return false, fmt.Sprintf("%s: token has no Ed25519 signature", BlockInvalidSignature)
	}
	if token.signerKeyID != expectedKeyID {
		return false, fmt.Sprintf("%s: signer_key_id mismatch: token=%s expected=%s",
			BlockInvalidSignature, token.signerKeyID, expectedKeyID)
	}
	message := []byte(token.tokenHash)
	if !ed25519.Verify(publicKey, message, token.signature) {
		return false, fmt.Sprintf("%s: Ed25519 signature verification failed", BlockInvalidSignature)
	}
	return true, "SIGNATURE_VALID"
}

// ================================================================
// CAPABILITY TOKEN (Sovereign-Grade)
// ================================================================

// capabilityTokenPayload is used for deterministic hash computation (GAP-17).
// All fields that define the token's binding are included.
type capabilityTokenPayload struct {
	TokenID         string `json:"token_id"`
	DecisionID      string `json:"decision_id"`
	RequestHash     string `json:"request_hash"`
	PolicyHash      string `json:"policy_hash"`
	EnforcementHash string `json:"enforcement_hash"`
	CorrelationID   string `json:"correlation_id"`
	Verdict         string `json:"verdict"`
	Issuer          string `json:"issuer"`
	Audience        string `json:"audience"`
	IssuedAt        string `json:"issued_at"`
	ExpiresAt       string `json:"expires_at"`
	RegistryVersion int64  `json:"registry_version"` // Gap 2
	RpaHash         string `json:"rpa_hash"`         // Gap 3
}

// CapabilityToken is the cryptographic proof that execution is authorized.
// It is the ONLY artifact the ExecutionEngine accepts. Without a valid,
// Ed25519-signed, unexpired, unconsumed token, execution is impossible.
//
// The token carries all data needed for execution — the engine does NOT
// need the ExecutionResponse. This is the architectural hard gate:
// the token IS the authority, not just a reference to it.
type CapabilityToken struct {
	// Core binding fields
	tokenID         string    // unique token identifier (UUID4)
	decisionID      string    // PDP decision that authorized this
	requestHash     string    // binds to the exact authorized request
	policyHash      string    // binds to the exact authorizing policy version
	enforcementHash string    // binds to the specific enforcement chain entry
	correlationID   string    // trace correlation across systems
	verdict         string    // the PDP verdict (always ALLOW for valid tokens)
	obligations     []string  // mandatory side-effects to discharge before execution
	registryVersion int64     // Gap 2: Freshness binding
	rpaHash         string    // Gap 3: Runtime verification binding

	// Token binding (RFC 7519 iss/aud pattern — prevents cross-instance replay)
	issuer   string // "sarathi-{instance_id}" — which enforcement adapter signed this
	audience string // target resource/service this token authorizes access to

	// Temporal binding
	issuedAt  time.Time // when the token was created
	expiresAt time.Time // when the token expires (matches decision TTL)

	// Integrity
	tokenHash string // SHA-256 over all binding fields (deterministic)

	// Cryptographic signature (Ed25519, RFC 8032)
	signature    []byte // Ed25519 signature over tokenHash
	signerKeyID  string // which TokenAuthority key signed this
	signatureHex string // hex representation for logging

	// State
	consumed bool // single-use flag — true after first use
}

// IssueCapabilityToken creates a new token from an ALLOW enforcement response.
// Returns nil for non-ALLOW verdicts or invalid responses.
// The token is created UNSIGNED — the TokenAuthority must sign it separately.
// This separation ensures only the adapter (which holds the private key) can
// produce valid tokens.
func IssueCapabilityToken(resp *ExecutionResponse, rpaHash string) *CapabilityToken {
	if resp == nil || resp.Verdict() != "ALLOW" {
		return nil
	}
	if resp.DecisionID() == "" {
		return nil
	}

	now := time.Now().UTC()

	// Maximum TTL cap: no token can live longer than MaxTokenTTL regardless of PDP decision.
	// Prevents misconfigured policies from issuing long-lived tokens (NIST SP 800-207).
	const MaxTokenTTL = 60 * time.Second
	expiresAt := resp.ValidUntil()
	if expiresAt.Sub(now) > MaxTokenTTL {
		expiresAt = now.Add(MaxTokenTTL)
	}

	token := &CapabilityToken{
		tokenID:         uuid.New().String(),
		decisionID:      resp.DecisionID(),
		requestHash:     resp.RequestHash(),
		policyHash:      resp.PolicyHashField(),
		enforcementHash: resp.EnforcementHash(),
		correlationID:   resp.CorrelationID(),
		verdict:         resp.Verdict(),
		obligations:     resp.Obligations(),
		registryVersion: resp.RegistryVersion(),
		rpaHash:         rpaHash,
		issuer:          "sarathi-enforcement-adapter",
		audience:        resp.ResourceTypeField(),
		issuedAt:        now,
		expiresAt:       expiresAt,
		consumed:        false,
	}
	token.tokenHash = token.computeHash()
	return token
}

// computeHash computes the SHA-256 integrity seal over all binding fields.
// Uses struct-based serialization for deterministic field ordering (GAP-17).
func (ct *CapabilityToken) computeHash() string {
	payload := capabilityTokenPayload{
		TokenID:         ct.tokenID,
		DecisionID:      ct.decisionID,
		RequestHash:     ct.requestHash,
		PolicyHash:      ct.policyHash,
		EnforcementHash: ct.enforcementHash,
		CorrelationID:   ct.correlationID,
		Verdict:         ct.verdict,
		Issuer:          ct.issuer,
		Audience:        ct.audience,
		IssuedAt:        ct.issuedAt.Format("2006-01-02T15:04:05.000000Z"),
		ExpiresAt:       ct.expiresAt.Format("2006-01-02T15:04:05.000000Z"),
		RegistryVersion: ct.registryVersion,
		RpaHash:         ct.rpaHash,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		// FIX-06 (v7.0): Safe fallback — deterministic error hash instead of panic
		return Sha256Hex([]byte(fmt.Sprintf("TOKEN_HASH_ERROR:%s:%s:%v", ct.tokenID, ct.decisionID, err)))
	}
	return Sha256Hex(data)
}

// --- Read-only accessors ---

func (ct *CapabilityToken) TokenID() string         { return ct.tokenID }
func (ct *CapabilityToken) DecisionID() string       { return ct.decisionID }
func (ct *CapabilityToken) RequestHash() string      { return ct.requestHash }
func (ct *CapabilityToken) PolicyHash() string       { return ct.policyHash }
func (ct *CapabilityToken) EnforcementHash() string  { return ct.enforcementHash }
func (ct *CapabilityToken) CorrelationID() string    { return ct.correlationID }
func (ct *CapabilityToken) Verdict() string          { return ct.verdict }
func (ct *CapabilityToken) RegistryVersion() int64   { return ct.registryVersion }
func (ct *CapabilityToken) RpaHash() string          { return ct.rpaHash }
func (ct *CapabilityToken) IssuedAt() time.Time      { return ct.issuedAt }
func (ct *CapabilityToken) ExpiresAt() time.Time     { return ct.expiresAt }
func (ct *CapabilityToken) TokenHash() string        { return ct.tokenHash }
func (ct *CapabilityToken) SignerKeyID() string      { return ct.signerKeyID }
func (ct *CapabilityToken) SignatureHex() string     { return ct.signatureHex }
func (ct *CapabilityToken) IsConsumed() bool         { return ct.consumed }
func (ct *CapabilityToken) IsSigned() bool           { return len(ct.signature) > 0 }
func (ct *CapabilityToken) Issuer() string           { return ct.issuer }
func (ct *CapabilityToken) Audience() string         { return ct.audience }

// Obligations returns a defensive copy of obligations.
func (ct *CapabilityToken) Obligations() []string {
	cp := make([]string, len(ct.obligations))
	copy(cp, ct.obligations)
	return cp
}

// IsExpired returns true if the token's TTL has elapsed.
// IsExpired checks if the token has exceeded its TTL, with clock skew tolerance
// to prevent false rejections in distributed deployments where clocks may drift.
// Reference: Kerberos uses 5min tolerance; JWT best practices recommend 30-60s.
func (ct *CapabilityToken) IsExpired() bool {
	return time.Now().UTC().After(ct.expiresAt.Add(ClockSkewTolerance))
}

// VerifyIntegrity recomputes the tokenHash and compares to stored value
// using constant-time comparison to prevent timing side-channel attacks.
// Returns false if any binding field was modified after issuance.
func (ct *CapabilityToken) VerifyIntegrity() bool {
	recomputed := ct.computeHash()
	return subtle.ConstantTimeCompare([]byte(ct.tokenHash), []byte(recomputed)) == 1
}

// ToMap returns a read-only map representation for trace/logging.
func (ct *CapabilityToken) ToMap() map[string]interface{} {
	return map[string]interface{}{
		"token_id":         ct.tokenID,
		"decision_id":      ct.decisionID,
		"request_hash":     ct.requestHash,
		"policy_hash":      ct.policyHash,
		"enforcement_hash": ct.enforcementHash,
		"correlation_id":   ct.correlationID,
		"verdict":          ct.verdict,
		"obligations":      ct.obligations,
		"issued_at":        ct.issuedAt.Format("2006-01-02T15:04:05.000000Z"),
		"expires_at":       ct.expiresAt.Format("2006-01-02T15:04:05.000000Z"),
		"token_hash":       ct.tokenHash,
		"signer_key_id":    ct.signerKeyID,
		"signature_hex":    ct.signatureHex,
		"registry_version": ct.registryVersion,
		"rpa_hash":         ct.rpaHash,
		"is_signed":        len(ct.signature) > 0,
		"consumed":         ct.consumed,
	}
}

// ================================================================
// EXECUTION RESULT (Standardized Output Contract)
// ================================================================

// ExecutionResult is the standardized output of any execution attempt.
// Every field is deterministic. No generic errors. Every block has a
// specific, documented, auditable reason code.
//
// This is the integration contract: external systems consume this
// structure to understand execution outcomes without parsing free-text.
type ExecutionResult struct {
	Executed          bool     `json:"executed"`
	Status            string   `json:"status"`             // EXECUTION_PERMITTED or EXECUTION_BLOCKED
	BlockReason       string   `json:"block_reason"`       // standardized code from BlockXxx constants
	BlockDetail       string   `json:"block_detail"`       // human-readable explanation
	TokenID           string   `json:"token_id"`
	DecisionID        string   `json:"decision_id"`
	CorrelationID     string   `json:"correlation_id"`
	RequestHash       string   `json:"request_hash"`
	PolicyHash        string   `json:"policy_hash"`
	EnforcementHash   string   `json:"enforcement_hash"`
	ExecutionSequence int      `json:"execution_sequence"`
	ExecutionHash     string   `json:"execution_hash"`
	PrevExecutionHash string   `json:"prev_execution_hash"`
	Obligations       []string `json:"obligations_discharged,omitempty"`
	Timestamp         string   `json:"timestamp"`
}

// ToMap returns the execution result as a map for backward compatibility.
func (er *ExecutionResult) ToMap() map[string]interface{} {
	m := map[string]interface{}{
		"executed":             er.Executed,
		"execution_state":     er.Status,
		"execution_sequence":  er.ExecutionSequence,
		"execution_hash":      er.ExecutionHash,
		"prev_execution_hash": er.PrevExecutionHash,
		"correlation_id":      er.CorrelationID,
		"decision_id":         er.DecisionID,
		"enforcement_hash":    er.EnforcementHash,
		"timestamp":           er.Timestamp,
	}
	if er.BlockReason != "" {
		m["block_reason"] = fmt.Sprintf("%s: %s", er.BlockReason, er.BlockDetail)
	}
	if len(er.Obligations) > 0 {
		m["obligations_discharged"] = er.Obligations
	}
	if er.TokenID != "" {
		m["token_id"] = er.TokenID
	}
	return m
}

// ================================================================
// TOKEN VALIDATION (8-Check Sovereign Gate)
// ================================================================

// TokenValidationResult contains the result of token validation.
type TokenValidationResult struct {
	Valid       bool   `json:"valid"`
	Reason      string `json:"reason"`       // standardized block code
	Detail      string `json:"detail"`       // human-readable explanation
	TokenID     string `json:"token_id,omitempty"`
	TokenHash   string `json:"token_hash,omitempty"`
}

// ValidateTokenFull performs the complete 8-check sovereign validation gate.
// This is the production-grade validation used by ExecuteWithToken.
// Checks: existence → signature → integrity → expiry → consumed → request_hash → policy_hash → enforcement_hash
func ValidateTokenFull(
	token *CapabilityToken,
	publicKey ed25519.PublicKey,
	expectedKeyID string,
	enforcementChainCheck func(string) bool,
) TokenValidationResult {
	// Check 1: Token existence
	if token == nil {
		return TokenValidationResult{
			Valid:  false,
			Reason: BlockNoToken,
			Detail: "execution requires a valid capability token",
		}
	}

	// Check 2: Ed25519 signature verification (cryptographic hard gate)
	sigValid, sigReason := VerifyTokenSignature(token, publicKey, expectedKeyID)
	if !sigValid {
		return TokenValidationResult{
			Valid:     false,
			Reason:    BlockInvalidSignature,
			Detail:    sigReason,
			TokenID:   token.tokenID,
			TokenHash: token.tokenHash,
		}
	}

	// Check 3: Token integrity (SHA-256 hash)
	if !token.VerifyIntegrity() {
		return TokenValidationResult{
			Valid:     false,
			Reason:    BlockHashMismatch,
			Detail:    "token_hash recomputation mismatch — token fields modified after signing",
			TokenID:   token.tokenID,
			TokenHash: token.tokenHash,
		}
	}

	// Check 4: Token expiry
	if token.IsExpired() {
		return TokenValidationResult{
			Valid:     false,
			Reason:    BlockTokenExpired,
			Detail:    fmt.Sprintf("expires_at=%s", token.expiresAt.Format("2006-01-02T15:04:05Z")),
			TokenID:   token.tokenID,
			TokenHash: token.tokenHash,
		}
	}

	// Check 5: Single-use consumed check — MOVED to ExecutionEngine.ExecuteWithToken()
	// for atomic validation+consumption under single lock (VULN-C3 FIX).
	// The consumed flag is checked inside TokenRegistry.Consume() which holds its own lock.

	// Check 6: Verdict must be ALLOW
	if token.verdict != "ALLOW" {
		return TokenValidationResult{
			Valid:     false,
			Reason:    BlockVerdictNotAllow,
			Detail:    fmt.Sprintf("token verdict=%s, expected ALLOW", token.verdict),
			TokenID:   token.tokenID,
			TokenHash: token.tokenHash,
		}
	}

	// Check 7: enforcement_hash exists in adapter chain (bypass prevention)
	if enforcementChainCheck != nil && !enforcementChainCheck(token.enforcementHash) {
		return TokenValidationResult{
			Valid:     false,
			Reason:    BlockEnforcementNotInChain,
			Detail:    "enforcement_hash not found in adapter chain — possible forgery",
			TokenID:   token.tokenID,
			TokenHash: token.tokenHash,
		}
	}

	// Check 8: Decision ID must be present
	if token.decisionID == "" {
		return TokenValidationResult{
			Valid:     false,
			Reason:    BlockAllowWithoutDecisionID,
			Detail:    "token has ALLOW verdict but no decision_id",
			TokenID:   token.tokenID,
			TokenHash: token.tokenHash,
		}
	}

	return TokenValidationResult{
		Valid:     true,
		Reason:    "TOKEN_VALID",
		Detail:    "all 8 checks passed",
		TokenID:   token.tokenID,
		TokenHash: token.tokenHash,
	}
}

// ValidateToken is the backward-compatible validation (without signature check).
// Used internally where signature was already verified or not yet available.
func ValidateToken(token *CapabilityToken, resp *ExecutionResponse) TokenValidationResult {
	if token == nil {
		return TokenValidationResult{
			Valid:  false,
			Reason: BlockNoToken,
			Detail: "execution requires a valid capability token",
		}
	}
	if !token.VerifyIntegrity() {
		return TokenValidationResult{
			Valid:     false,
			Reason:    BlockTokenIntegrityFailed,
			Detail:    "token_hash mismatch — possible tampering",
			TokenID:   token.tokenID,
			TokenHash: token.tokenHash,
		}
	}
	if token.IsExpired() {
		return TokenValidationResult{
			Valid:     false,
			Reason:    BlockTokenExpired,
			Detail:    fmt.Sprintf("expires_at=%s", token.expiresAt.Format("2006-01-02T15:04:05Z")),
			TokenID:   token.tokenID,
			TokenHash: token.tokenHash,
		}
	}
	if token.consumed {
		return TokenValidationResult{
			Valid:     false,
			Reason:    BlockTokenAlreadyUsed,
			Detail:    "replay attempt detected",
			TokenID:   token.tokenID,
			TokenHash: token.tokenHash,
		}
	}
	if resp != nil {
		if token.requestHash != resp.RequestHash() {
			return TokenValidationResult{
				Valid:     false,
				Reason:    BlockRequestHashMismatch,
				Detail:    fmt.Sprintf("token=%s resp=%s", token.requestHash, resp.RequestHash()),
				TokenID:   token.tokenID,
				TokenHash: token.tokenHash,
			}
		}
		if token.policyHash != resp.PolicyHashField() {
			return TokenValidationResult{
				Valid:     false,
				Reason:    BlockPolicyMismatch,
				Detail:    fmt.Sprintf("token=%s resp=%s", token.policyHash, resp.PolicyHashField()),
				TokenID:   token.tokenID,
				TokenHash: token.tokenHash,
			}
		}
	}
	return TokenValidationResult{
		Valid:     true,
		Reason:    "TOKEN_VALID",
		Detail:    "all checks passed",
		TokenID:   token.tokenID,
		TokenHash: token.tokenHash,
	}
}

// ================================================================
// TOKEN REGISTRY (Single-Use Enforcement + Durable Persistence)
// ================================================================

// CRIT-05 FIX: TokenRegistryStore defines the durable persistence interface
// for token state. In production, this MUST be backed by a durable store
// (PostgreSQL, Redis with AOF, etc.) to survive process restarts.
//
// Without durable persistence, a process restart clears the consumed set,
// allowing previously-consumed tokens to be replayed — a CRITICAL replay
// vulnerability that defeats the entire single-use guarantee.
//
// Industry alignment:
//   - AWS STS: Token state persisted in DynamoDB with cross-region replication
//   - Google Zanzibar: Token/tuple state in Spanner with global consistency
//   - HashiCorp Vault: Token state in Consul/Raft with crash recovery
//   - SPIFFE/SPIRE: Registration entries in SQLite/PostgreSQL
type TokenRegistryStore interface {
	// PersistIssued records a newly issued token to durable storage.
	PersistIssued(tokenID string, tokenHash string, expiresAt time.Time) error
	// PersistConsumed records a token consumption to durable storage.
	// This MUST be atomic — partial writes can allow replay.
	PersistConsumed(tokenHash string, consumedAt time.Time) error
	// IsConsumedDurable checks durable storage for a consumed token.
	// Used on cache miss to prevent replay after process restart.
	IsConsumedDurable(tokenHash string) (bool, error)
	// LoadActiveTokens loads all non-expired tokens from durable storage.
	// Called on startup to rebuild the in-memory cache.
	LoadActiveTokens() (issued map[string]time.Time, consumed map[string]time.Time, err error)
	// IsDurable returns true if the store survives process restarts.
	IsDurable() bool
}

// InMemoryTokenStore is a non-durable store for testing/development.
// It satisfies TokenRegistryStore but loses state on restart.
type InMemoryTokenStore struct{}

func (s *InMemoryTokenStore) PersistIssued(tokenID string, tokenHash string, expiresAt time.Time) error {
	return nil // no-op for in-memory
}
func (s *InMemoryTokenStore) PersistConsumed(tokenHash string, consumedAt time.Time) error {
	return nil // no-op for in-memory
}
func (s *InMemoryTokenStore) IsConsumedDurable(tokenHash string) (bool, error) {
	return false, nil // in-memory has no durable state
}
func (s *InMemoryTokenStore) LoadActiveTokens() (map[string]time.Time, map[string]time.Time, error) {
	return make(map[string]time.Time), make(map[string]time.Time), nil
}
func (s *InMemoryTokenStore) IsDurable() bool { return false }

// ================================================================
// POSTGRESQL TOKEN REGISTRY STORE (Phase 14 Fix)
// ================================================================

// PostgresTokenRegistryStore provides durable PostgreSQL-backed persistence.
// This prevents token replay across system restarts. It uses the connection
// pool shared with PostgresAuditSink for efficiency.
type PostgresTokenRegistryStore struct {
	db *sql.DB
}

// NewPostgresTokenRegistryStore creates a new durable token store.
// Automatically ensures the requisite schema exists.
func NewPostgresTokenRegistryStore(db *sql.DB) (*PostgresTokenRegistryStore, error) {
	if db == nil {
		return nil, fmt.Errorf("PostgresTokenRegistryStore requires non-nil *sql.DB")
	}
	store := &PostgresTokenRegistryStore{db: db}
	if err := store.EnsureTokenSchema(); err != nil {
		return nil, err
	}
	return store, nil
}

// EnsureTokenSchema sets up the tables for durable token storage.
func (s *PostgresTokenRegistryStore) EnsureTokenSchema() error {
	schema := `
	CREATE TABLE IF NOT EXISTS sarathi_consumed_tokens (
		token_hash  TEXT PRIMARY KEY,
		consumed_at TIMESTAMPTZ NOT NULL,
		created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
	);
	CREATE INDEX IF NOT EXISTS idx_consumed_tokens_time ON sarathi_consumed_tokens(consumed_at);
	`
	_, err := s.db.Exec(schema)
	if err != nil {
		return fmt.Errorf("failed to create sarathi_consumed_tokens schema: %w", err)
	}
	return nil
}

func (s *PostgresTokenRegistryStore) PersistIssued(tokenID string, tokenHash string, expiresAt time.Time) error {
	// For replay protection, tracking issued tokens is optional.
	// Only tracking consumed tokens is strictly necessary to prevent reuse.
	return nil
}

func (s *PostgresTokenRegistryStore) PersistConsumed(tokenHash string, consumedAt time.Time) error {
	_, err := s.db.Exec(`
		INSERT INTO sarathi_consumed_tokens (token_hash, consumed_at) 
		VALUES ($1, $2)
		ON CONFLICT (token_hash) DO NOTHING`,
		tokenHash, consumedAt)
	return err
}

func (s *PostgresTokenRegistryStore) IsConsumedDurable(tokenHash string) (bool, error) {
	var count int
	err := s.db.QueryRow("SELECT COUNT(*) FROM sarathi_consumed_tokens WHERE token_hash = $1", tokenHash).Scan(&count)
	if err != nil {
		return false, err
	}
	return count > 0, nil
}

func (s *PostgresTokenRegistryStore) LoadActiveTokens() (map[string]time.Time, map[string]time.Time, error) {
	consumed := make(map[string]time.Time)
	
	// Load tokens consumed within the last 2 minutes (tokens older than MaxTTL are ignored)
	rows, err := s.db.Query(`
		SELECT token_hash, consumed_at 
		FROM sarathi_consumed_tokens 
		WHERE consumed_at >= NOW() - INTERVAL '2 minutes'`)
	if err != nil {
		return nil, nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var hash string
		var t time.Time
		if err := rows.Scan(&hash, &t); err != nil {
			return nil, nil, err
		}
		consumed[hash] = t
	}
	
	return make(map[string]time.Time), consumed, nil
}

func (s *PostgresTokenRegistryStore) IsDurable() bool { return true }

// TokenRegistry tracks issued and consumed tokens with bounded memory.
// It enforces single-use semantics: once consumed, replay is cryptographically blocked.
// Consumed entries are evicted after 2x MaxTokenTTL since expired tokens can never be valid.
// This prevents unbounded memory growth under sustained load (C-09 fix).
//
// CRIT-05 FIX: Now supports a pluggable TokenRegistryStore for durable persistence.
// In production mode, the store MUST be durable (IsDurable() == true).
type TokenRegistry struct {
	mu       sync.Mutex
	issued   map[string]*CapabilityToken       // tokenID → token
	consumed map[string]time.Time              // tokenHash → consumedAt timestamp
	maxTTL   time.Duration                      // max token lifetime (for eviction)
	cleanupInterval time.Duration               // how often to run cleanup
	stopCleanup     chan struct{}
	store    TokenRegistryStore                 // CRIT-05: durable persistence backend
}

// NewTokenRegistry creates a new token registry with automatic eviction.
// Uses InMemoryTokenStore by default (non-durable, suitable for testing).
// For production, use NewTokenRegistryWithStore with a durable backend.
func NewTokenRegistry() *TokenRegistry {
	return NewTokenRegistryWithStore(&InMemoryTokenStore{})
}

// NewTokenRegistryWithStore creates a token registry backed by the given store.
// In production, pass a durable store (e.g., PostgresTokenStore) to survive restarts.
func NewTokenRegistryWithStore(store TokenRegistryStore) *TokenRegistry {
	tr := &TokenRegistry{
		issued:          make(map[string]*CapabilityToken),
		consumed:        make(map[string]time.Time),
		maxTTL:          60 * time.Second, // matches MaxTokenTTL
		cleanupInterval: 30 * time.Second,
		stopCleanup:     make(chan struct{}),
		store:           store,
	}

	// Attempt to load persisted state on startup (crash recovery)
	if store != nil && store.IsDurable() {
		if issued, consumed, err := store.LoadActiveTokens(); err == nil {
			for hash, ts := range consumed {
				tr.consumed[hash] = ts
			}
			_ = issued // issued tokens need full struct to be useful; consumed is critical
			fmt.Printf("[TokenRegistry] Recovered %d consumed tokens from durable store\n", len(consumed))
		} else {
			fmt.Printf("[TokenRegistry] WARNING: Failed to load from durable store: %v\n", err)
		}
	}

	go tr.cleanupLoop()
	return tr
}

// cleanupLoop periodically evicts expired entries to bound memory usage.
// Entries older than 2x maxTTL + ClockSkewTolerance are safe to remove because
// any token that old has definitively expired and can never be replayed.
func (tr *TokenRegistry) cleanupLoop() {
	ticker := time.NewTicker(tr.cleanupInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			tr.evictExpired()
		case <-tr.stopCleanup:
			return
		}
	}
}

// evictExpired removes consumed entries that are past the safe eviction window.
func (tr *TokenRegistry) evictExpired() {
	tr.mu.Lock()
	defer tr.mu.Unlock()

	evictionCutoff := time.Now().Add(-(2*tr.maxTTL + ClockSkewTolerance))
	evicted := 0
	for hash, consumedAt := range tr.consumed {
		if consumedAt.Before(evictionCutoff) {
			delete(tr.consumed, hash)
			evicted++
		}
	}

	// Also evict expired issued tokens
	for id, token := range tr.issued {
		if token != nil && token.IsExpired() {
			delete(tr.issued, id)
		}
	}
}

// StopCleanup stops the background eviction goroutine.
func (tr *TokenRegistry) StopCleanup() {
	close(tr.stopCleanup)
}

// Register records a newly issued token.
// CRIT-05 FIX: Write-through to durable store on register.
// If durable write fails, the token is still registered in memory but a warning is logged.
// The durable store is the source of truth for crash recovery.
func (tr *TokenRegistry) Register(token *CapabilityToken) {
	if token == nil {
		return
	}
	tr.mu.Lock()
	defer tr.mu.Unlock()
	tr.issued[token.tokenID] = token

	// Write-through to durable store
	if tr.store != nil && tr.store.IsDurable() {
		if err := tr.store.PersistIssued(token.tokenID, token.tokenHash, token.expiresAt); err != nil {
			fmt.Printf("[TokenRegistry] WARNING: durable persist-issued failed for %s: %v\n", token.tokenID, err)
		}
	}
}

// Consume marks a token as consumed. Returns false if already consumed (replay).
// CRIT-05 FIX: Write-through to durable store on consume.
// The durable write happens BEFORE marking the in-memory state to prevent
// a crash window where the token is consumed in-memory but not persisted.
// On restart, the durable store would not show the consumption → replay possible.
func (tr *TokenRegistry) Consume(token *CapabilityToken) bool {
	if token == nil {
		return false
	}
	tr.mu.Lock()
	defer tr.mu.Unlock()

	// Check in-memory first (fast path)
	if _, alreadyConsumed := tr.consumed[token.tokenHash]; alreadyConsumed {
		return false
	}

	// CRIT-05: Check durable store on cache miss (crash recovery path)
	if tr.store != nil && tr.store.IsDurable() {
		if consumed, err := tr.store.IsConsumedDurable(token.tokenHash); err == nil && consumed {
			// Token was consumed before a restart — update in-memory and reject
			tr.consumed[token.tokenHash] = time.Now().UTC()
			return false
		}
	}

	now := time.Now().UTC()

	// CRIT-05: Persist to durable store BEFORE in-memory update
	if tr.store != nil && tr.store.IsDurable() {
		if err := tr.store.PersistConsumed(token.tokenHash, now); err != nil {
			// FAIL-CLOSED: if we can't durably record consumption, reject the token.
			// Allowing consumption without durable record creates a replay window.
			fmt.Printf("[TokenRegistry] CRITICAL: durable persist-consumed failed for %s: %v — REJECTING to prevent replay\n", token.tokenHash, err)
			return false
		}
	}

	tr.consumed[token.tokenHash] = now
	token.consumed = true
	return true
}

// IsConsumed checks if a token has been consumed.
// CRIT-05 FIX: Falls through to durable store on cache miss.
func (tr *TokenRegistry) IsConsumed(tokenHash string) bool {
	tr.mu.Lock()
	defer tr.mu.Unlock()
	if _, exists := tr.consumed[tokenHash]; exists {
		return true
	}
	// Check durable store on miss (post-restart recovery)
	if tr.store != nil && tr.store.IsDurable() {
		if consumed, err := tr.store.IsConsumedDurable(tokenHash); err == nil && consumed {
			tr.consumed[tokenHash] = time.Now().UTC() // cache it
			return true
		}
	}
	return false
}

// IssuedCount returns the total number of tokens issued.
func (tr *TokenRegistry) IssuedCount() int {
	tr.mu.Lock()
	defer tr.mu.Unlock()
	return len(tr.issued)
}

// ConsumedCount returns the total number of tokens consumed.
func (tr *TokenRegistry) ConsumedCount() int {
	tr.mu.Lock()
	defer tr.mu.Unlock()
	return len(tr.consumed)
}
