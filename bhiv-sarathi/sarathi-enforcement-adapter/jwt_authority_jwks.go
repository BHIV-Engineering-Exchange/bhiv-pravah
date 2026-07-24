package main

// jwt_authority_jwks.go — v15.6 JWKS publication for the outbound JWT
// authority.
//
// This file builds the RFC 7517 JWKS document that Bridge fetches at
// GET /sarathi/.well-known/jwks.json. The bytes here are CANONICAL — same
// inputs always produce byte-identical output so the served ETag is stable
// across in-flight requests (Auth0 / AWS Cognito behave the same way).
//
// IMPORTANT DISTINCTION:
//   This is the AUTHORITY trust bundle. It publishes ONLY the public keys
//   used to sign outbound capability-token JWTs.
//   The OTHER JWKS document (evaluator_registry_extension.go::TrustBundleJWKS,
//   served at /v1/evaluators/.well-known/jwks when the FROZEN registration
//   API is mounted) publishes the INBOUND evaluator trust set used to verify
//   callers like Sovereign. The two bundles MUST stay separate — they bind
//   different trust directions.
//
// RFC compliance:
//   * RFC 7517 §4 — JWK members (kty, kid, use, alg)
//   * RFC 8037 §2 — OKP / Ed25519 (kty=OKP, crv=Ed25519, x = base64url(pub))
//   * RFC 7638 — JWK thumbprint as kid
//   * RFC 7517 §4.9 — x5t#S256 (we use SHA-256 hex of the public bytes for
//                              consistency with the evaluator bundle; Bridge
//                              treats it as advisory)
//
// TAG: jwt-authority-v15.6

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"
)

// AuthorityJWKSContentType is what the HTTP handler emits.
const AuthorityJWKSContentType = "application/jwk-set+json"

// AuthorityJWKSCacheMaxAgeSeconds is the suggested Cache-Control max-age.
// Auth0 commonly recommends 5–60 min; we default to 5 min so a rotation
// is visible to Bridge within one cache cycle.
const AuthorityJWKSCacheMaxAgeSeconds = 300

// authorityJWKSKey is one entry in the published key set.
//
// Field naming follows the evaluator-bundle shape from
// evaluator_registry_extension.go so operators see one consistent JWKS schema
// across both bundles. The `source` field doubles as a rotation hint:
// "current" or "grace-period".
type authorityJWKSKey struct {
	Kid          string `json:"kid"`               // RFC 7638 thumbprint, hex
	Kty          string `json:"kty"`               // "OKP" (RFC 8037)
	Crv          string `json:"crv"`               // "Ed25519"
	X            string `json:"x"`                 // base64url(pub), no pad
	Use          string `json:"use"`               // "sig"
	Alg          string `json:"alg"`               // "EdDSA" (RFC 8037)
	X5tS256      string `json:"x5t#S256"`          // SHA-256 hex of pub bytes
	IssuedAt     int64  `json:"iat"`               // unix seconds
	Source       string `json:"source"`            // "current" | "grace-period"
	GraceExpires string `json:"grace_expires,omitempty"`
}

// authorityJWKSDocument is the top-level JWKS payload.
type authorityJWKSDocument struct {
	SchemaVersion   string             `json:"schema_version"`
	RegistryVersion uint64             `json:"registry_version"`
	Issuer          string             `json:"issuer"`
	IssuedAt        string             `json:"issued_at"`
	Keys            []authorityJWKSKey `json:"keys"`
}

// BuildJWKSDocument returns the JWKS doc + canonical bytes + ETag for the
// current authority state. Safe to call from any goroutine.
//
// Returns:
//
//	doc          — populated authorityJWKSDocument struct (for tests)
//	canonical    — the JSON bytes that should be served on the wire
//	etag         — quoted ETag suitable for the HTTP header
//	err          — non-nil on serialization failure (should never happen)
func (a *JWTAuthority) BuildJWKSDocument() (authorityJWKSDocument, []byte, string, error) {
	if a == nil {
		return authorityJWKSDocument{}, nil, "", fmt.Errorf("BuildJWKSDocument: nil JWTAuthority")
	}
	cur, grace, ver, _ := a.SnapshotKeys()
	doc := authorityJWKSDocument{
		SchemaVersion:   a.SchemaVersion(),
		RegistryVersion: ver,
		Issuer:          a.Issuer(),
		IssuedAt:        time.Now().UTC().Format(time.RFC3339),
		Keys:            []authorityJWKSKey{},
	}
	if cur != nil {
		doc.Keys = append(doc.Keys, jwksEntryFromKey(cur.Kid(), cur.PublicKey(), cur.CreatedAt(), "current", time.Time{}))
	}
	for _, g := range grace {
		doc.Keys = append(doc.Keys, jwksEntryFromKey(g.Kid, g.Pub, g.CreatedAt, "grace-period", g.GraceExpires))
	}
	canonical, err := json.MarshalIndent(&doc, "", "  ")
	if err != nil {
		return doc, nil, "", fmt.Errorf("BuildJWKSDocument: marshal: %w", err)
	}
	etagSum := sha256.Sum256(canonical)
	etag := fmt.Sprintf(`"%s"`, hex.EncodeToString(etagSum[:]))
	return doc, canonical, etag, nil
}

