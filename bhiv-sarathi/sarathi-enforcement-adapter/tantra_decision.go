package main

// tantra_decision.go — TANTRA Sutradhar Final Decision Contract (v15.7).
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — TANTRA Inbound Decision Schema
// Host Organization: Blackhole Infiverse (BHIV)
//
// CONTRACT (frozen by BHIV Core, schema_version = "tantra.decision.v1"):
//
//   {
//     "schema_version":      "tantra.decision.v1",
//     "trace_id":            "<uuid-v4>",
//     "input_hash":          "<sha256_hex of raw input>",
//     "decision_id":         "<derived deterministic id>",
//     "decision_hash":       "<sha256_hex of canonical decision material>",
//     "verdict":             "ALLOW" | "DENY" | "ESCALATE",
//     "policy_reference":    "<policy pack id>",
//     "evaluator_id":        "bhiv.<system>.<component>.<environment>.v<major>",
//     "enforcement_binding": "<status>:<reason>",
//     "timestamp":           "<RFC3339Nano UTC>",
//     "signature": {
//       "alg":      "Ed25519" | "Composite-MLDSA65-Ed25519",
//       "key_id":   "<evaluator_id>#<rotation-tag>",
//       "encoding": "base64url_no_pad",
//       "value":    "<encoded signature>"
//     }
//   }
//
// FIELD ORDER IS LOAD-BEARING — the signing canonical bytes use this exact
// order. tantra_canonical.go emits the bytes; this file defines the types.
//
// IMMUTABLE INVARIANTS (TANTRA Final Contract §1–§8):
//   - signature is ALWAYS last in the payload and EXCLUDED from signing bytes.
//   - decision_hash material is a 6-field subset: schema_version, trace_id,
//     input_hash, verdict, policy_reference, evaluator_id (NO timestamp).
//   - timestamp is in the signed payload, NOT in decision_hash material.
//   - Unknown schema_version → fail closed.
//   - Unknown evaluator_id format → fail closed.
//   - Replay window: 300 s (per-decision_hash AND per-signed-payload).
//   - Mutation = signature failure. Any field reorder = signature failure.
//
// TAG: tantra-v15.7

import (
	"errors"
	"strings"
)

// TantraSchemaV1 is the only accepted schema_version on /sarathi/enforce.
// Anything else MUST fail closed with ERR_TANTRA_SCHEMA_VERSION_UNKNOWN.
const TantraSchemaV1 = "tantra.decision.v1"

// TantraSignatureEncoding is the only accepted signature.encoding value.
// Padded base64 and base64-std (different alphabet) are rejected.
const TantraSignatureEncoding = "base64url_no_pad"

// TantraVerdict is the closed set of acceptable verdict strings.
type TantraVerdict string

const (
	TantraVerdictAllow    TantraVerdict = "ALLOW"
	TantraVerdictDeny     TantraVerdict = "DENY"
	TantraVerdictEscalate TantraVerdict = "ESCALATE"
)

// IsValid returns true for ALLOW / DENY / ESCALATE only.
func (v TantraVerdict) IsValid() bool {
	switch v {
	case TantraVerdictAllow, TantraVerdictDeny, TantraVerdictEscalate:
		return true
	}
	return false
}

// TantraSignature is the four-field signature object placed last in every
// TANTRA payload. The signing bytes EXCLUDE this object entirely (per §6
// of the contract).
//
// JSON tag order matches the contract; the field order inside this object is
// itself part of the canonical-bytes contract.
type TantraSignature struct {
	Alg      string `json:"alg"`      // "Ed25519" or "Composite-MLDSA65-Ed25519"
	KeyID    string `json:"key_id"`   // "<evaluator_id>#<rotation>"
	Encoding string `json:"encoding"` // ALWAYS "base64url_no_pad"
	Value    string `json:"value"`    // encoded signature
}

