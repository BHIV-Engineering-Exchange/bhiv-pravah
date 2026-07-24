package main

// ═══════════════════════════════════════════════════════════════════
// FROZEN — v12.1 GAP-01 RECTIFICATION
// ═══════════════════════════════════════════════════════════════════
// This file is FROZEN: the REST API for evaluator registration and
// lifecycle management is a trust-service concern. Exposing these
// endpoints from the default Sarathi binary is a BOUNDARY VIOLATION.
// Compiles but is NOT WIRED — ServiceBoundary.Listen() does not
// register these routes in the default build. See KB_06 GAP 1.
// ═══════════════════════════════════════════════════════════════════

// evaluator_registration_api.go — HTTP handlers for evaluator registration
// + lifecycle management.
//
// Author: Hemanth B (Phase 12 — External Evaluator Hardening)
// System: Sarathi Governance Kernel — Zero-Trust Verification Boundary
// Host Organization: Blackhole Infiverse (BHIV)
// Classification: Internal Sovereign Design / Strictly Confidential
//
// PURPOSE:
//   The v11 evaluator registry had no external interface — registration
//   required a Go recompile + redeploy. This file closes CRITICAL #C2 by
//   exposing a tightly-scoped admin API surface for evaluator onboarding
//   and lifecycle management.
//
// CONSTRAINTS (FROM TASK.MD):
//   - Sarathi remains a verification-only boundary. None of these handlers
//     touch PDP, KSML, or GovernanceKernel.
//   - All mutating endpoints require an Ed25519-signed AdminRequest envelope.
//   - The PoP challenge/complete dance is mandatory for runtime registration.
//   - The JWKS endpoint is the only public route — no admin auth required —
//     so downstream systems can fetch the current trust bundle.
//
// ENDPOINTS:
//   POST /v1/evaluators/register/challenge   (admin: REGISTER_INIT)
//   POST /v1/evaluators/register/complete    (admin: REGISTER_COMPLETE)
//   GET  /v1/evaluators                      (admin: LIST)
//   GET  /v1/evaluators/{id}                 (admin: GET)
//   POST /v1/evaluators/{id}/suspend         (admin: SUSPEND)
//   POST /v1/evaluators/{id}/reactivate      (admin: REACTIVATE)
//   POST /v1/evaluators/{id}/revoke          (admin: REVOKE)
//   POST /v1/evaluators/{id}/rotate          (admin: ROTATE_KEY)
//   GET  /v1/evaluators/.well-known/jwks     (PUBLIC, RFC 7517 trust bundle)
//
// DESIGN REFERENCES:
//   - ACME RFC 8555 (challenge/complete onboarding flow)
//   - OAuth2 Dynamic Client Registration RFC 7591 (machine onboarding API)
//   - JWKS RFC 7517 / RFC 7638 (public trust bundle discovery)
//   - SPIFFE Trust Bundle API (workload trust set publication)

import (
	"context"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// EvaluatorRegistrationAPI binds the HTTP handlers to a registry. It is
// only constructed when the registry has been wired with an admin
// authenticator (i.e., production registration is enabled). Without an
// authenticator the constructor refuses to build a non-nil instance —
// this prevents an unauthenticated admin surface from being exposed by
// accident.
type EvaluatorRegistrationAPI struct {
	registry        *EvaluatorTrustRegistry
	maxBodyBytes    int64
	defaultGracePeriod time.Duration
}

// NewEvaluatorRegistrationAPI builds the HTTP handler set. Returns nil if
// the registry has no admin authenticator wired (defence-in-depth).
func NewEvaluatorRegistrationAPI(registry *EvaluatorTrustRegistry) *EvaluatorRegistrationAPI {
	if registry == nil {
		return nil
	}
	registry.mu.RLock()
	hasAuth := registry.adminAuth != nil
	registry.mu.RUnlock()
	if !hasAuth {
		return nil
	}
	return &EvaluatorRegistrationAPI{
		registry:           registry,
		maxBodyBytes:       1 << 20, // 1MB
		defaultGracePeriod: 24 * time.Hour,
	}
}

// RegisterRoutes attaches all evaluator endpoints to the given mux.
// The path prefix is fixed at /v1/evaluators (matches existing /v1/enforce).
func (api *EvaluatorRegistrationAPI) RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/v1/evaluators/register/challenge", api.handleRegisterChallenge)
	mux.HandleFunc("/v1/evaluators/register/complete", api.handleRegisterComplete)
	mux.HandleFunc("/v1/evaluators/.well-known/jwks", api.handleJWKS)
	mux.HandleFunc("/v1/evaluators/", api.handleEvaluatorByID) // catch-all for /:id and /:id/<op>
	mux.HandleFunc("/v1/evaluators", api.handleListEvaluators)
}

