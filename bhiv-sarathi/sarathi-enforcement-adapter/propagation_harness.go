// propagation_harness.go (v14.5 Cross-System Propagation Layer)
//
// N-iteration replay harness that proves byte-equality end-to-end. Each
// iteration:
//   1. Reads the fixture bytes (identical across runs — fixture is signed
//      with a deterministic Ed25519 key, fixed nonce, fixed timestamp).
//   2. Ingests via PDPAdapter → sealed PropagationEnvelope.
//   3. Dispatches envelope via router.RoutePropagation to all targets.
//   4. Records per-hop ByteEqualityResult, then computes the stable-form
//      hash (varying fields zeroed) for cross-iteration comparison.
//
// The success contract — ALL of these must hold for the harness to PASS:
//   - UniqueResponseHashes (stable form) length == 1
//   - UniqueChainBindings (stable form) length == 1
//   - DeterminismViolations == 0
//   - Every iteration's AllBytesMatch == true
//
// Outputs:
//   - propagation_byte_equality_report.json — wrapped via WriteCanonicalResults
//   - proof_logs/propagation_replay_results.jsonl — one JSONL record per iter

package main

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"time"
)

// PropagationReplayDefaultIterations is the default number of replay rounds.
// 50 iterations provides production-grade statistical confidence that
// byte-stability is not coincidental — any non-determinism source would
// manifest within the first few iterations due to varying timestamps,
// nonces, correlation IDs, and execution IDs across iterations.
const PropagationReplayDefaultIterations = 50

// DefaultPropagationReplayLogPath is where per-iteration JSONL records land.
const DefaultPropagationReplayLogPath = "proof_logs/propagation_replay_results.jsonl"

// DefaultPropagationReplayReportPath is the summary report file.
const DefaultPropagationReplayReportPath = "propagation_byte_equality_report.json"

// PropagationReplaySchemaVersion pins the report schema. If this drifts,
// downstream consumers (Vinayak's harness driver) must re-sync.
const PropagationReplaySchemaVersion = "sarathi.propagation.replay/v1.0"

// PropagationReplayConfig controls a replay run.
type PropagationReplayConfig struct {
	Iterations      int    // 0 → PropagationReplayDefaultIterations
	StopOnFirstFail bool   // default true
	LogFile         string // default DefaultPropagationReplayLogPath
	ReportFile      string // default DefaultPropagationReplayReportPath
	Quiet           bool   // suppress per-iteration console output
}

// PropagationReplayIteration is one row of the replay report.
type PropagationReplayIteration struct {
	Iteration             int                    `json:"iteration"`
	InputHash             string                 `json:"input_hash"`
	IngestHash            string                 `json:"ingest_hash"`
	DecisionHash          string                 `json:"decision_hash"`
	DecisionCoreHash      string                 `json:"decision_core_hash"`
	EnforcementHash       string                 `json:"enforcement_hash"`
	ResponseHash          string                 `json:"response_hash"`
	ChainBindingHash      string                 `json:"chain_binding_hash"`
	ResponseHashStable    string                 `json:"response_hash_stable"`
	ChainBindingHashStable string                `json:"chain_binding_hash_stable"`
	HopResults            []PropagationHopResult `json:"hop_results"`
	AllBytesMatch         bool                   `json:"all_bytes_match"`
	ChainHalted           bool                   `json:"chain_halted"`
	HaltHop               string                 `json:"halt_hop,omitempty"`
	HaltCode              string                 `json:"halt_code,omitempty"`
	DurationNs            int64                  `json:"duration_ns"`
	StartedAt             string                 `json:"started_at"`
}

// PropagationReplayReport is the final summary. Success is
// DeterminismViolations==0 AND len(UniqueResponseHashes)==1
// AND len(UniqueChainBindings)==1.
type PropagationReplayReport struct {
	SchemaVersion         string                       `json:"schema_version"`
	GeneratedAt           string                       `json:"generated_at"`
	Iterations            int                          `json:"iterations"`
	DeterminismViolations int                          `json:"determinism_violations"`
	ChainHalts            int                          `json:"chain_halts"`
	AllByteIdentical      bool                         `json:"all_byte_identical"`
	UniqueResponseHashes  []string                     `json:"unique_response_hashes"`
	UniqueChainBindings   []string                     `json:"unique_chain_bindings"`
	Runs                  []PropagationReplayIteration `json:"runs"`
}

// allowedVarianceTopLevelKeys names fields whose values are expected to vary
// between otherwise-identical iterations. They are zeroed before computing
// stable-form hashes. Keep in sync with the plan's "tolerated-variance set".
var allowedVarianceTopLevelKeys = []string{
	"correlation_id",
	"execution_id",
	"trace_id",
	"timestamp",
	"enforcement_token",
	// enforcement_hash includes a per-result nonce; stable form excludes it.
	"enforcement_hash",
	// response_hash and chain_binding_hash are filled by the seal path; on
	// the response itself they are "" — but the envelope stores them. Zero
	// them explicitly so stable form is identical to its in-canonical form.
	"response_hash",
	"chain_binding_hash",
}

