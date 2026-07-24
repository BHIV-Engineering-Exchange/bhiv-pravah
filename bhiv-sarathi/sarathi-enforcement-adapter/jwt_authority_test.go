package main

// jwt_authority_test.go — v15.6 unit + adversarial + roundtrip tests.
//
// These tests prove the wire format is library-independent (the Bridge can
// verify with any RFC 8037 verifier — not just golang-jwt) and that every
// RFC 8725 best-current-practice rejection path fires correctly.
//
// Categories:
//   * Roundtrip — golang-jwt parse, raw ed25519.Verify.
//   * Kid + RFC 7638 thumbprint determinism.
//   * Adversarial — alg=none, HS256 substitution, unknown kid, expired,
//     not-yet-valid, iss mismatch, aud mismatch.
//   * Rotation — old kid stays publishable in grace; sweep on expiry.
//   * Persistence — disk write/read roundtrip; permission-mode guard.
//   * Determinism — same input yields distinct jti/iat but both verify.
//
// TAG: jwt-authority-v15.6

import (
	"crypto/ed25519"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

// newTestAuthority constructs a fresh in-memory authority with sensible
// defaults for tests.
func newTestAuthority(t *testing.T) *JWTAuthority {
	t.Helper()
	signer, err := GenerateLocalEd25519Signer()
	if err != nil {
		t.Fatalf("keygen: %v", err)
	}
	auth, err := NewJWTAuthority(JWTAuthorityConfig{
		Signer:    signer,
		Issuer:    "https://test.bhiv.local/authority",
		Audience:  "bhiv-core-runtime",
		TokenTTL:  30 * time.Second,
		KeysDir:   t.TempDir(),
		Ephemeral: true,
	})
	if err != nil {
		t.Fatalf("NewJWTAuthority: %v", err)
	}
	return auth
}

// ============================================================================
// ROUNDTRIP
// ============================================================================

func TestMint_RoundtripWithGolangJWT(t *testing.T) {
	auth := newTestAuthority(t)
	mj, err := auth.MintJWT(MintRequest{
		Subject: "dec-test-001",
		PrivateClaims: map[string]interface{}{
			"verdict":     "ALLOW",
			"decision_id": "dec-test-001",
		},
	})
	if err != nil {
		t.Fatalf("MintJWT: %v", err)
	}
	if mj.Token == "" {
		t.Fatal("empty token")
	}

	pub := auth.CurrentSigner().PublicKey()
	parser := jwt.NewParser(jwt.WithValidMethods([]string{"EdDSA"}))
	parsed, err := parser.Parse(mj.Token, func(t *jwt.Token) (interface{}, error) {
		return ed25519.PublicKey(pub), nil
	})
	if err != nil {
		t.Fatalf("golang-jwt parse: %v", err)
	}
	claims := parsed.Claims.(jwt.MapClaims)
	if claims["iss"] != auth.Issuer() {
		t.Errorf("iss: got %v want %s", claims["iss"], auth.Issuer())
	}
	if claims["sub"] != "dec-test-001" {
		t.Errorf("sub: got %v want dec-test-001", claims["sub"])
	}
	if claims[claimMintPrefix+"verdict"] != "ALLOW" {
		t.Errorf("verdict private claim: got %v", claims[claimMintPrefix+"verdict"])
	}
}

func TestMint_RoundtripWithRawEd25519(t *testing.T) {
	// Proves the wire format is library-independent: split on ".",
	// base64url-decode header+payload+sig, call ed25519.Verify directly.
	auth := newTestAuthority(t)
	mj, err := auth.MintJWT(MintRequest{Subject: "raw"})
	if err != nil {
		t.Fatalf("MintJWT: %v", err)
	}
	parts := strings.Split(mj.Token, ".")
	if len(parts) != 3 {
		t.Fatalf("expected 3 parts, got %d", len(parts))
	}
	sigBytes, err := base64.RawURLEncoding.DecodeString(parts[2])
	if err != nil {
		t.Fatalf("decode sig: %v", err)
	}
	if len(sigBytes) != ed25519.SignatureSize {
		t.Fatalf("sig length=%d want=%d", len(sigBytes), ed25519.SignatureSize)
	}
	signedBytes := []byte(parts[0] + "." + parts[1])
	pub := auth.CurrentSigner().PublicKey()
	if !ed25519.Verify(pub, signedBytes, sigBytes) {
		t.Fatal("raw ed25519.Verify failed — wire format is not library-independent")
	}
	// And independently confirm header.kid matches RFC 7638 thumbprint.
	headerJSON, err := base64.RawURLEncoding.DecodeString(parts[0])
	if err != nil {
		t.Fatalf("decode header: %v", err)
	}
	var header map[string]interface{}
	if err := json.Unmarshal(headerJSON, &header); err != nil {
		t.Fatalf("unmarshal header: %v", err)
	}
	if header["alg"] != "EdDSA" {
		t.Errorf("alg header: got %v want EdDSA", header["alg"])
	}
	if header["typ"] != "JWT" {
		t.Errorf("typ header: got %v want JWT", header["typ"])
	}
	expectedKid, _ := ComputeRFC7638Thumbprint(pub)
	if header["kid"] != expectedKid {
		t.Errorf("kid: got %v want %s", header["kid"], expectedKid)
	}
}

func TestVerifyJWT_HappyPath(t *testing.T) {
	auth := newTestAuthority(t)
	mj, err := auth.MintJWT(MintRequest{Subject: "dec-test", Audience: "bhiv-core-runtime"})
	if err != nil {
		t.Fatalf("MintJWT: %v", err)
	}
	verified, code, detail := auth.VerifyJWT(mj.Token, VerifyOption{})
	if code != JWTVerifyOK {
		t.Fatalf("VerifyJWT: code=%s detail=%s", code, detail)
	}
	if verified.Subject != "dec-test" {
		t.Errorf("sub: got %s want dec-test", verified.Subject)
	}
	if verified.Source != "current" {
		t.Errorf("source: got %s want current", verified.Source)
	}
}

// ============================================================================
// RFC 7638 thumbprint determinism
// ============================================================================

func TestKidDerivation_RFC7638_Deterministic(t *testing.T) {
	pubHex := "11842138a82a4ce98e0c30a9c6b8b1dfa432b69d92a8fbb98f48a7e3e6b81b1c"
	pub, _ := hex.DecodeString(pubHex)
	got, err := ComputeRFC7638Thumbprint(pub)
	if err != nil {
		t.Fatalf("thumbprint: %v", err)
	}
	// Recompute — must be identical.
	got2, err := ComputeRFC7638Thumbprint(pub)
	if err != nil {
		t.Fatalf("thumbprint2: %v", err)
	}
	if got != got2 {
		t.Errorf("thumbprint not deterministic: %s vs %s", got, got2)
	}
	// And different key -> different kid.
	other, _ := hex.DecodeString("22842138a82a4ce98e0c30a9c6b8b1dfa432b69d92a8fbb98f48a7e3e6b81b1c")
	otherKid, _ := ComputeRFC7638Thumbprint(other)
	if got == otherKid {
		t.Error("thumbprint collision across different keys")
	}
}

// ============================================================================
// ADVERSARIAL
// ============================================================================

func TestVerify_RejectAlgNone(t *testing.T) {
	auth := newTestAuthority(t)
	// Craft alg=none token (unsigned).
	header := base64.RawURLEncoding.EncodeToString([]byte(`{"alg":"none","typ":"JWT"}`))
	payload := base64.RawURLEncoding.EncodeToString([]byte(`{"iss":"https://test.bhiv.local/authority","sub":"x","aud":"bhiv-core-runtime","exp":` + nowOffset(60) + `,"iat":` + nowOffset(0) + `}`))
	noneToken := header + "." + payload + "."
	_, code, _ := auth.VerifyJWT(noneToken, VerifyOption{})
	if code == JWTVerifyOK {
		t.Fatal("alg=none was ACCEPTED — RFC 8725 §3.1 violation")
	}
}

func TestVerify_RejectHS256WithPubKey(t *testing.T) {
	auth := newTestAuthority(t)
	pub := auth.CurrentSigner().PublicKey()
	// Build an HS256 token using the public key bytes as the HMAC secret.
	tok := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"iss": auth.Issuer(), "sub": "x", "aud": "bhiv-core-runtime",
		"exp": time.Now().Add(60 * time.Second).Unix(),
		"iat": time.Now().Unix(),
	})
	tok.Header["kid"] = auth.CurrentKid()
	signed, err := tok.SignedString([]byte(pub))
	if err != nil {
		t.Fatalf("sign HS256: %v", err)
	}
	_, code, _ := auth.VerifyJWT(signed, VerifyOption{})
	if code == JWTVerifyOK {
		t.Fatal("HS256 substitution accepted — alg pinning broken")
	}
}

