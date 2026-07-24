// parallel_execution_runner.go (v14.8 Sovereign Authority Closure)
//
// --parallel-execute [N] entry point.
//
// Runs N iterations through TWO pipelines side-by-side:
//
//   A. Sarathi pipeline   — full v14.7 live-integration chain (PDP → propagation
//                           → 3 OS peers → bucket readback → signed receipts)
//   B. Legacy pipeline    — in-tree reference shim (--legacy-shim, a separate
//                           process running an independent PDPAdapter), OR
//                           SARATHI_LEGACY_ENFORCE_URL when set (BHIV Core
//                           cutover mode).
//
// Each iteration's Sarathi response bytes and legacy response bytes are fed
// into CompareCanonicalResponses (parallel_execution_comparator.go). A
// divergence produces ERR_SHADOW_DIVERGENCE — the execution is failed closed
// and the divergence row journaled. Invariant INV-PARA-01:
//
//   For every parallel execution, sarathi_response_hash == legacy_response_hash
//   OR the execution is failed closed with ERR_SHADOW_DIVERGENCE.
//
// TAG: sovereign-authority-v14.8

package main

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// ParallelExecutionReportPath is the v14.8 artefact.
const ParallelExecutionReportPath = "parallel_execution_report.json"

// ShadowDivergenceLogPath is the append-only divergence journal.
const ShadowDivergenceLogPath = "proof_logs/shadow_divergence_log.jsonl"

// ParallelDivergenceLogPath is the v15.2 task2.md-mandated alias of the
// shadow_divergence_log. The runner writes BOTH files in lockstep so any
// reviewer following the task2.md deliverable list finds the file by its
// expected name without needing to learn the v14.8 history.
const ParallelDivergenceLogPath = "proof_logs/parallel_divergence_log.jsonl"

// ParallelExecutionSchemaVersion pins the report schema.
const ParallelExecutionSchemaVersion = "sarathi.parallel/v14.8"

// ParallelExecutionPolicyFailClosed is the default parallel-execution policy.
// When a divergence is detected, the Sarathi execution is failed closed
// (ERR_SHADOW_DIVERGENCE) rather than silently preferring either side.
const ParallelExecutionPolicyFailClosed = "fail_closed"

// ParallelExecutionPolicyLegacyFallback keeps legacy as the primary output
// path and only flags Sarathi output for auditor review. Disabled by default;
// the task.md contract is fail-closed.
const ParallelExecutionPolicyLegacyFallback = "legacy_fallback"

// ParallelExecutionRecord is one iteration's verdict.
type ParallelExecutionRecord struct {
	ExecutionID           string            `json:"execution_id"`
	DecisionID            string            `json:"decision_id"`
	SarathiResponseHash   string            `json:"sarathi_response_hash"`
	LegacyResponseHash    string            `json:"legacy_response_hash"`
	SarathiStructuralHash string            `json:"sarathi_structural_hash"`
	LegacyStructuralHash  string            `json:"legacy_structural_hash"`
	StructuralHashEqual   bool              `json:"structural_hash_equal"`
	SarathiBytesLength    int               `json:"sarathi_bytes_length"`
	LegacyBytesLength     int               `json:"legacy_bytes_length"`
	Match                 bool              `json:"match"`
	DivergenceCode        string            `json:"divergence_code,omitempty"`
	FieldDiffs            map[string]string `json:"field_diffs,omitempty"`
	GateSummary           GateSummary       `json:"gate_summary,omitempty"`
	BucketHash            string            `json:"bucket_hash,omitempty"`
	ComparedAt            string            `json:"compared_at"`
}

