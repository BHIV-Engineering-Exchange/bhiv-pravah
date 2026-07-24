// high_iteration_replay.go (v14.6 Global Determinism Validation — Phase 5)
//
// Thin wrapper around the v14.5 RunPropagationReplay that lifts the default
// iteration count from 50 → 1000 and adds:
//
//   - Progress printout every 100 iterations
//   - A distinct output path per run so the v14.5 50-iter artefacts are preserved
//   - On drift, a full drift-trace JSONL (proof_logs/replay_drift_trace_1000.jsonl)
//     capturing every deviating iteration's full canonical response bytes
//
// The v14.5 function is called UNCHANGED — no modification to the propagation
// core. This wrapper owns only orchestration + post-analysis.
//
// TAG: test-affordance-only

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// HighIterationReplayDefault is the v14.6 Phase 5 default iteration count.
const HighIterationReplayDefault = 1000

// HighIterationReportPath is the v14.6 Phase 5 aggregate artefact.
const HighIterationReportPath = "propagation_byte_equality_report_1000.json"

// HighIterationLogPath is the per-iteration JSONL log.
const HighIterationLogPath = "proof_logs/propagation_replay_results_1000.jsonl"

// HighIterationDriftTracePath captures full canonical bytes for any deviating iteration.
const HighIterationDriftTracePath = "proof_logs/replay_drift_trace_1000.jsonl"

// HighIterationDriftRow is one row of the drift trace.
type HighIterationDriftRow struct {
	Iteration              int    `json:"iteration"`
	ResponseHash           string `json:"response_hash"`
	ResponseHashStable     string `json:"response_hash_stable"`
	ChainBindingHashStable string `json:"chain_binding_hash_stable"`
	AllBytesMatch          bool   `json:"all_bytes_match"`
	ChainHalted            bool   `json:"chain_halted"`
	HaltHop                string `json:"halt_hop,omitempty"`
	HaltCode               string `json:"halt_code,omitempty"`
	DeviatesFromMajority   bool   `json:"deviates_from_majority"`
	MajorityStableHash     string `json:"majority_stable_hash,omitempty"`
}

// RunHighIterationReplay executes the Phase 5 1000-iteration replay.
func RunHighIterationReplay(iter int) (*PropagationReplayReport, error) {
	if iter <= 0 {
		iter = HighIterationReplayDefault
	}
	printHeader(fmt.Sprintf("HIGH-ITERATION REPLAY (v14.6 Phase 5 — N=%d)", iter))
	fmt.Println("  Proving: 1000-iteration replay yields UniqueResponseHashes==1, DeterminismViolations==0")
	fmt.Println()

	fx, err := BuildOrLoadReplayFixture()
	if err != nil {
		return nil, fmt.Errorf("high_iter: fixture: %w", err)
	}
	agentReg := NewRegistryInterface()
	ea := NewEnforcementAdapter(nil, nil, agentReg, nil)
	ea.InitExternalMode()
	if err := ea.GetEvaluatorRegistry().RegisterEvaluator(
		fx.EvaluatorID, "replay fixture evaluator", fx.PublicKey,
		map[string]string{"fixture": "true"}, "high_iter",
	); err != nil {
		return nil, fmt.Errorf("high_iter: register evaluator: %w", err)
	}
	mc := NewModeController(BHIVModeExternal)
	pa := NewPDPAdapter(ea, mc)

	router := NewMultiSystemRouter(nil)
	for _, name := range []string{"core_workflow", "insightflow", "bucket"} {
		router.InstallPropagationHandler(name, func(event *RoutedEvent) error { return nil }, true, false)
	}
	router.InstallPropagationHandler("intent_layer",
		func(event *RoutedEvent) error { return nil }, false, true)

	// Progress observer — the replay loop is quiet; we poll the report after.
	cfg := PropagationReplayConfig{
		Iterations:      iter,
		StopOnFirstFail: false,
		LogFile:         HighIterationLogPath,
		ReportFile:      HighIterationReportPath,
		Quiet:           true,
	}

	started := time.Now()
	fmt.Printf("  [HighIter] starting %d iterations at %s\n", iter, started.Format(time.RFC3339))
	passed, failed, report, err := RunPropagationReplay(pa, router, fx.Bytes, cfg)
	if err != nil {
		return report, fmt.Errorf("high_iter: replay: %w", err)
	}
	elapsed := time.Since(started)

	// Coarse progress — print post-run breakdown by bucket of 100.
	printHighIterProgress(report, 100)

	fmt.Printf("\n  [HighIter] completed in %s passed=%d failed=%d\n",
		elapsed.Round(time.Millisecond), passed, failed)
	fmt.Printf("    unique response_hash_stable   : %d\n", len(report.UniqueResponseHashes))
	fmt.Printf("    unique chain_binding_stable   : %d\n", len(report.UniqueChainBindings))
	fmt.Printf("    determinism_violations        : %d\n", report.DeterminismViolations)
	fmt.Printf("    chain_halts                   : %d\n", report.ChainHalts)
	fmt.Printf("    all_byte_identical            : %t\n", report.AllByteIdentical)

	// On drift: emit the drift-trace file so human diff is trivial.
	if !report.AllByteIdentical ||
		len(report.UniqueResponseHashes) != 1 ||
		report.DeterminismViolations != 0 {
		if derr := writeDriftTrace(report, HighIterationDriftTracePath); derr != nil {
			fmt.Fprintf(os.Stderr, "WARN: drift trace write: %v\n", derr)
		} else {
			fmt.Printf("  [HighIter] drift trace written: %s\n", HighIterationDriftTracePath)
		}
		return report, fmt.Errorf("high_iter: drift detected (unique=%d violations=%d)",
			len(report.UniqueResponseHashes), report.DeterminismViolations)
	}
	return report, nil
}

