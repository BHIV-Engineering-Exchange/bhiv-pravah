// multi_node_runner.go (v14.6 Global Determinism Validation — Phase 1)
//
// Spawns N independent Sarathi child processes and collects their per-node
// propagation-replay artefacts so a single cross-node byte-equality oracle
// can prove that "same input → same output" holds across real OS processes,
// not just across iterations inside one process.
//
// Each child is invoked as:
//   <self> --multi-node-child                          (CLI handled in v14_6_cli.go)
// with env:
//   SARATHI_NODE_ID=node-<i>
//   SARATHI_CLOCK_SKEW_SECONDS=<skew>                  (optional; 0 if unset)
//
// The child produces three artefacts keyed by node_id:
//   multi_node_reports/<node_id>/propagation_byte_equality_report.json
//   multi_node_reports/<node_id>/propagation_replay_results.jsonl
//   multi_node_reports/<node_id>/envelope_manifest.json
//
// The parent collects every manifest, hands the set to ValidateMultiNode, and
// emits multi_node_determinism_report.json — the canonical v14.6 Phase 1
// artefact.
//
// TAG: test-affordance-only

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"sync"
	"time"
)

// MultiNodeChildFlag is the sub-command passed to children so they run the
// per-node propagation flow without invoking the full v14.5/v14.6 stack.
const MultiNodeChildFlag = "--multi-node-child"

// MultiNodeReportRoot is the on-disk directory where per-node artefacts land.
const MultiNodeReportRoot = "multi_node_reports"

// MultiNodeJSONLLogName is the per-child JSONL log name.
const MultiNodeJSONLLogName = "propagation_replay_results.jsonl"

// MultiNodeReportName is the per-child summary report name.
const MultiNodeReportName = "propagation_byte_equality_report.json"

// MultiNodeManifestName is the single-iteration envelope fingerprint manifest.
const MultiNodeManifestName = "envelope_manifest.json"

// MultiNodeDefaultIterations is the iteration count each child runs. Two
// iterations are enough to surface in-process drift while keeping wall time
// small; cross-node drift is surfaced by the aggregator, not per-child.
const MultiNodeDefaultIterations = 2

// MultiNodeChildTimeout bounds a single child process. Exceeding this is
// treated as a non-determinism failure.
const MultiNodeChildTimeout = 2 * time.Minute

// MultiNodeChildEnvelopeManifest is the single-iteration fingerprint written
// by each child so the aggregator can compare stable hashes across nodes
// without needing to parse the full replay report.
type MultiNodeChildEnvelopeManifest struct {
	SchemaVersion          string `json:"schema_version"`
	NodeID                 string `json:"node_id"`
	ClockSkewSeconds       int    `json:"clock_skew_seconds"`
	GeneratedAt            string `json:"generated_at"`
	InputHash              string `json:"input_hash"`
	DecisionHash           string `json:"decision_hash"`
	DecisionCoreHash       string `json:"decision_core_hash"`
	EnforcementHash        string `json:"enforcement_hash"`
	ResponseHash           string `json:"response_hash"`
	ChainBindingHash       string `json:"chain_binding_hash"`
	ResponseHashStable     string `json:"response_hash_stable"`
	ChainBindingHashStable string `json:"chain_binding_hash_stable"`
	CanonicalLength        int    `json:"canonical_response_length"`
	CanonicalSha256        string `json:"canonical_response_sha256"`
	StableCanonicalLength  int    `json:"stable_canonical_length"`
	StableCanonicalSha256  string `json:"stable_canonical_sha256"`
}

// MultiNodeRunConfig controls one multi-node execution.
type MultiNodeRunConfig struct {
	NodeCount        int
	ClockSkewSeconds []int  // per-node skews. len(ClockSkewSeconds) >= NodeCount
	NodeIDs          []string // per-node IDs. Defaults to node-1..node-N
	Iterations       int
	OutputDir        string
	Quiet            bool
}