// ParallelExecutionReport is the aggregate output.
type ParallelExecutionReport struct {
	SchemaVersion    string                    `json:"schema_version"`
	GeneratedAt      string                    `json:"generated_at"`
	TargetExecutions int                       `json:"target_executions"`
	Policy           string                    `json:"policy"`
	SarathiAckAddr   string                    `json:"sarathi_ack_addr"`
	PeerAddrs        map[string]string         `json:"peer_addrs"`
	LegacyShimAddr   string                    `json:"legacy_shim_addr"`
	LegacyEnforceURL string                    `json:"legacy_enforce_url"`
	Matches          int                       `json:"matches"`
	Divergences      int                       `json:"divergences"`
	GateSatisfied    bool                      `json:"gate_satisfied"`
	Records          []ParallelExecutionRecord `json:"records"`
	Notes            []string                  `json:"notes,omitempty"`
}

// RunParallelExecution is the --parallel-execute entry point. Returns OS
// exit code (0 when matches == target and divergences == 0).
func RunParallelExecution(count int) int {
	if count <= 0 {
		count = ParallelExecuteDefaultCount
	}
	printHeader("PARALLEL EXECUTION (v14.8 — Sarathi vs legacy, fail-closed on divergence)")
	fmt.Printf("  executions=%d\n\n", count)

	policy := os.Getenv("SARATHI_PARALLEL_POLICY")
	if policy == "" {
		policy = ParallelExecutionPolicyFailClosed
	}

	rep := &ParallelExecutionReport{
		SchemaVersion:    ParallelExecutionSchemaVersion,
		GeneratedAt:      time.Now().UTC().Format(time.RFC3339Nano),
		TargetExecutions: count,
		Policy:           policy,
		PeerAddrs:        map[string]string{},
	}

	// ---- 1. Ack server + AckTracker (same as live-integration).
	ackAddr, ackSrv, err := startAckServer()
	if err != nil {
		rep.Notes = append(rep.Notes, "ack_server: "+err.Error())
		writeParallelReport(rep)
		return 1
	}
	defer ackSrv.Close()
	rep.SarathiAckAddr = ackAddr
	ackURL := "http://" + ackAddr + "/v1/downstream-ack"
	handshakeURL := "http://" + ackAddr + "/v1/handshake"

	ackTimeout := DefaultAckTimeout
	if ms, _ := strconv.Atoi(os.Getenv("SARATHI_DOWNSTREAM_ACK_TIMEOUT_MS")); ms > 0 {
		ackTimeout = time.Duration(ms) * time.Millisecond
	}
	tracker := NewAckTracker(ackTimeout)
	InstallGlobalAckTracker(tracker)

	// ---- 2. Spawn the v14.7 peer set.
	selfPath, err := os.Executable()
	if err != nil {
		rep.Notes = append(rep.Notes, "executable: "+err.Error())
		writeParallelReport(rep)
		return 1
	}
	peerProcs, peerAddrs, err := spawnPeers(selfPath, ackURL, handshakeURL)
	if err != nil {
		rep.Notes = append(rep.Notes, "peer_spawn: "+err.Error())
		stopPeers(peerProcs)
		writeParallelReport(rep)
		return 1
	}
	defer stopPeers(peerProcs)
	for k, addr := range peerAddrs {
		rep.PeerAddrs[string(k)] = addr
	}
	for kind, addr := range peerAddrs {
		if err := waitForHealth("http://"+addr+"/health", 5*time.Second); err != nil {
			rep.Notes = append(rep.Notes, fmt.Sprintf("peer %s health: %v", kind, err))
			writeParallelReport(rep)
			return 1
		}
	}

	_ = os.Setenv("SARATHI_ROUTE_CORE_URL", "http://"+peerAddrs[PeerCore]+"/v1/enforce")
	_ = os.Setenv("SARATHI_ROUTE_INSIGHTFLOW_URL", "http://"+peerAddrs[PeerInsightFlow]+"/v1/observe")
	_ = os.Setenv("SARATHI_ROUTE_BUCKET_URL", "http://"+peerAddrs[PeerBucket]+"/v1/audit")
	bucketBase := "http://" + peerAddrs[PeerBucket]

	// ---- 3. Build fixture + resolve legacy enforce URL.
	fx, ferr := BuildOrLoadReplayFixture()
	if ferr != nil {
		rep.Notes = append(rep.Notes, "fixture: "+ferr.Error())
		writeParallelReport(rep)
		return 1
	}

	legacyURL := os.Getenv("SARATHI_LEGACY_ENFORCE_URL")
	var shimProc *exec.Cmd
	if legacyURL == "" {
		// Spawn the in-tree legacy shim.
		shimAddr, cmd, serr := spawnLegacyShim(selfPath, fx)
		if serr != nil {
			rep.Notes = append(rep.Notes, "legacy_shim_spawn: "+serr.Error())
			writeParallelReport(rep)
			return 1
		}
		shimProc = cmd
		legacyURL = "http://" + shimAddr + LegacyEnforceEndpoint
		rep.LegacyShimAddr = shimAddr
	}
	rep.LegacyEnforceURL = legacyURL
	defer func() {
		if shimProc != nil && shimProc.Process != nil {
			_ = shimProc.Process.Kill()
			_, _ = shimProc.Process.Wait()
		}
	}()

	// Wait for legacy endpoint health.
	if strings.HasPrefix(legacyURL, "http://") || strings.HasPrefix(legacyURL, "https://") {
		base := strings.TrimSuffix(legacyURL, LegacyEnforceEndpoint)
		if err := waitForHealth(base+"/health", 5*time.Second); err != nil {
			// Real BHIV-Core endpoints may not expose /health — log but continue.
			rep.Notes = append(rep.Notes, "legacy_health_skip: "+err.Error())
		}
	}

	fmt.Printf("  peers healthy; legacy_enforce=%s\n\n", legacyURL)

	// ---- 4. Build Sarathi PDP pipeline (runner-local).
	agentReg := NewRegistryInterface()
	ea := NewEnforcementAdapter(nil, nil, agentReg, nil)
	ea.InitExternalMode()
	// v15.2 FIX: wire FallbackAuditSink so JSONL backup is generated.
	auditSink, asErr := WireFallbackAuditSink(ea)
	if asErr != nil {
		rep.Notes = append(rep.Notes, "audit_sink_wire_failed: "+asErr.Error())
		writeParallelReport(rep)
		return 1
	}
	defer auditSink.Close()
	if err := ea.GetEvaluatorRegistry().RegisterEvaluator(
		fx.EvaluatorID, "parallel execution fixture evaluator", fx.PublicKey,
		map[string]string{"fixture": "true"}, "parallel_execute",
	); err != nil {
		rep.Notes = append(rep.Notes, "register_evaluator: "+err.Error())
		writeParallelReport(rep)
		return 1
	}
	mc := NewModeController(BHIVModeExternal)
	pa := NewPDPAdapter(ea, mc)

	// ---- 5. Iterate.
	for i := 0; i < count; i++ {
		pa.ResetReplayTrackerForHarness()
		execID := fmt.Sprintf("EXEC-PARA-%04d", i+1)
		corrID := fmt.Sprintf("corr-para-%04d", i+1)

		iterBytes, berr := buildParallelIterationFixture(fx, i+1)
		if berr != nil {
			rep.Notes = append(rep.Notes, fmt.Sprintf("iter %d fixture: %v", i+1, berr))
			rep.Divergences++
			continue
		}

		rec := runSingleParallelExecution(pa, iterBytes, execID, corrID,
			tracker, bucketBase, legacyURL, auditSink)
		rep.Records = append(rep.Records, rec)
		if rec.Match {
			rep.Matches++
		} else {
			rep.Divergences++
		}
		// v15.2 task2.md compliance: every parallel execution gets a row
		// (match or divergence) so the parallel_divergence_log is a complete
		// field-level comparison record, not just a divergence-only journal.
		_ = appendShadowDivergenceRow(rec)
		fmt.Printf("  [%03d/%03d] %s match=%t s_hash=%s l_hash=%s\n",
			i+1, count, execID, rec.Match,
			shortHash(rec.SarathiResponseHash), shortHash(rec.LegacyResponseHash))
	}

	rep.GateSatisfied = rep.Matches == rep.TargetExecutions && rep.Divergences == 0
	writeParallelReport(rep)

	fmt.Printf("\n  PARALLEL EXECUTION: matches=%d/%d divergences=%d gate_satisfied=%t\n",
		rep.Matches, rep.TargetExecutions, rep.Divergences, rep.GateSatisfied)

	if rep.GateSatisfied {
		return 0
	}
	return 1
}

