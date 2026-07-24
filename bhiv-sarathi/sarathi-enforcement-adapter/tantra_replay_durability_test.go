package main

// tantra_replay_durability_test.go — proves replay-verification continuity
// across a process restart, and that the TTL window is honoured on rehydrate.
//
// These are the durability properties an integration owner verifies for the
// convergence chain: a decision accepted before a restart is still rejected as
// a replay after the restart (within the window), and stale rows do not cause
// false-positive replays after rehydrate.
//
// TAG: tantra-convergence-v1

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"
)

// newFileReplayStoreAt builds a file-backed replay store at an explicit path
// and rehydrates it — exactly what the boot path does, but isolated to a temp
// file so the test never touches the live proof log.
func newFileReplayStoreAt(t *testing.T, path string) *fileTantraReplayStore {
	t.Helper()
	f, err := os.OpenFile(path, os.O_CREATE|os.O_APPEND|os.O_RDWR, 0o644)
	if err != nil {
		t.Fatalf("open replay file: %v", err)
	}
	s := &fileTantraReplayStore{
		byHash:    make(map[string]time.Time),
		byPayload: make(map[string]time.Time),
		logFile:   f,
		enc:       json.NewEncoder(f),
		ttl:       time.Duration(TantraReplayTTLSeconds) * time.Second,
	}
	if err := s.rehydrateLocked(); err != nil {
		t.Fatalf("rehydrate: %v", err)
	}
	return s
}

func TestTantraReplay_ContinuityAfterRestart(t *testing.T) {
	path := filepath.Join(t.TempDir(), "replay.jsonl")
	now := time.Now().UTC()
	const decisionHash = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
	signed := []byte(`{"trace_id":"trace-tantra-001","input_hash":"x"}`)

	// --- before restart: record the decision ---
	s1 := newFileReplayStoreAt(t, path)
	if err := s1.Check(decisionHash, signed, now); err != nil {
		t.Fatalf("first Check should accept: %v", err)
	}
	_ = s1.logFile.Sync()
	_ = s1.logFile.Close()

	// --- restart: a brand-new store rehydrates from the same JSONL ---
	s2 := newFileReplayStoreAt(t, path)
	if s2.PendingCount() < 1 {
		t.Fatalf("rehydrate dropped the in-window row: pending=%d", s2.PendingCount())
	}

	// The same decision MUST now be rejected as a replay — continuity held.
	err := s2.Check(decisionHash, signed, now.Add(2*time.Second))
	if err == nil {
		t.Fatal("replay NOT rejected after restart — durability continuity broken")
	}
	tve, ok := err.(*TantraValidationError)
	if !ok || tve.Code != ErrTantraReplay {
		t.Fatalf("want ErrTantraReplay after restart, got %v", err)
	}
	_ = s2.logFile.Close()
}

func TestTantraReplay_ExpiredRowsDroppedOnRehydrate(t *testing.T) {
	path := filepath.Join(t.TempDir(), "replay.jsonl")
	now := time.Now().UTC()
	const decisionHash = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
	payloadHash := sha256HexBytes([]byte("stale-signed-bytes"))

	// Write a row whose timestamp is OUTSIDE the TTL window (stale).
	stale := tantraReplayLogRow{
		Timestamp:    now.Add(-time.Duration(TantraReplayTTLSeconds+120) * time.Second).Format(time.RFC3339Nano),
		DecisionHash: decisionHash,
		PayloadHash:  payloadHash,
	}
	raw, _ := json.Marshal(&stale)
	if err := os.WriteFile(path, append(raw, '\n'), 0o644); err != nil {
		t.Fatalf("seed stale row: %v", err)
	}

	// Rehydrate: the stale row must be dropped (not loaded into the window).
	s := newFileReplayStoreAt(t, path)
	if s.PendingCount() != 0 {
		t.Fatalf("stale row was not dropped on rehydrate: pending=%d", s.PendingCount())
	}
	// A fresh decision with the same hash must therefore be ACCEPTED (no
	// false-positive replay from a stale entry).
	if err := s.Check(decisionHash, []byte("stale-signed-bytes"), now); err != nil {
		t.Fatalf("stale-hash decision should be accepted post-rehydrate, got: %v", err)
	}
	_ = s.logFile.Close()
}
