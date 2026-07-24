package main

// translation_tantra_to_external_decision.go — Project a verified TANTRA
// decision into Sarathi's existing 16-field ExternalDecision so the rest of
// the PDP / propagation pipeline runs unchanged.
//
// SCOPING DECISION (per plan, user-confirmed): only the inbound surface
// changes. Everything from this point forward (envelope, peer receipts,
// response contract, propagation chain) stays on the existing schemas.
// This file is the bridge between the new contract and the old pipeline.
//
// TRANSLATION RULES:
//
//   TANTRA field            ExternalDecision field
//   --------------------    ----------------------------------------------
//   schema_version          Metadata["tantra_schema_version"]
//   trace_id                Metadata["trace_id"]
//   input_hash              Metadata["input_hash"]
//   decision_id             DecisionID                       (verified upstream)
//   decision_hash           Metadata["tantra_decision_hash"] (six-field hash)
//   verdict                 Verdict                          (ALLOW/DENY/ESCALATE)
//   policy_reference        Metadata["policy_reference"] + derived Action
//   evaluator_id            EvaluatorID
//   enforcement_binding     Reason                            (CLEARED/BLOCKED string)
//   timestamp               Timestamp                         (RFC3339 UTC -> time.Time)
//   signature               (verified upstream, dropped here)
//
// SARATHI-LOCAL DERIVATIONS:
//   agent_id    = evaluator_id           (Sovereign is the "agent" for the
//                                         pipeline's purposes; the real agent
//                                         identity lives in upstream context
//                                         which Sarathi does not see)
//   resource_id = evaluator_id           (same reasoning)
//   action      = deriveAction(policy_reference)
//   ttl         = SovereignTranslationDefaultTTL constant carried forward
//   nonce       = first 32 hex chars of tantra_decision_hash
//   obligations = []
//
// After projection, the existing 16-field ExternalDecision is fully populated
// and its computeHash() / computeCoreHash() produce stable values. The
// signature on the ExternalDecision is set to the TANTRA signature bytes —
// the existing pipeline verifies it would re-validate (it doesn't, because
// the TANTRA verifier has already verified it) — but the signature field is
// populated so audit downstream can reproduce it.
//
// TAG: tantra-v15.7