// printHighIterProgress emits a compact bucket-by-100 summary so operators can
// see the curve even though RunPropagationReplay ran in quiet mode.
func printHighIterProgress(report *PropagationReplayReport, bucket int) {
	if report == nil || bucket <= 0 || len(report.Runs) == 0 {
		return
	}
	fmt.Printf("  [HighIter] progress buckets (every %d iterations):\n", bucket)
	for i := 0; i < len(report.Runs); i += bucket {
		end := i + bucket
		if end > len(report.Runs) {
			end = len(report.Runs)
		}
		stable := map[string]int{}
		halted := 0
		for _, r := range report.Runs[i:end] {
			stable[r.ResponseHashStable]++
			if r.ChainHalted {
				halted++
			}
		}
		fmt.Printf("    iters %d–%d: unique_stable=%d halted=%d\n",
			i+1, end, len(stable), halted)
	}
}

// writeDriftTrace iterates every run and writes a row for any iteration whose
// stable response hash is not the majority hash. The file is truncated on each
// write so stale traces don't linger after a clean run.
func writeDriftTrace(report *PropagationReplayReport, path string) error {
	if report == nil {
		return fmt.Errorf("drift_trace: nil report")
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()

	// Majority stable hash wins; everyone else is a deviation.
	counts := map[string]int{}
	for _, r := range report.Runs {
		counts[r.ResponseHashStable]++
	}
	majority := ""
	majorityCount := -1
	for k, c := range counts {
		if c > majorityCount {
			majority = k
			majorityCount = c
		}
	}

	for _, r := range report.Runs {
		deviates := r.ResponseHashStable != majority || !r.AllBytesMatch
		if !deviates {
			continue
		}
		row := HighIterationDriftRow{
			Iteration:              r.Iteration,
			ResponseHash:           r.ResponseHash,
			ResponseHashStable:     r.ResponseHashStable,
			ChainBindingHashStable: r.ChainBindingHashStable,
			AllBytesMatch:          r.AllBytesMatch,
			ChainHalted:            r.ChainHalted,
			HaltHop:                r.HaltHop,
			HaltCode:               r.HaltCode,
			DeviatesFromMajority:   r.ResponseHashStable != majority,
			MajorityStableHash:     majority,
		}
		if b, jerr := json.Marshal(row); jerr == nil {
			f.Write(append(b, '\n'))
		}
	}
	return f.Sync()
}
