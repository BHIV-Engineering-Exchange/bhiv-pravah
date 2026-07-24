// determinism_validator.go (v14.5 Cross-System Propagation Layer)
//
// Byte-equality oracle + violation recorder for the propagation chain.
//
// At every outbound hop the DeterministicHTTPRoutingHandler computes
// response_hash = Sha256Hex(sentBytes) and stamps it into the
// X-Sarathi-Response-Hash header. The peer echoes the hash back in the
// X-Sarathi-Ack-Hash header. ValidateHop compares expected vs ACK hash
// and, on drift, emits a PropagationStopError with CodeDeterminismViolation.
//
// Every violation is appended to proof_logs/determinism_violation_log.jsonl
// for forensic replay. A successful chain run is expected to produce an
// empty (or absent) file.

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// --- Hop identifiers used in the chain ---

// HopIDs are fixed strings so JSONL audit records are comparable across runs.
const (
	HopPDPIngest        = "pdp_ingest"
	HopCanonicalFreeze  = "canonical_freeze"
	HopCore             = "core"
	HopInsightFlow      = "insightflow"
	HopBucket           = "bucket"
	HopIntelligence     = "intelligence"
	HopReplayStore      = "replay_store"
)

// ByteEqualityResult is the oracle-side record for a single hop. Emitted by
// ValidateHop; appended to proof_logs/determinism_violation_log.jsonl on
// failure; surfaced in propagation_byte_equality_report.json for each run.
type ByteEqualityResult struct {
	Hop           string    `json:"hop"`
	SentHash      string    `json:"sent_hash"`
	AckHash       string    `json:"ack_hash"`
	BytesMatch    bool      `json:"bytes_match"`
	BytesSentSize int       `json:"bytes_sent_size"`
	BytesRecvSize int       `json:"bytes_received_size"`
	ViolationCode string    `json:"violation_code,omitempty"`
	Timestamp     time.Time `json:"timestamp"`
	TraceID       string    `json:"trace_id"`
	CorrelationID string    `json:"correlation_id"`
	DecisionID    string    `json:"decision_id,omitempty"`
	ChainBinding  string    `json:"chain_binding_hash,omitempty"`
	Detail        string    `json:"detail,omitempty"`
}

// PropagationStopError is the hard-stop signal surfaced when the byte chain
// breaks. The router's propagation loop checks for this type and aborts
// remaining in-chain hops, emitting a synthetic CHAIN_HALTED audit event
// for each skipped target.
type PropagationStopError struct {
	Code          string
	Hop           string
	TraceID       string
	CorrelationID string
	Detail        string
}

// Error returns a canonical, grep-friendly message.
func (e *PropagationStopError) Error() string {
	return fmt.Sprintf("propagation_stop hop=%s code=%s trace_id=%s detail=%s",
		e.Hop, e.Code, e.TraceID, e.Detail)
}

// IsPropagationStop returns true if err is a *PropagationStopError.
// Use this rather than type-assertions so call sites are consistent.
func IsPropagationStop(err error) bool {
	if err == nil {
		return false
	}
	_, ok := err.(*PropagationStopError)
	return ok
}

// ValidateHop checks whether the bytes the router sent match what the peer
// acknowledged. The comparison is strict byte-equality: if either hash is
// empty OR they differ, the hop is considered broken.
//
// Returns (true, result) on success.
// Returns (false, result) on any failure. The result's ViolationCode field
// is set to one of:
//
//	CodeResponseHashMismatch   — ACK received but does not match sent hash
//	CodePropagationByteMismatch — sent bytes hash differs from envelope hash
//	CodeDeterminismViolation   — catch-all for any other byte-equality break
//
// Callers convert a false result into a *PropagationStopError to unwind the
// chain.
func ValidateHop(
	hop string,
	sentBytes []byte,
	sentHash, ackHash string,
	env *PropagationEnvelope,
) (bool, ByteEqualityResult) {
	now := time.Now().UTC()
	res := ByteEqualityResult{
		Hop:           hop,
		SentHash:      sentHash,
		AckHash:       ackHash,
		BytesSentSize: len(sentBytes),
		BytesRecvSize: len(ackHash), // ack arrives as a header string; body size is irrelevant
		Timestamp:     now,
	}
	if env != nil {
		res.TraceID = env.TraceID()
		res.CorrelationID = env.CorrelationID()
		res.DecisionID = env.DecisionID()
		res.ChainBinding = env.ChainBindingHash()
	}

	// 1. Sent bytes must hash to the declared sent hash. If they don't, the
	// propagation body has been re-serialized somewhere — a critical drift.
	if sentHash == "" {
		res.BytesMatch = false
		res.ViolationCode = CodeDeterminismViolation
		res.Detail = "sent_hash is empty"
		return false, res
	}
	actualSentHash := Sha256Hex(sentBytes)
	if actualSentHash != sentHash {
		res.BytesMatch = false
		res.ViolationCode = CodePropagationByteMismatch
		res.Detail = fmt.Sprintf("sent bytes hash=%s does not match declared sent_hash=%s",
			actualSentHash, sentHash)
		return false, res
	}

	// 2. Sent bytes must equal the envelope's sealed canonical bytes. If
	// not, something between envelope seal and socket.write mutated the body.
	if env != nil && !bytes.Equal(sentBytes, env.CanonicalResponseBytes()) {
		res.BytesMatch = false
		res.ViolationCode = CodePropagationByteMismatch
		res.Detail = fmt.Sprintf("sent bytes diverge from envelope canonical bytes (env_hash=%s)",
			env.ResponseHash())
		return false, res
	}

	// 3. ACK header must echo the sent hash verbatim.
	if ackHash == "" {
		res.BytesMatch = false
		res.ViolationCode = CodeResponseHashMismatch
		res.Detail = "ack_hash header missing"
		return false, res
	}
	if ackHash != sentHash {
		res.BytesMatch = false
		res.ViolationCode = CodeResponseHashMismatch
		res.Detail = fmt.Sprintf("ack_hash=%s does not match sent_hash=%s", ackHash, sentHash)
		return false, res
	}

	res.BytesMatch = true
	return true, res
}

