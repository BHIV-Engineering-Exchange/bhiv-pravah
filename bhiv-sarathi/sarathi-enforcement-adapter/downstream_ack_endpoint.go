// downstream_ack_endpoint.go (v14.7 Live Integration Closure)
//
// Sarathi-side HTTP endpoints used by the live peers:
//
//   GET  /v1/handshake         -> peer pins schema + required fields
//   POST /v1/downstream-ack    -> peer posts signed verification receipt
//
// The ACK handler verifies the Ed25519 signature, checks
// received_body_hash == response_hash, and records the receipt into the
// per-execution gate. Any invalid receipt is logged and rejected with
// CodeDownstreamReceiptInvalid. Valid receipts are appended to
// proof_logs/downstream_ack_receipts.jsonl as the audit trail.
//
// TAG: live-integration

package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// DownstreamAckReceiptsPath is where every verified receipt is appended.
const DownstreamAckReceiptsPath = "proof_logs/downstream_ack_receipts.jsonl"

// DownstreamAckRejectionsPath is where invalid receipts are logged for
// forensic review. Fail-closed means the gate will time out; this file
// records WHY it timed out.
const DownstreamAckRejectionsPath = "proof_logs/downstream_ack_rejections.jsonl"

var downstreamAckMu sync.Mutex

// RegisterDownstreamAckRoutes installs /v1/handshake + /v1/downstream-ack
// on the provided mux. Called by:
//   - service_boundary.go (production --service) when
//     SARATHI_ENABLE_PEER_RECEIPTS=1 or SARATHI_LIVE_INTEGRATION=1.
//   - live_integration_runner.go (the in-process --live-integration harness)
//     unconditionally — the harness owns its own mux.
//
// Mounting these endpoints does NOT initialize the AckTracker; valid
// receipts are still appended to proof_logs/downstream_ack_receipts.jsonl
// for audit. Per-execution gating only fires when the orchestrator opens
// a gate via tracker.Open().
func RegisterDownstreamAckRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/v1/handshake", handleHandshake)
	mux.HandleFunc("/v1/downstream-ack", handleDownstreamAck)
}

// handleHandshake serves the peer handshake contract.
func handleHandshake(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method_not_allowed", http.StatusMethodNotAllowed)
		return
	}
	resp := NewPeerHandshakeResponse()
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(resp)
}

// handleDownstreamAck receives signed receipts from peers.
func handleDownstreamAck(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method_not_allowed", http.StatusMethodNotAllowed)
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, LivePeerMaxBodyBytes)
	raw, err := io.ReadAll(r.Body)
	if err != nil {
		writeDownstreamAckErr(w, http.StatusBadRequest, CodeDownstreamReceiptInvalid,
			"read_body", err.Error())
		return
	}

	receipt, ok, detail := VerifyReceipt(raw)
	if !ok {
		_ = appendAckRejection(receipt, detail, raw)
		writeDownstreamAckErr(w, http.StatusBadRequest, CodeDownstreamReceiptInvalid,
			"invalid_receipt", detail)
		return
	}

	// Route to gate.
	tracker := GetGlobalAckTracker()
	if tracker == nil {
		// No tracker installed — we still log the receipt as an audit trail,
		// but respond with 200 so peers don't retry indefinitely. In a
		// deployed run the tracker is always installed; this branch exists
		// for adhoc smoke tests.
		_ = appendAckReceipt(receipt)
		w.WriteHeader(http.StatusOK)
		return
	}

	gate := tracker.Lookup(receipt.ExecutionID)
	if gate == nil {
		_ = appendAckRejection(receipt, "no_open_gate_for_execution_id", raw)
		writeDownstreamAckErr(w, http.StatusGone, CodeDownstreamReceiptInvalid,
			"unknown_execution", receipt.ExecutionID)
		return
	}
	satisfied := gate.Record(PeerKind(receipt.Peer), receipt)
	if err := appendAckReceipt(receipt); err != nil {
		// Fall-through: we still ACK; audit IO failure is not the peer's fault.
		fmt.Fprintf(os.Stderr, "[sarathi] append receipt failed: %v\n", err)
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"peer":          receipt.Peer,
		"execution_id":  receipt.ExecutionID,
		"gate_satisfied": satisfied,
		"recorded_at":   time.Now().UTC().Format(time.RFC3339Nano),
	})
}

// appendAckReceipt writes a verified receipt to the audit JSONL.
func appendAckReceipt(receipt *PeerReceipt) error {
	return appendAckJSON(DownstreamAckReceiptsPath, receipt)
}

// appendAckRejection logs a rejected receipt with the rejection reason.
func appendAckRejection(receipt *PeerReceipt, reason string, raw []byte) error {
	rec := map[string]interface{}{
		"rejected_at":  time.Now().UTC().Format(time.RFC3339Nano),
		"reason":       reason,
		"receipt":      receipt,
		"raw_preview":  safePreview(raw, 256),
	}
	return appendAckJSON(DownstreamAckRejectionsPath, rec)
}

func appendAckJSON(path string, v interface{}) error {
	downstreamAckMu.Lock()
	defer downstreamAckMu.Unlock()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	b, err := json.Marshal(v)
	if err != nil {
		return err
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()
	if _, err := f.Write(append(b, '\n')); err != nil {
		return err
	}
	return f.Sync()
}

func writeDownstreamAckErr(w http.ResponseWriter, status int, code, msg, detail string) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set(HeaderErrorCode, code)
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]string{
		"error_code": code,
		"error":      msg,
		"detail":     detail,
	})
}

func safePreview(b []byte, n int) string {
	if len(b) <= n {
		return string(b)
	}
	return string(b[:n]) + "...(truncated)"
}
