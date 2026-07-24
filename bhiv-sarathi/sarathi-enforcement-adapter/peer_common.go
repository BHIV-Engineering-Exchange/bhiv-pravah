// peer_common.go (v14.7 Live Integration Closure)
//
// Shared primitives for the three real downstream peer processes (BHIV Core,
// InsightFlow, Bucket). Each peer is an independent OS process started via
// --peer-core / --peer-insightflow / --peer-bucket. They are NOT mocks:
//
//   - Real TCP listeners (net.Listen), not httptest.Server.
//   - Real disk persistence with atomic rename + fsync.
//   - Real SHA-256 recomputation using the SAME canonical_json.go library
//     Sarathi uses — agreement on RFC 8785 canonicalization is an INVARIANT,
//     not a mock (in-toto / SLSA / Sigstore pattern).
//   - Real Ed25519-signed verification receipts POSTed back to Sarathi's
//     /v1/downstream-ack. The closed loop is what turns byte-equality at the
//     peer into end-to-end verified state.
//
// When BHIV supplies production URLs, the peer processes are NOT started;
// operator sets SARATHI_ROUTE_*_URL to the real endpoints and Sarathi's code
// is unchanged. The peers are a conformance reference implementation of the
// wire contract BHIV's production systems must also satisfy.
//
// TAG: live-integration-peer

package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// PeerKind enumerates the three real downstream peers. Keep in lockstep with
// PropagationChainOrder in multi_system_router_propagation.go.
type PeerKind string

const (
	PeerCore        PeerKind = "core"
	PeerInsightFlow PeerKind = "insightflow"
	PeerBucket      PeerKind = "bucket"
)

// LivePeerDefaultPorts assigns each peer a default TCP port. The runner
// overrides via --peer-port flag; nothing here is load-bearing except that
// the runner and peers agree at start-up.
var LivePeerDefaultPorts = map[PeerKind]int{
	PeerCore:        7101,
	PeerInsightFlow: 7102,
	PeerBucket:      7103,
}

// LivePeerDefaultStorageRoot is where each peer writes its persistent store.
// Runner creates the subdirectories up front; peers never mkdir at runtime
// outside their own root.
const LivePeerDefaultStorageRoot = "live"

// LivePeerMaxBodyBytes caps inbound POST bodies at 1 MiB. Sarathi's sealed
// canonical bytes are ~2-4 KiB; 1 MiB gives ~250x headroom with hard ceiling.
const LivePeerMaxBodyBytes = 1 << 20

// LivePeerReceiptSchemaVersion pins the receipt wire shape.
const LivePeerReceiptSchemaVersion = "sarathi.live.receipt/v1.0"

// LivePeerHandshakeSchemaVersion pins the handshake wire shape.
const LivePeerHandshakeSchemaVersion = "sarathi.live.handshake/v1.0"

// Header names specific to live-peer wire contract.
const (
	HeaderErrorCode      = "X-Sarathi-Error-Code"
	HeaderDigestOnly     = "X-Sarathi-Digest-Only"
	HeaderLivePeer       = "X-Sarathi-Live-Peer"
	HeaderLivePeerPubKey = "X-Sarathi-Live-Peer-Pubkey"
)

// ============================================================================
// PEER STORE — real disk persistence
// ============================================================================

// PeerStore is a disk-backed append-only store (Core, InsightFlow) or a
// per-key file store (Bucket). Every write is fsync'd before ACK. Writes
// are atomic on the key's namespace via os.Rename on the key-file variant,
// or via file-level mutex + fsync on the JSONL variant.
type PeerStore struct {
	kind      PeerKind
	root      string
	jsonlPath string       // used by append-only peers (Core, InsightFlow)
	mu        sync.Mutex   // serialises writes
	seenIndex map[string]string
	// seenIndex maps decision_id -> response_hash. Duplicate POST with same
	// hash returns the original receipt (idempotency); duplicate POST with
	// different hash is rejected as a determinism violation.

	// v15.2: trace_id -> []decision_id index. Built incrementally on every
	// PersistBody call where a trace_id is supplied (header). Used by
	// /bucket/artifacts?trace_id= for trace-level verification.
	traceIndex map[string][]string
}

