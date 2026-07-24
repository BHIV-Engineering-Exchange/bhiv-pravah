// legacy_enforcer_shim.go (v14.8 Sovereign Authority Closure)
//
// --legacy-shim runtime role. An in-tree, deterministic REFERENCE legacy
// enforcer. Accepts a signed ExternalDecision, runs it through an independent
// PDPAdapter instance in its OWN process, returns the canonical response
// bytes + hash. The whole point is to demonstrate two facts at once:
//
//   1. Given byte-identical input, the Sarathi pipeline is byte-stable across
//      independent OS processes running the same code. This is the
//      construction-level proof for the parallel-execution invariant.
//   2. The wire contract (schema-version, canonical JSON, hash algorithm,
//      field set) is portable. A real BHIV Core implementation that satisfies
//      the same contract will converge on the same bytes; anything else will
//      be caught by the parallel-execution comparator.
//
// Operators can swap the in-tree shim for a real BHIV Core endpoint by
// setting SARATHI_LEGACY_ENFORCE_URL=http://.../v1/legacy-enforce before
// launching --parallel-execute. When the env var is set, the parallel runner
// bypasses --legacy-shim entirely and POSTs directly to the configured URL.
//
// Endpoints:
//   GET  /health
//   POST /v1/legacy-enforce   body=canonical ExternalDecision bytes
//                             -> JSON{decision_id, response_hash,
//                                    canonical_response_bytes_hex}
//
// Persistence:
//   live/legacy/<decision_id>.json    verbatim canonical response bytes
//   live/legacy/legacy.jsonl          append-only audit of every POST
//
// TAG: sovereign-authority-v14.8

package main

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"sync"
	"time"
)

// LegacyShimSchemaVersion pins the shim's response envelope version.
const LegacyShimSchemaVersion = "sarathi.legacy.shim/v14.8"

// LegacyShimDefaultAddr is the shim's listen address when
// SARATHI_LEGACY_SHIM_ADDR is not set. Uses an ephemeral port on the bind
// host so parallel runners can pick it off the PID file.
const LegacyShimDefaultAddrEnv = "SARATHI_LEGACY_SHIM_ADDR"

// LegacyShimStoragePath is the root under which the shim persists canonical
// response bytes per decision_id.
const LegacyShimStoragePath = "live/legacy"

// LegacyShimAuditLogName is the append-only audit JSONL.
const LegacyShimAuditLogName = "legacy.jsonl"

// LegacyShimAddrFile is the file the shim writes with its bound address —
// parallel runner reads this to discover the port when Addr was ephemeral.
const LegacyShimAddrFile = "live/legacy/.addr"

// LegacyEnforceEndpoint is the canonical URL path Sarathi's parallel runner
// POSTs to. A real BHIV Core endpoint pointed at via SARATHI_LEGACY_ENFORCE_URL
// must implement this exact path (or the full URL must encode it).
const LegacyEnforceEndpoint = "/v1/legacy-enforce"

// LegacyShimResponse is the wire contract the parallel runner expects back.
type LegacyShimResponse struct {
	SchemaVersion             string `json:"schema_version"`
	DecisionID                string `json:"decision_id"`
	ResponseHash              string `json:"response_hash"`
	CanonicalResponseBytesHex string `json:"canonical_response_bytes_hex"`
	ProcessedAt               string `json:"processed_at"`
	EnforcerID                string `json:"enforcer_id"`
}

// LegacyShimServer bundles the independent PDPAdapter + persistence layer.
type LegacyShimServer struct {
	pa         *PDPAdapter
	store      string
	auditPath  string
	mu         sync.Mutex
	enforcerID string

	srv *http.Server
	ln  net.Listener
}