// jwksEntryFromKey converts an Ed25519 public key + metadata into one JWK.
func jwksEntryFromKey(kid string, pub []byte, createdAt time.Time, source string, graceExpires time.Time) authorityJWKSKey {
	x5tSum := sha256.Sum256(pub)
	entry := authorityJWKSKey{
		Kid:      kid,
		Kty:      "OKP",
		Crv:      "Ed25519",
		X:        base64UrlEncode(pub),
		Use:      "sig",
		Alg:      "EdDSA",
		X5tS256:  hex.EncodeToString(x5tSum[:]),
		IssuedAt: createdAt.Unix(),
		Source:   source,
	}
	if !graceExpires.IsZero() {
		entry.GraceExpires = graceExpires.UTC().Format(time.RFC3339)
	}
	return entry
}

// ============================================================================
// DISCOVERY DOC (RFC 8414-adapted)
// ============================================================================

// AuthorityDiscoveryDocument is the OIDC-style discovery payload served at
// GET /sarathi/.well-known/sarathi-authority. Adapted from RFC 8414 (OAuth
// 2.0 Authorization Server Metadata): Sarathi is not a full OAuth server, so
// `token_endpoint` advertises /sarathi/enforce (the place where Bridge
// obtains a token by submitting a signed Sovereign decision) and no client-
// credentials grant is offered.
type AuthorityDiscoveryDocument struct {
	Issuer                                  string   `json:"issuer"`
	JWKSURI                                 string   `json:"jwks_uri"`
	TokenEndpoint                           string   `json:"token_endpoint"`
	IntrospectionEndpoint                   string   `json:"introspection_endpoint,omitempty"`
	SigningAlgValuesSupported               []string `json:"signing_alg_values_supported"`
	IDTokenSigningAlgValuesSupported        []string `json:"id_token_signing_alg_values_supported"`
	SubjectTypesSupported                   []string `json:"subject_types_supported"`
	IntrospectionAuthMethodsSupported       []string `json:"introspection_endpoint_auth_methods_supported,omitempty"`
	TokenEndpointAuthMethodsSupported       []string `json:"token_endpoint_auth_methods_supported"`
	TokenLifetimeSeconds                    int      `json:"token_lifetime_seconds"`
	Version                                 string   `json:"version"`
	SchemaVersion                           string   `json:"schema_version"`
}

// AuthorityDiscoverySchema pins the discovery-doc schema version.
const AuthorityDiscoverySchema = "sarathi-authority-discovery/v1.0"

// BuildDiscoveryDocument constructs the discovery JSON. baseURL must be the
// externally-visible base (e.g. https://sarathi.bhiv.local) so paths are
// fully qualified. When baseURL is empty (dev), relative paths are returned.
func (a *JWTAuthority) BuildDiscoveryDocument(baseURL string) (AuthorityDiscoveryDocument, []byte, error) {
	if a == nil {
		return AuthorityDiscoveryDocument{}, nil, fmt.Errorf("BuildDiscoveryDocument: nil JWTAuthority")
	}
	join := func(p string) string {
		if baseURL == "" {
			return p
		}
		// Avoid double slashes if baseURL already has trailing /.
		if baseURL[len(baseURL)-1] == '/' && p[0] == '/' {
			return baseURL + p[1:]
		}
		if baseURL[len(baseURL)-1] != '/' && p[0] != '/' {
			return baseURL + "/" + p
		}
		return baseURL + p
	}
	doc := AuthorityDiscoveryDocument{
		Issuer:                            a.Issuer(),
		JWKSURI:                           join(JWKSPath),
		TokenEndpoint:                     join("/sarathi/enforce"),
		SigningAlgValuesSupported:         []string{"EdDSA"},
		IDTokenSigningAlgValuesSupported:  []string{"EdDSA"},
		SubjectTypesSupported:             []string{"public"},
		TokenEndpointAuthMethodsSupported: []string{"none"},
		TokenLifetimeSeconds:              int(a.TokenTTL() / time.Second),
		Version:                           "v15.6",
		SchemaVersion:                     AuthorityDiscoverySchema,
	}
	if a.IntrospectionEnabled() {
		doc.IntrospectionEndpoint = join(TokenIntrospectPath)
		doc.IntrospectionAuthMethodsSupported = []string{"client_secret_basic"}
	}
	out, err := json.MarshalIndent(&doc, "", "  ")
	if err != nil {
		return doc, nil, fmt.Errorf("BuildDiscoveryDocument: marshal: %w", err)
	}
	return doc, out, nil
}