// RunParallelExecutionSuite runs --parallel-execute then writes a
// task.md-Phase-2-shaped report summarising matches vs divergences.
func RunParallelExecutionSuite(count int) int {
	exitCode := RunParallelExecution(count)
	raw, err := os.ReadFile(ParallelExecutionReportPath)
	if err != nil {
		return exitCode
	}
	var rep ParallelExecutionReport
	if err := json.Unmarshal(raw, &rep); err != nil {
		return exitCode
	}
	suite := map[string]interface{}{
		"schema_version": "sarathi.parallel.suite/v14.8",
		"generated_at":   time.Now().UTC().Format(time.RFC3339Nano),
		"total":          rep.TargetExecutions,
		"matches":        rep.Matches,
		"divergences":    rep.Divergences,
		"gate_satisfied": rep.GateSatisfied,
		"policy":         rep.Policy,
	}
	_ = writeJSONFile("parallel_execution_suite_results.json", suite)
	return exitCode
}

// runSingleParallelExecution executes one iteration through both pipelines
// and compares the results.
func runSingleParallelExecution(
	pa *PDPAdapter, iterBytes []byte, execID, corrID string,
	tracker *AckTracker, bucketBase, legacyURL string, auditSink AuditSink,
) ParallelExecutionRecord {
	rec := ParallelExecutionRecord{
		ExecutionID: execID,
		ComparedAt:  time.Now().UTC().Format(time.RFC3339Nano),
	}

	// --- Sarathi pipeline (same sequence as live_integration_runner).
	sarathiLive := runSingleLiveExecution(pa, iterBytes, execID, corrID, tracker, bucketBase, auditSink)
	rec.DecisionID = sarathiLive.DecisionID
	rec.SarathiResponseHash = sarathiLive.ResponseHash
	rec.BucketHash = sarathiLive.BucketHash
	rec.GateSummary = sarathiLive.GateSummary
	if sarathiLive.ErrorCode != "" || !sarathiLive.Match {
		rec.Match = false
		rec.DivergenceCode = CodeShadowDivergence
		rec.FieldDiffs = map[string]string{
			"sarathi_pipeline_error": sarathiLive.ErrorCode + ": " + sarathiLive.Detail,
		}
		return rec
	}
	sarathiBytes, serr := bucketReadbackBytes(bucketBase, sarathiLive.DecisionID)
	if serr != nil {
		rec.Match = false
		rec.DivergenceCode = CodeShadowDivergence
		rec.FieldDiffs = map[string]string{"sarathi_readback_error": serr.Error()}
		return rec
	}
	rec.SarathiBytesLength = len(sarathiBytes)

	// --- Legacy pipeline.
	legacyBytes, lerr := postToLegacyEnforce(legacyURL, iterBytes, execID, corrID)
	if lerr != nil {
		rec.Match = false
		rec.DivergenceCode = CodeLegacyShimUnavailable
		rec.FieldDiffs = map[string]string{"legacy_pipeline_error": lerr.Error()}
		return rec
	}
	rec.LegacyBytesLength = len(legacyBytes)

	// --- Compare.
	diverge := CompareCanonicalResponses(sarathiBytes, legacyBytes)
	rec.SarathiResponseHash = diverge.SarathiResponseHash
	rec.LegacyResponseHash = diverge.LegacyResponseHash
	rec.SarathiStructuralHash = diverge.SarathiStructuralHash
	rec.LegacyStructuralHash = diverge.LegacyStructuralHash
	rec.StructuralHashEqual = diverge.StructuralHashEqual
	rec.Match = diverge.Match
	rec.FieldDiffs = diverge.FieldDiffs
	rec.DivergenceCode = diverge.DivergenceCode
	if rec.DecisionID == "" {
		rec.DecisionID = diverge.DecisionID
	}
	return rec
}

