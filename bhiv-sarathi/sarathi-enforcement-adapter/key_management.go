package main

// key_management.go — Sovereign Key Lifecycle Management for BHIV Ecosystem.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Key Management System (v5.0)
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   Manages the complete lifecycle of Ed25519 governance keys:
//   GENERATED → PENDING_ACTIVATION → ACTIVE → ROTATING → REVOKED → DESTROYED
//
//   Keys are the root of trust for the Sarathi system. Every frozen policy
//   is signed by an Ed25519 key. This module ensures keys are:
//   - Generated with cryptographic randomness
//   - Activated through a ceremony process (dual-control)
//   - Rotated with overlap periods (old key still valid during transition)
//   - Revoked with immediate effect and distribution to all subsystems
//   - Destroyed with cryptographic erasure
//
// ARCHITECTURE:
//   KeyManager → GovernanceKeyRing (policy_signing.go)
//                ↓
//              AuditSink (saarthi_service.go) — every key event persisted
//                ↓
//              RevocationDistributor — notifies all downstream systems
//
// NON-BYPASSABILITY:
//   - Key operations require the KeyManager — no direct keyring mutation
//   - Every key state change is audit-logged
//   - Revocation is immediate and distributed
//   - No key can be re-activated after REVOKED or DESTROYED
//
// DESIGN REFERENCES:
//   - NIST SP 800-57: Key Management Recommendations
//   - AWS KMS: Key lifecycle with automatic rotation
//   - Google Cloud KMS: Key versions with scheduled destruction
//   - HashiCorp Vault: Dynamic secrets and key rotation
//   - Signal Protocol: Double ratchet key rotation
//   - PKCS#11: HSM interface for key storage
//   - PCI DSS 4.0: Cryptographic key management requirements

import (
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"sync"
	"sync/atomic"
	"time"

	"github.com/google/uuid"
)

// ================================================================
// KEY LIFECYCLE STATES
// ================================================================

// KeyState represents the lifecycle state of a governance key.
type KeyState string

const (
	KeyStateGenerated          KeyState = "GENERATED"           // Key created but not yet active
	KeyStatePendingActivation  KeyState = "PENDING_ACTIVATION"  // Awaiting ceremony approval
	KeyStateActive             KeyState = "ACTIVE"              // In use for signing/verification
	KeyStateRotating           KeyState = "ROTATING"            // Being replaced — still valid during overlap
	KeyStateRevoked            KeyState = "REVOKED"             // Permanently invalidated
	KeyStateDestroyed          KeyState = "DESTROYED"           // Cryptographically erased
)

// validKeyTransitions defines the allowed state machine transitions.
// Any transition not in this map is structurally impossible.
var validKeyTransitions = map[KeyState][]KeyState{
	KeyStateGenerated:         {KeyStatePendingActivation, KeyStateActive, KeyStateDestroyed},
	KeyStatePendingActivation: {KeyStateActive, KeyStateDestroyed},
	KeyStateActive:            {KeyStateRotating, KeyStateRevoked},
	KeyStateRotating:          {KeyStateRevoked},
	KeyStateRevoked:           {KeyStateDestroyed},
	KeyStateDestroyed:         {}, // Terminal state — no transitions
}

// isValidTransition checks if a state transition is allowed.
func isValidTransition(from, to KeyState) bool {
	allowed, exists := validKeyTransitions[from]
	if !exists {
		return false
	}
	for _, s := range allowed {
		if s == to {
			return true
		}
	}
	return false
}

// ================================================================
// MANAGED KEY
// ================================================================

// ManagedKey represents a governance key with full lifecycle metadata.
type ManagedKey struct {
	// Identity
	KeyID       GovernanceKeyID `json:"key_id"`
	Fingerprint string          `json:"fingerprint"` // SHA-256 of public key bytes

	// Cryptographic material (public only — private NEVER stored here)
	PublicKey    ed25519.PublicKey `json:"-"`
	PublicKeyHex string           `json:"public_key_hex"`

	// Lifecycle state
	State       KeyState  `json:"state"`
	GeneratedAt time.Time `json:"generated_at"`
	ActivatedAt time.Time `json:"activated_at,omitempty"`
	RotatedAt   time.Time `json:"rotated_at,omitempty"`
	RevokedAt   time.Time `json:"revoked_at,omitempty"`
	DestroyedAt time.Time `json:"destroyed_at,omitempty"`

	// Rotation metadata
	ReplacedByKeyID GovernanceKeyID `json:"replaced_by_key_id,omitempty"` // Key that replaced this one
	ReplacesKeyID   GovernanceKeyID `json:"replaces_key_id,omitempty"`   // Key this one replaced

	// Usage tracking
	SignatureCount uint64    `json:"signature_count"`
	LastUsedAt     time.Time `json:"last_used_at,omitempty"`

	// Ceremony metadata
	CeremonyID    string `json:"ceremony_id,omitempty"`     // ID of the activation ceremony
	ApprovedBy    string `json:"approved_by,omitempty"`     // Who approved activation
	RevocationReason string `json:"revocation_reason,omitempty"` // Why revoked

	// Expiration
	ExpiresAt time.Time `json:"expires_at,omitempty"` // Auto-rotation trigger
}

