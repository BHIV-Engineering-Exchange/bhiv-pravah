package main

// cet_enforcement_artifact.go — Sarathi's enforcement-boundary artifacts for
// the TANTRA convergence chain.
//
// Produces exactly the two artifact shapes the TANTRA convergence packet
// requires:
//
//   1. SarathiEnforcementDecisionArtifact — the accepted-path artifact
//      (system_name=Sarathi, artifact_type=enforcement_decision, boundary
//      CET->Sarathi, decision=allow, contract_continuity proof, …).
//
//   2. SarathiTraceBoundRejectionArtifact — the fail-closed rejection artifact
//      (canonical_chain_identity.md §Rejection Visibility Requirement:
//      echoes the locked identifiers, validation_status=rejected,
//      rejection_reason, fail_closed=true).
//
// Both carry the locked identity verbatim. The artifacts contain ZERO Sarathi
// internal-architecture detail — they are pure boundary evidence records,
// re-verifiable by any party holding the locked chain identity.
//
// TAG: tantra-convergence-v1

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// CETArtifactDir is where convergence artifacts are persisted (append-only +
// one file per artifact for easy hand-off).
const CETArtifactDir = "proof_logs/tantra_convergence"

// CETEnforcementArtifactLog is the append-only JSONL of every emitted
// enforcement_decision artifact.
const CETEnforcementArtifactLog = "proof_logs/tantra_convergence/sarathi_enforcement_decisions.jsonl"

// CETRejectionArtifactLog is the append-only JSONL of every emitted rejection.
const CETRejectionArtifactLog = "proof_logs/tantra_convergence/sarathi_rejections.jsonl"

// SarathiEnforcementDecisionArtifact is the accepted-path artifact. JSON field
// order matches the TANTRA packet template.
type SarathiEnforcementDecisionArtifact struct {
	SystemName                string                `json:"system_name"`
	ArtifactType              string                `json:"artifact_type"`
	SchemaVersion             string                `json:"schema_version"`
	ContractVersion           string                `json:"contract_version"`
	ExecutionID               string                `json:"execution_id"`
	TraceID                   string                `json:"trace_id"`
	CETHash                   string                `json:"cet_hash"`
	BucketKey                 string                `json:"bucket_key"`
	Boundary                  string                `json:"boundary"`
	Decision                  string                `json:"decision"`
	EnforcementStatus         string                `json:"enforcement_status"`
	EnforcementTokenReference string                `json:"enforcement_token_reference"`
	ContractContinuity        CETContractContinuity `json:"contract_continuity"`
	// SarathiSealHash is Sarathi's own seal over the received SUM-SCRIPT
	// (mutation-detection anchor). Distinct from cet_hash.
	SarathiSealHash string `json:"sarathi_seal_hash"`
	// CETHashVerificationMode records HOW cet_hash was verified at this
	// boundary: "recompute+continuity" when CET supplied the pre-image,
	// "continuity" otherwise. Honest and explicit — never overstated.
	CETHashVerificationMode string `json:"cet_hash_verification_mode"`
	Provenance              string `json:"provenance"`
	TimestampUTC            string `json:"timestamp_utc"`
}

// SarathiTraceBoundRejectionArtifact is the fail-closed rejection artifact.
type SarathiTraceBoundRejectionArtifact struct {
	SystemName       string `json:"system_name"`
	ArtifactType     string `json:"artifact_type"`
	ExecutionID      string `json:"execution_id"`
	TraceID          string `json:"trace_id"`
	CETHash          string `json:"cet_hash"`
	Boundary         string `json:"boundary"`
	ValidationStatus string `json:"validation_status"`
	Decision         string `json:"decision"`
	ErrorCode        string `json:"error_code"`
	RejectionReason  string `json:"rejection_reason"`
	FailClosed       bool   `json:"fail_closed"`
	Provenance       string `json:"provenance"`
	TimestampUTC     string `json:"timestamp_utc"`
}

// CETArtifactProvenance is the source attribution string stamped on every
// artifact. No internal architecture — just the producing boundary identity.
const CETArtifactProvenance = "sarathi.enforcement_adapter@CET->Sarathi"

