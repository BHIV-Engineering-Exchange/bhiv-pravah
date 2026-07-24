package main

// peer_receipt_replay.go — v15.9 receipt replay rejection.
//
// CSO GAP FOUND IN THE v15.9 AUDIT PASS:
//
//   Before v15.9, `/v1/downstream-ack` had no defence against an attacker
//   replaying a valid peer receipt. A receipt's Ed25519 signature is valid
//   for as long as the embedded key is valid, so:
//
//     - An attacker who intercepted ONE valid receipt could replay it
//       repeatedly to inflate Sarathi's per-peer ack counter.
//     - The ack tracker would believe it had received N successful
//       acknowledgements when in reality only one peer-side store occurred.
//     - In a strict "3 receipts to close the gate" model, the same recycled
//       receipt across all three peer names could even close the gate from
//       a single intercepted message (the peer-name impersonation issue is
//       handled separately by the pinning gate; this one is the time-shift
//       issue).
//
// FIX (v15.9): track every accepted receipt by its content-hash + peer name
// with a TTL window (default 300 s, matches the TANTRA decision replay
// window). A duplicate within the window is rejected with
// `ERR_DOWNSTREAM_RECEIPT_REPLAY` and audited.
//
// THIS STORE IS SEPARATE FROM:
//
//   - inbound_nonce_store.go     (HTTP header nonces for inbound /sarathi/enforce)
//   - tantra_replay.go           (TANTRA decision_hash + signed-payload replay)
//
// All three coexist with different key spaces and TTLs because they protect
// different surfaces.
//
// TAG: peer-receipt-replay-v15.9

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strings"
	"sync"
	"time"
)

// PeerReceiptReplayTTLSeconds is the window during which a duplicate
// receipt is rejected. Matches TantraReplayTTLSeconds for consistency.
const PeerReceiptReplayTTLSeconds = 300

// PeerReceiptReplayMaxEntries bounds the in-memory map under burst load.
const PeerReceiptReplayMaxEntries = 100_000

// PeerReceiptReplayStore is the interface VerifyReceipt's wrapper consults.
// In-memory only — receipts are short-lived and rebooting the service is
// equivalent to "the gate is open again", which is the correct posture.
type PeerReceiptReplayStore interface {
	// Check records a fresh (peer, sha256(raw_receipt_bytes)) pair.
	// Returns nil on accept; a *TantraValidationError-style error on duplicate.
	Check(peer string, rawBytes []byte, now time.Time) error
	PendingCount() int
}

// memoryPeerReceiptReplayStore is the production implementation.
type memoryPeerReceiptReplayStore struct {
	mu     sync.Mutex
	bySig  map[string]time.Time // key = peer + "|" + sha256_hex(raw)
	ttl    time.Duration
	maxLen int
}

var activePeerReceiptReplayStore PeerReceiptReplayStore

// ActivePeerReceiptReplayStore returns the boot-loaded store.
func ActivePeerReceiptReplayStore() PeerReceiptReplayStore { return activePeerReceiptReplayStore }

// SetActivePeerReceiptReplayStoreForTest replaces the active store — test only.
func SetActivePeerReceiptReplayStoreForTest(s PeerReceiptReplayStore) {
	activePeerReceiptReplayStore = s
}

// BootstrapPeerReceiptReplayStore is the boot wiring. Pure in-memory (no
// JSONL persistence — receipts are short-lived and the replay window is
// short enough that a process restart safely resets the gate).
func BootstrapPeerReceiptReplayStore() PeerReceiptReplayStore {
	s := &memoryPeerReceiptReplayStore{
		bySig:  make(map[string]time.Time),
		ttl:    time.Duration(PeerReceiptReplayTTLSeconds) * time.Second,
		maxLen: PeerReceiptReplayMaxEntries,
	}
	activePeerReceiptReplayStore = s
	return s
}

// Check enforces the replay window. Key: peer || "|" || sha256(raw).
// A different peer claiming the same bytes is a separate key — that's
// already a cross-peer impersonation attempt and the pinning gate would
// have rejected it, but the separate-key choice makes the audit cleaner.
func (s *memoryPeerReceiptReplayStore) Check(peer string, rawBytes []byte, now time.Time) error {
	if len(rawBytes) == 0 {
		return fmt.Errorf("peer_receipt_replay: empty body")
	}
	sum := sha256.Sum256(rawBytes)
	key := strings.TrimSpace(peer) + "|" + hex.EncodeToString(sum[:])

	s.mu.Lock()
	defer s.mu.Unlock()

	// Lazy GC every ~256 inserts.
	if len(s.bySig) > 0 && len(s.bySig)%256 == 0 {
		cutoff := now.Add(-s.ttl)
		for k, t := range s.bySig {
			if t.Before(cutoff) {
				delete(s.bySig, k)
			}
		}
	}

	if first, seen := s.bySig[key]; seen && now.Sub(first) <= s.ttl {
		return fmt.Errorf(
			"peer_receipt_replay: peer=%s receipt sha256=%s first seen at %s (window=%ds)",
			peer, hex.EncodeToString(sum[:])[:16], first.Format(time.RFC3339Nano),
			PeerReceiptReplayTTLSeconds,
		)
	}

	// Bounded eviction.
	if len(s.bySig) >= s.maxLen {
		oldestKey := ""
		oldest := now
		for k, t := range s.bySig {
			if t.Before(oldest) {
				oldest = t
				oldestKey = k
			}
		}
		if oldestKey != "" {
			delete(s.bySig, oldestKey)
		}
	}

	s.bySig[key] = now
	return nil
}

func (s *memoryPeerReceiptReplayStore) PendingCount() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return len(s.bySig)
}