// bucketReadbackBytes fetches the bytes the Bucket peer persisted for the
// given decision_id. These are the "Sarathi canonical response bytes" the
// comparator evaluates. Reusing the bucket peer's GET path keeps the
// comparator honest — it sees the same bytes a downstream system would.
func bucketReadbackBytes(bucketBase, decisionID string) ([]byte, error) {
	url := fmt.Sprintf("%s/v1/audit/%s", bucketBase, decisionID)
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	client := &http.Client{Timeout: 3 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("bucket_get status=%d", resp.StatusCode)
	}
	return io.ReadAll(io.LimitReader(resp.Body, LivePeerMaxBodyBytes))
}

// postToLegacyEnforce sends the raw decision bytes to the legacy enforcer
// endpoint and parses out its canonical response bytes. When the shim is
// in-tree the response body is the LegacyShimResponse JSON; when the URL
// points at a real BHIV Core endpoint the response may be the canonical
// bytes themselves — we support both shapes.
func postToLegacyEnforce(url string, raw []byte, execID, corrID string) ([]byte, error) {
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set(HeaderExecutionID, execID)
	req.Header.Set(HeaderCorrelationID, corrID)

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(io.LimitReader(resp.Body, LivePeerMaxBodyBytes))
	if err != nil {
		return nil, err
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("legacy_enforce status=%d body=%s",
			resp.StatusCode, safePreview(body, 256))
	}

	// Try to interpret as LegacyShimResponse first.
	var shimResp LegacyShimResponse
	if err := json.Unmarshal(body, &shimResp); err == nil && shimResp.CanonicalResponseBytesHex != "" {
		canon, derr := hex.DecodeString(shimResp.CanonicalResponseBytesHex)
		if derr != nil {
			return nil, fmt.Errorf("hex decode: %w", derr)
		}
		return canon, nil
	}
	// Otherwise treat the raw body as the canonical response bytes directly
	// — this is the contract a real BHIV Core endpoint should satisfy.
	return body, nil
}

