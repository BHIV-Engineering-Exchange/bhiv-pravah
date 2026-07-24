package main

// inbound_nonce_store.go — v15.0 Sovereign Identity Closure.
//
// Bounded LRU nonce store for inbound caller request replay protection. Each
// accepted request presents X-Sarathi-Request-Nonce which must be unique
// within SARATHI_NONCE_WINDOW_S seconds. This file provides that uniqueness
// check without growing unbounded in memory.
//
// Design:
//   - Fixed-capacity in-memory LRU (SARATHI_NONCE_LRU_SIZE, default 100k).
//   - TTL trim: entries older than the window are lazily evicted on every Seen
//     call so the active set stays bounded even if capacity is far from full.
//   - Evicted entries are appended to live/inbound_nonces.jsonl so a forensic
//     log of every accepted nonce survives restart. The file is fsync'd on
//     every append for durability (cost is ~1 write per accepted request —
//     acceptable for governance boundary traffic).
//
// Safety:
//   - The store is the authoritative answer for "have we seen this nonce?"
//     NEVER derive nonce uniqueness from memory alone without the TTL trim —
//     a stale in-memory hit past the window is a false positive (replay
//     should already be out of scope).
//   - Seen() returns (alreadySeen, firstSeenAt). The middleware uses this to
//     short-circuit to ERR_INBOUND_NONCE_REPLAY before signature verification.
//   - This file does NOT own the timestamp skew check — that is enforced
//     before the nonce lookup, so the Seen cache is bounded by the skew
//     window, not by caller patience.
//
// This store is OFF the hot path when SARATHI_INBOUND_AUTH=off because the
// inbound-auth middleware is not even mounted in that mode.

import (
	"container/list"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// InboundNonceStore is a bounded LRU with TTL trim and optional disk overflow.
type InboundNonceStore struct {
	mu       sync.Mutex
	capacity int
	window   time.Duration
	entries  map[string]*list.Element
	order    *list.List
	sink     *os.File
	sinkPath string
	clock    Clock
}

// inboundNonceEntry is what the LRU element value carries.
type inboundNonceEntry struct {
	nonce    string
	firstAt  time.Time
	issuerID string
}

// NewInboundNonceStore constructs the store. If overflowPath is non-empty the
// store appends evicted-or-accepted entries to that JSONL file (fsync on
// append). A zero capacity defaults to 100k; a zero window defaults to 900s.
func NewInboundNonceStore(capacity int, window time.Duration, overflowPath string) (*InboundNonceStore, error) {
	if capacity <= 0 {
		capacity = 100_000
	}
	if window <= 0 {
		window = 15 * time.Minute
	}

	var sink *os.File
	if overflowPath != "" {
		if dir := filepath.Dir(overflowPath); dir != "" && dir != "." {
			if err := os.MkdirAll(dir, 0o755); err != nil {
				return nil, fmt.Errorf("inbound nonce overflow dir: %w", err)
			}
		}
		f, err := os.OpenFile(overflowPath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
		if err != nil {
			return nil, fmt.Errorf("inbound nonce overflow file: %w", err)
		}
		sink = f
	}

	return &InboundNonceStore{
		capacity: capacity,
		window:   window,
		entries:  make(map[string]*list.Element, capacity),
		order:    list.New(),
		sink:     sink,
		sinkPath: overflowPath,
		clock:    RealClock{},
	}, nil
}

// SetClock lets tests drive the TTL trim deterministically.
func (s *InboundNonceStore) SetClock(c Clock) {
	if c == nil {
		return
	}
	s.mu.Lock()
	s.clock = c
	s.mu.Unlock()
}

// Seen returns (alreadySeen, firstSeenAt).
//
//   - alreadySeen=true  → the middleware MUST reject with ERR_INBOUND_NONCE_REPLAY.
//   - alreadySeen=false → the nonce has been recorded. The caller is responsible
//     for only reaching this point after timestamp-skew and signature checks
//     have passed (we do not want to record nonces for invalid requests).
//
// The store drops expired entries lazily. Callers never need to call a
// separate Trim method.
func (s *InboundNonceStore) Seen(nonce, issuerID string) (bool, time.Time) {
	if nonce == "" {
		return false, time.Time{}
	}
	s.mu.Lock()
	defer s.mu.Unlock()

	now := s.now()
	s.trimExpiredLocked(now)

	if el, ok := s.entries[nonce]; ok {
		entry := el.Value.(*inboundNonceEntry)
		return true, entry.firstAt
	}
	s.insertLocked(nonce, issuerID, now)
	return false, time.Time{}
}

// Size returns the current entry count (for metrics / tests).
func (s *InboundNonceStore) Size() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.order.Len()
}

// Close flushes and closes the overflow file, if any.
func (s *InboundNonceStore) Close() error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.sink != nil {
		_ = s.sink.Sync()
		err := s.sink.Close()
		s.sink = nil
		return err
	}
	return nil
}

// ----- internals -----

func (s *InboundNonceStore) now() time.Time {
	if s.clock != nil {
		return s.clock.NowUTC()
	}
	return time.Now().UTC()
}

func (s *InboundNonceStore) trimExpiredLocked(now time.Time) {
	cutoff := now.Add(-s.window)
	for {
		el := s.order.Back()
		if el == nil {
			return
		}
		entry := el.Value.(*inboundNonceEntry)
		if entry.firstAt.After(cutoff) {
			return
		}
		s.order.Remove(el)
		delete(s.entries, entry.nonce)
	}
}

func (s *InboundNonceStore) insertLocked(nonce, issuerID string, now time.Time) {
	entry := &inboundNonceEntry{nonce: nonce, firstAt: now, issuerID: issuerID}
	el := s.order.PushFront(entry)
	s.entries[nonce] = el

	// Capacity eviction: fall back to LRU (oldest at back).
	for s.order.Len() > s.capacity {
		old := s.order.Back()
		if old == nil {
			break
		}
		oldEntry := old.Value.(*inboundNonceEntry)
		s.order.Remove(old)
		delete(s.entries, oldEntry.nonce)
	}

	// Forensic overflow append. Best-effort — a failing disk must not block
	// the request, so we log and continue rather than propagate the error.
	if s.sink != nil {
		line, err := json.Marshal(map[string]string{
			"ts":        now.UTC().Format(time.RFC3339Nano),
			"nonce":     nonce,
			"issuer_id": issuerID,
		})
		if err == nil {
			line = append(line, '\n')
			if _, werr := s.sink.Write(line); werr == nil {
				_ = s.sink.Sync()
			} else {
				fmt.Printf("[InboundNonceStore] overflow write failed: %v\n", werr)
			}
		}
	}
}
