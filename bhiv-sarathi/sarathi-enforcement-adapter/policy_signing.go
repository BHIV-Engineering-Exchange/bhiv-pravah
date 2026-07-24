package main

// policy_signing.go — Ed25519 Digital Signature Verification for Frozen Policies.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Cryptographic Policy Assurance Layer
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   Every frozen policy MUST be signed by an authorized governance key.
//   Ed25519 (RFC 8032) is used because:
//     - Deterministic signatures (no nonce reuse risk unlike ECDSA)
//     - 128-bit security level (equivalent to RSA-3072)
//     - Fast verification (~71,000 ops/sec on commodity hardware)
//     - Small keys (32 bytes) and signatures (64 bytes)
//     - Used by: Signal, WireGuard, Tor, NIST FIPS 186-5, OpenSSH
//
// SIGNING CONTRACT:
//   1. The policy_hash (SHA-256 of canonical rules) is the signed payload.
//   2. The signature is Ed25519(private_key, policy_hash_bytes).
//   3. Verification uses Ed25519Verify(public_key, policy_hash_bytes, signature).
//   4. A policy without a valid signature MUST NOT be activated in production.
//   5. Key rotation is supported via the GovernanceKeyRing (multiple public keys).
//
// GOVERNANCE INVARIANTS:
//   - Private keys NEVER exist in this codebase. They are held offline.
//   - Only public keys are embedded or loaded for verification.
//   - Signature verification is fail-closed: invalid/missing → rejection.
//   - Key revocation is immediate: remove from keyring → signatures invalid.

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"sync"
	"time"
)

// ================================================================
// ED25519 KEY MANAGEMENT
// ================================================================

// GovernanceKeyID is a human-readable identifier for a signing key.
type GovernanceKeyID string

// GovernancePublicKey holds a named Ed25519 public key for signature verification.
type GovernancePublicKey struct {
	KeyID     GovernanceKeyID    `json:"key_id"`
	PublicKey ed25519.PublicKey   `json:"-"`
	PublicHex string             `json:"public_key_hex"`
	AddedAt   string             `json:"added_at"`
	Status    string             `json:"status"` // ACTIVE, REVOKED
}

// GovernanceKeyRing manages the set of trusted Ed25519 public keys.
// Only keys in this ring can produce valid policy signatures.
// Thread-safe for concurrent reads.
type GovernanceKeyRing struct {
	mu   sync.RWMutex
	keys map[GovernanceKeyID]*GovernancePublicKey
}

// NewGovernanceKeyRing creates an empty keyring.
func NewGovernanceKeyRing() *GovernanceKeyRing {
	return &GovernanceKeyRing{
		keys: make(map[GovernanceKeyID]*GovernancePublicKey),
	}
}

// AddPublicKey registers a public key for signature verification.
// The key is provided as a 64-character hex string (32 bytes).
func (kr *GovernanceKeyRing) AddPublicKey(keyID GovernanceKeyID, publicHex string) error {
	kr.mu.Lock()
	defer kr.mu.Unlock()

	pubBytes, err := hex.DecodeString(publicHex)
	if err != nil {
		return fmt.Errorf("invalid public key hex: %w", err)
	}
	if len(pubBytes) != ed25519.PublicKeySize {
		return fmt.Errorf("invalid public key length: expected %d bytes, got %d",
			ed25519.PublicKeySize, len(pubBytes))
	}

	if _, exists := kr.keys[keyID]; exists {
		return fmt.Errorf("key %q already registered", keyID)
	}

	kr.keys[keyID] = &GovernancePublicKey{
		KeyID:     keyID,
		PublicKey: ed25519.PublicKey(pubBytes),
		PublicHex: publicHex,
		AddedAt:   time.Now().UTC().Format("2006-01-02T15:04:05Z"),
		Status:    "ACTIVE",
	}

	fmt.Printf("[KeyRing] Registered key: %s (Ed25519, %d bytes)\n", keyID, len(pubBytes))
	return nil
}

// RevokeKey marks a key as REVOKED. Signatures from revoked keys fail verification.
func (kr *GovernanceKeyRing) RevokeKey(keyID GovernanceKeyID) error {
	kr.mu.Lock()
	defer kr.mu.Unlock()

	key, exists := kr.keys[keyID]
	if !exists {
		return fmt.Errorf("key %q not found", keyID)
	}
	key.Status = "REVOKED"
	fmt.Printf("[KeyRing] Key REVOKED: %s\n", keyID)
	return nil
}

// GetActiveKey returns an active public key by ID, or nil if not found/revoked.
func (kr *GovernanceKeyRing) GetActiveKey(keyID GovernanceKeyID) *GovernancePublicKey {
	kr.mu.RLock()
	defer kr.mu.RUnlock()

	key, exists := kr.keys[keyID]
	if !exists || key.Status != "ACTIVE" {
		return nil
	}
	return key
}

// ListKeys returns all registered key IDs and their statuses.
func (kr *GovernanceKeyRing) ListKeys() []GovernancePublicKey {
	kr.mu.RLock()
	defer kr.mu.RUnlock()

	result := make([]GovernancePublicKey, 0, len(kr.keys))
	for _, k := range kr.keys {
		result = append(result, *k)
	}
	return result
}

// ActiveKeyCount returns the number of non-revoked keys.
func (kr *GovernanceKeyRing) ActiveKeyCount() int {
	kr.mu.RLock()
	defer kr.mu.RUnlock()

	count := 0
	for _, k := range kr.keys {
		if k.Status == "ACTIVE" {
			count++
		}
	}
	return count
}

// ================================================================
// POLICY SIGNATURE
// ================================================================

