package main

// crypto_provider_hybrid.go — Composite ML-DSA-65 + Ed25519 (FIPS 204 + RFC 8032).
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — Post-Quantum Crypto Provider
// Host Organization: Blackhole Infiverse (BHIV)
//
// THREAT MODEL:
//   ML-DSA-65 (CRYSTALS-Dilithium, FIPS 204) provides post-quantum
//   unforgeability — a future cryptographically-relevant quantum computer
//   running Shor's algorithm cannot forge ML-DSA signatures. Ed25519 retains
//   its present-day cryptographic strength against classical adversaries.
//
//   The composite-AND construction signs the SAME message bytes with BOTH
//   primitives and requires BOTH verifications to succeed. This guarantees:
//
//     * If ML-DSA is broken by an undiscovered classical attack, Ed25519
//       still binds the signature (no downgrade to a weaker scheme).
//     * If Ed25519 is broken by a future quantum computer, ML-DSA still
//       binds the signature (post-quantum safe).
//
//   This is the IETF "composite-AND" pattern (draft-ietf-lamps-pq-composite-sigs).
//
// LIBRARY CHOICE:
//   Cloudflare CIRCL — github.com/cloudflare/circl/sign/mldsa/mldsa65
//   - Pure Go, no CGO, Windows-buildable.
//   - Production-deployed in Cloudflare's edge at scale.
//   - FIPS 204 known-answer-test (KAT) vector parity.
//   - Constant-time signing, side-channel-aware.
//   - BSD-3-Clause licence.
//
//   The interface in crypto_provider.go is identical for a future liboqs-go
//   build (crypto_provider_hybrid_liboqs.go, gated by `-tags=liboqs`).
//
// WIRE FORMAT (SignatureValue, public key, private key):
//
//   SignatureValue — length-prefixed TLV:
//
//     | version  (1 byte, 0x01)
//     | tag      (1 byte, 0x01=Ed25519)
//     | length   (4 bytes, big-endian) -> N1 = 64
//     | ed25519_signature (N1 bytes)
//     | tag      (1 byte, 0x02=ML-DSA-65)
//     | length   (4 bytes, big-endian) -> N2 = 3309
//     | mldsa65_signature (N2 bytes)
//
//   Total: 1 + 1 + 4 + 64 + 1 + 4 + 3309 = 3384 bytes
//
//   PublicKeyMaterial.Encoded(): base64url-no-pad of the same TLV envelope
//   (tag bytes 0x01 + 0x02 carry the component keys).
//
//   PrivateKeyMaterial: JSON envelope, hex-encoded components:
//     {"alg":"Composite-MLDSA65-Ed25519",
//      "ed25519_priv_hex":"...","mldsa65_priv_hex":"..."}
//
// INVARIANTS:
//   - composite-AND only. A "verify if either matches" mode is FORBIDDEN.
//   - Tag bytes are stable forever; downgrades to single-primitive
//     verification are not possible at this layer.
//
// TAG: crypto-agility-v15.7

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"strings"

	mldsa65 "github.com/cloudflare/circl/sign/mldsa/mldsa65"
)

// Composite TLV constants.
const (
	compositeTLVVersion   byte = 0x01
	compositeTagEd25519   byte = 0x01
	compositeTagMLDSA65   byte = 0x02
	compositeMaxComponent      = 1 << 20 // 1 MiB sanity cap per component
)

// HybridProvider implements CryptoProvider with composite-AND ML-DSA-65 +
// Ed25519 signing and verification.
type HybridProvider struct{}

// NewHybridProvider constructs the singleton-per-process composite provider.
func NewHybridProvider() *HybridProvider { return &HybridProvider{} }

// Algorithm returns CryptoAlgCompositeMLDSA65Ed25519.
func (p *HybridProvider) Algorithm() CryptoAlgorithmID {
	return CryptoAlgCompositeMLDSA65Ed25519
}

// ============================================================================
// KEY MATERIAL TYPES
// ============================================================================

type hybridPrivateMaterial struct {
	edPriv ed25519.PrivateKey
	mlPriv *mldsa65.PrivateKey
	pub    *hybridPublicMaterial
}

