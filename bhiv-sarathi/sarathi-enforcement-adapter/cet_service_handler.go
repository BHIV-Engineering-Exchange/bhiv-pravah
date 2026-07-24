package main

// cet_service_handler.go — Live HTTP surface for the CET->Sarathi convergence
// boundary.
//
//	POST /sarathi/cet/enforce
//
// Accepts the SUM-SCRIPT envelope (schema_version "1.0",
// contract_version "TANTRA-CONVERGENCE-v1"), runs the CET boundary verifier
// (cet_verifier.go), and:
//
//   - on ACCEPT: emits + persists the enforcement_decision artifact and the
//     PREPARED_NOT_TRANSMITTED Sarathi->Bridge handoff, then returns the
//     enforcement_decision artifact as the response body;
//   - on REJECT: emits + persists the trace-bound fail-closed rejection
//     artifact and returns it with the mapped HTTP status + X-Sarathi-Error-Code.
//
// This route is ADDITIVE. It does not touch /sarathi/enforce
// (tantra.decision.v1) or any existing peer surface. The inner decision is
// still verified by the same 12-step verifier the existing TANTRA path uses.
//
// TAG: tantra-convergence-v1

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

// CETEnforcePath is the live CET->Sarathi ingestion path.
const CETEnforcePath = "/sarathi/cet/enforce"

// EnvBridgeIngressURL optionally configures the Bridge ingress URL surfaced in
// the handoff artifact. Empty => PREPARED_NOT_TRANSMITTED with no target.
const EnvBridgeIngressURL = "SARATHI_BRIDGE_INGRESS_URL"

// handleSarathiCETEnforce is the live handler mounted at POST /sarathi/cet/enforce.
func (sb *ServiceBoundary) handleSarathiCETEnforce(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	now := time.Now().UTC()

	if r.Method != http.MethodPost {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
		w.WriteHeader(http.StatusMethodNotAllowed)
		_ = json.NewEncoder(w).Encode(&IngestDecisionError{
			ErrorCode: "METHOD_NOT_ALLOWED",
			Detail:    "Only POST is accepted at " + CETEnforcePath,
		})
		return
	}
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

	// Trust + replay must be wired, else the inner verifier cannot run.
	if ActiveTantraTrust() == nil || activeTantraReplayStore == nil {
		sb.rejectCET(w, http.StatusServiceUnavailable, &CETValidationError{
			Code:   ErrCETInnerDecisionInvalid,
			Detail: "TANTRA trust registry / replay store not initialised",
		}, now)
		return
	}

	r.Body = http.MaxBytesReader(w, r.Body, sb.config.MaxRequestBodyBytes)
	raw, readErr := io.ReadAll(r.Body)
	if readErr != nil || len(raw) == 0 {
		detail := "empty body"
		if readErr != nil {
			detail = "read failed: " + readErr.Error()
		}
		sb.rejectCET(w, http.StatusBadRequest, &CETValidationError{Code: ErrCETMissingField, Detail: detail}, now)
		return
	}

	res, verr := NewCETBoundary().Verify(raw)
	if verr != nil {
		sb.rejectCET(w, cetStatusFor(verr.Code, verr.InnerCode), verr, now)
		return
	}

	// Defence-in-depth: header trace_id (if supplied) must match the chain.
	if hdr := strings.TrimSpace(r.Header.Get(HeaderTraceID)); hdr != "" && hdr != res.SumScript.TraceID {
		sb.rejectCET(w, http.StatusBadRequest, &CETValidationError{
			Code:        ErrCETTraceIDDiscontinuity,
			Detail:      "X-Sarathi-Trace-ID header does not match SUM-SCRIPT trace_id",
			ExecutionID: res.SumScript.ExecutionID, TraceID: res.SumScript.TraceID, CETHash: res.SumScript.CETHash,
		}, now)
		return
	}

	// Real enforcement token reference (best-effort signed attestation; falls
	// back to the seal-bound reference if enforcement keys are not configured).
	enforcementRef := cetLiveEnforcementReference(res, now)

	// Emit + persist the enforcement_decision artifact.
	artifact := BuildEnforcementDecisionArtifact(res, enforcementRef, now)
	if _, err := PersistEnforcementDecisionArtifact(artifact); err != nil {
		atomic.AddUint64(&sb.totalHTTPErrors, 1)
	}

	// Mint capability JWT for the Bridge hop (best-effort).
	capJWT, capKID := cetMintCapabilityJWT(sb, res, now)

	// Build + persist the Sarathi->Bridge handoff.
	handoff := BuildBridgeHandoffArtifact(res, enforcementRef, capJWT, capKID,
		strings.TrimSpace(os.Getenv(EnvBridgeIngressURL)), now)
	_, _ = PersistBridgeHandoffArtifact(handoff)

	// Transmit to Bridge in background if ingress URL + capability are ready.
	if handoff.BridgeIngressURL != "" && capJWT != "" {
		go cetTransmitToBridge(handoff, capJWT)
	}

	// Echo the locked identity in headers.
	w.Header().Set("X-Sarathi-Execution-ID", res.SumScript.ExecutionID)
	w.Header().Set(HeaderTraceID, res.SumScript.TraceID)
	w.Header().Set("X-Sarathi-CET-Hash", res.SumScript.CETHash)
	w.Header().Set("X-Sarathi-SumScript-Seal", res.SealHash)
	w.Header().Set("X-Sarathi-Contract-Version", res.SumScript.ContractVersion)
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(artifact)
}