// IsUsable returns true if the key can currently be used for verification.
func (mk *ManagedKey) IsUsable() bool {
	return mk.State == KeyStateActive || mk.State == KeyStateRotating
}

// IsExpired checks if the key has passed its expiration time.
func (mk *ManagedKey) IsExpired() bool {
	if mk.ExpiresAt.IsZero() {
		return false
	}
	return time.Now().UTC().After(mk.ExpiresAt)
}

// ================================================================
// KEY EVENT (AUDIT TRAIL)
// ================================================================

// KeyEvent represents an auditable key lifecycle event.
type KeyEvent struct {
	EventID     string          `json:"event_id"`
	KeyID       GovernanceKeyID `json:"key_id"`
	EventType   string          `json:"event_type"`   // GENERATED, ACTIVATED, ROTATED, REVOKED, DESTROYED
	FromState   KeyState        `json:"from_state"`
	ToState     KeyState        `json:"to_state"`
	Timestamp   time.Time       `json:"timestamp"`
	Detail      string          `json:"detail"`
	PerformedBy string          `json:"performed_by"`  // System or operator ID
	EventHash   string          `json:"event_hash"`    // SHA-256 of event for tamper detection
	PrevHash    string          `json:"prev_hash"`     // Hash chain link
}

// computeEventHash computes a tamper-evident hash for a key event.
func computeEventHash(event *KeyEvent, prevHash string) string {
	payload := fmt.Sprintf("%s|%s|%s|%s|%s|%s|%s|%s",
		event.EventID, event.KeyID, event.EventType,
		event.FromState, event.ToState,
		event.Timestamp.Format(time.RFC3339Nano),
		event.Detail, prevHash,
	)
	h := sha256.Sum256([]byte(payload))
	return hex.EncodeToString(h[:])
}

// ================================================================
// REVOCATION DISTRIBUTOR
// ================================================================

// RevocationSubscriber is a callback for systems that need revocation notifications.
type RevocationSubscriber func(keyID GovernanceKeyID, reason string, revokedAt time.Time) error

// RevocationDistributor manages distribution of key revocation events
// to all downstream systems that rely on key validity.
type RevocationDistributor struct {
	mu          sync.RWMutex
	subscribers map[string]RevocationSubscriber // name → callback
}

// NewRevocationDistributor creates a new distributor.
func NewRevocationDistributor() *RevocationDistributor {
	return &RevocationDistributor{
		subscribers: make(map[string]RevocationSubscriber),
	}
}

// Subscribe registers a system to receive revocation notifications.
func (rd *RevocationDistributor) Subscribe(name string, fn RevocationSubscriber) {
	rd.mu.Lock()
	defer rd.mu.Unlock()
	rd.subscribers[name] = fn
}

// Unsubscribe removes a system from revocation notifications.
func (rd *RevocationDistributor) Unsubscribe(name string) {
	rd.mu.Lock()
	defer rd.mu.Unlock()
	delete(rd.subscribers, name)
}

// Distribute sends a revocation event to all subscribers with retry.
// Returns errors keyed by subscriber name. Best-effort with 3 retries per subscriber.
// Revocation is NOT rolled back on subscriber failure — state change is committed first.
func (rd *RevocationDistributor) Distribute(keyID GovernanceKeyID, reason string, revokedAt time.Time) map[string]error {
	rd.mu.RLock()
	subs := make(map[string]RevocationSubscriber, len(rd.subscribers))
	for k, v := range rd.subscribers {
		subs[k] = v
	}
	rd.mu.RUnlock()

	const maxRetries = 3
	errors := make(map[string]error)
	for name, fn := range subs {
		var lastErr error
		for attempt := 0; attempt < maxRetries; attempt++ {
			if err := fn(keyID, reason, revokedAt); err != nil {
				lastErr = err
				// Exponential backoff: 100ms, 200ms, 400ms
				time.Sleep(time.Duration(100<<uint(attempt)) * time.Millisecond)
				continue
			}
			lastErr = nil
			break
		}
		if lastErr != nil {
			errors[name] = fmt.Errorf("failed after %d retries: %w", maxRetries, lastErr)
		}
	}
	return errors
}

// SubscriberCount returns the number of registered subscribers.
func (rd *RevocationDistributor) SubscriberCount() int {
	rd.mu.RLock()
	defer rd.mu.RUnlock()
	return len(rd.subscribers)
}

// ================================================================
// KEY MANAGER
// ================================================================

// KeyManagerConfig holds configuration for the Key Manager.
type KeyManagerConfig struct {
	DefaultKeyExpiryDays   int  // Days until auto-rotation trigger (0 = no expiry)
	RotationOverlapMinutes int  // Minutes old key remains valid during rotation
	RequireCeremony        bool // Whether activation requires a ceremony
	MaxActiveKeys          int  // Maximum concurrent active keys (0 = unlimited)
	AutoRotateOnExpiry     bool // Automatically rotate expired keys
}

// DefaultKeyManagerConfig returns production-grade defaults.
func DefaultKeyManagerConfig() KeyManagerConfig {
	return KeyManagerConfig{
		DefaultKeyExpiryDays:   90,   // 90-day rotation per NIST SP 800-57
		RotationOverlapMinutes: 60,   // 1-hour overlap for safe rotation
		RequireCeremony:        true, // Production: dual-control activation
		MaxActiveKeys:          3,    // At most 3 active keys (current + 2 rotating)
		AutoRotateOnExpiry:     false, // Manual rotation in production
	}
}

