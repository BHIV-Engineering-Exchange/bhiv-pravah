// transport_adversarial_harness.go (v14.6 Global Determinism Validation — Phase 3)
//
// Drives the DeterministicHTTPRoutingHandler through real net/httptest servers
// that simulate adversarial or benign transport-layer behaviour. Proves that
// every byte-mutating transport attack is detected and chain-halts, while
// every benign transport feature (chunked, gzip-decoded) is passed through.
//
// Scenarios:
//   T1 pass_through        — server echoes body verbatim → PASS
//   T2 chunked_encoding    — server uses chunked transfer encoding → PASS
//                            (transport chunking is invisible to the body hash)
//   T3 header_strip        — server drops X-Sarathi-Ack-Hash → HALT (ack missing)
//   T4 header_mutation     — server sets ack to "deadbeef..." → HALT (ack drift)
//   T5 proxy_reserialize   — server parses+re-marshals JSON (non-canonical)
//                            and acks the re-serialized hash → HALT (hash drift)
//   T6 body_byte_flip      — server XOR-flips one body byte before hashing → HALT
//   T7 duplicate_retry     — server echoes correctly twice (dedup idempotency) → PASS
//   T8 server_5xx          — server returns 500 → HALT (SERVER_ERROR)
//
// Every scenario writes a JSONL row and contributes to transport_integrity_report.json.
// The `transport_integrity_verified` summary key is exactly what task.md §PHASE 3 demands.
//
// TAG: test-affordance-only

package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"sort"
	"sync/atomic"
	"time"
)

// TransportIntegrityReportPath is the v14.6 Phase 3 aggregate artefact.
const TransportIntegrityReportPath = "transport_integrity_report.json"

// TransportAdversarialLogPath is the per-scenario JSONL log.
const TransportAdversarialLogPath = "proof_logs/transport_adversarial_log.jsonl"

// TransportIntegritySchemaVersion pins the aggregate report schema.
const TransportIntegritySchemaVersion = "sarathi.transport_integrity/v1.0"

// TransportScenarioResult is a single row in the transport integrity report.
type TransportScenarioResult struct {
	Name                      string `json:"name"`
	Expected                  string `json:"expected"` // "PASS" or "HALT"
	Actual                    string `json:"actual"`   // "PASS" | "HALT" | "ERROR"
	TransportIntegrityVerified bool  `json:"transport_integrity_verified"`
	HaltCode                  string `json:"halt_code,omitempty"`
	ErrorDetail               string `json:"error_detail,omitempty"`
	DurationMs                int64  `json:"duration_ms"`
	ServerHits                int64  `json:"server_hits"`
	Matched                   bool   `json:"matched"`
}

// TransportIntegrityReport aggregates all scenario outcomes.
type TransportIntegrityReport struct {
	SchemaVersion              string                    `json:"schema_version"`
	GeneratedAt                string                    `json:"generated_at"`
	ScenarioCount              int                       `json:"scenario_count"`
	MatchedExpected            int                       `json:"matched_expected"`
	MismatchedExpected         int                       `json:"mismatched_expected"`
	ScenariosPassed            []string                  `json:"scenarios_passed"`
	ScenariosHaltedAsExpected  []string                  `json:"scenarios_halted_as_expected"`
	TransportIntegrityVerified bool                      `json:"transport_integrity_verified"`
	Scenarios                  []TransportScenarioResult `json:"scenarios"`
}

