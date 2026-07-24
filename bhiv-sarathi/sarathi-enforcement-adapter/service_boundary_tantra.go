package main

// service_boundary_tantra.go — v15.7 TANTRA Final Contract handler.
//
// REPLACES service_boundary_sovereign.go.
//
// HTTP handler for POST /sarathi/enforce. Accepts ONLY the new TANTRA
// payload shape (schema_version = "tantra.decision.v1"). Runs the 12-step
// verifier (tantra_verifier.go), translates to ExternalDecision, and
// delegates to handleIngestDecision so the existing PDP / propagation
// pipeline is unchanged.
//
// EVERY VALIDATION FAILURE RETURNS A STABLE ERR_TANTRA_* CODE in BOTH:
//   - The response body's `error_code` field
//   - The X-Sarathi-Error-Code response header
//
// HTTP status mapping mirrors the existing legacy handler's semantics:
//   - Decode + structural errors        -> 400
//   - Auth / signature errors           -> 401
//   - Evaluator / registry errors       -> 403
//   - Replay / mutation errors          -> 409
//   - Adapter / pipeline errors         -> 422
//   - Pipeline not initialised          -> 503
//
// TAG: tantra-v15.7

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"sync/atomic"
	"time"
)

// handleSarathiEnforceTantra is the v15.7 TANTRA-only handler mounted at
// POST /sarathi/enforce. Flow:
//
//   1. Method + Content-Type checks.
//   2. API key extraction (X-API-Key OR Authorization: Bearer).
//   3. Pipeline-readiness check.
//   4. Read raw body (cap enforced upstream by MaxBytesReader).
//   5. Run the 12-step TANTRA verifier — produces *TantraVerifierResult.
//   6. Translate TANTRA result -> ExternalDecision.
//   7. Re-marshal canonical ExternalDecision and proxy to handleIngestDecision.
//   8. Emit a Sarathi-side enforcement attestation alongside the response.
//
// On any verifier failure, returns the precise ERR_TANTRA_* code and status.
func (sb *ServiceBoundary) handleSarathiEnforceTantra(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	// 1. Method.
	if r.Method != http.MethodPost {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusMethodNotAllowed)
		_ = json.NewEncoder(w).Encode(&IngestDecisionError{
			ErrorCode: "METHOD_NOT_ALLOWED",
			Detail:    "Only POST is accepted at /sarathi/enforce",
		})
		return
	}

	// 2. Content-Type.
	ct := r.Header.Get("Content-Type")
	if ct != "application/json" && ct != "" {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusUnsupportedMediaType)
		_ = json.NewEncoder(w).Encode(&IngestDecisionError{
			ErrorCode: "UNSUPPORTED_CONTENT_TYPE",
			Detail:    "Content-Type must be application/json",
		})
		return
	}

	// 3. API key — v15.11 makes the fingerprint check load-bearing.
	// Caller supplies the raw API key in X-API-Key (or Authorization: Bearer).
	// Sarathi computes sha256(api_key) and compares it (constant time) to the
	// fingerprint stored on the evaluator's TANTRA registry row. The body's
	// evaluator_id is parsed AFTER the signature verifier; for the api-key
	// gate we use a defensive trick: we tolerate the field being unset and
	// rely on the TANTRA verifier (step 7) to authenticate via signature.
	// But if any TANTRA registry row carries an api_key_fingerprint, the
	// header MUST be present AND match.
	//
	// Cases:
	//   - header absent + no fingerprint on the registry row → accept (signature is auth)
	//   - header absent + fingerprint on the row              → ERR_TANTRA_API_KEY_REQUIRED
	//   - header present + matches fingerprint                → accept
	//   - header present + mismatches fingerprint             → ERR_TANTRA_API_KEY_INVALID
	//   - header present + no fingerprint on row              → accept (key ignored, no downgrade)
	apiKey := r.Header.Get("X-API-Key")
	if apiKey == "" {
		auth := r.Header.Get("Authorization")
		if len(auth) > 7 && auth[:7] == "Bearer " {
			apiKey = auth[7:]
		}
	}

	// 4. Pipeline readiness.
	if sb.pdpAdapter == nil {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusServiceUnavailable)
		_ = json.NewEncoder(w).Encode(&IngestDecisionError{
			ErrorCode: CodeIngestDecisionInvalid,
			Detail:    "PDPAdapter not wired (pipeline external mode not initialized)",
		})
		return
	}

	// 5. Read raw body.
	r.Body = http.MaxBytesReader(w, r.Body, sb.config.MaxRequestBodyBytes)
	rawBytes, readErr := io.ReadAll(r.Body)
	if readErr != nil || len(rawBytes) == 0 {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		detail := "empty body"
		if readErr != nil {
			detail = "read failed: " + readErr.Error()
		}
		sb.rejectTantra(w, http.StatusBadRequest, ErrTantraMissingField, detail)
		return
	}

	// 6. Run the 12-step verifier.
	if ActiveTantraTrust() == nil {
		sb.rejectTantra(w, http.StatusServiceUnavailable, ErrTantraEvaluatorNotRegistered,
			"TANTRA trust registry not initialised — confirm SARATHI_TRUST_SNAPSHOT carries tantra_evaluators")
		return
	}
	if activeTantraReplayStore == nil {
		sb.rejectTantra(w, http.StatusServiceUnavailable, ErrTantraReplay,
			"TANTRA replay store not initialised")
		return
	}

	verifier := NewTantraVerifier()
	result, verr := verifier.Verify(rawBytes)
	if verr != nil {
		if tve, ok := verr.(*TantraValidationError); ok {
			status := tantraStatusFor(tve.Code)
			sb.rejectTantra(w, status, tve.Code, tve.Detail)
			return
		}
		sb.rejectTantra(w, http.StatusBadRequest, ErrTantraSignatureInvalid, verr.Error())
		return
	}

	// 7. trace_id header sanity (defence-in-depth — the verifier already
	// accepted the body, but we re-check the header invariant the existing
	// pipeline expects).
	if hdr := strings.TrimSpace(r.Header.Get(HeaderTraceID)); hdr != "" && hdr != result.Decision.TraceID {
		sb.rejectTantra(w, http.StatusBadRequest, ErrTantraMissingField,
			fmt.Sprintf("body.trace_id (%s) != X-Sarathi-Trace-ID header (%s)",
				result.Decision.TraceID, hdr))
		return
	}

	// 7b. v15.11 — API-key fingerprint gate (now load-bearing).
	// If the evaluator's registry row carries an api_key_fingerprint, the
	// X-API-Key header MUST be present and sha256(api_key) MUST equal it.
	expectedFP := strings.TrimSpace(result.EvaluatorRow.APIKeyFingerprint)
	if expectedFP != "" {
		if apiKey == "" {
			sb.rejectTantra(w, http.StatusUnauthorized, ErrTantraAPIKeyRequired,
				fmt.Sprintf("evaluator %q requires X-API-Key (registry row carries api_key_fingerprint)",
					result.Decision.EvaluatorID))
			return
		}
		got := sha256Hex([]byte(apiKey))
		if !constantTimeHexEqual(got, expectedFP) {
			sb.rejectTantra(w, http.StatusUnauthorized, ErrTantraAPIKeyInvalid,
				fmt.Sprintf("X-API-Key fingerprint mismatch for evaluator %q",
					result.Decision.EvaluatorID))
			return
		}
	}

	// 8. Translate to canonical ExternalDecision.
	externalDec, terr := TranslateTantraToExternalDecision(result)
	if terr != nil {
		sb.rejectTantra(w, http.StatusUnprocessableEntity, ErrTantraSignatureInvalid,
			"translation: "+terr.Error())
		return
	}

	// 9. Re-marshal canonical bytes for the inner ingest handler.
	canonical, merr := json.Marshal(externalDec)
	if merr != nil {
		sb.rejectTantra(w, http.StatusInternalServerError, ErrTantraSignatureInvalid,
			"canonical marshal failed: "+merr.Error())
		return
	}

	// 10. Build synthetic inner request and proxy to handleIngestDecision.
	inner := r.Clone(r.Context())
	inner.Body = io.NopCloser(bytes.NewReader(canonical))
	inner.ContentLength = int64(len(canonical))
	inner.URL.Path = "/v1/ingest-decision"
	inner.Header.Set(HeaderTraceID, result.Decision.TraceID)
	inner.Header.Set("X-Sarathi-Schema-Version", TantraSchemaV1)
	inner.Header.Set("X-Sarathi-Mint-JWT", "1")
	inner.Header.Set("X-Sarathi-Internal-Source", "sarathi-enforce-tantra")
	inner.Header.Set("X-Sarathi-Tantra-Decision-Id", result.Decision.DecisionID)
	inner.Header.Set("X-Sarathi-Tantra-Decision-Hash", result.Decision.DecisionHash)
	inner.Header.Set("X-Sarathi-Tantra-Signature-Alg", result.Decision.Signature.Alg)

	// 11. Emit the Sarathi-side enforcement attestation (best-effort —
	// failure to attest does NOT block enforcement; the existing pipeline
	// is still authoritative).
	go emitEnforcementAttestationAsync(result, externalDec)

	sb.handleIngestDecision(w, inner)
}

