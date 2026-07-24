// cross_system_integration_validator.go (v14.6 Global Determinism Validation — Phase 6)
//
// Proves Sarathi's sealed canonical response bytes reach BHIV Core (Raj),
// InsightFlow (Vijay), and Bucket (Siddhesh) BYTE-IDENTICAL, and each target
// independently verifies response_hash before processing.
//
// Three in-process httptest.Server instances simulate the downstream peers:
//
//   - Core (core_workflow)  — synchronous verify-then-store, echoes ACK.
//   - InsightFlow           — async accept (HTTP 202), still recomputes hash,
//                              rejects on mismatch.
//   - Bucket                 — verify, store, support GET readback.
//
// The validator wires the existing WireDeterministicTargets path via the
// SARATHI_ROUTE_CORE_URL / _INSIGHTFLOW_URL / _BUCKET_URL env vars, builds a
// sealed envelope, calls RoutePropagation, and then reads back each target's
// recorded body to compare against env.CanonicalResponseBytes().
//
// Output:
//   - cross_system_integration_report.json
//   - proof_logs/cross_system_integration_log.jsonl
//
// TAG: test-affordance-only

package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// CrossSystemIntegrationReportPath is the v14.6 Phase 6 aggregate artefact.
const CrossSystemIntegrationReportPath = "cross_system_integration_report.json"

// CrossSystemIntegrationLogPath is the per-target JSONL log.
const CrossSystemIntegrationLogPath = "proof_logs/cross_system_integration_log.jsonl"

// CrossSystemIntegrationSchemaVersion pins the aggregate report schema.
const CrossSystemIntegrationSchemaVersion = "sarathi.cross_system_integration/v1.0"

// CrossSystemTargetResult is one target's record in the cross-system report.
type CrossSystemTargetResult struct {
	Name              string `json:"name"`
	URL               string `json:"url"`
	Delivered         bool   `json:"delivered"`
	BytesReceived     int    `json:"bytes_received"`
	BodySha256        string `json:"body_sha256"`
	ExpectedSha256    string `json:"expected_sha256"`
	AckHashEchoed     string `json:"ack_hash_echoed"`
	HashEcho          bool   `json:"hash_echo_matches"`
	ByteEqual         bool   `json:"byte_equal"`
	AckVerified       bool   `json:"ack_verified"`
	LatencyNs         int64  `json:"latency_ns"`
	HaltCode          string `json:"halt_code,omitempty"`
	Error             string `json:"error,omitempty"`
}

// CrossSystemIntegrationReport is the Phase 6 artefact.
type CrossSystemIntegrationReport struct {
	SchemaVersion                 string                    `json:"schema_version"`
	GeneratedAt                   string                    `json:"generated_at"`
	DecisionID                    string                    `json:"decision_id"`
	ResponseHash                  string                    `json:"response_hash"`
	ChainBindingHash              string                    `json:"chain_binding_hash"`
	TargetCount                   int                       `json:"target_count"`
	TargetsVerified               int                       `json:"targets_verified"`
	CrossSystemIntegrationVerified bool                     `json:"cross_system_integration_verified"`
	BucketReadbackVerified        bool                      `json:"bucket_readback_verified"`
	Targets                       []CrossSystemTargetResult `json:"targets"`
	Notes                         []string                  `json:"notes,omitempty"`
}