// =============================================================================
// SHARED HELPERS
// =============================================================================

// readBody enforces Content-Type and body-size limits then returns the raw
// bytes (so they can be hashed for the admin auth body-hash binding before
// JSON decode).
func (api *EvaluatorRegistrationAPI) readBody(w http.ResponseWriter, r *http.Request) ([]byte, bool) {
	if r.Header.Get("Content-Type") != "application/json" && r.Method != http.MethodGet {
		writeJSONError(w, http.StatusUnsupportedMediaType, "UNSUPPORTED_CONTENT_TYPE",
			"Content-Type must be application/json")
		return nil, false
	}
	r.Body = http.MaxBytesReader(w, r.Body, api.maxBodyBytes)
	body, err := io.ReadAll(r.Body)
	if err != nil {
		writeJSONError(w, http.StatusRequestEntityTooLarge, "BODY_READ_FAILED", err.Error())
		return nil, false
	}
	return body, true
}

// extractAdminRequest decodes the admin envelope from a request body. The
// envelope is expected as a top-level "admin" field; the actual payload
// lives under "payload". Splitting body and envelope keeps the body hash
// binding meaningful — the payload is what gets hashed.
type adminEnvelopedRequest struct {
	Admin   *AdminRequest   `json:"admin"`
	Payload json.RawMessage `json:"payload"`
}

func parseAdminEnvelope(body []byte) (*AdminRequest, []byte, error) {
	var env adminEnvelopedRequest
	if err := json.Unmarshal(body, &env); err != nil {
		return nil, nil, fmt.Errorf("ADMIN_ENVELOPE_DECODE: %w", err)
	}
	if env.Admin == nil {
		return nil, nil, fmt.Errorf("ADMIN_ENVELOPE_MISSING_ADMIN")
	}
	return env.Admin, []byte(env.Payload), nil
}

// writeJSONError emits a structured error response.
func writeJSONError(w http.ResponseWriter, status int, code, detail string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{
		"error":  code,
		"detail": detail,
	})
}

// writeJSONOK emits a 200/201 response with the registry version header.
func (api *EvaluatorRegistrationAPI) writeJSONOK(w http.ResponseWriter, status int, body interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Sarathi-Registry-Version", fmt.Sprintf("%d", api.registry.Version()))
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}

// statusFromAdminErr maps admin auth errors to HTTP status codes.
func statusFromAdminErr(err error) int {
	if ae, ok := err.(*AdminAuthError); ok {
		switch ae.Code {
		case AdminErrRateLimited:
			return http.StatusTooManyRequests
		case AdminErrTimestampSkew, AdminErrNonceReplay:
			return http.StatusUnauthorized
		case AdminErrUnknownAdmin, AdminErrSigInvalid, AdminErrSigEmpty:
			return http.StatusUnauthorized
		case AdminErrOpMismatch, AdminErrTargetMismatch, AdminErrBodyHashMismatch:
			return http.StatusForbidden
		}
	}
	return http.StatusUnauthorized
}

// =============================================================================
// REGISTRATION (PoP)
// =============================================================================

// challengeRequest is the inner payload of the challenge call.
type challengeRequest struct {
	EvaluatorID  string            `json:"evaluator_id"`
	Name         string            `json:"name"`
	PublicKeyHex string            `json:"public_key_hex"`
	Metadata     map[string]string `json:"metadata,omitempty"`
	ExpiresAt    *time.Time        `json:"expires_at,omitempty"`
}

func (api *EvaluatorRegistrationAPI) handleRegisterChallenge(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeJSONError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "POST only")
		return
	}
	body, ok := api.readBody(w, r)
	if !ok {
		return
	}
	adminReq, payload, err := parseAdminEnvelope(body)
	if err != nil {
		writeJSONError(w, http.StatusBadRequest, "INVALID_ENVELOPE", err.Error())
		return
	}
	var inner challengeRequest
	if err := json.Unmarshal(payload, &inner); err != nil {
		writeJSONError(w, http.StatusBadRequest, "INVALID_PAYLOAD", err.Error())
		return
	}
	if err := api.registry.requireAdmin(adminReq, AdminOpRegisterInit, inner.EvaluatorID, payload); err != nil {
		writeJSONError(w, statusFromAdminErr(err), "ADMIN_AUTH_REJECTED", err.Error())
		return
	}
	store := api.registry.EnsureChallengeStore()
	challenge, err := store.Issue(inner.EvaluatorID, inner.Name, inner.PublicKeyHex, inner.Metadata, inner.ExpiresAt)
	if err != nil {
		writeJSONError(w, http.StatusBadRequest, "CHALLENGE_REJECTED", err.Error())
		return
	}
	api.writeJSONOK(w, http.StatusOK, map[string]interface{}{
		"challenge_id": challenge.ChallengeID,
		"nonce":        challenge.Nonce,
		"message":      challenge.Message,
		"expires_at":   challenge.ChallengeTTL,
	})
}

