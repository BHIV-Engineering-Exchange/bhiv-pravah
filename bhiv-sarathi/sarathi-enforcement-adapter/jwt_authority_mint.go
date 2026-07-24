package main

// jwt_authority_mint.go — v15.6 JWT mint path.
//
// MintRequest -> signed compact JWT, plus an audit row in
// proof_logs/jwt_issuance.jsonl.
//
// Two mint flows are supported (both Sovereign-path-only; /v1/enforce gets
// the field too via the GatedBridge for parity):
//
//  1. MintFromCapabilityToken — when an in-process CapabilityToken exists.
//     Maps the existing capabilityTokenPayload fields onto JWT claims with
//     the "sarathi:" private-claim prefix. This is the primary path for
//     /v1/enforce + the legacy path.
//
//  2. MintFromEnvelope — when the request came through PDPAdapter.Ingest
//     and we only have a PropagationEnvelope to bind to. The Sovereign
//     /sarathi/enforce path uses this — there is no in-process CapabilityToken
//     for the external-decision pipeline. We pack the envelope's decision_id,
//     trace_id, response_hash, chain_binding_hash, enforcement_hash, verdict
//     into the same JWT shape so Bridge cannot tell the two mint paths apart.
//
// Both flows produce a compact RFC 7515 JWT (header.payload.signature) with:
//   * Header: alg=EdDSA, typ=JWT, kid=<RFC 7638 thumbprint>
//   * Standard claims: iss, sub, aud, exp, nbf, iat, jti
//   * Private claims under the "sarathi:" prefix
//
// TAG: jwt-authority-v15.6

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

// MintRequest carries the per-call mint inputs that aren't already on the
// authority. Optional fields default to authority-wide values.
type MintRequest struct {
	// Subject identifies the resource the token authorises. Typically the
	// decision_id.
	Subject string
	// Audience overrides the authority default per-call. Empty -> default.
	Audience string
	// JTI is the unique token id. Empty -> uuid v4 minted here.
	JTI string
	// IssuedAt anchors the iat/nbf claims. Zero -> now.
	IssuedAt time.Time
	// TTL overrides the authority default per-call. Zero -> authority TTL.
	TTL time.Duration

	// PrivateClaims is the bag of "sarathi:<name>" claims. Caller is
	// responsible for selecting the right field set; the mint helpers below
	// build this automatically from a CapabilityToken or envelope.
	PrivateClaims map[string]interface{}

	// CorrelationID used for the audit-log row; not added as a claim by
	// the framework — callers usually also include it in PrivateClaims.
	CorrelationID string
}

// MintedJWT is the return shape: the compact wire token plus enough metadata
// to log + attach to a response without re-parsing.
type MintedJWT struct {
	Token         string
	Header        map[string]interface{}
	Claims        map[string]interface{}
	Kid           string
	ExpiresAt     time.Time
	SigningLatency time.Duration
}

// claimMintPrefix is the "sarathi:" private-claim prefix per RFC 7519 §4.3.
const claimMintPrefix = "sarathi:"

// JWTHeaderTyp is the typ header value. RFC 8725 §3.11 recommends typ for
// JWTs intended as access tokens.
const JWTHeaderTyp = "JWT"

// ============================================================================
// PRIMARY MINT
// ============================================================================

