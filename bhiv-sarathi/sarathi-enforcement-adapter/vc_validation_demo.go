// vc_validation_demo.go (v14.6 Global Determinism Validation — Phase 7)
//
// Scripted live-demo runner. Performs the five mandatory demonstrations:
//
//   D1  Multi-node deterministic execution      — 3 child nodes, one stable hash
//   D2  Transport mutation attempt → chain halt — proxy re-serialise halts the chain
//   D3  Successful propagation → identical hashes across Core/InsightFlow/Bucket
//   D4  Bucket read-back exact match            — 5 sampled decisions
//   D5  1000-iteration replay proof             — UniqueHashes==1, Violations==0
//
// Output:
//   - vc_demo_results.json
//   - vc_demo_session_log.jsonl
//   - review_packets/vc_validation_note_template.md  (emitted on first run)
//
// The runnable demo artefacts are Sarathi's deliverable. The actual live
// recording is owned by Vinayak Tiwari; this harness produces reproducible
// console output + a JSONL timeline his driver can replay offline.
//
// TAG: test-affordance-only

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// VCDemoResultsPath is the aggregate artefact.
const VCDemoResultsPath = "vc_demo_results.json"

// VCDemoSessionLogPath is the JSONL session timeline.
const VCDemoSessionLogPath = "vc_demo_session_log.jsonl"

// VCValidationNoteTemplatePath is the template for Vinayak's independent-validation note.
const VCValidationNoteTemplatePath = "review_packets/vc_validation_note_template.md"

// VCDemoSchemaVersion pins the aggregate report schema.
const VCDemoSchemaVersion = "sarathi.vc_demo/v1.0"

// VCDemoStep is one line in the JSONL session log.
type VCDemoStep struct {
	Timestamp  string                 `json:"timestamp"`
	Demo       string                 `json:"demo"`
	Step       string                 `json:"step"`
	Status     string                 `json:"status"` // PASS | FAIL | INFO
	Detail     string                 `json:"detail,omitempty"`
	Evidence   map[string]interface{} `json:"evidence,omitempty"`
}

// VCDemoOutcome aggregates one demo's outcome.
type VCDemoOutcome struct {
	Demo         string `json:"demo"`
	Description  string `json:"description"`
	Status       string `json:"status"`
	DurationMs   int64  `json:"duration_ms"`
	EvidencePath string `json:"evidence_path,omitempty"`
	Detail       string `json:"detail,omitempty"`
}

// VCDemoReport is the Phase 7 aggregate artefact.
type VCDemoReport struct {
	SchemaVersion string          `json:"schema_version"`
	GeneratedAt   string          `json:"generated_at"`
	DemoCount     int             `json:"demo_count"`
	DemosPassed   int             `json:"demos_passed"`
	AllPassed     bool            `json:"all_passed"`
	Demos         []VCDemoOutcome `json:"demos"`
	Notes         []string        `json:"notes,omitempty"`
}