// RunCrossSystemIntegration wires three mock downstream peers, propagates one
// sealed envelope, and verifies every target received byte-identical bytes.
func RunCrossSystemIntegration() (*CrossSystemIntegrationReport, error) {
	printHeader("CROSS-SYSTEM INTEGRATION VALIDATOR (v14.6 Phase 6)")
	fmt.Println("  Proving: Core / InsightFlow / Bucket receive byte-identical Sarathi bytes")
	fmt.Println()

	if err := os.MkdirAll(filepath.Dir(CrossSystemIntegrationLogPath), 0o755); err != nil {
		return nil, err
	}
	logF, err := os.OpenFile(CrossSystemIntegrationLogPath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return nil, err
	}
	defer logF.Close()

	// Three simulated peers, each with an independent verifier.
	coreSim := newHashVerifyingPeer("core", http.StatusOK, false)
	insightSim := newHashVerifyingPeer("insightflow", http.StatusAccepted, false)
	bucketSim := newHashVerifyingPeer("bucket", http.StatusOK, true)

	coreSrv := httptest.NewServer(coreSim.handler())
	defer coreSrv.Close()
	insightSrv := httptest.NewServer(insightSim.handler())
	defer insightSrv.Close()
	bucketSrv := httptest.NewServer(bucketSim.handler())
	defer bucketSrv.Close()

	// Save + override routing env vars.
	envBackup := saveEnv([]string{
		"SARATHI_ROUTE_CORE_URL",
		"SARATHI_ROUTE_INSIGHTFLOW_URL",
		"SARATHI_ROUTE_BUCKET_URL",
	})
	defer restoreEnv(envBackup)
	_ = os.Setenv("SARATHI_ROUTE_CORE_URL", coreSrv.URL+"/v1/enforce")
	_ = os.Setenv("SARATHI_ROUTE_INSIGHTFLOW_URL", insightSrv.URL+"/v1/observe")
	_ = os.Setenv("SARATHI_ROUTE_BUCKET_URL", bucketSrv.URL+"/v1/audit")

	// Build the per-test stack.
	fx, err := BuildOrLoadReplayFixture()
	if err != nil {
		return nil, fmt.Errorf("cross_system: fixture: %w", err)
	}
	agentReg := NewRegistryInterface()
	ea := NewEnforcementAdapter(nil, nil, agentReg, nil)
	ea.InitExternalMode()
	if err := ea.GetEvaluatorRegistry().RegisterEvaluator(
		fx.EvaluatorID, "replay fixture evaluator", fx.PublicKey,
		map[string]string{"fixture": "true"}, "cross_system",
	); err != nil {
		return nil, fmt.Errorf("cross_system: register evaluator: %w", err)
	}
	mc := NewModeController(BHIVModeExternal)
	pa := NewPDPAdapter(ea, mc)
	pa.ResetReplayTrackerForHarness()

	env, ierr := pa.Ingest(fx.Bytes, "EXEC-XSYS-001", "corr-xsys-001", nil)
	if ierr != nil {
		return nil, fmt.Errorf("cross_system: ingest: %w", ierr)
	}

	// Wire real router at the sealed envelope.
	router := NewMultiSystemRouter(nil)
	wired := router.WireDeterministicTargets(env)
	if wired < 3 {
		return nil, fmt.Errorf("cross_system: expected ≥3 wired targets, got %d", wired)
	}

	propStart := time.Now()
	propRes, perr := router.RoutePropagation(env)
	propDur := time.Since(propStart)
	if perr != nil {
		return nil, fmt.Errorf("cross_system: RoutePropagation: %w", perr)
	}

	report := &CrossSystemIntegrationReport{
		SchemaVersion:    CrossSystemIntegrationSchemaVersion,
		GeneratedAt:      time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		DecisionID:       env.DecisionID(),
		ResponseHash:     env.ResponseHash(),
		ChainBindingHash: env.ChainBindingHash(),
	}

	expectedHash := env.ResponseHash()
	expectedBytes := env.CanonicalResponseBytes()

	// Aggregate per-target from the propagation result and the peers' recorded body.
	targets := []struct {
		name string
		url  string
		peer *hashVerifyingPeer
	}{
		{"core_workflow", coreSrv.URL + "/v1/enforce", coreSim},
		{"insightflow", insightSrv.URL + "/v1/observe", insightSim},
		{"bucket", bucketSrv.URL + "/v1/audit", bucketSim},
	}

	for _, t := range targets {
		row := CrossSystemTargetResult{
			Name:           t.name,
			URL:            t.url,
			ExpectedSha256: expectedHash,
		}
		body, bodyHash := t.peer.lastBody()
		row.BytesReceived = len(body)
		row.BodySha256 = bodyHash
		row.ByteEqual = bodyHash == expectedHash && bytesEqualWithLen(body, expectedBytes)

		// Propagation hop result — maps target_name → hop.
		for _, hop := range propRes.Hops {
			if hop.Target == t.name {
				row.Delivered = hop.Delivered
				row.LatencyNs = hop.LatencyNs
				if !hop.Delivered {
					row.Error = hop.Error
					row.HaltCode = hop.ErrorCode
				}
				break
			}
		}
		row.AckHashEchoed = t.peer.lastAck()
		row.HashEcho = row.AckHashEchoed == expectedHash
		row.AckVerified = row.Delivered && row.HashEcho

		if row.ByteEqual && row.AckVerified {
			report.TargetsVerified++
		}
		report.Targets = append(report.Targets, row)
		if b, jerr := json.Marshal(row); jerr == nil {
			logF.Write(append(b, '\n'))
		}

		mark := "PASS"
		if !row.ByteEqual || !row.AckVerified {
			mark = "FAIL"
		}
		fmt.Printf("    %-14s byte_equal=%t ack_verified=%t delivered=%t latency=%dms [%s]\n",
			row.Name, row.ByteEqual, row.AckVerified, row.Delivered, row.LatencyNs/1_000_000, mark)
	}
	_ = logF.Sync()

	// Bucket GET readback — independent confirmation.
	readbackURL := strings.TrimRight(bucketSrv.URL+"/v1/audit/", "/") + "/" + env.DecisionID()
	client := &http.Client{Timeout: 5 * time.Second}
	resp, gerr := client.Get(readbackURL)
	if gerr == nil {
		b, _ := io.ReadAll(resp.Body)
		_ = resp.Body.Close()
		if Sha256Hex(b) == expectedHash && bytesEqualWithLen(b, expectedBytes) {
			report.BucketReadbackVerified = true
		} else {
			report.Notes = append(report.Notes,
				fmt.Sprintf("bucket readback mismatch: got=%s want=%s", Sha256Hex(b), expectedHash))
		}
	} else {
		report.Notes = append(report.Notes, fmt.Sprintf("bucket readback error: %v", gerr))
	}

	report.TargetCount = len(report.Targets)
	report.CrossSystemIntegrationVerified = report.TargetsVerified == report.TargetCount &&
		report.BucketReadbackVerified && report.TargetCount >= 3

	if !report.CrossSystemIntegrationVerified {
		_ = RecordViolation(ByteEqualityResult{
			Hop:           "cross_system.aggregate",
			BytesMatch:    false,
			ViolationCode: CodeTransportIntegrityViolation,
			Timestamp:     time.Now().UTC(),
			Detail: fmt.Sprintf("verified=%d/%d bucket_readback=%t",
				report.TargetsVerified, report.TargetCount, report.BucketReadbackVerified),
		})
	}

	passed := report.TargetsVerified
	failed := report.TargetCount - report.TargetsVerified
	if err := WriteCanonicalResults(
		CrossSystemIntegrationReportPath,
		"cross_system_integration",
		report.TargetCount,
		passed,
		failed,
		report,
	); err != nil {
		return report, err
	}

	fmt.Printf("\n  Cross-System: verified=%t targets=%d/%d bucket_readback=%t duration=%dms\n",
		report.CrossSystemIntegrationVerified, report.TargetsVerified, report.TargetCount,
		report.BucketReadbackVerified, propDur.Milliseconds())
	return report, nil
}

