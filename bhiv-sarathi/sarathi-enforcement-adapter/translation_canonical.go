package main

// translation_canonical.go — v15.5 Sovereign Translational Layer.
//
// Helper primitives shared by every translation builder. All hashing flows
// through CanonicalMarshal (RFC 8785) so producer and verifier agree on a
// single byte representation regardless of map iteration order.
//
// TAG: translation-layer

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// CanonicalHashOfStruct marshals v through CanonicalMarshal (RFC 8785-style
// canonical JSON, sorted keys, no whitespace) and returns hex sha256. This is
// the ONE deterministic content-addressing primitive used across the
// translation layer.
func CanonicalHashOfStruct(v interface{}) (string, error) {
	data, err := CanonicalMarshal(v)
	if err != nil {
		return "", fmt.Errorf("canonical_hash: marshal: %w", err)
	}
	h := sha256.Sum256(data)
	return hex.EncodeToString(h[:]), nil
}

// ComputePayloadHashHex returns hex sha256 of the raw bytes. Wraps Sha256Hex
// from policy_store.go with a translation-prefixed name for clarity in call
// sites that mix multiple hash purposes.
func ComputePayloadHashHex(b []byte) string {
	return Sha256Hex(b)
}

// ============================================================================
// Per-trace hop counter (drives InsightFlow Schema C event_sequence/hop_count)
// ============================================================================

// hopCounterStore tracks an in-memory monotonic counter per trace_id. Counter
// state is durable via live/translation/hop_count/{trace_id}.json so a service
// restart does not reset event_sequence mid-trace.
type hopCounterStore struct {
	mu       sync.Mutex
	rootDir  string
}

var globalHopCounter = newHopCounterStore("live/translation/hop_count")

// newHopCounterStore creates a hop counter rooted at dir.
func newHopCounterStore(dir string) *hopCounterStore {
	return &hopCounterStore{rootDir: dir}
}

// Next returns the next event_sequence for the given trace_id. First call for
// a fresh trace returns 1. Subsequent calls return monotonically increasing
// integers. Persisted to disk before return so a crash mid-fan-out cannot
// re-issue a sequence number.
func (s *hopCounterStore) Next(traceID string) (int, error) {
	if traceID == "" {
		return 0, fmt.Errorf("hop_counter: trace_id is empty")
	}
	s.mu.Lock()
	defer s.mu.Unlock()

	if err := os.MkdirAll(s.rootDir, 0o755); err != nil {
		return 0, fmt.Errorf("hop_counter: mkdir: %w", err)
	}
	path := filepath.Join(s.rootDir, safeForFilename(traceID)+".json")

	current := 0
	if data, err := os.ReadFile(path); err == nil {
		// Read deliberately tolerant: any decode error treats as fresh.
		var snap hopCounterSnapshot
		if e := unmarshalHopCounter(data, &snap); e == nil {
			current = snap.Count
		}
	}
	current++

	snap := hopCounterSnapshot{
		TraceID:   traceID,
		Count:     current,
		UpdatedAt: time.Now().UTC().Format(time.RFC3339Nano),
	}
	out, err := CanonicalMarshal(snap)
	if err != nil {
		return 0, fmt.Errorf("hop_counter: marshal: %w", err)
	}
	if err := atomicWriteFile(path, out, 0o644); err != nil {
		return 0, fmt.Errorf("hop_counter: write: %w", err)
	}
	return current, nil
}

