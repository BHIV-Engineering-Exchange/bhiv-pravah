// bucket_state_verifier.go (v14.6 Global Determinism Validation — Phase 4)
//
// Proves the final stored state in Bucket equals Sarathi's response output,
// byte-for-byte. An in-process net/httptest.Server emulates Bucket:
//
//   - POST /v1/audit           — verify X-Sarathi-Response-Hash matches
//                                SHA-256(body); on match, store body keyed by
//                                X-Sarathi-Decision-ID; echo X-Sarathi-Ack-Hash
//                                equal to the received body hash.
//   - GET  /v1/audit/{dec_id}  — return the previously stored body verbatim.
//
// 100 distinct fixtures (100 decision_id × 100 nonce pairs, each sealed with
// the same deterministic key) are routed through the server. After POST, the
// verifier GETs each decision back, recomputes SHA-256 over the returned body,
// and asserts equality to the envelope's response_hash.
//
// Output:
//   - bucket_state_verification_report.json
//   - proof_logs/bucket_verification_log.jsonl
//
// TAG: test-affordance-only

package main

import (
	"crypto/ed25519"
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

// BucketStateReportPath is the v14.6 Phase 4 aggregate artefact.
const BucketStateReportPath = "bucket_state_verification_report.json"

// BucketStateLogPath is the per-decision JSONL log.
const BucketStateLogPath = "proof_logs/bucket_verification_log.jsonl"

// BucketStateSchemaVersion pins the aggregate report schema.
const BucketStateSchemaVersion = "sarathi.bucket_state/v1.0"

// BucketStateDefaultCount is the number of distinct fixtures to exercise.
const BucketStateDefaultCount = 100

// BucketStateDecisionResult records the outcome for one decision round-trip.
type BucketStateDecisionResult struct {
	DecisionID       string `json:"decision_id"`
	Nonce            string `json:"nonce"`
	SentHash         string `json:"sent_hash"`
	AckHash          string `json:"ack_hash"`
	ReadbackHash     string `json:"readback_hash"`
	AckMatched       bool   `json:"ack_matched"`
	ReadbackMatched  bool   `json:"readback_matched"`
	BytesSent        int    `json:"bytes_sent"`
	BytesReadback    int    `json:"bytes_readback"`
	LatencyPostNs    int64  `json:"latency_post_ns"`
	LatencyGetNs     int64  `json:"latency_get_ns"`
	Error            string `json:"error,omitempty"`
}

// BucketStateMismatch is a compact record for the mismatched_decisions list.
type BucketStateMismatch struct {
	DecisionID string `json:"decision_id"`
	SentHash   string `json:"sent_hash"`
	GotHash    string `json:"got_hash"`
	Stage      string `json:"stage"` // "ack" | "readback"
}

// BucketStateReport aggregates the Phase 4 outcome.
type BucketStateReport struct {
	SchemaVersion         string                      `json:"schema_version"`
	GeneratedAt           string                      `json:"generated_at"`
	Count                 int                         `json:"count"`
	Matches               int                         `json:"matches"`
	Mismatches            int                         `json:"mismatches"`
	BucketStateVerified   bool                        `json:"bucket_state_verified"`
	MismatchedDecisions   []BucketStateMismatch       `json:"mismatched_decisions"`
	Decisions             []BucketStateDecisionResult `json:"decisions"`
	Notes                 []string                    `json:"notes,omitempty"`
}

// RunBucketStateVerifier runs the 100-decision round-trip against an in-process
// Bucket simulator and writes the aggregate report.
func RunBucketStateVerifier() (*BucketStateReport, error) {
	return RunBucketStateVerifierN(BucketStateDefaultCount)
}

// RunBucketStateVerifierN runs N distinct decisions. N must be >= 1.
// Writes to the canonical BucketStateReportPath.
func RunBucketStateVerifierN(count int) (*BucketStateReport, error) {
	return RunBucketStateVerifierNAt(count, BucketStateReportPath, BucketStateLogPath)
}

// RunBucketStateVerifierNAt runs N distinct decisions and writes artefacts to
// the caller-specified paths. This lets secondary entry points (the VC demo's
// sampled run) avoid clobbering the canonical 100-decision audit artefact.
func RunBucketStateVerifierNAt(count int, reportPath, logPath string) (*BucketStateReport, error) {
	if count < 1 {
		count = 1
	}
	if reportPath == "" {
		reportPath = BucketStateReportPath
	}
	if logPath == "" {
		logPath = BucketStateLogPath
	}
	printHeader("BUCKET STATE VERIFIER (v14.6 Phase 4)")
	fmt.Printf("  Proving: Bucket storage is byte-identical to Sarathi's sealed bytes (N=%d)\n\n", count)

	if err := os.MkdirAll(filepath.Dir(logPath), 0o755); err != nil {
		return nil, err
	}
	logF, err := os.OpenFile(logPath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return nil, err
	}
	defer logF.Close()

	// Derive the replay key once — all variant fixtures reuse it.
	priv, pub, err := deriveReplayKey()
	if err != nil {
		return nil, fmt.Errorf("bucket_verify: derive key: %w", err)
	}

	// Spin up the Bucket simulator.
	store := newBucketSimulator()
	server := httptest.NewServer(store.handler())
	defer server.Close()

	// Point the deterministic router at the simulator via the existing env var.
	oldURL := os.Getenv("SARATHI_ROUTE_BUCKET_URL")
	_ = os.Setenv("SARATHI_ROUTE_BUCKET_URL", server.URL+"/v1/audit")
	defer func() { _ = os.Setenv("SARATHI_ROUTE_BUCKET_URL", oldURL) }()

	// Build the per-test stack once.
	agentReg := NewRegistryInterface()
	ea := NewEnforcementAdapter(nil, nil, agentReg, nil)
	ea.InitExternalMode()
	if err := ea.GetEvaluatorRegistry().RegisterEvaluator(
		ReplayFixtureEvaluatorID, "replay fixture evaluator", pub,
		map[string]string{"fixture": "true"}, "bucket_verify",
	); err != nil {
		return nil, fmt.Errorf("bucket_verify: register evaluator: %w", err)
	}
	mc := NewModeController(BHIVModeExternal)
	pa := NewPDPAdapter(ea, mc)

	httpClient := &http.Client{Timeout: 5 * time.Second}
	report := &BucketStateReport{
		SchemaVersion: BucketStateSchemaVersion,
		GeneratedAt:   time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		Decisions:     make([]BucketStateDecisionResult, 0, count),
	}

	for i := 0; i < count; i++ {
		decisionID := fmt.Sprintf("DEC-BUCKET-%05d", i)
		nonce := fmt.Sprintf("NONCE-BUCKET-%05d", i)

		decBytes, err := buildVariantFixtureBytes(priv, decisionID, nonce)
		if err != nil {
			report.Notes = append(report.Notes,
				fmt.Sprintf("build %s: %v", decisionID, err))
			continue
		}

		pa.ResetReplayTrackerForHarness()
		execID := fmt.Sprintf("EXEC-BUCKET-%05d", i)
		corrID := fmt.Sprintf("corr-bucket-%05d", i)
		env, ierr := pa.Ingest(decBytes, execID, corrID, nil)
		if ierr != nil {
			report.Notes = append(report.Notes,
				fmt.Sprintf("ingest %s: %v", decisionID, ierr))
			continue
		}

		row := BucketStateDecisionResult{
			DecisionID: decisionID,
			Nonce:      nonce,
			SentHash:   env.ResponseHash(),
			BytesSent:  len(env.CanonicalResponseBytes()),
		}

		// POST via the deterministic handler so the full header set +
		// byte-equality check path is exercised (not a direct http.Post).
		cfg := DeterministicHTTPRoutingConfig{
			HTTPRoutingConfig: HTTPRoutingConfig{
				TargetURL:      server.URL + "/v1/audit",
				Timeout:        5 * time.Second,
				CircuitBreaker: CircuitBreakerConfig{FailureThreshold: 10, ResetTimeout: time.Second, HalfOpenMaxProbes: 2},
				MaxConcurrency: 8,
			},
			RequireAckHashHeader: true,
			AckHashHeader:        HeaderAckHash,
		}
		handler := NewDeterministicHTTPRoutingHandler("bucket", env, cfg)
		evt := &RoutedEvent{
			EventID:         fmt.Sprintf("evt-bucket-%05d", i),
			EventType:       "sarathi.propagation.hop",
			Source:          "sarathi/propagation",
			Timestamp:       time.Now().UTC(),
			ContentType:     "application/json",
			CorrelationID:   env.CorrelationID(),
			Verdict:         env.Verdict(),
			EnforcementHash: env.EnforcementHash(),
		}
		postStart := time.Now()
		if herr := handler(evt); herr != nil {
			row.Error = fmt.Sprintf("POST: %v", herr)
			row.LatencyPostNs = time.Since(postStart).Nanoseconds()
			report.Decisions = append(report.Decisions, row)
			report.MismatchedDecisions = append(report.MismatchedDecisions,
				BucketStateMismatch{DecisionID: decisionID, SentHash: row.SentHash, GotHash: "", Stage: "ack"})
			continue
		}
		row.LatencyPostNs = time.Since(postStart).Nanoseconds()

		// Independent GET round-trip.
		getStart := time.Now()
		getURL := server.URL + "/v1/audit/" + decisionID
		resp, gerr := httpClient.Get(getURL)
		row.LatencyGetNs = time.Since(getStart).Nanoseconds()
		if gerr != nil {
			row.Error = fmt.Sprintf("GET: %v", gerr)
			report.Decisions = append(report.Decisions, row)
			report.MismatchedDecisions = append(report.MismatchedDecisions,
				BucketStateMismatch{DecisionID: decisionID, SentHash: row.SentHash, GotHash: "", Stage: "readback"})
			continue
		}
		body, rerr := io.ReadAll(resp.Body)
		_ = resp.Body.Close()
		if rerr != nil {
			row.Error = fmt.Sprintf("GET body: %v", rerr)
			report.Decisions = append(report.Decisions, row)
			report.MismatchedDecisions = append(report.MismatchedDecisions,
				BucketStateMismatch{DecisionID: decisionID, SentHash: row.SentHash, GotHash: "", Stage: "readback"})
			continue
		}
		row.BytesReadback = len(body)

		// Canonicalise defensively — if bytes were already canonical this is
		// a no-op (VerifyCanonicalBytes enforces re-canonicalisation round-trip).
		if ok, detail := VerifyCanonicalBytes(body); !ok {
			row.Error = "non-canonical readback: " + detail
			report.Decisions = append(report.Decisions, row)
			report.MismatchedDecisions = append(report.MismatchedDecisions,
				BucketStateMismatch{DecisionID: decisionID, SentHash: row.SentHash, GotHash: Sha256Hex(body), Stage: "readback"})
			continue
		}
		readbackHash := Sha256Hex(body)
		row.ReadbackHash = readbackHash
		row.AckHash = resp.Header.Get(HeaderAckHash) // best-effort; POST handler already verified
		row.AckMatched = true                         // POST handler would have errored otherwise
		row.ReadbackMatched = readbackHash == row.SentHash

		if row.ReadbackMatched {
			report.Matches++
		} else {
			report.Mismatches++
			report.MismatchedDecisions = append(report.MismatchedDecisions,
				BucketStateMismatch{DecisionID: decisionID, SentHash: row.SentHash, GotHash: readbackHash, Stage: "readback"})
			_ = RecordViolation(ByteEqualityResult{
				Hop:           "bucket.readback",
				SentHash:      row.SentHash,
				AckHash:       readbackHash,
				BytesMatch:    false,
				ViolationCode: CodeBucketReadbackMismatch,
				Timestamp:     time.Now().UTC(),
				Detail: fmt.Sprintf("decision_id=%s sent=%s got=%s", decisionID, row.SentHash, readbackHash),
			})
		}

		report.Decisions = append(report.Decisions, row)
		if b, jerr := json.Marshal(row); jerr == nil {
			logF.Write(append(b, '\n'))
		}

		if (i+1)%25 == 0 {
			fmt.Printf("    %d/%d decisions verified (matches=%d mismatches=%d)\n",
				i+1, count, report.Matches, report.Mismatches)
		}
	}
	_ = logF.Sync()

	report.Count = len(report.Decisions)
	report.BucketStateVerified = report.Mismatches == 0 && report.Matches == report.Count && report.Count > 0

	passed := report.Matches
	failed := report.Mismatches
	if err := WriteCanonicalResults(
		reportPath,
		"bucket_state_verification",
		report.Count,
		passed,
		failed,
		report,
	); err != nil {
		return report, err
	}

	fmt.Printf("\n  Bucket State Verified: %t  matches=%d/%d  mismatches=%d\n",
		report.BucketStateVerified, report.Matches, report.Count, report.Mismatches)
	return report, nil
}

// --- Bucket simulator ---

// bucketSimulator is an in-memory Bucket stand-in. It stores the POSTed body
// verbatim (keyed by decision_id) and returns it verbatim on GET.
type bucketSimulator struct {
	mu    sync.Mutex
	store map[string][]byte
}

func newBucketSimulator() *bucketSimulator {
	return &bucketSimulator{store: make(map[string][]byte)}
}

func (b *bucketSimulator) handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/v1/audit", b.handlePost)
	mux.HandleFunc("/v1/audit/", b.handleGet)
	return mux
}