func (m *hybridPrivateMaterial) Algorithm() CryptoAlgorithmID {
	return CryptoAlgCompositeMLDSA65Ed25519
}
func (m *hybridPrivateMaterial) Public() PublicKeyMaterial { return m.pub }

type hybridPublicMaterial struct {
	edPub ed25519.PublicKey
	mlPub *mldsa65.PublicKey
	enc   string // cached base64url-no-pad TLV envelope
}

func (m *hybridPublicMaterial) Algorithm() CryptoAlgorithmID {
	return CryptoAlgCompositeMLDSA65Ed25519
}
func (m *hybridPublicMaterial) Encoded() string {
	if m.enc != "" {
		return m.enc
	}
	tlv, err := encodeHybridPublicTLV(m.edPub, m.mlPub)
	if err != nil {
		return ""
	}
	m.enc = base64.RawURLEncoding.EncodeToString(tlv)
	return m.enc
}

// ============================================================================
// SIGN / VERIFY
// ============================================================================

// Sign produces a composite signature over `material`.
func (p *HybridProvider) Sign(material []byte, key PrivateKeyMaterial) (SignatureValue, error) {
	priv, ok := key.(*hybridPrivateMaterial)
	if !ok {
		return nil, fmt.Errorf("hybrid_provider: foreign key type %T", key)
	}
	if len(priv.edPriv) != ed25519.PrivateKeySize {
		return nil, fmt.Errorf("hybrid_provider: bad ed25519 priv length %d", len(priv.edPriv))
	}
	if priv.mlPriv == nil {
		return nil, errors.New("hybrid_provider: nil ml-dsa-65 private key")
	}

	edSig := ed25519.Sign(priv.edPriv, material)

	mlSig := make([]byte, mldsa65.SignatureSize)
	if err := mldsa65.SignTo(priv.mlPriv, material, nil, false, mlSig); err != nil {
		return nil, fmt.Errorf("hybrid_provider: ml-dsa-65 sign: %w", err)
	}

	envelope, err := encodeHybridSignatureTLV(edSig, mlSig)
	if err != nil {
		return nil, err
	}
	return SignatureValue(envelope), nil
}

// Verify checks BOTH component signatures. Returns true only when both pass.
func (p *HybridProvider) Verify(material []byte, sig SignatureValue, pub PublicKeyMaterial) (bool, string) {
	pk, ok := pub.(*hybridPublicMaterial)
	if !ok {
		return false, fmt.Sprintf("hybrid_provider: foreign public key type %T", pub)
	}
	if pk.Algorithm() != CryptoAlgCompositeMLDSA65Ed25519 {
		return false, fmt.Sprintf("hybrid_provider: algorithm mismatch (key alg=%s)", pk.Algorithm())
	}

	edSig, mlSig, err := decodeHybridSignatureTLV(sig)
	if err != nil {
		return false, fmt.Sprintf("hybrid_provider: signature framing: %v", err)
	}

	if len(edSig) != ed25519.SignatureSize {
		return false, fmt.Sprintf("hybrid_provider: bad ed25519 sig length %d", len(edSig))
	}
	if len(mlSig) != mldsa65.SignatureSize {
		return false, fmt.Sprintf("hybrid_provider: bad ml-dsa-65 sig length %d", len(mlSig))
	}

	if !ed25519.Verify(pk.edPub, material, edSig) {
		return false, "hybrid_provider: ed25519 component did not verify"
	}
	if !mldsa65.Verify(pk.mlPub, material, nil, mlSig) {
		return false, "hybrid_provider: ml-dsa-65 component did not verify"
	}
	return true, ""
}

// ============================================================================
// GENERATE / PARSE / ENCODE
// ============================================================================

