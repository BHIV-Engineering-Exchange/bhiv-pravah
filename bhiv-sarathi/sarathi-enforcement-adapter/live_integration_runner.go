// live_integration_runner.go (v14.7 Live Integration Closure)
//
// The orchestrator. Spawns three REAL OS processes (Core/InsightFlow/Bucket
// peers), starts a Sarathi-side HTTP server for signed receipts + handshake,
// runs N executions through the actual v14.5 propagation path against the
// peers' real TCP listeners, waits for all three signed receipts, performs
// a Bucket GET read-back, and writes live_integration_report.json.
//
// No mocks. No httptest.Server. No in-memory stores on the propagation path.
//
// Flow per execution:
//
//   1. BuildOrLoadReplayFixture → fx.Bytes
//   2. PDPAdapter.Ingest(fx.Bytes, execID, corrID) → PropagationEnvelope
//   3. AckTracker.Open(execID, decisionID, responseHash) → gate
//   4. router.RoutePropagation(env) → 3 synchronous 200/202 responses
//   5. gate.Wait() → 3 signed receipts verified + recorded
//   6. VerifyBucketReadback(bucketURL, decisionID, env) → bucket_hash match
//   7. Append {execution_id, response_hash, bucket_hash, match=true} to
//      state_verification_log.jsonl
//
// Any failure along the chain fails the execution closed and emits the
// corresponding ERR_* code into the aggregate report.
//
// TAG: live-integration

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"sync"
	"time"
)

// LiveIntegrationReportPath is the canonical v14.7 artefact.
const LiveIntegrationReportPath = "live_integration_report.json"

// ----------------------------------------------------------------------------
// v14.8 host-binding helpers (additive; preserves v14.7 localhost defaults).
//
// When SARATHI_LISTEN_HOST is unset, bindHost() returns "127.0.0.1" — the
// exact v14.7 behaviour. When set (e.g. to "0.0.0.0" for cross-machine), the
// Sarathi ack server and the spawned peers listen on the operator-chosen
// interface.
//
// advertiseHost() is the host the peer process should be *told* to reach
// Sarathi on (via SARATHI_PEER_ACK_URL / SARATHI_PEER_HANDSHAKE_URL). When
// Sarathi binds to 0.0.0.0 the operator must set SARATHI_ADVERTISE_HOST to
// the routable IP peers will use; otherwise we fall back to the bind host.
// ----------------------------------------------------------------------------

// bindHost returns the host interface Sarathi + its locally-spawned peers
// should listen on.
func bindHost() string {
	if h := os.Getenv("SARATHI_LISTEN_HOST"); h != "" {
		return h
	}
	return "127.0.0.1"
}

// advertiseHost returns the routable host peers should use to reach Sarathi.
// Falls back to bindHost for backward compatibility with v14.7 single-host
// setups; operators running cross-machine must set SARATHI_ADVERTISE_HOST to
// the routable IP of the Sarathi machine.
func advertiseHost() string {
	if h := os.Getenv("SARATHI_ADVERTISE_HOST"); h != "" {
		return h
	}
	host := bindHost()
	if host == "0.0.0.0" || host == "::" {
		// 0.0.0.0 is not routable as a URL; fall back to loopback so peers
		// on the same host can still reach Sarathi. Cross-machine operators
		// should always set SARATHI_ADVERTISE_HOST explicitly.
		return "127.0.0.1"
	}
	return host
}

// StateVerificationLogPath is appended once per execution.
const StateVerificationLogPath = "proof_logs/state_verification_log.jsonl"

// LiveIntegrationSchemaVersion pins the report schema.
const LiveIntegrationSchemaVersion = "sarathi.live.integration/v14.7"

// LiveIntegrationReport is the aggregate output.
type LiveIntegrationReport struct {
	SchemaVersion           string                     `json:"schema_version"`
	GeneratedAt             string                     `json:"generated_at"`
	TargetCount             int                        `json:"target_executions"`
	VerifiedGateCount       int                        `json:"verified_gate_count"`
	BucketReadbackMatches   int                        `json:"bucket_readback_matches"`
	Failures                int                        `json:"failures"`
	GateSatisfied           bool                       `json:"gate_satisfied"`
	SarathiAckAddr          string                     `json:"sarathi_ack_addr"`
	PeerAddrs               map[string]string          `json:"peer_addrs"`
	Records                 []LiveIntegrationRecord    `json:"records"`
	Notes                   []string                   `json:"notes,omitempty"`
}

