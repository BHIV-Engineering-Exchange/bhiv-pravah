package main

// external_decision.go — BHIV External Decision Trust Boundary & Enforcement Path.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — External Decision Enforcement (v11.0)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   Implements the BHIV-compliant VERIFICATION + ENFORCEMENT boundary.
//   Sarathi is a PURE ENFORCEMENT LAYER. It does NOT evaluate policy.
//   It does NOT interpret context. It does NOT introduce trust scoring.
//
//   SARATHI'S RESPONSIBILITY (Execution Validity):
//     - Is the decision structurally complete?
//     - Is the evaluator trusted and active?
//     - Is the evaluator's cryptographic signature valid?
//     - Is the decision hash intact (untampered)?
//     - Is the decision unexpired?
//     - Is the decision a replay?
//     - Does the agent pass posture/rate checks?
//     - Is the decision bound to the correct request?
//
//   NOT SARATHI'S RESPONSIBILITY (Decision Correctness):
//     - Was the evaluator's policy logic correct?
//     - Should the agent have been allowed?
//     - Is the evaluator's confidence score valid?
//     - Does the decision align with business rules?
//
// TRUST MODEL:
//   Sarathi trusts ONLY cryptographic proof, not logic.
//   - Evaluator MUST be registered in the EvaluatorTrustRegistry
//   - Evaluator MUST have ACTIVE status
//   - Decision MUST carry Ed25519 signature from the evaluator
//   - Signature MUST verify against the evaluator's registered public key
//   - Decision core hash MUST match the recomputed hash
//   - Decision MUST be unexpired (Timestamp + TTL > now - ClockSkewTolerance)
//   - Decision nonce MUST NOT have been seen before (replay protection)
//   - Decision MUST bind to the request via deterministic hash
//
// BHIV FLOW:
//   Evaluator (Ishan) → signed ExternalDecision → Sarathi VerifyAndEnforce →
//   verification pipeline → enforcement + token → Execution Layer (Raj) → action
//
// ARCHITECTURE PHASES (v11.0 Hardening):
//   Phase 1: Trust Model Definition (verification-only boundary)
//   Phase 2: Evaluator Trust Registry (register/revoke/fetch)
//   Phase 3: Decision Signature System (Ed25519 per-evaluator)
//   Phase 4: Strict Verification Pipeline (exact sequence, no PDP/KSML)
//   Phase 5: Decision-Request Binding (hash commitment contract)
//   Phase 6: Mode Lock + Centralized Guard (immutable in production)
//   Phase 7: End-to-End Flow Validation (deterministic proof)
//
// DESIGN REFERENCES:
//   - RFC 8032: Ed25519 digital signatures for evaluator authentication
//   - NIST 800-207: Zero Trust — PE/PA/PEP separation, never trust, always verify
//   - Google Zanzibar: Capability-based tokens with external authorization
//   - AWS STS: External identity provider federation (trust external decisions)
//   - XACML: PDP/PEP separation — Sarathi = PEP ONLY in external mode
//   - SPIFFE/SPIRE: Workload identity with key-based trust
//   - BeyondCorp: Continuous posture assessment
//   - Bell-LaPadula: Classification-based access control (for internal mode)
//   - HashiCorp Vault: Dynamic secrets + identity-based access
//
// FORBIDDEN OPERATIONS (INVARIANTS):
//   - Sarathi MUST NOT evaluate policies in EXTERNAL mode
//   - Sarathi MUST NOT interpret evaluator context
//   - Sarathi MUST NOT introduce trust scoring
//   - Sarathi MUST NOT add any decision-making logic
//   - All logic MUST remain: deterministic, cryptographic, verifiable

import (
	"bytes"
	"crypto/ed25519"
	"crypto/tls"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"math/rand"
	"net/http"
	"os"
	"strconv"
	"sync"
	"time"

	"github.com/google/uuid"
)

// ================================================================
// PHASE 1: TRUST MODEL DEFINITION
// ================================================================
// Sarathi operates at the EXECUTION VALIDITY boundary.
// It verifies that a decision is structurally sound, cryptographically
// authentic, temporally valid, and non-replayed.
// It does NOT verify DECISION CORRECTNESS — that is the evaluator's domain.
//
// VERIFICATION BOUNDARY:
//   ┌─────────────────────────────────────────────────────┐
//   │ EXECUTION VALIDITY (Sarathi's Responsibility)       │
//   │                                                     │
//   │  ✓ Structure complete (all required fields present) │
//   │  ✓ Evaluator trusted (in registry, ACTIVE status)  │
//   │  ✓ Signature valid (Ed25519 from evaluator key)    │
//   │  ✓ Hash intact (SHA-256 over binding fields)       │
//   │  ✓ Unexpired (Timestamp + TTL > now - skew)        │
//   │  ✓ Non-replayed (nonce not seen before)            │
//   │  ✓ Agent posture OK (BeyondCorp check)             │
//   │  ✓ Rate limit OK (per-agent + global)              │
//   │  ✓ Request binding valid (hash commitment)         │
//   └─────────────────────────────────────────────────────┘
//
//   ┌─────────────────────────────────────────────────────┐
//   │ DECISION CORRECTNESS (NOT Sarathi's Responsibility) │
//   │                                                     │
//   │  ✗ Policy logic evaluation                          │
//   │  ✗ Context interpretation                           │
//   │  ✗ Trust scoring                                    │
//   │  ✗ Business rule validation                         │
//   │  ✗ Confidence assessment                            │
//   │  ✗ Agent capability evaluation                      │
//   └─────────────────────────────────────────────────────┘

// VerificationStage identifies which stage of the verification pipeline
// produced a result. Every verification step is named and auditable.
type VerificationStage string

const (
	StageStructureCheck         VerificationStage = "STRUCTURE_CHECK"
	StageEvaluatorTrustCheck    VerificationStage = "EVALUATOR_TRUST_CHECK"
	StageSignatureVerification  VerificationStage = "SIGNATURE_VERIFICATION"
	StageIntegrityCheck         VerificationStage = "INTEGRITY_CHECK"
	StageExpiryCheck            VerificationStage = "EXPIRY_CHECK"
	StageReplayCheck            VerificationStage = "REPLAY_CHECK"
	StageRateLimitCheck         VerificationStage = "RATE_LIMIT_CHECK"
	StagePostureCheck           VerificationStage = "POSTURE_CHECK"
	StageBindingCheck           VerificationStage = "BINDING_CHECK"
	StageModeCheck              VerificationStage = "MODE_CHECK"
	StageVerificationComplete   VerificationStage = "VERIFICATION_COMPLETE"
)

// VerificationResult records the outcome of a single verification stage.
// Every stage produces one of these, creating a full audit trail.
type VerificationResult struct {
	Stage     VerificationStage `json:"stage"`
	Passed    bool              `json:"passed"`
	Reason    string            `json:"reason"`
	Timestamp time.Time         `json:"timestamp"`
	Detail    string            `json:"detail,omitempty"`
}

// VerificationTrace is the complete audit trail of a verification pipeline run.
// It records every stage, whether it passed or failed, and the final verdict.
type VerificationTrace struct {
	DecisionID    string               `json:"decision_id"`
	EvaluatorID   string               `json:"evaluator_id"`
	CorrelationID string               `json:"correlation_id"`
	StartedAt     time.Time            `json:"started_at"`
	CompletedAt   time.Time            `json:"completed_at"`
	Results       []VerificationResult `json:"results"`
	FinalVerdict  string               `json:"final_verdict"` // "VERIFIED" or "REJECTED"
	FailedStage   VerificationStage    `json:"failed_stage,omitempty"`
	FailedReason  string               `json:"failed_reason,omitempty"`
}

// ================================================================
// PHASE 1 (continued): EXTERNAL DECISION MODEL
// ================================================================
// Independent of KSML and PDP. This is the decision structure that
// the Evaluator (Ishan) produces and Sarathi verifies + enforces.

// ExternalDecisionVerdict represents the possible verdicts from an external evaluator.
type ExternalDecisionVerdict string

const (
	ExternalVerdictAllow    ExternalDecisionVerdict = "ALLOW"
	ExternalVerdictDeny     ExternalDecisionVerdict = "DENY"
	ExternalVerdictEscalate ExternalDecisionVerdict = "ESCALATE"
)

// ExternalDecision is the canonical decision structure from an external evaluator.
// This model is completely independent of KSML and PDP — it represents a
// pre-computed authorization decision that Sarathi must VERIFY and ENFORCE
// without re-evaluating the policy logic.
//
// IMMUTABILITY: All fields are set at construction. No setter methods exist.
// INTEGRITY: DecisionHash is computed over all binding fields at creation.
// AUTHENTICITY: EvaluatorSignature is Ed25519 signed by the evaluator's private key.
// BINDING: DecisionCoreHash binds the decision to the specific request fields.
type ExternalDecision struct {
	// Core identity
	DecisionID  string `json:"decision_id"`  // Unique decision identifier (UUID)
	EvaluatorID string `json:"evaluator_id"` // Which evaluator produced this decision — MUST map to trusted registry

	// Request binding — what action this decision authorizes
	AgentID    string `json:"agent_id"`    // The agent requesting action
	ResourceID string `json:"resource_id"` // The target resource
	Action     string `json:"action"`      // The action (read/write/execute/delete)

	// Decision
	Verdict     ExternalDecisionVerdict `json:"verdict"`     // ALLOW / DENY / ESCALATE
	Obligations []string                `json:"obligations"` // Mandatory side-effects

	// Metadata
	Timestamp time.Time         `json:"timestamp"`  // When the decision was made
	TTL       time.Duration     `json:"ttl"`        // How long the decision is valid
	ExpiresAt time.Time         `json:"expires_at"` // Computed: Timestamp + TTL
	Metadata  map[string]string `json:"metadata"`   // Additional context from evaluator
	Reason    string            `json:"reason"`     // Human-readable decision reason

	// Integrity — SHA-256 over all binding fields
	DecisionHash string `json:"decision_hash"` // SHA-256 over all binding fields

	// Replay protection
	Nonce string `json:"nonce"` // Replay protection nonce (UUID)

	// PHASE 3: Cryptographic authenticity — Ed25519 evaluator signature
	// The evaluator signs the DecisionCoreHash with their private key.
	// Sarathi verifies this signature using the evaluator's registered public key.
	// Without a valid signature from a trusted evaluator, the decision is REJECTED.
	EvaluatorSignature    []byte `json:"evaluator_signature"`     // Ed25519 signature over DecisionCoreHash
	EvaluatorSignatureHex string `json:"evaluator_signature_hex"` // Hex representation for logging/transport

	// PHASE 5: Decision-Request binding hash
	// Deterministic hash over (decision_id, evaluator_id, agent_id, resource_id, action, verdict, timestamp, nonce).
	// This binds the decision to the EXACT request it authorizes.
	// The token issued by Sarathi carries this hash — if the request drifts from the decision, enforcement fails.
	DecisionCoreHash string `json:"decision_core_hash"` // SHA-256 binding hash
}

// externalDecisionHashPayload is the struct for deterministic full-decision hash computation.
// Mirrors GAP-17 pattern from existing system.
// CRITICAL: This covers ALL decision fields — including obligations, reason, TTL, and metadata.
// This is intentionally DIFFERENT from decisionCoreHashPayload which covers only binding fields.
// DecisionHash = full tamper-detection (integrity check, Step 5)
// DecisionCoreHash = request-binding verification (binding check, Step 10) + evaluator signature
type externalDecisionHashPayload struct {
	DecisionID   string            `json:"decision_id"`
	EvaluatorID  string            `json:"evaluator_id"`
	AgentID      string            `json:"agent_id"`
	ResourceID   string            `json:"resource_id"`
	Action       string            `json:"action"`
	Verdict      string            `json:"verdict"`
	Timestamp    string            `json:"timestamp"`
	Nonce        string            `json:"nonce"`
	Obligations  []string          `json:"obligations"`
	Reason       string            `json:"reason"`
	TTLSeconds   float64           `json:"ttl_seconds"`
	MetadataHash string            `json:"metadata_hash"`
}

// decisionCoreHashPayload is the struct for the decision-request binding hash.
// This is the payload that the evaluator signs with Ed25519.
// It contains ONLY the fields that bind the decision to a specific request.
// Phase 5: request_hash = SHA256(decision_core_fields)
type decisionCoreHashPayload struct {
	DecisionID  string `json:"decision_id"`
	EvaluatorID string `json:"evaluator_id"`
	AgentID     string `json:"agent_id"`
	ResourceID  string `json:"resource_id"`
	Action      string `json:"action"`
	Verdict     string `json:"verdict"`
	Timestamp   string `json:"timestamp"`
	Nonce       string `json:"nonce"`
}

// NewExternalDecision creates an immutable external decision with computed hash.
// This is the ONLY constructor for evaluator-side decision creation.
// The decision is created WITHOUT a signature — the evaluator must sign it separately
// using SignDecision().
func NewExternalDecision(
	evaluatorID, agentID, resourceID, action string,
	verdict ExternalDecisionVerdict,
	obligations []string,
	metadata map[string]string,
	reason string,
	ttl time.Duration,
) *ExternalDecision {
	now := time.Now().UTC()
	if ttl <= 0 {
		ttl = 30 * time.Second // Default TTL matches DefaultDecisionTTL
	}
	if obligations == nil {
		obligations = []string{}
	}
	if metadata == nil {
		metadata = make(map[string]string)
	}

	d := &ExternalDecision{
		DecisionID:  uuid.New().String(),
		EvaluatorID: evaluatorID,
		AgentID:     agentID,
		ResourceID:  resourceID,
		Action:      action,
		Verdict:     verdict,
		Obligations: obligations,
		Timestamp:   now,
		TTL:         ttl,
		ExpiresAt:   now.Add(ttl),
		Metadata:    metadata,
		Reason:      reason,
		Nonce:       uuid.New().String(),
	}
	d.DecisionHash = d.computeHash()
	d.DecisionCoreHash = d.computeCoreHash()
	return d
}

// computeHash computes SHA-256 over ALL decision fields using struct serialization.
// This is the FULL INTEGRITY hash — covers binding fields PLUS obligations, reason, TTL, metadata.
// Used in STEP 5 (integrity check) to detect ANY tamper to ANY field.
// This is intentionally different from computeCoreHash() which only covers binding fields.
func (d *ExternalDecision) computeHash() string {
	// Compute deterministic metadata hash (sorted keys for reproducibility)
	metadataHash := ""
	if len(d.Metadata) > 0 {
		metaBytes, err := json.Marshal(d.Metadata)
		if err == nil {
			metadataHash = Sha256Hex(metaBytes)
		}
	}
	payload := externalDecisionHashPayload{
		DecisionID:   d.DecisionID,
		EvaluatorID:  d.EvaluatorID,
		AgentID:      d.AgentID,
		ResourceID:   d.ResourceID,
		Action:       d.Action,
		Verdict:      string(d.Verdict),
		Timestamp:    d.Timestamp.Format("2006-01-02T15:04:05.000000Z"),
		Nonce:        d.Nonce,
		Obligations:  d.Obligations,
		Reason:       d.Reason,
		TTLSeconds:   d.TTL.Seconds(),
		MetadataHash: metadataHash,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return Sha256Hex([]byte(fmt.Sprintf("EXT_DECISION_HASH_ERROR:%s:%v", d.DecisionID, err)))
	}
	return Sha256Hex(data)
}