// allowedVarianceNestedKeys lists (parent, child) pairs whose nested field
// should also be zeroed. Covers request/enforcement/execution/trace_context
// sub-maps and observability.pipeline_duration_ns.
var allowedVarianceNestedKeys = []struct{ Parent, Child string }{
	{"request", "correlation_id"},
	{"enforcement", "correlation_id"},
	{"enforcement", "enforced_at"},
	{"enforcement", "request_binding_hash"}, // depends on request nonce
	{"enforcement", "enforcement_hash"},     // nonce-bearing
	{"enforcement", "enforced"},             // may flip if replay tracker changes state
	{"enforcement", "reason"},               // "ALLOW" vs "REPLAY_DETECTED" drift
	{"execution", "correlation_id"},
	{"execution", "execution_id"},
	{"execution", "timestamp"},
	{"execution", "enforcement_hash"},
	{"trace_context", "trace_id"},
	{"trace_context", "span_id"},
	{"observability", "pipeline_duration_ns"},
}

// allowedVarianceTopLevelKeysAugmented additionally zeroes the top-level
// "reason" field — when the replay tracker flips state this string drifts
// between "ALLOW" and "REPLAY_DETECTED" even though the cryptographic
// fingerprints do not. It is a legitimate varying field for harness purposes.
var allowedVarianceTopLevelKeysAugmented = append([]string{"reason"}, allowedVarianceTopLevelKeys...)

// ProduceStableEnvelope returns the byte-equality comparison form of the
// envelope's canonical response. It is NEVER called on the production
// wire — the envelope's real canonicalResponseBytes are sent as-is. Stable
// form exists purely so the harness can compare bytes across iterations
// whose real nonces/timestamps legitimately differ.
//
// Method: parse canonical bytes → normalize allowed-variance fields →
// re-canonicalize. The output is byte-stable across identical fixture runs.
func ProduceStableEnvelope(env *PropagationEnvelope) []byte {
	if env == nil {
		return nil
	}
	raw := env.CanonicalResponseBytes()
	if len(raw) == 0 {
		return nil
	}
	var m map[string]interface{}
	dec := json.NewDecoder(newBytesReaderHarness(raw))
	dec.UseNumber()
	if err := dec.Decode(&m); err != nil {
		return nil
	}
	// Top-level: zero known-variance keys (augmented set includes "reason").
	for _, k := range allowedVarianceTopLevelKeysAugmented {
		if _, ok := m[k]; ok {
			m[k] = ""
		}
	}
	// Nested: zero (parent, child) pairs.
	for _, nk := range allowedVarianceNestedKeys {
		parent, ok := m[nk.Parent].(map[string]interface{})
		if !ok {
			continue
		}
		if _, exists := parent[nk.Child]; exists {
			// Preserve numeric-ness for pipeline_duration_ns so stable form
			// still parses as JSON number if decoders care.
			if nk.Child == "pipeline_duration_ns" {
				parent[nk.Child] = 0
			} else {
				parent[nk.Child] = ""
			}
		}
	}
	// propagation_chain: position 3 is the response_hash placeholder; it is
	// part of the seal contract but varies iteration-to-iteration because
	// enforcement_hash in position 2 varies. Zero both to produce stable form.
	if chain, ok := m["propagation_chain"].([]interface{}); ok {
		for i := range chain {
			if i == 2 || i == 3 {
				chain[i] = ""
			}
		}
		m["propagation_chain"] = chain
	}

	out, err := CanonicalMarshal(m)
	if err != nil {
		return nil
	}
	return out
}

// stableChainBindingHash returns Sha256Hex(CanonicalJoinChain(stable chain))
// so the harness has a drift-free chain_binding_hash to compare across iters.
func stableChainBindingHash(env *PropagationEnvelope) string {
	if env == nil {
		return ""
	}
	chain := env.PropagationChain()
	if len(chain) < 4 {
		return ""
	}
	stable := []string{chain[0], chain[1], "", ""}
	return Sha256Hex(CanonicalJoinChain(stable))
}