// Generate produces a fresh composite keypair.
func (p *HybridProvider) Generate(r io.Reader) (PrivateKeyMaterial, PublicKeyMaterial, error) {
	if r == nil {
		r = rand.Reader
	}
	edPub, edPriv, err := ed25519.GenerateKey(r)
	if err != nil {
		return nil, nil, fmt.Errorf("hybrid_provider: ed25519 generate: %w", err)
	}
	mlPub, mlPriv, err := mldsa65.GenerateKey(r)
	if err != nil {
		return nil, nil, fmt.Errorf("hybrid_provider: ml-dsa-65 generate: %w", err)
	}
	hpub := &hybridPublicMaterial{edPub: edPub, mlPub: mlPub}
	hpriv := &hybridPrivateMaterial{edPriv: edPriv, mlPriv: mlPriv, pub: hpub}
	return hpriv, hpub, nil
}

// ParsePublicKey decodes a base64url-no-pad TLV envelope.
func (p *HybridProvider) ParsePublicKey(encoded string) (PublicKeyMaterial, error) {
	clean := strings.TrimSpace(encoded)
	if clean == "" {
		return nil, errors.New("hybrid_provider: empty public key")
	}
	raw, err := base64.RawURLEncoding.DecodeString(clean)
	if err != nil {
		return nil, fmt.Errorf("hybrid_provider: public key not base64url-no-pad: %w", err)
	}
	edPub, mlPub, err := decodeHybridPublicTLV(raw)
	if err != nil {
		return nil, err
	}
	return &hybridPublicMaterial{edPub: edPub, mlPub: mlPub, enc: clean}, nil
}

// hybridPrivateEnvelope is the on-disk JSON envelope for composite keypairs.
type hybridPrivateEnvelope struct {
	Alg           CryptoAlgorithmID `json:"alg"`
	Ed25519Priv   string            `json:"ed25519_priv_hex"`
	MLDSA65Priv   string            `json:"mldsa65_priv_b64url"`
	Ed25519Pub    string            `json:"ed25519_pub_hex"`
	MLDSA65Pub    string            `json:"mldsa65_pub_b64url"`
}

// ParsePrivateKey decodes the JSON envelope produced by EncodePrivateKey.
func (p *HybridProvider) ParsePrivateKey(encoded string) (PrivateKeyMaterial, error) {
	clean := strings.TrimSpace(encoded)
	if clean == "" {
		return nil, errors.New("hybrid_provider: empty private key envelope")
	}
	var env hybridPrivateEnvelope
	if err := json.Unmarshal([]byte(clean), &env); err != nil {
		return nil, fmt.Errorf("hybrid_provider: private key envelope decode: %w", err)
	}
	if env.Alg != CryptoAlgCompositeMLDSA65Ed25519 {
		return nil, fmt.Errorf("hybrid_provider: private key envelope alg=%q want=%q",
			env.Alg, CryptoAlgCompositeMLDSA65Ed25519)
	}

	edPrivRaw, err := hex.DecodeString(env.Ed25519Priv)
	if err != nil || len(edPrivRaw) != ed25519.PrivateKeySize {
		return nil, fmt.Errorf("hybrid_provider: ed25519 priv decode (len=%d, err=%v)", len(edPrivRaw), err)
	}
	mlPrivRaw, err := base64.RawURLEncoding.DecodeString(env.MLDSA65Priv)
	if err != nil || len(mlPrivRaw) != mldsa65.PrivateKeySize {
		return nil, fmt.Errorf("hybrid_provider: ml-dsa-65 priv decode (len=%d, err=%v)", len(mlPrivRaw), err)
	}
	edPubRaw, err := hex.DecodeString(env.Ed25519Pub)
	if err != nil || len(edPubRaw) != ed25519.PublicKeySize {
		return nil, fmt.Errorf("hybrid_provider: ed25519 pub decode (len=%d, err=%v)", len(edPubRaw), err)
	}
	mlPubRaw, err := base64.RawURLEncoding.DecodeString(env.MLDSA65Pub)
	if err != nil || len(mlPubRaw) != mldsa65.PublicKeySize {
		return nil, fmt.Errorf("hybrid_provider: ml-dsa-65 pub decode (len=%d, err=%v)", len(mlPubRaw), err)
	}

	var mlPriv mldsa65.PrivateKey
	if err := mlPriv.UnmarshalBinary(mlPrivRaw); err != nil {
		return nil, fmt.Errorf("hybrid_provider: ml-dsa-65 priv unmarshal: %w", err)
	}
	var mlPub mldsa65.PublicKey
	if err := mlPub.UnmarshalBinary(mlPubRaw); err != nil {
		return nil, fmt.Errorf("hybrid_provider: ml-dsa-65 pub unmarshal: %w", err)
	}

	hpub := &hybridPublicMaterial{edPub: ed25519.PublicKey(edPubRaw), mlPub: &mlPub}
	return &hybridPrivateMaterial{
		edPriv: ed25519.PrivateKey(edPrivRaw),
		mlPriv: &mlPriv,
		pub:    hpub,
	}, nil
}