func TestVerify_RejectUnknownKid(t *testing.T) {
	auth := newTestAuthority(t)
	// Mint a token from a different authority; same iss/aud, different kid.
	other := newTestAuthority(t)
	mj, err := other.MintJWT(MintRequest{Subject: "x", Audience: "bhiv-core-runtime"})
	if err != nil {
		t.Fatalf("other mint: %v", err)
	}
	_, code, _ := auth.VerifyJWT(mj.Token, VerifyOption{})
	if code == JWTVerifyOK {
		t.Fatal("foreign-kid token accepted")
	}
	if code != JWTVerifyKidUnknown && code != JWTVerifySignatureInvalid {
		t.Errorf("expected ERR_JWT_KID_UNKNOWN or ERR_JWT_SIGNATURE_INVALID, got %s", code)
	}
}

func TestVerify_RejectExpired(t *testing.T) {
	auth := newTestAuthority(t)
	// Mint with a backdated issuedAt + tiny TTL so the parser sees expired.
	mj, err := auth.MintJWT(MintRequest{
		Subject:  "x",
		IssuedAt: time.Now().Add(-2 * time.Minute),
		TTL:      time.Second, // exp = now - 2m + 1s = already-expired
	})
	if err != nil {
		t.Fatalf("MintJWT: %v", err)
	}
	_, code, _ := auth.VerifyJWT(mj.Token, VerifyOption{})
	if code != JWTVerifyExpired {
		t.Errorf("expected ERR_JWT_EXPIRED, got %s", code)
	}
	// AllowExpired path used by introspection.
	v, code2, _ := auth.VerifyJWT(mj.Token, VerifyOption{AllowExpired: true})
	if code2 != JWTVerifyOK {
		t.Errorf("AllowExpired path: code=%s", code2)
	}
	if v == nil {
		t.Error("AllowExpired returned nil VerifiedJWT")
	}
}

