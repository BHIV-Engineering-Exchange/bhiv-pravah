package main

// crypto_provider.go — v15.7 Crypto-Agile Provider Interface.
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Cryptographic Provider Abstraction
// Host Organization: Blackhole Infiverse (BHIV)
//
// PURPOSE:
//   Decouples the signing primitive (Ed25519 today, Composite ML-DSA-65 + Ed25519
//   tomorrow) from every business-logic step in Sarathi. The same canonical JSON
//   rules, the same registry lookups, the same replay/timestamp checks run under
//   every provider — only the bytes inside the signature.value differ.
//
//   THIS IS A CRYPTO-AGILITY LAYER, NOT A POLICY LAYER.
//
//   - The active provider is chosen ONCE at boot time from SARATHI_CRYPTO_PROVIDER.
//   - A wrong env value PANICS at boot (fail-closed, not fail-open).
//   - The provider is globally readable via ActiveProvider() after boot.
//   - Every signing/verification call site routes through this interface so a
//     post-quantum cutover is a single configuration flip across peers.
//
// DESIGN REFERENCES:
//   - NIST FIPS 204 (ML-DSA / CRYSTALS-Dilithium standardisation)
//   - draft-ietf-lamps-pq-composite-sigs (composite signature framing)
//   - RFC 8032 (Ed25519 / EdDSA)
//   - CISA "Quantum-Readiness: Migration to Post-Quantum Cryptography"
//
// TAG: crypto-agility-v15.7

import (
	"io"
)

// CryptoAlgorithmID is the human-readable identifier emitted in the signature
// `alg` field on every TANTRA-shaped record. It is also recorded in the
// evaluator registry so a verify call can refuse a payload whose algorithm
// does not match the registered key's algorithm (provider-mismatch detection).
type CryptoAlgorithmID string

const (
	// CryptoAlgEd25519 is RFC 8032 Ed25519 — the historical and default
	// algorithm. Produces 64-byte signatures, 32-byte public keys.
	CryptoAlgEd25519 CryptoAlgorithmID = "Ed25519"

	// CryptoAlgCompositeMLDSA65Ed25519 is a "composite-AND" of ML-DSA-65 (FIPS
	// 204, NIST Security Level 3) and Ed25519. Both signatures must be present
	// and both must verify. Produces a length-prefixed TLV-framed blob of
	// roughly 3,373 bytes.
	CryptoAlgCompositeMLDSA65Ed25519 CryptoAlgorithmID = "Composite-MLDSA65-Ed25519"
)

// PrivateKeyMaterial is an opaque handle for a provider-specific private key.
// Different providers store different types internally; callers MUST NOT
// inspect the underlying bytes — they are zeroed on Close() where supported.
type PrivateKeyMaterial interface {
	// Algorithm returns the algorithm this private key belongs to. Used by
	// the provider to refuse a foreign key passed in from another provider.
	Algorithm() CryptoAlgorithmID
	// Public returns the matching public key material.
	Public() PublicKeyMaterial
}

// PublicKeyMaterial is an opaque handle for a provider-specific public key.
// Stored on the evaluator registry as the encoded string + algorithm id.
type PublicKeyMaterial interface {
	// Algorithm returns the algorithm this public key belongs to.
	Algorithm() CryptoAlgorithmID
	// Encoded returns the canonical wire encoding (hex for Ed25519, base64url-
	// no-pad with a TLV envelope for composite).
	Encoded() string
}

// SignatureValue is the raw byte string produced by Sign(). The TANTRA layer
// base64url-no-pad-encodes it before wire emission; legacy hex-encoded paths
// continue to hex-encode this byte string.
//
// CompositeMLDSA65Ed25519 produces a TLV-framed blob:
//
//	version_byte (0x01)
//	tag_byte     (0x01 Ed25519)
//	length       (4-byte big-endian)
//	ed25519_signature
//	tag_byte     (0x02 ML-DSA-65)
//	length       (4-byte big-endian)
//	mldsa65_signature
//
// Ed25519 produces the bare 64-byte RFC 8032 signature.
type SignatureValue []byte

