package main

// cet_verifier.go — The CET->Sarathi convergence-boundary verifier.
//
// This is the enforcement-boundary gate the TANTRA convergence chain requires.
// It runs ON TOP OF the existing 12-step tantra.decision.v1 verifier: the
// inner decision is verified cryptographically by TantraVerifier (real
// signature, real registry lookup, real replay window), and this file adds the
// convergence-envelope continuity gates the locked chain mandates.
//
// GATE SEQUENCE (every gate is fail-closed; there is no partial-success path):
//
//	C0  Strict decode of the SUM-SCRIPT (DisallowUnknownFields + size cap).
//	C1  schema_version == "1.0".
//	C2  contract_version == "TANTRA-CONVERGENCE-v1".
//	C3  execution_id, trace_id, cet_hash, bucket_key present.
//	C4  cet_hash is 64 lowercase hex (structural).
//	C5  bucket_key is 64 lowercase hex (structural).
//	C6  Decode the inner tantra.decision.v1 bytes (decision_b64).
//	C7  Run the 12-step TANTRA verifier over the inner bytes (REAL crypto).
//	C8  trace_id continuity: inner decision trace_id == envelope trace_id.
//	C9  cet_hash recompute (ONLY when CET supplied cet_material_b64):
//	    sha256(material) MUST equal cet_hash, else hard reject.
//	C10 Seal the envelope (mutation-detection anchor) and build the
//	    contract-continuity proof.
//
// On any failure the verifier returns a *CETValidationError carrying the
// trace-bound identity (execution_id / trace_id / cet_hash when already
// parsed) so the caller can emit the spec-mandated trace-bound rejection
// artifact (canonical_chain_identity.md §Rejection Visibility Requirement).
//
// TAG: tantra-convergence-v1

import (
	"fmt"
	"strings"
	"time"
)

// CET boundary stable error codes (mirrors the ERR_TANTRA_* convention).
const (
	ErrCETSchemaVersionUnknown   = "ERR_CET_SCHEMA_VERSION_UNKNOWN"
	ErrCETContractVersionUnknown = "ERR_CET_CONTRACT_VERSION_UNKNOWN"
	ErrCETMissingField           = "ERR_CET_MISSING_FIELD"
	ErrCETUnknownField           = "ERR_CET_UNKNOWN_FIELD"
	ErrCETBodyTooLarge           = "ERR_CET_BODY_TOO_LARGE"
	ErrCETHashMalformed          = "ERR_CET_HASH_MALFORMED"
	ErrCETBucketKeyMalformed     = "ERR_CET_BUCKET_KEY_MALFORMED"
	ErrCETDecisionDecode         = "ERR_CET_DECISION_DECODE"
	ErrCETTraceIDDiscontinuity   = "ERR_CET_TRACE_ID_DISCONTINUITY"
	ErrCETHashRecomputeMismatch  = "ERR_CET_HASH_RECOMPUTE_MISMATCH"
	ErrCETInnerDecisionInvalid   = "ERR_CET_INNER_DECISION_INVALID"
)

// CETDecision is the explicit enforcement outcome at the CET->Sarathi boundary.
type CETDecision string

const (
	// CETDecisionAllow — the inner decision verified and the verdict authorises
	// execution.
	CETDecisionAllow CETDecision = "allow"
	// CETDecisionReject — fail-closed; the chain does not proceed to Bridge.
	CETDecisionReject CETDecision = "reject"
)

// CETContractContinuity is the exact contract_continuity proof block the TANTRA
// enforcement_decision artifact requires.
type CETContractContinuity struct {
	SumScriptReceived bool `json:"sum_script_received"`
	CETHashVerified   bool `json:"cet_hash_verified"`
	TraceIDPreserved  bool `json:"trace_id_preserved"`
	MutationDetected  bool `json:"mutation_detected"`
}

// CETVerifierResult is the outcome of a successful boundary verification.
type CETVerifierResult struct {
	SumScript   *CETSumScript
	InnerResult *TantraVerifierResult
	// SealHash is Sarathi's own seal over the received SUM-SCRIPT bytes.
	SealHash string
	// CETHashRecomputed reports whether the optional independent recompute gate
	// (C9) actually ran (i.e. CET supplied cet_material_b64).
	CETHashRecomputed bool
	// Decision is the explicit enforcement decision at this boundary.
	Decision CETDecision
	// Continuity is the contract_continuity proof.
	Continuity CETContractContinuity
	// VerifiedAt is the boundary verification time (UTC).
	VerifiedAt time.Time
}