// computeCoreHash computes the decision-request binding hash.
// This is the hash that the evaluator signs. It binds the decision
// to the exact request fields (agent, resource, action, verdict).
// Phase 5: request_hash = SHA256(decision_core_fields)
func (d *ExternalDecision) computeCoreHash() string {
	payload := decisionCoreHashPayload{
		DecisionID:  d.DecisionID,
		EvaluatorID: d.EvaluatorID,
		AgentID:     d.AgentID,
		ResourceID:  d.ResourceID,
		Action:      d.Action,
		Verdict:     string(d.Verdict),
		Timestamp:   d.Timestamp.Format("2006-01-02T15:04:05.000000Z"),
		Nonce:       d.Nonce,
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return Sha256Hex([]byte(fmt.Sprintf("EXT_DECISION_CORE_HASH_ERROR:%s:%v", d.DecisionID, err)))
	}
	return Sha256Hex(data)
}

// SignDecision signs the decision's core hash with the evaluator's Ed25519 private key.
// This MUST be called by the evaluator after creating the decision.
// The signature covers DecisionCoreHash, which itself covers all binding fields.
// Chain: binding fields → SHA-256 core hash → Ed25519 signature
func (d *ExternalDecision) SignDecision(privateKey ed25519.PrivateKey) {
	message := []byte(d.DecisionCoreHash)
	d.EvaluatorSignature = ed25519.Sign(privateKey, message)
	d.EvaluatorSignatureHex = hex.EncodeToString(d.EvaluatorSignature)
}

// VerifySignature verifies the decision's Ed25519 signature against the provided public key.
// Returns (valid, reason). This is called by Sarathi during the verification pipeline.
func (d *ExternalDecision) VerifySignature(publicKey ed25519.PublicKey) (bool, string) {
	if len(d.EvaluatorSignature) == 0 {
		return false, "SIGNATURE_MISSING: decision has no evaluator signature"
	}
	if len(publicKey) == 0 {
		return false, "PUBLIC_KEY_MISSING: evaluator public key not provided"
	}

	// Recompute core hash to verify against
	expectedCoreHash := d.computeCoreHash()
	if d.DecisionCoreHash != expectedCoreHash {
		return false, fmt.Sprintf("CORE_HASH_MISMATCH: stored=%s computed=%s", d.DecisionCoreHash[:16], expectedCoreHash[:16])
	}

	message := []byte(d.DecisionCoreHash)
	if !ed25519.Verify(publicKey, message, d.EvaluatorSignature) {
		return false, "SIGNATURE_INVALID: Ed25519 verification failed — decision not from claimed evaluator"
	}
	return true, "SIGNATURE_VALID"
}

// IsExpired returns true if the decision's TTL has elapsed (including clock skew tolerance).
func (d *ExternalDecision) IsExpired() bool {
	return time.Now().UTC().After(d.ExpiresAt.Add(ClockSkewTolerance))
}

// VerifyIntegrity recomputes the hash and compares to stored value.
func (d *ExternalDecision) VerifyIntegrity() bool {
	return d.DecisionHash == d.computeHash()
}

// VerifyCoreHashIntegrity recomputes the core binding hash and compares to stored value.
func (d *ExternalDecision) VerifyCoreHashIntegrity() bool {
	return d.DecisionCoreHash == d.computeCoreHash()
}

// ValidateStructure performs structural validation of the external decision.
// This checks ONLY structure — NOT signature, NOT evaluator trust, NOT expiry.
// Returns nil if valid, error describing the problem otherwise.
// Named ValidateStructure (not Validate) to make clear this is EXECUTION VALIDITY only.
func (d *ExternalDecision) ValidateStructure() error {
	if d == nil {
		return fmt.Errorf("STRUCTURE_INVALID: decision is nil")
	}
	if d.DecisionID == "" {
		return fmt.Errorf("STRUCTURE_INVALID: missing decision_id")
	}
	if d.EvaluatorID == "" {
		return fmt.Errorf("STRUCTURE_INVALID: missing evaluator_id")
	}
	if d.AgentID == "" {
		return fmt.Errorf("STRUCTURE_INVALID: missing agent_id")
	}
	if d.ResourceID == "" {
		return fmt.Errorf("STRUCTURE_INVALID: missing resource_id")
	}
	if d.Action == "" {
		return fmt.Errorf("STRUCTURE_INVALID: missing action")
	}
	validActions := map[string]bool{"read": true, "write": true, "execute": true, "delete": true}
	if !validActions[d.Action] {
		return fmt.Errorf("STRUCTURE_INVALID: invalid action '%s' (must be read/write/execute/delete)", d.Action)
	}
	if d.Verdict != ExternalVerdictAllow && d.Verdict != ExternalVerdictDeny && d.Verdict != ExternalVerdictEscalate {
		return fmt.Errorf("STRUCTURE_INVALID: invalid verdict '%s' (must be ALLOW/DENY/ESCALATE)", d.Verdict)
	}
	if d.DecisionHash == "" {
		return fmt.Errorf("STRUCTURE_INVALID: missing decision_hash")
	}
	if d.Nonce == "" {
		return fmt.Errorf("STRUCTURE_INVALID: missing nonce")
	}
	if d.DecisionCoreHash == "" {
		return fmt.Errorf("STRUCTURE_INVALID: missing decision_core_hash")
	}
	if len(d.EvaluatorSignature) == 0 {
		return fmt.Errorf("STRUCTURE_INVALID: missing evaluator_signature (decision must be signed)")
	}
	return nil
}

// Validate performs full structural validation including integrity and expiry.
// This is the LEGACY method for backward compatibility. New code should use
// the verification pipeline which calls each check separately.
func (d *ExternalDecision) Validate() error {
	if err := d.ValidateStructure(); err != nil {
		return err
	}
	if !d.VerifyIntegrity() {
		return fmt.Errorf("EXTERNAL_DECISION_INTEGRITY_FAILED")
	}
	if !d.VerifyCoreHashIntegrity() {
		return fmt.Errorf("EXTERNAL_DECISION_CORE_HASH_INTEGRITY_FAILED")
	}
	if d.IsExpired() {
		return fmt.Errorf("EXTERNAL_DECISION_EXPIRED: expires_at=%s", d.ExpiresAt.Format(time.RFC3339))
	}
	return nil
}

// ToJSON returns the decision as a JSON byte slice.
func (d *ExternalDecision) ToJSON() ([]byte, error) {
	return json.MarshalIndent(d, "", "  ")
}

// ToMap returns a read-only map for logging/tracing.
func (d *ExternalDecision) ToMap() map[string]interface{} {
	return map[string]interface{}{
		"decision_id":        d.DecisionID,
		"evaluator_id":       d.EvaluatorID,
		"agent_id":           d.AgentID,
		"resource_id":        d.ResourceID,
		"action":             d.Action,
		"verdict":            string(d.Verdict),
		"obligations":        d.Obligations,
		"timestamp":          d.Timestamp.Format("2006-01-02T15:04:05.000000Z"),
		"expires_at":         d.ExpiresAt.Format("2006-01-02T15:04:05.000000Z"),
		"decision_hash":      d.DecisionHash,
		"decision_core_hash": d.DecisionCoreHash,
		"nonce":              d.Nonce,
		"reason":             d.Reason,
		"metadata":           d.Metadata,
		"has_signature":      len(d.EvaluatorSignature) > 0,
		"signature_hex":      d.EvaluatorSignatureHex,
	}
}

// ================================================================
// PHASE 2: EVALUATOR TRUST REGISTRY
// ================================================================
// Production-grade registry of trusted evaluators. Only evaluators
// registered here with ACTIVE status can produce decisions that
// Sarathi will enforce. This closes ISSUE 2 — evaluator trust binding.
//
// DESIGN: Mirrors SPIFFE/SPIRE workload identity pattern.
// Each evaluator has an Ed25519 public key registered at trust time.
// Sarathi uses ONLY the public key to verify signatures.
// The private key is NEVER stored in Sarathi — it stays with the evaluator.
//
// LIFECYCLE: REGISTERED → ACTIVE → SUSPENDED → REVOKED
// Once REVOKED, an evaluator cannot be re-activated.
// SUSPENDED evaluators can be re-activated by privileged action.

// EvaluatorStatus defines the lifecycle states of an evaluator.
type EvaluatorStatus string

const (
	EvaluatorStatusActive    EvaluatorStatus = "ACTIVE"
	EvaluatorStatusSuspended EvaluatorStatus = "SUSPENDED"
	EvaluatorStatusRevoked   EvaluatorStatus = "REVOKED"
)

// EvaluatorRecord is a single evaluator's trust record in the registry.
// It holds the evaluator's identity, public key, and lifecycle state.
type EvaluatorRecord struct {
	EvaluatorID string              `json:"evaluator_id"` // Unique evaluator identifier
	Name        string              `json:"name"`         // Human-readable name
	Status      EvaluatorStatus     `json:"status"`       // ACTIVE / SUSPENDED / REVOKED
	PublicKey   ed25519.PublicKey    `json:"public_key"`   // Ed25519 public key for signature verification
	PublicKeyHex string             `json:"public_key_hex"` // Hex representation for logging/transport
	RegisteredAt time.Time          `json:"registered_at"`
	LastActiveAt time.Time          `json:"last_active_at"`
	SuspendedAt  *time.Time         `json:"suspended_at,omitempty"`
	RevokedAt    *time.Time         `json:"revoked_at,omitempty"`
	RevokeReason string             `json:"revoke_reason,omitempty"`
	Metadata     map[string]string  `json:"metadata"` // Additional evaluator metadata
	// Key rotation: list of previously active keys with grace period
	PreviousKeys []EvaluatorKeyVersion `json:"previous_keys,omitempty"`

	// Phase 12 (External Evaluator Hardening — additive, backward compatible):
	// KeyFingerprint is a compact identifier for the current public key
	// (first 16 bytes of SHA-256 over the raw public key). Used in logs
	// and idempotency checks. Zero value = not set (legacy records).
	KeyFingerprint string `json:"key_fingerprint,omitempty"`
	// ExpiresAt, if non-nil, enforces a per-evaluator crypto period (NIST SP 800-57).
	// GetActiveEvaluator returns EVALUATOR_KEY_EXPIRED once this instant has passed.
	// Zero value = no expiry (preserves legacy behaviour for existing records).
	ExpiresAt *time.Time `json:"expires_at,omitempty"`
}

// EvaluatorKeyVersion represents a historical public key for key rotation support.
// During key rotation, the old key remains valid for a grace period.
type EvaluatorKeyVersion struct {
	PublicKey    ed25519.PublicKey `json:"public_key"`
	PublicKeyHex string           `json:"public_key_hex"`
	ActiveFrom   time.Time        `json:"active_from"`
	DeactivatedAt time.Time       `json:"deactivated_at"`
	GraceExpiresAt time.Time     `json:"grace_expires_at"` // Old key accepted until this time
}

// EvaluatorRegistryEvent records changes to the registry for audit.
type EvaluatorRegistryEvent struct {
	EventID     string          `json:"event_id"`
	EventType   string          `json:"event_type"` // REGISTER, ACTIVATE, SUSPEND, REVOKE, KEY_ROTATE
	EvaluatorID string          `json:"evaluator_id"`
	Timestamp   time.Time       `json:"timestamp"`
	Initiator   string          `json:"initiator"` // Who performed the action
	Reason      string          `json:"reason"`
	Detail      string          `json:"detail,omitempty"`
}

// EvaluatorTrustRegistry is the production registry of trusted evaluators.
// Thread-safe. Append-only audit log. Only ACTIVE evaluators can have
// their decisions enforced by Sarathi.
type EvaluatorTrustRegistry struct {
	mu          sync.RWMutex
	evaluators  map[string]*EvaluatorRecord    // evaluator_id → record
	eventLog    []EvaluatorRegistryEvent        // Append-only audit log

	// Phase 12 (External Evaluator Hardening — additive, backward compatible).
	// These fields are nil/zero by default so untouched code paths behave
	// exactly as they did in v11. They are wired by evaluator_registry_extension.go.
	store       EvaluatorRegistryStore        // Persistence backend; nil → in-memory only
	adminAuth   *EvaluatorAdminAuthenticator  // Admin Ed25519 authenticator; nil → admin API disabled
	challenges  *evaluatorChallengeStore      // PoP challenge pool; nil → PoP path disabled
	clock       Clock                         // Injectable clock for tests; nil → RealClock
	version     uint64                        // Consistency version — bumped on every mutation
	prevEventHash string                      // Tamper-evident chain head for registry events
	metadataAllowList map[string]bool         // Optional allow-list for metadata keys
}

// NewEvaluatorTrustRegistry creates an empty evaluator registry.
func NewEvaluatorTrustRegistry() *EvaluatorTrustRegistry {
	return &EvaluatorTrustRegistry{
		evaluators: make(map[string]*EvaluatorRecord),
		eventLog:   make([]EvaluatorRegistryEvent, 0),
	}
}

// RegisterEvaluator adds a new evaluator to the trust registry.
// The evaluator starts in ACTIVE status. The public key is stored for
// future signature verification. Returns error if evaluator already exists.
func (r *EvaluatorTrustRegistry) RegisterEvaluator(
	evaluatorID, name string,
	publicKey ed25519.PublicKey,
	metadata map[string]string,
	initiator string,
) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if _, exists := r.evaluators[evaluatorID]; exists {
		return fmt.Errorf("EVALUATOR_ALREADY_EXISTS: %s", evaluatorID)
	}
	if len(publicKey) != ed25519.PublicKeySize {
		return fmt.Errorf("INVALID_PUBLIC_KEY: expected %d bytes, got %d", ed25519.PublicKeySize, len(publicKey))
	}
	if metadata == nil {
		metadata = make(map[string]string)
	}

	now := time.Now().UTC()
	r.evaluators[evaluatorID] = &EvaluatorRecord{
		EvaluatorID:  evaluatorID,
		Name:         name,
		Status:       EvaluatorStatusActive,
		PublicKey:     publicKey,
		PublicKeyHex: hex.EncodeToString(publicKey),
		RegisteredAt: now,
		LastActiveAt: now,
		Metadata:     metadata,
		PreviousKeys: make([]EvaluatorKeyVersion, 0),
	}

	r.eventLog = append(r.eventLog, EvaluatorRegistryEvent{
		EventID:     uuid.New().String(),
		EventType:   "REGISTER",
		EvaluatorID: evaluatorID,
		Timestamp:   now,
		Initiator:   initiator,
		Reason:      fmt.Sprintf("Evaluator '%s' registered with Ed25519 public key", name),
		Detail:      fmt.Sprintf("public_key=%s", hex.EncodeToString(publicKey)[:16]),
	})
	return nil
}

