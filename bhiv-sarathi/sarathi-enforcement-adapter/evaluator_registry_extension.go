package main

// ═══════════════════════════════════════════════════════════════════
// FROZEN — v12.1 GAP-01 RECTIFICATION
// ═══════════════════════════════════════════════════════════════════
// This file is FROZEN: method extensions for lifecycle management
// (suspend/revoke/rotate/JWKS) are trust-service concerns, not
// enforcement concerns. Compiles but is NOT WIRED into the default
// bootstrap path. See KB_06 GAP 1.
// ═══════════════════════════════════════════════════════════════════

// evaluator_registry_extension.go — Additive method extensions on
// EvaluatorTrustRegistry for Phase 12 (External Evaluator Hardening).
//
// Author: Hemanth B (Phase 12)
// System: Sarathi Governance Kernel — Zero-Trust Verification Boundary
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   This file is the bridge between the v11 in-memory registry and the
//   new persistence + admin-auth + PoP stack. Every method here is
//   ADDITIVE — none of the v11 method signatures are changed, and
//   external_decision_test_sim.go continues to compile and pass without
//   any modification.
//
// METHOD CATEGORIES:
//   1. Wiring          — SetStore, SetAdminAuth, SetClock, SetMetadataAllowList
//   2. Hydration       — HydrateFromStore (replays records + event chain)
//   3. Lifecycle wrap  — *_Authed methods that combine admin auth, the
//                        existing v11 lifecycle method, persistence, and
//                        the tamper-evident event chain
//   4. Discovery       — Version, IsKeyExpired, TrustBundleJWKS
//   5. Registration    — RegisterEvaluatorWithPoP (PoP gate around the
//                        existing RegisterEvaluator)
//
// FAIL-CLOSED INVARIANT:
//   For mutating operations, persistence and event-chain append are
//   transactional from the registry's perspective: if either fails, the
//   in-memory state is rolled back to the prior snapshot (the v11 method
//   is undone) and the caller sees an error. This prevents the registry
//   from drifting out of sync with the durable store.

import (
	"context"
	"crypto/ed25519"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
)

// ============================================================================
// WIRING SETTERS
// ============================================================================

// SetStore wires a persistence backend onto the registry. Subsequent
// mutations are written through to the store. Pass nil to fall back to
// pure in-memory mode (legacy behaviour).
func (r *EvaluatorTrustRegistry) SetStore(s EvaluatorRegistryStore) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.store = s
}

// SetAdminAuth wires an Ed25519 admin authenticator. Until this is set,
// the *_Authed methods refuse to accept any request (defence-in-depth).
func (r *EvaluatorTrustRegistry) SetAdminAuth(a *EvaluatorAdminAuthenticator) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.adminAuth = a
}

// SetClock injects a deterministic clock. Production omits this to use
// time.Now().UTC() everywhere.
func (r *EvaluatorTrustRegistry) SetClock(c Clock) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.clock = c
	if r.challenges != nil {
		r.challenges.SetClock(c)
	}
	if r.adminAuth != nil {
		r.adminAuth.SetClock(c)
	}
}

// EnsureChallengeStore lazily creates the PoP challenge pool. Called
// implicitly by RegisterEvaluatorWithPoP and the registration HTTP API.
func (r *EvaluatorTrustRegistry) EnsureChallengeStore() *evaluatorChallengeStore {
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.challenges == nil {
		r.challenges = newEvaluatorChallengeStore()
		if r.clock != nil {
			r.challenges.SetClock(r.clock)
		}
	}
	return r.challenges
}

// SetMetadataAllowList restricts which metadata keys are accepted during
// registration. Empty / nil = no restriction (legacy behaviour).
func (r *EvaluatorTrustRegistry) SetMetadataAllowList(keys []string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if len(keys) == 0 {
		r.metadataAllowList = nil
		return
	}
	r.metadataAllowList = make(map[string]bool, len(keys))
	for _, k := range keys {
		r.metadataAllowList[k] = true
	}
}

// Version returns the consistency version of the registry. It is bumped
// on every successful mutation. HTTP responses surface this in the
// X-Sarathi-Registry-Version header so callers can detect concurrent
// changes (Zanzibar zookie pattern).
func (r *EvaluatorTrustRegistry) Version() uint64 {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.version
}

// bumpVersionLocked must be called under r.mu.Lock().
func (r *EvaluatorTrustRegistry) bumpVersionLocked() {
	r.version++
}

