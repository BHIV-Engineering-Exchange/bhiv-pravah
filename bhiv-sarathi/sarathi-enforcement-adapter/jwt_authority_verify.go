package main

// jwt_authority_verify.go — v15.6 JWT verifier (Bridge-mirror).
//
// This file is what the in-process /sarathi/validate-token and
// /sarathi/v1/token/introspect handlers call. It is also what the
// failure-demo Bridge mock uses to prove the wire format is library-
// independent.
//
// Verification posture (RFC 8725 Best Current Practices):
//   * alg pinning: ONLY "EdDSA" accepted via jwt.WithValidMethods.
//     alg=none and any HMAC family are rejected at parse time.
//   * kid lookup: the JWTAuthority resolves kid -> ed25519.PublicKey via
//     SnapshotKeys (current + non-expired grace). Unknown kid -> reject.
//   * iss / aud / exp / nbf: all validated. iss MUST equal the authority's
//     configured issuer string. aud MUST match the authority's audience
//     (or any element when an audience list is configured).
//   * Optional consumption check: when consultRegistry=true the verifier
//     looks up sarathi:token_hash in TokenRegistry.IsConsumed and rejects
//     replays.
//
// Errors are deliberately opaque to outside callers — they're collapsed to
// a small enum so the introspect handler can return RFC 7662 active=false
// without disclosing the failure cause. Internal callers (tests, audit) get
// the detail string.
//
// TAG: jwt-authority-v15.6

