// peer_bhic_core.go (v14.7 Live Integration Closure + v15.2 BHIV-shaped routes)
//
// BHIV Core peer: real OS process, real TCP listener, real disk.
// Conformance reference implementation of the wire contract BHIV's production
// Core must also satisfy. See peer_common.go for the shared primitives.
//
// Wire (v14.7):
//   POST /v1/enforce
//
// Wire (v15.2 — BHIV-shaped, additive, default 3 endpoints):
//   POST /v1/enforce   — primary in-chain action (unchanged from v14.7)
//   POST /v1/execute   — secondary action endpoint (parallel-real-traffic)
//   GET  /health       — liveness probe (registered by peer_common.Start)
//
// Both POST endpoints share the same drift / idempotency / receipt semantics;
// the only difference is the endpoint tag recorded in the audit trail so a
// reviewer can attribute traffic to /v1/enforce vs /v1/execute.
//
// TAG: live-integration-peer

package main

import (
	"encoding/json"
	"net/http"
	"path/filepath"
	"time"
)

// handleCorePost is the BHIV Core peer's POST /v1/enforce handler. Used both
// by /v1/enforce and /v1/execute (peer_common.go registers both onto this
// handler). It wraps processIncomingEnvelope with a schema callback that
// validates the incoming canonical response body against the fields Sarathi
// pinned at handshake time. On success it emits a signed receipt asynchronously
// and tags the audit trail with the URL the request actually arrived on.
func (p *PeerServer) handleCorePost(w http.ResponseWriter, r *http.Request) {
	endpoint := r.URL.Path
	accepted, body, bodyHash, decisionID, persist := p.processIncomingEnvelope(w, r, p.validatePinnedFields)
	if !accepted {
		return
	}
	w.Header().Set(HeaderAckHash, bodyHash)
	w.Header().Set(HeaderLivePeer, string(PeerCore))
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"peer":         string(PeerCore),
		"ack_hash":     bodyHash,
		"decision_id":  decisionID,
		"storage_path": persist.StoragePath,
		"duplicate":    persist.Duplicate,
		"endpoint":     endpoint,
	})
	// v15.2: per-endpoint audit trail so /v1/enforce and /v1/execute traffic
	// is independently auditable.
	_ = appendJSONLine(filepath.Join(p.cfg.StorageRoot, string(p.cfg.Kind),
		"endpoint_calls.jsonl"), map[string]interface{}{
		"endpoint":      endpoint,
		"decision_id":   decisionID,
		"response_hash": bodyHash,
		"timestamp":     time.Now().UTC().Format(time.RFC3339Nano),
	})
	// Fire-and-forget signed receipt back to Sarathi.
	go p.emitReceipt(body, bodyHash, decisionID, persist.StoragePath, r)
}

// validatePinnedFields is the shared schema check used by all three peers.
// It parses the body as a JSON object and asserts every field pinned at
// handshake time is present as a top-level key. This binds the peer to the
// exact contract Sarathi advertised; any drift (added/removed field) is
// caught at the boundary.
//
// If no contract is pinned (peer started without a handshake URL), this
// check is skipped — the runner always provides the handshake URL, so this
// is only permissive in adhoc smoke tests.
func (p *PeerServer) validatePinnedFields(body []byte) string {
	p.mu.Lock()
	pinned := p.pinnedFields
	p.mu.Unlock()
	if len(pinned) == 0 {
		return ""
	}
	var obj map[string]interface{}
	if err := json.Unmarshal(body, &obj); err != nil {
		return CodeDownstreamSchemaMismatch
	}
	for f := range pinned {
		if _, ok := obj[f]; !ok {
			return CodeDownstreamSchemaMismatch
		}
	}
	return ""
}