// GetEvaluator returns the evaluator record by ID.
// Returns (record, found). Does NOT check status — caller must verify.
func (r *EvaluatorTrustRegistry) GetEvaluator(evaluatorID string) (*EvaluatorRecord, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	rec, found := r.evaluators[evaluatorID]
	return rec, found
}

// GetActiveEvaluator returns the evaluator ONLY if it exists AND has ACTIVE status.
// This is the primary lookup used by the verification pipeline.
// Returns (record, error). Error describes why the evaluator is not trusted.
func (r *EvaluatorTrustRegistry) GetActiveEvaluator(evaluatorID string) (*EvaluatorRecord, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	rec, found := r.evaluators[evaluatorID]
	if !found {
		return nil, fmt.Errorf("EVALUATOR_NOT_FOUND: '%s' is not registered in the trust registry", evaluatorID)
	}
	if rec.Status == EvaluatorStatusRevoked {
		return nil, fmt.Errorf("EVALUATOR_REVOKED: '%s' was revoked at %s reason=%s",
			evaluatorID, rec.RevokedAt.Format(time.RFC3339), rec.RevokeReason)
	}
	if rec.Status == EvaluatorStatusSuspended {
		return nil, fmt.Errorf("EVALUATOR_SUSPENDED: '%s' was suspended at %s",
			evaluatorID, rec.SuspendedAt.Format(time.RFC3339))
	}
	if rec.Status != EvaluatorStatusActive {
		return nil, fmt.Errorf("EVALUATOR_NOT_ACTIVE: '%s' has status '%s'", evaluatorID, rec.Status)
	}

	// Phase 12 (External Evaluator Hardening): per-evaluator key crypto period.
	// Additive — legacy records have ExpiresAt == nil and are unaffected.
	if rec.ExpiresAt != nil {
		now := time.Now().UTC()
		if r.clock != nil {
			now = r.clock.NowUTC()
		}
		if now.After(*rec.ExpiresAt) {
			return nil, fmt.Errorf("EVALUATOR_KEY_EXPIRED: '%s' key expired at %s (NIST SP 800-57 crypto period)",
				evaluatorID, rec.ExpiresAt.Format(time.RFC3339))
		}
	}

	return rec, nil
}

// SuspendEvaluator sets an evaluator to SUSPENDED status.
// Suspended evaluators' decisions are rejected. Can be re-activated.
func (r *EvaluatorTrustRegistry) SuspendEvaluator(evaluatorID, reason, initiator string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	rec, found := r.evaluators[evaluatorID]
	if !found {
		return fmt.Errorf("EVALUATOR_NOT_FOUND: %s", evaluatorID)
	}
	if rec.Status == EvaluatorStatusRevoked {
		return fmt.Errorf("EVALUATOR_ALREADY_REVOKED: cannot suspend a revoked evaluator")
	}

	now := time.Now().UTC()
	rec.Status = EvaluatorStatusSuspended
	rec.SuspendedAt = &now

	r.eventLog = append(r.eventLog, EvaluatorRegistryEvent{
		EventID:     uuid.New().String(),
		EventType:   "SUSPEND",
		EvaluatorID: evaluatorID,
		Timestamp:   now,
		Initiator:   initiator,
		Reason:      reason,
	})
	return nil
}

// ReactivateEvaluator moves a SUSPENDED evaluator back to ACTIVE.
func (r *EvaluatorTrustRegistry) ReactivateEvaluator(evaluatorID, reason, initiator string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	rec, found := r.evaluators[evaluatorID]
	if !found {
		return fmt.Errorf("EVALUATOR_NOT_FOUND: %s", evaluatorID)
	}
	if rec.Status != EvaluatorStatusSuspended {
		return fmt.Errorf("EVALUATOR_NOT_SUSPENDED: current status is '%s'", rec.Status)
	}

	now := time.Now().UTC()
	rec.Status = EvaluatorStatusActive
	rec.SuspendedAt = nil
	rec.LastActiveAt = now

	r.eventLog = append(r.eventLog, EvaluatorRegistryEvent{
		EventID:     uuid.New().String(),
		EventType:   "REACTIVATE",
		EvaluatorID: evaluatorID,
		Timestamp:   now,
		Initiator:   initiator,
		Reason:      reason,
	})
	return nil
}

// RevokeEvaluator permanently revokes an evaluator. This is IRREVERSIBLE.
// Once revoked, the evaluator can never produce trusted decisions again.
func (r *EvaluatorTrustRegistry) RevokeEvaluator(evaluatorID, reason, initiator string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	rec, found := r.evaluators[evaluatorID]
	if !found {
		return fmt.Errorf("EVALUATOR_NOT_FOUND: %s", evaluatorID)
	}
	if rec.Status == EvaluatorStatusRevoked {
		return fmt.Errorf("EVALUATOR_ALREADY_REVOKED: %s", evaluatorID)
	}

	now := time.Now().UTC()
	rec.Status = EvaluatorStatusRevoked
	rec.RevokedAt = &now
	rec.RevokeReason = reason

	r.eventLog = append(r.eventLog, EvaluatorRegistryEvent{
		EventID:     uuid.New().String(),
		EventType:   "REVOKE",
		EvaluatorID: evaluatorID,
		Timestamp:   now,
		Initiator:   initiator,
		Reason:      reason,
	})
	return nil
}

// RotateKey replaces the evaluator's public key, keeping the old key valid
// for the specified grace period. During the grace period, signatures from
// EITHER key are accepted.
func (r *EvaluatorTrustRegistry) RotateKey(
	evaluatorID string,
	newPublicKey ed25519.PublicKey,
	gracePeriod time.Duration,
	initiator string,
) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	rec, found := r.evaluators[evaluatorID]
	if !found {
		return fmt.Errorf("EVALUATOR_NOT_FOUND: %s", evaluatorID)
	}
	if rec.Status != EvaluatorStatusActive {
		return fmt.Errorf("EVALUATOR_NOT_ACTIVE: cannot rotate key for status '%s'", rec.Status)
	}
	if len(newPublicKey) != ed25519.PublicKeySize {
		return fmt.Errorf("INVALID_PUBLIC_KEY: expected %d bytes, got %d", ed25519.PublicKeySize, len(newPublicKey))
	}

	now := time.Now().UTC()

	// Archive current key with grace period
	rec.PreviousKeys = append(rec.PreviousKeys, EvaluatorKeyVersion{
		PublicKey:      rec.PublicKey,
		PublicKeyHex:   rec.PublicKeyHex,
		ActiveFrom:     rec.RegisteredAt,
		DeactivatedAt:  now,
		GraceExpiresAt: now.Add(gracePeriod),
	})

	// Install new key
	rec.PublicKey = newPublicKey
	rec.PublicKeyHex = hex.EncodeToString(newPublicKey)
	rec.LastActiveAt = now

	r.eventLog = append(r.eventLog, EvaluatorRegistryEvent{
		EventID:     uuid.New().String(),
		EventType:   "KEY_ROTATE",
		EvaluatorID: evaluatorID,
		Timestamp:   now,
		Initiator:   initiator,
		Reason:      fmt.Sprintf("Key rotated, grace period=%v", gracePeriod),
		Detail:      fmt.Sprintf("new_key=%s", hex.EncodeToString(newPublicKey)[:16]),
	})
	return nil
}

// VerifySignatureWithRotation verifies a signature against the evaluator's
// current key AND any previous keys still within their grace period.
// Returns (valid, key_source, reason).
// NOTE: Uses full Lock() not RLock() because successful verification updates LastActiveAt.
// GAP-2 FIX: Writing rec.LastActiveAt under RLock was a data race.
func (r *EvaluatorTrustRegistry) VerifySignatureWithRotation(
	evaluatorID string, message, signature []byte,
) (bool, string, string) {
	r.mu.Lock()
	defer r.mu.Unlock()

	rec, found := r.evaluators[evaluatorID]
	if !found {
		return false, "", "EVALUATOR_NOT_FOUND"
	}
	if rec.Status != EvaluatorStatusActive {
		return false, "", fmt.Sprintf("EVALUATOR_NOT_ACTIVE: status=%s", rec.Status)
	}

	// Try current key first
	if ed25519.Verify(rec.PublicKey, message, signature) {
		rec.LastActiveAt = time.Now().UTC()
		return true, "CURRENT_KEY", "SIGNATURE_VALID"
	}

	// Try previous keys within grace period
	now := time.Now().UTC()
	for i, kv := range rec.PreviousKeys {
		if now.Before(kv.GraceExpiresAt) {
			if ed25519.Verify(kv.PublicKey, message, signature) {
				rec.LastActiveAt = now
				return true, fmt.Sprintf("PREVIOUS_KEY_%d", i), "SIGNATURE_VALID_GRACE_PERIOD"
			}
		}
	}

	return false, "", "SIGNATURE_INVALID: no matching key found (current + grace period keys checked)"
}

// GetEventLog returns a copy of the audit event log.
func (r *EvaluatorTrustRegistry) GetEventLog() []EvaluatorRegistryEvent {
	r.mu.RLock()
	defer r.mu.RUnlock()
	cp := make([]EvaluatorRegistryEvent, len(r.eventLog))
	copy(cp, r.eventLog)
	return cp
}

// EvaluatorCount returns the total number of registered evaluators.
func (r *EvaluatorTrustRegistry) EvaluatorCount() int {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return len(r.evaluators)
}

// ActiveEvaluatorCount returns the number of ACTIVE evaluators.
func (r *EvaluatorTrustRegistry) ActiveEvaluatorCount() int {
	r.mu.RLock()
	defer r.mu.RUnlock()
	count := 0
	for _, rec := range r.evaluators {
		if rec.Status == EvaluatorStatusActive {
			count++
		}
	}
	return count
}

// ListEvaluators returns a summary map of all evaluators for debugging/audit.
func (r *EvaluatorTrustRegistry) ListEvaluators() []map[string]interface{} {
	r.mu.RLock()
	defer r.mu.RUnlock()
	result := make([]map[string]interface{}, 0, len(r.evaluators))
	for _, rec := range r.evaluators {
		m := map[string]interface{}{
			"evaluator_id":   rec.EvaluatorID,
			"name":           rec.Name,
			"status":         string(rec.Status),
			"public_key_hex": rec.PublicKeyHex[:16] + "...",
			"registered_at":  rec.RegisteredAt.Format(time.RFC3339),
			"last_active_at": rec.LastActiveAt.Format(time.RFC3339),
			"previous_keys":  len(rec.PreviousKeys),
		}
		result = append(result, m)
	}
	return result
}

// ================================================================
// PHASE 3: MODE SEPARATION (EXTERNAL | INTERNAL) + PHASE 6: MODE LOCK
// ================================================================
// System-level mode that determines whether Sarathi operates as a
// full decision+enforcement system (INTERNAL) or as a pure enforcement
// layer for externally computed decisions (EXTERNAL).
//
// ISSUE 3 FIX: Mode is now LOCKABLE in production.
// When locked, mode cannot be changed at runtime — preventing
// an attacker from switching to INTERNAL to regain PDP control.

// BHIVDecisionMode defines whether the system accepts external decisions
// or generates its own via PDP/KSML. Named BHIVDecisionMode to avoid
// conflict with the existing EnforcementMode (ENFORCE/ADVISORY/DRY_RUN)
// in governance_hardening.go.
type BHIVDecisionMode string

const (
	// BHIVModeExternal: Sarathi acts as pure verification + enforcement layer.
	// PDP MUST NOT execute. KSML MUST NOT execute. GovernanceKernel MUST NOT decide.
	// Only externally signed decisions are verified and enforced.
	BHIVModeExternal BHIVDecisionMode = "EXTERNAL"

	// BHIVModeInternal: Sarathi operates as full decision+enforcement system.
	// PDP, KSML, and GovernanceKernel operate normally.
	// This is the existing behavior.
	BHIVModeInternal BHIVDecisionMode = "INTERNAL"
)

// ModeLockLevel defines how strictly the mode is locked.
type ModeLockLevel string

const (
	// ModeLockNone: Mode can be changed freely. For development/testing only.
	ModeLockNone ModeLockLevel = "NONE"

	// ModeLockPrivileged: Mode change requires privileged initiator + audit.
	// This is the minimum lock level for staging environments.
	ModeLockPrivileged ModeLockLevel = "PRIVILEGED"

	// ModeLockImmutable: Mode cannot be changed at runtime.
	// This is the REQUIRED lock level for production BHIV deployments.
	// The only way to change mode is to restart with different config.
	ModeLockImmutable ModeLockLevel = "IMMUTABLE"
)

// ModeController manages the system-wide enforcement mode and provides
// hard guards that prevent PDP/KSML execution in EXTERNAL mode.
// Phase 6: Now supports mode locking and privileged-only transitions.
type ModeController struct {
	mu   sync.RWMutex
	mode BHIVDecisionMode

	// Phase 6: Mode lock configuration
	lockLevel        ModeLockLevel
	privilegedUsers  map[string]bool // Set of users allowed to change mode in PRIVILEGED lock
	lockedAt         *time.Time      // When the mode was locked
	lockedBy         string          // Who locked the mode

	// Audit: track mode transitions for compliance
	modeHistory []ModeTransition

	// Guard violation tracking
	guardViolations []GuardViolation
}

// ModeTransition records a mode change for audit purposes.
type ModeTransition struct {
	From      BHIVDecisionMode `json:"from"`
	To        BHIVDecisionMode `json:"to"`
	Timestamp time.Time        `json:"timestamp"`
	Reason    string           `json:"reason"`
	Initiator string           `json:"initiator"`
}

// GuardViolation records an attempt to use PDP/KSML in EXTERNAL mode.
type GuardViolation struct {
	Timestamp  time.Time `json:"timestamp"`
	Component  string    `json:"component"`   // "PDP", "KSML", "GovernanceKernel"
	Operation  string    `json:"operation"`    // What was attempted
	CallerInfo string    `json:"caller_info"`  // Who attempted it
	Mode       string    `json:"mode"`         // Current mode when violation occurred
}

