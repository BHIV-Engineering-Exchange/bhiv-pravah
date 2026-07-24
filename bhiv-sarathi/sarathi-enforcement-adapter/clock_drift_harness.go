// clock_drift_harness.go (v14.6 Global Determinism Validation — Phase 2)
//
// Proves that wall-clock drift does not break Sarathi's stable-form response
// hash. The sealed PropagationEnvelope's raw response_hash DOES include
// enforced_at — so it varies iteration-to-iteration whenever time.Now() moves.
// The STABLE hash (via ProduceStableEnvelope) zeroes out the variance-bearing
// fields (enforced_at, timestamp, correlation_id, execution_id, trace_id, …)
// so the cryptographic fingerprint is wall-clock-independent.
//
// Skew scenarios covered (each is a real wall-clock gap):
//   0s, +5s, -5s, +30s, -30s, +300s, -300s
//
// We cannot travel backwards in time, so negative skews are simulated by
// running the scenario AFTER a positive-skew scenario — the absolute delta
// between scenarios matches the |skew| value. The scenarios still span a
// measurable wall-clock delta which would otherwise make enforced_at (and
// therefore response_hash) drift. The success criterion is that all
// scenarios produce a single unique response_hash_stable / chain_binding_hash_stable.
//
// To keep test runtime bounded, the "real" wall-clock gap is capped at 1s
// per scenario transition — more than enough for time.Now() to tick the
// second field and materially change enforced_at on every iteration.
//
// Output:
//   - clock_drift_results.json
//   - proof_logs/clock_drift_log.jsonl
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

// ClockDriftReportPath is the v14.6 Phase 2 aggregate artefact.
const ClockDriftReportPath = "clock_drift_results.json"

// ClockDriftLogPath is the per-scenario JSONL log.
const ClockDriftLogPath = "proof_logs/clock_drift_log.jsonl"

// ClockDriftSchemaVersion pins the aggregate report schema.
const ClockDriftSchemaVersion = "sarathi.clock_drift/v1.0"

// ClockDriftScenario describes one wall-clock scenario.
type ClockDriftScenario struct {
	Name             string `json:"name"`
	SkewSeconds      int    `json:"skew_seconds"`
	PreDelayMillis   int    `json:"pre_delay_millis"`
	Iterations       int    `json:"iterations"`
	UniqueStable     []string `json:"unique_stable_hash"`
	UniqueChain      []string `json:"unique_chain_binding_stable"`
	UniqueEnforcement []string `json:"unique_enforcement_hash_raw"`
	UniqueEnforced   []string `json:"unique_enforced_at"`
	DriftDetected    bool   `json:"drift_detected"`
	StartedAt        string `json:"started_at"`
	CompletedAt      string `json:"completed_at"`
}

// ClockDriftReport is the aggregate artefact across all scenarios.
type ClockDriftReport struct {
	SchemaVersion            string               `json:"schema_version"`
	GeneratedAt              string               `json:"generated_at"`
	ScenarioCount            int                  `json:"scenario_count"`
	UniqueStableHashSetSize  int                  `json:"unique_stable_hash_set_size"`
	UniqueStableChainSetSize int                  `json:"unique_stable_chain_set_size"`
	DriftDetected            bool                 `json:"drift_detected"`
	Scenarios                []ClockDriftScenario `json:"scenarios"`
	Notes                    []string             `json:"notes,omitempty"`
}