// CETValidationError is a trace-bound, fail-closed rejection. It carries
// whatever identity has been parsed at the point of failure so the rejection
// artifact can echo the locked identifiers.
type CETValidationError struct {
	Code        string
	Detail      string
	ExecutionID string
	TraceID     string
	CETHash     string
	// InnerCode is the underlying ERR_TANTRA_* code when the failure originated
	// in the inner decision verifier (empty otherwise).
	InnerCode string
}

// Error satisfies error.
func (e *CETValidationError) Error() string {
	if e.InnerCode != "" {
		return fmt.Sprintf("%s (inner=%s): %s", e.Code, e.InnerCode, e.Detail)
	}
	return e.Code + ": " + e.Detail
}

// CETBoundary wires the convergence gate to an inner TANTRA verifier. The inner
// verifier does the real cryptographic work; the boundary adds the convergence
// continuity gates. Both the live HTTP handler and the offline convergence
// driver construct one of these.
type CETBoundary struct {
	Inner *TantraVerifier
	Now   func() time.Time
}

// NewCETBoundary builds a boundary backed by the process-wide active TANTRA
// verifier (active provider + active trust registry + boot replay store). Used
// by the live HTTP surface.
func NewCETBoundary() *CETBoundary {
	return &CETBoundary{
		Inner: NewTantraVerifier(),
		Now:   func() time.Time { return time.Now().UTC() },
	}
}