// RunLegacyShim is the --legacy-shim entry point. Runs forever (or until
// ctrl-c / parent-death if SARATHI_PEER_PARENT_PID is set).
func RunLegacyShim() int {
	fmt.Println("[legacy-shim] starting…")

	srv, err := newLegacyShimServer()
	if err != nil {
		fmt.Fprintf(os.Stderr, "[legacy-shim] init: %v\n", err)
		return 1
	}

	addr := os.Getenv(LegacyShimDefaultAddrEnv)
	if addr == "" {
		addr = bindHost() + ":0" // ephemeral
	}

	if err := srv.Start(addr); err != nil {
		fmt.Fprintf(os.Stderr, "[legacy-shim] start: %v\n", err)
		return 1
	}
	fmt.Printf("[legacy-shim] listening on %s storage=%s enforcer_id=%s\n",
		srv.ln.Addr().String(), srv.store, srv.enforcerID)

	// Write addr file so the parallel runner can discover the bound port.
	_ = os.MkdirAll(filepath.Dir(LegacyShimAddrFile), 0o755)
	_ = os.WriteFile(LegacyShimAddrFile, []byte(srv.ln.Addr().String()), 0o644)

	// Optional parent-death watchdog (when spawned by parallel runner).
	if pid, _ := strconv.Atoi(os.Getenv("SARATHI_PEER_PARENT_PID")); pid > 0 {
		go parentWatchStandalone(pid, func() {
			fmt.Println("[legacy-shim] parent died, shutting down.")
			_ = srv.Stop()
		})
	}

	// Block forever; Stop via parent watchdog or signal.
	select {}
}

// newLegacyShimServer constructs the in-process enforcer but defers starting
// the HTTP listener.
func newLegacyShimServer() (*LegacyShimServer, error) {
	if err := os.MkdirAll(LegacyShimStoragePath, 0o755); err != nil {
		return nil, fmt.Errorf("mkdir shim storage: %w", err)
	}

	// Independent PDPAdapter. This is the key to byte-identity: same code
	// path, fresh state, different process.
	agentReg := NewRegistryInterface()
	ea := NewEnforcementAdapter(nil, nil, agentReg, nil)
	ea.InitExternalMode()
	mc := NewModeController(BHIVModeExternal)
	pa := NewPDPAdapter(ea, mc)

	enforcerID := fmt.Sprintf("legacy-shim-%d", os.Getpid())

	return &LegacyShimServer{
		pa:         pa,
		store:      LegacyShimStoragePath,
		auditPath:  filepath.Join(LegacyShimStoragePath, LegacyShimAuditLogName),
		enforcerID: enforcerID,
	}, nil
}

// Start opens the HTTP listener. Blocks until Stop() is called.
func (s *LegacyShimServer) Start(addr string) error {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", s.handleHealth)
	mux.HandleFunc(LegacyEnforceEndpoint, s.handleEnforce)
	mux.HandleFunc("/v1/register-evaluator", s.handleRegisterEvaluator)

	s.srv = &http.Server{
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return fmt.Errorf("legacy-shim listen %s: %w", addr, err)
	}
	s.ln = ln
	go func() { _ = s.srv.Serve(ln) }()
	return nil
}

// Stop triggers graceful shutdown.
func (s *LegacyShimServer) Stop() error {
	if s.srv != nil {
		return s.srv.Close()
	}
	return nil
}

// Addr returns the bound listener address (useful after ephemeral binding).
func (s *LegacyShimServer) Addr() string {
	if s.ln == nil {
		return ""
	}
	return s.ln.Addr().String()
}

func (s *LegacyShimServer) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]string{
		"ok":          "true",
		"enforcer_id": s.enforcerID,
		"schema":      LegacyShimSchemaVersion,
	})
}

// handleRegisterEvaluator is an out-of-band hook so the parallel runner can
// tell the shim which EvaluatorID + PublicKey to expect BEFORE sending
// enforce POSTs. Without this the shim's PDPAdapter would fail integrity
// checks on the incoming decisions (unknown evaluator).
func (s *LegacyShimServer) handleRegisterEvaluator(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method_not_allowed", http.StatusMethodNotAllowed)
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
	body, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "read_body: "+err.Error(), http.StatusBadRequest)
		return
	}
	var req struct {
		EvaluatorID  string `json:"evaluator_id"`
		PublicKeyHex string `json:"public_key_hex"`
	}
	if err := json.Unmarshal(body, &req); err != nil {
		http.Error(w, "unmarshal: "+err.Error(), http.StatusBadRequest)
		return
	}
	if req.EvaluatorID == "" || req.PublicKeyHex == "" {
		http.Error(w, "missing evaluator_id or public_key_hex", http.StatusBadRequest)
		return
	}
	pubBytes, err := hex.DecodeString(req.PublicKeyHex)
	if err != nil {
		http.Error(w, "pubkey hex: "+err.Error(), http.StatusBadRequest)
		return
	}
	if err := s.pa.adapter.GetEvaluatorRegistry().RegisterEvaluator(
		req.EvaluatorID, "parallel-execution legacy shim evaluator", pubBytes,
		map[string]string{"source": "legacy-shim"}, "parallel_execute",
	); err != nil {
		http.Error(w, "register: "+err.Error(), http.StatusConflict)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]string{
		"registered":  req.EvaluatorID,
		"enforcer_id": s.enforcerID,
	})
}