// spawnLegacyShim boots the in-tree shim as a child process, waits for it to
// write its bound address, then registers the fixture evaluator with it so
// incoming decisions pass the shim's PDP integrity check.
func spawnLegacyShim(selfPath string, fx *ReplayFixture) (string, *exec.Cmd, error) {
	// Remove any stale address file.
	_ = os.Remove(LegacyShimAddrFile)

	cmd := exec.Command(selfPath, LegacyShimFlag)
	cmd.Env = append(os.Environ(),
		fmt.Sprintf("SARATHI_PEER_PARENT_PID=%d", os.Getpid()),
		fmt.Sprintf("%s=%s:0", LegacyShimDefaultAddrEnv, bindHost()),
	)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Start(); err != nil {
		return "", nil, fmt.Errorf("start: %w", err)
	}

	// Wait for shim to write its addr file.
	var addr string
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		b, err := os.ReadFile(LegacyShimAddrFile)
		if err == nil && len(b) > 0 {
			addr = strings.TrimSpace(string(b))
			break
		}
		time.Sleep(100 * time.Millisecond)
	}
	if addr == "" {
		_ = cmd.Process.Kill()
		return "", nil, fmt.Errorf("shim did not publish addr within 5s")
	}

	// Wait for /health.
	if err := waitForHealth("http://"+addr+"/health", 5*time.Second); err != nil {
		_ = cmd.Process.Kill()
		return "", nil, fmt.Errorf("shim health: %w", err)
	}

	// Register the fixture evaluator with the shim so its PDP pipeline will
	// accept the decisions the runner is about to POST.
	regBody, _ := json.Marshal(map[string]string{
		"evaluator_id":   fx.EvaluatorID,
		"public_key_hex": hex.EncodeToString(fx.PublicKey),
	})
	regReq, _ := http.NewRequest(http.MethodPost,
		"http://"+addr+"/v1/register-evaluator", bytes.NewReader(regBody))
	regReq.Header.Set("Content-Type", "application/json")
	client := &http.Client{Timeout: 3 * time.Second}
	regResp, err := client.Do(regReq)
	if err != nil {
		_ = cmd.Process.Kill()
		return "", nil, fmt.Errorf("register evaluator: %w", err)
	}
	_ = regResp.Body.Close()
	if regResp.StatusCode != http.StatusOK {
		_ = cmd.Process.Kill()
		return "", nil, fmt.Errorf("register evaluator status=%d", regResp.StatusCode)
	}

	return addr, cmd, nil
}

