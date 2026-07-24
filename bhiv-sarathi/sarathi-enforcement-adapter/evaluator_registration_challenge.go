package main

// ═══════════════════════════════════════════════════════════════════
// FROZEN — v12.1 GAP-01 RECTIFICATION
// ═══════════════════════════════════════════════════════════════════
// This file is FROZEN: PoP challenge/response is a registration flow,
// not a verification concern. It compiles but is NOT WIRED into the
// default bootstrap path. See KB_06 GAP 1.
// ═══════════════════════════════════════════════════════════════════

// evaluator_registration_challenge.go — Proof-of-possession challenge/
// response for evaluator self-registration.
//
// Author: Hemanth B (Phase 12 — External Evaluator Hardening)
// System: Sarathi Governance Kernel — Zero-Trust Verification Boundary
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   The v11 RegisterEvaluator() blindly trusted any caller with any public
//   key. An attacker who could reach the registration path could bind
//   their own controlled key under a legitimate evaluator_id. That key
//   would then pass Step 4 (SIGNATURE_VERIFICATION) of the 10-stage
//   pipeline forever. This file closes that gap (CRITICAL #C3) with an
//   ACME RFC 8555-style challenge/response: the registrant must prove
//   possession of the private key matching the public key they claim by
//   signing a server-issued challenge.
//
// FLOW:
//   1. Admin POSTs /v1/evaluators/register/challenge with the proposed
//      evaluator_id, name, public_key_hex, metadata. The admin auth
//      envelope guards this call (operation=REGISTER_INIT).
//   2. The server generates a random nonce, stores a Challenge with a
//      5-minute TTL, and returns the challenge bytes:
//        message = SHA256("BHIV-PoP|"||evaluator_id||"|"||pub_hex||"|"||nonce||"|"||expires_at)
//   3. The registrant signs `message` with the private key matching their
//      claimed public key.
//   4. Admin POSTs /v1/evaluators/register/complete with the signature.
//      The server verifies ed25519.Verify(claimed_pub, message, sig) and
//      then calls EvaluatorTrustRegistry.RegisterEvaluator(...).
//
// CHALLENGE STORE PROPERTIES:
//   - Single-use: a challenge is deleted on first consumption (no replay).
//   - TTL: 5 minutes default; expired challenges are pruned on every Issue.
//   - In-memory: challenges are ephemeral; restart cancels in-flight PoP
//     flows. This is acceptable because challenges are short-lived and
//     the registrant simply re-initiates.
//
// DESIGN REFERENCES:
//   - ACME RFC 8555 Section 8 (challenge-response identifier validation)
//   - X.509 CSR self-signature (proof-of-possession of subject key)
//   - WebAuthn attestation (FIDO2 PoP for credential registration)
//   - SPIFFE node attestation (cryptographic proof during workload onboarding)

import (
	"crypto/ed25519"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
)

// PoPChallenge is the bytes the registrant must sign with their private key.
type PoPChallenge struct {
	ChallengeID  string    `json:"challenge_id"`
	EvaluatorID  string    `json:"evaluator_id"`
	PublicKeyHex string    `json:"public_key_hex"`
	Name         string    `json:"name"`
	Metadata     map[string]string `json:"metadata,omitempty"`
	ExpiresAt    *time.Time `json:"evaluator_expires_at,omitempty"` // optional crypto period
	Nonce        string    `json:"nonce"`
	Message      string    `json:"message"`     // hex SHA-256 challenge bytes the registrant signs
	IssuedAt     time.Time `json:"issued_at"`
	ChallengeTTL time.Time `json:"challenge_ttl"` // when the challenge itself expires
}

// computePoPMessage returns the deterministic hex-SHA256 message bytes
// the registrant must sign. Domain-separated with the literal "BHIV-PoP"
// to prevent cross-protocol signature reuse.
func computePoPMessage(evaluatorID, pubHex, nonce string, expires *time.Time) string {
	expStr := ""
	if expires != nil {
		expStr = expires.UTC().Format(time.RFC3339Nano)
	}
	canonical := fmt.Sprintf("BHIV-PoP|v1|%s|%s|%s|%s",
		evaluatorID, pubHex, nonce, expStr)
	sum := sha256.Sum256([]byte(canonical))
	return hex.EncodeToString(sum[:])
}

// evaluatorChallengeStore is the in-memory pool of outstanding PoP
// challenges. It is referenced from EvaluatorTrustRegistry.challenges.
type evaluatorChallengeStore struct {
	mu         sync.Mutex
	challenges map[string]*PoPChallenge
	ttl        time.Duration
	clock      Clock
}

// newEvaluatorChallengeStore constructs an empty challenge pool with a
// 5-minute TTL.
func newEvaluatorChallengeStore() *evaluatorChallengeStore {
	return &evaluatorChallengeStore{
		challenges: make(map[string]*PoPChallenge),
		ttl:        5 * time.Minute,
		clock:      RealClock{},
	}
}