// EncodePublicKey returns base64url-no-pad of the TLV envelope.
func (p *HybridProvider) EncodePublicKey(pub PublicKeyMaterial) string {
	m, ok := pub.(*hybridPublicMaterial)
	if !ok {
		return ""
	}
	return m.Encoded()
}

// EncodePrivateKey returns the JSON envelope.
func (p *HybridProvider) EncodePrivateKey(priv PrivateKeyMaterial) string {
	m, ok := priv.(*hybridPrivateMaterial)
	if !ok {
		return ""
	}
	mlPrivBin, err := m.mlPriv.MarshalBinary()
	if err != nil {
		return ""
	}
	mlPubBin, err := m.pub.mlPub.MarshalBinary()
	if err != nil {
		return ""
	}
	env := hybridPrivateEnvelope{
		Alg:         CryptoAlgCompositeMLDSA65Ed25519,
		Ed25519Priv: hex.EncodeToString(m.edPriv),
		MLDSA65Priv: base64.RawURLEncoding.EncodeToString(mlPrivBin),
		Ed25519Pub:  hex.EncodeToString(m.pub.edPub),
		MLDSA65Pub:  base64.RawURLEncoding.EncodeToString(mlPubBin),
	}
	raw, err := json.MarshalIndent(&env, "", "  ")
	if err != nil {
		return ""
	}
	return string(raw)
}

// KeyIDSuffixTemplate returns "#composite-mldsa65-ed25519-<rotation>".
func (p *HybridProvider) KeyIDSuffixTemplate() string {
	return "#composite-mldsa65-ed25519-<rotation>"
}

// Compile-time check.
var _ CryptoProvider = (*HybridProvider)(nil)

// ============================================================================
// TLV ENCODE / DECODE HELPERS
// ============================================================================

func writeTLVSegment(buf []byte, tag byte, payload []byte) []byte {
	buf = append(buf, tag)
	var lenBuf [4]byte
	binary.BigEndian.PutUint32(lenBuf[:], uint32(len(payload)))
	buf = append(buf, lenBuf[:]...)
	buf = append(buf, payload...)
	return buf
}

func readTLVSegment(data []byte, offset int) (tag byte, payload []byte, next int, err error) {
	if offset+5 > len(data) {
		return 0, nil, 0, fmt.Errorf("tlv: truncated header at offset %d", offset)
	}
	tag = data[offset]
	length := binary.BigEndian.Uint32(data[offset+1 : offset+5])
	if length > compositeMaxComponent {
		return 0, nil, 0, fmt.Errorf("tlv: segment length %d exceeds cap %d", length, compositeMaxComponent)
	}
	end := offset + 5 + int(length)
	if end > len(data) {
		return 0, nil, 0, fmt.Errorf("tlv: segment truncated (need %d, have %d)", end, len(data))
	}
	return tag, data[offset+5 : end], end, nil
}

func encodeHybridSignatureTLV(edSig, mlSig []byte) ([]byte, error) {
	if len(edSig) != ed25519.SignatureSize {
		return nil, fmt.Errorf("hybrid_tlv: ed25519 sig length %d != %d", len(edSig), ed25519.SignatureSize)
	}
	if len(mlSig) != mldsa65.SignatureSize {
		return nil, fmt.Errorf("hybrid_tlv: ml-dsa-65 sig length %d != %d", len(mlSig), mldsa65.SignatureSize)
	}
	buf := make([]byte, 0, 2+8+ed25519.SignatureSize+mldsa65.SignatureSize)
	buf = append(buf, compositeTLVVersion)
	buf = writeTLVSegment(buf, compositeTagEd25519, edSig)
	buf = writeTLVSegment(buf, compositeTagMLDSA65, mlSig)
	return buf, nil
}