// ValidateChain re-derives the chain_binding_hash from the envelope's stored
// propagation chain and compares it to the stored chain_binding_hash. This
// is a superset of PropagationEnvelope.VerifySelf() — it also enforces that
// the chain has exactly four elements and that propagation_chain[3] equals
// the envelope's response_hash.
//
// Returns (true, "") on success.
// Returns (false, detail) on mismatch. The detail is safe to log.
func ValidateChain(env *PropagationEnvelope) (bool, string) {
	if env == nil {
		return false, "envelope is nil"
	}
	chain := env.PropagationChain()
	if len(chain) != 4 {
		return false, fmt.Sprintf("propagation_chain must have 4 elements, got %d", len(chain))
	}
	if chain[3] != env.ResponseHash() {
		return false, fmt.Sprintf("propagation_chain[3]=%s != response_hash=%s",
			chain[3], env.ResponseHash())
	}
	expected := Sha256Hex(CanonicalJoinChain(chain))
	if expected != env.ChainBindingHash() {
		return false, fmt.Sprintf("chain_binding_hash mismatch: expected=%s stored=%s",
			expected, env.ChainBindingHash())
	}
	return true, ""
}

// NewPropagationStopError constructs a *PropagationStopError from a failing
// ByteEqualityResult. The returned error can be checked with errors.As.
func NewPropagationStopError(res ByteEqualityResult) *PropagationStopError {
	code := res.ViolationCode
	if code == "" {
		code = CodeDeterminismViolation
	}
	return &PropagationStopError{
		Code:          code,
		Hop:           res.Hop,
		TraceID:       res.TraceID,
		CorrelationID: res.CorrelationID,
		Detail:        res.Detail,
	}
}

// --- Violation recording (JSONL, append-only) ---

// DeterminismViolationLogPath is the JSONL file that accumulates every
// ByteEqualityResult with BytesMatch == false.
const DeterminismViolationLogPath = "proof_logs/determinism_violation_log.jsonl"

var (
	violationMu   sync.Mutex
	violationFile *os.File
)

// RecordViolation appends the given result to the violation log. Safe to
// call concurrently. If the log file cannot be opened (disk full, permission
// denied), the error is returned so the caller can decide whether to abort.
//
// A passing result (BytesMatch == true) is a no-op — the log only records
// failures so a clean run produces an empty file.
func RecordViolation(res ByteEqualityResult) error {
	if res.BytesMatch {
		return nil
	}

	violationMu.Lock()
	defer violationMu.Unlock()

	if violationFile == nil {
		dir := filepath.Dir(DeterminismViolationLogPath)
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return fmt.Errorf("record_violation: mkdir %s: %w", dir, err)
		}
		f, err := os.OpenFile(DeterminismViolationLogPath,
			os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
		if err != nil {
			return fmt.Errorf("record_violation: open %s: %w", DeterminismViolationLogPath, err)
		}
		violationFile = f
	}

	line, err := json.Marshal(res)
	if err != nil {
		return fmt.Errorf("record_violation: marshal: %w", err)
	}
	line = append(line, '\n')
	if _, err := violationFile.Write(line); err != nil {
		return fmt.Errorf("record_violation: write: %w", err)
	}
	return violationFile.Sync()
}

// CloseViolationLog flushes and closes the violation log. Called at program
// exit from the main harness. Idempotent.
func CloseViolationLog() {
	violationMu.Lock()
	defer violationMu.Unlock()
	if violationFile != nil {
		_ = violationFile.Sync()
		_ = violationFile.Close()
		violationFile = nil
	}
}