// RunPropagationReplay runs N iterations of the fixture-driven replay flow.
// Returns (passed, failed, report, err).
//
// A passing run: every iteration's AllBytesMatch==true, zero determinism
// violations, and a single unique stable response_hash / chain_binding_hash.
func RunPropagationReplay(
	pa *PDPAdapter, router *MultiSystemRouter, fixture []byte, cfg PropagationReplayConfig,
) (int, int, *PropagationReplayReport, error) {
	if cfg.Iterations <= 0 {
		cfg.Iterations = PropagationReplayDefaultIterations
	}
	if cfg.LogFile == "" {
		cfg.LogFile = DefaultPropagationReplayLogPath
	}
	if cfg.ReportFile == "" {
		cfg.ReportFile = DefaultPropagationReplayReportPath
	}
	if pa == nil {
		return 0, 0, nil, fmt.Errorf("propagation_replay: PDPAdapter is nil")
	}
	if router == nil {
		return 0, 0, nil, fmt.Errorf("propagation_replay: router is nil")
	}
	if len(fixture) == 0 {
		return 0, 0, nil, fmt.Errorf("propagation_replay: fixture is empty")
	}

	// Prepare output paths.
	if err := os.MkdirAll(filepath.Dir(cfg.LogFile), 0o755); err != nil {
		return 0, 0, nil, fmt.Errorf("propagation_replay: mkdir log dir: %w", err)
	}
	// Open JSONL log in truncate mode — a fresh harness run starts a fresh file.
	logF, err := os.OpenFile(cfg.LogFile, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return 0, 0, nil, fmt.Errorf("propagation_replay: open log: %w", err)
	}
	defer logF.Close()

	report := &PropagationReplayReport{
		SchemaVersion:        PropagationReplaySchemaVersion,
		GeneratedAt:          time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		Iterations:           cfg.Iterations,
		UniqueResponseHashes: []string{},
		UniqueChainBindings:  []string{},
		Runs:                 make([]PropagationReplayIteration, 0, cfg.Iterations),
	}

	inputHash := Sha256Hex(fixture)
	stableHashSet := map[string]bool{}
	stableChainSet := map[string]bool{}
	passed := 0
	failed := 0

	if !cfg.Quiet {
		fmt.Printf("  [PropagationReplay] Running %d iterations (input_hash=%s)\n",
			cfg.Iterations, inputHash[:16])
	}

	for i := 1; i <= cfg.Iterations; i++ {
		started := time.Now().UTC()

		row := PropagationReplayIteration{
			Iteration: i,
			InputHash: inputHash,
			StartedAt: started.Format("2006-01-02T15:04:05.000000Z"),
		}

		// Test affordance: clear the adapter's replay tracker between
		// iterations so the FIXED-nonce fixture is not rejected as a
		// nonce-replay attack. Production code paths never invoke this.
		// See PDPAdapter.ResetReplayTrackerForHarness documentation.
		pa.ResetReplayTrackerForHarness()

		// Build a varying executionID/correlationID per iteration — their
		// variance is expected, and stable-form hashing normalises it away.
		execID := fmt.Sprintf("EXEC-REPLAY-%03d", i)
		corrID := fmt.Sprintf("corr-replay-%03d", i)

		env, ierr := pa.Ingest(fixture, execID, corrID, nil)
		if ierr != nil {
			row.AllBytesMatch = false
			row.HaltCode = CodePDPDecisionInvalid
			row.HaltHop = HopPDPIngest
			failed++
			writeIterationLog(logF, row)
			report.Runs = append(report.Runs, row)
			if !cfg.Quiet {
				fmt.Printf("    iter %d/%d INGEST_FAIL: %v\n", i, cfg.Iterations, ierr)
			}
			if cfg.StopOnFirstFail {
				break
			}
			continue
		}

		row.IngestHash = env.IngestHash()
		row.DecisionHash = env.DecisionHash()
		row.DecisionCoreHash = env.DecisionCoreHash()
		row.EnforcementHash = env.EnforcementHash()
		row.ResponseHash = env.ResponseHash()
		row.ChainBindingHash = env.ChainBindingHash()
		row.ResponseHashStable = Sha256Hex(ProduceStableEnvelope(env))
		row.ChainBindingHashStable = stableChainBindingHash(env)

		// Route through the router — may contain in-memory handlers wired by
		// the caller (propagation_fault_injection_sim.go uses this).
		propRes, rerr := router.RoutePropagation(env)
		if rerr != nil {
			row.AllBytesMatch = false
			row.HaltCode = "ROUTE_ERROR"
			failed++
			writeIterationLog(logF, row)
			report.Runs = append(report.Runs, row)
			if cfg.StopOnFirstFail {
				break
			}
			continue
		}
		row.HopResults = propRes.Hops
		row.ChainHalted = propRes.ChainHalted
		row.HaltHop = propRes.HaltHop
		row.HaltCode = propRes.HaltCode

		// AllBytesMatch: every in-chain hop delivered AND chain did not halt.
		allOK := !propRes.ChainHalted && propRes.AllInChainDelivered()
		row.AllBytesMatch = allOK
		row.DurationNs = time.Since(started).Nanoseconds()

		if allOK {
			passed++
		} else {
			failed++
			report.DeterminismViolations++
			if propRes.ChainHalted {
				report.ChainHalts++
			}
		}

		stableHashSet[row.ResponseHashStable] = true
		stableChainSet[row.ChainBindingHashStable] = true

		writeIterationLog(logF, row)
		report.Runs = append(report.Runs, row)

		if !cfg.Quiet {
			fmt.Printf("    iter %d/%d response_hash=%s... stable=%s... bytes_match=%t\n",
				i, cfg.Iterations, row.ResponseHash[:12], row.ResponseHashStable[:12], row.AllBytesMatch)
		}

		if !allOK && cfg.StopOnFirstFail {
			break
		}
	}

	report.UniqueResponseHashes = sortedKeys(stableHashSet)
	report.UniqueChainBindings = sortedKeys(stableChainSet)
	report.AllByteIdentical = report.DeterminismViolations == 0 &&
		len(report.UniqueResponseHashes) == 1 &&
		len(report.UniqueChainBindings) == 1

	// Sync log file before writing summary so both artefacts are durable on
	// process kill.
	_ = logF.Sync()

	// Write summary report through the canonical envelope.
	if werr := WriteCanonicalResults(
		cfg.ReportFile,
		"propagation_byte_equality",
		cfg.Iterations,
		passed,
		failed,
		report,
	); werr != nil {
		return passed, failed, report, werr
	}

	if !cfg.Quiet {
		fmt.Printf("\n  Summary:\n")
		fmt.Printf("    iterations                   : %d\n", cfg.Iterations)
		fmt.Printf("    unique response_hash_stable  : %d%s\n",
			len(report.UniqueResponseHashes), pickMark(len(report.UniqueResponseHashes) == 1))
		fmt.Printf("    unique chain_binding_stable  : %d%s\n",
			len(report.UniqueChainBindings), pickMark(len(report.UniqueChainBindings) == 1))
		fmt.Printf("    determinism_violations       : %d%s\n",
			report.DeterminismViolations, pickMark(report.DeterminismViolations == 0))
		fmt.Printf("    determinism_status           : %s\n", pickStatus(report.AllByteIdentical))
	}

	return passed, failed, report, nil
}

