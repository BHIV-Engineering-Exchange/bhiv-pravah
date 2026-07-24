package main

// cet_contract.go — CET → Sarathi convergence contract (the SUM-SCRIPT envelope).
//
// Author: Hemanth B
// System: Sarathi Governance Kernel — CET Convergence Boundary (TANTRA-CONVERGENCE-v1)
// Host Organization: Blackhole Infiverse (BHIV)
//
// PURPOSE:
//   The TANTRA convergence chain is:
//
//       Core -> CET -> Sarathi -> Bridge -> Runtime -> InsightFlow -> Bucket
//
//   CET (the Contract / Canonical Execution Trace compiler) takes the
//   Core-produced decision, compiles it into a canonical execution contract,
//   computes the `cet_hash` integrity anchor ONCE, and seals the result as a
//   SUM-SCRIPT. The SUM-SCRIPT is the deterministic unit that flows downstream
//   and is persisted immutably in Bucket for byte-identical replay.
//
//   This file defines the on-the-wire SUM-SCRIPT envelope Sarathi accepts at
//   the CET->Sarathi boundary, the locked convergence constants, and the
//   deterministic canonical encoder used to (a) seal the envelope for mutation
//   detection and (b) optionally recompute the cet_hash when CET supplies the
//   pre-image material.
//
// SCOPING (additive — does NOT touch the existing tantra.decision.v1 surface):
//   The envelope WRAPS an inner, fully-signed `tantra.decision.v1` decision
//   (carried verbatim as base64 of its canonical wire bytes so the inner
//   signature verifies on byte-identical input). The existing 12-step TANTRA
//   verifier (tantra_verifier.go) does the real cryptographic verification of
//   the inner decision; this layer adds the convergence-envelope continuity
//   gates on top.
//
// IDENTITY PRESERVATION INVARIANT (canonical_chain_identity.md §Continuity Rules):
//   execution_id, trace_id, and cet_hash MUST be preserved byte-identical from
//   the moment Sarathi receives the SUM-SCRIPT through every Sarathi egress
//   surface. Sarathi NEVER regenerates, aliases, normalizes, or substitutes
//   these identifiers. Any mismatch is a chain discontinuity and fails closed.
//
// TAG: tantra-convergence-v1

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"strings"
)

// Locked convergence constants. These mirror the values the TANTRA team locked
// in canonical_chain_identity.md. Any envelope that does not carry these exact
// values at the CET->Sarathi boundary is rejected fail-closed.
const (
	// CETConvergenceSchemaVersion is the envelope-level schema_version carried
	// alongside the sealed SUM-SCRIPT. NOT to be confused with the inner
	// decision's schema_version (tantra.decision.v1).
	CETConvergenceSchemaVersion = "1.0"

	// CETConvergenceContractVersion is the convergence contract identifier.
	CETConvergenceContractVersion = "TANTRA-CONVERGENCE-v1"

	// CETBoundaryName is the producing/validating boundary label used in every
	// artifact Sarathi emits for this chain.
	CETBoundaryName = "CET->Sarathi"

	// CETSumScriptMaxBytes caps an inbound SUM-SCRIPT body (1 MiB — same cap as
	// the inbound TANTRA decision body).
	CETSumScriptMaxBytes = 1 << 20
)

// CETSumScript is the exact wire shape Sarathi accepts at the CET->Sarathi
// boundary. Field order in this struct is the canonical seal order — see
// CanonicalBytes.
//
// IMPORTANT: do NOT add wire fields without updating CanonicalBytes; the
// decoder uses DisallowUnknownFields so any undeclared field is rejected.
type CETSumScript struct {
	// SchemaVersion MUST equal CETConvergenceSchemaVersion ("1.0").
	SchemaVersion string `json:"schema_version"`
	// ContractVersion MUST equal CETConvergenceContractVersion.
	ContractVersion string `json:"contract_version"`
	// ExecutionID is the upstream-locked execution identifier (originates at
	// Core, preserved unchanged). e.g. "exec-tantra-001".
	ExecutionID string `json:"execution_id"`
	// TraceID is the upstream-locked trace identifier. e.g. "trace-tantra-001".
	TraceID string `json:"trace_id"`
	// CETHash is the integrity anchor CET computed over the compiled contract.
	// 64 lowercase hex. Sarathi PRESERVES this; it never regenerates it.
	CETHash string `json:"cet_hash"`
	// BucketKey is the immutable replay-truth reference under which the sealed
	// SUM-SCRIPT is persisted in Bucket. 64 lowercase hex.
	BucketKey string `json:"bucket_key"`
	// DecisionB64 carries the inner, fully-signed tantra.decision.v1 decision
	// as base64-std of its EXACT canonical wire bytes (so the inner Ed25519 /
	// composite signature verifies on byte-identical input — no re-encoding).
	DecisionB64 string `json:"decision_b64"`
	// CETMaterialB64 is OPTIONAL. When CET supplies the exact canonical bytes
	// it hashed to produce CETHash, Sarathi independently recomputes
	// sha256(material) and asserts it equals CETHash. When absent, cet_hash
	// verification rests on structural + binding + continuity (Sarathi does not
	// fabricate a pre-image — cet_hash originates at CET).
	CETMaterialB64 string `json:"cet_material_b64,omitempty"`
}

