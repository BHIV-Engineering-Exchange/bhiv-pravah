package main

// tantra_canonical.go — TANTRA Fixed-Order Canonical JSON encoder.
//
// THIS FILE IS DELIBERATELY SEPARATE FROM canonical_json.go.
//
//   canonical_json.go        — RFC 8785 alphabetical ordering (peer receipts,
//                              propagation envelopes, JWK sets, response
//                              contract). UNCHANGED. Continues to serve the
//                              existing chain.
//
//   tantra_canonical.go      — TANTRA Final Contract §2/§6 fixed key order.
//                              The contract specifies an EXPLICIT field order
//                              (NOT alphabetical) for the signing bytes:
//                                schema_version, trace_id, input_hash,
//                                decision_id, decision_hash, verdict,
//                                policy_reference, evaluator_id,
//                                enforcement_binding, timestamp.
//                              signature is EXCLUDED from the signed bytes.
//
//                              decision_hash material order:
//                                schema_version, trace_id, input_hash,
//                                verdict, policy_reference, evaluator_id.
//
// The two encoders MUST produce different bytes for the same input — they
// implement different canonicalisations on purpose.
//
// CRYPTOGRAPHIC INVARIANT:
//   The byte string returned by CanonicalDecisionPayloadBytes() is the
//   EXACT input to provider.Sign() / provider.Verify(). One character of
//   drift = signature failure.
//
// TAG: tantra-v15.7

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"strings"
	"unicode/utf8"
)

// tantraStringEscape writes a JSON string literal using the same escape rules
// as canonical_json.go::encodeString (RFC 8785 compatible). Same rules apply:
// no HTML escaping, \u00XX lowercase hex for control characters, raw UTF-8
// for everything else.
func tantraStringEscape(buf *bytes.Buffer, s string) {
	buf.WriteByte('"')
	for i := 0; i < len(s); {
		r, size := utf8.DecodeRuneInString(s[i:])
		switch {
		case r == '"':
			buf.WriteString(`\"`)
		case r == '\\':
			buf.WriteString(`\\`)
		case r == '\b':
			buf.WriteString(`\b`)
		case r == '\f':
			buf.WriteString(`\f`)
		case r == '\n':
			buf.WriteString(`\n`)
		case r == '\r':
			buf.WriteString(`\r`)
		case r == '\t':
			buf.WriteString(`\t`)
		case r < 0x20:
			fmt.Fprintf(buf, `\u%04x`, r)
		default:
			buf.WriteString(s[i : i+size])
		}
		i += size
	}
	buf.WriteByte('"')
}

// writeKVString emits  "<key>":"<value>"  with no whitespace.
func writeKVString(buf *bytes.Buffer, key, value string, prependComma bool) {
	if prependComma {
		buf.WriteByte(',')
	}
	tantraStringEscape(buf, key)
	buf.WriteByte(':')
	tantraStringEscape(buf, value)
}

// CanonicalDecisionPayloadBytes returns the EXACT UTF-8 bytes that should be
// signed (when called with includeEmptySignature=false) OR the EXACT bytes
// emitted on the wire (when called with includeEmptySignature=true and the
// signature object is fully populated).
//
// FIELD ORDER (load-bearing — per Contract §2):
//   schema_version, trace_id, input_hash, decision_id, decision_hash,
//   verdict, policy_reference, evaluator_id, enforcement_binding, timestamp,
//   signature (only when emitting on the wire).
//
// signature is OMITTED entirely when computing signing bytes. Calling code
// that wants the signing bytes invokes CanonicalSignableBytes(d) — a thin
// wrapper that calls this function with the signature-stripped invariant.
//
// NOTE: encoding/json's default Marshal preserves struct field declaration
// order, but it ALSO adds the signature object when present. Using a
// hand-written emitter keeps the contract field order load-bearing and
// independent of any future struct-field reordering.
func CanonicalDecisionPayloadBytes(d *TantraDecision, includeSignature bool) ([]byte, error) {
	if d == nil {
		return nil, fmt.Errorf("tantra_canonical: nil decision")
	}
	var buf bytes.Buffer
	buf.Grow(1024)
	buf.WriteByte('{')

	writeKVString(&buf, "schema_version", d.SchemaVersion, false)
	writeKVString(&buf, "trace_id", d.TraceID, true)
	writeKVString(&buf, "input_hash", d.InputHash, true)
	writeKVString(&buf, "decision_id", d.DecisionID, true)
	writeKVString(&buf, "decision_hash", d.DecisionHash, true)
	writeKVString(&buf, "verdict", string(d.Verdict), true)
	writeKVString(&buf, "policy_reference", d.PolicyReference, true)
	writeKVString(&buf, "evaluator_id", d.EvaluatorID, true)
	writeKVString(&buf, "enforcement_binding", d.EnforcementBinding, true)
	writeKVString(&buf, "timestamp", d.Timestamp, true)

	if includeSignature {
		// Emit signature object with INNER field order: alg, key_id, encoding, value.
		buf.WriteByte(',')
		tantraStringEscape(&buf, "signature")
		buf.WriteByte(':')
		buf.WriteByte('{')
		writeKVString(&buf, "alg", d.Signature.Alg, false)
		writeKVString(&buf, "key_id", d.Signature.KeyID, true)
		writeKVString(&buf, "encoding", d.Signature.Encoding, true)
		writeKVString(&buf, "value", d.Signature.Value, true)
		buf.WriteByte('}')
	}

	buf.WriteByte('}')
	return buf.Bytes(), nil
}

