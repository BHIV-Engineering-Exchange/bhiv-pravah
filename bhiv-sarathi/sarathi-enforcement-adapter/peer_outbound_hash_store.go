package main

// peer_outbound_hash_store.go — v15.12 dual-hash transport-integrity store.
//
// PURPOSE:
//
//   Sarathi sends each peer (Bucket, InsightFlow, Core) a peer-shaped wrapper
//   whose body bytes are NOT byte-identical to the canonical 20-field response
//   that response_hash is computed over. Per task.md, peers must verify TWO
//   distinct hashes when posting back a callback receipt:
//
//     received_body_hash    == Sarathi-minted body_hash[decision_id, peer]
//                              (transport integrity — proves the wrapper bytes
//                               Sarathi sent are byte-identical to the wrapper
//                               bytes the peer received)
//
//     observed_response_hash == Sarathi's minted response_hash
//                              (decision integrity — peer extracted the
//                               embedded 20-field canonical response from the
//                               wrapper, hashed it, must equal what Sarathi
//                               sealed)
//
//   Both must pass; either failure halts the per-execution gate fail-closed.
//
// THIS STORE owns the minted body_hash value per (decision_id, peer) tuple
// so VerifyReceipt can look it up when the receipt arrives.
//
// PERSISTENCE:
//
//   In-memory map for fast O(1) lookup at receipt time.
//   JSONL append-only persistence at proof_logs/peer_outbound_hashes.jsonl
//   for boot rehydration and out-of-process audit.
//
// TTL:
//
//   1 hour default — receipts must arrive within the ack window
//   (SARATHI_DOWNSTREAM_ACK_TIMEOUT_S, default 300 s). The 1-hour
//   in-memory window gives generous slack for slow peers.
//
// TAG: dual-hash-v15.12