// NewModeController creates a mode controller with the specified default mode.
// Lock level defaults to NONE (for backward compatibility and testing).
func NewModeController(defaultMode BHIVDecisionMode) *ModeController {
	return &ModeController{
		mode:            defaultMode,
		lockLevel:       ModeLockNone,
		privilegedUsers: make(map[string]bool),
		modeHistory: []ModeTransition{{
			From:      "",
			To:        defaultMode,
			Timestamp: time.Now().UTC(),
			Reason:    "SYSTEM_INIT",
			Initiator: "system",
		}},
		guardViolations: make([]GuardViolation, 0),
	}
}

// NewProductionModeController creates a mode controller LOCKED in EXTERNAL mode.
// This is the REQUIRED constructor for BHIV production deployments.
// The mode CANNOT be changed at runtime.
func NewProductionModeController() *ModeController {
	now := time.Now().UTC()
	return &ModeController{
		mode:            BHIVModeExternal,
		lockLevel:       ModeLockImmutable,
		privilegedUsers: make(map[string]bool),
		lockedAt:        &now,
		lockedBy:        "PRODUCTION_INIT",
		modeHistory: []ModeTransition{{
			From:      "",
			To:        BHIVModeExternal,
			Timestamp: now,
			Reason:    "PRODUCTION_INIT: Mode locked to EXTERNAL (immutable)",
			Initiator: "system",
		}},
		guardViolations: make([]GuardViolation, 0),
	}
}

// NewPrivilegedModeController creates a mode controller that requires
// privileged initiator for mode changes. For staging environments.
func NewPrivilegedModeController(defaultMode BHIVDecisionMode, privilegedUsers []string) *ModeController {
	mc := NewModeController(defaultMode)
	mc.lockLevel = ModeLockPrivileged
	for _, u := range privilegedUsers {
		mc.privilegedUsers[u] = true
	}
	return mc
}

// LockMode locks the mode at the current level. Once locked to IMMUTABLE,
// the mode cannot be changed at runtime.
func (mc *ModeController) LockMode(level ModeLockLevel, initiator string) error {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	if mc.lockLevel == ModeLockImmutable {
		return fmt.Errorf("MODE_ALREADY_IMMUTABLE: mode was locked by '%s' at %s",
			mc.lockedBy, mc.lockedAt.Format(time.RFC3339))
	}

	now := time.Now().UTC()
	mc.lockLevel = level
	mc.lockedAt = &now
	mc.lockedBy = initiator

	mc.modeHistory = append(mc.modeHistory, ModeTransition{
		From:      mc.mode,
		To:        mc.mode,
		Timestamp: now,
		Reason:    fmt.Sprintf("MODE_LOCKED: level=%s", level),
		Initiator: initiator,
	})
	return nil
}

// GetLockLevel returns the current mode lock level.
func (mc *ModeController) GetLockLevel() ModeLockLevel {
	mc.mu.RLock()
	defer mc.mu.RUnlock()
	return mc.lockLevel
}

// IsLocked returns true if the mode is locked (PRIVILEGED or IMMUTABLE).
func (mc *ModeController) IsLocked() bool {
	mc.mu.RLock()
	defer mc.mu.RUnlock()
	return mc.lockLevel != ModeLockNone
}

// GetMode returns the current enforcement mode. Thread-safe.
func (mc *ModeController) GetMode() BHIVDecisionMode {
	mc.mu.RLock()
	defer mc.mu.RUnlock()
	return mc.mode
}

// SetMode transitions the system to a new enforcement mode.
// Phase 6: Now respects mode lock levels.
// - IMMUTABLE: SetMode always fails (mode cannot change at runtime).
// - PRIVILEGED: SetMode requires initiator to be in privilegedUsers set.
// - NONE: SetMode works as before (for testing/development).
func (mc *ModeController) SetMode(newMode BHIVDecisionMode, reason, initiator string) error {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	// Phase 6: Check mode lock
	if mc.lockLevel == ModeLockImmutable {
		// Record this as a guard violation — someone tried to change an immutable mode
		mc.guardViolations = append(mc.guardViolations, GuardViolation{
			Timestamp:  time.Now().UTC(),
			Component:  "ModeController",
			Operation:  fmt.Sprintf("SetMode(%s)", newMode),
			CallerInfo: initiator,
			Mode:       string(mc.mode),
		})
		return fmt.Errorf("MODE_LOCKED_IMMUTABLE: mode is locked to '%s' and cannot be changed at runtime (locked by '%s' at %s)",
			mc.mode, mc.lockedBy, mc.lockedAt.Format(time.RFC3339))
	}

	if mc.lockLevel == ModeLockPrivileged {
		if !mc.privilegedUsers[initiator] {
			mc.guardViolations = append(mc.guardViolations, GuardViolation{
				Timestamp:  time.Now().UTC(),
				Component:  "ModeController",
				Operation:  fmt.Sprintf("SetMode(%s) — UNPRIVILEGED", newMode),
				CallerInfo: initiator,
				Mode:       string(mc.mode),
			})
			return fmt.Errorf("MODE_CHANGE_UNAUTHORIZED: initiator '%s' is not in privileged users list", initiator)
		}
	}

	if newMode != BHIVModeExternal && newMode != BHIVModeInternal {
		return fmt.Errorf("INVALID_MODE: %s (must be EXTERNAL or INTERNAL)", newMode)
	}

	oldMode := mc.mode
	mc.mode = newMode
	mc.modeHistory = append(mc.modeHistory, ModeTransition{
		From:      oldMode,
		To:        newMode,
		Timestamp: time.Now().UTC(),
		Reason:    reason,
		Initiator: initiator,
	})
	return nil
}

// IsExternalMode returns true if the system is in EXTERNAL mode.
func (mc *ModeController) IsExternalMode() bool {
	mc.mu.RLock()
	defer mc.mu.RUnlock()
	return mc.mode == BHIVModeExternal
}

// IsInternalMode returns true if the system is in INTERNAL mode.
func (mc *ModeController) IsInternalMode() bool {
	mc.mu.RLock()
	defer mc.mu.RUnlock()
	return mc.mode == BHIVModeInternal
}

// ================================================================
// PHASE 6 (continued): CENTRALIZED GUARD INTERCEPTOR
// ================================================================
// ISSUE 5 FIX: Instead of scattered per-function guards, we implement
// a CENTRALIZED guard that blocks ALL decision interfaces globally
// when mode == EXTERNAL.
//
// CentralGuardCheck is the SINGLE enforcement gate. Before any decision
// interface (PDP, KSML, GovernanceKernel) can execute, this guard MUST
// be checked. If mode is EXTERNAL, ALL decision interfaces are blocked.
//
// This replaces the scattered per-function guards with a single point
// of enforcement, making bypass impossible.

// DecisionInterface identifies which internal decision component is being guarded.
type DecisionInterface string

const (
	DecisionInterfacePDP              DecisionInterface = "PDP"
	DecisionInterfaceKSML             DecisionInterface = "KSML"
	DecisionInterfaceGovernanceKernel DecisionInterface = "GovernanceKernel"
)

// CentralGuardCheck is the SINGLE enforcement gate that blocks ALL decision
// interfaces in EXTERNAL mode. This is the centralized interceptor that
// replaces scattered per-function guards.
//
// Parameters:
//   - component: which decision interface is being accessed (PDP/KSML/GovernanceKernel)
//   - operation: what operation is being attempted
//   - callerInfo: who is attempting it (for audit)
//
// Returns:
//   - nil if the operation is permitted (INTERNAL mode)
//   - error if the operation is blocked (EXTERNAL mode)
//
// Every call to CentralGuardCheck is recorded. In EXTERNAL mode, violations
// are logged to the guard violation record for audit.
func (mc *ModeController) CentralGuardCheck(component DecisionInterface, operation, callerInfo string) error {
	mc.mu.Lock()
	defer mc.mu.Unlock()

	if mc.mode == BHIVModeExternal {
		violation := GuardViolation{
			Timestamp:  time.Now().UTC(),
			Component:  string(component),
			Operation:  operation,
			CallerInfo: callerInfo,
			Mode:       string(mc.mode),
		}
		mc.guardViolations = append(mc.guardViolations, violation)
		return fmt.Errorf("CENTRAL_GUARD_VIOLATION: %s.%s blocked in EXTERNAL mode (caller: %s) — ALL decision interfaces are disabled when Sarathi operates as pure enforcement layer",
			component, operation, callerInfo)
	}
	return nil
}

// GuardCheckPDP verifies that PDP execution is permitted in the current mode.
// Delegates to CentralGuardCheck for centralized enforcement.
func (mc *ModeController) GuardCheckPDP(callerInfo string) error {
	return mc.CentralGuardCheck(DecisionInterfacePDP, "Evaluate", callerInfo)
}

// GuardCheckKSML verifies that KSML execution is permitted in the current mode.
// Delegates to CentralGuardCheck for centralized enforcement.
func (mc *ModeController) GuardCheckKSML(callerInfo string) error {
	return mc.CentralGuardCheck(DecisionInterfaceKSML, "GovernIntent", callerInfo)
}

// GuardCheckGovernanceKernel verifies that GovernanceKernel decisions are permitted.
// Delegates to CentralGuardCheck for centralized enforcement.
func (mc *ModeController) GuardCheckGovernanceKernel(callerInfo string) error {
	return mc.CentralGuardCheck(DecisionInterfaceGovernanceKernel, "Decide", callerInfo)
}

// GetGuardViolations returns all recorded guard violations.
func (mc *ModeController) GetGuardViolations() []GuardViolation {
	mc.mu.RLock()
	defer mc.mu.RUnlock()
	cp := make([]GuardViolation, len(mc.guardViolations))
	copy(cp, mc.guardViolations)
	return cp
}

// GetModeHistory returns the full mode transition history.
func (mc *ModeController) GetModeHistory() []ModeTransition {
	mc.mu.RLock()
	defer mc.mu.RUnlock()
	cp := make([]ModeTransition, len(mc.modeHistory))
	copy(cp, mc.modeHistory)
	return cp
}

// GuardViolationCount returns the number of guard violations recorded.
func (mc *ModeController) GuardViolationCount() int {
	mc.mu.RLock()
	defer mc.mu.RUnlock()
	return len(mc.guardViolations)
}

// ================================================================
// PHASE 4: STRICT VERIFICATION PIPELINE + PHASE 5: BINDING ENFORCEMENT
// ================================================================
// The verification pipeline is the exact sequence of checks that every
// external decision MUST pass before Sarathi issues a capability token.
//
// PIPELINE ORDER (FIXED — cannot be reordered):
//   1. MODE CHECK      → Is the system in EXTERNAL mode?
//   2. STRUCTURE CHECK  → Are all required fields present and valid?
//   3. EVALUATOR TRUST  → Is the evaluator registered and ACTIVE?
//   4. SIGNATURE CHECK  → Is the Ed25519 signature valid?
//   5. INTEGRITY CHECK  → Does the hash match recomputed value?
//   6. EXPIRY CHECK     → Is the decision within its TTL?
//   7. REPLAY CHECK     → Has this nonce been seen before?
//   8. RATE LIMIT CHECK → Is the agent within rate limits?
//   9. POSTURE CHECK    → Does the agent pass BeyondCorp posture?
//   10. BINDING CHECK   → Does the decision bind to the request?
//
// CRITICAL: If ANY step fails, the pipeline HALTS immediately.
// No subsequent steps execute. The failure is recorded with the
// exact stage that failed, creating a deterministic audit trail.

// ExternalEnforcementResult contains the complete result of verifying
// and enforcing an external decision, including the capability token.
type ExternalEnforcementResult struct {
	// Decision that was verified and enforced
	Decision *ExternalDecision `json:"decision"`

	// Enforcement outcome
	Enforced        bool   `json:"enforced"`
	Verdict         string `json:"verdict"`
	EnforcementHash string `json:"enforcement_hash"`
	CorrelationID   string `json:"correlation_id"`

	// Token (nil if not ALLOW or verification failed)
	Token *CapabilityToken `json:"-"` // Not serialized — sensitive

	// Audit
	EnforcedAt string `json:"enforced_at"`
	Mode       string `json:"mode"` // Always "EXTERNAL"

	// Failure info
	BlockReason string `json:"block_reason,omitempty"`
	BlockDetail string `json:"block_detail,omitempty"`

	// Phase 4: Verification trace — complete audit trail of pipeline
	VerificationTrace *VerificationTrace `json:"verification_trace,omitempty"`

	// Phase 5: Decision-request binding
	DecisionCoreHash string `json:"decision_core_hash,omitempty"`
	RequestBindingHash string `json:"request_binding_hash,omitempty"`
}

// ToMap returns a read-only map for logging.
func (r *ExternalEnforcementResult) ToMap() map[string]interface{} {
	m := map[string]interface{}{
		"enforced":         r.Enforced,
		"verdict":          r.Verdict,
		"enforcement_hash": r.EnforcementHash,
		"correlation_id":   r.CorrelationID,
		"enforced_at":      r.EnforcedAt,
		"mode":             r.Mode,
		"has_token":        r.Token != nil,
	}
	if r.BlockReason != "" {
		m["block_reason"] = r.BlockReason
		m["block_detail"] = r.BlockDetail
	}
	if r.Decision != nil {
		m["decision_id"] = r.Decision.DecisionID
		m["evaluator_id"] = r.Decision.EvaluatorID
	}
	if r.DecisionCoreHash != "" {
		m["decision_core_hash"] = r.DecisionCoreHash
	}
	if r.RequestBindingHash != "" {
		m["request_binding_hash"] = r.RequestBindingHash
	}
	if r.VerificationTrace != nil {
		m["verification_stages"] = len(r.VerificationTrace.Results)
		m["verification_verdict"] = r.VerificationTrace.FinalVerdict
		if r.VerificationTrace.FailedStage != "" {
			m["failed_stage"] = string(r.VerificationTrace.FailedStage)
		}
	}
	return m
}

// externalReplayTracker tracks nonces of external decisions to prevent replay.
type externalReplayTracker struct {
	mu     sync.Mutex
	nonces map[string]time.Time // nonce → first-seen timestamp
	maxAge time.Duration        // how long to keep nonces
}

func newExternalReplayTracker() *externalReplayTracker {
	t := &externalReplayTracker{
		nonces: make(map[string]time.Time),
		maxAge: 5 * time.Minute,
	}
	go t.cleanupLoop()
	return t
}

func (t *externalReplayTracker) IsReplay(nonce string) bool {
	t.mu.Lock()
	defer t.mu.Unlock()
	_, exists := t.nonces[nonce]
	return exists
}

func (t *externalReplayTracker) Record(nonce string) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.nonces[nonce] = time.Now().UTC()
}

func (t *externalReplayTracker) cleanupLoop() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		t.mu.Lock()
		cutoff := time.Now().UTC().Add(-t.maxAge)
		for nonce, ts := range t.nonces {
			if ts.Before(cutoff) {
				delete(t.nonces, nonce)
			}
		}
		t.mu.Unlock()
	}
}