// NewPeerStore initialises a peer store and creates its directory tree.
func NewPeerStore(kind PeerKind, root string) (*PeerStore, error) {
	dir := filepath.Join(root, string(kind))
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return nil, fmt.Errorf("peer_store: mkdir %s: %w", dir, err)
	}
	ps := &PeerStore{
		kind:       kind,
		root:       dir,
		jsonlPath:  filepath.Join(dir, string(kind)+".jsonl"),
		seenIndex:  make(map[string]string),
		traceIndex: make(map[string][]string),
	}
	// Restore seen index from existing jsonl on crash-recovery.
	if data, err := os.ReadFile(ps.jsonlPath); err == nil {
		for _, line := range strings.Split(string(data), "\n") {
			if line == "" {
				continue
			}
			var rec map[string]interface{}
			if jerr := json.Unmarshal([]byte(line), &rec); jerr != nil {
				continue
			}
			if d, ok := rec["decision_id"].(string); ok {
				if h, ok2 := rec["response_hash"].(string); ok2 {
					ps.seenIndex[d] = h
				}
			}
		}
	}
	return ps, nil
}

// PersistResult describes what happened on a POST.
type PersistResult struct {
	Duplicate    bool   // previously stored with same hash
	DriftRejected bool   // duplicate decision_id with DIFFERENT hash (halt)
	StoragePath string
	OffsetBytes int64
}