// rejectTantra writes a single-shot error response with the X-Sarathi-Error-Code
// header populated.
func (sb *ServiceBoundary) rejectTantra(w http.ResponseWriter, status int, code, detail string) {
	atomic.AddUint64(&sb.totalHTTPErrors, 1)
	w.Header().Set("X-Sarathi-Error-Code", code)
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(&IngestDecisionError{ErrorCode: code, Detail: detail})
}

// tantraStatusFor maps a stable ERR_TANTRA_* code to an HTTP status.
func tantraStatusFor(code string) int {
	switch code {
	case ErrTantraSchemaVersionUnknown,
		ErrTantraMissingField,
		ErrTantraUnknownField,
		ErrTantraVerdictInvalid,
		ErrTantraEvaluatorIDFormat,
		ErrTantraEncodingUnsupported,
		ErrTantraCanonicalEncoding,
		ErrTantraBodyTooLarge,
		ErrTantraTimestampUnparseable:
		return http.StatusBadRequest
	case ErrTantraSignatureInvalid,
		ErrTantraSignatureDecode,
		ErrTantraTimestampSkewed,
		ErrTantraAPIKeyRequired,
		ErrTantraAPIKeyInvalid:
		return http.StatusUnauthorized
	case ErrTantraEvaluatorNotRegistered,
		ErrTantraEvaluatorNotActive,
		ErrTantraEvaluatorSchemaMismatch,
		ErrTantraKeyIDMismatch,
		ErrTantraAlgMismatch:
		return http.StatusForbidden
	case ErrTantraReplay,
		ErrTantraDecisionHashMismatch,
		ErrTantraDecisionIDMismatch:
		return http.StatusConflict
	default:
		return http.StatusBadRequest
	}
}

// emitEnforcementAttestationAsync runs in a goroutine because it touches
// disk and signs a fresh attestation — neither of which should block the
// HTTP response. Errors are logged but never surfaced to the caller.
func emitEnforcementAttestationAsync(result *TantraVerifierResult, externalDec *ExternalDecision) {
	defer func() {
		if rec := recover(); rec != nil {
			fmt.Fprintf(os.Stderr, "[tantra_emit] panic recovered: %v\n", rec)
		}
	}()
	if _, err := EmitSarathiEnforcementAttestation(result, externalDec, time.Now().UTC()); err != nil {
		fmt.Fprintf(os.Stderr, "[tantra_emit] WARN: %v\n", err)
	}
}
