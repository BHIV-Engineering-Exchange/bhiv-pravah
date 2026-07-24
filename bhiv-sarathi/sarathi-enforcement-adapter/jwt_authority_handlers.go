package main

// jwt_authority_handlers.go — v15.6 HTTP handlers for the outbound JWT
// authority.
//
// Three routes are registered (when an authority is bound to the boundary):
//
//   GET  /sarathi/.well-known/jwks.json         — RFC 7517 JWKS (public read)
//   GET  /sarathi/.well-known/sarathi-authority — OIDC-style discovery doc
//   POST /sarathi/v1/token/introspect           — RFC 7662 introspection
//
// All three are GET-or-POST-only; other methods return 405. JWKS and discovery
// are cacheable + ETagged. Introspection is fail-closed: when no API key is
// configured (SARATHI_JWT_INTROSPECTION_API_KEY empty) it returns 503; with a
// key set, every request MUST present a matching Bearer token (constant-time
// compared).
//
// IMPORTANT: these handlers MUST NOT interact with the existing inbound
// signature middleware (service_inbound_auth.go) — the middleware bypasses
// non-POST and not-in-ProtectedPaths requests automatically. The introspect
// endpoint, although POST, is intentionally NOT in the ProtectedPaths default
// because it has its own auth model (bearer key, not evaluator signature).
//
// TAG: jwt-authority-v15.6

import (
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"sync/atomic"
	"time"
)

// RegisterJWTAuthorityRoutes attaches the three v15.6 routes to mux. Always
// safe to call, including before SetJWTAuthority is invoked — the handlers
// themselves check `sb.jwtAuthority == nil` at request time and respond 503.
// This decoupling lets NewServiceBoundary register routes unconditionally
// while letting service_runtime_cli.go bind the actual authority later.
func RegisterJWTAuthorityRoutes(mux *http.ServeMux, sb *ServiceBoundary) {
	if sb == nil || mux == nil {
		return
	}
	mux.HandleFunc(JWKSPath, sb.handleAuthorityJWKS)
	mux.HandleFunc(AuthorityDiscoveryPath, sb.handleAuthorityDiscovery)
	mux.HandleFunc(TokenIntrospectPath, sb.handleTokenIntrospect)
}

// ============================================================================
// JWKS
// ============================================================================

// handleAuthorityJWKS serves the RFC 7517 JWKS document. Public read; no
// auth. Honours conditional GET via If-None-Match (saves cache refreshes for
// Bridge between rotations).
func (sb *ServiceBoundary) handleAuthorityJWKS(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusMethodNotAllowed)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error":  "METHOD_NOT_ALLOWED",
			"detail": "Only GET is accepted at " + JWKSPath,
		})
		return
	}
	if sb.jwtAuthority == nil {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusServiceUnavailable)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error":  "JWT_AUTHORITY_NOT_BOUND",
			"detail": "operator has not bootstrapped a JWT authority key",
		})
		return
	}
	_, canonical, etag, err := sb.jwtAuthority.BuildJWKSDocument()
	if err != nil {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusInternalServerError)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error":  "JWKS_BUILD_FAILED",
			"detail": err.Error(),
		})
		return
	}
	if match := r.Header.Get("If-None-Match"); match != "" && match == etag {
		w.WriteHeader(http.StatusNotModified)
		return
	}
	w.Header().Set("Content-Type", AuthorityJWKSContentType)
	w.Header().Set("Cache-Control", fmt.Sprintf("public, max-age=%d", AuthorityJWKSCacheMaxAgeSeconds))
	w.Header().Set("ETag", etag)
	w.Header().Set("X-Sarathi-Schema-Version", sb.jwtAuthority.SchemaVersion())
	w.Header().Set("X-Sarathi-Registry-Version", fmt.Sprintf("%d", sb.jwtAuthority.RegistryVersion()))
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(canonical)
}

// ============================================================================
// DISCOVERY
// ============================================================================