// MultiNodeChildResult is the parent-side view of one child run.
type MultiNodeChildResult struct {
	NodeID       string                           `json:"node_id"`
	ClockSkewSec int                              `json:"clock_skew_seconds"`
	ReportPath   string                           `json:"report_path"`
	ManifestPath string                           `json:"manifest_path"`
	LogPath      string                           `json:"log_path"`
	ExitCode     int                              `json:"exit_code"`
	DurationNs   int64                            `json:"duration_ns"`
	StdoutTail   string                           `json:"stdout_tail,omitempty"`
	StderrTail   string                           `json:"stderr_tail,omitempty"`
	Error        string                           `json:"error,omitempty"`
	Manifest     *MultiNodeChildEnvelopeManifest  `json:"manifest,omitempty"`
	Report       *PropagationReplayReport         `json:"report,omitempty"`
}

// RunMultiNode spawns cfg.NodeCount independent children and collects their
// artefacts. It does NOT validate byte-equality — that is the job of
// ValidateMultiNode. The two are split so each step is independently testable.
//
// Returns the per-node results in the same order as cfg.NodeIDs.
func RunMultiNode(cfg MultiNodeRunConfig) ([]*MultiNodeChildResult, error) {
	if cfg.NodeCount <= 0 {
		cfg.NodeCount = 3
	}
	if cfg.Iterations <= 0 {
		cfg.Iterations = MultiNodeDefaultIterations
	}
	if cfg.OutputDir == "" {
		cfg.OutputDir = MultiNodeReportRoot
	}
	if len(cfg.NodeIDs) < cfg.NodeCount {
		ids := make([]string, cfg.NodeCount)
		for i := 0; i < cfg.NodeCount; i++ {
			ids[i] = fmt.Sprintf("node-%d", i+1)
		}
		cfg.NodeIDs = ids
	}
	if len(cfg.ClockSkewSeconds) < cfg.NodeCount {
		skews := make([]int, cfg.NodeCount)
		copy(skews, cfg.ClockSkewSeconds)
		cfg.ClockSkewSeconds = skews
	}
	if err := os.MkdirAll(cfg.OutputDir, 0o755); err != nil {
		return nil, fmt.Errorf("multi_node: mkdir %s: %w", cfg.OutputDir, err)
	}

	self, err := os.Executable()
	if err != nil {
		return nil, fmt.Errorf("multi_node: resolve self executable: %w", err)
	}

	results := make([]*MultiNodeChildResult, cfg.NodeCount)
	var wg sync.WaitGroup
	for i := 0; i < cfg.NodeCount; i++ {
		wg.Add(1)
		idx := i
		go func() {
			defer wg.Done()
			res := runOneChild(self, cfg, idx)
			results[idx] = res
		}()
	}
	wg.Wait()

	// Load each manifest + report so callers have the parsed structs.
	for _, r := range results {
		if r == nil {
			continue
		}
		if mb, err := os.ReadFile(r.ManifestPath); err == nil {
			m := &MultiNodeChildEnvelopeManifest{}
			if jerr := json.Unmarshal(mb, m); jerr == nil {
				r.Manifest = m
			}
		}
		if rb, err := os.ReadFile(r.ReportPath); err == nil {
			report := &PropagationReplayReport{}
			// Reports are wrapped in a CanonicalResultEnvelope by WriteCanonicalResults;
			// peel the outer envelope if present.
			if parsed, perr := unwrapCanonicalResultEnvelope(rb, report); perr == nil && parsed != nil {
				r.Report = parsed
			}
		}
	}

	if !cfg.Quiet {
		fmt.Printf("  [MultiNode] Completed %d nodes\n", cfg.NodeCount)
	}
	return results, nil
}