func (b *bucketSimulator) handlePost(w http.ResponseWriter, r *http.Request) {
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

	wantHash := r.Header.Get(HeaderResponseHash)
	decisionID := r.Header.Get(HeaderDecisionID)
	if wantHash == "" || decisionID == "" {
		w.Header().Set(HeaderAckHash, bodyHashHex)
		http.Error(w, "missing required propagation headers", http.StatusPreconditionFailed)
		return
	}
	if bodyHashHex != wantHash {
		// Still echo the received hash so the client can see the mismatch;
		// reject with 412 Precondition Failed so the router surfaces it.
		w.Header().Set(HeaderAckHash, bodyHashHex)
		http.Error(w, "response hash mismatch", http.StatusPreconditionFailed)
		return
	}
	b.mu.Lock()
	// Store a copy — safe against any later reuse of the buffer.
	cp := make([]byte, len(body))
	copy(cp, body)
	b.store[decisionID] = cp
	b.mu.Unlock()

	w.Header().Set(HeaderAckHash, bodyHashHex)
	w.WriteHeader(http.StatusOK)
}

func (b *bucketSimulator) handleGet(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	decisionID := strings.TrimPrefix(r.URL.Path, "/v1/audit/")
	if decisionID == "" {
		http.Error(w, "missing decision_id", http.StatusBadRequest)
		return
	}
	b.mu.Lock()
	body, ok := b.store[decisionID]
	b.mu.Unlock()
	if !ok {
		http.Error(w, "not found", http.StatusNotFound)
		return
	}
	// Return stored bytes VERBATIM — no re-serialisation.
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(body)
}

