// v14_6_audit_harness.go (v14.6 Global Determinism Validation — Audit Pass)
//
// Independent verifier. Re-opens every v14.6 artefact, parses the payload
// (peeling the CanonicalResultEnvelope when present), and asserts the
// success markers required by task.md §AUDIT. Failure causes the process
// (invoked via `--v14-6-audit`) to exit non-zero; success emits
// audit_v14_6_report.md summarising every verdict.
//
// This harness must NEVER share mutable state with the phase harnesses —
// it only reads files. That is intentional: the auditor's claim is "every
// on-disk artefact contains the values task.md demands".
//
// TAG: test-affordance-only

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// V14_6AuditReportPath is the human-readable audit summary.
const V14_6AuditReportPath = "audit_v14_6_report.md"

// V14_6AuditSchemaVersion pins the JSON summary schema.
const V14_6AuditSchemaVersion = "sarathi.audit.v14_6/v1.0"

// V14_6AuditJSONPath is the machine-readable audit summary.
const V14_6AuditJSONPath = "audit_v14_6_report.json"

// V14_6AuditCheck records one success-marker assertion.
type V14_6AuditCheck struct {
	Artefact   string `json:"artefact"`
	Field      string `json:"field"`
	Expected   string `json:"expected"`
	Got        string `json:"got"`
	Pass       bool   `json:"pass"`
	Comment    string `json:"comment,omitempty"`
}

// V14_6AuditReport is the aggregate audit verdict.
type V14_6AuditReport struct {
	SchemaVersion string              `json:"schema_version"`
	GeneratedAt   string              `json:"generated_at"`
	TotalChecks   int                 `json:"total_checks"`
	PassedChecks  int                 `json:"passed_checks"`
	FailedChecks  int                 `json:"failed_checks"`
	AllPassed     bool                `json:"all_passed"`
	Checks        []V14_6AuditCheck   `json:"checks"`
	Notes         []string            `json:"notes,omitempty"`
}