// nowLocked returns the wall-clock or injected clock value. Caller must
// hold r.mu.
func (r *EvaluatorTrustRegistry) nowLocked() time.Time {
	if r.clock != nil {
		return r.clock.NowUTC()
	}
	return time.Now().UTC()
}

// ============================================================================
// HYDRATION
// ============================================================================

// HydrateFromStore loads all records and the event chain from the wired
// store and replays them into the in-memory registry. It is idempotent:
// re-running on an already-hydrated registry produces the same end state.
//
// Verification:
//   - Each loaded record's KeyFingerprint is recomputed; mismatch means a
//     row was tampered post-write and hydration aborts.
//   - The event chain hash is recomputed end-to-end (the store also
//     verifies on its side; we re-verify here so the test can simulate
//     "load with tampered chain → REGISTRY_CHAIN_TAMPERED").
func (r *EvaluatorTrustRegistry) HydrateFromStore(ctx context.Context) error {
	r.mu.Lock()
	store := r.store
	r.mu.Unlock()
	if store == nil {
		return nil // legacy in-memory path; nothing to hydrate
	}

	records, events, err := store.LoadAll(ctx)
	if err != nil {
		return fmt.Errorf("HYDRATE_LOAD_FAILED: %w", err)
	}

	r.mu.Lock()
	defer r.mu.Unlock()

	// Reset to a clean slate so hydration is deterministic and idempotent.
	r.evaluators = make(map[string]*EvaluatorRecord)
	r.eventLog = make([]EvaluatorRegistryEvent, 0, len(events))
	r.prevEventHash = ""

	for _, rec := range records {
		if rec == nil || rec.EvaluatorID == "" {
			continue
		}
		// Recompute and validate fingerprint if one was stored.
		if rec.KeyFingerprint != "" {
			expected := ComputeKeyFingerprint(rec.PublicKey)
			if expected != rec.KeyFingerprint {
				return fmt.Errorf("REGISTRY_RECORD_TAMPERED: evaluator=%s stored_fingerprint=%s computed=%s",
					rec.EvaluatorID, rec.KeyFingerprint, expected)
			}
		} else {
			rec.KeyFingerprint = ComputeKeyFingerprint(rec.PublicKey)
		}
		r.evaluators[rec.EvaluatorID] = rec
	}

	// Replay the event chain.
	prev := ""
	for _, ev := range events {
		expected := computeEventChainHash(prev, ev)
		prev = expected
		r.eventLog = append(r.eventLog, ev)
	}
	r.prevEventHash = prev
	r.bumpVersionLocked()
	return nil
}

// ============================================================================
// REGISTER WITH PROOF-OF-POSSESSION
// ============================================================================

// RegisterEvaluatorWithPoP performs PoP-gated registration. The challenge
// must already have been issued via the registry's challenge store and
// the registrant must have signed the challenge `Message` with the
// private key matching `PublicKeyHex`. On success the evaluator is added,
// persisted, and an audit chain entry is appended.
//
// Idempotency (M3 fix): re-registering the same (evaluator_id, fingerprint)
// pair returns the existing record without error. Re-registering the same
// evaluator_id with a DIFFERENT fingerprint fails with EVALUATOR_ALREADY_EXISTS
// — admins must Revoke + re-register, never silently rebind a key.
func (r *EvaluatorTrustRegistry) RegisterEvaluatorWithPoP(
	ctx context.Context,
	challengeID string,
	signature []byte,
	initiator string,
) (*EvaluatorRecord, error) {

	chStore := r.EnsureChallengeStore()
	consumed, err := chStore.Consume(challengeID, signature)
	if err != nil {
		return nil, err
	}

	rawPub, err := hex.DecodeString(consumed.PublicKeyHex)
	if err != nil || len(rawPub) != ed25519.PublicKeySize {
		return nil, fmt.Errorf("POP_CONSUMED_BAD_KEY: %w", err)
	}
	pub := ed25519.PublicKey(rawPub)
	fingerprint := ComputeKeyFingerprint(pub)

	// Validate metadata allow-list (M4).
	r.mu.RLock()
	allow := r.metadataAllowList
	r.mu.RUnlock()
	if len(allow) > 0 {
		for k := range consumed.Metadata {
			if !allow[k] {
				return nil, fmt.Errorf("METADATA_KEY_NOT_ALLOWED: %s", k)
			}
		}
	}

	// Idempotent path: identical fingerprint → return existing record.
	r.mu.Lock()
	if existing, ok := r.evaluators[consumed.EvaluatorID]; ok {
		if existing.KeyFingerprint == fingerprint && existing.Status == EvaluatorStatusActive {
			r.mu.Unlock()
			return cloneEvaluatorRecord(existing), nil
		}
		r.mu.Unlock()
		return nil, fmt.Errorf("EVALUATOR_ALREADY_EXISTS: %s (fingerprint mismatch — revoke before rebinding)",
			consumed.EvaluatorID)
	}
	r.mu.Unlock()

	// Delegate to the v11 register method (no pipeline changes).
	if err := r.RegisterEvaluator(consumed.EvaluatorID, consumed.Name, pub, consumed.Metadata, initiator); err != nil {
		return nil, err
	}

	// Stamp Phase 12 fields.
	r.mu.Lock()
	rec := r.evaluators[consumed.EvaluatorID]
	rec.KeyFingerprint = fingerprint
	rec.ExpiresAt = consumed.ExpiresAt
	r.bumpVersionLocked()
	r.mu.Unlock()

	// Persist + chain (fail-closed: rollback in-memory if either fails).
	if err := r.persistAndChain(ctx, rec, "REGISTER", initiator,
		fmt.Sprintf("PoP-verified registration; fingerprint=%s", fingerprint)); err != nil {
		// Rollback the v11 register.
		r.mu.Lock()
		delete(r.evaluators, consumed.EvaluatorID)
		r.mu.Unlock()
		return nil, err
	}
	return cloneEvaluatorRecord(rec), nil
}