import (
	"crypto/ed25519"
	"fmt"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

// VerifyOption tunes the verifier.
type VerifyOption struct {
	// ExpectedAudience overrides the authority default. Empty -> use authority.
	ExpectedAudience string
	// AllowMissingAudience accepts tokens without aud (debug only).
	AllowMissingAudience bool
	// AllowExpired accepts already-exp tokens (introspection use case).
	AllowExpired bool
	// ConsultConsumptionRegistry, when true, looks up
	// sarathi:token_hash via TokenRegistry.IsConsumed.
	ConsultConsumptionRegistry bool
	// TokenRegistry to consult when ConsultConsumptionRegistry is true.
	TokenRegistry *TokenRegistry
	// Clock allows tests to override the wall-clock.
	Clock func() time.Time
}

// VerifiedJWT is the parsed + verified token. Empty/zero on failure.
type VerifiedJWT struct {
	Token   *jwt.Token
	Claims  jwt.MapClaims
	Kid     string
	Issuer  string
	Subject string
	Audience string
	JTI     string
	IssuedAt  time.Time
	NotBefore time.Time
	ExpiresAt time.Time
	TokenHash string // sarathi:token_hash, when present
	DecisionID string
	Verdict   string
	Consumed  bool // populated when ConsultConsumptionRegistry=true
	Source    string // "current" | "grace-period"
}

// Standard verify error codes. Bridge sees only opaque "invalid"; internal
// tests + the introspection audit row capture the specific reason.
const (
	JWTVerifyOK                  = "OK"
	JWTVerifyMalformed           = "ERR_JWT_MALFORMED"
	JWTVerifyAlgInvalid          = "ERR_JWT_ALG_INVALID"
	JWTVerifyKidMissing          = "ERR_JWT_KID_MISSING"
	JWTVerifyKidUnknown          = "ERR_JWT_KID_UNKNOWN"
	JWTVerifySignatureInvalid    = "ERR_JWT_SIGNATURE_INVALID"
	JWTVerifyExpired             = "ERR_JWT_EXPIRED"
	JWTVerifyNotYetValid         = "ERR_JWT_NOT_YET_VALID"
	JWTVerifyIssuerMismatch      = "ERR_JWT_ISSUER_MISMATCH"
	JWTVerifyAudienceMismatch    = "ERR_JWT_AUDIENCE_MISMATCH"
	JWTVerifyConsumedReplay      = "ERR_JWT_CONSUMED_REPLAY"
	JWTVerifyUnexpectedClaimType = "ERR_JWT_UNEXPECTED_CLAIM_TYPE"
)

// VerifyJWT parses + verifies a compact JWT against the authority's current
// key set. On success returns a populated VerifiedJWT; on failure returns
// nil, the standardized code, and a detail string.
//
// The verifier does NOT touch the network; it is fully offline (which is
// the point of Bridge's caching the JWKS).
func (a *JWTAuthority) VerifyJWT(tokenStr string, opts VerifyOption) (*VerifiedJWT, string, string) {
	if a == nil {
		return nil, JWTVerifyMalformed, "nil JWTAuthority"
	}
	if strings.TrimSpace(tokenStr) == "" {
		return nil, JWTVerifyMalformed, "empty token"
	}
	clk := opts.Clock
	if clk == nil {
		clk = func() time.Time { return time.Now().UTC() }
	}

	parser := jwt.NewParser(jwt.WithValidMethods([]string{"EdDSA"}))
	parsed, err := parser.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
		// alg already validated by jwt.WithValidMethods; check kid is
		// present and resolves.
		if t == nil || t.Header == nil {
			return nil, fmt.Errorf(JWTVerifyKidMissing)
		}
		kidRaw, ok := t.Header["kid"]
		if !ok {
			return nil, fmt.Errorf(JWTVerifyKidMissing + ":no_kid")
		}
		kid, ok := kidRaw.(string)
		if !ok || kid == "" {
			return nil, fmt.Errorf(JWTVerifyKidMissing + ":kid_not_string")
		}
		pub := a.LookupPublicKey(kid)
		if pub == nil {
			return nil, fmt.Errorf(JWTVerifyKidUnknown+":kid=%s", kid)
		}
		return ed25519.PublicKey(pub), nil
	})
	if err != nil {
		// Map jwt/v5 sentinel errors to our codes for the verbose path.
		switch {
		case strings.Contains(err.Error(), JWTVerifyKidMissing):
			return nil, JWTVerifyKidMissing, err.Error()
		case strings.Contains(err.Error(), JWTVerifyKidUnknown):
			return nil, JWTVerifyKidUnknown, err.Error()
		case strings.Contains(err.Error(), "signing method"):
			return nil, JWTVerifyAlgInvalid, err.Error()
		case strings.Contains(err.Error(), "token is expired"):
			if opts.AllowExpired {
				// continue with the parsed claims even though signature
				// validated against an expired token
				break
			}
			return nil, JWTVerifyExpired, err.Error()
		case strings.Contains(err.Error(), "token used before issued") ||
			strings.Contains(err.Error(), "not valid yet"):
			return nil, JWTVerifyNotYetValid, err.Error()
		case strings.Contains(err.Error(), "signature is invalid") ||
			strings.Contains(err.Error(), "crypto/ed25519"):
			return nil, JWTVerifySignatureInvalid, err.Error()
		default:
			return nil, JWTVerifyMalformed, err.Error()
		}
	}

	if parsed == nil || parsed.Claims == nil {
		return nil, JWTVerifyMalformed, "parser returned nil"
	}
	claims, ok := parsed.Claims.(jwt.MapClaims)
	if !ok {
		return nil, JWTVerifyUnexpectedClaimType, "claims not jwt.MapClaims"
	}

	v := &VerifiedJWT{
		Token:  parsed,
		Claims: claims,
	}

	// Header bookkeeping.
	if kidRaw, ok := parsed.Header["kid"]; ok {
		if k, ok2 := kidRaw.(string); ok2 {
			v.Kid = k
			if a.CurrentKid() == k {
				v.Source = "current"
			} else {
				v.Source = "grace-period"
			}
		}
	}

	// iss check.
	if iss, ok := claims["iss"].(string); ok {
		v.Issuer = iss
		if iss != a.Issuer() {
			return nil, JWTVerifyIssuerMismatch,
				fmt.Sprintf("iss=%q want=%q", iss, a.Issuer())
		}
	} else {
		return nil, JWTVerifyIssuerMismatch, "iss claim missing or not string"
	}

	// aud check.
	expectedAud := strings.TrimSpace(opts.ExpectedAudience)
	if expectedAud == "" {
		expectedAud = a.Audience()
	}
	matched := false
	switch audVal := claims["aud"].(type) {
	case string:
		v.Audience = audVal
		if audVal == expectedAud {
			matched = true
		}
	case []interface{}:
		for _, a2 := range audVal {
			if s, ok := a2.(string); ok {
				if v.Audience == "" {
					v.Audience = s
				}
				if s == expectedAud {
					matched = true
					v.Audience = s
					break
				}
			}
		}
	case nil:
		if opts.AllowMissingAudience {
			matched = true
		}
	}
	if !matched {
		return nil, JWTVerifyAudienceMismatch,
			fmt.Sprintf("aud=%v want=%q", claims["aud"], expectedAud)
	}

	// Time bounds (parser already enforced these unless opts.AllowExpired).
	if subVal, ok := claims["sub"].(string); ok {
		v.Subject = subVal
	}
	if jtiVal, ok := claims["jti"].(string); ok {
		v.JTI = jtiVal
	}
	v.IssuedAt = unixToTime(claims["iat"])
	v.NotBefore = unixToTime(claims["nbf"])
	v.ExpiresAt = unixToTime(claims["exp"])

	// Pluck the small set of private claims callers tend to need.
	if th, ok := claims[claimMintPrefix+"token_hash"].(string); ok {
		v.TokenHash = th
	}
	if did, ok := claims[claimMintPrefix+"decision_id"].(string); ok {
		v.DecisionID = did
	}
	if vd, ok := claims[claimMintPrefix+"verdict"].(string); ok {
		v.Verdict = vd
	}

	// Optional consumption check.
	if opts.ConsultConsumptionRegistry && opts.TokenRegistry != nil && v.TokenHash != "" {
		if opts.TokenRegistry.IsConsumed(v.TokenHash) {
			v.Consumed = true
			return v, JWTVerifyConsumedReplay,
				fmt.Sprintf("token_hash=%s already consumed", v.TokenHash)
		}
	}

	return v, JWTVerifyOK, ""
}

// unixToTime tolerates float64 (json default) and int64 (rare) unix-second
// representations. Zero on parse failure.
func unixToTime(v interface{}) time.Time {
	switch t := v.(type) {
	case float64:
		return time.Unix(int64(t), 0).UTC()
	case int64:
		return time.Unix(t, 0).UTC()
	case int:
		return time.Unix(int64(t), 0).UTC()
	}
	return time.Time{}
}

// LooksLikeJWT reports whether s is plausibly a compact JWT (two dots, header
// starts with "eyJ" which is base64url("{")). Used by handleValidateToken to
// decide between the legacy capability-token-id branch and the JWT branch.
func LooksLikeJWT(s string) bool {
	if len(s) < 16 {
		return false
	}
	if !strings.HasPrefix(s, "eyJ") {
		return false
	}
	return strings.Count(s, ".") == 2
}
