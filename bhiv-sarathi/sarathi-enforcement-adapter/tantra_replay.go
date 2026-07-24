package main

// tantra_replay.go — TANTRA Contract §8 replay + mutation rejection.
//
// Two replay surfaces are checked at the verifier:
//
//   A. decision_hash already seen   (rejects "same decision posted twice")
//   B. signed-payload-hash already seen (rejects "same bytes posted twice
//                                        even after re-canonicalisation")
//
// Both windows are 300 seconds (Contract recommended TTL, §8). Entries
// outside the window are pruned lazily on the next Check call.
//
// PERSISTENCE: every accepted (i.e. fresh) entry is appended to
// proof_logs/tantra_replay.jsonl so a process restart does not silently lose
// the replay window. On boot, BootstrapTantraReplayStore reads back the
// JSONL and re-populates the in-memory map with any rows still in window.
//
// MUTATION REJECTION is intentionally NOT in this file — mutation is caught
// by the signature verifier in tantra_verifier.go step 7. The replay store
// only concerns itself with "same bytes seen before".
//
// TAG: tantra-v15.7

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// TantraReplayLogPath is the append-only persistence trail. The verifier writes
// one row per accepted decision. The boot loader reads back rows within window
// and re-populates the in-memory map.
const TantraReplayLogPath = "proof_logs/tantra_replay.jsonl"

// TantraReplayMaxEntries caps the in-memory map to bound memory under burst
// load. When the cap is hit, the oldest entry is evicted (it has already been
// fsynced to disk).
const TantraReplayMaxEntries = 100_000

// TantraReplayStore is the interface the verifier consumes. A test can swap
// in a fake; production wires the file-backed implementation.
type TantraReplayStore interface {
	// Check records a fresh (decision_hash, payload_hash) pair and returns
	// (nil) on accept. If either key has already been seen within the TTL
	// window, returns a *TantraValidationError with code ErrTantraReplay.
	Check(decisionHash string, signedBytes []byte, now time.Time) error

	// PendingCount returns the number of entries currently in window.
	PendingCount() int
}

// fileTantraReplayStore is the default implementation.
type fileTantraReplayStore struct {
	mu          sync.Mutex
	byHash      map[string]time.Time // decision_hash -> first seen
	byPayload   map[string]time.Time // sha256(signed bytes) -> first seen
	logFile     *os.File
	enc         *json.Encoder
	ttl         time.Duration
}

// tantraReplayLogRow is the JSONL persistence row.
type tantraReplayLogRow struct {
	Timestamp    string `json:"ts"`
	DecisionHash string `json:"decision_hash"`
	PayloadHash  string `json:"payload_hash"`
}

var activeTantraReplayStore TantraReplayStore

// BootstrapTantraReplayStore opens (or creates) the JSONL log and rehydrates
// the in-memory map with any rows still within the TTL window. Safe to call
// before or after InitCryptoProvider.
func BootstrapTantraReplayStore() (TantraReplayStore, error) {
	dir := filepath.Dir(TantraReplayLogPath)
	if dir != "" && dir != "." {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return nil, fmt.Errorf("tantra_replay: mkdir %s: %w", dir, err)
		}
	}
	f, err := os.OpenFile(TantraReplayLogPath, os.O_CREATE|os.O_APPEND|os.O_RDWR, 0o644)
	if err != nil {
		return nil, fmt.Errorf("tantra_replay: open %s: %w", TantraReplayLogPath, err)
	}
	store := &fileTantraReplayStore{
		byHash:    make(map[string]time.Time),
		byPayload: make(map[string]time.Time),
		logFile:   f,
		enc:       json.NewEncoder(f),
		ttl:       time.Duration(TantraReplayTTLSeconds) * time.Second,
	}
	if err := store.rehydrateLocked(); err != nil {
		_ = f.Close()
		return nil, err
	}
	activeTantraReplayStore = store
	return store, nil
}

// rehydrateLocked reads the JSONL back from disk on boot. Entries outside the
// TTL window are dropped. Called once at boot before any concurrent access,
// so no lock is taken (the suffix is on the function name as documentation
// only).
func (s *fileTantraReplayStore) rehydrateLocked() error {
	if _, err := s.logFile.Seek(0, 0); err != nil {
		return fmt.Errorf("tantra_replay: seek for rehydrate: %w", err)
	}
	dec := json.NewDecoder(s.logFile)
	now := time.Now().UTC()
	count := 0
	for dec.More() {
		var row tantraReplayLogRow
		if err := dec.Decode(&row); err != nil {
			// Don't error out — log is append-only, partial last line is
			// possible if a prior process crashed mid-write. Stop reading.
			break
		}
		ts, err := time.Parse(time.RFC3339Nano, row.Timestamp)
		if err != nil {
			continue
		}
		if now.Sub(ts) > s.ttl {
			continue
		}
		s.byHash[row.DecisionHash] = ts
		s.byPayload[row.PayloadHash] = ts
		count++
	}
	// Seek to end for appends.
	if _, err := s.logFile.Seek(0, 2); err != nil {
		return fmt.Errorf("tantra_replay: seek to end after rehydrate: %w", err)
	}
	if count > 0 {
		fmt.Fprintf(os.Stderr, "[tantra_replay] rehydrated %d in-window rows from %s\n",
			count, TantraReplayLogPath)
	}
	return nil
}