// --- Variant fixture builder ---

// buildVariantFixtureBytes is the per-decision variant of the replay fixture.
// It reuses the same deterministic Ed25519 key but rotates decision_id +
// nonce so the Bucket simulator sees 100 distinct round-trip payloads.
func buildVariantFixtureBytes(priv ed25519.PrivateKey, decisionID, nonce string) ([]byte, error) {
	ts, err := time.Parse("2006-01-02T15:04:05.000000Z", ReplayFixtureTimestamp)
	if err != nil {
		return nil, fmt.Errorf("variant_fixture: timestamp: %w", err)
	}
	d := &ExternalDecision{
		DecisionID:  decisionID,
		EvaluatorID: ReplayFixtureEvaluatorID,
		AgentID:     "gov-agent-001",
		ResourceID:  "policy-reg-001",
		Action:      "read",
		Verdict:     ExternalVerdictAllow,
		Obligations: []string{},
		Timestamp:   ts,
		TTL:         365 * 24 * time.Hour,
		ExpiresAt:   ts.Add(365 * 24 * time.Hour),
		Metadata:    map[string]string{"fixture": "replay", "variant": "bucket_verify"},
		Reason:      "Bucket verification variant fixture",
		Nonce:       nonce,
	}
	d.DecisionHash = d.computeHash()
	d.DecisionCoreHash = d.computeCoreHash()
	d.SignDecision(priv)

	return json.Marshal(d)
}
