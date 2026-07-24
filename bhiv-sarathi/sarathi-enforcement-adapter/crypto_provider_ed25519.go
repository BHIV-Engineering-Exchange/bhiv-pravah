package main

// crypto_provider_ed25519.go — Default CryptoProvider matching v15.6 behaviour.
//
// THIS PROVIDER MUST BE BIT-FOR-BIT IDENTICAL TO THE EXISTING ed25519.Sign /
// ed25519.Verify CALL SITES IT REPLACES. Any divergence is a regression.
//
// Wire encoding:
//   - PublicKey:  hex(32 bytes)              — same as existing trust_snapshot.json
//   - PrivateKey: hex(64 bytes seed||public) — same as existing keygen files
//   - Signature:  hex(64 bytes) on legacy paths, base64url-no-pad on TANTRA
//
// The provider exposes the raw 64-byte signature; encoding for the wire is
// performed by the caller (legacy paths hex-encode; tantra_canonical.go
// base64url-no-pad-encodes).
//
// TAG: crypto-agility-v15.7

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"strings"
)

// Ed25519Provider implements CryptoProvider over the standard library
// crypto/ed25519 package. No external dependencies; constant-time verify is
// guaranteed by the stdlib implementation.
type Ed25519Provider struct{}

// NewEd25519Provider returns the singleton-per-process Ed25519 provider.
func NewEd25519Provider() *Ed25519Provider { return &Ed25519Provider{} }

// Algorithm returns CryptoAlgEd25519.
func (p *Ed25519Provider) Algorithm() CryptoAlgorithmID { return CryptoAlgEd25519 }

// ed25519PrivateMaterial wraps an ed25519.PrivateKey as PrivateKeyMaterial.
type ed25519PrivateMaterial struct{ key ed25519.PrivateKey }

// Algorithm satisfies PrivateKeyMaterial.
func (m *ed25519PrivateMaterial) Algorithm() CryptoAlgorithmID { return CryptoAlgEd25519 }

// Public returns the matching public key material.
func (m *ed25519PrivateMaterial) Public() PublicKeyMaterial {
	return &ed25519PublicMaterial{key: m.key.Public().(ed25519.PublicKey)}
}

// Raw exposes the underlying ed25519.PrivateKey for the legacy code paths
// that still call ed25519.Sign directly (jwt_authority.go, etc.). New code
// MUST NOT use Raw — go through CryptoProvider.Sign instead.
func (m *ed25519PrivateMaterial) Raw() ed25519.PrivateKey { return m.key }

// ed25519PublicMaterial wraps an ed25519.PublicKey as PublicKeyMaterial.
type ed25519PublicMaterial struct{ key ed25519.PublicKey }

// Algorithm satisfies PublicKeyMaterial.
func (m *ed25519PublicMaterial) Algorithm() CryptoAlgorithmID { return CryptoAlgEd25519 }

// Encoded returns the hex-encoded 32-byte public key — same format the
// existing trust snapshot stores.
func (m *ed25519PublicMaterial) Encoded() string { return hex.EncodeToString(m.key) }

// Raw exposes the underlying ed25519.PublicKey for legacy interop.
func (m *ed25519PublicMaterial) Raw() ed25519.PublicKey { return m.key }

// Sign returns a 64-byte Ed25519 signature over material.
func (p *Ed25519Provider) Sign(material []byte, key PrivateKeyMaterial) (SignatureValue, error) {
	priv, ok := key.(*ed25519PrivateMaterial)
	if !ok {
		return nil, fmt.Errorf("ed25519_provider: foreign key type %T (expected ed25519PrivateMaterial)", key)
	}
	if len(priv.key) != ed25519.PrivateKeySize {
		return nil, fmt.Errorf("ed25519_provider: bad private key length %d (want %d)", len(priv.key), ed25519.PrivateKeySize)
	}
	return SignatureValue(ed25519.Sign(priv.key, material)), nil
}

// Verify checks an Ed25519 signature.
func (p *Ed25519Provider) Verify(material []byte, sig SignatureValue, pub PublicKeyMaterial) (bool, string) {
	pk, ok := pub.(*ed25519PublicMaterial)
	if !ok {
		return false, fmt.Sprintf("ed25519_provider: foreign public key type %T", pub)
	}
	if pk.Algorithm() != CryptoAlgEd25519 {
		return false, fmt.Sprintf("ed25519_provider: algorithm mismatch (key alg=%s)", pk.Algorithm())
	}
	if len(sig) != ed25519.SignatureSize {
		return false, fmt.Sprintf("ed25519_provider: bad signature length %d (want %d)", len(sig), ed25519.SignatureSize)
	}
	if len(pk.key) != ed25519.PublicKeySize {
		return false, fmt.Sprintf("ed25519_provider: bad public key length %d (want %d)", len(pk.key), ed25519.PublicKeySize)
	}
	if !ed25519.Verify(pk.key, material, sig) {
		return false, "ed25519_provider: signature did not verify"
	}
	return true, ""
}