// PersistBody stores the body under decision_id. For Core and InsightFlow
// the body is appended as a single JSONL line with a wrapper containing the
// raw body base64-encoded so byte-equality survives. For Bucket the body is
// stored verbatim at {root}/bucket/{decision_id}.json so GET returns the
// EXACT bytes Sarathi sealed.
func (ps *PeerStore) PersistBody(decisionID, responseHash string, body []byte) (PersistResult, error) {
	ps.mu.Lock()
	defer ps.mu.Unlock()

	if existing, ok := ps.seenIndex[decisionID]; ok {
		if existing == responseHash {
			return PersistResult{Duplicate: true, StoragePath: ps.storagePath(decisionID)}, nil
		}
		return PersistResult{DriftRejected: true}, fmt.Errorf(
			"duplicate decision_id=%s with drifted hash: stored=%s received=%s",
			decisionID, existing, responseHash)
	}

	if ps.kind == PeerBucket {
		path := ps.storagePath(decisionID)
		tmp := path + ".tmp"
		f, err := os.OpenFile(tmp, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
		if err != nil {
			return PersistResult{}, fmt.Errorf("create tmp: %w", err)
		}
		if _, err := f.Write(body); err != nil {
			_ = f.Close()
			_ = os.Remove(tmp)
			return PersistResult{}, fmt.Errorf("write tmp: %w", err)
		}
		if err := f.Sync(); err != nil {
			_ = f.Close()
			_ = os.Remove(tmp)
			return PersistResult{}, fmt.Errorf("fsync tmp: %w", err)
		}
		if err := f.Close(); err != nil {
			_ = os.Remove(tmp)
			return PersistResult{}, fmt.Errorf("close tmp: %w", err)
		}
		if err := os.Rename(tmp, path); err != nil {
			return PersistResult{}, fmt.Errorf("rename: %w", err)
		}
		ps.seenIndex[decisionID] = responseHash
		return PersistResult{StoragePath: path}, nil
	}

	// Core / InsightFlow: append JSONL record wrapping the body.
	// The body itself is hex-encoded so the JSONL line is self-contained and
	// round-trippable. Sarathi verifies hashes against the live/bucket/*.json
	// file for byte-equality; the jsonl here is an audit trail, not the
	// byte-equality source of truth.
	rec := map[string]interface{}{
		"peer":          string(ps.kind),
		"decision_id":   decisionID,
		"response_hash": responseHash,
		"body_hex":      hex.EncodeToString(body),
		"body_size":     len(body),
		"persisted_at":  time.Now().UTC().Format(time.RFC3339Nano),
	}
	line, err := json.Marshal(rec)
	if err != nil {
		return PersistResult{}, fmt.Errorf("marshal: %w", err)
	}
	line = append(line, '\n')

	f, err := os.OpenFile(ps.jsonlPath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return PersistResult{}, fmt.Errorf("open jsonl: %w", err)
	}
	off, _ := f.Seek(0, io.SeekEnd)
	if _, err := f.Write(line); err != nil {
		_ = f.Close()
		return PersistResult{}, fmt.Errorf("append: %w", err)
	}
	if err := f.Sync(); err != nil {
		_ = f.Close()
		return PersistResult{}, fmt.Errorf("fsync: %w", err)
	}
	if err := f.Close(); err != nil {
		return PersistResult{}, fmt.Errorf("close: %w", err)
	}
	ps.seenIndex[decisionID] = responseHash
	return PersistResult{StoragePath: fmt.Sprintf("%s#offset=%d", ps.jsonlPath, off), OffsetBytes: off}, nil
}

// storagePath returns the disk path for a given decision_id (Bucket only).
func (ps *PeerStore) storagePath(decisionID string) string {
	if ps.kind == PeerBucket {
		return filepath.Join(ps.root, safeDecisionID(decisionID)+".json")
	}
	return ps.jsonlPath
}

// ReadBody returns the stored bytes for decisionID (Bucket only).
func (ps *PeerStore) ReadBody(decisionID string) ([]byte, error) {
	if ps.kind != PeerBucket {
		return nil, fmt.Errorf("peer %s does not support GET", ps.kind)
	}
	path := filepath.Join(ps.root, safeDecisionID(decisionID)+".json")
	return os.ReadFile(path)
}

// IndexByTraceID associates decisionID with traceID for later query via
// QueryByTraceID. Safe to call multiple times for the same pair (de-dup).
// v15.2: powers the /bucket/artifacts?trace_id= endpoint.
func (ps *PeerStore) IndexByTraceID(traceID, decisionID string) {
	if traceID == "" || decisionID == "" {
		return
	}
	ps.mu.Lock()
	defer ps.mu.Unlock()
	for _, id := range ps.traceIndex[traceID] {
		if id == decisionID {
			return
		}
	}
	ps.traceIndex[traceID] = append(ps.traceIndex[traceID], decisionID)
}

// QueryByTraceID returns the list of decision_ids associated with traceID.
// Order is insertion order. Empty trace_id or unknown trace_id returns nil.
// v15.2.
func (ps *PeerStore) QueryByTraceID(traceID string) []string {
	if traceID == "" {
		return nil
	}
	ps.mu.Lock()
	defer ps.mu.Unlock()
	src := ps.traceIndex[traceID]
	if len(src) == 0 {
		return nil
	}
	out := make([]string, len(src))
	copy(out, src)
	return out
}

// safeDecisionID rejects path traversal. decision_ids come in via URL path
// segment on Bucket's GET; reject anything outside [A-Za-z0-9_-].
func safeDecisionID(id string) string {
	clean := make([]byte, 0, len(id))
	for i := 0; i < len(id); i++ {
		c := id[i]
		if (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
			(c >= '0' && c <= '9') || c == '-' || c == '_' {
			clean = append(clean, c)
		}
	}
	return string(clean)
}

// ============================================================================
// PEER RECEIPT SIGNER — Ed25519 closed-loop verification
// ============================================================================

// PeerReceipt is what a peer POSTs back to Sarathi after a successful store.
// Sarathi verifies Signature and that ReceivedBodyHash == ResponseHash before
// marking the execution's peer-gate satisfied.
type PeerReceipt struct {
	SchemaVersion     string `json:"schema_version"`
	Peer              string `json:"peer"`
	ExecutionID       string `json:"execution_id"`
	DecisionID        string `json:"decision_id"`
	ResponseHash      string `json:"response_hash"`
	ReceivedBodyHash  string `json:"received_body_hash"`
	ChainBindingHash  string `json:"chain_binding_hash"`
	PersistedAt       string `json:"persisted_at"`
	StoragePath       string `json:"storage_path"`
	PeerPublicKeyHex  string `json:"peer_public_key_hex"`
	// v15.12 dual-hash model: peer extracts the canonical 20-field response
	// from the wrapper (Bucket: payload.canonical_response_b64; InsightFlow:
	// canonical_response_b64 at top level), base64-decodes, SHA-256-hashes,
	// puts the result here. Sarathi compares it to its minted response_hash
	// at receipt time. Empty allowed for backwards-compat callbacks during
	// migration; v15.12 production requires it set.
	ObservedResponseHash string `json:"observed_response_hash,omitempty"`
	ReceiptSignature  string `json:"receipt_signature,omitempty"`
}

// PeerReceiptSigner generates an Ed25519 keypair on startup (per-peer-process
// identity) and signs receipts. Public key is included in each receipt so
// Sarathi can verify without an out-of-band key directory. In production the
// public key would be pinned at handshake time.
type PeerReceiptSigner struct {
	pub  ed25519.PublicKey
	priv ed25519.PrivateKey
}

// NewPeerReceiptSigner mints a fresh keypair for this peer process.
func NewPeerReceiptSigner() (*PeerReceiptSigner, error) {
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return nil, fmt.Errorf("ed25519 keygen: %w", err)
	}
	return &PeerReceiptSigner{pub: pub, priv: priv}, nil
}

// Sign produces the canonical signed form of r. The signature covers the
// canonical bytes of r with ReceiptSignature cleared.
func (s *PeerReceiptSigner) Sign(r *PeerReceipt) ([]byte, error) {
	r.SchemaVersion = LivePeerReceiptSchemaVersion
	r.PeerPublicKeyHex = hex.EncodeToString(s.pub)
	r.ReceiptSignature = ""
	preSign, err := CanonicalMarshal(r)
	if err != nil {
		return nil, fmt.Errorf("canonical receipt: %w", err)
	}
	sig := ed25519.Sign(s.priv, preSign)
	r.ReceiptSignature = hex.EncodeToString(sig)
	return CanonicalMarshal(r)
}

// VerifyReceipt returns (ok, detail). Sarathi side. Rehydrates the receipt,
// clears Signature, canonicalizes, and verifies against the embedded pubkey.
//
// v15.9 hardening (closes the prior TOFU weakness):
//
//   After signature verification succeeds, two additional gates fire:
//
//     a) Peer-key registry pinning (peer_key_registry.go::CheckPinned)
//        - Cross-peer impersonation defence (peer field must be a known kind)
//        - Registry presence (strict mode: required; relaxed mode: warn-only)
//        - Status check (ACTIVE only; SUSPENDED/REVOKED reject)
//        - Constant-time key pinning (embedded key MUST equal registered)
//
//     b) Receipt-replay rejection (peer_receipt_replay.go::Check)
//        - sha256(raw receipt bytes) keyed by peer
//        - 300 s window; duplicate receipt within window is rejected
//
// Both gates are FAIL-CLOSED. Signature verification ALONE no longer
// suffices for a receipt to be accepted.
func VerifyReceipt(raw []byte) (*PeerReceipt, bool, string) {
	var r PeerReceipt
	if err := json.Unmarshal(raw, &r); err != nil {
		return nil, false, fmt.Sprintf("unmarshal: %v", err)
	}
	if r.SchemaVersion != LivePeerReceiptSchemaVersion {
		return &r, false, fmt.Sprintf("schema_version mismatch: got=%s want=%s",
			r.SchemaVersion, LivePeerReceiptSchemaVersion)
	}
	pubBytes, err := hex.DecodeString(r.PeerPublicKeyHex)
	if err != nil || len(pubBytes) != ed25519.PublicKeySize {
		return &r, false, "invalid peer_public_key_hex"
	}
	sigBytes, err := hex.DecodeString(r.ReceiptSignature)
	if err != nil || len(sigBytes) != ed25519.SignatureSize {
		return &r, false, "invalid receipt_signature"
	}
	rCopy := r
	rCopy.ReceiptSignature = ""
	preSign, err := CanonicalMarshal(&rCopy)
	if err != nil {
		return &r, false, fmt.Sprintf("canonical: %v", err)
	}
	if !ed25519.Verify(ed25519.PublicKey(pubBytes), preSign, sigBytes) {
		return &r, false, "signature verification failed"
	}

	// v15.12 dual-hash transport + decision integrity gates.
	// Look up Sarathi's minted (body_hash, response_hash) for this
	// (decision_id, peer). If the OutboundHashStore knows about it, both
	// checks are load-bearing. If the store doesn't know (legacy / dev /
	// pre-migration), fall back to the previous body_hash == response_hash
	// byte-equality check (which only worked under Path A but stays as a
	// graceful-degradation safety net).
	if store := ActivePeerOutboundHashStore(); store != nil {
		if minted, found := store.Lookup(r.DecisionID, r.Peer); found {
			// G1 — transport integrity: bytes Sarathi sent == bytes peer received.
			if r.ReceivedBodyHash != minted.BodyHash {
				return &r, false, fmt.Sprintf(
					"transport_integrity: received_body_hash=%s minted_body_hash=%s (peer received different bytes than Sarathi sent)",
					r.ReceivedBodyHash, minted.BodyHash)
			}
			// G2 — decision integrity: peer extracted canonical_response from
			// the wrapper, hashed it, must equal Sarathi's response_hash.
			if r.ObservedResponseHash == "" {
				return &r, false, "decision_integrity: receipt missing observed_response_hash (peer must compute from canonical_response_b64)"
			}
			if r.ObservedResponseHash != minted.ResponseHash {
				return &r, false, fmt.Sprintf(
					"decision_integrity: observed_response_hash=%s minted_response_hash=%s (peer's extracted 20-field hash differs from Sarathi's)",
					r.ObservedResponseHash, minted.ResponseHash)
			}
			// Also confirm the receipt's echoed response_hash matches (defense-in-depth).
			if r.ResponseHash != "" && r.ResponseHash != minted.ResponseHash {
				return &r, false, fmt.Sprintf(
					"response_hash_echo_mismatch: receipt=%s minted=%s",
					r.ResponseHash, minted.ResponseHash)
			}
		} else {
			// Store doesn't know this (decision_id, peer). Could be a
			// pre-v15.12 peer or a receipt for an outbound we never tracked.
			// Apply the legacy byte-equality fallback.
			if r.ReceivedBodyHash != r.ResponseHash {
				return &r, false, fmt.Sprintf("body_hash != response_hash: got=%s want=%s (no outbound-store entry for decision_id=%s peer=%s; using legacy fallback)",
					r.ReceivedBodyHash, r.ResponseHash, r.DecisionID, r.Peer)
			}
		}
	} else {
		// No outbound store wired (legacy boot). Apply legacy byte-equality.
		if r.ReceivedBodyHash != r.ResponseHash {
			return &r, false, fmt.Sprintf("body_hash != response_hash: got=%s want=%s",
				r.ReceivedBodyHash, r.ResponseHash)
		}
	}

	// v15.9 — peer-key registry pinning gate.
	if reg := ActivePeerKeyRegistry(); reg != nil {
		if ok, reason := reg.CheckPinned(r.Peer, r.PeerPublicKeyHex); !ok {
			return &r, false, "peer_key_pinning: " + reason
		}
	}

	// v15.9 — receipt-replay gate.
	if store := ActivePeerReceiptReplayStore(); store != nil {
		if err := store.Check(r.Peer, raw, time.Now().UTC()); err != nil {
			return &r, false, err.Error()
		}
	}

	return &r, true, ""
}

// ============================================================================
// PEER HANDSHAKE — schema-version agreement
// ============================================================================

// PeerHandshakeResponse is what Sarathi returns at GET /v1/handshake so peers
// can pin the expected schema before accepting any POST.
type PeerHandshakeResponse struct {
	SchemaVersion          string   `json:"schema_version"`
	PropagationVersion     string   `json:"propagation_version"`
	LiveIntegrationVersion string   `json:"live_integration_version"`
	RequiredFields         []string `json:"required_fields"`
	PropagationFields      []string `json:"propagation_fields"`
	HashAlgo               string   `json:"hash_algo"`
	CanonicalAlgo          string   `json:"canonical_algo"`
	ServedAt               string   `json:"served_at"`
}

// NewPeerHandshakeResponse builds the handshake payload from the locked
// contract constants in response_contract.go + propagation_envelope.go.
func NewPeerHandshakeResponse() *PeerHandshakeResponse {
	return &PeerHandshakeResponse{
		SchemaVersion:          SchemaVersion,
		PropagationVersion:     "sarathi.propagation/v14.5",
		LiveIntegrationVersion: LivePeerHandshakeSchemaVersion,
		RequiredFields:         append([]string(nil), RequiredResponseFields...),
		PropagationFields:      append([]string(nil), PropagationResponseFields...),
		HashAlgo:               "sha256",
		CanonicalAlgo:          "rfc8785-jcs-equivalent",
		ServedAt:               time.Now().UTC().Format(time.RFC3339Nano),
	}
}

// ============================================================================
// PEER SERVER — the actual HTTP listener
// ============================================================================

// PeerServerConfig carries the knobs a peer binary reads from CLI flags / env.
type PeerServerConfig struct {
	Kind           PeerKind
	Addr           string // e.g. ":7101"
	StorageRoot    string // parent dir (each peer creates its subdir)
	SarathiAckURL  string // POST /v1/downstream-ack on Sarathi
	HandshakeURL   string // GET /v1/handshake on Sarathi
	ParentPID      int    // if > 0, peer exits when parent dies
	IdleShutdownSec int   // 0 = never
}

// PeerServer bundles the runtime objects shared across handlers.
type PeerServer struct {
	cfg    PeerServerConfig
	store  *PeerStore
	signer *PeerReceiptSigner
	srv    *http.Server
	ln     net.Listener

	// Lifecycle
	startedAt  time.Time
	mu         sync.Mutex
	totalPosts uint64
	totalGets  uint64

	// Expected contract (pinned at handshake); zero values until first handshake
	pinnedSchema  string
	pinnedFields  map[string]struct{}
}

// NewPeerServer constructs a peer server and performs the handshake with
// Sarathi. If the handshake fails, we still start — Sarathi may not be up
// yet in test topologies — but schema validation is disabled until a
// subsequent handshake succeeds. In the runner topology, Sarathi is started
// first so this is a non-issue.
func NewPeerServer(cfg PeerServerConfig) (*PeerServer, error) {
	if cfg.Addr == "" {
		cfg.Addr = fmt.Sprintf(":%d", LivePeerDefaultPorts[cfg.Kind])
	}
	if cfg.StorageRoot == "" {
		cfg.StorageRoot = LivePeerDefaultStorageRoot
	}
	store, err := NewPeerStore(cfg.Kind, cfg.StorageRoot)
	if err != nil {
		return nil, err
	}
	signer, err := NewPeerReceiptSigner()
	if err != nil {
		return nil, err
	}
	return &PeerServer{
		cfg:       cfg,
		store:     store,
		signer:    signer,
		startedAt: time.Now().UTC(),
	}, nil
}

// Start begins listening. Blocks until stopped.
func (p *PeerServer) Start() error {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", p.handleHealth)
	mux.HandleFunc("/v1/handshake-peer", p.handleHandshakeInfo)
	p.registerPeerRoutes(mux)

	p.srv = &http.Server{
		Addr:         p.cfg.Addr,
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}
	ln, err := net.Listen("tcp", p.cfg.Addr)
	if err != nil {
		return fmt.Errorf("peer %s listen %s: %w", p.cfg.Kind, p.cfg.Addr, err)
	}
	p.ln = ln

	// Pin contract by handshaking Sarathi if URL is set.
	if p.cfg.HandshakeURL != "" {
		if err := p.pinContract(); err != nil {
			fmt.Fprintf(os.Stderr, "[peer %s] handshake warning: %v\n", p.cfg.Kind, err)
		}
	}

	// Parent-death watchdog: if runner dies, peers should not leak.
	if p.cfg.ParentPID > 0 {
		go p.parentWatch()
	}

	// Write pid file for runner to track.
	pidFile := filepath.Join(p.cfg.StorageRoot, string(p.cfg.Kind), ".pid")
	_ = os.WriteFile(pidFile, []byte(fmt.Sprintf("%d", os.Getpid())), 0o644)

	fmt.Printf("[peer %s] listening on %s storage=%s pubkey=%s...\n",
		p.cfg.Kind, p.cfg.Addr, p.cfg.StorageRoot,
		hex.EncodeToString(p.signer.pub)[:16])

	err = p.srv.Serve(p.ln)
	if err != nil && err != http.ErrServerClosed {
		return err
	}
	return nil
}

// Stop triggers graceful shutdown.
func (p *PeerServer) Stop() {
	if p.srv != nil {
		_ = p.srv.Close()
	}
}

// registerPeerRoutes is implemented by peer-specific files: peer_bhic_core.go,
// peer_insightflow.go, peer_bucket.go each set up their /v1/... route. The
// common file does not know which peer this is; the peer-specific file does.
//
// v15.2 ADDITIVE: alongside the existing Sarathi-internal contract paths
// (/v1/enforce, /v1/observe, /v1/audit) every peer also exposes the BHIV-
// shaped paths the user provided. Both surfaces share the same handlers and
// the same drift/idempotency semantics; clients pick which path to use via
// EcosystemEndpoints. Existing v15.1 regression paths remain unchanged.
func (p *PeerServer) registerPeerRoutes(mux *http.ServeMux) {
	switch p.cfg.Kind {
	case PeerCore:
		// Sarathi-internal contract.
		mux.HandleFunc("/v1/enforce", p.handleCorePost)
		// BHIV-shaped (v15.2): 3 endpoints — Enforce, Execute, Health.
		// /health is already registered by Start(); /v1/enforce already
		// covers Core's primary in-chain hop. Add /v1/execute as an alias
		// so SARATHI_PARALLEL_TARGET=bhiv can compare against the same body
		// shape on a sibling endpoint.
		mux.HandleFunc("/v1/execute", p.handleCorePost)
	case PeerInsightFlow:
		// Sarathi-internal contract.
		mux.HandleFunc("/v1/observe", p.handleInsightFlowPost)
		// BHIV-shaped (v15.2): 4 endpoints.
		mux.HandleFunc("/sarathi_trigger", p.handleSarathiTrigger)
		mux.HandleFunc("/core_execute", p.handleCoreExecute)
		mux.HandleFunc("/insightflow_process", p.handleInsightFlowProcess)
		mux.HandleFunc("/bucket_persist", p.handleBucketPersist)
	case PeerBucket:
		// Sarathi-internal contract.
		mux.HandleFunc("/v1/audit", p.handleBucketPost)
		mux.HandleFunc("/v1/audit/", p.handleBucketGet)
		// BHIV-shaped (v15.2): 3 endpoints — Artifact POST, Artifact GET,
		// Artifacts-by-trace GET.
		mux.HandleFunc("/bucket/artifact", p.handleArtifactPost)
		mux.HandleFunc("/bucket/artifact/", p.handleArtifactGet)
		mux.HandleFunc("/bucket/artifacts", p.handleArtifactsByTrace)
	}
}

// handleHealth is a simple liveness probe.
func (p *PeerServer) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"peer":        string(p.cfg.Kind),
		"uptime_sec":  int64(time.Since(p.startedAt).Seconds()),
		"posts":       p.totalPosts,
		"gets":        p.totalGets,
		"pubkey_hex":  hex.EncodeToString(p.signer.pub),
		"started_at":  p.startedAt.Format(time.RFC3339Nano),
	})
}