import (
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// SovereignTranslationDefaultTTL is the TTL applied to every translated
// ExternalDecision. Re-declared in case the old translation_sovereign_to_sarathi.go
// gets removed before this file lands. Mirrored from the contract default.
const TantraTranslationDefaultTTL = 30 * time.Second

// TantraTranslationAuditLog records every projection event for the
// translation-loss CLI to verify against.
const TantraTranslationAuditLog = "proof_logs/tantra_translation_map.jsonl"

// TranslateTantraToExternalDecision projects a verified TANTRA decision into
// the existing 16-field ExternalDecision. Caller is the HTTP handler in
// service_boundary_tantra.go AFTER the 12-step verifier has accepted the
// payload.
//
// Preconditions:
//   - d != nil
//   - d.Decision is fully populated (the verifier returns it on success)
//   - signature bytes verified by tantra_verifier.go step 7
//
// Postconditions:
//   - returned ExternalDecision passes ValidateStructure()
//   - DecisionHash + DecisionCoreHash are recomputed fresh
//   - one row appended to TantraTranslationAuditLog (best-effort, non-fatal)
func TranslateTantraToExternalDecision(result *TantraVerifierResult) (*ExternalDecision, error) {
	if result == nil || result.Decision == nil {
		return nil, fmt.Errorf("tantra_translation: nil result")
	}
	d := result.Decision

	tsParsed, err := parseTantraTimestamp(d.Timestamp)
	if err != nil {
		return nil, fmt.Errorf("tantra_translation: timestamp: %w", err)
	}
	ttl := loadTantraTranslationTTL()
	expires := tsParsed.Add(ttl)

	metadata := map[string]string{
		"tantra_schema_version":  d.SchemaVersion,
		"trace_id":               d.TraceID,
		"input_hash":             d.InputHash,
		"tantra_decision_hash":   d.DecisionHash,
		"policy_reference":       d.PolicyReference,
		"enforcement_binding":    d.EnforcementBinding,
		"tantra_signature_alg":   d.Signature.Alg,
		"tantra_signature_keyid": d.Signature.KeyID,
		"translation_version":    "tantra-v15.7",
		"recomputed_decision_id":   result.RecomputedDecisionID,
		"recomputed_decision_hash": result.RecomputedDecisionHash,
	}

	action := deriveActionFromPolicyReference(d.PolicyReference)
	verdict := ExternalDecisionVerdict(d.Verdict)

	out := &ExternalDecision{
		DecisionID:  d.DecisionID,
		EvaluatorID: d.EvaluatorID,
		AgentID:     d.EvaluatorID,
		ResourceID:  d.EvaluatorID,
		Action:      action,
		Verdict:     verdict,
		Obligations: []string{},
		Timestamp:   tsParsed,
		TTL:         ttl,
		ExpiresAt:   expires,
		Metadata:    metadata,
		Reason:      d.EnforcementBinding,
		Nonce:       deriveTantraNonce(d.DecisionHash),
	}

	// Recompute hashes fresh — pipeline will re-derive them and the equality
	// check passes because we use the same helpers.
	out.DecisionHash = out.computeHash()
	out.DecisionCoreHash = out.computeCoreHash()

	// Carry the TANTRA signature bytes through. The existing pipeline's
	// VerifySignature call site has been routed through the active crypto
	// provider, so it will be able to re-verify if a downstream consumer asks.
	sigBytes, err := decodeBase64URLNoPad(d.Signature.Value)
	if err == nil {
		out.EvaluatorSignature = sigBytes
		out.EvaluatorSignatureHex = hex.EncodeToString(sigBytes)
	}

	if err := out.ValidateStructure(); err != nil {
		return nil, fmt.Errorf("tantra_translation: post-build structure invalid: %w", err)
	}
	appendTantraTranslationAudit(d, out, result)
	return out, nil
}

// deriveActionFromPolicyReference mirrors the existing heuristic used in the
// (now-removed) translation_sovereign_to_sarathi.go. Maps policy_reference
// substrings to one of read/write/execute/delete with a default of "execute".
//
// This kept identical to the legacy behaviour so the downstream pipeline's
// posture/rate checks see the same Action distribution they did pre-TANTRA.
func deriveActionFromPolicyReference(policyReference string) string {
	p := strings.ToLower(policyReference)
	switch {
	case strings.Contains(p, ".read") || strings.Contains(p, "_read") || strings.HasSuffix(p, "/read"):
		return "read"
	case strings.Contains(p, ".write") || strings.Contains(p, "_write") || strings.HasSuffix(p, "/write"):
		return "write"
	case strings.Contains(p, ".delete") || strings.Contains(p, "_delete") || strings.HasSuffix(p, "/delete"):
		return "delete"
	default:
		return "execute"
	}
}

// deriveTantraNonce returns the first 32 hex characters of decision_hash, or
// a SHA-256 hash thereof if decision_hash is too short. Same shape as the
// legacy translator so the existing replay store key is unchanged.
func deriveTantraNonce(decisionHash string) string {
	clean := strings.TrimSpace(decisionHash)
	if len(clean) >= 32 {
		return clean[:32]
	}
	h := sha256.Sum256([]byte(clean))
	return hex.EncodeToString(h[:])[:32]
}

// loadTantraTranslationTTL reads SARATHI_TANTRA_DEFAULT_TTL_S (or the legacy
// SARATHI_SOVEREIGN_DEFAULT_TTL_S for compatibility) and returns the
// duration. Falls back to the constant default.
func loadTantraTranslationTTL() time.Duration {
	for _, env := range []string{"SARATHI_TANTRA_DEFAULT_TTL_S", "SARATHI_SOVEREIGN_DEFAULT_TTL_S"} {
		raw := strings.TrimSpace(os.Getenv(env))
		if raw == "" {
			continue
		}
		var n int
		if _, err := fmt.Sscanf(raw, "%d", &n); err == nil && n > 0 && n <= 24*60*60 {
			return time.Duration(n) * time.Second
		}
	}
	return TantraTranslationDefaultTTL
}

func decodeBase64URLNoPad(s string) ([]byte, error) {
	clean := strings.TrimSpace(s)
	if clean == "" {
		return nil, fmt.Errorf("empty signature value")
	}
	return base64.RawURLEncoding.DecodeString(clean)
}

// ============================================================================
// AUDIT
// ============================================================================

type tantraTranslationAuditRow struct {
	Timestamp              string `json:"ts"`
	TraceID                string `json:"trace_id"`
	TantraSchemaVersion    string `json:"tantra_schema_version"`
	InputHash              string `json:"input_hash"`
	EvaluatorID            string `json:"evaluator_id"`
	TantraDecisionID       string `json:"tantra_decision_id"`
	TantraDecisionHash     string `json:"tantra_decision_hash"`
	RecomputedDecisionHash string `json:"recomputed_decision_hash"`
	RecomputedDecisionID   string `json:"recomputed_decision_id"`
	SarathiDecisionID      string `json:"sarathi_decision_id"`
	SarathiDecisionHash    string `json:"sarathi_decision_hash"`
	SarathiCoreHash        string `json:"sarathi_decision_core_hash"`
	Verdict                string `json:"verdict"`
	Action                 string `json:"action"`
	EnforcementBinding     string `json:"enforcement_binding"`
	SignatureAlg           string `json:"signature_alg"`
	SignatureKeyID         string `json:"signature_key_id"`
}

func appendTantraTranslationAudit(tantra *TantraDecision, sarathi *ExternalDecision, result *TantraVerifierResult) {
	dir := filepath.Dir(TantraTranslationAuditLog)
	if dir != "" && dir != "." {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			fmt.Fprintf(os.Stderr, "[tantra_translation] WARN: mkdir audit: %v\n", err)
			return
		}
	}
	row := tantraTranslationAuditRow{
		Timestamp:              time.Now().UTC().Format(time.RFC3339Nano),
		TraceID:                tantra.TraceID,
		TantraSchemaVersion:    tantra.SchemaVersion,
		InputHash:              tantra.InputHash,
		EvaluatorID:            tantra.EvaluatorID,
		TantraDecisionID:       tantra.DecisionID,
		TantraDecisionHash:     tantra.DecisionHash,
		RecomputedDecisionHash: result.RecomputedDecisionHash,
		RecomputedDecisionID:   result.RecomputedDecisionID,
		SarathiDecisionID:      sarathi.DecisionID,
		SarathiDecisionHash:    sarathi.DecisionHash,
		SarathiCoreHash:        sarathi.DecisionCoreHash,
		Verdict:                string(sarathi.Verdict),
		Action:                 sarathi.Action,
		EnforcementBinding:     tantra.EnforcementBinding,
		SignatureAlg:           tantra.Signature.Alg,
		SignatureKeyID:         tantra.Signature.KeyID,
	}
	raw, err := json.Marshal(&row)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[tantra_translation] WARN: marshal audit row: %v\n", err)
		return
	}
	raw = append(raw, '\n')
	f, err := os.OpenFile(TantraTranslationAuditLog, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[tantra_translation] WARN: open audit: %v\n", err)
		return
	}
	defer f.Close()
	_, _ = f.Write(raw)
}