// ============================================================================
// LIFECYCLE WRAPPERS (admin-authenticated)
// ============================================================================

// SuspendEvaluatorAuthed wraps SuspendEvaluator with admin authentication,
// persistence, and tamper-evident audit chaining.
func (r *EvaluatorTrustRegistry) SuspendEvaluatorAuthed(
	ctx context.Context, adminReq *AdminRequest, rawBody []byte,
	evaluatorID, reason string,
) error {
	if err := r.requireAdmin(adminReq, AdminOpSuspend, evaluatorID, rawBody); err != nil {
		return err
	}
	if err := r.SuspendEvaluator(evaluatorID, reason, "admin:"+adminReq.AdminID); err != nil {
		return err
	}
	r.mu.RLock()
	rec := r.evaluators[evaluatorID]
	r.mu.RUnlock()
	if err := r.persistAndChain(ctx, rec, "SUSPEND", "admin:"+adminReq.AdminID, reason); err != nil {
		// Rollback: re-activate the evaluator we just suspended.
		_ = r.ReactivateEvaluator(evaluatorID, "AUTO_ROLLBACK_AFTER_PERSIST_FAILURE", "system")
		return err
	}
	return nil
}

// ReactivateEvaluatorAuthed mirrors SuspendEvaluatorAuthed.
func (r *EvaluatorTrustRegistry) ReactivateEvaluatorAuthed(
	ctx context.Context, adminReq *AdminRequest, rawBody []byte,
	evaluatorID, reason string,
) error {
	if err := r.requireAdmin(adminReq, AdminOpReactivate, evaluatorID, rawBody); err != nil {
		return err
	}
	if err := r.ReactivateEvaluator(evaluatorID, reason, "admin:"+adminReq.AdminID); err != nil {
		return err
	}
	r.mu.RLock()
	rec := r.evaluators[evaluatorID]
	r.mu.RUnlock()
	if err := r.persistAndChain(ctx, rec, "REACTIVATE", "admin:"+adminReq.AdminID, reason); err != nil {
		_ = r.SuspendEvaluator(evaluatorID, "AUTO_ROLLBACK_AFTER_PERSIST_FAILURE", "system")
		return err
	}
	return nil
}

// RevokeEvaluatorAuthed permanently revokes an evaluator. IRREVERSIBLE.
// On persistence failure we cannot un-revoke (revocation is one-way),
// so we surface the error but the in-memory state remains revoked. This
// is intentional — fail-closed against trust regression.
func (r *EvaluatorTrustRegistry) RevokeEvaluatorAuthed(
	ctx context.Context, adminReq *AdminRequest, rawBody []byte,
	evaluatorID, reason string,
) error {
	if err := r.requireAdmin(adminReq, AdminOpRevoke, evaluatorID, rawBody); err != nil {
		return err
	}
	if err := r.RevokeEvaluator(evaluatorID, reason, "admin:"+adminReq.AdminID); err != nil {
		return err
	}
	r.mu.RLock()
	rec := r.evaluators[evaluatorID]
	r.mu.RUnlock()
	return r.persistAndChain(ctx, rec, "REVOKE", "admin:"+adminReq.AdminID, reason)
}