// handleHandshakeInfo exposes the peer's identity for Sarathi-side pinning.
func (p *PeerServer) handleHandshakeInfo(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]string{
		"peer":       string(p.cfg.Kind),
		"pubkey_hex": hex.EncodeToString(p.signer.pub),
		"addr":       p.cfg.Addr,
	})
}

// pinContract fetches the handshake from Sarathi and locks expected fields.
func (p *PeerServer) pinContract() error {
	client := &http.Client{Timeout: 3 * time.Second}
	resp, err := client.Get(p.cfg.HandshakeURL)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("handshake status %d", resp.StatusCode)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	var h PeerHandshakeResponse
	if err := json.Unmarshal(body, &h); err != nil {
		return err
	}
	p.mu.Lock()
	p.pinnedSchema = h.SchemaVersion
	p.pinnedFields = make(map[string]struct{})
	for _, f := range h.RequiredFields {
		p.pinnedFields[f] = struct{}{}
	}
	for _, f := range h.PropagationFields {
		p.pinnedFields[f] = struct{}{}
	}
	p.mu.Unlock()
	fmt.Printf("[peer %s] pinned schema=%s (%d fields)\n",
		p.cfg.Kind, h.SchemaVersion, len(p.pinnedFields))
	return nil
}

// parentWatch exits the peer if the parent (runner) PID disappears. This is
// best-effort: cross-platform PID existence check via os.FindProcess + Signal(0).
func (p *PeerServer) parentWatch() {
	tick := time.NewTicker(2 * time.Second)
	defer tick.Stop()
	for range tick.C {
		proc, err := os.FindProcess(p.cfg.ParentPID)
		if err != nil {
			p.Stop()
			return
		}
		// On Windows FindProcess always succeeds — use Signal(0) probe.
		if err := proc.Signal(nil); err != nil {
			p.Stop()
			return
		}
	}
}