// ================================================================
// PHASE 4: EnforceExternalDecision — STRICT VERIFICATION PIPELINE
// ================================================================
// This is the BHIV-compliant external enforcement entry point.
// It runs the EXACT verification sequence defined above.
// NO step can be skipped. NO step can be reordered.
//
// NAMING CONVENTION (ISSUE 1 FIX):
//   - "Verify*" = Execution validity check (Sarathi's responsibility)
//   - "Evaluate*" = FORBIDDEN — this would be decision correctness
//   - "Enforce*" = Post-verification token issuance and chain recording

func (ea *EnforcementAdapter) EnforceExternalDecision(
	decision *ExternalDecision,
	modeCtrl *ModeController,
) *ExternalEnforcementResult {
	ea.mu.Lock()
	defer ea.mu.Unlock()

	now := time.Now().UTC()
	correlationID := uuid.New().String()

	// Initialize verification trace
	trace := &VerificationTrace{
		CorrelationID: correlationID,
		StartedAt:     now,
		Results:       make([]VerificationResult, 0, 10),
	}
	if decision != nil {
		trace.DecisionID = decision.DecisionID
		trace.EvaluatorID = decision.EvaluatorID
	}

	// Helper: record a verification stage result
	recordStage := func(stage VerificationStage, passed bool, reason, detail string) {
		trace.Results = append(trace.Results, VerificationResult{
			Stage:     stage,
			Passed:    passed,
			Reason:    reason,
			Timestamp: time.Now().UTC(),
			Detail:    detail,
		})
	}

	// Helper: create a blocked result with full trace
	blocked := func(stage VerificationStage, reason, detail string) *ExternalEnforcementResult {
		recordStage(stage, false, reason, detail)
		trace.CompletedAt = time.Now().UTC()
		trace.FinalVerdict = "REJECTED"
		trace.FailedStage = stage
		trace.FailedReason = reason

		result := &ExternalEnforcementResult{
			Decision:          decision,
			Enforced:          false,
			Verdict:           "DENY",
			CorrelationID:     correlationID,
			EnforcedAt:        now.Format("2006-01-02T15:04:05.000000Z"),
			Mode:              string(BHIVModeExternal),
			BlockReason:       reason,
			BlockDetail:       detail,
			VerificationTrace: trace,
		}

		// Record in enforcement chain for audit completeness
		if decision != nil {
			synthReq := NewExecutionRequest(
				decision.AgentID, decision.ResourceID, decision.Action,
				correlationID,
			)
			synthResp := NewExecutionResponse(synthReq, nil, "EXTERNAL_VERIFICATION_REJECTED",
				fmt.Sprintf("stage=%s reason=%s detail=%s", stage, reason, detail))
			result.EnforcementHash = synthResp.EnforcementHash()
			ea.appendToChain(synthResp)
		}
		return result
	}

	// ═══════════════════════════════════════════════════════
	// STEP 1: MODE CHECK — Is system in EXTERNAL mode?
	// ═══════════════════════════════════════════════════════
	if modeCtrl == nil {
		return blocked(StageModeCheck, "MODE_CONTROLLER_NIL", "ModeController not provided — cannot verify enforcement mode")
	}
	if !modeCtrl.IsExternalMode() {
		return blocked(StageModeCheck, "MODE_NOT_EXTERNAL",
			fmt.Sprintf("EnforceExternalDecision requires EXTERNAL mode, current=%s", modeCtrl.GetMode()))
	}
	recordStage(StageModeCheck, true, "MODE_EXTERNAL_CONFIRMED", fmt.Sprintf("mode=%s lock=%s", modeCtrl.GetMode(), modeCtrl.GetLockLevel()))

	// ═══════════════════════════════════════════════════════
	// STEP 2: STRUCTURE CHECK — Are all required fields present?
	// ═══════════════════════════════════════════════════════
	if decision == nil {
		return blocked(StageStructureCheck, "STRUCTURE_INVALID", "decision is nil")
	}
	if err := decision.ValidateStructure(); err != nil {
		return blocked(StageStructureCheck, "STRUCTURE_INVALID", err.Error())
	}
	recordStage(StageStructureCheck, true, "STRUCTURE_VALID",
		fmt.Sprintf("decision_id=%s evaluator=%s agent=%s", decision.DecisionID, decision.EvaluatorID, decision.AgentID))

	// ═══════════════════════════════════════════════════════
	// STEP 3: EVALUATOR TRUST CHECK — Is evaluator registered and ACTIVE?
	// (ISSUE 2 FIX: Evaluator trust binding)
	// ═══════════════════════════════════════════════════════
	if ea.evaluatorRegistry == nil {
		return blocked(StageEvaluatorTrustCheck, "EVALUATOR_REGISTRY_NOT_INITIALIZED",
			"EvaluatorTrustRegistry is nil — cannot verify evaluator trust")
	}
	evaluatorRecord, evalErr := ea.evaluatorRegistry.GetActiveEvaluator(decision.EvaluatorID)
	if evalErr != nil {
		return blocked(StageEvaluatorTrustCheck, "EVALUATOR_NOT_TRUSTED", evalErr.Error())
	}
	recordStage(StageEvaluatorTrustCheck, true, "EVALUATOR_TRUSTED",
		fmt.Sprintf("evaluator=%s status=%s key=%s", evaluatorRecord.EvaluatorID, evaluatorRecord.Status, evaluatorRecord.PublicKeyHex[:16]))

	// ═══════════════════════════════════════════════════════
	// STEP 4: SIGNATURE VERIFICATION — Is the Ed25519 signature valid?
	// (ISSUE 2 FIX: Cryptographic evaluator authentication)
	// ═══════════════════════════════════════════════════════
	sigValid, sigKeySource, sigReason := ea.evaluatorRegistry.VerifySignatureWithRotation(
		decision.EvaluatorID,
		[]byte(decision.DecisionCoreHash),
		decision.EvaluatorSignature,
	)
	if !sigValid {
		return blocked(StageSignatureVerification, "SIGNATURE_VERIFICATION_FAILED", sigReason)
	}
	recordStage(StageSignatureVerification, true, "SIGNATURE_VERIFIED",
		fmt.Sprintf("key_source=%s reason=%s", sigKeySource, sigReason))

	// ═══════════════════════════════════════════════════════
	// STEP 5: INTEGRITY CHECK — Does the hash match recomputed value?
	// ═══════════════════════════════════════════════════════
	if !decision.VerifyIntegrity() {
		return blocked(StageIntegrityCheck, "INTEGRITY_FAILED",
			"decision_hash does not match recomputed hash — decision was tampered")
	}
	if !decision.VerifyCoreHashIntegrity() {
		return blocked(StageIntegrityCheck, "CORE_HASH_INTEGRITY_FAILED",
			"decision_core_hash does not match recomputed core hash — binding fields tampered")
	}
	recordStage(StageIntegrityCheck, true, "INTEGRITY_VERIFIED",
		fmt.Sprintf("hash=%s core_hash=%s", decision.DecisionHash[:16], decision.DecisionCoreHash[:16]))

	// ═══════════════════════════════════════════════════════
	// STEP 6: EXPIRY CHECK — Is the decision within its TTL?
	// ═══════════════════════════════════════════════════════
	if decision.IsExpired() {
		return blocked(StageExpiryCheck, "DECISION_EXPIRED",
			fmt.Sprintf("expires_at=%s now=%s clock_skew_tolerance=%v",
				decision.ExpiresAt.Format(time.RFC3339), now.Format(time.RFC3339), ClockSkewTolerance))
	}
	recordStage(StageExpiryCheck, true, "NOT_EXPIRED",
		fmt.Sprintf("expires_at=%s remaining=%v", decision.ExpiresAt.Format(time.RFC3339), time.Until(decision.ExpiresAt)))

	// ═══════════════════════════════════════════════════════
	// STEP 7: REPLAY CHECK — Has this nonce been seen before?
	// ═══════════════════════════════════════════════════════
	if ea.externalReplayTracker != nil && ea.externalReplayTracker.IsReplay(decision.Nonce) {
		return blocked(StageReplayCheck, "REPLAY_DETECTED",
			fmt.Sprintf("nonce=%s already seen — replay attack blocked", decision.Nonce))
	}
	// GAP-3 FIX: Do NOT record nonce here. Recording now deferred to AFTER rate limit
	// and posture checks pass (before token issuance). This ensures that if rate limit
	// or posture fails, the nonce is NOT consumed and the legitimate caller can retry
	// with the same decision. Recording at this point would cause a retry to be falsely
	// blocked as a replay attack.
	recordStage(StageReplayCheck, true, "NOT_REPLAY", fmt.Sprintf("nonce=%s checked (recording deferred)", decision.Nonce[:8]))

	// ═══════════════════════════════════════════════════════
	// STEP 8: RATE LIMIT CHECK — Is the agent within limits?
	// ═══════════════════════════════════════════════════════
	if ea.rateLimitConfig.Enabled {
		// Global rate limit
		if ea.rateLimitConfig.GlobalMaxPerWindow > 0 {
			cutoff := now.Add(-ea.rateLimitConfig.WindowDuration)
			cleaned := make([]time.Time, 0, len(ea.globalRateWindow))
			for _, ts := range ea.globalRateWindow {
				if ts.After(cutoff) {
					cleaned = append(cleaned, ts)
				}
			}
			if len(cleaned) >= ea.rateLimitConfig.GlobalMaxPerWindow {
				ea.globalRateWindow = cleaned
				return blocked(StageRateLimitCheck, "GLOBAL_RATE_LIMIT_EXCEEDED",
					fmt.Sprintf("max=%d per %v", ea.rateLimitConfig.GlobalMaxPerWindow, ea.rateLimitConfig.WindowDuration))
			}
			cleaned = append(cleaned, now)
			ea.globalRateWindow = cleaned
		}
		// Per-agent rate limit
		if decision.AgentID != "" {
			if ea.isRateLimited(decision.AgentID) {
				return blocked(StageRateLimitCheck, "AGENT_RATE_LIMIT_EXCEEDED",
					fmt.Sprintf("agent=%s max=%d per %v",
						decision.AgentID, ea.rateLimitConfig.MaxRequestsPerWindow,
						ea.rateLimitConfig.WindowDuration))
			}
			ea.recordRequest(decision.AgentID)
		}
	}
	recordStage(StageRateLimitCheck, true, "RATE_LIMIT_OK", "within limits")

	// ═══════════════════════════════════════════════════════
	// STEP 9: POSTURE CHECK — Does agent pass BeyondCorp check?
	// ═══════════════════════════════════════════════════════
	if ea.postureMonitor != nil && decision.AgentID != "" {
		ea.postureMonitor.RecordRequest(decision.AgentID, "")
		trustworthy, reason := ea.postureMonitor.EvaluatePosture(decision.AgentID)
		if !trustworthy {
			return blocked(StagePostureCheck, "POSTURE_CHECK_FAILED",
				fmt.Sprintf("agent=%s reason=%s", decision.AgentID, reason))
		}
	}
	recordStage(StagePostureCheck, true, "POSTURE_OK", fmt.Sprintf("agent=%s", decision.AgentID))

	// ═══════════════════════════════════════════════════════
	// NONCE COMMIT — Record nonce AFTER all retryable checks pass
	// GAP-3 FIX: Nonce is committed here (after rate limit + posture) rather than
	// at Step 7. This ensures that rate-limited or posture-failed requests can be
	// legitimately retried without being falsely blocked as replay attacks.
	// Once committed, this nonce can never be used again.
	// ═══════════════════════════════════════════════════════
	if ea.externalReplayTracker != nil {
		ea.externalReplayTracker.Record(decision.Nonce)
	}

	// ═══════════════════════════════════════════════════════
	// STEP 10: BINDING CHECK — Does decision bind to request?
	// (ISSUE 4 FIX: Decision-request binding)
	// ═══════════════════════════════════════════════════════
	// The DecisionCoreHash binds: decision_id + evaluator_id + agent_id +
	// resource_id + action + verdict + timestamp + nonce.
	// This ensures the token cannot drift from the decision.
	expectedCoreHash := decision.computeCoreHash()
	if decision.DecisionCoreHash != expectedCoreHash {
		return blocked(StageBindingCheck, "BINDING_HASH_MISMATCH",
			fmt.Sprintf("stored_core_hash=%s computed_core_hash=%s — decision-request binding broken",
				decision.DecisionCoreHash[:16], expectedCoreHash[:16]))
	}
	recordStage(StageBindingCheck, true, "BINDING_VERIFIED",
		fmt.Sprintf("core_hash=%s", decision.DecisionCoreHash[:16]))

	// ═══════════════════════════════════════════════════════
	// ALL VERIFICATION STAGES PASSED
	// ═══════════════════════════════════════════════════════
	recordStage(StageVerificationComplete, true, "ALL_STAGES_PASSED",
		fmt.Sprintf("10/10 verification stages passed for decision_id=%s", decision.DecisionID))
	trace.CompletedAt = time.Now().UTC()
	trace.FinalVerdict = "VERIFIED"

	// ═══════════════════════════════════════════════════════
	// ENFORCEMENT: For DENY/ESCALATE verdicts — enforce without token
	// ═══════════════════════════════════════════════════════
	if decision.Verdict != ExternalVerdictAllow {
		synthReq := NewExecutionRequest(
			decision.AgentID, decision.ResourceID, decision.Action,
			correlationID,
		)
		synthResp := NewExecutionResponse(synthReq, nil, "EXTERNAL_DECISION_VERIFIED_AND_ENFORCED",
			fmt.Sprintf("EXTERNAL_%s: evaluator=%s reason=%s",
				decision.Verdict, decision.EvaluatorID, decision.Reason))
		ea.appendToChain(synthResp)

		return &ExternalEnforcementResult{
			Decision:          decision,
			Enforced:          true,
			Verdict:           string(decision.Verdict),
			EnforcementHash:   synthResp.EnforcementHash(),
			CorrelationID:     correlationID,
			EnforcedAt:        now.Format("2006-01-02T15:04:05.000000Z"),
			Mode:              string(BHIVModeExternal),
			Token:             nil, // No token for DENY/ESCALATE
			VerificationTrace: trace,
			DecisionCoreHash:  decision.DecisionCoreHash,
		}
	}

	// ═══════════════════════════════════════════════════════
	// ENFORCEMENT: ALLOW verdict — issue token with binding
	// (ISSUE 4 + ISSUE 6 FIX: Token bound to verified decision)
	// ═══════════════════════════════════════════════════════
	// Create synthetic ExecutionRequest for hash chain binding
	// Phase 5: request_hash = decision_core_hash (explicit binding)
	synthReq := NewExecutionRequest(
		decision.AgentID, decision.ResourceID, decision.Action,
		correlationID,
	)

	// Create synthetic PDP response from the VERIFIED external decision
	// The token carries: decision_id + evaluator_id + decision_core_hash
	synthPDPResp := &PDPResponse{
		DecisionID:          decision.DecisionID,
		Verdict:             string(decision.Verdict),
		PolicyVersion:       fmt.Sprintf("external:%s:verified", decision.EvaluatorID),
		PolicyHash:          decision.DecisionCoreHash, // Phase 5: bind token to decision core hash
		DeterminingRules:    []string{fmt.Sprintf("EXT-VERIFIED-%s", decision.DecisionID[:8])},
		TruthClassification: "EXTERNAL_VERIFIED",
		RequestHash:         synthReq.RequestHash(),
		Timestamp:           decision.Timestamp.Format("2006-01-02T15:04:05.000000Z"),
		Reason:              fmt.Sprintf("VERIFIED_EXTERNAL_ALLOW: evaluator=%s signature=VALID", decision.EvaluatorID),
		AgentRole:           "EXTERNAL",
		ResourceType:        "EXTERNAL",
		StageReached:        5,
		Obligations:         decision.Obligations,
	}

	// Create enforcement response (issues token on ALLOW)
	synthResp := NewExecutionResponse(synthReq, synthPDPResp, "EXTERNAL_DECISION_VERIFIED_AND_ENFORCED", "VERIFIED_EXTERNAL_ALLOW_ACCEPTED")

	// Sign the capability token with TokenAuthority (Ed25519)
	if ea.tokenAuthority != nil {
		ea.tokenAuthority.SignToken(synthResp.GetCapabilityToken())
	}

	// Append to enforcement chain
	ea.appendToChain(synthResp)

	// Build result with full verification trace
	return &ExternalEnforcementResult{
		Decision:           decision,
		Enforced:           true,
		Verdict:            string(decision.Verdict),
		EnforcementHash:    synthResp.EnforcementHash(),
		CorrelationID:      correlationID,
		Token:              synthResp.GetCapabilityToken(),
		EnforcedAt:         now.Format("2006-01-02T15:04:05.000000Z"),
		Mode:               string(BHIVModeExternal),
		VerificationTrace:  trace,
		DecisionCoreHash:   decision.DecisionCoreHash,
		RequestBindingHash: synthReq.RequestHash(),
	}
}