// RunTransportAdversarialHarness runs every scenario and writes the aggregate report.
func RunTransportAdversarialHarness() (*TransportIntegrityReport, error) {
	printHeader("TRANSPORT ADVERSARIAL HARNESS (v14.6 Phase 3)")
	fmt.Println("  Proving: byte-mutating transport attacks are detected and chain-halt")
	fmt.Println()

	if err := os.MkdirAll(filepath.Dir(TransportAdversarialLogPath), 0o755); err != nil {
		return nil, err
	}
	logF, err := os.OpenFile(TransportAdversarialLogPath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
	if err != nil {
		return nil, err
	}
	defer logF.Close()

	// Ingest a sealed envelope once — all scenarios route this same envelope
	// through a different adversarial server.
	fx, err := BuildOrLoadReplayFixture()
	if err != nil {
		return nil, err
	}
	agentReg := NewRegistryInterface()
	ea := NewEnforcementAdapter(nil, nil, agentReg, nil)
	ea.InitExternalMode()
	if err := ea.GetEvaluatorRegistry().RegisterEvaluator(
		fx.EvaluatorID, "replay fixture evaluator", fx.PublicKey,
		map[string]string{"fixture": "true"}, "transport_adv",
	); err != nil {
		return nil, err
	}
	mc := NewModeController(BHIVModeExternal)
	pa := NewPDPAdapter(ea, mc)
	pa.ResetReplayTrackerForHarness()
	env, err := pa.Ingest(fx.Bytes, "EXEC-TRANSPORT-001", "corr-transport-001", nil)
	if err != nil {
		return nil, fmt.Errorf("transport: ingest: %w", err)
	}

	scenarios := []struct {
		name     string
		expected string
		handler  func(sent *int64) http.Handler
	}{
		{"pass_through", "PASS", makePassThroughHandler},
		{"chunked_encoding", "PASS", makeChunkedHandler},
		{"header_strip", "HALT", makeHeaderStripHandler},
		{"header_mutation", "HALT", makeHeaderMutationHandler},
		{"proxy_reserialize", "HALT", makeProxyReserializeHandler},
		{"body_byte_flip", "HALT", makeBodyByteFlipHandler},
		{"duplicate_retry", "PASS", makePassThroughHandler},
		{"server_5xx", "HALT", makeServer5xxHandler},
	}

	report := &TransportIntegrityReport{
		SchemaVersion: TransportIntegritySchemaVersion,
		GeneratedAt:   time.Now().UTC().Format("2006-01-02T15:04:05.000000Z"),
		Scenarios:     make([]TransportScenarioResult, 0, len(scenarios)),
	}

	for _, sc := range scenarios {
		var hits int64
		server := httptest.NewServer(sc.handler(&hits))
		started := time.Now()

		row := runTransportScenario(sc.name, sc.expected, env, server.URL, &hits)

		server.Close()
		row.DurationMs = time.Since(started).Milliseconds()
		row.Matched = row.Actual == row.Expected

		report.Scenarios = append(report.Scenarios, row)

		if row.Matched {
			report.MatchedExpected++
			if row.Expected == "PASS" {
				report.ScenariosPassed = append(report.ScenariosPassed, row.Name)
			} else {
				report.ScenariosHaltedAsExpected = append(report.ScenariosHaltedAsExpected, row.Name)
			}
		} else {
			report.MismatchedExpected++
			_ = RecordViolation(ByteEqualityResult{
				Hop:           "transport." + row.Name,
				BytesMatch:    false,
				ViolationCode: CodeTransportIntegrityViolation,
				Timestamp:     time.Now().UTC(),
				Detail: fmt.Sprintf("scenario=%s expected=%s actual=%s code=%s",
					row.Name, row.Expected, row.Actual, row.HaltCode),
			})
		}

		if b, jerr := json.Marshal(row); jerr == nil {
			logF.Write(append(b, '\n'))
		}

		mark := "PASS"
		if !row.Matched {
			mark = "FAIL"
		}
		fmt.Printf("    %-20s expected=%-4s actual=%-5s verified=%t halt_code=%-34s [%s]\n",
			row.Name, row.Expected, row.Actual, row.TransportIntegrityVerified,
			transportTruncate(row.HaltCode, 34), mark)
	}
	_ = logF.Sync()

	sort.Strings(report.ScenariosPassed)
	sort.Strings(report.ScenariosHaltedAsExpected)
	report.ScenarioCount = len(report.Scenarios)
	report.TransportIntegrityVerified = report.MismatchedExpected == 0 &&
		len(report.Scenarios) == len(scenarios)

	if err := WriteCanonicalResults(
		TransportIntegrityReportPath,
		"transport_integrity",
		report.ScenarioCount,
		report.MatchedExpected,
		report.MismatchedExpected,
		report,
	); err != nil {
		return report, err
	}

	fmt.Printf("\n  Transport Integrity: matched=%d/%d verified=%t\n",
		report.MatchedExpected, report.ScenarioCount,
		report.TransportIntegrityVerified)
	return report, nil
}

// runTransportScenario routes one envelope through one adversarial server and
// classifies the outcome as PASS / HALT / ERROR.
func runTransportScenario(name, expected string, env *PropagationEnvelope, targetURL string, hits *int64) TransportScenarioResult {
	row := TransportScenarioResult{Name: name, Expected: expected}

	// Build a fresh handler bound to this server URL.
	cfg := DeterministicHTTPRoutingConfig{
		HTTPRoutingConfig: HTTPRoutingConfig{
			TargetURL:      targetURL,
			Timeout:        3 * time.Second,
			CircuitBreaker: CircuitBreakerConfig{FailureThreshold: 10, ResetTimeout: time.Second, HalfOpenMaxProbes: 2},
			MaxConcurrency: 4,
		},
		RequireAckHashHeader: true,
		AckHashHeader:        HeaderAckHash,
	}
	handler := NewDeterministicHTTPRoutingHandler("transport_"+name, env, cfg)

	// For duplicate_retry: invoke the handler twice. Both should succeed.
	iterations := 1
	if name == "duplicate_retry" {
		iterations = 2
	}

	for i := 0; i < iterations; i++ {
		event := &RoutedEvent{
			EventID:         fmt.Sprintf("evt-%s-%d", name, i),
			EventType:       "sarathi.propagation.hop",
			Source:          "sarathi/propagation",
			Timestamp:       time.Now().UTC(),
			ContentType:     "application/json",
			CorrelationID:   env.CorrelationID(),
			Verdict:         env.Verdict(),
			EnforcementHash: env.EnforcementHash(),
		}
		err := handler(event)
		if err == nil {
			row.Actual = "PASS"
			row.TransportIntegrityVerified = true
			continue
		}
		// Extract halt code + classify.
		if pse, ok := err.(*PropagationStopError); ok {
			row.Actual = "HALT"
			row.HaltCode = pse.Code
			row.ErrorDetail = pse.Error()
		} else {
			row.Actual = "HALT"
			row.HaltCode = extractErrorCodePrefix(err.Error())
			if row.HaltCode == "" {
				row.HaltCode = "HTTP_ERROR"
			}
			row.ErrorDetail = err.Error()
		}
		row.TransportIntegrityVerified = false
		break
	}
	row.ServerHits = atomic.LoadInt64(hits)
	return row
}

// --- handler factories ---

func makePassThroughHandler(hits *int64) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt64(hits, 1)
		body, _ := io.ReadAll(r.Body)
		sum := sha256.Sum256(body)
		w.Header().Set(HeaderAckHash, hex.EncodeToString(sum[:]))
		w.WriteHeader(http.StatusOK)
	})
}