// Peek returns the current hop count without advancing it. Used by Schema D
// builders to report the same hop count Schema C just advanced through.
func (s *hopCounterStore) Peek(traceID string) int {
	if traceID == "" {
		return 0
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	path := filepath.Join(s.rootDir, safeForFilename(traceID)+".json")
	data, err := os.ReadFile(path)
	if err != nil {
		return 0
	}
	var snap hopCounterSnapshot
	if e := unmarshalHopCounter(data, &snap); e != nil {
		return 0
	}
	return snap.Count
}

type hopCounterSnapshot struct {
	TraceID   string `json:"trace_id"`
	Count     int    `json:"count"`
	UpdatedAt string `json:"updated_at"`
}

// unmarshalHopCounter is a thin wrapper kept so callers do not import
// encoding/json directly. Tolerates RFC 8785 canonical bytes.
func unmarshalHopCounter(data []byte, snap *hopCounterSnapshot) error {
	return jsonUnmarshalStrict(data, snap)
}

// ============================================================================
// File-system primitives (atomic write, safe filenames)
// ============================================================================

// atomicWriteFile writes b to path atomically: tmp + fsync + rename. Caller
// holds the surrounding mutex / flock. mode is honoured on the rename target.
func atomicWriteFile(path string, b []byte, mode os.FileMode) error {
	if dir := filepath.Dir(path); dir != "" && dir != "." {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return err
		}
	}
	tmp := path + ".tmp"
	f, err := os.OpenFile(tmp, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, mode)
	if err != nil {
		return err
	}
	if _, err := f.Write(b); err != nil {
		_ = f.Close()
		_ = os.Remove(tmp)
		return err
	}
	if err := f.Sync(); err != nil {
		_ = f.Close()
		_ = os.Remove(tmp)
		return err
	}
	if err := f.Close(); err != nil {
		_ = os.Remove(tmp)
		return err
	}
	return os.Rename(tmp, path)
}

// safeForFilename strips characters that are illegal on Windows or unsafe on
// POSIX from a string so it can be used as a filename. Hex/UUID trace_ids
// pass through untouched; defensive only.
func safeForFilename(s string) string {
	out := make([]byte, 0, len(s))
	for i := 0; i < len(s); i++ {
		c := s[i]
		switch {
		case c >= 'a' && c <= 'z':
			out = append(out, c)
		case c >= 'A' && c <= 'Z':
			out = append(out, c)
		case c >= '0' && c <= '9':
			out = append(out, c)
		case c == '-' || c == '_':
			out = append(out, c)
		default:
			out = append(out, '_')
		}
	}
	if len(out) == 0 {
		return "_empty_"
	}
	if len(out) > 100 {
		out = out[:100]
	}
	return string(out)
}

// jsonUnmarshalStrict is a thin indirection so we can swap to a strict
// decoder if the project later adopts one. Currently a direct
// encoding/json.Unmarshal — the translation layer never round-trips
// untrusted bytes through it; only its own snapshots.
func jsonUnmarshalStrict(data []byte, v interface{}) error {
	return json.Unmarshal(data, v)
}

// PrecreateTranslationDirs creates the translation + proof-log directory
// scaffold so the first enforcement event does not race to mkdir. Safe to
// call multiple times; mkdir-with-already-exists is a no-op.
//
// v15.7: also creates the TANTRA-specific proof-log paths.
func PrecreateTranslationDirs() {
	dirs := []string{
		"live/translation",
		"live/translation/hop_count",
		"live/keys",
		"proof_logs",
	}
	for _, d := range dirs {
		_ = os.MkdirAll(d, 0o755)
	}
}

// ============================================================================
// Trust snapshot side-channel: api_key_fingerprint lookup
// ============================================================================

// trustSnapshotAPIKeyFingerprint returns the registered sha256 fingerprint of
// the API key for evaluatorID, or "" if no fingerprint is registered (legacy
// snapshot rows without the field). Reads SARATHI_TRUST_SNAPSHOT or the
// default path on each call — the snapshot is small and read-cheap.
//
// Returning "" is interpreted by callers as "no fingerprint check
// configured" (caller-key fallback applies). Returning a non-empty value
// requires a constant-time match against sha256(provided_api_key).
func trustSnapshotAPIKeyFingerprint(evaluatorID string) string {
	path := os.Getenv("SARATHI_TRUST_SNAPSHOT")
	if path == "" {
		path = "./live/trust_snapshot.json"
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	var snap TrustSnapshotFile
	if e := json.Unmarshal(data, &snap); e != nil {
		return ""
	}
	for _, e := range snap.Evaluators {
		if e.EvaluatorID == evaluatorID {
			return e.APIKeyFingerprint
		}
	}
	return ""
}