// CanonicalSignableBytes returns the bytes that get fed to provider.Sign() /
// provider.Verify(). Equivalent to CanonicalDecisionPayloadBytes(d, false).
func CanonicalSignableBytes(d *TantraDecision) ([]byte, error) {
	return CanonicalDecisionPayloadBytes(d, false)
}

// CanonicalWireBytes returns the bytes emitted on the wire (signature
// included). Equivalent to CanonicalDecisionPayloadBytes(d, true).
func CanonicalWireBytes(d *TantraDecision) ([]byte, error) {
	return CanonicalDecisionPayloadBytes(d, true)
}

// CanonicalDecisionMaterialBytes returns the EXACT UTF-8 bytes that get
// hashed to produce decision_hash. Per Contract §3, the material is the
// six-field subset in the fixed order:
//
//   schema_version, trace_id, input_hash, verdict, policy_reference, evaluator_id
//
// timestamp is NOT included (load-bearing — timestamps change per run but
// decision content does not).
func CanonicalDecisionMaterialBytes(m TantraDecisionMaterial) []byte {
	var buf bytes.Buffer
	buf.Grow(256)
	buf.WriteByte('{')
	writeKVString(&buf, "schema_version", m.SchemaVersion, false)
	writeKVString(&buf, "trace_id", m.TraceID, true)
	writeKVString(&buf, "input_hash", m.InputHash, true)
	writeKVString(&buf, "verdict", string(m.Verdict), true)
	writeKVString(&buf, "policy_reference", m.PolicyReference, true)
	writeKVString(&buf, "evaluator_id", m.EvaluatorID, true)
	buf.WriteByte('}')
	return buf.Bytes()
}

// ComputeTantraDecisionHash returns hex(SHA-256(material_canonical_bytes)).
// This is the exact value that must populate TantraDecision.DecisionHash.
//
// The deterministic, reproducible nature of this hash is the audit anchor:
// any verifier can recompute it from the six material fields and compare to
// the stored value. Mismatch = ERR_TANTRA_DECISION_HASH_MISMATCH.
func ComputeTantraDecisionHash(m TantraDecisionMaterial) string {
	bytes := CanonicalDecisionMaterialBytes(m)
	h := sha256.Sum256(bytes)
	return hex.EncodeToString(h[:])
}

// VerifyDecodeStrict parses a TANTRA decision body with DisallowUnknownFields
// and a body-size cap. Returns the typed decision OR a precise validation
// error suitable for HTTP response translation.
//
// Caller is expected to have already enforced TantraMaxBodyBytes on the
// transport layer; this function does a final length sanity check.
func VerifyDecodeStrict(raw []byte) (*TantraDecision, error) {
	if len(raw) == 0 {
		return nil, &TantraValidationError{
			Code:   ErrTantraMissingField,
			Detail: "empty request body",
		}
	}
	if len(raw) > TantraMaxBodyBytes {
		return nil, &TantraValidationError{
			Code:   ErrTantraBodyTooLarge,
			Detail: fmt.Sprintf("body size %d exceeds cap %d", len(raw), TantraMaxBodyBytes),
		}
	}
	dec := json.NewDecoder(strings.NewReader(string(raw)))
	dec.DisallowUnknownFields()
	var out TantraDecision
	if err := dec.Decode(&out); err != nil {
		// Surface unknown-field rejection as a distinct error code per §8.
		emsg := err.Error()
		switch {
		case strings.Contains(emsg, "unknown field"):
			return nil, &TantraValidationError{
				Code:   ErrTantraUnknownField,
				Detail: emsg,
			}
		default:
			return nil, &TantraValidationError{
				Code:   ErrTantraMissingField,
				Detail: "decode failed: " + emsg,
			}
		}
	}
	// Reject trailing JSON (a second value or whitespace + garbage).
	if dec.More() {
		return nil, &TantraValidationError{
			Code:   ErrTantraUnknownField,
			Detail: "trailing data after decision object",
		}
	}
	return &out, nil
}

// CanonicalRoundTripVerify is a defensive helper that re-marshals the typed
// TantraDecision via the hand-written emitter and compares to the input
// bytes. Used by the verifier as a structural-canonicity check before any
// cryptographic step runs — if the input bytes deviated from the contract
// field order (e.g. an upstream re-encoder), this surfaces immediately as
// ERR_TANTRA_CANONICAL_ENCODING.
//
// Returns (true, nil) if input bytes match the canonical wire form.
//
// Production note: this helper is OPTIONAL. The signature verification step
// will already fail on any byte drift. Round-trip is provided so audit logs
// carry a precise reason ("field order drift" vs "wrong key") rather than a
// generic "signature invalid".
func CanonicalRoundTripVerify(input []byte, d *TantraDecision) (bool, string) {
	want, err := CanonicalWireBytes(d)
	if err != nil {
		return false, "round_trip_encode_failed: " + err.Error()
	}
	if !bytes.Equal(want, input) {
		return false, fmt.Sprintf(
			"round_trip_mismatch: input_sha256=%s reencoded_sha256=%s input_len=%d reencoded_len=%d",
			sha256Hex(input), sha256Hex(want), len(input), len(want),
		)
	}
	return true, ""
}

// sha256Hex is a local helper to avoid a dependency on the existing
// Sha256Hex (capitalised) in case someone refactors that signature later.
func sha256Hex(b []byte) string {
	h := sha256.Sum256(b)
	return hex.EncodeToString(h[:])
}