// MintJWT serializes a JWT from a MintRequest. Returns the compact token bytes,
// a snapshot of the header + claims for the response handler, the exp time
// for logging, and the time the signer spent.
//
// Concurrency: safe — the authority is read-locked for the duration of the
// signing call.
func (a *JWTAuthority) MintJWT(req MintRequest) (*MintedJWT, error) {
	if a == nil {
		return nil, fmt.Errorf("MintJWT: nil JWTAuthority")
	}
	signer := a.CurrentSigner()
	if signer == nil {
		return nil, fmt.Errorf("MintJWT: no current signer")
	}
	now := time.Now().UTC()
	if !req.IssuedAt.IsZero() {
		now = req.IssuedAt.UTC()
	}
	ttl := req.TTL
	if ttl <= 0 || ttl > a.TokenTTL() {
		ttl = a.TokenTTL()
	}
	jti := strings.TrimSpace(req.JTI)
	if jti == "" {
		jti = newMintNonce()
	}
	aud := strings.TrimSpace(req.Audience)
	if aud == "" {
		aud = a.Audience()
	}
	exp := now.Add(ttl)
	claims := jwt.MapClaims{
		"iss": a.Issuer(),
		"sub": strings.TrimSpace(req.Subject),
		"aud": aud,
		"exp": exp.Unix(),
		"nbf": now.Unix(),
		"iat": now.Unix(),
		"jti": jti,
	}
	for k, v := range req.PrivateClaims {
		// Force the namespace prefix even if a caller forgot.
		key := k
		if !strings.HasPrefix(key, claimMintPrefix) {
			key = claimMintPrefix + key
		}
		claims[key] = v
	}
	// Always pin the schema-version claim so Bridge can detect contract drift.
	if _, ok := claims[claimMintPrefix+"schema_version"]; !ok {
		claims[claimMintPrefix+"schema_version"] = JWTCapabilityTokenSchema
	}

	// Build the JWT with EdDSA, attach kid header.
	token := jwt.NewWithClaims(jwt.SigningMethodEdDSA, claims)
	token.Header["kid"] = signer.Kid()
	token.Header["typ"] = JWTHeaderTyp
	// alg is set by jwt.NewWithClaims; we don't override it.

	signingStart := time.Now()
	tokenStr, err := token.SignedString(signerToEd25519PrivateKey(signer))
	if err != nil {
		return nil, fmt.Errorf("MintJWT: sign: %w", err)
	}
	signingLat := time.Since(signingStart)

	// Snapshot the header for the caller (no extra parse).
	header := map[string]interface{}{
		"alg": "EdDSA",
		"typ": JWTHeaderTyp,
		"kid": signer.Kid(),
	}
	out := &MintedJWT{
		Token:          tokenStr,
		Header:         header,
		Claims:         map[string]interface{}(claims),
		Kid:            signer.Kid(),
		ExpiresAt:      exp,
		SigningLatency: signingLat,
	}

	// Best-effort audit. Errors logged but not returned to the caller — the
	// token has been minted; failing the request because the audit log is
	// unwritable would create a worse failure mode than logging the miss.
	a.appendIssuanceAudit(out, req.CorrelationID)
	return out, nil
}

// signerToEd25519PrivateKey extracts the raw private key from a Signer when
// it's a LocalEd25519Signer; HSM/KMS signers should implement their own
// jwt.SigningMethod (out of scope for v15.6).
func signerToEd25519PrivateKey(s Signer) interface{} {
	if local, ok := s.(*LocalEd25519Signer); ok {
		return local.PrivateKey()
	}
	// Fallback: jwt/v5 will reject a non-ed25519.PrivateKey, surfacing the
	// HSM/KMS gap as a clear error — that's the right failure mode until
	// the dedicated SigningMethod lands.
	return nil
}

// newMintNonce returns a fresh UUIDv4 string. Uses the existing helper
// elsewhere in the repo (see evaluator_registration_challenge.go).
func newMintNonce() string {
	return generatePhase12UUID()
}

// ============================================================================
// CAPABILITY TOKEN -> MINT REQUEST
// ============================================================================

// MintFromCapabilityToken converts an in-process CapabilityToken into a
// MintRequest and signs it. Used by the /v1/enforce path (and tests).
//
// The legacy in-struct issuer ("sarathi-enforcement-adapter") is preserved
// as a private claim so the Bridge audit can cross-check against the
// internal hash chain.
func (a *JWTAuthority) MintFromCapabilityToken(ct *CapabilityToken, traceID string) (*MintedJWT, error) {
	if ct == nil {
		return nil, fmt.Errorf("MintFromCapabilityToken: nil token")
	}
	private := map[string]interface{}{
		"request_hash":     ct.RequestHash(),
		"policy_hash":      ct.PolicyHash(),
		"enforcement_hash": ct.EnforcementHash(),
		"correlation_id":   ct.CorrelationID(),
		"verdict":          ct.Verdict(),
		"obligations":      ct.Obligations(),
		"registry_version": ct.RegistryVersion(),
		"rpa_hash":         ct.RpaHash(),
		"token_hash":       ct.TokenHash(),
		"legacy_issuer":    ct.Issuer(),
		"schema_version":   JWTCapabilityTokenSchema,
	}
	if traceID != "" {
		private["trace_id"] = traceID
	}
	req := MintRequest{
		Subject:       ct.DecisionID(),
		Audience:      ct.Audience(),
		JTI:           ct.TokenID(),
		IssuedAt:      ct.IssuedAt(),
		TTL:           time.Until(ct.ExpiresAt()),
		PrivateClaims: private,
		CorrelationID: ct.CorrelationID(),
	}
	return a.MintJWT(req)
}