// RunV14_6Audit reads every v14.6 artefact and writes the audit report.
func RunV14_6Audit() (*V14_6AuditReport, error) {
	printHeader("v14.6 AUDIT HARNESS")
	fmt.Println("  Re-opening every artefact and asserting task.md success markers")
	fmt.Println()

	rep := &V14_6AuditReport{
		SchemaVersion: V14_6AuditSchemaVersion,
		GeneratedAt:   time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
	}

	// 1. multi_node_determinism_report.json -------------------------------
	if payload, err := loadEnvelopeResults(MultiNodeDeterminismReportPath); err == nil {
		var m MultiNodeDeterminismReport
		if err := json.Unmarshal(payload, &m); err == nil {
			rep.addCheck(V14_6AuditCheck{
				Artefact: MultiNodeDeterminismReportPath,
				Field:    "all_byte_identical",
				Expected: "true",
				Got:      fmt.Sprintf("%t", m.AllByteIdentical),
				Pass:     m.AllByteIdentical,
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: MultiNodeDeterminismReportPath,
				Field:    "len(unique_response_hash_stable)",
				Expected: "1",
				Got:      fmt.Sprintf("%d", len(m.UniqueStableHash)),
				Pass:     len(m.UniqueStableHash) == 1,
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: MultiNodeDeterminismReportPath,
				Field:    "node_count",
				Expected: ">=3",
				Got:      fmt.Sprintf("%d", m.NodeCount),
				Pass:     m.NodeCount >= 3,
			})
		} else {
			rep.addCheck(failedParse(MultiNodeDeterminismReportPath, err))
		}
	} else {
		rep.addCheck(missing(MultiNodeDeterminismReportPath, err))
	}

	// 2. clock_drift_results.json -----------------------------------------
	if payload, err := loadEnvelopeResults(ClockDriftReportPath); err == nil {
		var m ClockDriftReport
		if err := json.Unmarshal(payload, &m); err == nil {
			rep.addCheck(V14_6AuditCheck{
				Artefact: ClockDriftReportPath,
				Field:    "unique_stable_hash_set_size",
				Expected: "1",
				Got:      fmt.Sprintf("%d", m.UniqueStableHashSetSize),
				Pass:     m.UniqueStableHashSetSize == 1,
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: ClockDriftReportPath,
				Field:    "drift_detected",
				Expected: "false",
				Got:      fmt.Sprintf("%t", m.DriftDetected),
				Pass:     !m.DriftDetected,
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: ClockDriftReportPath,
				Field:    "scenario_count",
				Expected: ">=7",
				Got:      fmt.Sprintf("%d", m.ScenarioCount),
				Pass:     m.ScenarioCount >= 7,
			})
		} else {
			rep.addCheck(failedParse(ClockDriftReportPath, err))
		}
	} else {
		rep.addCheck(missing(ClockDriftReportPath, err))
	}

	// 3. transport_integrity_report.json ----------------------------------
	if payload, err := loadEnvelopeResults(TransportIntegrityReportPath); err == nil {
		var m TransportIntegrityReport
		if err := json.Unmarshal(payload, &m); err == nil {
			accountedFor := len(m.ScenariosPassed) + len(m.ScenariosHaltedAsExpected)
			rep.addCheck(V14_6AuditCheck{
				Artefact: TransportIntegrityReportPath,
				Field:    "scenarios_passed + scenarios_halted_as_expected",
				Expected: "8",
				Got:      fmt.Sprintf("%d", accountedFor),
				Pass:     accountedFor == 8,
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: TransportIntegrityReportPath,
				Field:    "transport_integrity_verified",
				Expected: "true",
				Got:      fmt.Sprintf("%t", m.TransportIntegrityVerified),
				Pass:     m.TransportIntegrityVerified,
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: TransportIntegrityReportPath,
				Field:    "mismatched_expected",
				Expected: "0",
				Got:      fmt.Sprintf("%d", m.MismatchedExpected),
				Pass:     m.MismatchedExpected == 0,
			})
		} else {
			rep.addCheck(failedParse(TransportIntegrityReportPath, err))
		}
	} else {
		rep.addCheck(missing(TransportIntegrityReportPath, err))
	}

	// 4. bucket_state_verification_report.json ----------------------------
	if payload, err := loadEnvelopeResults(BucketStateReportPath); err == nil {
		var m BucketStateReport
		if err := json.Unmarshal(payload, &m); err == nil {
			rep.addCheck(V14_6AuditCheck{
				Artefact: BucketStateReportPath,
				Field:    "mismatches",
				Expected: "0",
				Got:      fmt.Sprintf("%d", m.Mismatches),
				Pass:     m.Mismatches == 0,
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: BucketStateReportPath,
				Field:    "matches",
				Expected: ">=100",
				Got:      fmt.Sprintf("%d", m.Matches),
				Pass:     m.Matches >= 100,
				Comment:  "task.md §PHASE 4 mandates 100 distinct decisions",
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: BucketStateReportPath,
				Field:    "bucket_state_verified",
				Expected: "true",
				Got:      fmt.Sprintf("%t", m.BucketStateVerified),
				Pass:     m.BucketStateVerified,
			})
		} else {
			rep.addCheck(failedParse(BucketStateReportPath, err))
		}
	} else {
		rep.addCheck(missing(BucketStateReportPath, err))
	}

	// 5. propagation_byte_equality_report_1000.json -----------------------
	if payload, err := loadEnvelopeResults(HighIterationReportPath); err == nil {
		var m PropagationReplayReport
		if err := json.Unmarshal(payload, &m); err == nil {
			rep.addCheck(V14_6AuditCheck{
				Artefact: HighIterationReportPath,
				Field:    "iterations",
				Expected: "1000",
				Got:      fmt.Sprintf("%d", m.Iterations),
				Pass:     m.Iterations == 1000,
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: HighIterationReportPath,
				Field:    "determinism_violations",
				Expected: "0",
				Got:      fmt.Sprintf("%d", m.DeterminismViolations),
				Pass:     m.DeterminismViolations == 0,
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: HighIterationReportPath,
				Field:    "len(unique_response_hashes)",
				Expected: "1",
				Got:      fmt.Sprintf("%d", len(m.UniqueResponseHashes)),
				Pass:     len(m.UniqueResponseHashes) == 1,
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: HighIterationReportPath,
				Field:    "all_byte_identical",
				Expected: "true",
				Got:      fmt.Sprintf("%t", m.AllByteIdentical),
				Pass:     m.AllByteIdentical,
			})
		} else {
			rep.addCheck(failedParse(HighIterationReportPath, err))
		}
	} else {
		rep.addCheck(missing(HighIterationReportPath, err))
	}

	// 6. cross_system_integration_report.json -----------------------------
	if payload, err := loadEnvelopeResults(CrossSystemIntegrationReportPath); err == nil {
		var m CrossSystemIntegrationReport
		if err := json.Unmarshal(payload, &m); err == nil {
			rep.addCheck(V14_6AuditCheck{
				Artefact: CrossSystemIntegrationReportPath,
				Field:    "cross_system_integration_verified",
				Expected: "true",
				Got:      fmt.Sprintf("%t", m.CrossSystemIntegrationVerified),
				Pass:     m.CrossSystemIntegrationVerified,
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: CrossSystemIntegrationReportPath,
				Field:    "bucket_readback_verified",
				Expected: "true",
				Got:      fmt.Sprintf("%t", m.BucketReadbackVerified),
				Pass:     m.BucketReadbackVerified,
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: CrossSystemIntegrationReportPath,
				Field:    "targets_verified",
				Expected: fmt.Sprintf("%d", m.TargetCount),
				Got:      fmt.Sprintf("%d", m.TargetsVerified),
				Pass:     m.TargetsVerified == m.TargetCount && m.TargetCount >= 3,
			})
		} else {
			rep.addCheck(failedParse(CrossSystemIntegrationReportPath, err))
		}
	} else {
		rep.addCheck(missing(CrossSystemIntegrationReportPath, err))
	}

	// 7. vc_demo_results.json ---------------------------------------------
	if payload, err := loadEnvelopeResults(VCDemoResultsPath); err == nil {
		var m VCDemoReport
		if err := json.Unmarshal(payload, &m); err == nil {
			rep.addCheck(V14_6AuditCheck{
				Artefact: VCDemoResultsPath,
				Field:    "demos_passed",
				Expected: "5",
				Got:      fmt.Sprintf("%d", m.DemosPassed),
				Pass:     m.DemosPassed == 5,
			})
			rep.addCheck(V14_6AuditCheck{
				Artefact: VCDemoResultsPath,
				Field:    "all_passed",
				Expected: "true",
				Got:      fmt.Sprintf("%t", m.AllPassed),
				Pass:     m.AllPassed,
			})
		} else {
			rep.addCheck(failedParse(VCDemoResultsPath, err))
		}
	} else {
		rep.addCheck(missing(VCDemoResultsPath, err))
	}

	// 8. determinism_violation_log.jsonl emptiness (v14.6 scope) ----------
	if emptyOK, lines := determinismViolationLogClean(); emptyOK {
		rep.addCheck(V14_6AuditCheck{
			Artefact: "proof_logs/determinism_violation_log.jsonl",
			Field:    "v14_6_entries",
			Expected: "0",
			Got:      "0",
			Pass:     true,
			Comment:  "no v14.6 violations recorded",
		})
	} else {
		rep.addCheck(V14_6AuditCheck{
			Artefact: "proof_logs/determinism_violation_log.jsonl",
			Field:    "v14_6_entries",
			Expected: "0",
			Got:      fmt.Sprintf("%d", lines),
			Pass:     false,
			Comment:  "determinism violations logged — inspect proof_logs/determinism_violation_log.jsonl",
		})
	}

	// Aggregate -----------------------------------------------------------
	rep.TotalChecks = len(rep.Checks)
	for _, c := range rep.Checks {
		if c.Pass {
			rep.PassedChecks++
		} else {
			rep.FailedChecks++
		}
	}
	rep.AllPassed = rep.FailedChecks == 0 && rep.TotalChecks > 0

	if err := writeAuditMarkdown(V14_6AuditReportPath, rep); err != nil {
		return rep, fmt.Errorf("audit: write markdown: %w", err)
	}
	if err := writeAuditJSON(V14_6AuditJSONPath, rep); err != nil {
		return rep, fmt.Errorf("audit: write json: %w", err)
	}

	fmt.Printf("\n  v14.6 Audit: %d/%d checks passed (all_passed=%t)\n",
		rep.PassedChecks, rep.TotalChecks, rep.AllPassed)
	if !rep.AllPassed {
		for _, c := range rep.Checks {
			if !c.Pass {
				fmt.Printf("    FAIL %s.%s expected=%s got=%s %s\n",
					c.Artefact, c.Field, c.Expected, c.Got, c.Comment)
			}
		}
	}
	return rep, nil
}