// --- hash-verifying peer ---

// hashVerifyingPeer emulates a downstream system that requires
// X-Sarathi-Response-Hash == SHA-256(body) BEFORE accepting.
// On mismatch it returns HTTP 412 and echoes the received body hash.
// Bucket targets also support GET /{decision_id} readback.
type hashVerifyingPeer struct {
	name        string
	successCode int
	supportsGet bool

	mu       sync.Mutex
	body     []byte
	bodyHash string
	ackEchoed string
	store    map[string][]byte
	hits     int
}

func newHashVerifyingPeer(name string, successCode int, supportsGet bool) *hashVerifyingPeer {
	return &hashVerifyingPeer{
		name:        name,
		successCode: successCode,
		supportsGet: supportsGet,
		store:       make(map[string][]byte),
	}
}

func (p *hashVerifyingPeer) handler() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		p.mu.Lock()
		p.hits++
		p.mu.Unlock()

		if r.Method == http.MethodGet && p.supportsGet {
			id := strings.TrimPrefix(r.URL.Path, "/v1/audit/")
			if id == "" {
				http.Error(w, "missing decision_id", http.StatusBadRequest)
				return
			}
			p.mu.Lock()
			body, ok := p.store[id]
			p.mu.Unlock()
			if !ok {
				http.Error(w, "not found", http.StatusNotFound)
				return
			}
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write(body)
			return
		}

		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		body, err := io.ReadAll(r.Body)
		if err != nil {
			http.Error(w, "read body: "+err.Error(), http.StatusBadRequest)
			return
		}
		sum := sha256.Sum256(body)
		bodyHashHex := hex.EncodeToString(sum[:])
		want := r.Header.Get(HeaderResponseHash)
		decisionID := r.Header.Get(HeaderDecisionID)

		p.mu.Lock()
		p.body = append(p.body[:0:0], body...)
		p.bodyHash = bodyHashHex
		p.ackEchoed = bodyHashHex
		if p.supportsGet && decisionID != "" {
			cp := make([]byte, len(body))
			copy(cp, body)
			p.store[decisionID] = cp
		}
		p.mu.Unlock()

		if want == "" || bodyHashHex != want {
			// Precondition failed — echo the received hash so the caller can diff.
			w.Header().Set(HeaderAckHash, bodyHashHex)
			http.Error(w, "response_hash mismatch", http.StatusPreconditionFailed)
			return
		}
		w.Header().Set(HeaderAckHash, bodyHashHex)
		w.WriteHeader(p.successCode)
	})
}

func (p *hashVerifyingPeer) lastBody() ([]byte, string) {
	p.mu.Lock()
	defer p.mu.Unlock()
	cp := make([]byte, len(p.body))
	copy(cp, p.body)
	return cp, p.bodyHash
}

func (p *hashVerifyingPeer) lastAck() string {
	p.mu.Lock()
	defer p.mu.Unlock()
	return p.ackEchoed
}

// --- env helpers ---

func saveEnv(keys []string) map[string]string {
	m := make(map[string]string, len(keys))
	for _, k := range keys {
		m[k] = os.Getenv(k)
	}
	return m
}

func restoreEnv(m map[string]string) {
	for k, v := range m {
		if v == "" {
			_ = os.Unsetenv(k)
		} else {
			_ = os.Setenv(k, v)
		}
	}
}

// bytesEqualWithLen is length-checked byte comparison (reuses stdlib semantics
// without importing bytes here — keeps this file's imports minimal).
func bytesEqualWithLen(a, b []byte) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}