// LiveIntegrationRecord is one execution's verdict.
type LiveIntegrationRecord struct {
	ExecutionID  string      `json:"execution_id"`
	DecisionID   string      `json:"decision_id"`
	ResponseHash string      `json:"response_hash"`
	BucketHash   string      `json:"bucket_hash"`
	Match        bool        `json:"match"`
	GateSummary  GateSummary `json:"gate_summary"`
	ErrorCode    string      `json:"error_code,omitempty"`
	Detail       string      `json:"detail,omitempty"`
}

// RunLiveIntegration is the --live-integration entry point. Returns the OS
// exit code (0 on success).
func RunLiveIntegration(count int) int {
	if count <= 0 {
		count = LiveIntegrationDefaultCount
	}
	printHeader("LIVE INTEGRATION (v14.7 — REAL peers, REAL disk, REAL signed receipts)")
	fmt.Printf("  executions=%d peers=core,insightflow,bucket\n\n", count)

	rep := &LiveIntegrationReport{
		SchemaVersion: LiveIntegrationSchemaVersion,
		GeneratedAt:   time.Now().UTC().Format(time.RFC3339Nano),
		TargetCount:   count,
		PeerAddrs:     map[string]string{},
	}

	// ---- 1. Start Sarathi-side HTTP server for handshake + ACK receipts.
	ackAddr, ackSrv, err := startAckServer()
	if err != nil {
		rep.Notes = append(rep.Notes, "ack_server_start_failed: "+err.Error())
		writeLiveReport(rep)
		return 1
	}
	defer ackSrv.Close()
	rep.SarathiAckAddr = ackAddr
	ackURL := "http://" + ackAddr + "/v1/downstream-ack"
	handshakeURL := "http://" + ackAddr + "/v1/handshake"

	// ---- 2. Install AckTracker (process-wide).
	ackTimeout := DefaultAckTimeout
	if ms, _ := strconv.Atoi(os.Getenv("SARATHI_DOWNSTREAM_ACK_TIMEOUT_MS")); ms > 0 {
		ackTimeout = time.Duration(ms) * time.Millisecond
	}
	tracker := NewAckTracker(ackTimeout)
	InstallGlobalAckTracker(tracker)

	// ---- 3. Spawn 3 peers on free ports.
	selfPath, err := os.Executable()
	if err != nil {
		rep.Notes = append(rep.Notes, "executable_path_failed: "+err.Error())
		writeLiveReport(rep)
		return 1
	}
	peerProcs, peerAddrs, err := spawnPeers(selfPath, ackURL, handshakeURL)
	if err != nil {
		rep.Notes = append(rep.Notes, "peer_spawn_failed: "+err.Error())
		stopPeers(peerProcs)
		writeLiveReport(rep)
		return 1
	}
	defer stopPeers(peerProcs)

	for k, addr := range peerAddrs {
		rep.PeerAddrs[string(k)] = addr
	}

	// ---- 4. Wait for each peer /health.
	for kind, addr := range peerAddrs {
		if err := waitForHealth("http://"+addr+"/health", 5*time.Second); err != nil {
			rep.Notes = append(rep.Notes, fmt.Sprintf("peer %s health_wait: %v", kind, err))
			writeLiveReport(rep)
			return 1
		}
	}
	fmt.Printf("  all 3 peers healthy; ack_server=%s\n\n", ackAddr)

	// ---- 5. Point routing env vars at peer URLs.
	_ = os.Setenv("SARATHI_ROUTE_CORE_URL", "http://"+peerAddrs[PeerCore]+"/v1/enforce")
	_ = os.Setenv("SARATHI_ROUTE_INSIGHTFLOW_URL", "http://"+peerAddrs[PeerInsightFlow]+"/v1/observe")
	_ = os.Setenv("SARATHI_ROUTE_BUCKET_URL", "http://"+peerAddrs[PeerBucket]+"/v1/audit")

	bucketBase := "http://" + peerAddrs[PeerBucket]

	// ---- 6. Run N executions.
	fx, ferr := BuildOrLoadReplayFixture()
	if ferr != nil {
		rep.Notes = append(rep.Notes, "fixture_build_failed: "+ferr.Error())
		writeLiveReport(rep)
		return 1
	}

	// Evaluator registration + adapter (mirrors cross_system_integration_validator).
	agentReg := NewRegistryInterface()
	ea := NewEnforcementAdapter(nil, nil, agentReg, nil)
	ea.InitExternalMode()
	// v15.2 FIX: wire FallbackAuditSink so proof_logs/enforcement_audit_backup.jsonl
	// is generated. Prior versions left the sink nil here, which silently
	// suppressed every JSONL backup line during --live-integration. See
	// VC_CALL_VALIDATION_SCRIPT3 §3 (trace validation) — that path requires
	// the JSONL backup to read trace_id from.
	auditSink, asErr := WireFallbackAuditSink(ea)
	if asErr != nil {
		rep.Notes = append(rep.Notes, "audit_sink_wire_failed: "+asErr.Error())
		writeLiveReport(rep)
		return 1
	}
	defer auditSink.Close()

	if err := ea.GetEvaluatorRegistry().RegisterEvaluator(
		fx.EvaluatorID, "live integration fixture evaluator", fx.PublicKey,
		map[string]string{"fixture": "true"}, "live_integration",
	); err != nil {
		rep.Notes = append(rep.Notes, "register_evaluator_failed: "+err.Error())
		writeLiveReport(rep)
		return 1
	}
	mc := NewModeController(BHIVModeExternal)
	pa := NewPDPAdapter(ea, mc)

	for i := 0; i < count; i++ {
		pa.ResetReplayTrackerForHarness()
		execID := fmt.Sprintf("EXEC-LIVE-%04d", i+1)
		corrID := fmt.Sprintf("corr-live-%04d", i+1)

		// Each iteration gets a UNIQUE signed decision so peers see distinct
		// decision_ids — the fixture would otherwise emit the same decision_id
		// across iterations and trigger the peers' drift-rejection guard (which
		// exists precisely to detect same-id-different-body divergence).
		iterBytes, berr := buildLiveIterationFixture(fx, i+1)
		if berr != nil {
			rep.Notes = append(rep.Notes, fmt.Sprintf("iter %d fixture: %v", i+1, berr))
			rep.Failures++
			continue
		}

		record := runSingleLiveExecution(pa, iterBytes, execID, corrID, tracker, bucketBase, auditSink)
		rep.Records = append(rep.Records, record)
		if record.Match && record.GateSummary.Satisfied {
			rep.VerifiedGateCount++
			rep.BucketReadbackMatches++
		} else {
			rep.Failures++
		}
		fmt.Printf("  [%03d/%03d] %s match=%t gate=%t\n",
			i+1, count, execID, record.Match, record.GateSummary.Satisfied)
	}

	rep.GateSatisfied = rep.VerifiedGateCount == rep.TargetCount && rep.Failures == 0
	writeLiveReport(rep)

	fmt.Printf("\n  LIVE INTEGRATION: verified=%d/%d bucket_match=%d failures=%d gate_satisfied=%t\n",
		rep.VerifiedGateCount, rep.TargetCount, rep.BucketReadbackMatches, rep.Failures, rep.GateSatisfied)

	if rep.GateSatisfied {
		return 0
	}
	return 1
}