// handleEnforce is the main endpoint. Body is the exact canonical
// ExternalDecision bytes Sarathi also ingested.
func (s *LegacyShimServer) handleEnforce(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		writeShimErr(w, http.StatusMethodNotAllowed, CodeContractViolation,
			"method_not_allowed")
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, LivePeerMaxBodyBytes)
	raw, err := io.ReadAll(r.Body)
	if err != nil {
		writeShimErr(w, http.StatusBadRequest, CodePropagationByteMismatch,
			"read_body: "+err.Error())
		return
	}

	execID := r.Header.Get(HeaderExecutionID)
	corrID := r.Header.Get(HeaderCorrelationID)
	if execID == "" {
		execID = fmt.Sprintf("EXEC-LEGACY-%d", time.Now().UnixNano())
	}

	env, err := s.pa.Ingest(raw, execID, corrID, nil)
	if err != nil {
		writeShimErr(w, http.StatusUnprocessableEntity, CodePDPDecisionInvalid,
			"ingest: "+err.Error())
		return
	}

	canonBytes := env.CanonicalResponseBytes()
	hash := env.ResponseHash()
	decID := env.DecisionID()

	// Persist verbatim canonical bytes for reviewer inspection.
	s.mu.Lock()
	defer s.mu.Unlock()
	path := filepath.Join(s.store, safeDecisionID(decID)+".json")
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, canonBytes, 0o644); err != nil {
		writeShimErr(w, http.StatusServiceUnavailable, CodeDownstreamPersistFailed,
			"write_tmp: "+err.Error())
		return
	}
	if err := os.Rename(tmp, path); err != nil {
		writeShimErr(w, http.StatusServiceUnavailable, CodeDownstreamPersistFailed,
			"rename: "+err.Error())
		return
	}

	// Append audit row.
	audit := map[string]interface{}{
		"enforcer_id":   s.enforcerID,
		"decision_id":   decID,
		"execution_id":  execID,
		"response_hash": hash,
		"body_size":     len(canonBytes),
		"processed_at":  time.Now().UTC().Format(time.RFC3339Nano),
	}
	if b, merr := json.Marshal(audit); merr == nil {
		f, ferr := os.OpenFile(s.auditPath,
			os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
		if ferr == nil {
			_, _ = f.Write(append(b, '\n'))
			_ = f.Sync()
			_ = f.Close()
		}
	}

	resp := LegacyShimResponse{
		SchemaVersion:             LegacyShimSchemaVersion,
		DecisionID:                decID,
		ResponseHash:              hash,
		CanonicalResponseBytesHex: hex.EncodeToString(canonBytes),
		ProcessedAt:               time.Now().UTC().Format(time.RFC3339Nano),
		EnforcerID:                s.enforcerID,
	}
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set(HeaderAckHash, hash)
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(resp)
}

func writeShimErr(w http.ResponseWriter, status int, code, detail string) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set(HeaderErrorCode, code)
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{
		"error_code": code,
		"detail":     detail,
	})
}

// parentWatchStandalone is a minimal parent-death watchdog for --legacy-shim
// and --peer-standalone modes. Exits the process when the parent PID
// disappears. Separate from peer_common.go::parentWatch so that we do not
// require a full PeerServer to get this behaviour.
func parentWatchStandalone(pid int, onDeath func()) {
	tick := time.NewTicker(2 * time.Second)
	defer tick.Stop()
	for range tick.C {
		proc, err := os.FindProcess(pid)
		if err != nil {
			onDeath()
			return
		}
		if err := proc.Signal(nil); err != nil {
			onDeath()
			return
		}
	}
}