// BuildEnforcementDecisionArtifact assembles the accepted-path artifact from a
// successful boundary verification plus the enforcement token reference.
func BuildEnforcementDecisionArtifact(
	res *CETVerifierResult,
	enforcementTokenReference string,
	now time.Time,
) *SarathiEnforcementDecisionArtifact {
	mode := "continuity"
	if res.CETHashRecomputed {
		mode = "recompute+continuity"
	}
	status := "authorized"
	if res.Decision != CETDecisionAllow {
		status = "not_authorized"
	}
	return &SarathiEnforcementDecisionArtifact{
		SystemName:                "Sarathi",
		ArtifactType:              "enforcement_decision",
		SchemaVersion:             res.SumScript.SchemaVersion,
		ContractVersion:           res.SumScript.ContractVersion,
		ExecutionID:               res.SumScript.ExecutionID,
		TraceID:                   res.SumScript.TraceID,
		CETHash:                   res.SumScript.CETHash,
		BucketKey:                 res.SumScript.BucketKey,
		Boundary:                  CETBoundaryName,
		Decision:                  string(res.Decision),
		EnforcementStatus:         status,
		EnforcementTokenReference: enforcementTokenReference,
		ContractContinuity:        res.Continuity,
		SarathiSealHash:           res.SealHash,
		CETHashVerificationMode:   mode,
		Provenance:                CETArtifactProvenance,
		TimestampUTC:              now.UTC().Format(time.RFC3339Nano),
	}
}

// BuildTraceBoundRejectionArtifact assembles the fail-closed rejection artifact
// from a *CETValidationError.
func BuildTraceBoundRejectionArtifact(verr *CETValidationError, now time.Time) *SarathiTraceBoundRejectionArtifact {
	reason := verr.Detail
	if verr.InnerCode != "" {
		reason = fmt.Sprintf("[%s] %s", verr.InnerCode, verr.Detail)
	}
	return &SarathiTraceBoundRejectionArtifact{
		SystemName:       "Sarathi",
		ArtifactType:     "enforcement_rejection",
		ExecutionID:      verr.ExecutionID,
		TraceID:          verr.TraceID,
		CETHash:          verr.CETHash,
		Boundary:         CETBoundaryName,
		ValidationStatus: "rejected",
		Decision:         "reject",
		ErrorCode:        verr.Code,
		RejectionReason:  reason,
		FailClosed:       true,
		Provenance:       CETArtifactProvenance,
		TimestampUTC:     now.UTC().Format(time.RFC3339Nano),
	}
}

// PersistEnforcementDecisionArtifact appends the artifact to the JSONL log and
// also writes a standalone file keyed by execution_id for clean hand-off.
// Returns the standalone file path.
func PersistEnforcementDecisionArtifact(a *SarathiEnforcementDecisionArtifact) (string, error) {
	if err := cetAppendJSONLine(CETEnforcementArtifactLog, a); err != nil {
		return "", err
	}
	standalone := filepath.Join(CETArtifactDir, fmt.Sprintf("enforcement_decision_%s.json", safeFileToken(a.ExecutionID)))
	if err := writeIndentedJSON(standalone, a); err != nil {
		return "", err
	}
	return standalone, nil
}

// PersistTraceBoundRejectionArtifact appends + writes a standalone rejection.
func PersistTraceBoundRejectionArtifact(a *SarathiTraceBoundRejectionArtifact) (string, error) {
	if err := cetAppendJSONLine(CETRejectionArtifactLog, a); err != nil {
		return "", err
	}
	token := safeFileToken(a.ExecutionID)
	if token == "" {
		token = "no-execution-id"
	}
	standalone := filepath.Join(CETArtifactDir, fmt.Sprintf("rejection_%s_%s.json", token, a.ErrorCode))
	if err := writeIndentedJSON(standalone, a); err != nil {
		return "", err
	}
	return standalone, nil
}

// ============================================================================
// small shared persistence helpers (local to the convergence package surface)
// ============================================================================

func cetAppendJSONLine(path string, v interface{}) error {
	if dir := filepath.Dir(path); dir != "" && dir != "." {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return fmt.Errorf("mkdir %s: %w", dir, err)
		}
	}
	// SetEscapeHTML(false) so identifiers like "CET->Sarathi" are written
	// literally rather than as ">" — these artifacts are handed to an
	// external team and must read cleanly.
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		return fmt.Errorf("marshal: %w", err)
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return fmt.Errorf("open %s: %w", path, err)
	}
	defer f.Close()
	if _, err := f.Write(buf.Bytes()); err != nil { // Encode already appends '\n'
		return fmt.Errorf("write %s: %w", path, err)
	}
	return f.Sync()
}

func writeIndentedJSON(path string, v interface{}) error {
	if dir := filepath.Dir(path); dir != "" && dir != "." {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return fmt.Errorf("mkdir %s: %w", dir, err)
		}
	}
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", "  ")
	if err := enc.Encode(v); err != nil {
		return fmt.Errorf("marshal: %w", err)
	}
	return os.WriteFile(path, buf.Bytes(), 0o644)
}

// safeFileToken sanitizes an identifier for use in a filename.
func safeFileToken(s string) string {
	out := make([]rune, 0, len(s))
	for _, r := range s {
		switch {
		case r >= 'a' && r <= 'z', r >= 'A' && r <= 'Z', r >= '0' && r <= '9', r == '-', r == '_':
			out = append(out, r)
		default:
			out = append(out, '_')
		}
	}
	return string(out)
}