import (
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// encodeCanonicalResponseB64 returns the standard-base64 encoding of the
// canonical 20-field response bytes. Embedded into peer-shaped wrappers
// (BucketArtifactPayload.CanonicalResponseB64,
// InsightFlowSchemaD.CanonicalResponseB64) so peers can extract, decode,
// and SHA-256 the result to recompute observed_response_hash.
//
// Standard base64 (not URL-safe-no-pad) keeps consistency with how external
// auditors typically decode embedded byte blobs.
func encodeCanonicalResponseB64(canonical []byte) string {
	if len(canonical) == 0 {
		return ""
	}
	return base64.StdEncoding.EncodeToString(canonical)
}

// decodeCanonicalResponseB64 is the inverse — used by audit scripts that
// want to recompute response_hash from the embedded blob.
func decodeCanonicalResponseB64(s string) ([]byte, error) {
	clean := strings.TrimSpace(s)
	if clean == "" {
		return nil, fmt.Errorf("encodeCanonicalResponseB64: empty input")
	}
	return base64.StdEncoding.DecodeString(clean)
}

// computeBodyHash returns hex SHA-256 of the raw wire body bytes. Used by
// Sarathi to mint body_hash before sending, and conceptually equivalent to
// what every peer computes on receipt.
func computeBodyHash(body []byte) string {
	h := sha256.Sum256(body)
	return hex.EncodeToString(h[:])
}

// PeerOutboundHashLog is the append-only audit trail of outbound body hashes.
const PeerOutboundHashLog = "proof_logs/peer_outbound_hashes.jsonl"

// PeerOutboundHashTTL is the in-memory retention window.
const PeerOutboundHashTTL = 1 * time.Hour

// PeerOutboundHashMaxEntries bounds the in-memory map.
const PeerOutboundHashMaxEntries = 50_000

// OutboundHashEntry is one stored row.
type OutboundHashEntry struct {
	DecisionID   string    `json:"decision_id"`
	Peer         string    `json:"peer"`
	TraceID      string    `json:"trace_id"`
	ResponseHash string    `json:"response_hash"`
	BodyHash     string    `json:"body_hash"`
	BodyBytes    int       `json:"body_bytes"`
	WrapperSchema string   `json:"wrapper_schema"`
	SentAt       time.Time `json:"sent_at"`
}

// PeerOutboundHashStore is the in-memory + JSONL store.
type PeerOutboundHashStore struct {
	mu       sync.RWMutex
	byKey    map[string]*OutboundHashEntry // key = decision_id + "|" + peer
	ttl      time.Duration
	maxLen   int
}

var activePeerOutboundHashStore *PeerOutboundHashStore

// ActivePeerOutboundHashStore returns the boot-loaded store; nil if not booted.
func ActivePeerOutboundHashStore() *PeerOutboundHashStore { return activePeerOutboundHashStore }

// SetActivePeerOutboundHashStoreForTest replaces the active store (test only).
func SetActivePeerOutboundHashStoreForTest(s *PeerOutboundHashStore) {
	activePeerOutboundHashStore = s
}

// BootstrapPeerOutboundHashStore initialises the store and rehydrates any
// recent rows from the JSONL log on disk.
func BootstrapPeerOutboundHashStore() *PeerOutboundHashStore {
	s := &PeerOutboundHashStore{
		byKey:  make(map[string]*OutboundHashEntry),
		ttl:    PeerOutboundHashTTL,
		maxLen: PeerOutboundHashMaxEntries,
	}
	s.rehydrate()
	activePeerOutboundHashStore = s
	return s
}

// rehydrate reads the JSONL log on boot. Drops entries older than TTL.
func (s *PeerOutboundHashStore) rehydrate() {
	f, err := os.Open(PeerOutboundHashLog)
	if err != nil {
		return // missing file is fine
	}
	defer f.Close()
	dec := json.NewDecoder(f)
	now := time.Now().UTC()
	count := 0
	for dec.More() {
		var row OutboundHashEntry
		if err := dec.Decode(&row); err != nil {
			break
		}
		if now.Sub(row.SentAt) > s.ttl {
			continue
		}
		key := row.DecisionID + "|" + row.Peer
		s.byKey[key] = &row
		count++
	}
	if count > 0 {
		fmt.Fprintf(os.Stderr, "[peer_outbound_hash_store] rehydrated %d entries from %s\n",
			count, PeerOutboundHashLog)
	}
}

// Record stores the (decision_id, peer) outbound body hash + response_hash
// and appends a JSONL row. Best-effort persistence — in-memory map is
// authoritative for the receipt-verification path.
func (s *PeerOutboundHashStore) Record(entry OutboundHashEntry) {
	if s == nil {
		return
	}
	if strings.TrimSpace(entry.DecisionID) == "" || strings.TrimSpace(entry.Peer) == "" {
		return
	}
	if entry.SentAt.IsZero() {
		entry.SentAt = time.Now().UTC()
	}
	key := entry.DecisionID + "|" + entry.Peer

	s.mu.Lock()
	// Lazy GC every ~256 inserts.
	if len(s.byKey) > 0 && len(s.byKey)%256 == 0 {
		cutoff := time.Now().Add(-s.ttl)
		for k, e := range s.byKey {
			if e.SentAt.Before(cutoff) {
				delete(s.byKey, k)
			}
		}
	}
	// Eviction if over cap.
	if len(s.byKey) >= s.maxLen {
		oldestKey := ""
		oldestT := time.Now()
		for k, e := range s.byKey {
			if e.SentAt.Before(oldestT) {
				oldestT = e.SentAt
				oldestKey = k
			}
		}
		if oldestKey != "" {
			delete(s.byKey, oldestKey)
		}
	}
	cp := entry
	s.byKey[key] = &cp
	s.mu.Unlock()

	// Append to JSONL (best-effort).
	dir := filepath.Dir(PeerOutboundHashLog)
	if dir != "" && dir != "." {
		_ = os.MkdirAll(dir, 0o755)
	}
	raw, err := json.Marshal(&entry)
	if err != nil {
		return
	}
	raw = append(raw, '\n')
	f, err := os.OpenFile(PeerOutboundHashLog, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		return
	}
	defer f.Close()
	_, _ = f.Write(raw)
}

// Lookup returns the stored entry for (decision_id, peer), or nil + false.
// The returned pointer is a copy; safe for the caller to retain.
func (s *PeerOutboundHashStore) Lookup(decisionID, peer string) (*OutboundHashEntry, bool) {
	if s == nil {
		return nil, false
	}
	s.mu.RLock()
	defer s.mu.RUnlock()
	key := strings.TrimSpace(decisionID) + "|" + strings.TrimSpace(peer)
	e, ok := s.byKey[key]
	if !ok {
		return nil, false
	}
	cp := *e
	return &cp, true
}

// Count returns the number of in-memory entries.
func (s *PeerOutboundHashStore) Count() int {
	if s == nil {
		return 0
	}
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.byKey)
}