func decodeHybridSignatureTLV(sig []byte) (edSig, mlSig []byte, err error) {
	if len(sig) < 1 {
		return nil, nil, errors.New("hybrid_tlv: empty signature blob")
	}
	if sig[0] != compositeTLVVersion {
		return nil, nil, fmt.Errorf("hybrid_tlv: bad version byte 0x%02x", sig[0])
	}
	tag1, seg1, next, err := readTLVSegment(sig, 1)
	if err != nil {
		return nil, nil, fmt.Errorf("hybrid_tlv: segment 1: %w", err)
	}
	if tag1 != compositeTagEd25519 {
		return nil, nil, fmt.Errorf("hybrid_tlv: segment 1 tag 0x%02x, want ed25519 (0x01)", tag1)
	}
	tag2, seg2, end, err := readTLVSegment(sig, next)
	if err != nil {
		return nil, nil, fmt.Errorf("hybrid_tlv: segment 2: %w", err)
	}
	if tag2 != compositeTagMLDSA65 {
		return nil, nil, fmt.Errorf("hybrid_tlv: segment 2 tag 0x%02x, want ml-dsa-65 (0x02)", tag2)
	}
	if end != len(sig) {
		return nil, nil, fmt.Errorf("hybrid_tlv: %d trailing bytes after segment 2", len(sig)-end)
	}
	return seg1, seg2, nil
}

func encodeHybridPublicTLV(edPub ed25519.PublicKey, mlPub *mldsa65.PublicKey) ([]byte, error) {
	if len(edPub) != ed25519.PublicKeySize {
		return nil, fmt.Errorf("hybrid_tlv: ed25519 pub length %d != %d", len(edPub), ed25519.PublicKeySize)
	}
	mlPubBin, err := mlPub.MarshalBinary()
	if err != nil {
		return nil, fmt.Errorf("hybrid_tlv: ml-dsa-65 pub marshal: %w", err)
	}
	buf := make([]byte, 0, 2+8+ed25519.PublicKeySize+mldsa65.PublicKeySize)
	buf = append(buf, compositeTLVVersion)
	buf = writeTLVSegment(buf, compositeTagEd25519, edPub)
	buf = writeTLVSegment(buf, compositeTagMLDSA65, mlPubBin)
	return buf, nil
}

func decodeHybridPublicTLV(raw []byte) (ed25519.PublicKey, *mldsa65.PublicKey, error) {
	if len(raw) < 1 || raw[0] != compositeTLVVersion {
		return nil, nil, fmt.Errorf("hybrid_tlv: bad public key version byte")
	}
	tag1, seg1, next, err := readTLVSegment(raw, 1)
	if err != nil {
		return nil, nil, fmt.Errorf("hybrid_tlv: pub segment 1: %w", err)
	}
	if tag1 != compositeTagEd25519 || len(seg1) != ed25519.PublicKeySize {
		return nil, nil, fmt.Errorf("hybrid_tlv: pub segment 1 mismatch (tag=0x%02x, len=%d)", tag1, len(seg1))
	}
	tag2, seg2, end, err := readTLVSegment(raw, next)
	if err != nil {
		return nil, nil, fmt.Errorf("hybrid_tlv: pub segment 2: %w", err)
	}
	if tag2 != compositeTagMLDSA65 || len(seg2) != mldsa65.PublicKeySize {
		return nil, nil, fmt.Errorf("hybrid_tlv: pub segment 2 mismatch (tag=0x%02x, len=%d)", tag2, len(seg2))
	}
	if end != len(raw) {
		return nil, nil, fmt.Errorf("hybrid_tlv: %d trailing bytes after pub segment 2", len(raw)-end)
	}
	var mlPub mldsa65.PublicKey
	if err := mlPub.UnmarshalBinary(seg2); err != nil {
		return nil, nil, fmt.Errorf("hybrid_tlv: ml-dsa-65 pub unmarshal: %w", err)
	}
	return ed25519.PublicKey(seg1), &mlPub, nil
}
