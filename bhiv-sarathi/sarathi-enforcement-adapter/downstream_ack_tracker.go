// downstream_ack_tracker.go (v14.7 Live Integration Closure)
//
// Sarathi-side per-execution gate for signed peer receipts.
// Every live-integration execution must collect exactly three in-chain
// receipts (core, insightflow, bucket) within the configured timeout. The
// tracker is the canonical source of truth for "has the full chain verified
// this execution end-to-end?" — if it fails to produce a satisfied gate,
// the execution is failed closed (CodeLiveIntegrationGateFailed).
//
// Design constraints:
//   - Stateful only during the live-integration window (TTL eviction).
//   - No silent success on partial ACKs — require all 3 peers with valid
//     signatures and ReceivedBodyHash == ResponseHash.
//   - Thread-safe; peers POST receipts asynchronously after the synchronous
//     200/202/OK returns to Sarathi's propagation client.
//
// TAG: live-integration

package main

import (
	"fmt"
	"sync"
	"time"
)

// ExpectedPeers is the fixed set of in-chain peers that must acknowledge an
// execution before its gate is considered satisfied. Kept in lockstep with
// PropagationChainOrder's in-chain subset.
var ExpectedPeers = []PeerKind{PeerCore, PeerInsightFlow, PeerBucket}

// DefaultAckTimeout is the window within which all three peer receipts must
// arrive. Overridable via SARATHI_DOWNSTREAM_ACK_TIMEOUT_MS.
const DefaultAckTimeout = 5 * time.Second

// ExecutionGate tracks receipts for a single execution_id.
type ExecutionGate struct {
	ExecutionID  string
	DecisionID   string
	ResponseHash string
	CreatedAt    time.Time
	Deadline     time.Time

	mu       sync.Mutex
	receipts map[PeerKind]*PeerReceipt
	errors   map[PeerKind]string
	done     chan struct{}
	closed   bool
}

// NewExecutionGate creates a gate with the given timeout.
func NewExecutionGate(executionID, decisionID, responseHash string, timeout time.Duration) *ExecutionGate {
	now := time.Now().UTC()
	return &ExecutionGate{
		ExecutionID:  executionID,
		DecisionID:   decisionID,
		ResponseHash: responseHash,
		CreatedAt:    now,
		Deadline:     now.Add(timeout),
		receipts:     make(map[PeerKind]*PeerReceipt),
		errors:       make(map[PeerKind]string),
		done:         make(chan struct{}),
	}
}

// Record stores a verified receipt. If this satisfies the gate, Wait() unblocks.
// Returns true if the gate became satisfied on this call.
func (g *ExecutionGate) Record(peer PeerKind, receipt *PeerReceipt) bool {
	g.mu.Lock()
	defer g.mu.Unlock()

	// Bind the receipt to this gate's response_hash. The peer's
	// ReceivedBodyHash was already verified to equal ResponseHash inside
	// VerifyReceipt; here we also bind it to THIS execution's hash.
	if receipt.ResponseHash != g.ResponseHash {
		g.errors[peer] = fmt.Sprintf("gate_hash_mismatch: gate=%s receipt=%s",
			g.ResponseHash, receipt.ResponseHash)
		return false
	}
	g.receipts[peer] = receipt

	// Check satisfaction.
	for _, p := range ExpectedPeers {
		if _, ok := g.receipts[p]; !ok {
			return false
		}
	}
	if !g.closed {
		close(g.done)
		g.closed = true
	}
	return true
}

// RecordError stores a rejection (signature invalid, schema mismatch, etc.).
// The gate remains open; caller can still receive later receipts from other
// peers, but the overall gate will never satisfy until a valid receipt
// overwrites the error (not supported here — error is sticky).
func (g *ExecutionGate) RecordError(peer PeerKind, detail string) {
	g.mu.Lock()
	defer g.mu.Unlock()
	if _, ok := g.errors[peer]; !ok {
		g.errors[peer] = detail
	}
}

// Wait blocks until either the gate is satisfied or timeout elapses.
// Returns (satisfied, summary).
func (g *ExecutionGate) Wait() (bool, GateSummary) {
	select {
	case <-g.done:
		return true, g.snapshot(true)
	case <-time.After(time.Until(g.Deadline)):
		return false, g.snapshot(false)
	}
}