type completeRequest struct {
	ChallengeID string `json:"challenge_id"`
	Signature   string `json:"signature"` // hex-encoded Ed25519 signature
}

func (api *EvaluatorRegistrationAPI) handleRegisterComplete(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeJSONError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "POST only")
		return
	}
	body, ok := api.readBody(w, r)
	if !ok {
		return
	}
	adminReq, payload, err := parseAdminEnvelope(body)
	if err != nil {
		writeJSONError(w, http.StatusBadRequest, "INVALID_ENVELOPE", err.Error())
		return
	}
	var inner completeRequest
	if err := json.Unmarshal(payload, &inner); err != nil {
		writeJSONError(w, http.StatusBadRequest, "INVALID_PAYLOAD", err.Error())
		return
	}
	// We don't know the evaluator_id until we consume the challenge — so we
	// auth against the challenge_id as the target. The challenge embeds the
	// evaluator_id internally.
	if err := api.registry.requireAdmin(adminReq, AdminOpRegisterComplete, inner.ChallengeID, payload); err != nil {
		writeJSONError(w, statusFromAdminErr(err), "ADMIN_AUTH_REJECTED", err.Error())
		return
	}
	sig, err := hex.DecodeString(inner.Signature)
	if err != nil {
		writeJSONError(w, http.StatusBadRequest, "INVALID_SIGNATURE_HEX", err.Error())
		return
	}
	rec, err := api.registry.RegisterEvaluatorWithPoP(
		context.Background(), inner.ChallengeID, sig, "admin:"+adminReq.AdminID,
	)
	if err != nil {
		// Map well-known error prefixes to status codes for operator clarity.
		msg := err.Error()
		switch {
		case strings.HasPrefix(msg, "POP_FAILED"):
			writeJSONError(w, http.StatusForbidden, "POP_FAILED", msg)
		case strings.HasPrefix(msg, "CHALLENGE_EXPIRED"):
			writeJSONError(w, http.StatusGone, "CHALLENGE_EXPIRED", msg)
		case strings.HasPrefix(msg, "CHALLENGE_ALREADY_CONSUMED"):
			writeJSONError(w, http.StatusConflict, "CHALLENGE_ALREADY_CONSUMED", msg)
		case strings.HasPrefix(msg, "EVALUATOR_ALREADY_EXISTS"):
			writeJSONError(w, http.StatusConflict, "EVALUATOR_ALREADY_EXISTS", msg)
		default:
			writeJSONError(w, http.StatusBadRequest, "REGISTER_FAILED", msg)
		}
		return
	}
	api.writeJSONOK(w, http.StatusCreated, map[string]interface{}{
		"evaluator_id":    rec.EvaluatorID,
		"status":          string(rec.Status),
		"key_fingerprint": rec.KeyFingerprint,
		"registered_at":   rec.RegisteredAt,
		"expires_at":      rec.ExpiresAt,
	})
}

// =============================================================================
// LIST + GET
// =============================================================================

func (api *EvaluatorRegistrationAPI) handleListEvaluators(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSONError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "GET only")
		return
	}
	// Admin auth on read paths so trust set is not publicly enumerable.
	// (JWKS is the only public surface.)
	adminEnvHdr := r.Header.Get("X-Admin-Request")
	if adminEnvHdr == "" {
		writeJSONError(w, http.StatusUnauthorized, "ADMIN_HEADER_MISSING",
			"X-Admin-Request header required (base64-decoded JSON envelope)")
		return
	}
	adminReq, err := UnmarshalAdminRequest([]byte(adminEnvHdr))
	if err != nil {
		writeJSONError(w, http.StatusUnauthorized, "ADMIN_HEADER_DECODE", err.Error())
		return
	}
	if err := api.registry.requireAdmin(adminReq, AdminOpList, "", nil); err != nil {
		writeJSONError(w, statusFromAdminErr(err), "ADMIN_AUTH_REJECTED", err.Error())
		return
	}
	api.writeJSONOK(w, http.StatusOK, map[string]interface{}{
		"registry_version": api.registry.Version(),
		"evaluators":       api.registry.ListEvaluators(),
	})
}