// handleAuthorityDiscovery serves the OIDC-style discovery doc (RFC 8414
// adapted). The baseURL is derived from the request's Host + scheme when
// available, falling back to relative paths for dev.
func (sb *ServiceBoundary) handleAuthorityDiscovery(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusMethodNotAllowed)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error":  "METHOD_NOT_ALLOWED",
			"detail": "Only GET is accepted at " + AuthorityDiscoveryPath,
		})
		return
	}
	if sb.jwtAuthority == nil {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusServiceUnavailable)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error":  "JWT_AUTHORITY_NOT_BOUND",
			"detail": "operator has not bootstrapped a JWT authority key",
		})
		return
	}
	baseURL := deriveExternalBaseURL(r)
	_, body, err := sb.jwtAuthority.BuildDiscoveryDocument(baseURL)
	if err != nil {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusInternalServerError)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error":  "DISCOVERY_BUILD_FAILED",
			"detail": err.Error(),
		})
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "public, max-age=300")
	w.Header().Set("X-Sarathi-Schema-Version", AuthorityDiscoverySchema)
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(body)
}

// deriveExternalBaseURL builds the externally-visible base URL from a request,
// honouring an explicit SARATHI_EXTERNAL_BASE_URL env override when set.
func deriveExternalBaseURL(r *http.Request) string {
	if v := strings.TrimSpace(envDefault("SARATHI_EXTERNAL_BASE_URL", "")); v != "" {
		return strings.TrimRight(v, "/")
	}
	if r == nil || r.Host == "" {
		return ""
	}
	scheme := "http"
	if r.TLS != nil {
		scheme = "https"
	}
	// Honour X-Forwarded-Proto when running behind a TLS-terminating proxy.
	if fp := r.Header.Get("X-Forwarded-Proto"); fp != "" {
		scheme = fp
	}
	return fmt.Sprintf("%s://%s", scheme, r.Host)
}

// ============================================================================
// INTROSPECTION (RFC 7662)
// ============================================================================

// IntrospectionResponse mirrors RFC 7662 §2.2. The "active" boolean is the
// only required field; everything else is omitempty so a failed-token
// response reads exactly `{"active":false}`.
type IntrospectionResponse struct {
	Active              bool     `json:"active"`
	Issuer              string   `json:"iss,omitempty"`
	Subject             string   `json:"sub,omitempty"`
	Audience            string   `json:"aud,omitempty"`
	ExpiresAt           int64    `json:"exp,omitempty"`
	NotBefore           int64    `json:"nbf,omitempty"`
	IssuedAt            int64    `json:"iat,omitempty"`
	JTI                 string   `json:"jti,omitempty"`
	TokenType           string   `json:"token_type,omitempty"`
	TokenHash           string   `json:"sarathi:token_hash,omitempty"`
	Consumed            bool     `json:"sarathi:consumed,omitempty"`
	RegistryVersion     int64    `json:"sarathi:registry_version,omitempty"`
	Verdict             string   `json:"sarathi:verdict,omitempty"`
	Source              string   `json:"sarathi:source,omitempty"`
}