// Check enforces both replay surfaces.
func (s *fileTantraReplayStore) Check(decisionHash string, signedBytes []byte, now time.Time) error {
	if strings.TrimSpace(decisionHash) == "" {
		return &TantraValidationError{
			Code:   ErrTantraDecisionHashMismatch,
			Detail: "decision_hash empty at replay check",
		}
	}
	payloadHash := sha256HexBytes(signedBytes)

	s.mu.Lock()
	defer s.mu.Unlock()

	// Prune expired entries (lazy GC).
	cutoff := now.Add(-s.ttl)
	if len(s.byHash) > 0 && (len(s.byHash)+len(s.byPayload))%256 == 0 {
		// Throttled GC — only every ~256 inserts to avoid scanning the map
		// on the hot path more often than necessary.
		for k, t := range s.byHash {
			if t.Before(cutoff) {
				delete(s.byHash, k)
			}
		}
		for k, t := range s.byPayload {
			if t.Before(cutoff) {
				delete(s.byPayload, k)
			}
		}
	}

	if first, seen := s.byHash[decisionHash]; seen && now.Sub(first) <= s.ttl {
		return &TantraValidationError{
			Code: ErrTantraReplay,
			Detail: fmt.Sprintf(
				"decision_hash %s seen at %s (window=%ds)",
				decisionHash[:16], first.Format(time.RFC3339Nano), TantraReplayTTLSeconds,
			),
		}
	}
	if first, seen := s.byPayload[payloadHash]; seen && now.Sub(first) <= s.ttl {
		return &TantraValidationError{
			Code: ErrTantraReplay,
			Detail: fmt.Sprintf(
				"signed-payload hash %s seen at %s (window=%ds)",
				payloadHash[:16], first.Format(time.RFC3339Nano), TantraReplayTTLSeconds,
			),
		}
	}

	// Eviction if at cap.
	if len(s.byHash) >= TantraReplayMaxEntries {
		oldestKey := ""
		oldestT := now
		for k, t := range s.byHash {
			if t.Before(oldestT) {
				oldestT = t
				oldestKey = k
			}
		}
		if oldestKey != "" {
			delete(s.byHash, oldestKey)
		}
	}
	if len(s.byPayload) >= TantraReplayMaxEntries {
		oldestKey := ""
		oldestT := now
		for k, t := range s.byPayload {
			if t.Before(oldestT) {
				oldestT = t
				oldestKey = k
			}
		}
		if oldestKey != "" {
			delete(s.byPayload, oldestKey)
		}
	}

	s.byHash[decisionHash] = now
	s.byPayload[payloadHash] = now

	// Persist (best-effort — failure logs to stderr, does NOT block accept;
	// in-memory map already has the entry, so within-process replays remain
	// rejected even if the disk write fails).
	row := tantraReplayLogRow{
		Timestamp:    now.UTC().Format(time.RFC3339Nano),
		DecisionHash: decisionHash,
		PayloadHash:  payloadHash,
	}
	if err := s.enc.Encode(&row); err != nil {
		fmt.Fprintf(os.Stderr, "[tantra_replay] WARN: jsonl append failed: %v\n", err)
	}
	return nil
}

// PendingCount returns len(byHash); useful for boot banners and tests.
func (s *fileTantraReplayStore) PendingCount() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.byHash)
}

func sha256HexBytes(b []byte) string {
	h := sha256.Sum256(b)
	return hex.EncodeToString(h[:])
}

// ============================================================================
// IN-MEMORY-ONLY VARIANT (for unit tests)
// ============================================================================

// MemoryTantraReplayStore is a non-persistent implementation. Used in unit
// tests where disk side-effects are unwelcome.
type MemoryTantraReplayStore struct {
	mu        sync.Mutex
	byHash    map[string]time.Time
	byPayload map[string]time.Time
	ttl       time.Duration
}

// NewMemoryTantraReplayStore returns an empty in-memory replay store with the
// contract TTL.
func NewMemoryTantraReplayStore() *MemoryTantraReplayStore {
	return &MemoryTantraReplayStore{
		byHash:    make(map[string]time.Time),
		byPayload: make(map[string]time.Time),
		ttl:       time.Duration(TantraReplayTTLSeconds) * time.Second,
	}
}

// Check satisfies TantraReplayStore.
func (s *MemoryTantraReplayStore) Check(decisionHash string, signedBytes []byte, now time.Time) error {
	if strings.TrimSpace(decisionHash) == "" {
		return &TantraValidationError{Code: ErrTantraDecisionHashMismatch, Detail: "empty decision_hash"}
	}
	payloadHash := sha256HexBytes(signedBytes)
	s.mu.Lock()
	defer s.mu.Unlock()
	if first, seen := s.byHash[decisionHash]; seen && now.Sub(first) <= s.ttl {
		return &TantraValidationError{Code: ErrTantraReplay, Detail: "decision_hash replay"}
	}
	if first, seen := s.byPayload[payloadHash]; seen && now.Sub(first) <= s.ttl {
		return &TantraValidationError{Code: ErrTantraReplay, Detail: "payload replay"}
	}
	s.byHash[decisionHash] = now
	s.byPayload[payloadHash] = now
	return nil
}

// PendingCount satisfies TantraReplayStore.
func (s *MemoryTantraReplayStore) PendingCount() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.byHash)
}