// GateSummary is the serialisable end-state of a gate.
type GateSummary struct {
	ExecutionID   string                  `json:"execution_id"`
	DecisionID    string                  `json:"decision_id"`
	ResponseHash  string                  `json:"response_hash"`
	Satisfied     bool                    `json:"satisfied"`
	CreatedAt     string                  `json:"created_at"`
	ResolvedAt    string                  `json:"resolved_at"`
	ElapsedMs     int64                   `json:"elapsed_ms"`
	Receipts      map[string]*PeerReceipt `json:"receipts"`
	Errors        map[string]string       `json:"errors,omitempty"`
	MissingPeers  []string                `json:"missing_peers,omitempty"`
}

func (g *ExecutionGate) snapshot(satisfied bool) GateSummary {
	g.mu.Lock()
	defer g.mu.Unlock()
	resolved := time.Now().UTC()
	receipts := make(map[string]*PeerReceipt, len(g.receipts))
	for k, v := range g.receipts {
		receipts[string(k)] = v
	}
	errs := make(map[string]string, len(g.errors))
	for k, v := range g.errors {
		errs[string(k)] = v
	}
	missing := []string{}
	for _, p := range ExpectedPeers {
		if _, ok := g.receipts[p]; !ok {
			missing = append(missing, string(p))
		}
	}
	return GateSummary{
		ExecutionID:  g.ExecutionID,
		DecisionID:   g.DecisionID,
		ResponseHash: g.ResponseHash,
		Satisfied:    satisfied,
		CreatedAt:    g.CreatedAt.Format(time.RFC3339Nano),
		ResolvedAt:   resolved.Format(time.RFC3339Nano),
		ElapsedMs:    resolved.Sub(g.CreatedAt).Milliseconds(),
		Receipts:     receipts,
		Errors:       errs,
		MissingPeers: missing,
	}
}

// ============================================================================
// AckTracker — global registry of pending gates
// ============================================================================

// AckTracker is the process-wide registry of open execution gates. Installed
// as a singleton at Sarathi startup when SARATHI_LIVE_INTEGRATION=1.
type AckTracker struct {
	mu    sync.RWMutex
	gates map[string]*ExecutionGate // key = execution_id
	ttl   time.Duration
}

// NewAckTracker creates a tracker with the given per-gate lifetime.
func NewAckTracker(ttl time.Duration) *AckTracker {
	t := &AckTracker{
		gates: make(map[string]*ExecutionGate),
		ttl:   ttl,
	}
	go t.evictLoop()
	return t
}

// Open registers a new gate for execution_id. If a gate already exists (e.g.
// re-submission of the same execution), the existing gate is returned — this
// preserves idempotency under retry.
func (t *AckTracker) Open(executionID, decisionID, responseHash string) *ExecutionGate {
	t.mu.Lock()
	defer t.mu.Unlock()
	if g, ok := t.gates[executionID]; ok {
		return g
	}
	g := NewExecutionGate(executionID, decisionID, responseHash, t.ttl)
	t.gates[executionID] = g
	return g
}

// Lookup returns the gate for execution_id, or nil.
func (t *AckTracker) Lookup(executionID string) *ExecutionGate {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return t.gates[executionID]
}

// Close removes a gate from the tracker after the caller is done with it.
func (t *AckTracker) Close(executionID string) {
	t.mu.Lock()
	defer t.mu.Unlock()
	delete(t.gates, executionID)
}

// evictLoop removes gates older than 2*ttl to avoid unbounded growth under
// long-running Sarathi processes.
func (t *AckTracker) evictLoop() {
	tick := time.NewTicker(t.ttl)
	defer tick.Stop()
	for range tick.C {
		cutoff := time.Now().UTC().Add(-2 * t.ttl)
		t.mu.Lock()
		for id, g := range t.gates {
			if g.CreatedAt.Before(cutoff) {
				delete(t.gates, id)
			}
		}
		t.mu.Unlock()
	}
}

// ============================================================================
// Global singleton — installed at startup when live integration is active
// ============================================================================

var (
	globalAckTracker   *AckTracker
	globalAckTrackerMu sync.RWMutex
)

// InstallGlobalAckTracker wires the process-wide tracker. Called from
// live-integration runner startup.
func InstallGlobalAckTracker(t *AckTracker) {
	globalAckTrackerMu.Lock()
	defer globalAckTrackerMu.Unlock()
	globalAckTracker = t
}

// GetGlobalAckTracker returns the active tracker (nil if not installed).
func GetGlobalAckTracker() *AckTracker {
	globalAckTrackerMu.RLock()
	defer globalAckTrackerMu.RUnlock()
	return globalAckTracker
}