// Generate produces a fresh Ed25519 keypair.
func (p *Ed25519Provider) Generate(r io.Reader) (PrivateKeyMaterial, PublicKeyMaterial, error) {
	if r == nil {
		r = rand.Reader
	}
	pub, priv, err := ed25519.GenerateKey(r)
	if err != nil {
		return nil, nil, fmt.Errorf("ed25519_provider: generate: %w", err)
	}
	return &ed25519PrivateMaterial{key: priv}, &ed25519PublicMaterial{key: pub}, nil
}

// ParsePublicKey accepts the hex-encoded 32-byte form. Tolerant of surrounding
// whitespace; rejects anything else (no base64 fallback to avoid silent format
// confusion with the composite provider's encoding).
func (p *Ed25519Provider) ParsePublicKey(encoded string) (PublicKeyMaterial, error) {
	clean := strings.TrimSpace(encoded)
	if clean == "" {
		return nil, errors.New("ed25519_provider: empty public key")
	}
	raw, err := hex.DecodeString(clean)
	if err != nil {
		return nil, fmt.Errorf("ed25519_provider: public key not hex: %w", err)
	}
	if len(raw) != ed25519.PublicKeySize {
		return nil, fmt.Errorf("ed25519_provider: public key length %d (want %d)", len(raw), ed25519.PublicKeySize)
	}
	return &ed25519PublicMaterial{key: ed25519.PublicKey(raw)}, nil
}

// ParsePrivateKey accepts the hex-encoded 64-byte form (seed||public).
func (p *Ed25519Provider) ParsePrivateKey(encoded string) (PrivateKeyMaterial, error) {
	clean := strings.TrimSpace(encoded)
	if clean == "" {
		return nil, errors.New("ed25519_provider: empty private key")
	}
	raw, err := hex.DecodeString(clean)
	if err != nil {
		return nil, fmt.Errorf("ed25519_provider: private key not hex: %w", err)
	}
	if len(raw) != ed25519.PrivateKeySize {
		return nil, fmt.Errorf("ed25519_provider: private key length %d (want %d)", len(raw), ed25519.PrivateKeySize)
	}
	return &ed25519PrivateMaterial{key: ed25519.PrivateKey(raw)}, nil
}

// EncodePublicKey returns the hex-encoded 32-byte form.
func (p *Ed25519Provider) EncodePublicKey(pub PublicKeyMaterial) string {
	m, ok := pub.(*ed25519PublicMaterial)
	if !ok {
		return ""
	}
	return hex.EncodeToString(m.key)
}

// EncodePrivateKey returns the hex-encoded 64-byte form.
func (p *Ed25519Provider) EncodePrivateKey(priv PrivateKeyMaterial) string {
	m, ok := priv.(*ed25519PrivateMaterial)
	if !ok {
		return ""
	}
	return hex.EncodeToString(m.key)
}

// KeyIDSuffixTemplate returns "#ed25519-<rotation>" — the suffix the keygen
// CLI appends to the base evaluator_id when minting fresh key_id values.
func (p *Ed25519Provider) KeyIDSuffixTemplate() string { return "#ed25519-<rotation>" }

// Ed25519PublicFromMaterial extracts the raw ed25519.PublicKey from a
// PublicKeyMaterial that wraps Ed25519 bytes. Returns (nil, false) for any
// other algorithm. Used by legacy code paths (jwt_authority.go, etc.) that
// still call ed25519.Verify directly.
//
// New code SHOULD route through ActiveProvider().Verify() instead.
func Ed25519PublicFromMaterial(pub PublicKeyMaterial) (ed25519.PublicKey, bool) {
	m, ok := pub.(*ed25519PublicMaterial)
	if !ok {
		return nil, false
	}
	return m.key, true
}

// Ed25519PrivateFromMaterial extracts the raw ed25519.PrivateKey from a
// PrivateKeyMaterial that wraps Ed25519 bytes. See above caveat.
func Ed25519PrivateFromMaterial(priv PrivateKeyMaterial) (ed25519.PrivateKey, bool) {
	m, ok := priv.(*ed25519PrivateMaterial)
	if !ok {
		return nil, false
	}
	return m.key, true
}

// NewEd25519PublicMaterial wraps an existing ed25519.PublicKey into the
// material interface. Used by translation_tantra_to_external_decision.go and
// other code that has already loaded the raw key bytes from elsewhere.
func NewEd25519PublicMaterial(pub ed25519.PublicKey) PublicKeyMaterial {
	return &ed25519PublicMaterial{key: pub}
}

// NewEd25519PrivateMaterial wraps an existing ed25519.PrivateKey.
func NewEd25519PrivateMaterial(priv ed25519.PrivateKey) PrivateKeyMaterial {
	return &ed25519PrivateMaterial{key: priv}
}

// Compile-time check that Ed25519Provider satisfies CryptoProvider.
var _ CryptoProvider = (*Ed25519Provider)(nil)

// Sentinel error for callers that wish to distinguish ed25519-specific failures.
var ErrEd25519Provider = errors.New("ed25519_provider")

// SignatureValueEqualConstantTime is a defensive helper for any caller that
// needs to compare two signature byte strings. The stdlib's ed25519.Verify is
// already constant-time so this helper is rarely needed, but it is exported
// so the audit document can reference one canonical comparator.
func SignatureValueEqualConstantTime(a, b SignatureValue) bool {
	return bytes.Equal(a, b)
}