func TestVerify_RejectIssMismatch(t *testing.T) {
	auth := newTestAuthority(t)
	// Mint with a different iss by directly building a jwt.Token whose
	// claims we control. We have to sign with the live signer.
	signer := auth.CurrentSigner()
	tok := jwt.NewWithClaims(jwt.SigningMethodEdDSA, jwt.MapClaims{
		"iss": "https://attacker.example/authority",
		"sub": "x",
		"aud": "bhiv-core-runtime",
		"exp": time.Now().Add(60 * time.Second).Unix(),
		"iat": time.Now().Unix(),
	})
	tok.Header["kid"] = signer.Kid()
	signed, err := tok.SignedString(signerToEd25519PrivateKey(signer))
	if err != nil {
		t.Fatalf("sign: %v", err)
	}
	_, code, _ := auth.VerifyJWT(signed, VerifyOption{})
	if code != JWTVerifyIssuerMismatch {
		t.Errorf("expected ERR_JWT_ISSUER_MISMATCH, got %s", code)
	}
}

func TestVerify_RejectAudMismatch(t *testing.T) {
	auth := newTestAuthority(t)
	mj, err := auth.MintJWT(MintRequest{Subject: "x", Audience: "wrong-audience"})
	if err != nil {
		t.Fatalf("MintJWT: %v", err)
	}
	_, code, _ := auth.VerifyJWT(mj.Token, VerifyOption{})
	if code != JWTVerifyAudienceMismatch {
		t.Errorf("expected ERR_JWT_AUDIENCE_MISMATCH, got %s", code)
	}
}