// RunVCValidationDemo executes the five demos in sequence.
func RunVCValidationDemo() (*VCDemoReport, error) {
	printHeader("VC VALIDATION DEMO (v14.6 Phase 7)")
	fmt.Println("  Five demonstrations — multi-node, transport halt, cross-system, bucket, 1000-iter")
	fmt.Println()

	if err := os.MkdirAll(filepath.Dir(VCDemoSessionLogPath), 0o755); err != nil {
		return nil, err
	}
	logF, err := os.OpenFile(VCDemoSessionLogPath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return nil, err
	}
	defer logF.Close()

	log := func(step VCDemoStep) {
		if step.Timestamp == "" {
			step.Timestamp = time.Now().UTC().Format("2006-01-02T15:04:05.000000Z")
		}
		if b, jerr := json.Marshal(step); jerr == nil {
			logF.Write(append(b, '\n'))
		}
	}

	report := &VCDemoReport{
		SchemaVersion: VCDemoSchemaVersion,
		GeneratedAt:   time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		Demos:         make([]VCDemoOutcome, 0, 5),
	}

	// --- D1: Multi-node deterministic execution -----------------------------
	d1 := VCDemoOutcome{Demo: "D1", Description: "Multi-node deterministic execution"}
	d1Start := time.Now()
	fmt.Println("\n── DEMO 1 — Multi-node deterministic execution (3 nodes)")
	log(VCDemoStep{Demo: "D1", Step: "start", Status: "INFO",
		Detail: "spawning 3 child nodes with divergent clock skews"})
	mnResults, mnErr := RunMultiNode(MultiNodeRunConfig{
		NodeCount:        3,
		ClockSkewSeconds: []int{0, 5, -5},
		NodeIDs:          []string{"node-A", "node-B", "node-C"},
		Iterations:       MultiNodeDefaultIterations,
		Quiet:            true,
	})
	if mnErr != nil {
		d1.Status = "FAIL"
		d1.Detail = "runner: " + mnErr.Error()
	} else {
		mnReport, verr := ValidateMultiNode(mnResults)
		if verr != nil {
			d1.Status = "FAIL"
			d1.Detail = "validator: " + verr.Error()
		} else if !mnReport.AllByteIdentical {
			d1.Status = "FAIL"
			d1.Detail = fmt.Sprintf("unique_stable=%d expected=1", len(mnReport.UniqueStableHash))
		} else {
			d1.Status = "PASS"
			d1.EvidencePath = MultiNodeDeterminismReportPath
			for _, r := range mnResults {
				if r == nil || r.Manifest == nil {
					continue
				}
				fmt.Printf("    %s response_hash_stable=%s... skew=%+ds\n",
					r.NodeID, safeHashPrefix(r.Manifest.ResponseHashStable, 16), r.ClockSkewSec)
				log(VCDemoStep{Demo: "D1", Step: "node_manifest", Status: "INFO",
					Detail: r.NodeID,
					Evidence: map[string]interface{}{
						"node_id":              r.NodeID,
						"clock_skew_seconds":   r.ClockSkewSec,
						"response_hash_stable": r.Manifest.ResponseHashStable,
						"chain_binding_stable": r.Manifest.ChainBindingHashStable,
					},
				})
			}
		}
	}
	d1.DurationMs = time.Since(d1Start).Milliseconds()
	log(VCDemoStep{Demo: "D1", Step: "end", Status: d1.Status, Detail: d1.Detail})
	report.Demos = append(report.Demos, d1)
	fmt.Printf("  D1 %s (%dms) — %s\n", d1.Status, d1.DurationMs, d1.Detail)

	// --- D2: Transport mutation → chain halt --------------------------------
	d2 := VCDemoOutcome{Demo: "D2", Description: "Transport mutation attempt → chain halt"}
	d2Start := time.Now()
	fmt.Println("\n── DEMO 2 — Transport mutation attempt → chain halt (proxy_reserialize)")
	log(VCDemoStep{Demo: "D2", Step: "start", Status: "INFO",
		Detail: "routing sealed envelope through proxy that re-serialises JSON"})
	tReport, tErr := RunTransportAdversarialHarness()
	if tErr != nil {
		d2.Status = "FAIL"
		d2.Detail = tErr.Error()
	} else {
		found := false
		halted := false
		for _, sc := range tReport.Scenarios {
			if sc.Name == "proxy_reserialize" {
				found = true
				halted = sc.Actual == "HALT" && sc.HaltCode != "" && sc.Matched
				log(VCDemoStep{Demo: "D2", Step: "proxy_reserialize", Status: boolStatus(halted),
					Detail: sc.HaltCode,
					Evidence: map[string]interface{}{
						"expected":           sc.Expected,
						"actual":             sc.Actual,
						"halt_code":          sc.HaltCode,
						"integrity_verified": sc.TransportIntegrityVerified,
					},
				})
				break
			}
		}
		switch {
		case !found:
			d2.Status = "FAIL"
			d2.Detail = "proxy_reserialize scenario missing"
		case !halted:
			d2.Status = "FAIL"
			d2.Detail = "proxy_reserialize did not chain-halt as expected"
		default:
			d2.Status = "PASS"
			d2.EvidencePath = TransportIntegrityReportPath
		}
	}
	d2.DurationMs = time.Since(d2Start).Milliseconds()
	log(VCDemoStep{Demo: "D2", Step: "end", Status: d2.Status, Detail: d2.Detail})
	report.Demos = append(report.Demos, d2)
	fmt.Printf("  D2 %s (%dms) — %s\n", d2.Status, d2.DurationMs, d2.Detail)

	// --- D3: Successful propagation — identical hashes ----------------------
	d3 := VCDemoOutcome{Demo: "D3", Description: "Successful propagation → identical hashes across Core/InsightFlow/Bucket"}
	d3Start := time.Now()
	fmt.Println("\n── DEMO 3 — Cross-system integration (3 downstream peers)")
	log(VCDemoStep{Demo: "D3", Step: "start", Status: "INFO",
		Detail: "routing sealed envelope to 3 hash-verifying peers"})
	xReport, xErr := RunCrossSystemIntegration()
	if xErr != nil {
		d3.Status = "FAIL"
		d3.Detail = xErr.Error()
	} else if !xReport.CrossSystemIntegrationVerified {
		d3.Status = "FAIL"
		d3.Detail = fmt.Sprintf("verified=%d/%d readback=%t",
			xReport.TargetsVerified, xReport.TargetCount, xReport.BucketReadbackVerified)
	} else {
		d3.Status = "PASS"
		d3.EvidencePath = CrossSystemIntegrationReportPath
		for _, t := range xReport.Targets {
			log(VCDemoStep{Demo: "D3", Step: t.Name, Status: boolStatus(t.ByteEqual && t.AckVerified),
				Detail: fmt.Sprintf("bytes=%d", t.BytesReceived),
				Evidence: map[string]interface{}{
					"body_sha256":     t.BodySha256,
					"expected_sha256": t.ExpectedSha256,
					"byte_equal":      t.ByteEqual,
					"ack_verified":    t.AckVerified,
				},
			})
		}
	}
	d3.DurationMs = time.Since(d3Start).Milliseconds()
	log(VCDemoStep{Demo: "D3", Step: "end", Status: d3.Status, Detail: d3.Detail})
	report.Demos = append(report.Demos, d3)
	fmt.Printf("  D3 %s (%dms) — %s\n", d3.Status, d3.DurationMs, d3.Detail)

	// --- D4: Bucket read-back exact match -----------------------------------
	d4 := VCDemoOutcome{Demo: "D4", Description: "Bucket read-back exact match (5 sampled decisions)"}
	d4Start := time.Now()
	fmt.Println("\n── DEMO 4 — Bucket read-back (5 sampled decisions)")
	log(VCDemoStep{Demo: "D4", Step: "start", Status: "INFO",
		Detail: "5 POST + GET round-trips against in-process Bucket simulator"})
	// Write to a VC-scoped path so the canonical 100-decision audit artefact
	// produced by `--bucket-verify` is not clobbered by this sampled demo.
	bReport, bErr := RunBucketStateVerifierNAt(5,
		"vc_demo_bucket_verification_report.json",
		"proof_logs/vc_demo_bucket_verification_log.jsonl")
	if bErr != nil {
		d4.Status = "FAIL"
		d4.Detail = bErr.Error()
	} else if !bReport.BucketStateVerified {
		d4.Status = "FAIL"
		d4.Detail = fmt.Sprintf("matches=%d mismatches=%d", bReport.Matches, bReport.Mismatches)
	} else {
		d4.Status = "PASS"
		d4.EvidencePath = BucketStateReportPath
		for _, dec := range bReport.Decisions {
			log(VCDemoStep{Demo: "D4", Step: dec.DecisionID, Status: boolStatus(dec.ReadbackMatched),
				Detail: "readback_matched",
				Evidence: map[string]interface{}{
					"sent_hash":     dec.SentHash,
					"readback_hash": dec.ReadbackHash,
				},
			})
		}
	}
	d4.DurationMs = time.Since(d4Start).Milliseconds()
	log(VCDemoStep{Demo: "D4", Step: "end", Status: d4.Status, Detail: d4.Detail})
	report.Demos = append(report.Demos, d4)
	fmt.Printf("  D4 %s (%dms) — %s\n", d4.Status, d4.DurationMs, d4.Detail)

	// --- D5: 1000-iteration replay proof ------------------------------------
	d5 := VCDemoOutcome{Demo: "D5", Description: "1000-iteration replay proof"}
	d5Start := time.Now()
	fmt.Println("\n── DEMO 5 — 1000-iteration replay")
	log(VCDemoStep{Demo: "D5", Step: "start", Status: "INFO",
		Detail: "1000-iteration replay proving zero drift"})
	hReport, hErr := RunHighIterationReplay(HighIterationReplayDefault)
	if hErr != nil {
		d5.Status = "FAIL"
		d5.Detail = hErr.Error()
	} else if !hReport.AllByteIdentical ||
		len(hReport.UniqueResponseHashes) != 1 ||
		hReport.DeterminismViolations != 0 {
		d5.Status = "FAIL"
		d5.Detail = fmt.Sprintf("unique=%d violations=%d",
			len(hReport.UniqueResponseHashes), hReport.DeterminismViolations)
	} else {
		d5.Status = "PASS"
		d5.EvidencePath = HighIterationReportPath
		d5.Detail = fmt.Sprintf("iterations=%d unique_stable=%d violations=%d",
			hReport.Iterations, len(hReport.UniqueResponseHashes), hReport.DeterminismViolations)
		log(VCDemoStep{Demo: "D5", Step: "summary", Status: "PASS",
			Detail: d5.Detail,
			Evidence: map[string]interface{}{
				"iterations":                    hReport.Iterations,
				"unique_response_hashes":        hReport.UniqueResponseHashes,
				"unique_chain_bindings":         hReport.UniqueChainBindings,
				"determinism_violations":        hReport.DeterminismViolations,
				"all_byte_identical":            hReport.AllByteIdentical,
			},
		})
	}
	d5.DurationMs = time.Since(d5Start).Milliseconds()
	log(VCDemoStep{Demo: "D5", Step: "end", Status: d5.Status, Detail: d5.Detail})
	report.Demos = append(report.Demos, d5)
	fmt.Printf("  D5 %s (%dms) — %s\n", d5.Status, d5.DurationMs, d5.Detail)

	// --- Aggregate ----------------------------------------------------------
	report.DemoCount = len(report.Demos)
	for _, d := range report.Demos {
		if d.Status == "PASS" {
			report.DemosPassed++
		}
	}
	report.AllPassed = report.DemosPassed == report.DemoCount && report.DemoCount > 0

	_ = logF.Sync()

	passed := report.DemosPassed
	failed := report.DemoCount - report.DemosPassed
	if err := WriteCanonicalResults(
		VCDemoResultsPath,
		"vc_demo",
		report.DemoCount,
		passed,
		failed,
		report,
	); err != nil {
		return report, err
	}

	// Emit the validation note template (best-effort — template should always exist).
	if err := emitVCValidationNoteTemplate(VCValidationNoteTemplatePath, report); err != nil {
		report.Notes = append(report.Notes, "validation-note template: "+err.Error())
	}

	fmt.Printf("\n  VC Demo: %d/%d PASS (all_passed=%t)\n",
		report.DemosPassed, report.DemoCount, report.AllPassed)
	return report, nil
}