// runOneChild spawns and awaits one child process. Each child writes its
// artefacts to <OutputDir>/<NodeID>/.
func runOneChild(self string, cfg MultiNodeRunConfig, idx int) *MultiNodeChildResult {
	nodeID := cfg.NodeIDs[idx]
	skew := cfg.ClockSkewSeconds[idx]
	nodeDir := filepath.Join(cfg.OutputDir, nodeID)
	_ = os.MkdirAll(nodeDir, 0o755)

	reportPath := filepath.Join(nodeDir, MultiNodeReportName)
	manifestPath := filepath.Join(nodeDir, MultiNodeManifestName)
	logPath := filepath.Join(nodeDir, MultiNodeJSONLLogName)

	res := &MultiNodeChildResult{
		NodeID:       nodeID,
		ClockSkewSec: skew,
		ReportPath:   reportPath,
		ManifestPath: manifestPath,
		LogPath:      logPath,
	}

	start := time.Now()

	cmd := exec.Command(self, MultiNodeChildFlag,
		"--iterations", strconv.Itoa(cfg.Iterations),
		"--node-id", nodeID,
		"--node-dir", nodeDir,
	)
	cmd.Env = append(os.Environ(),
		EnvNodeID+"="+nodeID,
		EnvClockSkewSeconds+"="+strconv.Itoa(skew),
		// Isolate each child: do not fight over the default proof_logs/*.jsonl.
		"SARATHI_OUTPUT_LOG=",
	)

	stdout, stderr, exitCode, werr := runWithTimeout(cmd, MultiNodeChildTimeout)
	res.DurationNs = time.Since(start).Nanoseconds()
	res.ExitCode = exitCode
	res.StdoutTail = tailStringN(stdout, 400)
	res.StderrTail = tailStringN(stderr, 400)
	if werr != nil {
		res.Error = werr.Error()
	}
	return res
}

// runWithTimeout executes cmd and enforces a hard deadline. Returns
// (stdout, stderr, exitCode, err).
func runWithTimeout(cmd *exec.Cmd, d time.Duration) (string, string, int, error) {
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return "", "", -1, err
	}
	stderr, err := cmd.StderrPipe()
	if err != nil {
		_ = stdout.Close()
		return "", "", -1, err
	}
	if err := cmd.Start(); err != nil {
		return "", "", -1, err
	}

	outBytesCh := make(chan []byte, 1)
	errBytesCh := make(chan []byte, 1)
	go func() {
		b, _ := readAll(stdout)
		outBytesCh <- b
	}()
	go func() {
		b, _ := readAll(stderr)
		errBytesCh <- b
	}()

	done := make(chan error, 1)
	go func() { done <- cmd.Wait() }()

	timer := time.NewTimer(d)
	defer timer.Stop()

	select {
	case werr := <-done:
		outB := <-outBytesCh
		errB := <-errBytesCh
		exitCode := 0
		if werr != nil {
			exitCode = -1
			if ee, ok := werr.(*exec.ExitError); ok {
				exitCode = ee.ExitCode()
			}
		}
		return string(outB), string(errB), exitCode, werr
	case <-timer.C:
		if cmd.Process != nil {
			_ = cmd.Process.Kill()
		}
		<-done
		outB := <-outBytesCh
		errB := <-errBytesCh
		return string(outB), string(errB), -1, fmt.Errorf("multi_node: child timed out after %s", d)
	}
}

// readAll reads every byte from r until EOF. Separated out so multi_node_runner
// does not pull in io/ioutil for one call site.
func readAll(r interface{ Read(p []byte) (int, error) }) ([]byte, error) {
	buf := make([]byte, 0, 8192)
	tmp := make([]byte, 4096)
	for {
		n, err := r.Read(tmp)
		if n > 0 {
			buf = append(buf, tmp[:n]...)
		}
		if err != nil {
			if err.Error() == "EOF" || err.Error() == "io: read/write on closed pipe" {
				return buf, nil
			}
			return buf, nil
		}
	}
}

// tailStringN returns the last n bytes of s (or all of s if shorter).
func tailStringN(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return "..." + s[len(s)-n:]
}

// unwrapCanonicalResultEnvelope parses a file that may be either the raw
// typed report or the outer CanonicalResultEnvelope {results: …}. It returns
// the target pointer (which was mutated in place) if successful.
func unwrapCanonicalResultEnvelope(raw []byte, target *PropagationReplayReport) (*PropagationReplayReport, error) {
	// First, try envelope form.
	var envelope struct {
		Results json.RawMessage `json:"results"`
	}
	if err := json.Unmarshal(raw, &envelope); err == nil && len(envelope.Results) > 0 {
		if jerr := json.Unmarshal(envelope.Results, target); jerr == nil {
			return target, nil
		}
	}
	// Fallback: raw report.
	if jerr := json.Unmarshal(raw, target); jerr == nil {
		return target, nil
	}
	return nil, fmt.Errorf("cannot parse replay report payload")
}