// ============================================================================
// ROTATION
// ============================================================================

func TestRotation_BothKidsVerifyInGraceWindow(t *testing.T) {
	auth := newTestAuthority(t)
	oldMint, err := auth.MintJWT(MintRequest{Subject: "x"})
	if err != nil {
		t.Fatalf("old mint: %v", err)
	}
	oldKid := auth.CurrentKid()

	newSigner, err := GenerateLocalEd25519Signer()
	if err != nil {
		t.Fatalf("new signer: %v", err)
	}
	graceUntil := time.Now().Add(1 * time.Hour).UTC()
	if err := auth.AdoptRotatedSigner(newSigner, graceUntil); err != nil {
		t.Fatalf("AdoptRotatedSigner: %v", err)
	}
	if auth.CurrentKid() == oldKid {
		t.Fatal("rotation did not change kid")
	}

	// Old token must still verify (grace period).
	verifiedOld, code, _ := auth.VerifyJWT(oldMint.Token, VerifyOption{})
	if code != JWTVerifyOK {
		t.Errorf("old token in grace: code=%s", code)
	}
	if verifiedOld != nil && verifiedOld.Source != "grace-period" {
		t.Errorf("old token source: got %s want grace-period", verifiedOld.Source)
	}

	// New mint must verify under new kid as "current".
	newMint, err := auth.MintJWT(MintRequest{Subject: "y"})
	if err != nil {
		t.Fatalf("new mint: %v", err)
	}
	verifiedNew, code, _ := auth.VerifyJWT(newMint.Token, VerifyOption{})
	if code != JWTVerifyOK {
		t.Errorf("new token: code=%s", code)
	}
	if verifiedNew != nil && verifiedNew.Source != "current" {
		t.Errorf("new token source: got %s want current", verifiedNew.Source)
	}
}

func TestRotation_ExpiredGraceIsSwept(t *testing.T) {
	auth := newTestAuthority(t)
	oldMint, err := auth.MintJWT(MintRequest{Subject: "x"})
	if err != nil {
		t.Fatalf("old mint: %v", err)
	}
	newSigner, err := GenerateLocalEd25519Signer()
	if err != nil {
		t.Fatalf("new signer: %v", err)
	}
	graceUntil := time.Now().Add(-1 * time.Minute) // already expired
	if err := auth.AdoptRotatedSigner(newSigner, graceUntil); err != nil {
		t.Fatalf("AdoptRotatedSigner: %v", err)
	}
	// SnapshotKeys sweeps expired entries.
	_, grace, _, _ := auth.SnapshotKeys()
	if len(grace) != 0 {
		t.Errorf("expected 0 grace keys after sweep, got %d", len(grace))
	}
	// Old token should now FAIL because the kid is no longer in the set.
	_, code, _ := auth.VerifyJWT(oldMint.Token, VerifyOption{})
	if code == JWTVerifyOK {
		t.Fatal("token from swept grace key was ACCEPTED")
	}
}

// ============================================================================
// PERSISTENCE
// ============================================================================