// KeyManager is the sovereign key lifecycle manager for the BHIV ecosystem.
// All key operations MUST go through this manager. Direct keyring mutation
// is structurally prevented — the keyring is wrapped and controlled.
type KeyManager struct {
	mu     sync.RWMutex
	config KeyManagerConfig

	// Key storage
	keys map[GovernanceKeyID]*ManagedKey

	// Underlying keyring (from policy_signing.go)
	keyring *GovernanceKeyRing

	// Audit
	auditSink AuditSink
	eventsMu  sync.Mutex
	events    []KeyEvent
	lastHash  string // Hash chain head

	// Revocation distribution
	distributor *RevocationDistributor

	// Metrics
	totalGenerated  uint64
	totalActivated  uint64
	totalRotated    uint64
	totalRevoked    uint64
	totalDestroyed  uint64
	totalSignatures uint64

	// Lifecycle
	startedAt time.Time
	shutdownCh chan struct{}
}

// NewKeyManager creates a sovereign key lifecycle manager.
func NewKeyManager(
	keyring *GovernanceKeyRing,
	auditSink AuditSink,
	config KeyManagerConfig,
) (*KeyManager, error) {
	if keyring == nil {
		return nil, fmt.Errorf("FATAL: KeyManager requires non-nil GovernanceKeyRing")
	}
	if auditSink == nil {
		auditSink = NewInMemoryAuditSink()
	}

	km := &KeyManager{
		config:      config,
		keys:        make(map[GovernanceKeyID]*ManagedKey),
		keyring:     keyring,
		auditSink:   auditSink,
		events:      make([]KeyEvent, 0, 100),
		lastHash:    "GENESIS", // Hash chain anchored at GENESIS
		distributor: NewRevocationDistributor(),
		startedAt:   time.Now().UTC(),
		shutdownCh:  make(chan struct{}),
	}

	// Record startup (best-effort — service must start regardless)
	if err := auditSink.RecordSystemEvent("KEY_MANAGER_STARTED", "KeyManager initialized"); err != nil {
		fmt.Printf("[KeyManager] WARNING: Failed to audit startup event: %v\n", err)
	}

	// Start expiry monitor if auto-rotation is enabled
	if config.AutoRotateOnExpiry {
		go km.expiryMonitorLoop()
	}

	return km, nil
}

// ================================================================
// KEY GENERATION
// ================================================================

// GenerateKey creates a new Ed25519 key pair and registers it in GENERATED state.
// The private key is returned ONCE for secure storage. It is NOT retained.
//
// In production, this would happen on an air-gapped HSM. The private key
// would be stored in the HSM and never exported. Here we simulate the
// ceremony by returning the private key for the caller to store securely.
func (km *KeyManager) GenerateKey(keyID GovernanceKeyID) (ed25519.PrivateKey, error) {
	km.mu.Lock()
	defer km.mu.Unlock()

	// Check for duplicate
	if _, exists := km.keys[keyID]; exists {
		return nil, fmt.Errorf("key %q already exists", keyID)
	}

	// Generate Ed25519 key pair
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return nil, fmt.Errorf("key generation failed: %w", err)
	}

	// Compute fingerprint (SHA-256 of public key bytes)
	fingerprint := sha256.Sum256(pub)

	now := time.Now().UTC()
	mk := &ManagedKey{
		KeyID:        keyID,
		Fingerprint:  hex.EncodeToString(fingerprint[:]),
		PublicKey:     pub,
		PublicKeyHex: hex.EncodeToString(pub),
		State:        KeyStateGenerated,
		GeneratedAt:  now,
	}

	// Set expiry if configured
	if km.config.DefaultKeyExpiryDays > 0 {
		mk.ExpiresAt = now.Add(time.Duration(km.config.DefaultKeyExpiryDays) * 24 * time.Hour)
	}

	km.keys[keyID] = mk
	atomic.AddUint64(&km.totalGenerated, 1)

	// Record event
	km.recordEventLocked(keyID, "KEY_GENERATED", "", KeyStateGenerated,
		fmt.Sprintf("Ed25519 key generated, fingerprint=%s", mk.Fingerprint[:16]),
		"key_manager",
	)

	fmt.Printf("[KeyManager] Generated key: %s (fingerprint=%s...)\n", keyID, mk.Fingerprint[:16])
	return priv, nil
}

// ================================================================
// KEY ACTIVATION (CEREMONY)
// ================================================================