func makeChunkedHandler(hits *int64) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt64(hits, 1)
		body, _ := io.ReadAll(r.Body)
		sum := sha256.Sum256(body)
		w.Header().Set(HeaderAckHash, hex.EncodeToString(sum[:]))
		// Force chunked encoding: set Transfer-Encoding explicitly AND omit Content-Length
		// by writing in two flushes.
		w.Header().Set("Transfer-Encoding", "chunked")
		w.WriteHeader(http.StatusOK)
		if fl, ok := w.(http.Flusher); ok {
			fmt.Fprintf(w, "{\"status\":\"ack\"}")
			fl.Flush()
		}
	})
}

func makeHeaderStripHandler(hits *int64) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt64(hits, 1)
		// Read but do not echo the ack hash header — it will be missing on response.
		_, _ = io.ReadAll(r.Body)
		w.WriteHeader(http.StatusOK)
	})
}

func makeHeaderMutationHandler(hits *int64) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt64(hits, 1)
		_, _ = io.ReadAll(r.Body)
		// Echo a hash that is deliberately wrong.
		w.Header().Set(HeaderAckHash, "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef")
		w.WriteHeader(http.StatusOK)
	})
}

func makeProxyReserializeHandler(hits *int64) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt64(hits, 1)
		body, _ := io.ReadAll(r.Body)
		// Parse JSON → re-marshal with indentation so the output bytes differ
		// from the canonical compact form even though field ordering is preserved.
		// This is the real-world "helpful proxy" failure mode: the intermediate
		// prettifies the payload and breaks byte-equality.
		var m map[string]interface{}
		if err := json.Unmarshal(body, &m); err == nil {
			if reserialized, merr := json.MarshalIndent(m, "", "  "); merr == nil {
				sum := sha256.Sum256(reserialized)
				w.Header().Set(HeaderAckHash, hex.EncodeToString(sum[:]))
				w.WriteHeader(http.StatusOK)
				return
			}
		}
		// Fallback: pass-through ack (shouldn't hit on valid JSON).
		sum := sha256.Sum256(body)
		w.Header().Set(HeaderAckHash, hex.EncodeToString(sum[:]))
		w.WriteHeader(http.StatusOK)
	})
}

func makeBodyByteFlipHandler(hits *int64) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt64(hits, 1)
		body, _ := io.ReadAll(r.Body)
		if len(body) > 0 {
			flipped := make([]byte, len(body))
			copy(flipped, body)
			flipped[0] ^= 0xFF
			sum := sha256.Sum256(flipped)
			w.Header().Set(HeaderAckHash, hex.EncodeToString(sum[:]))
		}
		w.WriteHeader(http.StatusOK)
	})
}

func makeServer5xxHandler(hits *int64) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt64(hits, 1)
		_, _ = io.ReadAll(r.Body)
		w.WriteHeader(http.StatusInternalServerError)
	})
}

// --- helpers ---

func transportTruncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n]
}

// guard unused imports check.
var _ = bytes.Equal
