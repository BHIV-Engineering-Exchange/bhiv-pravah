// parallel_execution_comparator.go (v14.8 Sovereign Authority Closure)
//
// Pure comparator: given two canonical response byte arrays (Sarathi vs
// legacy enforcer), produce a divergence verdict. No side effects, no I/O.
//
// Why not byte-identity?
// ----------------------
// Task.md asks the parallel-execution mode to "match or fail deterministically,
// never silently diverge". Two INDEPENDENT processes can never produce
// byte-identical canonical responses for the same input because the response
// envelope carries per-process wall-clock fields (enforced_at,
// execution.timestamp) and per-process random fields (enforcement_token,
// trace_id, span_id). These are part of the contract, not noise — but they
// cannot match across processes.
//
// What the comparator actually proves
// -----------------------------------
// The comparator asserts SEMANTIC decision parity: both pipelines, given the
// same signed input decision, arrive at the same enforcement conclusion. The
// gate fields are the ones derived deterministically from the input:
//
//   decision_id, decision_hash, decision_core_hash  (input-bound)
//   verdict, error_code, reason, mode               (policy conclusion)
//   enforcement.request_binding_hash                (chain anchor)
//
// Raw response hashes + structural hashes (after wall-clock/random fields
// are blanked) are ALSO recorded so the reviewer sees exactly which fields
// diverged. The match gate however fires on semantic parity.
//
// Any semantic divergence — different verdict, different decision_id,
// different chain anchor, parse failure — surfaces as ERR_SHADOW_DIVERGENCE
// and fails the execution closed.
//
// TAG: sovereign-authority-v14.8

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
)

// ShadowDivergenceRecord is the canonical row shape written to
// proof_logs/shadow_divergence_log.jsonl on every parallel execution.
type ShadowDivergenceRecord struct {
	SchemaVersion         string            `json:"schema_version"`
	ExecutionID           string            `json:"execution_id"`
	DecisionID            string            `json:"decision_id"`
	SarathiResponseHash   string            `json:"sarathi_response_hash"`
	LegacyResponseHash    string            `json:"legacy_response_hash"`
	SarathiStructuralHash string            `json:"sarathi_structural_hash"`
	LegacyStructuralHash  string            `json:"legacy_structural_hash"`
	Match                 bool              `json:"match"`
	ByteEqual             bool              `json:"byte_equal"`
	HashEqual             bool              `json:"hash_equal"`
	StructuralHashEqual   bool              `json:"structural_hash_equal"`
	SemanticEqual         bool              `json:"semantic_equal"`
	SarathiBytesLength    int               `json:"sarathi_bytes_length"`
	LegacyBytesLength     int               `json:"legacy_bytes_length"`
	SemanticFields        map[string]string `json:"semantic_fields,omitempty"`
	FieldDiffs            map[string]string `json:"field_diffs,omitempty"`
	DivergenceCode        string            `json:"divergence_code,omitempty"`
	Detail                string            `json:"detail,omitempty"`
	VerifiedAt            string            `json:"verified_at"`
}

// ShadowDivergenceSchemaVersion pins the record schema.
const ShadowDivergenceSchemaVersion = "sarathi.shadow-divergence/v14.8"

// shadowNormalizedFields are the keys replaced with a fixed placeholder when
// computing the *structural* hash. They are wall-clock or per-process random
// and cannot match across independent processes. Reported for transparency
// but not part of the match gate.
var shadowNormalizedFields = map[string]struct{}{
	"enforced_at":       {},
	"enforcement_token": {},
	"enforcement_hash":  {},
	"timestamp":         {},
	"trace_id":          {},
	"span_id":           {},
}

// shadowNormalizedChainKeys are list-valued keys whose last element is
// derived from a normalized scalar (propagation_chain's last element is
// enforcement_hash). Replacing the tail lets the rest of the chain still be
// compared.
var shadowNormalizedChainKeys = map[string]struct{}{
	"propagation_chain": {},
}

// shadowPlaceholder is the fixed value substituted for normalized fields.
const shadowPlaceholder = "$SHADOW_NORMALIZED$"

// semanticGateFields are the input-bound + policy-derived fields the match
// gate compares across both responses. These are the fields that MUST agree
// if both pipelines reached the same conclusion for the same decision. They
// are deterministically derived from the signed input decision.
var semanticGateFields = []string{
	"decision_id",
	"decision_hash",
	"decision_core_hash",
	"verdict",
	"error_code",
}

// semanticEnforcementFields are the fields extracted from the nested
// enforcement envelope and folded into the semantic comparison.
var semanticEnforcementFields = []string{
	"reason",
	"mode",
	"request_binding_hash",
}