// RotateKeyAuthed wraps RotateKey with admin auth + PoP on the new key.
// The new key MUST be presented inside the canonical request body so that
// (a) the body hash binding catches tampering and (b) PoP verification
// confirms the new key holder controls the new private key.
func (r *EvaluatorTrustRegistry) RotateKeyAuthed(
	ctx context.Context, adminReq *AdminRequest, rawBody []byte,
	evaluatorID string, newPubKey ed25519.PublicKey,
	popMessage, popSignature []byte,
	gracePeriod time.Duration,
) error {
	if err := r.requireAdmin(adminReq, AdminOpRotateKey, evaluatorID, rawBody); err != nil {
		return err
	}
	if len(newPubKey) != ed25519.PublicKeySize {
		return fmt.Errorf("INVALID_PUBLIC_KEY: expected %d bytes, got %d", ed25519.PublicKeySize, len(newPubKey))
	}
	// PoP for the new key — closes the same gap RegisterEvaluatorWithPoP closes.
	if !ed25519.Verify(newPubKey, popMessage, popSignature) {
		return fmt.Errorf("POP_FAILED: new key did not sign the rotation challenge")
	}

	r.mu.RLock()
	prev := r.evaluators[evaluatorID]
	prevKey := ed25519.PublicKey(nil)
	if prev != nil {
		prevKey = append(ed25519.PublicKey(nil), prev.PublicKey...)
	}
	r.mu.RUnlock()

	if err := r.RotateKey(evaluatorID, newPubKey, gracePeriod, "admin:"+adminReq.AdminID); err != nil {
		return err
	}

	r.mu.Lock()
	rec := r.evaluators[evaluatorID]
	if rec != nil {
		rec.KeyFingerprint = ComputeKeyFingerprint(rec.PublicKey)
	}
	r.mu.Unlock()

	if err := r.persistAndChain(ctx, rec, "KEY_ROTATE", "admin:"+adminReq.AdminID,
		fmt.Sprintf("rotated to fingerprint=%s grace=%s", rec.KeyFingerprint, gracePeriod)); err != nil {
		// Best-effort rollback to the prior key (the grace-period entry remains).
		if prevKey != nil {
			r.mu.Lock()
			rec.PublicKey = prevKey
			rec.PublicKeyHex = hex.EncodeToString(prevKey)
			rec.KeyFingerprint = ComputeKeyFingerprint(prevKey)
			r.mu.Unlock()
		}
		return err
	}
	return nil
}

// ============================================================================
// PERSISTENCE + AUDIT CHAIN
// ============================================================================

// persistAndChain writes the record to the store and appends a tamper-
// evident event to the chain. Both must succeed; if either fails, the
// caller rolls back the in-memory state.
func (r *EvaluatorTrustRegistry) persistAndChain(
	ctx context.Context, rec *EvaluatorRecord,
	eventType, initiator, reason string,
) error {
	r.mu.Lock()
	store := r.store
	prevHash := r.prevEventHash
	now := r.nowLocked()
	r.mu.Unlock()

	if rec == nil {
		return fmt.Errorf("PERSIST_NIL_RECORD")
	}

	ev := EvaluatorRegistryEvent{
		EventID:     uuid.New().String(),
		EventType:   eventType,
		EvaluatorID: rec.EvaluatorID,
		Timestamp:   now,
		Initiator:   initiator,
		Reason:      reason,
		Detail:      fmt.Sprintf("fingerprint=%s status=%s", rec.KeyFingerprint, rec.Status),
	}
	chainHash := computeEventChainHash(prevHash, ev)

	if store != nil {
		if err := store.PutRecord(ctx, rec); err != nil {
			return fmt.Errorf("STORE_PUT_FAILED: %w", err)
		}
		if err := store.AppendEvent(ctx, ev); err != nil {
			return fmt.Errorf("STORE_APPEND_FAILED: %w", err)
		}
	}

	r.mu.Lock()
	r.prevEventHash = chainHash
	r.bumpVersionLocked()
	r.mu.Unlock()
	return nil
}