// CanonicalBytes returns deterministic UTF-8 bytes for the envelope using a
// fixed field order. This is the seal input: any byte-level change to any
// field (including the embedded inner decision) changes the seal, which is how
// Sarathi detects post-receipt mutation.
//
// Field order (load-bearing):
//
//	schema_version, contract_version, execution_id, trace_id, cet_hash,
//	bucket_key, decision_b64, [cet_material_b64 when present]
func (s *CETSumScript) CanonicalBytes() []byte {
	var buf bytes.Buffer
	buf.Grow(1024)
	buf.WriteByte('{')
	writeKVString(&buf, "schema_version", s.SchemaVersion, false)
	writeKVString(&buf, "contract_version", s.ContractVersion, true)
	writeKVString(&buf, "execution_id", s.ExecutionID, true)
	writeKVString(&buf, "trace_id", s.TraceID, true)
	writeKVString(&buf, "cet_hash", s.CETHash, true)
	writeKVString(&buf, "bucket_key", s.BucketKey, true)
	writeKVString(&buf, "decision_b64", s.DecisionB64, true)
	if strings.TrimSpace(s.CETMaterialB64) != "" {
		writeKVString(&buf, "cet_material_b64", s.CETMaterialB64, true)
	}
	buf.WriteByte('}')
	return buf.Bytes()
}

// SealHash returns hex(SHA-256(CanonicalBytes())). This is Sarathi's own seal
// over the received SUM-SCRIPT. Recorded at ingress and re-asserted at every
// egress surface; a divergence proves the contract was mutated in-flight.
func (s *CETSumScript) SealHash() string {
	return sha256Hex(s.CanonicalBytes())
}

// DecodeInnerDecisionBytes base64-std-decodes DecisionB64 into the exact
// canonical wire bytes of the inner tantra.decision.v1 decision. These bytes
// are fed verbatim to the 12-step TANTRA verifier.
func (s *CETSumScript) DecodeInnerDecisionBytes() ([]byte, error) {
	clean := strings.TrimSpace(s.DecisionB64)
	if clean == "" {
		return nil, fmt.Errorf("decision_b64 is empty")
	}
	raw, err := base64.StdEncoding.DecodeString(clean)
	if err != nil {
		return nil, fmt.Errorf("decision_b64 not base64-std: %w", err)
	}
	if len(raw) == 0 {
		return nil, fmt.Errorf("decision_b64 decoded to empty bytes")
	}
	return raw, nil
}

// RecomputeCETHashFromMaterial returns (recomputedHash, true) when
// CETMaterialB64 is present, or ("", false) when absent. The caller compares
// the recomputed value to CETHash.
func (s *CETSumScript) RecomputeCETHashFromMaterial() (string, bool, error) {
	clean := strings.TrimSpace(s.CETMaterialB64)
	if clean == "" {
		return "", false, nil
	}
	raw, err := base64.StdEncoding.DecodeString(clean)
	if err != nil {
		return "", false, fmt.Errorf("cet_material_b64 not base64-std: %w", err)
	}
	return sha256Hex(raw), true, nil
}

// DecodeCETSumScriptStrict parses a SUM-SCRIPT body with DisallowUnknownFields
// and the body-size cap. Returns the typed envelope or a precise error.
func DecodeCETSumScriptStrict(raw []byte) (*CETSumScript, error) {
	if len(raw) == 0 {
		return nil, fmt.Errorf("empty SUM-SCRIPT body")
	}
	if len(raw) > CETSumScriptMaxBytes {
		return nil, fmt.Errorf("SUM-SCRIPT body size %d exceeds cap %d", len(raw), CETSumScriptMaxBytes)
	}
	dec := json.NewDecoder(strings.NewReader(string(raw)))
	dec.DisallowUnknownFields()
	var out CETSumScript
	if err := dec.Decode(&out); err != nil {
		return nil, err
	}
	if dec.More() {
		return nil, fmt.Errorf("trailing data after SUM-SCRIPT object")
	}
	return &out, nil
}

// isLowerHex64 reports whether s is exactly 64 lowercase hex characters — the
// shape of a SHA-256 hex digest. Used for cet_hash and bucket_key structural
// gates.
func isLowerHex64(s string) bool {
	if len(s) != 64 {
		return false
	}
	for i := 0; i < len(s); i++ {
		c := s[i]
		if (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') {
			continue
		}
		return false
	}
	return true
}