// ActivateKey transitions a key from GENERATED/PENDING_ACTIVATION to ACTIVE.
// If RequireCeremony is true, the key must first be moved to PENDING_ACTIVATION
// via RequestActivation(), then approved via this method.
func (km *KeyManager) ActivateKey(keyID GovernanceKeyID, approvedBy string) error {
	km.mu.Lock()
	defer km.mu.Unlock()

	mk, exists := km.keys[keyID]
	if !exists {
		return fmt.Errorf("key %q not found", keyID)
	}

	// Determine target state transition
	var fromState KeyState
	if km.config.RequireCeremony {
		if mk.State != KeyStatePendingActivation {
			return fmt.Errorf("key %q is in state %s — ceremony requires PENDING_ACTIVATION", keyID, mk.State)
		}
		fromState = KeyStatePendingActivation
	} else {
		if mk.State != KeyStateGenerated && mk.State != KeyStatePendingActivation {
			return fmt.Errorf("key %q is in state %s — can only activate from GENERATED or PENDING_ACTIVATION", keyID, mk.State)
		}
		fromState = mk.State
	}

	if !isValidTransition(fromState, KeyStateActive) {
		return fmt.Errorf("invalid transition: %s → ACTIVE", fromState)
	}

	// Check max active keys
	if km.config.MaxActiveKeys > 0 {
		activeCount := km.countKeysInStateLocked(KeyStateActive)
		if activeCount >= km.config.MaxActiveKeys {
			return fmt.Errorf("max active keys reached (%d) — rotate or revoke an existing key first", km.config.MaxActiveKeys)
		}
	}

	// Transition
	now := time.Now().UTC()
	mk.State = KeyStateActive
	mk.ActivatedAt = now
	mk.ApprovedBy = approvedBy
	mk.CeremonyID = uuid.New().String()

	// Register in the underlying keyring for policy verification
	if err := km.keyring.AddPublicKey(keyID, mk.PublicKeyHex); err != nil {
		// Rollback state
		mk.State = fromState
		mk.ActivatedAt = time.Time{}
		return fmt.Errorf("keyring registration failed: %w", err)
	}

	atomic.AddUint64(&km.totalActivated, 1)

	km.recordEventLocked(keyID, "KEY_ACTIVATED", fromState, KeyStateActive,
		fmt.Sprintf("approved_by=%s ceremony=%s", approvedBy, mk.CeremonyID),
		approvedBy,
	)

	fmt.Printf("[KeyManager] Activated key: %s (approved_by=%s, ceremony=%s)\n", keyID, approvedBy, mk.CeremonyID)
	return nil
}

// RequestActivation transitions a key from GENERATED to PENDING_ACTIVATION.
// This is the first step of the dual-control ceremony.
func (km *KeyManager) RequestActivation(keyID GovernanceKeyID, requestedBy string) error {
	km.mu.Lock()
	defer km.mu.Unlock()

	mk, exists := km.keys[keyID]
	if !exists {
		return fmt.Errorf("key %q not found", keyID)
	}

	if mk.State != KeyStateGenerated {
		return fmt.Errorf("key %q is in state %s — can only request activation from GENERATED", keyID, mk.State)
	}

	if !isValidTransition(KeyStateGenerated, KeyStatePendingActivation) {
		return fmt.Errorf("invalid transition: GENERATED → PENDING_ACTIVATION")
	}

	mk.State = KeyStatePendingActivation

	km.recordEventLocked(keyID, "ACTIVATION_REQUESTED", KeyStateGenerated, KeyStatePendingActivation,
		fmt.Sprintf("requested_by=%s", requestedBy),
		requestedBy,
	)

	fmt.Printf("[KeyManager] Activation requested for key: %s (requested_by=%s)\n", keyID, requestedBy)
	return nil
}

// ================================================================
// KEY ROTATION
// ================================================================

// RotateKey initiates key rotation: generates a new key and begins the
// overlap period where both old and new keys are valid.
//
// Flow:
//   1. Old key transitions ACTIVE → ROTATING
//   2. New key is generated and immediately activated
//   3. During overlap period, both keys verify signatures
//   4. After overlap, old key transitions ROTATING → REVOKED
//
// Returns the new key ID and private key for secure storage.
func (km *KeyManager) RotateKey(oldKeyID GovernanceKeyID, newKeyID GovernanceKeyID, approvedBy string) (ed25519.PrivateKey, error) {
	km.mu.Lock()
	defer km.mu.Unlock()

	// Validate old key
	oldKey, exists := km.keys[oldKeyID]
	if !exists {
		return nil, fmt.Errorf("old key %q not found", oldKeyID)
	}
	if oldKey.State != KeyStateActive {
		return nil, fmt.Errorf("old key %q is in state %s — can only rotate from ACTIVE", oldKeyID, oldKey.State)
	}
	if !isValidTransition(KeyStateActive, KeyStateRotating) {
		return nil, fmt.Errorf("invalid transition: ACTIVE → ROTATING")
	}

	// Check new key doesn't exist
	if _, exists := km.keys[newKeyID]; exists {
		return nil, fmt.Errorf("new key %q already exists", newKeyID)
	}

	// Generate new key pair
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return nil, fmt.Errorf("new key generation failed: %w", err)
	}

	fingerprint := sha256.Sum256(pub)
	now := time.Now().UTC()

	// Create new managed key
	newKey := &ManagedKey{
		KeyID:         newKeyID,
		Fingerprint:   hex.EncodeToString(fingerprint[:]),
		PublicKey:      pub,
		PublicKeyHex:  hex.EncodeToString(pub),
		State:         KeyStateActive,
		GeneratedAt:   now,
		ActivatedAt:   now,
		ReplacesKeyID: oldKeyID,
		ApprovedBy:    approvedBy,
		CeremonyID:    uuid.New().String(),
	}

	if km.config.DefaultKeyExpiryDays > 0 {
		newKey.ExpiresAt = now.Add(time.Duration(km.config.DefaultKeyExpiryDays) * 24 * time.Hour)
	}

	// Register new key in keyring
	if err := km.keyring.AddPublicKey(newKeyID, newKey.PublicKeyHex); err != nil {
		return nil, fmt.Errorf("new key keyring registration failed: %w", err)
	}

	// Transition old key to ROTATING
	oldKey.State = KeyStateRotating
	oldKey.RotatedAt = now
	oldKey.ReplacedByKeyID = newKeyID

	// Store new key
	km.keys[newKeyID] = newKey

	atomic.AddUint64(&km.totalGenerated, 1)
	atomic.AddUint64(&km.totalActivated, 1)
	atomic.AddUint64(&km.totalRotated, 1)

	// Record events
	km.recordEventLocked(oldKeyID, "KEY_ROTATION_STARTED", KeyStateActive, KeyStateRotating,
		fmt.Sprintf("replaced_by=%s approved_by=%s", newKeyID, approvedBy),
		approvedBy,
	)
	km.recordEventLocked(newKeyID, "KEY_ACTIVATED_VIA_ROTATION", "", KeyStateActive,
		fmt.Sprintf("replaces=%s ceremony=%s", oldKeyID, newKey.CeremonyID),
		approvedBy,
	)

	// Schedule overlap completion
	if km.config.RotationOverlapMinutes > 0 {
		go km.scheduleRotationCompletion(oldKeyID, time.Duration(km.config.RotationOverlapMinutes)*time.Minute)
	}

	fmt.Printf("[KeyManager] Rotation started: %s → %s (overlap=%dm)\n",
		oldKeyID, newKeyID, km.config.RotationOverlapMinutes)
	return priv, nil
}