// SetClock injects a deterministic clock for tests.
func (s *evaluatorChallengeStore) SetClock(c Clock) {
	if c == nil {
		return
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.clock = c
}

// Issue creates a new PoP challenge for the given (evaluator_id, public_key)
// pair and stores it pending completion. Returns the full challenge so the
// caller can transmit `Message` to the registrant for signing.
func (s *evaluatorChallengeStore) Issue(
	evaluatorID, name, pubHex string,
	metadata map[string]string,
	expires *time.Time,
) (*PoPChallenge, error) {
	if evaluatorID == "" || pubHex == "" {
		return nil, fmt.Errorf("CHALLENGE_INVALID_INPUT: evaluator_id and public_key_hex required")
	}
	rawPub, err := hex.DecodeString(pubHex)
	if err != nil || len(rawPub) != ed25519.PublicKeySize {
		return nil, fmt.Errorf("CHALLENGE_INVALID_PUBLIC_KEY: hex decode failed or wrong size (got %d)", len(rawPub))
	}
	s.mu.Lock()
	defer s.mu.Unlock()

	now := s.now()
	s.pruneLocked(now)

	nonce := uuid.New().String()
	challengeID := uuid.New().String()
	msg := computePoPMessage(evaluatorID, pubHex, nonce, expires)

	ch := &PoPChallenge{
		ChallengeID:  challengeID,
		EvaluatorID:  evaluatorID,
		PublicKeyHex: pubHex,
		Name:         name,
		Metadata:     metadata,
		ExpiresAt:    expires,
		Nonce:        nonce,
		Message:      msg,
		IssuedAt:     now,
		ChallengeTTL: now.Add(s.ttl),
	}
	s.challenges[challengeID] = ch
	return ch, nil
}

// Consume verifies the signature against the stored challenge and deletes
// the challenge on success. Single-use: a second call with the same
// challenge_id will return CHALLENGE_ALREADY_CONSUMED.
//
// Returns the consumed challenge so the caller can use the captured
// (evaluator_id, public_key, metadata) without re-trusting client input.
func (s *evaluatorChallengeStore) Consume(challengeID string, signature []byte) (*PoPChallenge, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	now := s.now()
	s.pruneLocked(now)

	ch, ok := s.challenges[challengeID]
	if !ok {
		return nil, fmt.Errorf("CHALLENGE_ALREADY_CONSUMED: challenge_id=%s (or never issued)", challengeID)
	}
	if now.After(ch.ChallengeTTL) {
		delete(s.challenges, challengeID)
		return nil, fmt.Errorf("CHALLENGE_EXPIRED: issued_at=%s ttl_expired_at=%s",
			ch.IssuedAt.Format(time.RFC3339), ch.ChallengeTTL.Format(time.RFC3339))
	}

	rawPub, err := hex.DecodeString(ch.PublicKeyHex)
	if err != nil || len(rawPub) != ed25519.PublicKeySize {
		delete(s.challenges, challengeID)
		return nil, fmt.Errorf("CHALLENGE_CORRUPT_KEY: %w", err)
	}
	if len(signature) != ed25519.SignatureSize {
		delete(s.challenges, challengeID)
		return nil, fmt.Errorf("POP_FAILED: signature wrong size (got %d, expected %d)",
			len(signature), ed25519.SignatureSize)
	}

	// The signed message is the SHA-256 hex string the server returned.
	// We sign the hex bytes (deterministic ASCII) — the registrant must
	// sign exactly the bytes returned in `message`.
	if !ed25519.Verify(ed25519.PublicKey(rawPub), []byte(ch.Message), signature) {
		// Do NOT delete on failure — let the registrant retry within TTL.
		// (The bucket-style protection lives in admin auth, not here.)
		return nil, fmt.Errorf("POP_FAILED: signature does not verify against claimed public key")
	}

	// Single-use: delete on success
	delete(s.challenges, challengeID)
	return ch, nil
}

// Cancel deletes a challenge without verifying it. Used by admin tooling
// to retract an outstanding registration intent.
func (s *evaluatorChallengeStore) Cancel(challengeID string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.challenges, challengeID)
}

// Count returns the number of outstanding challenges (post-prune).
func (s *evaluatorChallengeStore) Count() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.pruneLocked(s.now())
	return len(s.challenges)
}

// pruneLocked removes expired challenges. Caller must hold the mutex.
func (s *evaluatorChallengeStore) pruneLocked(now time.Time) {
	for id, ch := range s.challenges {
		if now.After(ch.ChallengeTTL) {
			delete(s.challenges, id)
		}
	}
}

func (s *evaluatorChallengeStore) now() time.Time {
	if s.clock != nil {
		return s.clock.NowUTC()
	}
	return time.Now().UTC()
}

// generatePhase12UUID is the shim referenced by evaluator_admin_auth.go.
// Defining the helper here keeps the uuid import scoped to phase-12
// files that already need it (this file).
func generatePhase12UUID() string {
	return uuid.New().String()
}