// Verify runs the full CET->Sarathi boundary gate over raw SUM-SCRIPT bytes.
func (b *CETBoundary) Verify(raw []byte) (*CETVerifierResult, *CETValidationError) {
	now := time.Now().UTC()
	if b.Now != nil {
		now = b.Now()
	}

	// C0 — strict decode.
	s, err := DecodeCETSumScriptStrict(raw)
	if err != nil {
		emsg := err.Error()
		code := ErrCETMissingField
		switch {
		case strings.Contains(emsg, "unknown field"):
			code = ErrCETUnknownField
		case strings.Contains(emsg, "exceeds cap"):
			code = ErrCETBodyTooLarge
		}
		return nil, &CETValidationError{Code: code, Detail: "decode: " + emsg}
	}

	// C1 — schema_version.
	if strings.TrimSpace(s.SchemaVersion) != CETConvergenceSchemaVersion {
		return nil, &CETValidationError{
			Code:        ErrCETSchemaVersionUnknown,
			Detail:      fmt.Sprintf("schema_version %q is not %q", s.SchemaVersion, CETConvergenceSchemaVersion),
			ExecutionID: s.ExecutionID, TraceID: s.TraceID, CETHash: s.CETHash,
		}
	}

	// C2 — contract_version.
	if strings.TrimSpace(s.ContractVersion) != CETConvergenceContractVersion {
		return nil, &CETValidationError{
			Code:        ErrCETContractVersionUnknown,
			Detail:      fmt.Sprintf("contract_version %q is not %q", s.ContractVersion, CETConvergenceContractVersion),
			ExecutionID: s.ExecutionID, TraceID: s.TraceID, CETHash: s.CETHash,
		}
	}

	// C3 — required identity fields.
	missing := []string{}
	if strings.TrimSpace(s.ExecutionID) == "" {
		missing = append(missing, "execution_id")
	}
	if strings.TrimSpace(s.TraceID) == "" {
		missing = append(missing, "trace_id")
	}
	if strings.TrimSpace(s.CETHash) == "" {
		missing = append(missing, "cet_hash")
	}
	if strings.TrimSpace(s.BucketKey) == "" {
		missing = append(missing, "bucket_key")
	}
	if strings.TrimSpace(s.DecisionB64) == "" {
		missing = append(missing, "decision_b64")
	}
	if len(missing) > 0 {
		return nil, &CETValidationError{
			Code:        ErrCETMissingField,
			Detail:      "missing required fields: " + strings.Join(missing, ", "),
			ExecutionID: s.ExecutionID, TraceID: s.TraceID, CETHash: s.CETHash,
		}
	}

	// C4 — cet_hash structural.
	if !isLowerHex64(s.CETHash) {
		return nil, &CETValidationError{
			Code:        ErrCETHashMalformed,
			Detail:      "cet_hash must be 64 lowercase hex characters",
			ExecutionID: s.ExecutionID, TraceID: s.TraceID, CETHash: s.CETHash,
		}
	}

	// C5 — bucket_key structural.
	if !isLowerHex64(s.BucketKey) {
		return nil, &CETValidationError{
			Code:        ErrCETBucketKeyMalformed,
			Detail:      "bucket_key must be 64 lowercase hex characters",
			ExecutionID: s.ExecutionID, TraceID: s.TraceID, CETHash: s.CETHash,
		}
	}

	// C6 — decode inner decision bytes (verbatim canonical wire bytes).
	innerRaw, derr := s.DecodeInnerDecisionBytes()
	if derr != nil {
		return nil, &CETValidationError{
			Code:        ErrCETDecisionDecode,
			Detail:      derr.Error(),
			ExecutionID: s.ExecutionID, TraceID: s.TraceID, CETHash: s.CETHash,
		}
	}

	// C7 — real 12-step cryptographic verification of the inner decision.
	if b.Inner == nil {
		return nil, &CETValidationError{
			Code:        ErrCETInnerDecisionInvalid,
			Detail:      "inner TANTRA verifier not wired",
			ExecutionID: s.ExecutionID, TraceID: s.TraceID, CETHash: s.CETHash,
		}
	}
	innerResult, ierr := b.Inner.Verify(innerRaw)
	if ierr != nil {
		innerCode := ErrTantraSignatureInvalid
		if tve, ok := ierr.(*TantraValidationError); ok {
			innerCode = tve.Code
		}
		return nil, &CETValidationError{
			Code:        ErrCETInnerDecisionInvalid,
			Detail:      "inner tantra.decision.v1 verification failed: " + ierr.Error(),
			InnerCode:   innerCode,
			ExecutionID: s.ExecutionID, TraceID: s.TraceID, CETHash: s.CETHash,
		}
	}

	// C8 — trace_id continuity (envelope vs inner decision).
	if innerResult.Decision.TraceID != s.TraceID {
		return nil, &CETValidationError{
			Code: ErrCETTraceIDDiscontinuity,
			Detail: fmt.Sprintf("inner decision trace_id %q != envelope trace_id %q",
				innerResult.Decision.TraceID, s.TraceID),
			ExecutionID: s.ExecutionID, TraceID: s.TraceID, CETHash: s.CETHash,
		}
	}

	// C9 — optional independent cet_hash recompute (only when CET shared the
	// pre-image material). Absence does NOT fail the chain — cet_hash
	// originates at CET; Sarathi preserves + binds it. A mismatch DOES fail.
	recomputed, ran, rerr := s.RecomputeCETHashFromMaterial()
	if rerr != nil {
		return nil, &CETValidationError{
			Code:        ErrCETHashRecomputeMismatch,
			Detail:      rerr.Error(),
			ExecutionID: s.ExecutionID, TraceID: s.TraceID, CETHash: s.CETHash,
		}
	}
	if ran && !strings.EqualFold(recomputed, s.CETHash) {
		return nil, &CETValidationError{
			Code: ErrCETHashRecomputeMismatch,
			Detail: fmt.Sprintf("sha256(cet_material)=%s != declared cet_hash=%s",
				recomputed, s.CETHash),
			ExecutionID: s.ExecutionID, TraceID: s.TraceID, CETHash: s.CETHash,
		}
	}

	// C10 — seal + continuity proof.
	seal := s.SealHash()

	decision := CETDecisionReject
	if innerResult.Decision.Verdict == TantraVerdictAllow {
		decision = CETDecisionAllow
	}

	continuity := CETContractContinuity{
		SumScriptReceived: true,
		CETHashVerified:   true, // structural + binding + (recompute when material supplied)
		TraceIDPreserved:  true, // envelope == inner == egress; Sarathi never mutates trace_id
		MutationDetected:  false,
	}

	return &CETVerifierResult{
		SumScript:         s,
		InnerResult:       innerResult,
		SealHash:          seal,
		CETHashRecomputed: ran,
		Decision:          decision,
		Continuity:        continuity,
		VerifiedAt:        now,
	}, nil
}