func (r *V14_6AuditReport) addCheck(c V14_6AuditCheck) {
	r.Checks = append(r.Checks, c)
}

// loadEnvelopeResults reads a file. If it parses as a CanonicalResultEnvelope,
// returns the inner `results` payload; otherwise returns the raw bytes.
func loadEnvelopeResults(path string) ([]byte, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var envelope struct {
		Results json.RawMessage `json:"results"`
	}
	if jerr := json.Unmarshal(b, &envelope); jerr == nil && len(envelope.Results) > 0 {
		return envelope.Results, nil
	}
	return b, nil
}

func failedParse(path string, err error) V14_6AuditCheck {
	return V14_6AuditCheck{
		Artefact: path,
		Field:    "parse",
		Expected: "valid JSON",
		Got:      err.Error(),
		Pass:     false,
	}
}

func missing(path string, err error) V14_6AuditCheck {
	return V14_6AuditCheck{
		Artefact: path,
		Field:    "exists",
		Expected: "present",
		Got:      "missing: " + errorOrEmpty(err),
		Pass:     false,
	}
}

func errorOrEmpty(err error) string {
	if err == nil {
		return ""
	}
	return err.Error()
}

// determinismViolationLogClean returns (true, 0) if the violation log is
// absent or contains zero JSONL entries with ViolationCode referring to the
// v14.6 scope. v14.5 fault-injection entries live in fault_injection_report.json
// and are excluded.
func determinismViolationLogClean() (bool, int) {
	const path = "proof_logs/determinism_violation_log.jsonl"
	b, err := os.ReadFile(path)
	if err != nil || len(b) == 0 {
		return true, 0
	}
	lines := strings.Split(strings.TrimSpace(string(b)), "\n")
	// Empty file (one empty line after trim) → clean.
	if len(lines) == 1 && lines[0] == "" {
		return true, 0
	}
	// Count only v14.6-scoped codes; anything else may be legitimate from
	// other harnesses and is ignored for audit purposes.
	v14_6Codes := map[string]bool{
		CodeTransportIntegrityViolation: true,
		CodeBucketReadbackMismatch:      true,
		CodeMultiNodeDrift:              true,
		CodeDeterminismViolation:        true,
		CodePropagationByteMismatch:     true,
		CodeResponseHashMismatch:        true,
		CodePropagationChainBroken:      true,
	}
	bad := 0
	for _, line := range lines {
		if line == "" {
			continue
		}
		var row map[string]interface{}
		if jerr := json.Unmarshal([]byte(line), &row); jerr != nil {
			continue
		}
		// Entries whose hop starts with "transport_" come from the transport
		// adversarial harness (either Phase 3 or VC demo D2) — those halts
		// are the success criterion of the adversarial test, not drift.
		hop, _ := row["hop"].(string)
		if strings.HasPrefix(hop, "transport_") {
			continue
		}
		vc, _ := row["violation_code"].(string)
		if vc == "" {
			vc, _ = row["ViolationCode"].(string)
		}
		if v14_6Codes[vc] {
			bad++
		}
	}
	return bad == 0, bad
}

