// peer_bucket.go (v14.7 Live Integration Closure + v15.2 BHIV-shaped routes)
//
// Bucket peer: the byte-equality source of truth.
// Stores each sealed canonical response at live/bucket/{decision_id}.json
// verbatim (atomic rename + fsync) so GET /v1/audit/{decision_id} returns
// bytes that are SHA-256-identical to what Sarathi sealed.
//
// Wire (Sarathi-internal contract — v14.7):
//   POST /v1/audit          body=canonical response
//     -> 200 OK + X-Sarathi-Ack-Hash
//   GET  /v1/audit/{id}
//     -> 200 OK body=stored bytes (byte-identical)
//     -> 404 Not Found when unknown
//
// Wire (BHIV-shaped contract — v15.2):
//   POST /bucket/artifact          body=canonical response
//     -> 200 OK + X-Sarathi-Ack-Hash
//   GET  /bucket/artifact/{id}
//     -> 200 OK body=stored bytes (byte-identical)
//   GET  /bucket/artifacts?trace_id={id}
//     -> 200 OK body={"artifacts":[{"decision_id":"...","response_hash":"..."}]}
//
// TAG: live-integration-peer

package main

import (
	"encoding/json"
	"net/http"
	"strings"
)

// handleBucketPost persists the sealed canonical bytes under decision_id
// atomically (tmp + fsync + rename). Duplicate-decision-same-hash is
// idempotent; duplicate-decision-different-hash returns 409 to surface a
// determinism violation.
func (p *PeerServer) handleBucketPost(w http.ResponseWriter, r *http.Request) {
	accepted, body, bodyHash, decisionID, persist := p.processIncomingEnvelope(w, r, p.validatePinnedFields)
	if !accepted {
		return
	}
	// v15.2: index trace_id -> decision_id for trace-level queries.
	if traceID := r.Header.Get(HeaderTraceID); traceID != "" {
		p.store.IndexByTraceID(traceID, decisionID)
	}
	w.Header().Set(HeaderAckHash, bodyHash)
	w.Header().Set(HeaderLivePeer, string(PeerBucket))
	w.WriteHeader(http.StatusOK)
	// Bucket ACK body is minimal — GET returns the full sealed bytes.
	_, _ = w.Write([]byte(`{"peer":"bucket","ack_hash":"` + bodyHash +
		`","decision_id":"` + decisionID +
		`","storage_path":"` + persist.StoragePath + `"}`))
	go p.emitReceipt(body, bodyHash, decisionID, persist.StoragePath, r)
}

// handleBucketGet returns the bytes stored for decision_id verbatim. This
// endpoint powers the end-to-end bucket read-back proof: Sarathi GETs the
// stored body and recomputes SHA-256 to confirm it matches response_hash.
// Any drift fails the execution closed.
func (p *PeerServer) handleBucketGet(w http.ResponseWriter, r *http.Request) {
	p.serveBucketGet(w, r, "/v1/audit/")
}

// ----------------------------------------------------------------------------
// v15.2 BHIV-shaped handlers (additive)
// ----------------------------------------------------------------------------

// handleArtifactPost is the BHIV-shaped alias of /v1/audit. Same drift
// semantics, same idempotency, same atomic on-disk persistence.
func (p *PeerServer) handleArtifactPost(w http.ResponseWriter, r *http.Request) {
	accepted, body, bodyHash, decisionID, persist := p.processIncomingEnvelope(w, r, p.validatePinnedFields)
	if !accepted {
		return
	}
	if traceID := r.Header.Get(HeaderTraceID); traceID != "" {
		p.store.IndexByTraceID(traceID, decisionID)
	}
	w.Header().Set(HeaderAckHash, bodyHash)
	w.Header().Set(HeaderLivePeer, string(PeerBucket))
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"peer":         string(PeerBucket),
		"ack_hash":     bodyHash,
		"decision_id":  decisionID,
		"storage_path": persist.StoragePath,
		"duplicate":    persist.Duplicate,
		"endpoint":     "/bucket/artifact",
	})
	go p.emitReceipt(body, bodyHash, decisionID, persist.StoragePath, r)
}

// handleArtifactGet is the BHIV-shaped alias of GET /v1/audit/{id}.
func (p *PeerServer) handleArtifactGet(w http.ResponseWriter, r *http.Request) {
	p.serveBucketGet(w, r, "/bucket/artifact/")
}

// handleArtifactsByTrace returns the list of artifacts for a given trace_id.
// Body shape: {"trace_id":"...","artifacts":[{decision_id,response_hash,...}]}.
// Empty trace returns 400; unknown trace returns 200 with empty array.
func (p *PeerServer) handleArtifactsByTrace(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeErr(w, http.StatusMethodNotAllowed, CodeContractViolation,
			"method_not_allowed", "")
		return
	}
	traceID := r.URL.Query().Get("trace_id")
	if traceID == "" {
		writeErr(w, http.StatusBadRequest, CodeContractViolation,
			"missing_trace_id", "trace_id query parameter required")
		return
	}
	decisionIDs := p.store.QueryByTraceID(traceID)
	artifacts := make([]map[string]interface{}, 0, len(decisionIDs))
	for _, id := range decisionIDs {
		body, err := p.store.ReadBody(id)
		if err != nil {
			// Skip artifacts that can't be read but record the gap.
			artifacts = append(artifacts, map[string]interface{}{
				"decision_id":   id,
				"response_hash": "",
				"error":         err.Error(),
			})
			continue
		}
		artifacts = append(artifacts, map[string]interface{}{
			"decision_id":   id,
			"response_hash": Sha256Hex(body),
			"size_bytes":    len(body),
			"storage_path":  "live/bucket/" + safeDecisionID(id) + ".json",
		})
	}
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set(HeaderLivePeer, string(PeerBucket))
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"trace_id":  traceID,
		"count":     len(artifacts),
		"artifacts": artifacts,
	})
}

// serveBucketGet is the shared GET-by-decision-id path used by both the
// /v1/audit/{id} legacy route and the /bucket/artifact/{id} BHIV-shaped
// route. The prefix argument tells the parser where to slice the URL.
func (p *PeerServer) serveBucketGet(w http.ResponseWriter, r *http.Request, prefix string) {
	p.mu.Lock()
	p.totalGets++
	p.mu.Unlock()

	if r.Method != http.MethodGet {
		writeErr(w, http.StatusMethodNotAllowed, CodeContractViolation,
			"method_not_allowed", "")
		return
	}
	if !strings.HasPrefix(r.URL.Path, prefix) {
		writeErr(w, http.StatusBadRequest, CodeContractViolation,
			"bad_path", r.URL.Path)
		return
	}
	id := strings.TrimPrefix(r.URL.Path, prefix)
	if id == "" {
		writeErr(w, http.StatusBadRequest, CodeContractViolation,
			"missing_decision_id", "")
		return
	}
	if safeDecisionID(id) != id {
		writeErr(w, http.StatusBadRequest, CodeContractViolation,
			"invalid_decision_id", "decision_id must match [A-Za-z0-9_-]")
		return
	}
	body, err := p.store.ReadBody(id)
	if err != nil {
		writeErr(w, http.StatusNotFound, CodeContractViolation,
			"not_found", err.Error())
		return
	}
	ackHash := Sha256Hex(body)
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set(HeaderAckHash, ackHash)
	w.Header().Set(HeaderLivePeer, string(PeerBucket))
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(body)
}