// --- helpers ---

func boolStatus(b bool) string {
	if b {
		return "PASS"
	}
	return "FAIL"
}

func safeHashPrefix(h string, n int) string {
	if len(h) <= n {
		return h
	}
	return h[:n]
}

// emitVCValidationNoteTemplate writes the sign-off template for Vinayak.
// Template is written only once unless overwritten explicitly (we truncate on
// every run so the timestamps match the latest demo).
func emitVCValidationNoteTemplate(path string, report *VCDemoReport) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	var sb strings.Builder
	sb.WriteString("# Sarathi v14.6 — Independent Validation Note (Template)\n\n")
	sb.WriteString("**Generated:** " + report.GeneratedAt + "\n")
	sb.WriteString("**Sign-off owner:** Vinayak Tiwari (independent validator)\n\n")
	sb.WriteString("## Demo summary (auto-populated)\n\n")
	sb.WriteString("| # | Demo | Status | Duration | Evidence |\n")
	sb.WriteString("|---|------|--------|----------|----------|\n")
	for _, d := range report.Demos {
		sb.WriteString(fmt.Sprintf("| %s | %s | %s | %dms | `%s` |\n",
			d.Demo, d.Description, d.Status, d.DurationMs, d.EvidencePath))
	}
	sb.WriteString(fmt.Sprintf("\n**All demos passed:** %t (%d/%d)\n\n",
		report.AllPassed, report.DemosPassed, report.DemoCount))
	sb.WriteString(`## Independent Validation

I, ___________________________________ (Vinayak Tiwari), have independently
verified the artefacts referenced above on ____________ (date), using commit
______________ of the Sarathi enforcement adapter. My findings are:

- [ ] Multi-node determinism: byte-identical response hashes across 3 nodes.
- [ ] Transport integrity: byte-mutating transport attacks chain-halt; benign features pass.
- [ ] Cross-system integration: Core, InsightFlow, and Bucket received byte-identical bytes.
- [ ] Bucket readback: persisted bytes equal Sarathi's sealed bytes.
- [ ] 1000-iteration replay: ` + "`UniqueResponseHashes == 1`" + `, ` + "`DeterminismViolations == 0`" + `.

### Deviations observed (if any)

_Fill in any departures from expected outcomes, with reproduction steps._

### Sign-off

Signed: __________________________________________   Date: ________________

Vinayak Tiwari — Independent Validator, Sarathi v14.6
`)
	return os.WriteFile(path, []byte(sb.String()), 0o644)
}