// =============================================================================
// LIFECYCLE: SUSPEND / REACTIVATE / REVOKE / ROTATE / GET
// =============================================================================

// handleEvaluatorByID multiplexes /v1/evaluators/{id}, /v1/evaluators/{id}/suspend, etc.
func (api *EvaluatorRegistrationAPI) handleEvaluatorByID(w http.ResponseWriter, r *http.Request) {
	// Strip prefix "/v1/evaluators/"
	path := strings.TrimPrefix(r.URL.Path, "/v1/evaluators/")
	if path == "" {
		writeJSONError(w, http.StatusNotFound, "NOT_FOUND", "missing evaluator id")
		return
	}
	parts := strings.SplitN(path, "/", 2)
	evaluatorID := parts[0]
	op := ""
	if len(parts) == 2 {
		op = parts[1]
	}
	switch op {
	case "":
		api.handleGetEvaluator(w, r, evaluatorID)
	case "suspend":
		api.handleLifecycleOp(w, r, evaluatorID, AdminOpSuspend)
	case "reactivate":
		api.handleLifecycleOp(w, r, evaluatorID, AdminOpReactivate)
	case "revoke":
		api.handleLifecycleOp(w, r, evaluatorID, AdminOpRevoke)
	case "rotate":
		api.handleRotate(w, r, evaluatorID)
	default:
		writeJSONError(w, http.StatusNotFound, "UNKNOWN_OP", "op="+op)
	}
}

func (api *EvaluatorRegistrationAPI) handleGetEvaluator(w http.ResponseWriter, r *http.Request, evaluatorID string) {
	if r.Method != http.MethodGet {
		writeJSONError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "GET only")
		return
	}
	adminEnvHdr := r.Header.Get("X-Admin-Request")
	if adminEnvHdr == "" {
		writeJSONError(w, http.StatusUnauthorized, "ADMIN_HEADER_MISSING",
			"X-Admin-Request header required")
		return
	}
	adminReq, err := UnmarshalAdminRequest([]byte(adminEnvHdr))
	if err != nil {
		writeJSONError(w, http.StatusUnauthorized, "ADMIN_HEADER_DECODE", err.Error())
		return
	}
	if err := api.registry.requireAdmin(adminReq, AdminOpGet, evaluatorID, nil); err != nil {
		writeJSONError(w, statusFromAdminErr(err), "ADMIN_AUTH_REJECTED", err.Error())
		return
	}
	rec, found := api.registry.GetEvaluator(evaluatorID)
	if !found {
		writeJSONError(w, http.StatusNotFound, "EVALUATOR_NOT_FOUND", evaluatorID)
		return
	}
	api.writeJSONOK(w, http.StatusOK, map[string]interface{}{
		"evaluator_id":    rec.EvaluatorID,
		"name":            rec.Name,
		"status":          string(rec.Status),
		"key_fingerprint": rec.KeyFingerprint,
		"public_key_hex":  rec.PublicKeyHex,
		"registered_at":   rec.RegisteredAt,
		"last_active_at":  rec.LastActiveAt,
		"expires_at":      rec.ExpiresAt,
		"previous_keys":   len(rec.PreviousKeys),
	})
}

// lifecycleRequest is the inner payload of suspend/reactivate/revoke.
type lifecycleRequest struct {
	Reason string `json:"reason"`
}