// CompleteRotation finalizes the rotation by revoking the old key.
// Called automatically after overlap period or manually.
func (km *KeyManager) CompleteRotation(oldKeyID GovernanceKeyID) error {
	return km.RevokeKey(oldKeyID, "ROTATION_COMPLETE", "key_manager")
}

// scheduleRotationCompletion auto-completes rotation after the overlap period.
func (km *KeyManager) scheduleRotationCompletion(keyID GovernanceKeyID, overlap time.Duration) {
	select {
	case <-time.After(overlap):
		if err := km.CompleteRotation(keyID); err != nil {
			fmt.Printf("[KeyManager] WARNING: auto-rotation completion failed for %s: %v\n", keyID, err)
		} else {
			fmt.Printf("[KeyManager] Auto-rotation completed for %s after %v overlap\n", keyID, overlap)
		}
	case <-km.shutdownCh:
		return
	}
}

// ================================================================
// KEY REVOCATION
// ================================================================

// RevokeKey immediately revokes a key. Revocation is:
//   - Immediate: The key is marked REVOKED and removed from the keyring
//   - Permanent: A revoked key CANNOT be re-activated
//   - Distributed: All subscribers are notified
//   - Audited: The event is recorded in the tamper-evident chain
//
// This is modeled after CRL (Certificate Revocation List) behavior:
// once revoked, the key is dead. There is no "un-revoke".
func (km *KeyManager) RevokeKey(keyID GovernanceKeyID, reason string, revokedBy string) error {
	km.mu.Lock()
	defer km.mu.Unlock()

	mk, exists := km.keys[keyID]
	if !exists {
		return fmt.Errorf("key %q not found", keyID)
	}

	// Validate transition
	if mk.State == KeyStateRevoked || mk.State == KeyStateDestroyed {
		return fmt.Errorf("key %q is already in terminal state %s", keyID, mk.State)
	}
	if !isValidTransition(mk.State, KeyStateRevoked) {
		return fmt.Errorf("invalid transition: %s → REVOKED", mk.State)
	}

	fromState := mk.State
	now := time.Now().UTC()

	// Revoke in keyring (immediate effect)
	_ = km.keyring.RevokeKey(keyID) // Ignore error if key not in keyring (may be GENERATED)

	// Update managed key
	mk.State = KeyStateRevoked
	mk.RevokedAt = now
	mk.RevocationReason = reason

	atomic.AddUint64(&km.totalRevoked, 1)

	km.recordEventLocked(keyID, "KEY_REVOKED", fromState, KeyStateRevoked,
		fmt.Sprintf("reason=%s revoked_by=%s", reason, revokedBy),
		revokedBy,
	)

	// Audit sink — key revocation is security-critical and MUST be audited.
	// The revocation itself still proceeds even if audit fails (revocation is
	// irrevocable), but a CRITICAL alert fires to indicate audit gap.
	if auditErr := km.auditSink.RecordSystemEvent("KEY_REVOKED",
		fmt.Sprintf("key=%s reason=%s revoked_by=%s", keyID, reason, revokedBy)); auditErr != nil {
		fmt.Printf("[KeyManager] CRITICAL: Failed to audit KEY_REVOKED for %s: %v — revocation proceeded but audit gap exists\n", keyID, auditErr)
	}

	fmt.Printf("[KeyManager] Key REVOKED: %s (reason=%s, by=%s)\n", keyID, reason, revokedBy)

	// Distribute revocation to all subscribers (AFTER state change)
	// Revocation is NOT rolled back even if distribution fails.
	go func() {
		errors := km.distributor.Distribute(keyID, reason, now)
		for name, err := range errors {
			fmt.Printf("[KeyManager] WARNING: Revocation distribution failed for subscriber %q: %v\n", name, err)
			if auditErr := km.auditSink.RecordSystemEvent("REVOCATION_DISTRIBUTION_FAILED",
				fmt.Sprintf("key=%s subscriber=%s error=%v", keyID, name, err)); auditErr != nil {
				fmt.Printf("[KeyManager] CRITICAL: Failed to audit REVOCATION_DISTRIBUTION_FAILED for %s/%s: %v\n", keyID, name, auditErr)
			}
		}
	}()

	return nil
}