// ================================================================
// ADAPTER FIELD EXTENSION
// ================================================================
// Extends EnforcementAdapter with external enforcement capabilities.

// InitExternalMode initializes external enforcement capabilities on the adapter.
// This MUST be called before EnforceExternalDecision can be used.
// It initializes the replay tracker and evaluator registry.
// It does NOT modify any existing internal enforcement behavior.
func (ea *EnforcementAdapter) InitExternalMode() {
	ea.mu.Lock()
	defer ea.mu.Unlock()
	if ea.externalReplayTracker == nil {
		ea.externalReplayTracker = newExternalReplayTracker()
	}
	if ea.evaluatorRegistry == nil {
		ea.evaluatorRegistry = NewEvaluatorTrustRegistry()
	}
}

// ResetReplayTrackerForHarness clears the external replay tracker.
//
// THIS IS A TEST-ONLY AFFORDANCE. Production code MUST NEVER call this method:
// clearing the replay tracker opens the adapter to nonce-replay attacks that
// the tracker otherwise prevents.
//
// Purpose: the v14.5 propagation replay harness runs the SAME signed fixture
// through the adapter N times (see propagation_harness.go). The fixture uses
// a FIXED nonce for byte-stability; between iterations the harness calls
// this method so the tracker accepts the next iteration's nonce rather than
// rejecting it as a replay. This is safe because:
//   - The call is guarded behind PropagationReplayConfig — harness only.
//   - No production code path invokes it.
//   - The tracker is re-initialised, not removed — subsequent production
//     calls continue to get replay protection.
//
// TAG: test-affordance-only
func (ea *EnforcementAdapter) ResetReplayTrackerForHarness() {
	ea.mu.Lock()
	defer ea.mu.Unlock()
	if ea.externalReplayTracker != nil {
		// Swap with a fresh instance — the old one's cleanup goroutine will
		// exit on next tick when it finds the map empty and no new inserts.
		ea.externalReplayTracker = newExternalReplayTracker()
	}
}

// GetEvaluatorRegistry returns the evaluator trust registry for configuration.
func (ea *EnforcementAdapter) GetEvaluatorRegistry() *EvaluatorTrustRegistry {
	return ea.evaluatorRegistry
}

// SetEvaluatorRegistry sets a pre-configured evaluator registry on the adapter.
func (ea *EnforcementAdapter) SetEvaluatorRegistry(registry *EvaluatorTrustRegistry) {
	ea.mu.Lock()
	defer ea.mu.Unlock()
	ea.evaluatorRegistry = registry
}

// ================================================================
// PHASE 7: END-TO-END BHIV FLOW
// ================================================================
// Complete flow: Evaluator → signed decision → VerifyAndEnforce →
//   token → ExecuteWithToken → audit

// BHIVEnforcementFlow executes the complete BHIV external enforcement pipeline.
// This is the production entry point for the external decision path.
//
// Flow:
//   1. Verify system is in EXTERNAL mode
//   2. Verify + enforce external decision (10-stage pipeline, no PDP)
//   3. Execute with token (reuses existing execution engine)
//   4. Verify all audit entries
//
// All logic is deterministic, cryptographic, and verifiable.
func BHIVEnforcementFlow(
	decision *ExternalDecision,
	modeCtrl *ModeController,
	adapter *EnforcementAdapter,
	engine *ExecutionEngine,
) map[string]interface{} {

	result := make(map[string]interface{})
	result["flow"] = "BHIV_EXTERNAL_VERIFICATION_AND_ENFORCEMENT"
	result["mode"] = string(modeCtrl.GetMode())
	result["mode_lock"] = string(modeCtrl.GetLockLevel())

	// Step 1: Verify + enforce external decision
	enfResult := adapter.EnforceExternalDecision(decision, modeCtrl)
	result["enforcement"] = enfResult.ToMap()

	// Include verification trace summary
	if enfResult.VerificationTrace != nil {
		result["verification_verdict"] = enfResult.VerificationTrace.FinalVerdict
		result["verification_stages"] = len(enfResult.VerificationTrace.Results)
		if enfResult.VerificationTrace.FailedStage != "" {
			result["verification_failed_stage"] = string(enfResult.VerificationTrace.FailedStage)
			result["verification_failed_reason"] = enfResult.VerificationTrace.FailedReason
		}
	}

	if !enfResult.Enforced || enfResult.Token == nil {
		result["execution"] = map[string]interface{}{
			"executed":     false,
			"block_reason": enfResult.BlockReason,
		}
		return result
	}

	// Step 2: Execute with token (reuses existing execution engine)
	execResult := engine.ExecuteWithToken(enfResult.Token)
	result["execution"] = execResult.ToMap()

	// Step 3: Record trace
	result["decision_id"] = decision.DecisionID
	result["evaluator_id"] = decision.EvaluatorID
	result["correlation_id"] = enfResult.CorrelationID
	result["enforcement_hash"] = enfResult.EnforcementHash
	result["decision_core_hash"] = enfResult.DecisionCoreHash
	result["request_binding_hash"] = enfResult.RequestBindingHash
	result["token_id"] = enfResult.Token.TokenID()

	return result
}

// ================================================================
// ── v12.1/v12.2 THIN TRUST CONSUMER (GAP-01 FIX) ──
// ================================================================
// PURPOSE:
//   This is the ONLY coupling allowed between the Sarathi enforcement core
//   and any evaluator trust state source. The enforcement adapter and the
//   external-decision pipeline reference TrustConsumer — never the heavy
//   EvaluatorTrustRegistry directly (in the default build).
//
// GAP-01 FIX (v12.1):
//   Sarathi was OWNING evaluator lifecycle (store backends, admin auth,
//   PoP registration, JWKS, config loader, REST API). That surface is
//   now soft-frozen (compile-not-wired). The default binary uses
//   InMemoryTrustConsumer loaded from a static snapshot.
//
// v12.2 BOUNDARY PURIFICATION:
//   Originally introduced in trust_consumer.go (v12.1). Folded into
//   external_decision.go in v12.2 to honor the "no dilution" rule —
//   it now lives next to EvaluatorTrustRegistry, the type it adapts.
//
// DESIGN RULE:
//   If the TrustConsumer interface needs a new method, justify it in
//   KB_06 and add a default no-op in InMemoryTrustConsumer.

// TrustConsumer is the minimal interface Sarathi needs to verify
// evaluator identity. It does NOT manage lifecycle — no registration,
// no suspension, no key rotation, no admin auth, no JWKS publication.
type TrustConsumer interface {
	// GetActiveEvaluator returns the evaluator record ONLY if it exists
	// AND has ACTIVE status. Error describes why the evaluator is not trusted.
	GetActiveEvaluator(evaluatorID string) (*EvaluatorRecord, error)

	// VerifyEvaluatorSignature verifies a signature against the evaluator's
	// current key (and any previous keys within their grace period).
	// Returns (valid, keySource, reason).
	VerifyEvaluatorSignature(evaluatorID string, message, signature []byte) (bool, string, string)
}

// EvaluatorTrustSnapshot is a lightweight evaluator entry for the
// in-memory trust consumer. Loaded from a JSON file at startup.
type EvaluatorTrustSnapshot struct {
	EvaluatorID  string `json:"evaluator_id"`
	Name         string `json:"name"`
	Status       string `json:"status"`         // ACTIVE, SUSPENDED, REVOKED
	PublicKeyHex string `json:"public_key_hex"` // Ed25519 public key (hex-encoded)
	// v15.5: sha256(api_key) — Sarathi stores the fingerprint only; the raw
	// secret travels in the X-API-Key header on every call. Empty for
	// evaluators created before v15.5; in that case the inbound auth
	// middleware skips the fingerprint check (caller-key fallback applies).
	APIKeyFingerprint string `json:"api_key_fingerprint,omitempty"`
}

// TrustSnapshotFile is the JSON structure for the static trust snapshot.
type TrustSnapshotFile struct {
	Version    string                   `json:"version"`
	Evaluators []EvaluatorTrustSnapshot `json:"evaluators"`
}

// InMemoryTrustConsumer is a read-only, snapshot-based implementation of
// TrustConsumer. It loads evaluator trust state from a static JSON file at
// startup. Changes require a Sarathi restart — intentional, because lifecycle
// operations are NOT Sarathi's job.
type InMemoryTrustConsumer struct {
	mu         sync.RWMutex
	evaluators map[string]*evaluatorTrustEntry
}

type evaluatorTrustEntry struct {
	record    *EvaluatorRecord
	publicKey ed25519.PublicKey
}

// NewInMemoryTrustConsumer creates a trust consumer from a static snapshot.
func NewInMemoryTrustConsumer(snapshot *TrustSnapshotFile) (*InMemoryTrustConsumer, error) {
	tc := &InMemoryTrustConsumer{
		evaluators: make(map[string]*evaluatorTrustEntry),
	}

	if snapshot == nil {
		return tc, nil
	}

	for _, s := range snapshot.Evaluators {
		pubBytes, err := hex.DecodeString(s.PublicKeyHex)
		if err != nil {
			return nil, fmt.Errorf("invalid public key hex for evaluator '%s': %w", s.EvaluatorID, err)
		}
		if len(pubBytes) != ed25519.PublicKeySize {
			return nil, fmt.Errorf("invalid public key size for evaluator '%s': expected %d, got %d",
				s.EvaluatorID, ed25519.PublicKeySize, len(pubBytes))
		}

		now := time.Now().UTC()
		status := EvaluatorStatus(s.Status)
		if status == "" {
			status = EvaluatorStatusActive
		}

		tc.evaluators[s.EvaluatorID] = &evaluatorTrustEntry{
			record: &EvaluatorRecord{
				EvaluatorID:  s.EvaluatorID,
				Name:         s.Name,
				Status:       status,
				PublicKey:    ed25519.PublicKey(pubBytes),
				PublicKeyHex: s.PublicKeyHex,
				RegisteredAt: now,
				LastActiveAt: now,
				Metadata:     make(map[string]string),
				PreviousKeys: make([]EvaluatorKeyVersion, 0),
			},
			publicKey: ed25519.PublicKey(pubBytes),
		}
	}

	return tc, nil
}

// GetActiveEvaluator returns the evaluator ONLY if ACTIVE.
func (tc *InMemoryTrustConsumer) GetActiveEvaluator(evaluatorID string) (*EvaluatorRecord, error) {
	tc.mu.RLock()
	defer tc.mu.RUnlock()

	entry, found := tc.evaluators[evaluatorID]
	if !found {
		return nil, fmt.Errorf("EVALUATOR_NOT_FOUND: '%s' is not registered in the trust snapshot", evaluatorID)
	}

	rec := entry.record
	if rec.Status == EvaluatorStatusRevoked {
		return nil, fmt.Errorf("EVALUATOR_REVOKED: '%s'", evaluatorID)
	}
	if rec.Status == EvaluatorStatusSuspended {
		return nil, fmt.Errorf("EVALUATOR_SUSPENDED: '%s'", evaluatorID)
	}
	if rec.Status != EvaluatorStatusActive {
		return nil, fmt.Errorf("EVALUATOR_NOT_ACTIVE: '%s' has status '%s'", evaluatorID, rec.Status)
	}

	return rec, nil
}

// VerifyEvaluatorSignature verifies an Ed25519 signature against the
// evaluator's public key from the snapshot.
func (tc *InMemoryTrustConsumer) VerifyEvaluatorSignature(
	evaluatorID string, message, signature []byte,
) (bool, string, string) {
	tc.mu.RLock()
	defer tc.mu.RUnlock()

	entry, found := tc.evaluators[evaluatorID]
	if !found {
		return false, "", "EVALUATOR_NOT_FOUND"
	}
	if entry.record.Status != EvaluatorStatusActive {
		return false, "", fmt.Sprintf("EVALUATOR_NOT_ACTIVE: status=%s", entry.record.Status)
	}

	if ed25519.Verify(entry.publicKey, message, signature) {
		return true, "SNAPSHOT_KEY", "SIGNATURE_VALID"
	}
	return false, "", "SIGNATURE_INVALID: no matching key found"
}

// LoadTrustSnapshot reads a trust snapshot JSON file from disk.
func LoadTrustSnapshot(path string) (*TrustSnapshotFile, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read trust snapshot file '%s': %w", path, err)
	}

	var snapshot TrustSnapshotFile
	if err := json.Unmarshal(data, &snapshot); err != nil {
		return nil, fmt.Errorf("failed to parse trust snapshot file '%s': %w", path, err)
	}

	return &snapshot, nil
}