func (api *EvaluatorRegistrationAPI) handleLifecycleOp(
	w http.ResponseWriter, r *http.Request, evaluatorID string, op AdminOperation,
) {
	if r.Method != http.MethodPost {
		writeJSONError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "POST only")
		return
	}
	body, ok := api.readBody(w, r)
	if !ok {
		return
	}
	adminReq, payload, err := parseAdminEnvelope(body)
	if err != nil {
		writeJSONError(w, http.StatusBadRequest, "INVALID_ENVELOPE", err.Error())
		return
	}
	var inner lifecycleRequest
	if err := json.Unmarshal(payload, &inner); err != nil {
		writeJSONError(w, http.StatusBadRequest, "INVALID_PAYLOAD", err.Error())
		return
	}
	ctx := context.Background()
	switch op {
	case AdminOpSuspend:
		err = api.registry.SuspendEvaluatorAuthed(ctx, adminReq, payload, evaluatorID, inner.Reason)
	case AdminOpReactivate:
		err = api.registry.ReactivateEvaluatorAuthed(ctx, adminReq, payload, evaluatorID, inner.Reason)
	case AdminOpRevoke:
		err = api.registry.RevokeEvaluatorAuthed(ctx, adminReq, payload, evaluatorID, inner.Reason)
	default:
		writeJSONError(w, http.StatusInternalServerError, "INVALID_OP", "")
		return
	}
	if err != nil {
		if _, isAuth := err.(*AdminAuthError); isAuth {
			writeJSONError(w, statusFromAdminErr(err), "ADMIN_AUTH_REJECTED", err.Error())
			return
		}
		writeJSONError(w, http.StatusBadRequest, string(op)+"_FAILED", err.Error())
		return
	}
	api.writeJSONOK(w, http.StatusOK, map[string]interface{}{
		"evaluator_id": evaluatorID,
		"operation":    string(op),
		"applied":      true,
	})
}

type rotateRequest struct {
	NewPublicKeyHex string `json:"new_public_key_hex"`
	PoPMessage      string `json:"pop_message"`     // hex
	PoPSignature    string `json:"pop_signature"`   // hex
	GraceHours      int    `json:"grace_hours"`
}

func (api *EvaluatorRegistrationAPI) handleRotate(
	w http.ResponseWriter, r *http.Request, evaluatorID string,
) {
	if r.Method != http.MethodPost {
		writeJSONError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "POST only")
		return
	}
	body, ok := api.readBody(w, r)
	if !ok {
		return
	}
	adminReq, payload, err := parseAdminEnvelope(body)
	if err != nil {
		writeJSONError(w, http.StatusBadRequest, "INVALID_ENVELOPE", err.Error())
		return
	}
	var inner rotateRequest
	if err := json.Unmarshal(payload, &inner); err != nil {
		writeJSONError(w, http.StatusBadRequest, "INVALID_PAYLOAD", err.Error())
		return
	}
	newKey, err := hex.DecodeString(inner.NewPublicKeyHex)
	if err != nil {
		writeJSONError(w, http.StatusBadRequest, "INVALID_KEY_HEX", err.Error())
		return
	}
	popMsg, err := hex.DecodeString(inner.PoPMessage)
	if err != nil {
		writeJSONError(w, http.StatusBadRequest, "INVALID_POP_MESSAGE_HEX", err.Error())
		return
	}
	popSig, err := hex.DecodeString(inner.PoPSignature)
	if err != nil {
		writeJSONError(w, http.StatusBadRequest, "INVALID_POP_SIGNATURE_HEX", err.Error())
		return
	}
	grace := api.defaultGracePeriod
	if inner.GraceHours > 0 {
		grace = time.Duration(inner.GraceHours) * time.Hour
	}
	err = api.registry.RotateKeyAuthed(
		context.Background(), adminReq, payload, evaluatorID, newKey, popMsg, popSig, grace,
	)
	if err != nil {
		if _, isAuth := err.(*AdminAuthError); isAuth {
			writeJSONError(w, statusFromAdminErr(err), "ADMIN_AUTH_REJECTED", err.Error())
			return
		}
		if strings.HasPrefix(err.Error(), "POP_FAILED") {
			writeJSONError(w, http.StatusForbidden, "POP_FAILED", err.Error())
			return
		}
		writeJSONError(w, http.StatusBadRequest, "ROTATE_FAILED", err.Error())
		return
	}
	api.writeJSONOK(w, http.StatusOK, map[string]interface{}{
		"evaluator_id": evaluatorID,
		"operation":    string(AdminOpRotateKey),
		"grace_period": grace.String(),
		"applied":      true,
	})
}

// =============================================================================
// PUBLIC JWKS (no admin auth — RFC 7517)
// =============================================================================

func (api *EvaluatorRegistrationAPI) handleJWKS(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSONError(w, http.StatusMethodNotAllowed, "METHOD_NOT_ALLOWED", "GET only")
		return
	}
	doc, err := api.registry.TrustBundleJWKS()
	if err != nil {
		writeJSONError(w, http.StatusInternalServerError, "JWKS_GENERATE_FAILED", err.Error())
		return
	}
	w.Header().Set("Content-Type", "application/jwk-set+json")
	w.Header().Set("X-Sarathi-Registry-Version", fmt.Sprintf("%d", api.registry.Version()))
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(doc)
}