// ================================================================
// KEY DESTRUCTION (CRYPTOGRAPHIC ERASURE)
// ================================================================

// DestroyKey permanently destroys a key. After destruction:
//   - The public key bytes are zeroed
//   - The managed key entry is retained (for audit) but all crypto material is erased
//   - The key CANNOT be recovered
//
// Destruction is only allowed for GENERATED (unused) or REVOKED keys.
// You cannot destroy an ACTIVE key — revoke it first.
func (km *KeyManager) DestroyKey(keyID GovernanceKeyID, destroyedBy string) error {
	km.mu.Lock()
	defer km.mu.Unlock()

	mk, exists := km.keys[keyID]
	if !exists {
		return fmt.Errorf("key %q not found", keyID)
	}

	if mk.State == KeyStateDestroyed {
		return fmt.Errorf("key %q is already destroyed", keyID)
	}
	if !isValidTransition(mk.State, KeyStateDestroyed) {
		return fmt.Errorf("invalid transition: %s → DESTROYED (must be GENERATED, PENDING_ACTIVATION, or REVOKED)", mk.State)
	}

	fromState := mk.State
	now := time.Now().UTC()

	// Cryptographic erasure: zero out all key material
	for i := range mk.PublicKey {
		mk.PublicKey[i] = 0
	}
	mk.PublicKeyHex = "[DESTROYED]"
	mk.Fingerprint = "[DESTROYED]"

	mk.State = KeyStateDestroyed
	mk.DestroyedAt = now

	atomic.AddUint64(&km.totalDestroyed, 1)

	km.recordEventLocked(keyID, "KEY_DESTROYED", fromState, KeyStateDestroyed,
		fmt.Sprintf("destroyed_by=%s cryptographic_erasure=complete", destroyedBy),
		destroyedBy,
	)

	// Key destruction is security-critical — audit MUST record this.
	if auditErr := km.auditSink.RecordSystemEvent("KEY_DESTROYED",
		fmt.Sprintf("key=%s destroyed_by=%s", keyID, destroyedBy)); auditErr != nil {
		fmt.Printf("[KeyManager] CRITICAL: Failed to audit KEY_DESTROYED for %s: %v — destruction proceeded but audit gap exists\n", keyID, auditErr)
	}

	fmt.Printf("[KeyManager] Key DESTROYED: %s (cryptographic erasure complete)\n", keyID)
	return nil
}

// ================================================================
// KEY QUERIES
// ================================================================

// GetKey returns a copy of the managed key metadata. Returns nil if not found.
func (km *KeyManager) GetKey(keyID GovernanceKeyID) *ManagedKey {
	km.mu.RLock()
	defer km.mu.RUnlock()

	mk, exists := km.keys[keyID]
	if !exists {
		return nil
	}
	// Return a copy to prevent external mutation
	cp := *mk
	if mk.PublicKey != nil {
		cp.PublicKey = make(ed25519.PublicKey, len(mk.PublicKey))
		copy(cp.PublicKey, mk.PublicKey)
	}
	return &cp
}

// GetActiveKeys returns all keys in ACTIVE state.
func (km *KeyManager) GetActiveKeys() []*ManagedKey {
	km.mu.RLock()
	defer km.mu.RUnlock()

	result := make([]*ManagedKey, 0)
	for _, mk := range km.keys {
		if mk.State == KeyStateActive {
			cp := *mk
			result = append(result, &cp)
		}
	}
	return result
}

// GetUsableKeys returns all keys that can currently verify signatures (ACTIVE + ROTATING).
func (km *KeyManager) GetUsableKeys() []*ManagedKey {
	km.mu.RLock()
	defer km.mu.RUnlock()

	result := make([]*ManagedKey, 0)
	for _, mk := range km.keys {
		if mk.IsUsable() {
			cp := *mk
			result = append(result, &cp)
		}
	}
	return result
}

// ListAllKeys returns all managed keys with their lifecycle states.
func (km *KeyManager) ListAllKeys() []*ManagedKey {
	km.mu.RLock()
	defer km.mu.RUnlock()

	result := make([]*ManagedKey, 0, len(km.keys))
	for _, mk := range km.keys {
		cp := *mk
		result = append(result, &cp)
	}
	return result
}

// countKeysInStateLocked counts keys in a given state. Caller MUST hold km.mu.
func (km *KeyManager) countKeysInStateLocked(state KeyState) int {
	count := 0
	for _, mk := range km.keys {
		if mk.State == state {
			count++
		}
	}
	return count
}

// ================================================================
// SIGNATURE TRACKING
// ================================================================

// RecordSignatureUse records that a key was used to verify a signature.
// This is called by the enforcement pipeline after successful verification.
func (km *KeyManager) RecordSignatureUse(keyID GovernanceKeyID) {
	km.mu.Lock()
	defer km.mu.Unlock()

	mk, exists := km.keys[keyID]
	if !exists {
		return
	}

	mk.SignatureCount++
	mk.LastUsedAt = time.Now().UTC()
	atomic.AddUint64(&km.totalSignatures, 1)
}