// RunLiveIntegrationSuite runs the live-integration pipeline with the full
// test-suite semantics: writes integration_test_suite_results.json in the
// shape task.md Phase 5 requires.
func RunLiveIntegrationSuite(count int) int {
	exitCode := RunLiveIntegration(count)
	// Rewrite the report in the task.md Phase 5 shape.
	raw, err := os.ReadFile(LiveIntegrationReportPath)
	if err != nil {
		return exitCode
	}
	var rep LiveIntegrationReport
	if err := json.Unmarshal(raw, &rep); err != nil {
		return exitCode
	}
	suite := map[string]interface{}{
		"schema_version": "sarathi.live.suite/v14.7",
		"generated_at":   time.Now().UTC().Format(time.RFC3339Nano),
		"total":          rep.TargetCount,
		"passed":         rep.VerifiedGateCount,
		"failed":         rep.Failures,
		"records":        simplifiedRecords(rep.Records),
	}
	_ = writeJSONFile("integration_test_suite_results.json", suite)
	return exitCode
}

func simplifiedRecords(records []LiveIntegrationRecord) []map[string]interface{} {
	out := make([]map[string]interface{}, 0, len(records))
	for _, r := range records {
		out = append(out, map[string]interface{}{
			"execution_id":  r.ExecutionID,
			"response_hash": r.ResponseHash,
			"bucket_hash":   r.BucketHash,
			"match":         r.Match,
		})
	}
	return out
}