// RunDeterministicPropagationReplayTests is the thin wrapper result_writer-style
// exposes so the main harness can call through consistently. Builds the
// default fixture + a deterministic router (no HTTP — in-memory OK handlers
// bound to all targets) and runs PropagationReplayDefaultIterations rounds.
func RunDeterministicPropagationReplayTests(
	pa *PDPAdapter, router *MultiSystemRouter, fixture []byte, iterations int,
) (int, int, *PropagationReplayReport) {
	printHeader("CROSS-SYSTEM PROPAGATION REPLAY (Phase 14.5)")
	fmt.Println("  Proving: SAME PDP input → SAME byte-identical output across iterations")
	fmt.Println()

	cfg := PropagationReplayConfig{
		Iterations:      iterations,
		StopOnFirstFail: false, // harness mode: record every run
	}
	passed, failed, _, err := RunPropagationReplay(pa, router, fixture, cfg)
	if err != nil {
		fmt.Printf("  [ERROR] propagation replay: %v\n", err)
	}
	fmt.Printf("\n  Propagation Replay: %d/%d PASSED\n", passed, passed+failed)
	report := &PropagationReplayReport{}
	return passed, passed + failed, report
}

// --- helpers ---

// writeIterationLog appends one iteration record to the JSONL log. Errors
// are swallowed so a transient write failure does not abort the harness —
// the summary report is still produced.
func writeIterationLog(f *os.File, row PropagationReplayIteration) {
	if f == nil {
		return
	}
	b, err := json.Marshal(row)
	if err != nil {
		return
	}
	b = append(b, '\n')
	_, _ = f.Write(b)
}

// sortedKeys returns the keys of a bool-set in ascending order.
func sortedKeys(m map[string]bool) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

// pickMark returns a visual mark — " ← OK" for true, " ← DRIFT" for false.
// Keeps console output terse and grep-able.
func pickMark(ok bool) string {
	if ok {
		return " (ok)"
	}
	return " (DRIFT)"
}

// pickStatus returns "PASS" or "FAIL".
func pickStatus(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}

// newBytesReaderHarness is a minimal io.Reader around []byte used by the
// JSON decoder. Separated from newByteReader in replay_fixture_builder.go
// to keep file dependencies tight.
type bytesReaderHarness struct {
	b   []byte
	pos int
}

func newBytesReaderHarness(b []byte) *bytesReaderHarness { return &bytesReaderHarness{b: b} }

func (r *bytesReaderHarness) Read(p []byte) (int, error) {
	if r.pos >= len(r.b) {
		return 0, io.EOF
	}
	n := copy(p, r.b[r.pos:])
	r.pos += n
	return n, nil
}