// PolicySignature represents an Ed25519 signature over a policy hash.
type PolicySignature struct {
	PolicyVersion string          `json:"policy_version"`
	PolicyHash    string          `json:"policy_hash"`
	SignerKeyID   GovernanceKeyID `json:"signer_key_id"`
	SignatureHex  string          `json:"signature_hex"`
	SignedAt      string          `json:"signed_at"`
}

// ================================================================
// SIGNATURE VERIFICATION
// ================================================================

// VerifyPolicySignature checks that a policy signature is valid against
// the keyring. Returns (valid, reason).
//
// Verification steps:
//   1. Look up signer_key_id in the keyring
//   2. Reject if key is missing or REVOKED
//   3. Decode the signature from hex
//   4. Verify Ed25519(public_key, policy_hash_bytes, signature)
//   5. Verify policy_hash in signature matches the actual policy hash
func VerifyPolicySignature(sig *PolicySignature, keyring *GovernanceKeyRing, actualPolicyHash string) (bool, string) {
	// Step 1-2: Key lookup
	key := keyring.GetActiveKey(sig.SignerKeyID)
	if key == nil {
		return false, fmt.Sprintf("SIGNER_KEY_NOT_FOUND_OR_REVOKED: %s", sig.SignerKeyID)
	}

	// Step 3: Decode signature
	sigBytes, err := hex.DecodeString(sig.SignatureHex)
	if err != nil {
		return false, fmt.Sprintf("INVALID_SIGNATURE_HEX: %v", err)
	}
	if len(sigBytes) != ed25519.SignatureSize {
		return false, fmt.Sprintf("INVALID_SIGNATURE_LENGTH: expected %d, got %d",
			ed25519.SignatureSize, len(sigBytes))
	}

	// Step 4: Verify Ed25519 signature over the policy hash
	message := []byte(sig.PolicyHash)
	if !ed25519.Verify(key.PublicKey, message, sigBytes) {
		return false, "ED25519_SIGNATURE_INVALID"
	}

	// Step 5: Verify hash consistency
	if sig.PolicyHash != actualPolicyHash {
		return false, fmt.Sprintf("POLICY_HASH_MISMATCH: signature covers %s but policy has %s",
			sig.PolicyHash, actualPolicyHash)
	}

	return true, "SIGNATURE_VALID"
}

// ================================================================
// SIGNING (for testing and offline key ceremony)
// ================================================================

// SignPolicyHash creates an Ed25519 signature over a policy hash.
// This function is for LOCAL TESTING and OFFLINE KEY CEREMONIES only.
// In production, signing happens on air-gapped machines.
func SignPolicyHash(privateKey ed25519.PrivateKey, policyHash string, keyID GovernanceKeyID) *PolicySignature {
	message := []byte(policyHash)
	signature := ed25519.Sign(privateKey, message)

	return &PolicySignature{
		PolicyHash:   policyHash,
		SignerKeyID:  keyID,
		SignatureHex: hex.EncodeToString(signature),
		SignedAt:     time.Now().UTC().Format("2006-01-02T15:04:05Z"),
	}
}

// GenerateGovernanceKeyPair generates a new Ed25519 key pair for testing.
// In production, keys are generated on air-gapped machines during key ceremonies.
func GenerateGovernanceKeyPair() (ed25519.PublicKey, ed25519.PrivateKey, error) {
	return ed25519.GenerateKey(rand.Reader)
}

// ================================================================
// INTEGRATION: PolicyRegistry + Signature Verification
// ================================================================

// SignedPolicyEntry extends PolicyEntry with signature metadata.
type SignedPolicyEntry struct {
	PolicyVersion string          `json:"policy_version"`
	PolicyHash    string          `json:"policy_hash"`
	Signature     *PolicySignature `json:"signature,omitempty"`
	Verified      bool            `json:"verified"`
	VerifyReason  string          `json:"verify_reason"`
}

// VerifyRegistrySignatures checks all loaded policies against the keyring.
// Returns a list of verification results and whether ALL policies pass.
func VerifyRegistrySignatures(
	registry *PolicyRegistry,
	signatures map[string]*PolicySignature,
	keyring *GovernanceKeyRing,
) ([]SignedPolicyEntry, bool) {

	versions := registry.ListPolicyVersions()
	results := make([]SignedPolicyEntry, 0, len(versions))
	allValid := true

	for _, version := range versions {
		ps := registry.GetPolicy(version)
		if ps == nil {
			continue
		}

		entry := SignedPolicyEntry{
			PolicyVersion: version,
			PolicyHash:    ps.GetPolicyHash(),
		}

		sig, hasSig := signatures[version]
		if !hasSig {
			entry.Verified = false
			entry.VerifyReason = "NO_SIGNATURE_PROVIDED"
			allValid = false
		} else {
			entry.Signature = sig
			valid, reason := VerifyPolicySignature(sig, keyring, ps.GetPolicyHash())
			entry.Verified = valid
			entry.VerifyReason = reason
			if !valid {
				allValid = false
			}
		}

		results = append(results, entry)
	}

	return results, allValid
}

// PrintSignatureVerification outputs a human-readable signature verification report.
func PrintSignatureVerification(results []SignedPolicyEntry) {
	fmt.Println("\n  ┌─── ED25519 POLICY SIGNATURE VERIFICATION ───")
	fmt.Printf("  │ Policies Checked: %d\n", len(results))

	for _, r := range results {
		status := "FAIL"
		if r.Verified {
			status = "PASS"
		}
		fmt.Printf("  │ [%s] version=%s hash=%s... reason=%s\n",
			status, r.PolicyVersion, r.PolicyHash[:16], r.VerifyReason)
		if r.Signature != nil {
			fmt.Printf("  │        signer=%s signed_at=%s\n",
				r.Signature.SignerKeyID, r.Signature.SignedAt)
		}
	}
	fmt.Println("  └────────────────────────────────────────────────")
}