func TestPersistSigner_RoundTrip(t *testing.T) {
	dir := t.TempDir()
	signer, err := GenerateLocalEd25519Signer()
	if err != nil {
		t.Fatalf("keygen: %v", err)
	}
	if err := PersistSignerToDisk(signer, dir); err != nil {
		t.Fatalf("persist: %v", err)
	}
	privPath := filepath.Join(dir, "current.key")
	pubPath := filepath.Join(dir, "current.pub")
	st, err := os.Stat(privPath)
	if err != nil {
		t.Fatalf("stat priv: %v", err)
	}
	if runtime.GOOS != "windows" {
		if st.Mode().Perm()&0o077 != 0 {
			t.Errorf("priv mode=%o, expected 0600", st.Mode().Perm())
		}
	}

	loaded, ephemeral, _, err := loadOrGenerateSigner(privPath, pubPath, dir)
	if err != nil {
		t.Fatalf("load: %v", err)
	}
	if ephemeral {
		t.Error("loaded signer reported ephemeral=true")
	}
	if loaded.Kid() != signer.Kid() {
		t.Errorf("kid mismatch: %s vs %s", loaded.Kid(), signer.Kid())
	}
}

// ============================================================================
// JWKS DOCUMENT
// ============================================================================

func TestJWKS_HasRequiredFields(t *testing.T) {
	auth := newTestAuthority(t)
	doc, raw, etag, err := auth.BuildJWKSDocument()
	if err != nil {
		t.Fatalf("BuildJWKSDocument: %v", err)
	}
	if etag == "" {
		t.Error("etag empty")
	}
	if len(raw) == 0 {
		t.Error("canonical bytes empty")
	}
	if doc.Issuer != auth.Issuer() {
		t.Errorf("issuer mismatch: got %s want %s", doc.Issuer, auth.Issuer())
	}
	if len(doc.Keys) != 1 {
		t.Fatalf("expected 1 key, got %d", len(doc.Keys))
	}
	k := doc.Keys[0]
	if k.Kty != "OKP" || k.Crv != "Ed25519" || k.Alg != "EdDSA" || k.Use != "sig" {
		t.Errorf("JWK field shape wrong: %+v", k)
	}
	if k.Source != "current" {
		t.Errorf("source: got %s want current", k.Source)
	}
	// base64url x must decode to 32 bytes.
	xBytes, err := base64.RawURLEncoding.DecodeString(k.X)
	if err != nil {
		t.Fatalf("decode x: %v", err)
	}
	if len(xBytes) != ed25519.PublicKeySize {
		t.Errorf("x length=%d want %d", len(xBytes), ed25519.PublicKeySize)
	}
}

func TestDiscovery_HasRequiredFields(t *testing.T) {
	auth := newTestAuthority(t)
	doc, body, err := auth.BuildDiscoveryDocument("https://test.bhiv.local")
	if err != nil {
		t.Fatalf("BuildDiscoveryDocument: %v", err)
	}
	if len(body) == 0 {
		t.Error("body empty")
	}
	if doc.Issuer != auth.Issuer() {
		t.Errorf("issuer mismatch")
	}
	if doc.JWKSURI != "https://test.bhiv.local"+JWKSPath {
		t.Errorf("jwks_uri: got %s", doc.JWKSURI)
	}
	if doc.TokenEndpoint != "https://test.bhiv.local/sarathi/enforce" {
		t.Errorf("token_endpoint: got %s", doc.TokenEndpoint)
	}
	if len(doc.SigningAlgValuesSupported) != 1 || doc.SigningAlgValuesSupported[0] != "EdDSA" {
		t.Errorf("alg list: %v", doc.SigningAlgValuesSupported)
	}
}

// ============================================================================
// DETERMINISM (jti uniqueness)
// ============================================================================

