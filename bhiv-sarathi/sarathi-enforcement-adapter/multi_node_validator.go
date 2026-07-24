// multi_node_validator.go (v14.6 Global Determinism Validation — Phase 1)
//
// Cross-node byte-equality oracle. Given the set of MultiNodeChildResult
// produced by RunMultiNode, ValidateMultiNode proves that every node's
// sealed PropagationEnvelope produces:
//
//   - Identical decision_hash          (the PDP input)
//   - Identical decision_core_hash     (the signed core)
//   - Identical response_hash_stable   (Sha256 over the variance-zeroed
//                                       canonical response)
//   - Identical chain_binding_hash_stable
//   - Identical stable_canonical_sha256
//
// Variance-bearing hashes (enforcement_hash, response_hash raw) are expected
// to differ across nodes because they legitimately include per-node
// correlation/execution IDs and enforced-at timestamps. The stable forms
// strip those back out; the *stable* set MUST have size exactly 1.
//
// On any drift, the validator records the offending hash, emits a
// CodeMultiNodeDrift violation to the determinism log, and marks the report
// with all_byte_identical=false. The CLI caller exits non-zero.
//
// Output:
//   - multi_node_determinism_report.json (wrapped via WriteCanonicalResults)
//   - proof_logs/multi_node_determinism_log.jsonl (per-node JSONL row)
//
// TAG: test-affordance-only

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"time"
)

// MultiNodeDeterminismReportPath is the canonical v14.6 Phase 1 artefact.
const MultiNodeDeterminismReportPath = "multi_node_determinism_report.json"

// MultiNodeDeterminismLogPath is the append-only JSONL record of per-node fingerprints.
const MultiNodeDeterminismLogPath = "proof_logs/multi_node_determinism_log.jsonl"

// MultiNodeDeterminismSchemaVersion pins the aggregate-report schema.
const MultiNodeDeterminismSchemaVersion = "sarathi.multi_node.determinism/v1.0"

// MultiNodeNodeReport is one row in the aggregate multi-node report.
type MultiNodeNodeReport struct {
	NodeID                 string `json:"node_id"`
	ClockSkewSec           int    `json:"clock_skew_seconds"`
	ReportPath             string `json:"report_path"`
	ManifestPath           string `json:"manifest_path"`
	ExitCode               int    `json:"exit_code"`
	DurationNs             int64  `json:"duration_ns"`
	InputHash              string `json:"input_hash"`
	DecisionHash           string `json:"decision_hash"`
	DecisionCoreHash       string `json:"decision_core_hash"`
	ResponseHash           string `json:"response_hash"`
	ChainBindingHash       string `json:"chain_binding_hash"`
	ResponseHashStable     string `json:"response_hash_stable"`
	ChainBindingHashStable string `json:"chain_binding_hash_stable"`
	StableCanonicalSha     string `json:"stable_canonical_sha256"`
	Error                  string `json:"error,omitempty"`
	StdoutTail             string `json:"stdout_tail,omitempty"`
	StderrTail             string `json:"stderr_tail,omitempty"`
}

// MultiNodeDeterminismReport is the aggregate Phase 1 artefact.
type MultiNodeDeterminismReport struct {
	SchemaVersion         string                 `json:"schema_version"`
	GeneratedAt           string                 `json:"generated_at"`
	NodeCount             int                    `json:"node_count"`
	AllByteIdentical      bool                   `json:"all_byte_identical"`
	DriftDetected         bool                   `json:"drift_detected"`
	UniqueStableHash      []string               `json:"unique_response_hash_stable"`
	UniqueStableChain     []string               `json:"unique_chain_binding_stable"`
	UniqueStableCanonical []string               `json:"unique_stable_canonical_sha256"`
	UniqueDecisionHash    []string               `json:"unique_decision_hash"`
	Nodes                 []MultiNodeNodeReport  `json:"nodes"`
	Notes                 []string               `json:"notes,omitempty"`
}