// rejectCET emits + persists a trace-bound rejection artifact and writes it as
// the HTTP response.
func (sb *ServiceBoundary) rejectCET(w http.ResponseWriter, status int, verr *CETValidationError, now time.Time) {
	atomic.AddUint64(&sb.totalHTTPErrors, 1)
	rej := BuildTraceBoundRejectionArtifact(verr, now)
	_, _ = PersistTraceBoundRejectionArtifact(rej)
	w.Header().Set("X-Sarathi-Error-Code", verr.Code)
	if verr.TraceID != "" {
		w.Header().Set(HeaderTraceID, verr.TraceID)
	}
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(rej)
}

// cetLiveEnforcementReference returns a real enforcement-token reference for
// the live path. Prefers the signed Sarathi enforcement attestation; falls
// back to a seal-bound reference when enforcement signing keys are not
// configured on this node.
func cetLiveEnforcementReference(res *CETVerifierResult, now time.Time) string {
	if strings.TrimSpace(os.Getenv(EnvSarathiEnforcementPrivPath)) != "" {
		if extDec, terr := TranslateTantraToExternalDecision(res.InnerResult); terr == nil {
			if attest, aerr := EmitSarathiEnforcementAttestation(res.InnerResult, extDec, now); aerr == nil && attest != nil {
				return "sarathi-enforcement:" + attest.DecisionID
			}
		}
	}
	return "sarathi-enforcement-seal:" + res.SealHash
}

// cetMintCapabilityJWT mints a capability JWT for the Sarathi->Bridge hop.
// Returns ("", "") when the JWT authority is not configured on this boundary.
func cetMintCapabilityJWT(sb *ServiceBoundary, res *CETVerifierResult, now time.Time) (token, kid string) {
	if sb.jwtAuthority == nil {
		return "", ""
	}
	s := res.SumScript
	decisionID := ""
	if res.InnerResult != nil && res.InnerResult.Decision != nil {
		decisionID = res.InnerResult.Decision.DecisionID
	}
	mj, err := sb.jwtAuthority.MintJWT(MintRequest{
		Subject:  decisionID,
		Audience: DefaultJWTAudience,
		IssuedAt: now,
		PrivateClaims: map[string]interface{}{
			"execution_id":     s.ExecutionID,
			"trace_id":         s.TraceID,
			"cet_hash":         s.CETHash,
			"bucket_key":       s.BucketKey,
			"decision_id":      decisionID,
			"verdict":          string(res.Decision),
			"contract_version": s.ContractVersion,
			"sumscript_seal":   res.SealHash,
			"boundary":         "Sarathi->Bridge",
		},
		CorrelationID: s.TraceID,
	})
	if err != nil || mj == nil {
		return "", ""
	}
	return mj.Token, mj.Kid
}

// cetTransmitToBridge POSTs the handoff to the Bridge ingress URL with the
// capability token as the Bearer credential. On a 2xx ACK the handoff is
// re-persisted with TRANSMITTED status. Runs in a background goroutine so it
// never delays the CET response.
func cetTransmitToBridge(handoff *CETBridgeHandoffArtifact, capabilityJWT string) {
	body, err := json.Marshal(handoff)
	if err != nil {
		return
	}
	req, err := http.NewRequest(http.MethodPost, handoff.BridgeIngressURL, bytes.NewReader(body))
	if err != nil {
		return
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+capabilityJWT)
	req.Header.Set("ngrok-skip-browser-warning", "true")
	req.Header.Set("X-Sarathi-Execution-ID", handoff.ExecutionID)
	req.Header.Set("X-Sarathi-Trace-ID", handoff.TraceID)
	req.Header.Set("X-Sarathi-CET-Hash", handoff.CETHash)
	req.Header.Set("X-Sarathi-Bucket-Key", handoff.BucketKey)
	req.Header.Set("X-Sarathi-SumScript-Seal", handoff.HashContinuity.SarathiSealHash)
	req.Header.Set("X-Sarathi-Schema-Version", handoff.SchemaVersion)
	req.Header.Set("X-Sarathi-Contract-Version", handoff.ContractVersion)

	resp, err := (&http.Client{Timeout: 30 * time.Second}).Do(req)
	if err != nil {
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		handoff.TransmissionStatus = HandoffTransmitted
		handoff.TransmissionNote = fmt.Sprintf("Transmitted to Bridge — HTTP %d ACK received at %s.",
			resp.StatusCode, handoff.BridgeIngressURL)
		_, _ = PersistBridgeHandoffArtifact(handoff)
	}
}

// cetStatusFor maps a CET error code to an HTTP status. Inner-decision failures
// reuse the TANTRA status mapping so the underlying cause is reflected.
func cetStatusFor(code, innerCode string) int {
	switch code {
	case ErrCETSchemaVersionUnknown,
		ErrCETContractVersionUnknown,
		ErrCETMissingField,
		ErrCETUnknownField,
		ErrCETBodyTooLarge,
		ErrCETHashMalformed,
		ErrCETBucketKeyMalformed,
		ErrCETDecisionDecode:
		return http.StatusBadRequest
	case ErrCETTraceIDDiscontinuity,
		ErrCETHashRecomputeMismatch:
		return http.StatusConflict
	case ErrCETInnerDecisionInvalid:
		if innerCode != "" {
			return tantraStatusFor(innerCode)
		}
		return http.StatusUnprocessableEntity
	default:
		return http.StatusBadRequest
	}
}