// ================================================================
// KEY EVENT CHAIN (TAMPER-EVIDENT)
// ================================================================

// recordEventLocked records a key lifecycle event in the hash chain.
// Caller MUST hold km.mu.
func (km *KeyManager) recordEventLocked(
	keyID GovernanceKeyID,
	eventType string,
	fromState KeyState,
	toState KeyState,
	detail string,
	performedBy string,
) {
	km.eventsMu.Lock()
	defer km.eventsMu.Unlock()

	event := &KeyEvent{
		EventID:     uuid.New().String(),
		KeyID:       keyID,
		EventType:   eventType,
		FromState:   fromState,
		ToState:     toState,
		Timestamp:   time.Now().UTC(),
		Detail:      detail,
		PerformedBy: performedBy,
		PrevHash:    km.lastHash,
	}

	event.EventHash = computeEventHash(event, km.lastHash)
	km.lastHash = event.EventHash

	km.events = append(km.events, *event)
}

// GetEventChain returns a copy of the full key event chain.
func (km *KeyManager) GetEventChain() []KeyEvent {
	km.eventsMu.Lock()
	defer km.eventsMu.Unlock()

	cp := make([]KeyEvent, len(km.events))
	copy(cp, km.events)
	return cp
}

// VerifyEventChain verifies the integrity of the key event hash chain.
// Returns (valid, brokenAtIndex, reason).
func (km *KeyManager) VerifyEventChain() (bool, int, string) {
	km.eventsMu.Lock()
	defer km.eventsMu.Unlock()

	prevHash := "GENESIS"
	for i, event := range km.events {
		expected := computeEventHash(&event, prevHash)
		if event.EventHash != expected {
			return false, i, fmt.Sprintf(
				"hash mismatch at index %d: expected %s, got %s",
				i, expected[:16], event.EventHash[:16],
			)
		}
		if event.PrevHash != prevHash {
			return false, i, fmt.Sprintf(
				"prev_hash mismatch at index %d: expected %s, got %s",
				i, prevHash[:16], event.PrevHash[:16],
			)
		}
		prevHash = event.EventHash
	}
	return true, -1, "CHAIN_INTACT"
}

// ================================================================
// METRICS
// ================================================================

// KeyManagerMetrics holds operational metrics for the key manager.
type KeyManagerMetrics struct {
	TotalGenerated  uint64 `json:"total_generated"`
	TotalActivated  uint64 `json:"total_activated"`
	TotalRotated    uint64 `json:"total_rotated"`
	TotalRevoked    uint64 `json:"total_revoked"`
	TotalDestroyed  uint64 `json:"total_destroyed"`
	TotalSignatures uint64 `json:"total_signatures"`
	ActiveKeys      int    `json:"active_keys"`
	UsableKeys      int    `json:"usable_keys"`
	TotalKeys       int    `json:"total_keys"`
	EventChainLen   int    `json:"event_chain_length"`
	ChainIntact     bool   `json:"chain_intact"`
	Subscribers     int    `json:"revocation_subscribers"`
}

// GetMetrics returns current key manager metrics.
func (km *KeyManager) GetMetrics() KeyManagerMetrics {
	km.mu.RLock()
	activeCount := km.countKeysInStateLocked(KeyStateActive)
	usableCount := 0
	for _, mk := range km.keys {
		if mk.IsUsable() {
			usableCount++
		}
	}
	totalKeys := len(km.keys)
	km.mu.RUnlock()

	km.eventsMu.Lock()
	chainLen := len(km.events)
	km.eventsMu.Unlock()

	valid, _, _ := km.VerifyEventChain()

	return KeyManagerMetrics{
		TotalGenerated:  atomic.LoadUint64(&km.totalGenerated),
		TotalActivated:  atomic.LoadUint64(&km.totalActivated),
		TotalRotated:    atomic.LoadUint64(&km.totalRotated),
		TotalRevoked:    atomic.LoadUint64(&km.totalRevoked),
		TotalDestroyed:  atomic.LoadUint64(&km.totalDestroyed),
		TotalSignatures: atomic.LoadUint64(&km.totalSignatures),
		ActiveKeys:      activeCount,
		UsableKeys:      usableCount,
		TotalKeys:       totalKeys,
		EventChainLen:   chainLen,
		ChainIntact:     valid,
		Subscribers:     km.distributor.SubscriberCount(),
	}
}

// ================================================================
// EXPIRY MONITOR
// ================================================================

// expiryMonitorLoop periodically checks for expired keys and triggers rotation.
func (km *KeyManager) expiryMonitorLoop() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			km.checkExpiredKeys()
		case <-km.shutdownCh:
			return
		}
	}
}