// TantraDecision is the exact wire shape exchanged at /sarathi/enforce.
// JSON struct tag order MUST mirror the contract field order — Go's
// encoding/json preserves declaration order on Marshal, which lines up with
// the fixed canonical ordering tantra_canonical.go relies on.
//
// IMPORTANT: do NOT add fields here. Any extra field on the wire is rejected
// at decode time via json.Decoder.DisallowUnknownFields.
type TantraDecision struct {
	SchemaVersion      string          `json:"schema_version"`
	TraceID            string          `json:"trace_id"`
	InputHash          string          `json:"input_hash"`
	DecisionID         string          `json:"decision_id"`
	DecisionHash       string          `json:"decision_hash"`
	Verdict            TantraVerdict   `json:"verdict"`
	PolicyReference    string          `json:"policy_reference"`
	EvaluatorID        string          `json:"evaluator_id"`
	EnforcementBinding string          `json:"enforcement_binding"`
	Timestamp          string          `json:"timestamp"`
	Signature          TantraSignature `json:"signature"`
}

// TantraDecisionMaterial is the SIX-field subset hashed to produce
// decision_hash. The contract specifies these exact fields in this exact
// order. timestamp is NOT included — that's load-bearing.
//
// JSON tag order MUST mirror the contract.
type TantraDecisionMaterial struct {
	SchemaVersion   string        `json:"schema_version"`
	TraceID         string        `json:"trace_id"`
	InputHash       string        `json:"input_hash"`
	Verdict         TantraVerdict `json:"verdict"`
	PolicyReference string        `json:"policy_reference"`
	EvaluatorID     string        `json:"evaluator_id"`
}

// FromDecision projects a verified TantraDecision into its decision_hash
// material (the six fields, in the right order).
func (d *TantraDecision) Material() TantraDecisionMaterial {
	return TantraDecisionMaterial{
		SchemaVersion:   d.SchemaVersion,
		TraceID:         d.TraceID,
		InputHash:       d.InputHash,
		Verdict:         d.Verdict,
		PolicyReference: d.PolicyReference,
		EvaluatorID:     d.EvaluatorID,
	}
}

// RequiredFields enumerates every field that MUST be present and non-empty on
// a TANTRA decision. Used by the structural-validation step before signature
// verification (so a malformed body fails fast with a precise error).
//
// signature is checked separately because its inner fields have their own
// required-set; an empty signature object is its own error code.
func (d *TantraDecision) RequiredFields() error {
	missing := []string{}
	if strings.TrimSpace(d.SchemaVersion) == "" {
		missing = append(missing, "schema_version")
	}
	if strings.TrimSpace(d.TraceID) == "" {
		missing = append(missing, "trace_id")
	}
	if strings.TrimSpace(d.InputHash) == "" {
		missing = append(missing, "input_hash")
	}
	if strings.TrimSpace(d.DecisionID) == "" {
		missing = append(missing, "decision_id")
	}
	if strings.TrimSpace(d.DecisionHash) == "" {
		missing = append(missing, "decision_hash")
	}
	if strings.TrimSpace(string(d.Verdict)) == "" {
		missing = append(missing, "verdict")
	}
	if strings.TrimSpace(d.PolicyReference) == "" {
		missing = append(missing, "policy_reference")
	}
	if strings.TrimSpace(d.EvaluatorID) == "" {
		missing = append(missing, "evaluator_id")
	}
	if strings.TrimSpace(d.EnforcementBinding) == "" {
		missing = append(missing, "enforcement_binding")
	}
	if strings.TrimSpace(d.Timestamp) == "" {
		missing = append(missing, "timestamp")
	}
	if strings.TrimSpace(d.Signature.Alg) == "" {
		missing = append(missing, "signature.alg")
	}
	if strings.TrimSpace(d.Signature.KeyID) == "" {
		missing = append(missing, "signature.key_id")
	}
	if strings.TrimSpace(d.Signature.Encoding) == "" {
		missing = append(missing, "signature.encoding")
	}
	if strings.TrimSpace(d.Signature.Value) == "" {
		missing = append(missing, "signature.value")
	}
	if len(missing) > 0 {
		return &TantraValidationError{
			Code:   ErrTantraMissingField,
			Detail: "missing required fields: " + strings.Join(missing, ", "),
		}
	}
	if !d.Verdict.IsValid() {
		return &TantraValidationError{
			Code:   ErrTantraVerdictInvalid,
			Detail: "verdict must be ALLOW, DENY, or ESCALATE (got " + string(d.Verdict) + ")",
		}
	}
	if d.SchemaVersion != TantraSchemaV1 {
		return &TantraValidationError{
			Code:   ErrTantraSchemaVersionUnknown,
			Detail: "schema_version " + d.SchemaVersion + " is not " + TantraSchemaV1,
		}
	}
	if d.Signature.Encoding != TantraSignatureEncoding {
		return &TantraValidationError{
			Code:   ErrTantraEncodingUnsupported,
			Detail: "signature.encoding " + d.Signature.Encoding + " is not " + TantraSignatureEncoding,
		}
	}
	return nil
}