// CompareCanonicalResponses is the pure comparator. Returns a record with
// Match=true when both responses decode as canonical JSON and carry
// identical values for every field in semanticGateFields +
// semanticEnforcementFields.
func CompareCanonicalResponses(sarathiBytes, legacyBytes []byte) ShadowDivergenceRecord {
	rec := ShadowDivergenceRecord{
		SchemaVersion:       ShadowDivergenceSchemaVersion,
		SarathiResponseHash: Sha256Hex(sarathiBytes),
		LegacyResponseHash:  Sha256Hex(legacyBytes),
		SarathiBytesLength:  len(sarathiBytes),
		LegacyBytesLength:   len(legacyBytes),
	}
	rec.HashEqual = rec.SarathiResponseHash == rec.LegacyResponseHash
	rec.ByteEqual = bytes.Equal(sarathiBytes, legacyBytes)

	sTree, sErr := decodeResponse(sarathiBytes)
	lTree, lErr := decodeResponse(legacyBytes)
	if sErr != nil || lErr != nil {
		rec.Match = false
		rec.DivergenceCode = CodeShadowDivergence
		rec.Detail = fmt.Sprintf("parse: sarathi_err=%v legacy_err=%v", sErr, lErr)
		return rec
	}

	rec.DecisionID = getStringField(sTree, "decision_id")
	if rec.DecisionID == "" {
		rec.DecisionID = getStringField(lTree, "decision_id")
	}

	// Structural hashes (wall-clock + random neutralised) — transparency only.
	if sStruct, err := structuralNormalize(sarathiBytes); err == nil {
		rec.SarathiStructuralHash = Sha256Hex(sStruct)
	}
	if lStruct, err := structuralNormalize(legacyBytes); err == nil {
		rec.LegacyStructuralHash = Sha256Hex(lStruct)
	}
	rec.StructuralHashEqual = rec.SarathiStructuralHash != "" &&
		rec.SarathiStructuralHash == rec.LegacyStructuralHash

	// Semantic parity — the actual gate.
	diffs := map[string]string{}
	sFields := extractSemanticFields(sTree)
	lFields := extractSemanticFields(lTree)
	rec.SemanticFields = sFields
	for k, sv := range sFields {
		lv := lFields[k]
		if sv != lv {
			diffs[k] = fmt.Sprintf("sarathi=%s legacy=%s", sv, lv)
		}
	}
	rec.SemanticEqual = len(diffs) == 0 && sFields["decision_id"] != ""

	if !rec.ByteEqual && rec.HashEqual {
		diffs["byte_equality"] = "hashes_equal_but_bytes_differ_CRITICAL"
	}
	if len(diffs) > 0 {
		rec.FieldDiffs = diffs
	}

	rec.Match = rec.SemanticEqual
	if !rec.Match {
		rec.DivergenceCode = CodeShadowDivergence
		if rec.Detail == "" {
			rec.Detail = "semantic_field_divergence"
		}
	}
	return rec
}

func decodeResponse(raw []byte) (map[string]interface{}, error) {
	if len(raw) == 0 {
		return nil, fmt.Errorf("empty_bytes")
	}
	var tree map[string]interface{}
	if err := json.Unmarshal(raw, &tree); err != nil {
		return nil, fmt.Errorf("unmarshal: %w", err)
	}
	return tree, nil
}

func extractSemanticFields(tree map[string]interface{}) map[string]string {
	out := make(map[string]string, len(semanticGateFields)+len(semanticEnforcementFields))
	for _, f := range semanticGateFields {
		out[f] = getStringField(tree, f)
	}
	// Fallback: verdict sometimes only appears inside the enforcement envelope.
	if out["verdict"] == "" {
		if enf, ok := tree["enforcement"].(map[string]interface{}); ok {
			out["verdict"] = getStringField(enf, "verdict")
		}
	}
	enf, _ := tree["enforcement"].(map[string]interface{})
	for _, f := range semanticEnforcementFields {
		if enf != nil {
			out["enforcement."+f] = getStringField(enf, f)
		} else {
			out["enforcement."+f] = ""
		}
	}
	return out
}

func getStringField(m map[string]interface{}, key string) string {
	if m == nil {
		return ""
	}
	if v, ok := m[key].(string); ok {
		return v
	}
	return ""
}

// structuralNormalize decodes the canonical response JSON, replaces every
// occurrence of the wall-clock / per-process fields with a fixed placeholder,
// and re-marshals via CanonicalMarshal so the output is deterministic and
// byte-stable across independent processes. Used for transparency-only hash
// reporting; the match gate uses semantic parity.
func structuralNormalize(canonicalBytes []byte) ([]byte, error) {
	if len(canonicalBytes) == 0 {
		return nil, fmt.Errorf("empty_bytes")
	}
	var tree interface{}
	if err := json.Unmarshal(canonicalBytes, &tree); err != nil {
		return nil, fmt.Errorf("unmarshal: %w", err)
	}
	neutralized := replaceNormalizedFields(tree)
	return CanonicalMarshal(neutralized)
}

func replaceNormalizedFields(v interface{}) interface{} {
	switch t := v.(type) {
	case map[string]interface{}:
		out := make(map[string]interface{}, len(t))
		for k, vv := range t {
			if _, ok := shadowNormalizedFields[k]; ok {
				out[k] = shadowPlaceholder
				continue
			}
			if _, ok := shadowNormalizedChainKeys[k]; ok {
				if arr, ok := vv.([]interface{}); ok && len(arr) > 0 {
					normed := make([]interface{}, len(arr))
					for i, el := range arr {
						normed[i] = replaceNormalizedFields(el)
					}
					normed[len(normed)-1] = shadowPlaceholder
					out[k] = normed
					continue
				}
			}
			out[k] = replaceNormalizedFields(vv)
		}
		return out
	case []interface{}:
		out := make([]interface{}, len(t))
		for i, vv := range t {
			out[i] = replaceNormalizedFields(vv)
		}
		return out
	default:
		return v
	}
}