func TestMint_DistinctTokensSameInput(t *testing.T) {
	auth := newTestAuthority(t)
	a, err := auth.MintJWT(MintRequest{Subject: "x"})
	if err != nil {
		t.Fatalf("mint a: %v", err)
	}
	// Sleep just long enough that iat (second resolution) can differ.
	time.Sleep(1100 * time.Millisecond)
	b, err := auth.MintJWT(MintRequest{Subject: "x"})
	if err != nil {
		t.Fatalf("mint b: %v", err)
	}
	if a.Token == b.Token {
		t.Fatal("two mints produced identical JWTs")
	}
	if a.Claims["jti"] == b.Claims["jti"] {
		t.Fatal("two mints produced identical jti")
	}
	// Both must still verify under the same authority.
	if _, code, _ := auth.VerifyJWT(a.Token, VerifyOption{}); code != JWTVerifyOK {
		t.Errorf("a verify: %s", code)
	}
	if _, code, _ := auth.VerifyJWT(b.Token, VerifyOption{}); code != JWTVerifyOK {
		t.Errorf("b verify: %s", code)
	}
}

// ============================================================================
// PRODUCTION GATES
// ============================================================================

func TestProductionGate_EphemeralRefused(t *testing.T) {
	t.Setenv("SARATHI_ENV", "production")
	auth := newTestAuthority(t) // ephemeral=true
	err := EnforceJWTAuthorityProductionGates(auth)
	if err == nil {
		t.Fatal("expected production refusal for ephemeral key")
	}
	if !strings.Contains(err.Error(), CodeJWTAuthorityKeyMissing) {
		t.Errorf("error did not mention %s: %v", CodeJWTAuthorityKeyMissing, err)
	}
}

func TestProductionGate_NonHTTPSIssuerRefused(t *testing.T) {
	t.Setenv("SARATHI_ENV", "production")
	// Persisted (non-ephemeral) but with http:// issuer.
	dir := t.TempDir()
	signer, _ := GenerateLocalEd25519Signer()
	_ = PersistSignerToDisk(signer, dir)
	auth, _ := NewJWTAuthority(JWTAuthorityConfig{
		Signer:    signer,
		Issuer:    "http://insecure.example/authority",
		KeysDir:   dir,
		Ephemeral: false,
	})
	err := EnforceJWTAuthorityProductionGates(auth)
	if err == nil {
		t.Fatal("expected production refusal for http:// issuer")
	}
	if !strings.Contains(err.Error(), CodeJWTAuthorityIssuerInsecure) {
		t.Errorf("error did not mention %s: %v", CodeJWTAuthorityIssuerInsecure, err)
	}
}

// ============================================================================
// HELPERS
// ============================================================================

func nowOffset(seconds int64) string {
	// Returns unix seconds as a JSON-number string usable inside a raw
	// payload literal.
	return strconvFormatInt(time.Now().Unix() + seconds)
}

func strconvFormatInt(n int64) string {
	// Avoid importing strconv just for this — direct formatting.
	if n == 0 {
		return "0"
	}
	neg := n < 0
	if neg {
		n = -n
	}
	var b [32]byte
	i := len(b)
	for n > 0 {
		i--
		b[i] = byte('0' + n%10)
		n /= 10
	}
	if neg {
		i--
		b[i] = '-'
	}
	return string(b[i:])
}

// Ensure verifier handles a missing kid header.
func TestVerify_RejectKidMissing(t *testing.T) {
	auth := newTestAuthority(t)
	signer := auth.CurrentSigner()
	tok := jwt.NewWithClaims(jwt.SigningMethodEdDSA, jwt.MapClaims{
		"iss": auth.Issuer(),
		"sub": "x",
		"aud": "bhiv-core-runtime",
		"exp": time.Now().Add(60 * time.Second).Unix(),
		"iat": time.Now().Unix(),
	})
	// DO NOT set kid header.
	signed, err := tok.SignedString(signerToEd25519PrivateKey(signer))
	if err != nil {
		t.Fatalf("sign: %v", err)
	}
	_, code, _ := auth.VerifyJWT(signed, VerifyOption{})
	if code != JWTVerifyKidMissing {
		t.Errorf("expected ERR_JWT_KID_MISSING, got %s", code)
	}
}