// CryptoProvider is the single interface every signing / verifying call site
// in Sarathi routes through. Concrete providers live in:
//
//   - crypto_provider_ed25519.go            (default, matches v15.6 behaviour)
//   - crypto_provider_hybrid.go             (Composite ML-DSA-65 + Ed25519)
//
// A provider is selected at boot by crypto_provider_init.go.
//
// INVARIANTS (CSO-mandated):
//   - The provider NEVER reaches into application state. It is a pure
//     bytes-in / bytes-out primitive plus key material management.
//   - The provider performs constant-time signature comparison where the
//     underlying library supports it.
//   - The provider refuses to verify a payload whose Algorithm() does not
//     match the public key's Algorithm() (no silent algorithm downgrade).
type CryptoProvider interface {
	// Algorithm returns the algorithm identifier emitted in signature.alg.
	Algorithm() CryptoAlgorithmID

	// Sign computes the signature over `material`. `material` is the EXACT
	// bytes produced by the upstream canonicalizer — the provider does NOT
	// re-canonicalize.
	Sign(material []byte, key PrivateKeyMaterial) (SignatureValue, error)

	// Verify checks `sig` over `material` against `pub`. Returns (true, "") on
	// success; (false, reason) on failure. The reason string is for audit
	// logging only — it is never returned to remote callers.
	Verify(material []byte, sig SignatureValue, pub PublicKeyMaterial) (bool, string)

	// Generate produces a fresh keypair using `rand` as the entropy source.
	// Passing nil uses crypto/rand.Reader.
	Generate(rand io.Reader) (PrivateKeyMaterial, PublicKeyMaterial, error)

	// ParsePublicKey decodes the wire-encoded public key. Hex for Ed25519,
	// base64url-no-pad TLV envelope for composite.
	ParsePublicKey(encoded string) (PublicKeyMaterial, error)

	// ParsePrivateKey decodes a wire-encoded private key (file format
	// determined by the provider; Ed25519 uses hex, composite uses a JSON
	// envelope holding both component keys).
	ParsePrivateKey(encoded string) (PrivateKeyMaterial, error)

	// EncodePublicKey is the inverse of ParsePublicKey.
	EncodePublicKey(pub PublicKeyMaterial) string

	// EncodePrivateKey is the inverse of ParsePrivateKey. Used by the keygen
	// CLI; never used in the hot path.
	EncodePrivateKey(priv PrivateKeyMaterial) string

	// KeyIDSuffixTemplate returns the algorithm-specific suffix appended to
	// the base key id. For Ed25519: "#ed25519-<rotation>". For composite:
	// "#composite-mldsa65-ed25519-<rotation>". Used by cmd_provider_keygen.go
	// when minting fresh key_id values.
	KeyIDSuffixTemplate() string
}

// activeProvider is the process-wide singleton. Set ONCE by crypto_provider_init.go
// at boot, read-only thereafter. Accessing it before initialisation panics.
var activeProvider CryptoProvider

// ActiveProvider returns the boot-selected provider. Calling this before
// InitCryptoProvider() runs is a programming error and panics with a clear
// message — there is no "default-on-read" fallback because such a fallback
// would allow signing with an unintended algorithm.
func ActiveProvider() CryptoProvider {
	if activeProvider == nil {
		panic("crypto_provider: ActiveProvider() called before InitCryptoProvider() — boot sequence violation")
	}
	return activeProvider
}

// SetActiveProviderForTest is the only sanctioned way to override the active
// provider after boot. Only test code should call this — calling it from
// production code will produce non-deterministic verify behaviour because
// other goroutines may already hold references to the previous provider.
//
// The function is intentionally named to surface in code review.
func SetActiveProviderForTest(p CryptoProvider) {
	activeProvider = p
}