// MintFromEnvelope converts a PropagationEnvelope (the canonical artefact the
// /sarathi/enforce path returns) into a MintRequest. Used by the Sovereign
// path's mint hook in handleIngestDecision.
//
// The envelope's response_hash and chain_binding_hash are the strongest
// cross-system identifiers Sarathi produces; binding them into the JWT lets
// Bridge cross-verify the token against the propagation chain it observes.
func (a *JWTAuthority) MintFromEnvelope(env *PropagationEnvelope, traceID, audienceHint string) (*MintedJWT, error) {
	if env == nil {
		return nil, fmt.Errorf("MintFromEnvelope: nil envelope")
	}
	private := map[string]interface{}{
		"decision_id":        env.DecisionID(),
		"decision_hash":      env.DecisionHash(),
		"decision_core_hash": env.DecisionCoreHash(),
		"response_hash":      env.ResponseHash(),
		"chain_binding_hash": env.ChainBindingHash(),
		"enforcement_hash":   env.EnforcementHash(),
		"correlation_id":     env.CorrelationID(),
		"execution_id":       env.ExecutionID(),
		"verdict":            env.Verdict(),
		"schema_version":     JWTCapabilityTokenSchema,
		"legacy_issuer":      "sarathi-enforcement-adapter",
	}
	if tid := strings.TrimSpace(traceID); tid != "" {
		private["trace_id"] = tid
	} else if env.TraceID() != "" {
		private["trace_id"] = env.TraceID()
	}
	req := MintRequest{
		Subject:       env.DecisionID(),
		Audience:      audienceHint,
		PrivateClaims: private,
		CorrelationID: env.CorrelationID(),
	}
	return a.MintJWT(req)
}

// ============================================================================
// AUDIT LOG (proof_logs/jwt_issuance.jsonl)
// ============================================================================

var (
	issuanceAuditMu sync.Mutex
)

// appendIssuanceAudit writes a single JSON line per mint. Append-only;
// rotation handled by ops. Failures are logged but not returned.
func (a *JWTAuthority) appendIssuanceAudit(mj *MintedJWT, correlationID string) {
	if a == nil || mj == nil {
		return
	}
	path := a.IssuanceLogPath()
	if path == "" {
		return
	}
	row := map[string]interface{}{
		"event":          "jwt_issued",
		"schema_version": JWTAuthoritySchemaVersion,
		"ts":             time.Now().UTC().Format(time.RFC3339Nano),
		"jti":            mj.Claims["jti"],
		"sub":            mj.Claims["sub"],
		"iss":            mj.Claims["iss"],
		"aud":            mj.Claims["aud"],
		"exp":            mj.Claims["exp"],
		"iat":            mj.Claims["iat"],
		"kid":            mj.Kid,
		"size_bytes":     len(mj.Token),
		"signing_lat_us": mj.SigningLatency.Microseconds(),
		"correlation_id": correlationID,
	}
	// Pluck a small set of private claims for fast querying without re-parsing.
	for _, k := range []string{"trace_id", "decision_id", "verdict", "registry_version"} {
		if v, ok := mj.Claims[claimMintPrefix+k]; ok {
			row[k] = v
		}
	}
	line, err := json.Marshal(row)
	if err != nil {
		return
	}
	line = append(line, '\n')

	issuanceAuditMu.Lock()
	defer issuanceAuditMu.Unlock()
	if dir := filepath.Dir(path); dir != "" && dir != "." {
		_ = os.MkdirAll(dir, 0o755)
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[jwt_authority] WARN: open issuance log %s: %v\n", path, err)
		return
	}
	defer f.Close()
	if _, werr := f.Write(line); werr != nil {
		fmt.Fprintf(os.Stderr, "[jwt_authority] WARN: write issuance log: %v\n", werr)
		return
	}
	_ = f.Sync()
}