// ============================================================================
// PEER REQUEST PROCESSING — shared path for in-chain peers (Core/InsightFlow/Bucket POST)
// ============================================================================

// processIncomingEnvelope is the common POST handler for all three peers.
// Returns the HTTP status code + (optional) error code to emit, and the
// persist result so the peer-specific wrapper can customise the success path.
func (p *PeerServer) processIncomingEnvelope(
	w http.ResponseWriter, r *http.Request, validateSchema func([]byte) string,
) (accepted bool, body []byte, bodyHash string, decisionID string, persist PersistResult) {
	p.mu.Lock()
	p.totalPosts++
	p.mu.Unlock()

	if r.Method != http.MethodPost {
		writeErr(w, http.StatusMethodNotAllowed, CodeContractViolation,
			"method_not_allowed", "")
		return
	}

	// Body size cap
	r.Body = http.MaxBytesReader(w, r.Body, LivePeerMaxBodyBytes)
	body, err := io.ReadAll(r.Body)
	if err != nil {
		writeErr(w, http.StatusBadRequest, CodePropagationByteMismatch,
			"read_body_failed", err.Error())
		return
	}

	bodyHash = Sha256Hex(body)
	decisionID = r.Header.Get(HeaderDecisionID)
	wantHash := r.Header.Get(HeaderResponseHash)

	if decisionID == "" {
		writeErr(w, http.StatusBadRequest, CodePropagationByteMismatch,
			"missing_decision_id", "")
		return
	}
	if safeDecisionID(decisionID) != decisionID {
		writeErr(w, http.StatusBadRequest, CodePropagationByteMismatch,
			"invalid_decision_id", "decision_id must match [A-Za-z0-9_-]")
		return
	}
	if wantHash == "" || bodyHash != wantHash {
		// Precondition failed — echo received hash so Sarathi can diff.
		w.Header().Set(HeaderAckHash, bodyHash)
		writeErr(w, http.StatusPreconditionFailed, CodeResponseHashMismatch,
			"response_hash mismatch",
			fmt.Sprintf("header=%s computed=%s", wantHash, bodyHash))
		return
	}

	// Canonical form check — body MUST be byte-identical to its
	// re-canonicalisation. Proxies that re-serialise are the #1 cause of
	// silent byte drift.
	if ok, detail := VerifyCanonicalBytes(body); !ok {
		w.Header().Set(HeaderAckHash, bodyHash)
		writeErr(w, http.StatusPreconditionFailed, CodePropagationByteMismatch,
			"non_canonical_body", detail)
		return
	}

	// Schema validation — peer-specific.
	if validateSchema != nil {
		if errCode := validateSchema(body); errCode != "" {
			w.Header().Set(HeaderAckHash, bodyHash)
			writeErr(w, http.StatusUnprocessableEntity, errCode,
				"schema_mismatch", "")
			// Log violation for audit.
			_ = appendJSONLine(filepath.Join(p.cfg.StorageRoot, string(p.cfg.Kind),
				"schema_violations.jsonl"), map[string]interface{}{
				"decision_id": decisionID,
				"error_code":  errCode,
				"body_sha256": bodyHash,
				"timestamp":   time.Now().UTC().Format(time.RFC3339Nano),
			})
			return
		}
	}

	// Persist.
	res, err := p.store.PersistBody(decisionID, wantHash, body)
	if err != nil {
		w.Header().Set(HeaderAckHash, bodyHash)
		if res.DriftRejected {
			writeErr(w, http.StatusConflict, CodeResponseHashMismatch,
				"decision_id_drift", err.Error())
			return
		}
		writeErr(w, http.StatusServiceUnavailable, CodeDownstreamPersistFailed,
			"persist_failed", err.Error())
		return
	}

	persist = res
	accepted = true
	return
}