// buildParallelIterationFixture mints a fresh unique decision for iteration i
// using the replay fixture's signing key.
func buildParallelIterationFixture(fx *ReplayFixture, iter int) ([]byte, error) {
	var d ExternalDecision
	if err := json.Unmarshal(fx.Bytes, &d); err != nil {
		return nil, fmt.Errorf("unmarshal fixture: %w", err)
	}
	d.DecisionID = fmt.Sprintf("DEC-PARA-%04d", iter)
	d.Nonce = fmt.Sprintf("NONCE-PARA-%04d", iter)
	d.DecisionHash = d.computeHash()
	d.DecisionCoreHash = d.computeCoreHash()
	d.SignDecision(fx.PrivateKey)
	return json.Marshal(&d)
}

func appendShadowDivergenceRow(rec ParallelExecutionRecord) error {
	if err := os.MkdirAll(filepath.Dir(ShadowDivergenceLogPath), 0o755); err != nil {
		return err
	}
	row := ShadowDivergenceRecord{
		SchemaVersion:         ShadowDivergenceSchemaVersion,
		ExecutionID:           rec.ExecutionID,
		DecisionID:            rec.DecisionID,
		SarathiResponseHash:   rec.SarathiResponseHash,
		LegacyResponseHash:    rec.LegacyResponseHash,
		SarathiStructuralHash: rec.SarathiStructuralHash,
		LegacyStructuralHash:  rec.LegacyStructuralHash,
		StructuralHashEqual:   rec.StructuralHashEqual,
		Match:                 rec.Match,
		SarathiBytesLength:    rec.SarathiBytesLength,
		LegacyBytesLength:     rec.LegacyBytesLength,
		FieldDiffs:            rec.FieldDiffs,
		DivergenceCode:        rec.DivergenceCode,
		VerifiedAt:            rec.ComparedAt,
	}
	row.HashEqual = row.SarathiResponseHash == row.LegacyResponseHash
	b, err := json.Marshal(row)
	if err != nil {
		return err
	}
	line := append(b, '\n')
	for _, path := range []string{ShadowDivergenceLogPath, ParallelDivergenceLogPath} {
		f, err := os.OpenFile(path,
			os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
		if err != nil {
			return err
		}
		if _, err := f.Write(line); err != nil {
			_ = f.Close()
			return err
		}
		if err := f.Sync(); err != nil {
			_ = f.Close()
			return err
		}
		_ = f.Close()
	}
	return nil
}

func writeParallelReport(rep *ParallelExecutionReport) {
	_ = writeJSONFile(ParallelExecutionReportPath, rep)
}

func shortHash(h string) string {
	if len(h) >= 12 {
		return h[:12]
	}
	return h
}