func runSingleLiveExecution(
	pa *PDPAdapter, fxBytes []byte, execID, corrID string,
	tracker *AckTracker, bucketBase string, auditSink AuditSink,
) LiveIntegrationRecord {
	rec := LiveIntegrationRecord{
		ExecutionID: execID,
	}

	env, ierr := pa.Ingest(fxBytes, execID, corrID, nil)
	if ierr != nil {
		rec.ErrorCode = CodePropagationByteMismatch
		rec.Detail = "ingest: " + ierr.Error()
		return rec
	}
	rec.DecisionID = env.DecisionID()
	rec.ResponseHash = env.ResponseHash()

	// v15.2 FIX: record the enforcement decision into the JSONL backup so
	// VC_CALL_VALIDATION_SCRIPT3 §3 trace validation can read trace_id +
	// decision_id + response_hash + chain_binding_hash off
	// proof_logs/enforcement_audit_backup.jsonl.
	_ = RecordHarnessEnforcement(auditSink, env, fxBytes, execID, corrID, "")

	// Open gate BEFORE routing so peer receipts always find an open gate.
	gate := tracker.Open(execID, env.DecisionID(), env.ResponseHash())
	defer tracker.Close(execID)

	// Wire + route via real router (same code path v14.6 uses, just pointed
	// at real peer processes via env vars).
	router := NewMultiSystemRouter(nil)
	wired := router.WireDeterministicTargets(env)
	if wired < 3 {
		rec.ErrorCode = CodeLiveIntegrationGateFailed
		rec.Detail = fmt.Sprintf("wired=%d", wired)
		return rec
	}
	propRes, perr := router.RoutePropagation(env)
	if perr != nil {
		rec.ErrorCode = CodePropagationChainBroken
		rec.Detail = "route: " + perr.Error()
		return rec
	}
	if propRes.ChainHalted {
		rec.ErrorCode = propRes.HaltCode
		if rec.ErrorCode == "" {
			rec.ErrorCode = CodePropagationChainBroken
		}
		rec.Detail = fmt.Sprintf("chain_halted_at=%s", propRes.HaltHop)
		return rec
	}

	// Wait for three signed receipts.
	satisfied, summary := gate.Wait()
	rec.GateSummary = summary
	if !satisfied {
		rec.ErrorCode = CodeDownstreamAckTimeout
		rec.Detail = fmt.Sprintf("missing=%v errors=%v", summary.MissingPeers, summary.Errors)
		return rec
	}

	// Bucket read-back — end-to-end state proof.
	readback := VerifyBucketReadback(context.Background(), bucketBase, env.DecisionID(), execID,
		env.CanonicalResponseBytes(), env.ResponseHash())
	rec.BucketHash = readback.BucketHash
	rec.Match = readback.Match
	if !readback.Match {
		rec.ErrorCode = readback.ErrorCode
		rec.Detail = readback.Detail
		return rec
	}

	// Append to Phase-5 per-execution state verification log.
	_ = appendStateVerificationLine(rec)
	return rec
}