// emitReceipt signs and POSTs a verification receipt back to Sarathi. Called
// AFTER the synchronous ACK so the peer's HTTP handler returns quickly.
// Errors here are logged but do not un-persist the record — the asynchronous
// nature of the receipt mirrors at-least-once delivery semantics.
func (p *PeerServer) emitReceipt(body []byte, bodyHash, decisionID, storagePath string, r *http.Request) {
	if p.cfg.SarathiAckURL == "" {
		return
	}
	receipt := &PeerReceipt{
		Peer:             string(p.cfg.Kind),
		ExecutionID:      r.Header.Get(HeaderExecutionID),
		DecisionID:       decisionID,
		ResponseHash:     r.Header.Get(HeaderResponseHash),
		ReceivedBodyHash: bodyHash,
		ChainBindingHash: r.Header.Get(HeaderChainBinding),
		PersistedAt:      time.Now().UTC().Format(time.RFC3339Nano),
		StoragePath:      storagePath,
	}
	raw, err := p.signer.Sign(receipt)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[peer %s] sign receipt failed: %v\n", p.cfg.Kind, err)
		return
	}
	req, err := http.NewRequest("POST", p.cfg.SarathiAckURL, nil)
	if err != nil {
		return
	}
	req.Body = io.NopCloser(newBytesReader(raw))
	req.ContentLength = int64(len(raw))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set(HeaderLivePeer, string(p.cfg.Kind))
	client := &http.Client{Timeout: 3 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Fprintf(os.Stderr, "[peer %s] receipt POST failed: %v\n", p.cfg.Kind, err)
		return
	}
	_ = resp.Body.Close()
}

// ============================================================================
// Helpers
// ============================================================================

// writeErr sets the X-Sarathi-Error-Code header and writes a compact JSON error.
func writeErr(w http.ResponseWriter, status int, code, msg, detail string) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set(HeaderErrorCode, code)
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{
		"error_code": code,
		"error":      msg,
		"detail":     detail,
	})
}

// appendJSONLine is a small helper for audit side-channels (not the main store).
func appendJSONLine(path string, rec map[string]interface{}) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()
	b, err := json.Marshal(rec)
	if err != nil {
		return err
	}
	_, err = f.Write(append(b, '\n'))
	return err
}

// newBytesReader avoids importing bytes in peer_common.go given its already
// heavy import footprint; this is a minimal adapter.
type bytesReaderLite struct {
	buf []byte
	pos int
}

func newBytesReader(b []byte) *bytesReaderLite { return &bytesReaderLite{buf: b} }
func (b *bytesReaderLite) Read(p []byte) (int, error) {
	if b.pos >= len(b.buf) {
		return 0, io.EOF
	}
	n := copy(p, b.buf[b.pos:])
	b.pos += n
	return n, nil
}