// BootstrapTrustConsumer creates the appropriate TrustConsumer implementation
// based on environment configuration. This is the default-build replacement for
// BootstrapEvaluatorRegistry (which is soft-frozen / compile-not-wired).
//
// WIRING PRIORITY (v14.2 Production Hardening):
//   1. If SARATHI_TRUST_REMOTE_URL is set → RemoteTrustConsumer (real external registry)
//      with InMemoryTrustConsumer as fallback (if SARATHI_TRUST_SNAPSHOT is also set).
//   2. If only SARATHI_TRUST_SNAPSHOT is set → InMemoryTrustConsumer (static snapshot).
//   3. If neither is set → empty InMemoryTrustConsumer (INTERNAL mode only).
//
// SECURITY INVARIANT: The returned TrustConsumer is READ-ONLY.
// It can verify evaluator identity and signatures but CANNOT register,
// suspend, revoke, or rotate evaluator keys. Evaluator lifecycle is
// NOT Sarathi's responsibility (KB_06 GAP-01 boundary rule).
func BootstrapTrustConsumer(adapter *EnforcementAdapter) (TrustConsumer, error) {
	snapshotPath := os.Getenv("SARATHI_TRUST_SNAPSHOT")
	remoteURL := os.Getenv("SARATHI_TRUST_REMOTE_URL")

	// Step 1: Always build the in-memory consumer (may serve as primary or fallback)
	var snapshot *TrustSnapshotFile
	if snapshotPath != "" {
		var err error
		snapshot, err = LoadTrustSnapshot(snapshotPath)
		if err != nil {
			return nil, fmt.Errorf("trust snapshot load failed: %w", err)
		}
		fmt.Printf("  Trust snapshot loaded: %d evaluators from %s\n", len(snapshot.Evaluators), snapshotPath)
	}

	inMemory, err := NewInMemoryTrustConsumer(snapshot)
	if err != nil {
		return nil, fmt.Errorf("trust consumer creation failed: %w", err)
	}

	// Step 2: If remote URL is configured, create RemoteTrustConsumer
	if remoteURL != "" {
		cfg := RemoteTrustConfig{
			BaseURL:  remoteURL,
			APIKey:   os.Getenv("SARATHI_TRUST_REMOTE_KEY"),
			CacheTTL: parseDurationEnv("SARATHI_TRUST_CACHE_TTL", 30*time.Second),
			Timeout:  parseDurationEnv("SARATHI_TRUST_TIMEOUT", 5*time.Second),
			CircuitBreakerConfig: CircuitBreakerConfig{
				FailureThreshold: parseIntEnv("SARATHI_TRUST_CB_THRESHOLD", 5),
				ResetTimeout:     parseDurationEnv("SARATHI_TRUST_CB_RESET", 30*time.Second),
				HalfOpenMaxProbes: 2,
			},
			Retry: RetryConfig{
				MaxRetries:        parseIntEnv("SARATHI_TRUST_MAX_RETRIES", 3),
				InitialBackoff:    100 * time.Millisecond,
				MaxBackoff:        5 * time.Second,
				BackoffMultiplier: 2.0,
				Jitter:            0.1,
			},
			Fallback: inMemory, // InMemoryTrustConsumer as degradation fallback
		}

		remote, err := NewRemoteTrustConsumer(cfg)
		if err != nil {
			return nil, fmt.Errorf("remote trust consumer creation failed: %w", err)
		}

		fmt.Printf("  Remote trust consumer: %s (cache_ttl=%v, cb_threshold=%d)\n",
			remoteURL, cfg.CacheTTL, cfg.CircuitBreakerConfig.FailureThreshold)
		if snapshotPath != "" {
			fmt.Printf("  Fallback trust consumer: InMemoryTrustConsumer (%d evaluators)\n", len(snapshot.Evaluators))
		}
		return remote, nil
	}

	return inMemory, nil
}

// Compile-time assertion: EvaluatorTrustRegistry satisfies TrustConsumer.
// This lets a future trust_service build use EvaluatorTrustRegistry as a drop-in.
var _ TrustConsumer = (*EvaluatorTrustRegistry)(nil)

// VerifyEvaluatorSignature adapts EvaluatorTrustRegistry to TrustConsumer.
// Delegates to VerifySignatureWithRotation defined earlier in this file.
func (r *EvaluatorTrustRegistry) VerifyEvaluatorSignature(
	evaluatorID string, message, signature []byte,
) (bool, string, string) {
	return r.VerifySignatureWithRotation(evaluatorID, message, signature)
}

// ================================================================
// ── v14.2 PRODUCTION HARDENING: RESILIENCE PRIMITIVES ──
// ================================================================
// Shared resilience types used by:
//   - RemoteTrustConsumer (Phase A: external evaluator integration)
//   - ProductionWebhookHandler (Phase B: execution handler wiring)
//   - HTTPRoutingHandler (Phase C: multi-system flow pressure)
//
// Placement: external_decision.go — per KB_06 "no dilution" rule,
// these live alongside the first consumer (TrustConsumer interface).
//
// Industry alignment:
//   - Netflix Hystrix / Resilience4j: Circuit Breaker pattern
//   - Google SRE: Exponential backoff with jitter
//   - Microsoft Azure: Bulkhead isolation pattern
//   - NIST 800-207: Fail-closed on degradation

// ================================================================
// CIRCUIT BREAKER
// ================================================================

// CircuitBreakerState represents the current state of a circuit breaker.
type CircuitBreakerState int

const (
	// CircuitClosed — normal operation, requests pass through.
	CircuitClosed CircuitBreakerState = iota
	// CircuitOpen — too many failures, requests are fast-rejected.
	CircuitOpen
	// CircuitHalfOpen — probe mode, limited requests allowed to test recovery.
	CircuitHalfOpen
)

// CircuitBreakerConfig configures the circuit breaker behavior.
type CircuitBreakerConfig struct {
	FailureThreshold  int           // failures before opening circuit
	ResetTimeout      time.Duration // how long to stay OPEN before trying HALF_OPEN
	HalfOpenMaxProbes int           // max probe requests in HALF_OPEN state
}

// DefaultCircuitBreakerConfig returns production-grade defaults.
func DefaultCircuitBreakerConfig() CircuitBreakerConfig {
	return CircuitBreakerConfig{
		FailureThreshold:  5,
		ResetTimeout:      30 * time.Second,
		HalfOpenMaxProbes: 2,
	}
}

// CircuitBreaker implements the three-state circuit breaker pattern.
// Thread-safe. Fail-closed: if the breaker is OPEN, all requests are
// immediately rejected without making the downstream call.
type CircuitBreaker struct {
	mu              sync.Mutex
	state           CircuitBreakerState
	config          CircuitBreakerConfig
	failureCount    int
	successCount    int
	lastFailureTime time.Time
	halfOpenProbes  int
	name            string // for logging
}

// NewCircuitBreaker creates a circuit breaker with the given config.
func NewCircuitBreaker(name string, config CircuitBreakerConfig) *CircuitBreaker {
	if config.FailureThreshold <= 0 {
		config.FailureThreshold = 5
	}
	if config.ResetTimeout <= 0 {
		config.ResetTimeout = 30 * time.Second
	}
	if config.HalfOpenMaxProbes <= 0 {
		config.HalfOpenMaxProbes = 2
	}
	return &CircuitBreaker{
		state:  CircuitClosed,
		config: config,
		name:   name,
	}
}

// Allow checks if a request should be allowed through the circuit breaker.
// Returns true if the request is permitted, false if the circuit is OPEN.
// Thread-safe.
func (cb *CircuitBreaker) Allow() bool {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	switch cb.state {
	case CircuitClosed:
		return true
	case CircuitOpen:
		// Check if we should transition to HALF_OPEN
		if time.Since(cb.lastFailureTime) >= cb.config.ResetTimeout {
			cb.state = CircuitHalfOpen
			cb.halfOpenProbes = 0
			fmt.Printf("  [CircuitBreaker:%s] OPEN → HALF_OPEN (reset timeout elapsed)\n", cb.name)
			return true
		}
		return false
	case CircuitHalfOpen:
		// Allow limited probes in HALF_OPEN
		if cb.halfOpenProbes < cb.config.HalfOpenMaxProbes {
			cb.halfOpenProbes++
			return true
		}
		return false
	}
	return false
}

// RecordSuccess records a successful request. In HALF_OPEN, enough
// successes close the circuit (return to normal).
func (cb *CircuitBreaker) RecordSuccess() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.successCount++
	if cb.state == CircuitHalfOpen {
		// Enough successful probes → close the circuit
		cb.state = CircuitClosed
		cb.failureCount = 0
		cb.halfOpenProbes = 0
		fmt.Printf("  [CircuitBreaker:%s] HALF_OPEN → CLOSED (probe succeeded)\n", cb.name)
	} else if cb.state == CircuitClosed {
		// In closed state, successes reset the failure counter
		if cb.failureCount > 0 {
			cb.failureCount = 0
		}
	}
}

// RecordFailure records a failed request. If failures exceed the threshold,
// the circuit opens and all subsequent requests are fast-rejected.
func (cb *CircuitBreaker) RecordFailure() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	cb.failureCount++
	cb.lastFailureTime = time.Now()

	if cb.state == CircuitHalfOpen {
		// Any failure in HALF_OPEN → back to OPEN
		cb.state = CircuitOpen
		fmt.Printf("  [CircuitBreaker:%s] HALF_OPEN → OPEN (probe failed)\n", cb.name)
	} else if cb.state == CircuitClosed && cb.failureCount >= cb.config.FailureThreshold {
		cb.state = CircuitOpen
		fmt.Printf("  [CircuitBreaker:%s] CLOSED → OPEN (failure threshold %d reached)\n",
			cb.name, cb.config.FailureThreshold)
	}
}

// GetState returns the current circuit breaker state. Thread-safe.
func (cb *CircuitBreaker) GetState() CircuitBreakerState {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return cb.state
}

// GetStateString returns the current state as a human-readable string.
func (cb *CircuitBreaker) GetStateString() string {
	switch cb.GetState() {
	case CircuitClosed:
		return "CLOSED"
	case CircuitOpen:
		return "OPEN"
	case CircuitHalfOpen:
		return "HALF_OPEN"
	}
	return "UNKNOWN"
}

// ================================================================
// RETRY CONFIG
// ================================================================

// RetryConfig configures exponential backoff retry behavior.
// Shared by all production-grade network clients in the system.
type RetryConfig struct {
	MaxRetries        int           // maximum retry attempts (0 = no retry)
	InitialBackoff    time.Duration // backoff for first retry
	MaxBackoff        time.Duration // maximum backoff duration
	BackoffMultiplier float64       // multiply backoff after each retry
	Jitter            float64       // random jitter fraction (0.0–1.0)
}

// DefaultRetryConfig returns production-grade retry defaults.
func DefaultRetryConfig() RetryConfig {
	return RetryConfig{
		MaxRetries:        3,
		InitialBackoff:    100 * time.Millisecond,
		MaxBackoff:        5 * time.Second,
		BackoffMultiplier: 2.0,
		Jitter:            0.1,
	}
}

// ComputeBackoff returns the backoff duration for a given attempt number (0-indexed).
func (rc *RetryConfig) ComputeBackoff(attempt int) time.Duration {
	if attempt <= 0 {
		return rc.InitialBackoff
	}
	backoff := float64(rc.InitialBackoff) * math.Pow(rc.BackoffMultiplier, float64(attempt))
	if backoff > float64(rc.MaxBackoff) {
		backoff = float64(rc.MaxBackoff)
	}
	// Add jitter
	if rc.Jitter > 0 {
		jitterRange := backoff * rc.Jitter
		backoff += (rand.Float64()*2 - 1) * jitterRange
	}
	if backoff < 0 {
		backoff = float64(rc.InitialBackoff)
	}
	return time.Duration(backoff)
}

// ================================================================
// BULKHEAD LIMITER
// ================================================================

// BulkheadLimiter implements semaphore-based bulkhead isolation.
// Limits the number of concurrent in-flight requests to a downstream
// service, preventing a slow target from consuming all goroutines.
//
// Industry alignment:
//   - Netflix Hystrix: Thread-pool bulkhead
//   - Resilience4j: Semaphore-based bulkhead
//   - Microsoft Azure: Bulkhead pattern for microservices
type BulkheadLimiter struct {
	semaphore      chan struct{}
	maxConcurrency int
	name           string
}

// NewBulkheadLimiter creates a bulkhead with the given max concurrency.
func NewBulkheadLimiter(name string, maxConcurrency int) *BulkheadLimiter {
	if maxConcurrency <= 0 {
		maxConcurrency = 10
	}
	return &BulkheadLimiter{
		semaphore:      make(chan struct{}, maxConcurrency),
		maxConcurrency: maxConcurrency,
		name:           name,
	}
}

// Acquire attempts to acquire a slot. Returns true if acquired,
// false if the bulkhead is full (all slots occupied). Non-blocking.
func (bl *BulkheadLimiter) Acquire() bool {
	select {
	case bl.semaphore <- struct{}{}:
		return true
	default:
		return false
	}
}

// Release releases a slot back to the bulkhead.
func (bl *BulkheadLimiter) Release() {
	select {
	case <-bl.semaphore:
	default:
		// Safety: release on empty channel is a no-op
	}
}

// ================================================================
// ── v14.2 PRODUCTION HARDENING: REMOTE TRUST CONSUMER ──
// ================================================================
// PURPOSE:
//   RemoteTrustConsumer is a production-grade HTTPS client implementation
//   of TrustConsumer that queries a real external evaluator registry.
//
// SECURITY MODEL:
//   - READ-ONLY: This consumer can ONLY read evaluator records. It has
//     ZERO write methods. It CANNOT register, suspend, revoke, or rotate
//     evaluator keys. Evaluator lifecycle is managed by the external
//     registry, NOT by Sarathi.
//   - FAIL-CLOSED: If the remote registry is unreachable and no fallback
//     is configured, ALL evaluator lookups return errors → enforcement
//     pipeline produces DENY verdicts (INV-02 guaranteed).
//   - SIGNATURE VERIFICATION IS LOCAL: Ed25519 signatures are verified
//     locally using the public key fetched from the registry. The
//     verification itself never makes a network call.
//
// NON-MANIPULATION GUARANTEE:
//   - RemoteTrustConsumer implements TrustConsumer (2 read-only methods).
//   - There is no method to add, modify, or delete evaluators.
//   - The enforcement pipeline (INV-35 hash-pinned) calls only these
//     2 methods during the EVALUATOR_TRUST_CHECK and SIGNATURE_VERIFICATION
//     stages. No other method is invokable from the pipeline.
//   - Even if a rogue entry existed in the remote registry, decisions
//     must carry a valid Ed25519 signature from the matching private key.
//     Without the private key, the signature check fails → DENY.