func appendStateVerificationLine(rec LiveIntegrationRecord) error {
	if err := os.MkdirAll(filepath.Dir(StateVerificationLogPath), 0o755); err != nil {
		return err
	}
	line := map[string]interface{}{
		"execution_id":  rec.ExecutionID,
		"response_hash": rec.ResponseHash,
		"bucket_hash":   rec.BucketHash,
		"match":         rec.Match,
		"verified_at":   time.Now().UTC().Format(time.RFC3339Nano),
	}
	b, err := json.Marshal(line)
	if err != nil {
		return err
	}
	f, err := os.OpenFile(StateVerificationLogPath,
		os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()
	if _, err := f.Write(append(b, '\n')); err != nil {
		return err
	}
	return f.Sync()
}

// buildLiveIterationFixture mints a fresh signed ExternalDecision using the
// replay fixture's signing key, but with a per-iteration unique DecisionID
// and Nonce. This produces N distinct, legitimately-signed decisions so the
// peers see unique decision_ids across iterations — the drift-rejection
// guard still fires correctly on same-id-different-body attacks.
func buildLiveIterationFixture(fx *ReplayFixture, iter int) ([]byte, error) {
	// Parse the cached fixture bytes to inherit its canonical shape.
	var d ExternalDecision
	if err := json.Unmarshal(fx.Bytes, &d); err != nil {
		return nil, fmt.Errorf("unmarshal fixture: %w", err)
	}
	d.DecisionID = fmt.Sprintf("DEC-LIVE-%04d", iter)
	d.Nonce = fmt.Sprintf("NONCE-LIVE-%04d", iter)
	// Recompute hashes, then re-sign.
	d.DecisionHash = d.computeHash()
	d.DecisionCoreHash = d.computeCoreHash()
	d.SignDecision(fx.PrivateKey)
	return json.Marshal(&d)
}

// ============================================================================
// Sarathi-side HTTP server for handshake + ACK receipts
// ============================================================================

func startAckServer() (string, *http.Server, error) {
	mux := http.NewServeMux()
	RegisterDownstreamAckRoutes(mux)
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"ok":true}`))
	})
	ln, err := net.Listen("tcp", bindHost()+":0")
	if err != nil {
		return "", nil, err
	}
	srv := &http.Server{
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}
	go func() { _ = srv.Serve(ln) }()
	// Build the advertised URL using advertiseHost() so peers — possibly on a
	// different machine — can reach back to Sarathi even when bind is 0.0.0.0.
	port := ln.Addr().(*net.TCPAddr).Port
	return fmt.Sprintf("%s:%d", advertiseHost(), port), srv, nil
}

// ============================================================================
// Peer spawn / stop / health
// ============================================================================

type peerProc struct {
	kind PeerKind
	cmd  *exec.Cmd
	addr string
}

func spawnPeers(self, ackURL, handshakeURL string) ([]*peerProc, map[PeerKind]string, error) {
	pid := os.Getpid()
	peers := []*peerProc{}
	addrs := map[PeerKind]string{}
	flags := map[PeerKind]string{
		PeerCore:        LivePeerCoreFlag,
		PeerInsightFlow: LivePeerInsightFlowFlag,
		PeerBucket:      LivePeerBucketFlag,
	}
	for _, kind := range []PeerKind{PeerCore, PeerInsightFlow, PeerBucket} {
		port, err := pickFreePort()
		if err != nil {
			return peers, addrs, fmt.Errorf("pick port for %s: %w", kind, err)
		}
		bindAddr := fmt.Sprintf("%s:%d", bindHost(), port)
		// The routable address Sarathi itself will use to reach the peer and
		// the address reported in live_integration_report.json. When the
		// operator has not overridden, bindAddr == advertiseAddr (v14.7
		// behaviour preserved). When bindHost=0.0.0.0 the advertise host
		// falls back to 127.0.0.1 unless SARATHI_ADVERTISE_HOST is set.
		advertiseAddr := fmt.Sprintf("%s:%d", advertiseHost(), port)
		cmd := exec.Command(self, flags[kind])
		cmd.Env = append(os.Environ(),
			"SARATHI_PEER_ADDR="+bindAddr,
			"SARATHI_PEER_STORAGE_ROOT=live",
			"SARATHI_PEER_ACK_URL="+ackURL,
			"SARATHI_PEER_HANDSHAKE_URL="+handshakeURL,
			"SARATHI_PEER_PARENT_PID="+strconv.Itoa(pid),
			"SARATHI_LIVE_INTEGRATION=1",
		)
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if err := cmd.Start(); err != nil {
			return peers, addrs, fmt.Errorf("spawn %s: %w", kind, err)
		}
		peers = append(peers, &peerProc{kind: kind, cmd: cmd, addr: advertiseAddr})
		addrs[kind] = advertiseAddr
	}
	return peers, addrs, nil
}

func stopPeers(peers []*peerProc) {
	var wg sync.WaitGroup
	for _, p := range peers {
		wg.Add(1)
		go func(pp *peerProc) {
			defer wg.Done()
			if pp.cmd == nil || pp.cmd.Process == nil {
				return
			}
			_ = pp.cmd.Process.Kill()
			_, _ = pp.cmd.Process.Wait()
		}(p)
	}
	wg.Wait()
}

func pickFreePort() (int, error) {
	ln, err := net.Listen("tcp", bindHost()+":0")
	if err != nil {
		return 0, err
	}
	port := ln.Addr().(*net.TCPAddr).Port
	_ = ln.Close()
	return port, nil
}

func waitForHealth(url string, timeout time.Duration) error {
	deadline := time.Now().Add(timeout)
	client := &http.Client{Timeout: 500 * time.Millisecond}
	var lastErr error
	for time.Now().Before(deadline) {
		resp, err := client.Get(url)
		if err == nil {
			_ = resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				return nil
			}
			lastErr = fmt.Errorf("status=%d", resp.StatusCode)
		} else {
			lastErr = err
		}
		time.Sleep(100 * time.Millisecond)
	}
	return fmt.Errorf("timeout: %v", lastErr)
}

// ============================================================================
// Report writing
// ============================================================================

func writeLiveReport(rep *LiveIntegrationReport) {
	_ = writeJSONFile(LiveIntegrationReportPath, rep)
}

func writeJSONFile(path string, v interface{}) error {
	if dir := filepath.Dir(path); dir != "" && dir != "." {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return err
		}
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()
	enc := json.NewEncoder(f)
	enc.SetIndent("", "  ")
	if err := enc.Encode(v); err != nil {
		return err
	}
	return f.Sync()
}

// RunRetryDeterminismCLI is implemented in retry_determinism_harness.go;
// live_integration_cli.go dispatches to it when --live-retry-determinism
// is passed. Runtime wiring only; no circular import.