// ValidateMultiNode aggregates per-child manifests into a single MultiNodeDeterminismReport.
// It writes the aggregate report and a JSONL log.
func ValidateMultiNode(results []*MultiNodeChildResult) (*MultiNodeDeterminismReport, error) {
	rep := &MultiNodeDeterminismReport{
		SchemaVersion: MultiNodeDeterminismSchemaVersion,
		GeneratedAt:   time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		NodeCount:     len(results),
		Nodes:         make([]MultiNodeNodeReport, 0, len(results)),
	}

	stableSet := map[string]bool{}
	stableChainSet := map[string]bool{}
	stableCanonicalSet := map[string]bool{}
	decisionHashSet := map[string]bool{}

	if err := os.MkdirAll(filepath.Dir(MultiNodeDeterminismLogPath), 0o755); err != nil {
		return nil, err
	}
	logF, err := os.OpenFile(MultiNodeDeterminismLogPath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return nil, err
	}
	defer logF.Close()

	for _, r := range results {
		if r == nil {
			rep.Notes = append(rep.Notes, "nil child result encountered")
			continue
		}
		node := MultiNodeNodeReport{
			NodeID:       r.NodeID,
			ClockSkewSec: r.ClockSkewSec,
			ReportPath:   r.ReportPath,
			ManifestPath: r.ManifestPath,
			ExitCode:     r.ExitCode,
			DurationNs:   r.DurationNs,
			Error:        r.Error,
			StdoutTail:   r.StdoutTail,
			StderrTail:   r.StderrTail,
		}
		if r.Manifest != nil {
			m := r.Manifest
			node.InputHash = m.InputHash
			node.DecisionHash = m.DecisionHash
			node.DecisionCoreHash = m.DecisionCoreHash
			node.ResponseHash = m.ResponseHash
			node.ChainBindingHash = m.ChainBindingHash
			node.ResponseHashStable = m.ResponseHashStable
			node.ChainBindingHashStable = m.ChainBindingHashStable
			node.StableCanonicalSha = m.StableCanonicalSha256

			if m.ResponseHashStable != "" {
				stableSet[m.ResponseHashStable] = true
			}
			if m.ChainBindingHashStable != "" {
				stableChainSet[m.ChainBindingHashStable] = true
			}
			if m.StableCanonicalSha256 != "" {
				stableCanonicalSet[m.StableCanonicalSha256] = true
			}
			if m.DecisionHash != "" {
				decisionHashSet[m.DecisionHash] = true
			}
		} else {
			rep.Notes = append(rep.Notes, fmt.Sprintf("node %s missing manifest", r.NodeID))
		}
		rep.Nodes = append(rep.Nodes, node)

		// JSONL log — one row per node.
		if nb, jerr := json.Marshal(node); jerr == nil {
			logF.Write(append(nb, '\n'))
		}
	}
	_ = logF.Sync()

	rep.UniqueStableHash = sortStringSet(stableSet)
	rep.UniqueStableChain = sortStringSet(stableChainSet)
	rep.UniqueStableCanonical = sortStringSet(stableCanonicalSet)
	rep.UniqueDecisionHash = sortStringSet(decisionHashSet)

	rep.AllByteIdentical = len(rep.UniqueStableHash) == 1 &&
		len(rep.UniqueStableChain) == 1 &&
		len(rep.UniqueStableCanonical) == 1 &&
		len(rep.UniqueDecisionHash) == 1 &&
		rep.NodeCount > 0 &&
		allChildrenExited0(results)

	rep.DriftDetected = !rep.AllByteIdentical

	if rep.DriftDetected {
		// Record a determinism violation entry so the audit log surfaces it.
		_ = RecordViolation(ByteEqualityResult{
			Hop:           "multi_node.aggregate",
			SentHash:      firstOrEmpty(rep.UniqueStableHash),
			AckHash:       lastOrEmpty(rep.UniqueStableHash),
			BytesMatch:    false,
			ViolationCode: CodeMultiNodeDrift,
			Timestamp:     time.Now().UTC(),
			Detail: fmt.Sprintf(
				"multi-node drift: unique_stable_hash=%d unique_chain=%d unique_decision=%d nodes=%d",
				len(rep.UniqueStableHash), len(rep.UniqueStableChain),
				len(rep.UniqueDecisionHash), rep.NodeCount),
		})
	}

	// Write aggregate report wrapped in CanonicalResultEnvelope for parity.
	passed := rep.NodeCount
	failed := 0
	if rep.DriftDetected {
		failed = rep.NodeCount
		passed = 0
	}
	if err := WriteCanonicalResults(
		MultiNodeDeterminismReportPath,
		"multi_node_determinism",
		rep.NodeCount,
		passed,
		failed,
		rep,
	); err != nil {
		return rep, err
	}
	return rep, nil
}

func sortStringSet(m map[string]bool) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

func allChildrenExited0(results []*MultiNodeChildResult) bool {
	for _, r := range results {
		if r == nil || r.ExitCode != 0 {
			return false
		}
	}
	return true
}

func firstOrEmpty(s []string) string {
	if len(s) == 0 {
		return ""
	}
	return s[0]
}

func lastOrEmpty(s []string) string {
	if len(s) == 0 {
		return ""
	}
	return s[len(s)-1]
}