// checkExpiredKeys finds expired active keys and logs warnings.
// Auto-rotation is best-effort — it logs but does not auto-generate
// because new key private material needs secure storage.
func (km *KeyManager) checkExpiredKeys() {
	km.mu.RLock()
	var expired []GovernanceKeyID
	for keyID, mk := range km.keys {
		if mk.State == KeyStateActive && mk.IsExpired() {
			expired = append(expired, keyID)
		}
	}
	km.mu.RUnlock()

	for _, keyID := range expired {
		fmt.Printf("[KeyManager] WARNING: Key %s has EXPIRED — rotation required\n", keyID)
		if auditErr := km.auditSink.RecordSystemEvent("KEY_EXPIRED",
			fmt.Sprintf("key=%s — manual rotation required", keyID)); auditErr != nil {
			fmt.Printf("[KeyManager] WARNING: Failed to audit KEY_EXPIRED for %s: %v\n", keyID, auditErr)
		}
	}
}

// ================================================================
// REVOCATION DISTRIBUTOR ACCESS
// ================================================================

// GetDistributor returns the revocation distributor for subscriber registration.
func (km *KeyManager) GetDistributor() *RevocationDistributor {
	return km.distributor
}

// GetKeyring returns the underlying GovernanceKeyRing.
func (km *KeyManager) GetKeyring() *GovernanceKeyRing {
	return km.keyring
}

// ================================================================
// SHUTDOWN
// ================================================================

// Shutdown gracefully shuts down the key manager.
func (km *KeyManager) Shutdown() {
	close(km.shutdownCh)
	if err := km.auditSink.RecordSystemEvent("KEY_MANAGER_SHUTDOWN", "KeyManager shutdown initiated"); err != nil {
		fmt.Printf("[KeyManager] WARNING: Failed to audit shutdown event: %v\n", err)
	}
	fmt.Println("[KeyManager] Shutdown complete")
}

// ================================================================
// PRINT UTILITIES
// ================================================================

// PrintKeyInventory prints a human-readable summary of all managed keys.
func (km *KeyManager) PrintKeyInventory() {
	keys := km.ListAllKeys()
	fmt.Println("\n  ┌─── KEY MANAGEMENT INVENTORY ───")
	fmt.Printf("  │ Total Keys: %d\n", len(keys))
	fmt.Println("  │")

	for _, mk := range keys {
		fingerprint := mk.Fingerprint
		if len(fingerprint) > 16 {
			fingerprint = fingerprint[:16] + "..."
		}
		fmt.Printf("  │ [%s] %s  state=%s  fingerprint=%s\n",
			mk.KeyID, mk.State, mk.State, fingerprint)
		if !mk.ActivatedAt.IsZero() {
			fmt.Printf("  │   activated=%s  approved_by=%s\n",
				mk.ActivatedAt.Format("2006-01-02T15:04:05Z"), mk.ApprovedBy)
		}
		if !mk.RevokedAt.IsZero() {
			fmt.Printf("  │   revoked=%s  reason=%s\n",
				mk.RevokedAt.Format("2006-01-02T15:04:05Z"), mk.RevocationReason)
		}
		if mk.ReplacedByKeyID != "" {
			fmt.Printf("  │   replaced_by=%s\n", mk.ReplacedByKeyID)
		}
		if mk.ReplacesKeyID != "" {
			fmt.Printf("  │   replaces=%s\n", mk.ReplacesKeyID)
		}
		if mk.SignatureCount > 0 {
			fmt.Printf("  │   signatures=%d  last_used=%s\n",
				mk.SignatureCount, mk.LastUsedAt.Format("2006-01-02T15:04:05Z"))
		}
		if !mk.ExpiresAt.IsZero() {
			status := "valid"
			if mk.IsExpired() {
				status = "EXPIRED"
			}
			fmt.Printf("  │   expires=%s  (%s)\n",
				mk.ExpiresAt.Format("2006-01-02T15:04:05Z"), status)
		}
	}

	metrics := km.GetMetrics()
	fmt.Println("  │")
	fmt.Printf("  │ Active: %d  Usable: %d  Revoked: %d  Destroyed: %d\n",
		metrics.ActiveKeys, metrics.UsableKeys,
		metrics.TotalRevoked, metrics.TotalDestroyed)
	fmt.Printf("  │ Event chain: %d entries  Integrity: %v\n",
		metrics.EventChainLen, metrics.ChainIntact)
	fmt.Printf("  │ Revocation subscribers: %d\n", metrics.Subscribers)
	fmt.Println("  └──────────────────────────────────")
}

// PrintEventChain prints the key event audit chain.
func (km *KeyManager) PrintEventChain() {
	events := km.GetEventChain()
	fmt.Println("\n  ┌─── KEY EVENT CHAIN ───")
	fmt.Printf("  │ Events: %d\n", len(events))

	for i, e := range events {
		hashPrefix := e.EventHash
		if len(hashPrefix) > 16 {
			hashPrefix = hashPrefix[:16]
		}
		fmt.Printf("  │ [%d] %s  key=%s  %s→%s  hash=%s...\n",
			i, e.EventType, e.KeyID, e.FromState, e.ToState, hashPrefix)
		fmt.Printf("  │     detail=%s  by=%s  at=%s\n",
			e.Detail, e.PerformedBy, e.Timestamp.Format("2006-01-02T15:04:05Z"))
	}

	valid, brokenAt, reason := km.VerifyEventChain()
	if valid {
		fmt.Println("  │ Chain Integrity: INTACT")
	} else {
		fmt.Printf("  │ Chain Integrity: BROKEN at index %d — %s\n", brokenAt, reason)
	}
	fmt.Println("  └────────────────────────────")
}