func writeAuditMarkdown(path string, rep *V14_6AuditReport) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil && filepath.Dir(path) != "." {
		return err
	}
	var sb strings.Builder
	sb.WriteString("# Sarathi v14.6 — Audit Report\n\n")
	sb.WriteString("Generated: " + rep.GeneratedAt + "\n\n")
	sb.WriteString(fmt.Sprintf("**Total checks:** %d  **Passed:** %d  **Failed:** %d  **All passed:** %t\n\n",
		rep.TotalChecks, rep.PassedChecks, rep.FailedChecks, rep.AllPassed))
	sb.WriteString("| # | Artefact | Field | Expected | Got | Verdict |\n")
	sb.WriteString("|---|----------|-------|----------|-----|---------|\n")

	// Stable ordering: group by artefact then original insertion order.
	indexed := make([]V14_6AuditCheck, len(rep.Checks))
	copy(indexed, rep.Checks)
	sort.SliceStable(indexed, func(i, j int) bool {
		if indexed[i].Artefact != indexed[j].Artefact {
			return indexed[i].Artefact < indexed[j].Artefact
		}
		return false
	})
	for i, c := range indexed {
		mark := "PASS"
		if !c.Pass {
			mark = "FAIL"
		}
		sb.WriteString(fmt.Sprintf("| %d | `%s` | `%s` | `%s` | `%s` | %s |\n",
			i+1, c.Artefact, c.Field, c.Expected, c.Got, mark))
	}
	sb.WriteString("\n")
	if len(rep.Notes) > 0 {
		sb.WriteString("## Notes\n\n")
		for _, n := range rep.Notes {
			sb.WriteString("- " + n + "\n")
		}
	}
	return os.WriteFile(path, []byte(sb.String()), 0o644)
}

func writeAuditJSON(path string, rep *V14_6AuditReport) error {
	return WriteCanonicalResults(
		path,
		"v14_6_audit",
		rep.TotalChecks,
		rep.PassedChecks,
		rep.FailedChecks,
		rep,
	)
}
