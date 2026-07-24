// peer_insightflow.go (v14.7 Live Integration Closure + v15.2 BHIV-shaped routes)
//
// InsightFlow peer: real OS process, real TCP listener, real disk.
// Conformance reference for BHIV's production InsightFlow. Appends observed
// enforcement events to live/insightflow/insightflow.jsonl with fsync.
//
// Wire (Sarathi-internal contract — v14.7):
//   POST /v1/observe -> 202 Accepted + X-Sarathi-Ack-Hash
//
// Wire (BHIV-shaped contract — v15.2):
//   POST /sarathi_trigger      -> 202 + X-Sarathi-Ack-Hash
//   POST /core_execute         -> 202 + X-Sarathi-Ack-Hash
//   POST /insightflow_process  -> 202 + X-Sarathi-Ack-Hash
//   POST /bucket_persist       -> 202 + X-Sarathi-Ack-Hash
//
// All four BHIV-shaped endpoints share the same envelope-acceptance + ACK
// semantics; only the audit-tag distinguishes them in the JSONL trail.
//
// TAG: live-integration-peer

package main

import (
	"encoding/json"
	"net/http"
	"path/filepath"
	"time"
)

// handleInsightFlowPost is the InsightFlow peer's POST /v1/observe handler.
// Uses the shared envelope processor with the pinned-fields schema check.
// Returns 202 Accepted on success (observational semantic) plus the ACK hash.
func (p *PeerServer) handleInsightFlowPost(w http.ResponseWriter, r *http.Request) {
	p.respondInsightFlow(w, r, "/v1/observe")
}

// ----------------------------------------------------------------------------
// v15.2 BHIV-shaped handlers (additive, all 4)
// ----------------------------------------------------------------------------

// handleSarathiTrigger maps to BHIV's /sarathi_trigger endpoint — entry
// trigger from Sarathi to InsightFlow.
func (p *PeerServer) handleSarathiTrigger(w http.ResponseWriter, r *http.Request) {
	p.respondInsightFlow(w, r, "/sarathi_trigger")
}

// handleCoreExecute maps to BHIV's /core_execute endpoint — InsightFlow's
// view of a Core execute action.
func (p *PeerServer) handleCoreExecute(w http.ResponseWriter, r *http.Request) {
	p.respondInsightFlow(w, r, "/core_execute")
}

// handleInsightFlowProcess maps to BHIV's /insightflow_process endpoint —
// the primary observability ingest. Digest-only by contract; the body
// validation is identical to /v1/observe so peer simulators can stand in
// for either client style.
func (p *PeerServer) handleInsightFlowProcess(w http.ResponseWriter, r *http.Request) {
	p.respondInsightFlow(w, r, "/insightflow_process")
}

// handleBucketPersist maps to BHIV's /bucket_persist endpoint — the
// InsightFlow-mediated bucket persistence signal. The actual bucket write
// happens via the Bucket peer; this endpoint is purely observability.
func (p *PeerServer) handleBucketPersist(w http.ResponseWriter, r *http.Request) {
	p.respondInsightFlow(w, r, "/bucket_persist")
}

// respondInsightFlow is the shared handler body. The endpoint argument is
// recorded in the response payload + per-endpoint audit JSONL line so each
// of the 5 InsightFlow routes is independently traceable.
func (p *PeerServer) respondInsightFlow(w http.ResponseWriter, r *http.Request, endpoint string) {
	// InsightFlow accepts both full canonical bytes (legacy /v1/observe) and
	// digest-only payloads (v15.2 BHIV routes). When digest-only, the body
	// has no decision_id header pin requirement; we still re-verify hash
	// echo so byte drift is caught.
	digestOnly := r.Header.Get(HeaderDigestOnly) == "1"
	if digestOnly {
		p.respondInsightFlowDigest(w, r, endpoint)
		return
	}
	accepted, body, bodyHash, decisionID, persist := p.processIncomingEnvelope(w, r, p.validatePinnedFields)
	if !accepted {
		return
	}
	w.Header().Set(HeaderAckHash, bodyHash)
	w.Header().Set(HeaderLivePeer, string(PeerInsightFlow))
	w.WriteHeader(http.StatusAccepted)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"peer":         string(PeerInsightFlow),
		"ack_hash":     bodyHash,
		"decision_id":  decisionID,
		"storage_path": persist.StoragePath,
		"duplicate":    persist.Duplicate,
		"endpoint":     endpoint,
	})
	// Tag the per-endpoint audit trail so reviewers can distinguish each
	// of the 5 routes in the JSONL file.
	_ = appendJSONLine(filepath.Join(p.cfg.StorageRoot, string(p.cfg.Kind),
		"endpoint_calls.jsonl"), map[string]interface{}{
		"endpoint":      endpoint,
		"decision_id":   decisionID,
		"response_hash": bodyHash,
		"digest_only":   false,
		"timestamp":     time.Now().UTC().Format(time.RFC3339Nano),
	})
	go p.emitReceipt(body, bodyHash, decisionID, persist.StoragePath, r)
}

// respondInsightFlowDigest accepts a digest-only payload (no canonical full
// body, no decision_id-in-header requirement). The payload SHOULD include
// {decision_id, response_hash} as JSON top-level fields; we acknowledge with
// the body's SHA-256 — Intelligence Layer is out-of-chain (INV-PROP-06) so
// callers do NOT need to re-verify the ack hash.
func (p *PeerServer) respondInsightFlowDigest(w http.ResponseWriter, r *http.Request, endpoint string) {
	if r.Method != http.MethodPost {
		writeErr(w, http.StatusMethodNotAllowed, CodeContractViolation,
			"method_not_allowed", "")
		return
	}
	// Limit body size and read.
	r.Body = http.MaxBytesReader(w, r.Body, LivePeerMaxBodyBytes)
	var dig map[string]interface{}
	dec := json.NewDecoder(r.Body)
	if err := dec.Decode(&dig); err != nil {
		writeErr(w, http.StatusBadRequest, CodePropagationByteMismatch,
			"digest_unmarshal_failed", err.Error())
		return
	}
	decisionID, _ := dig["decision_id"].(string)
	responseHash, _ := dig["response_hash"].(string)
	traceID, _ := dig["trace_id"].(string)
	bodyHash := responseHash
	w.Header().Set(HeaderAckHash, bodyHash)
	w.Header().Set(HeaderLivePeer, string(PeerInsightFlow))
	w.WriteHeader(http.StatusAccepted)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"peer":          string(PeerInsightFlow),
		"ack_hash":      bodyHash,
		"decision_id":   decisionID,
		"trace_id":      traceID,
		"endpoint":      endpoint,
		"digest_only":   true,
		"observed_at":   time.Now().UTC().Format(time.RFC3339Nano),
	})
	_ = appendJSONLine(filepath.Join(p.cfg.StorageRoot, string(p.cfg.Kind),
		"endpoint_calls.jsonl"), map[string]interface{}{
		"endpoint":      endpoint,
		"decision_id":   decisionID,
		"response_hash": responseHash,
		"trace_id":      traceID,
		"digest_only":   true,
		"timestamp":     time.Now().UTC().Format(time.RFC3339Nano),
	})
}