// TantraValidationError carries a stable error code + a human-readable detail.
// HTTP handlers translate this into ERR_TANTRA_* response codes.
type TantraValidationError struct {
	Code   string
	Detail string
}

// Error satisfies error.
func (e *TantraValidationError) Error() string {
	return e.Code + ": " + e.Detail
}

// Is exists so callers can use errors.Is(err, &TantraValidationError{Code:"..."}).
func (e *TantraValidationError) Is(target error) bool {
	var t *TantraValidationError
	if !errors.As(target, &t) {
		return false
	}
	return t.Code == e.Code
}

// ============================================================================
// STABLE ERROR CODES (returned in HTTP responses as ERR_TANTRA_*)
// ============================================================================

const (
	ErrTantraSchemaVersionUnknown   = "ERR_TANTRA_SCHEMA_VERSION_UNKNOWN"
	ErrTantraMissingField           = "ERR_TANTRA_MISSING_FIELD"
	ErrTantraUnknownField           = "ERR_TANTRA_UNKNOWN_FIELD"
	ErrTantraVerdictInvalid         = "ERR_TANTRA_VERDICT_INVALID"
	ErrTantraEvaluatorIDFormat      = "ERR_TANTRA_EVALUATOR_ID_FORMAT"
	ErrTantraEvaluatorNotRegistered = "ERR_TANTRA_EVALUATOR_NOT_REGISTERED"
	ErrTantraEvaluatorNotActive     = "ERR_TANTRA_EVALUATOR_NOT_ACTIVE"
	ErrTantraEvaluatorSchemaMismatch = "ERR_TANTRA_EVALUATOR_SCHEMA_MISMATCH"
	ErrTantraKeyIDMismatch          = "ERR_TANTRA_KEY_ID_MISMATCH"
	ErrTantraAlgMismatch            = "ERR_TANTRA_ALG_MISMATCH"
	ErrTantraEncodingUnsupported    = "ERR_TANTRA_ENCODING_UNSUPPORTED"
	ErrTantraSignatureInvalid       = "ERR_TANTRA_SIGNATURE_INVALID"
	ErrTantraSignatureDecode        = "ERR_TANTRA_SIGNATURE_DECODE"
	ErrTantraDecisionHashMismatch   = "ERR_TANTRA_DECISION_HASH_MISMATCH"
	ErrTantraDecisionIDMismatch     = "ERR_TANTRA_DECISION_ID_MISMATCH"
	ErrTantraTimestampSkewed        = "ERR_TANTRA_TIMESTAMP_SKEWED"
	ErrTantraTimestampUnparseable   = "ERR_TANTRA_TIMESTAMP_UNPARSEABLE"
	ErrTantraReplay                 = "ERR_TANTRA_REPLAY"
	ErrTantraCanonicalEncoding      = "ERR_TANTRA_CANONICAL_ENCODING"
	ErrTantraBodyTooLarge           = "ERR_TANTRA_BODY_TOO_LARGE"
	// v15.11 — load-bearing API-key fingerprint gate codes.
	ErrTantraAPIKeyRequired = "ERR_TANTRA_API_KEY_REQUIRED"
	ErrTantraAPIKeyInvalid  = "ERR_TANTRA_API_KEY_INVALID"
)

// TantraReplayTTL is the contract-mandated replay window (§8).
const TantraReplayTTLSeconds = 300

// TantraTimestampSkewSeconds is ±300 s — matches the contract's recommended
// TTL. The existing SARATHI_REQUEST_SKEW_S (default 300) is the same value
// applied at the header layer; reusing the constant keeps both surfaces
// aligned but lets us tune the TANTRA window independently if needed.
const TantraTimestampSkewSeconds = 300

// TantraMaxBodyBytes caps inbound TANTRA POST bodies (1 MiB — same as the
// existing peer-receipt cap). A typical TANTRA body is <2 KiB under Ed25519
// and <8 KiB under hybrid.
const TantraMaxBodyBytes = 1 << 20