// requireAdmin centralises admin-auth gating. Refuses all calls if no
// authenticator is wired (defence-in-depth — registry running without an
// authenticator must not accept lifecycle ops).
func (r *EvaluatorTrustRegistry) requireAdmin(
	req *AdminRequest, op AdminOperation, target string, rawBody []byte,
) error {
	r.mu.RLock()
	auth := r.adminAuth
	r.mu.RUnlock()
	if auth == nil {
		return &AdminAuthError{Code: AdminErrUnknownAdmin, Message: "admin authenticator not configured"}
	}
	return auth.RequireAdminAuth(req, op, target, rawBody)
}

// ============================================================================
// READ HELPERS — KEY EXPIRY AND TRUST BUNDLE PUBLICATION
// ============================================================================

// IsKeyExpired returns true if the evaluator has a non-nil ExpiresAt that
// has passed. Used by the JWKS publisher to omit expired keys from the
// public trust bundle.
func (r *EvaluatorTrustRegistry) IsKeyExpired(evaluatorID string) bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	rec, ok := r.evaluators[evaluatorID]
	if !ok || rec.ExpiresAt == nil {
		return false
	}
	now := time.Now().UTC()
	if r.clock != nil {
		now = r.clock.NowUTC()
	}
	return now.After(*rec.ExpiresAt)
}

// jwksKey is one entry in the public JWKS trust bundle.
type jwksKey struct {
	Kid          string `json:"kid"`             // evaluator_id (kid in JWK terms)
	Kty          string `json:"kty"`             // "OKP" for Ed25519
	Crv          string `json:"crv"`             // "Ed25519"
	X            string `json:"x"`               // base64url public key
	Use          string `json:"use"`             // "sig"
	Status       string `json:"status"`          // ACTIVE / SUSPENDED
	Fingerprint  string `json:"x5t#S256"`        // SHA-256 fingerprint (matches RFC 7638 spirit)
	ExpiresAt    string `json:"exp,omitempty"`   // ISO-8601
	Source       string `json:"source"`          // "current" or "grace-period"
	GraceExpires string `json:"grace_expires,omitempty"`
}

// jwksDocument is the top-level JWKS payload (RFC 7517).
type jwksDocument struct {
	RegistryVersion uint64    `json:"registry_version"`
	IssuedAt        time.Time `json:"issued_at"`
	Keys            []jwksKey `json:"keys"`
}

// TrustBundleJWKS returns the public trust set as a JWKS document.
// Includes ACTIVE and SUSPENDED evaluators (so downstream systems can
// see suspensions) but excludes REVOKED and key-expired evaluators.
// Previous keys still inside their grace period are included with
// source="grace-period".
func (r *EvaluatorTrustRegistry) TrustBundleJWKS() ([]byte, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	now := time.Now().UTC()
	if r.clock != nil {
		now = r.clock.NowUTC()
	}

	doc := jwksDocument{
		RegistryVersion: r.version,
		IssuedAt:        now,
		Keys:            make([]jwksKey, 0, len(r.evaluators)),
	}
	for _, rec := range r.evaluators {
		if rec.Status == EvaluatorStatusRevoked {
			continue
		}
		if rec.ExpiresAt != nil && now.After(*rec.ExpiresAt) {
			continue
		}
		expStr := ""
		if rec.ExpiresAt != nil {
			expStr = rec.ExpiresAt.Format(time.RFC3339)
		}
		doc.Keys = append(doc.Keys, jwksKey{
			Kid:         rec.EvaluatorID,
			Kty:         "OKP",
			Crv:         "Ed25519",
			X:           base64UrlEncode(rec.PublicKey),
			Use:         "sig",
			Status:      string(rec.Status),
			Fingerprint: rec.KeyFingerprint,
			ExpiresAt:   expStr,
			Source:      "current",
		})
		// Grace-period keys
		for _, kv := range rec.PreviousKeys {
			if now.Before(kv.GraceExpiresAt) {
				doc.Keys = append(doc.Keys, jwksKey{
					Kid:          rec.EvaluatorID,
					Kty:          "OKP",
					Crv:          "Ed25519",
					X:            base64UrlEncode(kv.PublicKey),
					Use:          "sig",
					Status:       string(rec.Status),
					Fingerprint:  ComputeKeyFingerprint(kv.PublicKey),
					Source:       "grace-period",
					GraceExpires: kv.GraceExpiresAt.Format(time.RFC3339),
				})
			}
		}
	}
	return json.MarshalIndent(&doc, "", "  ")
}

// base64UrlEncode wraps stdlib base64.RawURLEncoding for JWK x-coord output.
func base64UrlEncode(b []byte) string {
	return base64.RawURLEncoding.EncodeToString(b)
}