// RemoteTrustConfig configures the RemoteTrustConsumer.
type RemoteTrustConfig struct {
	BaseURL              string               // external registry base URL
	APIKey               string               // API key for authentication
	CacheTTL             time.Duration         // local cache TTL
	Timeout              time.Duration         // HTTP request timeout
	CircuitBreakerConfig CircuitBreakerConfig  // circuit breaker settings
	Retry                RetryConfig           // retry settings
	Fallback             TrustConsumer         // optional fallback consumer
	TLSInsecureSkipVerify bool                 // for dev/test only — NEVER in production
}

// cachedEvaluator holds a cached evaluator record with expiration.
type cachedEvaluator struct {
	record    *EvaluatorRecord
	publicKey ed25519.PublicKey
	fetchedAt time.Time
	err       error // cached error (negative cache)
}

// RemoteTrustConsumer queries a real external evaluator registry via HTTPS.
// Implements TrustConsumer (read-only: GetActiveEvaluator, VerifyEvaluatorSignature).
type RemoteTrustConsumer struct {
	mu             sync.RWMutex
	config         RemoteTrustConfig
	httpClient     *http.Client
	circuitBreaker *CircuitBreaker
	cache          map[string]*cachedEvaluator
	fallback       TrustConsumer
}

// Compile-time assertion: RemoteTrustConsumer satisfies TrustConsumer.
var _ TrustConsumer = (*RemoteTrustConsumer)(nil)

// NewRemoteTrustConsumer creates a production-grade remote evaluator trust consumer.
func NewRemoteTrustConsumer(config RemoteTrustConfig) (*RemoteTrustConsumer, error) {
	if config.BaseURL == "" {
		return nil, fmt.Errorf("RemoteTrustConsumer requires non-empty BaseURL")
	}
	if config.CacheTTL <= 0 {
		config.CacheTTL = 30 * time.Second
	}
	if config.Timeout <= 0 {
		config.Timeout = 5 * time.Second
	}

	tlsConfig := &tls.Config{
		MinVersion: tls.VersionTLS12,
	}
	if config.TLSInsecureSkipVerify {
		tlsConfig.InsecureSkipVerify = true
	}

	transport := &http.Transport{
		TLSClientConfig:     tlsConfig,
		MaxIdleConns:        10,
		MaxIdleConnsPerHost: 5,
		IdleConnTimeout:     90 * time.Second,
	}

	return &RemoteTrustConsumer{
		config: config,
		httpClient: &http.Client{
			Timeout:   config.Timeout,
			Transport: transport,
		},
		circuitBreaker: NewCircuitBreaker("remote-trust", config.CircuitBreakerConfig),
		cache:          make(map[string]*cachedEvaluator),
		fallback:       config.Fallback,
	}, nil
}

// GetActiveEvaluator returns the evaluator record from the remote registry
// ONLY if the evaluator exists AND has ACTIVE status. Uses local cache,
// circuit breaker, retry logic, and optional fallback.
//
// SECURITY: This method is READ-ONLY. It queries but cannot modify the
// remote registry. If the remote registry is down and no fallback is
// configured, it returns an error → enforcement pipeline DENYs.
func (rtc *RemoteTrustConsumer) GetActiveEvaluator(evaluatorID string) (*EvaluatorRecord, error) {
	// Step 1: Check local cache
	rtc.mu.RLock()
	if cached, ok := rtc.cache[evaluatorID]; ok {
		if time.Since(cached.fetchedAt) < rtc.config.CacheTTL {
			rtc.mu.RUnlock()
			if cached.err != nil {
				return nil, cached.err
			}
			return cached.record, nil
		}
	}
	rtc.mu.RUnlock()

	// Step 2: Check circuit breaker
	if !rtc.circuitBreaker.Allow() {
		// Circuit is OPEN — fail-closed or use fallback
		if rtc.fallback != nil {
			return rtc.fallback.GetActiveEvaluator(evaluatorID)
		}
		return nil, fmt.Errorf("EVALUATOR_LOOKUP_CIRCUIT_OPEN: remote trust registry unavailable (circuit breaker OPEN for %s)",
			rtc.circuitBreaker.name)
	}

	// Step 3: Fetch from remote registry with retries
	var lastErr error
	for attempt := 0; attempt <= rtc.config.Retry.MaxRetries; attempt++ {
		if attempt > 0 {
			backoff := rtc.config.Retry.ComputeBackoff(attempt - 1)
			time.Sleep(backoff)
		}

		record, pubKey, err := rtc.fetchEvaluatorFromRemote(evaluatorID)
		if err == nil {
			// Success — cache and return
			rtc.circuitBreaker.RecordSuccess()
			rtc.mu.Lock()
			rtc.cache[evaluatorID] = &cachedEvaluator{
				record:    record,
				publicKey: pubKey,
				fetchedAt: time.Now(),
			}
			rtc.mu.Unlock()
			return record, nil
		}

		lastErr = err

		// Check if this is a permanent error (4xx) vs transient (5xx/timeout)
		if isPermanentError(err) {
			// Don't retry permanent errors — cache the negative result
			rtc.mu.Lock()
			rtc.cache[evaluatorID] = &cachedEvaluator{
				err:       err,
				fetchedAt: time.Now(),
			}
			rtc.mu.Unlock()
			return nil, err
		}
	}

	// All retries exhausted — record failure in circuit breaker
	rtc.circuitBreaker.RecordFailure()

	// Try fallback
	if rtc.fallback != nil {
		return rtc.fallback.GetActiveEvaluator(evaluatorID)
	}

	return nil, fmt.Errorf("EVALUATOR_LOOKUP_FAILED: remote trust registry query failed after %d retries: %w",
		rtc.config.Retry.MaxRetries, lastErr)
}

// VerifyEvaluatorSignature verifies an Ed25519 signature against the
// evaluator's public key. The key is fetched via GetActiveEvaluator
// (which uses cache/circuit breaker/retry). The actual Ed25519
// verification is LOCAL — no network call for the signature check itself.
func (rtc *RemoteTrustConsumer) VerifyEvaluatorSignature(
	evaluatorID string, message, signature []byte,
) (bool, string, string) {
	// Step 1: Get the evaluator record (may use cache)
	record, err := rtc.GetActiveEvaluator(evaluatorID)
	if err != nil {
		return false, "", fmt.Sprintf("EVALUATOR_LOOKUP_FAILED: %v", err)
	}

	// Step 2: Get the cached public key
	rtc.mu.RLock()
	cached, ok := rtc.cache[evaluatorID]
	rtc.mu.RUnlock()

	var pubKey ed25519.PublicKey
	if ok && cached.publicKey != nil {
		pubKey = cached.publicKey
	} else if record.PublicKey != nil {
		pubKey = record.PublicKey
	} else {
		return false, "", "EVALUATOR_NO_PUBLIC_KEY"
	}

	// Step 3: LOCAL Ed25519 verification — no network call
	if ed25519.Verify(pubKey, message, signature) {
		return true, "REMOTE_REGISTRY_KEY", "SIGNATURE_VALID"
	}

	// Step 4: Check previous keys (if any) for rotation grace period
	for _, prevKey := range record.PreviousKeys {
		if prevKey.GraceExpiresAt.After(time.Now().UTC()) {
			prevPubBytes, hexErr := hex.DecodeString(prevKey.PublicKeyHex)
			if hexErr == nil && len(prevPubBytes) == ed25519.PublicKeySize {
				if ed25519.Verify(ed25519.PublicKey(prevPubBytes), message, signature) {
					return true, "REMOTE_PREVIOUS_KEY", "SIGNATURE_VALID_GRACE_PERIOD"
				}
			}
		}
	}

	return false, "", "SIGNATURE_INVALID: no matching key found in remote registry"
}

// fetchEvaluatorFromRemote makes an HTTP GET request to the remote registry.
func (rtc *RemoteTrustConsumer) fetchEvaluatorFromRemote(evaluatorID string) (*EvaluatorRecord, ed25519.PublicKey, error) {
	url := fmt.Sprintf("%s/evaluators/%s", rtc.config.BaseURL, evaluatorID)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Accept", "application/json")
	req.Header.Set("X-Sarathi-Component", "RemoteTrustConsumer")
	if rtc.config.APIKey != "" {
		req.Header.Set("Authorization", "Bearer "+rtc.config.APIKey)
	}

	resp, err := rtc.httpClient.Do(req)
	if err != nil {
		return nil, nil, fmt.Errorf("REMOTE_HTTP_ERROR: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20)) // 1MB limit
	if err != nil {
		return nil, nil, fmt.Errorf("REMOTE_READ_ERROR: %w", err)
	}

	// Handle non-2xx responses
	if resp.StatusCode == http.StatusNotFound {
		return nil, nil, fmt.Errorf("EVALUATOR_NOT_FOUND: '%s' is not registered in the remote trust registry", evaluatorID)
	}
	if resp.StatusCode == http.StatusForbidden || resp.StatusCode == http.StatusUnauthorized {
		return nil, nil, fmt.Errorf("EVALUATOR_AUTH_FAILED: remote registry returned %d for evaluator '%s'", resp.StatusCode, evaluatorID)
	}
	if resp.StatusCode >= 500 {
		return nil, nil, fmt.Errorf("REMOTE_SERVER_ERROR: registry returned HTTP %d: %s", resp.StatusCode, string(body))
	}
	if resp.StatusCode >= 400 {
		return nil, nil, fmt.Errorf("EVALUATOR_CLIENT_ERROR: registry returned HTTP %d for '%s': %s",
			resp.StatusCode, evaluatorID, string(body))
	}

	// Parse the response into an evaluator snapshot format
	var evalResp struct {
		EvaluatorID  string `json:"evaluator_id"`
		Name         string `json:"name"`
		Status       string `json:"status"`
		PublicKeyHex string `json:"public_key_hex"`
		PreviousKeys []struct {
			PublicKeyHex   string `json:"public_key_hex"`
			GracePeriodEnd string `json:"grace_period_end"`
		} `json:"previous_keys,omitempty"`
	}
	if err := json.Unmarshal(body, &evalResp); err != nil {
		return nil, nil, fmt.Errorf("REMOTE_PARSE_ERROR: failed to parse evaluator response: %w", err)
	}

	// Validate status
	status := EvaluatorStatus(evalResp.Status)
	if status == EvaluatorStatusRevoked {
		return nil, nil, fmt.Errorf("EVALUATOR_REVOKED: '%s'", evaluatorID)
	}
	if status == EvaluatorStatusSuspended {
		return nil, nil, fmt.Errorf("EVALUATOR_SUSPENDED: '%s'", evaluatorID)
	}
	if status != EvaluatorStatusActive {
		return nil, nil, fmt.Errorf("EVALUATOR_NOT_ACTIVE: '%s' has status '%s'", evaluatorID, status)
	}

	// Parse public key
	pubBytes, err := hex.DecodeString(evalResp.PublicKeyHex)
	if err != nil {
		return nil, nil, fmt.Errorf("EVALUATOR_KEY_INVALID: bad public key hex for '%s': %w", evaluatorID, err)
	}
	if len(pubBytes) != ed25519.PublicKeySize {
		return nil, nil, fmt.Errorf("EVALUATOR_KEY_SIZE: invalid public key size for '%s': expected %d, got %d",
			evaluatorID, ed25519.PublicKeySize, len(pubBytes))
	}
	pubKey := ed25519.PublicKey(pubBytes)

	// Parse previous keys for rotation grace period
	var prevKeys []EvaluatorKeyVersion
	for _, pk := range evalResp.PreviousKeys {
		graceEnd, _ := time.Parse(time.RFC3339, pk.GracePeriodEnd)
		prevKeys = append(prevKeys, EvaluatorKeyVersion{
			PublicKeyHex:    pk.PublicKeyHex,
			GraceExpiresAt:  graceEnd,
		})
	}

	now := time.Now().UTC()
	record := &EvaluatorRecord{
		EvaluatorID:  evalResp.EvaluatorID,
		Name:         evalResp.Name,
		Status:       status,
		PublicKey:    pubKey,
		PublicKeyHex: evalResp.PublicKeyHex,
		RegisteredAt: now,
		LastActiveAt: now,
		Metadata:     make(map[string]string),
		PreviousKeys: prevKeys,
	}

	return record, pubKey, nil
}

// isPermanentError returns true if the error represents a permanent failure
// that should not be retried (4xx errors, parse errors, etc.).
func isPermanentError(err error) bool {
	if err == nil {
		return false
	}
	msg := err.Error()
	// Check for 4xx-class errors that should not be retried
	for _, prefix := range []string{
		"EVALUATOR_NOT_FOUND",
		"EVALUATOR_REVOKED",
		"EVALUATOR_SUSPENDED",
		"EVALUATOR_NOT_ACTIVE",
		"EVALUATOR_CLIENT_ERROR",
		"EVALUATOR_AUTH_FAILED",
		"EVALUATOR_KEY_INVALID",
		"EVALUATOR_KEY_SIZE",
		"REMOTE_PARSE_ERROR",
	} {
		for i := 0; i+len(prefix) <= len(msg); i++ {
			if msg[i:i+len(prefix)] == prefix {
				return true
			}
		}
	}
	return false
}

// GetCacheStats returns cache statistics for monitoring.
func (rtc *RemoteTrustConsumer) GetCacheStats() map[string]interface{} {
	rtc.mu.RLock()
	defer rtc.mu.RUnlock()
	return map[string]interface{}{
		"cache_entries":        len(rtc.cache),
		"circuit_breaker":      rtc.circuitBreaker.GetStateString(),
		"base_url":             rtc.config.BaseURL,
		"cache_ttl":            rtc.config.CacheTTL.String(),
		"has_fallback":         rtc.fallback != nil,
	}
}

// ================================================================
// ENV PARSING HELPERS
// ================================================================

// parseDurationEnv reads a duration from an environment variable.
// Returns defaultVal if the env var is empty or unparseable.
func parseDurationEnv(key string, defaultVal time.Duration) time.Duration {
	val := os.Getenv(key)
	if val == "" {
		return defaultVal
	}
	d, err := time.ParseDuration(val)
	if err != nil {
		return defaultVal
	}
	return d
}

// parseIntEnv reads an integer from an environment variable.
// Returns defaultVal if the env var is empty or unparseable.
func parseIntEnv(key string, defaultVal int) int {
	val := os.Getenv(key)
	if val == "" {
		return defaultVal
	}
	i, err := strconv.Atoi(val)
	if err != nil {
		return defaultVal
	}
	return i
}

// Suppress "imported and not used" for packages that are used by types
// defined here and by the handlers in other files.
var _ = bytes.NewBuffer
var _ = io.ReadAll
var _ = tls.VersionTLS12
var _ = strconv.Atoi
var _ = rand.Float64
var _ = math.Pow