// handleTokenIntrospect implements POST /sarathi/v1/token/introspect. Per
// RFC 7662 the request body is application/x-www-form-urlencoded with at
// least a `token` field. We additionally accept application/json bodies for
// operator convenience (curl with --data-urlencode is cleaner than building a
// form). Either way the response is JSON.
func (sb *ServiceBoundary) handleTokenIntrospect(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if r.Method != http.MethodPost {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusMethodNotAllowed)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error":  "METHOD_NOT_ALLOWED",
			"detail": "Only POST is accepted at " + TokenIntrospectPath,
		})
		return
	}
	if sb.jwtAuthority == nil {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusServiceUnavailable)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error":  "JWT_AUTHORITY_NOT_BOUND",
			"detail": "operator has not bootstrapped a JWT authority key",
		})
		return
	}
	if !sb.jwtAuthority.IntrospectionEnabled() {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusServiceUnavailable)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error":  "INTROSPECTION_DISABLED",
			"detail": "set SARATHI_JWT_INTROSPECTION_API_KEY to enable",
		})
		return
	}

	// Auth: bearer token MUST be present and match (constant-time).
	auth := r.Header.Get("Authorization")
	const bearer = "Bearer "
	if !strings.HasPrefix(auth, bearer) {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusUnauthorized)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error":  "MISSING_BEARER",
			"detail": "Authorization: Bearer <key> required",
		})
		return
	}
	got := strings.TrimSpace(auth[len(bearer):])
	want := sb.jwtAuthority.IntrospectionAPIKey()
	if subtle.ConstantTimeCompare([]byte(got), []byte(want)) != 1 {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusUnauthorized)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error": "INVALID_BEARER",
		})
		return
	}

	// Read body (1 MiB cap to mirror the rest of the boundary).
	r.Body = http.MaxBytesReader(w, r.Body, sb.config.MaxRequestBodyBytes)
	raw, err := io.ReadAll(r.Body)
	if err != nil {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusBadRequest)
		_ = json.NewEncoder(w).Encode(map[string]string{
			"error":  "BODY_READ_FAILED",
			"detail": err.Error(),
		})
		return
	}
	token := extractIntrospectToken(r.Header.Get("Content-Type"), raw, r.URL.RawQuery)
	if token == "" {
		// RFC 7662 §2.2 — no token field => active=false (no body explanation).
		w.WriteHeader(http.StatusOK)
		_ = json.NewEncoder(w).Encode(IntrospectionResponse{Active: false})
		return
	}

	// Pull the consumption registry from the bound pipeline.
	var registry *TokenRegistry
	if pl := sb.bridge.getService().GetPipeline(); pl != nil && pl.Engine != nil {
		registry = pl.Engine.tokenRegistry
	}

	verified, code, _ := sb.jwtAuthority.VerifyJWT(token, VerifyOption{
		AllowExpired:               true,
		ConsultConsumptionRegistry: registry != nil,
		TokenRegistry:              registry,
	})
	// Map results to an IntrospectionResponse. active=true ONLY when the
	// verifier returned OK AND the token has not expired AND it has not
	// been consumed.
	resp := IntrospectionResponse{Active: false, TokenType: "Bearer"}
	if verified != nil {
		resp.Issuer = verified.Issuer
		resp.Subject = verified.Subject
		resp.Audience = verified.Audience
		resp.JTI = verified.JTI
		resp.ExpiresAt = verified.ExpiresAt.Unix()
		resp.NotBefore = verified.NotBefore.Unix()
		resp.IssuedAt = verified.IssuedAt.Unix()
		resp.TokenHash = verified.TokenHash
		resp.Consumed = verified.Consumed
		resp.Verdict = verified.Verdict
		resp.Source = verified.Source
	}
	now := time.Now().UTC()
	switch code {
	case JWTVerifyOK:
		if verified != nil && verified.ExpiresAt.After(now) && !verified.Consumed {
			resp.Active = true
		}
	case JWTVerifyExpired, JWTVerifyConsumedReplay:
		resp.Active = false
	default:
		// On any other failure we deliberately drop the populated fields so the
		// response is opaque (RFC 7662 §4 — privacy/security considerations).
		resp = IntrospectionResponse{Active: false}
	}
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(resp)
}

// extractIntrospectToken reads the "token" parameter from a body whose
// content type is form-urlencoded OR application/json, OR from the URL
// query string when the operator prefers that style.
func extractIntrospectToken(contentType string, body []byte, rawQuery string) string {
	ct := strings.ToLower(strings.TrimSpace(contentType))
	if strings.HasPrefix(ct, "application/x-www-form-urlencoded") {
		return parseFormTokenField(string(body))
	}
	if strings.HasPrefix(ct, "application/json") {
		var obj map[string]string
		if err := json.Unmarshal(body, &obj); err == nil {
			if t, ok := obj["token"]; ok {
				return strings.TrimSpace(t)
			}
		}
	}
	// Query-string fallback.
	if rawQuery != "" {
		return parseFormTokenField(rawQuery)
	}
	return ""
}

// parseFormTokenField returns the `token` value from a form-style payload
// without pulling in net/url (avoids the encoding subtleties we don't care
// about here — tokens never contain `&` or `=` characters in compact JWT).
func parseFormTokenField(s string) string {
	for _, pair := range strings.Split(s, "&") {
		kv := strings.SplitN(pair, "=", 2)
		if len(kv) != 2 {
			continue
		}
		if strings.EqualFold(kv[0], "token") {
			return strings.TrimSpace(kv[1])
		}
	}
	return ""
}