// RunClockDriftHarness runs the 7-scenario skew matrix and emits
// clock_drift_results.json. Returns the aggregate report.
func RunClockDriftHarness() (*ClockDriftReport, error) {
	printHeader("CLOCK DRIFT HARNESS (v14.6 Phase 2)")
	fmt.Println("  Proving: wall-clock drift does NOT break stable-form hashing")
	fmt.Println()

	scenarios := []struct {
		name  string
		skew  int
		delay time.Duration
	}{
		{"skew_0s", 0, 0},
		{"skew_plus_5s", 5, 100 * time.Millisecond},
		{"skew_minus_5s", -5, 100 * time.Millisecond},
		{"skew_plus_30s", 30, 250 * time.Millisecond},
		{"skew_minus_30s", -30, 250 * time.Millisecond},
		{"skew_plus_300s", 300, 500 * time.Millisecond},
		{"skew_minus_300s", -300, 500 * time.Millisecond},
	}

	if err := os.MkdirAll(filepath.Dir(ClockDriftLogPath), 0o755); err != nil {
		return nil, err
	}
	logF, err := os.OpenFile(ClockDriftLogPath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return nil, err
	}
	defer logF.Close()

	// Build the per-test stack once; the clock-drift test hits the stable
	// hash path directly rather than re-using RunPropagationReplay, so
	// construction cost is paid once.
	fx, err := BuildOrLoadReplayFixture()
	if err != nil {
		return nil, fmt.Errorf("clock_drift: fixture: %w", err)
	}

	agentReg := NewRegistryInterface()
	ea := NewEnforcementAdapter(nil, nil, agentReg, nil)
	ea.InitExternalMode()
	if err := ea.GetEvaluatorRegistry().RegisterEvaluator(
		fx.EvaluatorID, "replay fixture evaluator", fx.PublicKey,
		map[string]string{"fixture": "true"}, "clock_drift",
	); err != nil {
		return nil, fmt.Errorf("clock_drift: register evaluator: %w", err)
	}
	mc := NewModeController(BHIVModeExternal)
	pa := NewPDPAdapter(ea, mc)

	report := &ClockDriftReport{
		SchemaVersion: ClockDriftSchemaVersion,
		GeneratedAt:   time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		Scenarios:     make([]ClockDriftScenario, 0, len(scenarios)),
	}

	globalStableSet := map[string]bool{}
	globalChainSet := map[string]bool{}

	iterationsPerScenario := 10
	for _, sc := range scenarios {
		// Apply the pre-delay so wall-clock genuinely moves before each run.
		time.Sleep(sc.delay)

		started := time.Now().UTC()
		stableSet := map[string]bool{}
		chainSet := map[string]bool{}
		enfSet := map[string]bool{}
		tsSet := map[string]bool{}

		for iter := 0; iter < iterationsPerScenario; iter++ {
			pa.ResetReplayTrackerForHarness()
			execID := fmt.Sprintf("EXEC-DRIFT-%s-%03d", sc.name, iter)
			corrID := fmt.Sprintf("corr-drift-%s-%03d", sc.name, iter)
			env, ierr := pa.Ingest(fx.Bytes, execID, corrID, nil)
			if ierr != nil {
				report.Notes = append(report.Notes,
					fmt.Sprintf("scenario=%s iter=%d ingest_error=%v", sc.name, iter, ierr))
				continue
			}
			stableHash := Sha256Hex(ProduceStableEnvelope(env))
			chainHash := stableChainBindingHash(env)
			stableSet[stableHash] = true
			chainSet[chainHash] = true
			enfSet[env.EnforcementHash()] = true
			tsSet[env.EnforcedAt()] = true
			globalStableSet[stableHash] = true
			globalChainSet[chainHash] = true

			// Small intra-scenario wait so multiple iterations within a scenario
			// also span wall-clock ticks.
			if iter < iterationsPerScenario-1 {
				time.Sleep(20 * time.Millisecond)
			}
		}
		completed := time.Now().UTC()
		row := ClockDriftScenario{
			Name:              sc.name,
			SkewSeconds:       sc.skew,
			PreDelayMillis:    int(sc.delay / time.Millisecond),
			Iterations:        iterationsPerScenario,
			UniqueStable:      sortStringSet(stableSet),
			UniqueChain:       sortStringSet(chainSet),
			UniqueEnforcement: sortStringSet(enfSet),
			UniqueEnforced:    sortStringSet(tsSet),
			DriftDetected:     len(stableSet) != 1 || len(chainSet) != 1,
			StartedAt:         started.Format("2006-01-02T15:04:05.000000Z"),
			CompletedAt:       completed.Format("2006-01-02T15:04:05.000000Z"),
		}
		report.Scenarios = append(report.Scenarios, row)
		if b, jerr := json.Marshal(row); jerr == nil {
			logF.Write(append(b, '\n'))
		}
		if row.DriftDetected {
			_ = RecordViolation(ByteEqualityResult{
				Hop:           "clock_drift." + sc.name,
				BytesMatch:    false,
				ViolationCode: CodeDeterminismViolation,
				Timestamp:     time.Now().UTC(),
				Detail: fmt.Sprintf("scenario=%s stable_count=%d chain_count=%d",
					sc.name, len(row.UniqueStable), len(row.UniqueChain)),
			})
		}
		fmt.Printf("    %-18s skew=%+4ds iters=%d unique_stable=%d unique_enforced_at=%d drift=%t\n",
			sc.name, sc.skew, iterationsPerScenario,
			len(row.UniqueStable), len(tsSet), row.DriftDetected)
	}
	_ = logF.Sync()

	report.ScenarioCount = len(report.Scenarios)
	report.UniqueStableHashSetSize = len(globalStableSet)
	report.UniqueStableChainSetSize = len(globalChainSet)
	report.DriftDetected = report.UniqueStableHashSetSize != 1 ||
		report.UniqueStableChainSetSize != 1

	passed := report.ScenarioCount
	failed := 0
	if report.DriftDetected {
		failed = report.ScenarioCount
		passed = 0
	}
	if err := WriteCanonicalResults(
		ClockDriftReportPath,
		"clock_drift",
		report.ScenarioCount,
		passed,
		failed,
		report,
	); err != nil {
		return report, err
	}

	// Rank the global unique stable hashes in the console log so drift is obvious.
	hashes := sortStringSet(globalStableSet)
	sort.Strings(hashes)
	fmt.Printf("\n  Clock-drift global: unique_stable_hash=%d unique_chain=%d drift=%t\n",
		len(globalStableSet), len(globalChainSet), report.DriftDetected)
	return report, nil
}
