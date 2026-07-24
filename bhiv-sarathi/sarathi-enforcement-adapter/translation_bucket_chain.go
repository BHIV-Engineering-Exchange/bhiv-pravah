package main

// translation_bucket_chain.go — v15.5 Sovereign Translational Layer.
//
// Per-trace parent_hash chain store for Bucket artifacts. Each artifact in a
// trace_id chains back to the artifact_id of the previous artifact (or the
// hard-coded BucketArtifactGenesisHash for the first one). State is durable
// at live/translation/parent_chain/{trace_id}.json.
//
// Concurrency: an in-process per-trace mutex serialises LookupParent +
// AppendParent for the same trace_id. Multi-process safety is out-of-scope —
// the production --service runtime is single-process.
//
// TAG: translation-layer

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// ParentHashStore tracks the running tip_hash per trace_id.
type ParentHashStore struct {
	rootDir string

	mu    sync.Mutex
	locks map[string]*sync.Mutex // per-trace_id
}

// parentChainSnapshot is the on-disk record. CanonicalMarshal preserves field
// order so any verifier can recompute the file hash byte-for-byte.
type parentChainSnapshot struct {
	TraceID   string `json:"trace_id"`
	TipHash   string `json:"tip_hash"`
	Count     int    `json:"count"`
	UpdatedAt string `json:"updated_at"`
}

// globalParentHashStore is the process-wide store wired into the Bucket
// fan-out.
var globalParentHashStore = NewParentHashStore("live/translation/parent_chain")

// NewParentHashStore creates a store rooted at dir.
func NewParentHashStore(dir string) *ParentHashStore {
	return &ParentHashStore{
		rootDir: dir,
		locks:   make(map[string]*sync.Mutex),
	}
}

// lockFor returns the mutex for traceID, creating one if needed. Holds
// s.mu only briefly to fetch/install — the per-trace mutex is held by the
// caller during the read-modify-write window.
func (s *ParentHashStore) lockFor(traceID string) *sync.Mutex {
	s.mu.Lock()
	defer s.mu.Unlock()
	m, ok := s.locks[traceID]
	if !ok {
		m = &sync.Mutex{}
		s.locks[traceID] = m
	}
	return m
}

// LookupParent returns the parent_hash that the NEXT artifact for traceID
// should carry. For a fresh trace, returns BucketArtifactGenesisHash and
// isGenesis=true. The store is not advanced until AppendParent is called.
func (s *ParentHashStore) LookupParent(traceID string) (parentHash string, isGenesis bool, err error) {
	if traceID == "" {
		return "", false, fmt.Errorf("parent_chain: trace_id is empty")
	}
	m := s.lockFor(traceID)
	m.Lock()
	defer m.Unlock()
	return s.lookupParentLocked(traceID)
}

// lookupParentLocked is the unlocked variant for callers already holding the
// per-trace mutex.
func (s *ParentHashStore) lookupParentLocked(traceID string) (string, bool, error) {
	path := s.pathFor(traceID)
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return BucketArtifactGenesisHash, true, nil
		}
		return "", false, fmt.Errorf("parent_chain: read: %w", err)
	}
	var snap parentChainSnapshot
	if e := jsonUnmarshalStrict(data, &snap); e != nil {
		return "", false, fmt.Errorf("parent_chain: decode: %w", e)
	}
	if snap.TipHash == "" {
		return BucketArtifactGenesisHash, true, nil
	}
	return snap.TipHash, false, nil
}

// AppendParent advances the chain: the just-built artifact_id becomes the
// new tip_hash. Returns the post-append count. Caller is responsible for
// having computed artifactID over the EXACT same payload that will be sent
// downstream.
func (s *ParentHashStore) AppendParent(traceID, artifactID string) (count int, err error) {
	if traceID == "" {
		return 0, fmt.Errorf("parent_chain: trace_id is empty")
	}
	if artifactID == "" {
		return 0, fmt.Errorf("parent_chain: artifact_id is empty")
	}
	m := s.lockFor(traceID)
	m.Lock()
	defer m.Unlock()

	path := s.pathFor(traceID)

	// Read existing count if any. Missing file ⇒ count=0 (genesis precedes).
	existing := parentChainSnapshot{TraceID: traceID}
	if data, rerr := os.ReadFile(path); rerr == nil {
		_ = jsonUnmarshalStrict(data, &existing)
	}

	next := parentChainSnapshot{
		TraceID:   traceID,
		TipHash:   artifactID,
		Count:     existing.Count + 1,
		UpdatedAt: time.Now().UTC().Format(time.RFC3339Nano),
	}
	out, merr := CanonicalMarshal(next)
	if merr != nil {
		return 0, fmt.Errorf("parent_chain: marshal: %w", merr)
	}
	if werr := atomicWriteFile(path, out, 0o644); werr != nil {
		return 0, fmt.Errorf("parent_chain: write: %w", werr)
	}
	return next.Count, nil
}

// LookupAndAppend is the typical fan-out call: returns the parent for the
// next artifact, then expects the caller to invoke AppendParent once the
// artifact_id is computed. We do NOT fold them into one call because the
// artifact_id depends on parent_hash, and parent_hash depends on the prior
// state — splitting the operations gives the caller the value it needs to
// assemble the artifact before committing the chain advance.
//
// This helper exists to preserve the per-trace lock across the split, which
// guarantees no concurrent fan-out can interleave its lookup between our
// lookup and append.
func (s *ParentHashStore) LookupAndAppend(traceID string, computeArtifactID func(parentHash string, isGenesis bool) (string, error)) (parentHash, artifactID string, count int, err error) {
	m := s.lockFor(traceID)
	m.Lock()
	defer m.Unlock()

	parent, isGenesis, lerr := s.lookupParentLocked(traceID)
	if lerr != nil {
		return "", "", 0, lerr
	}
	aid, cerr := computeArtifactID(parent, isGenesis)
	if cerr != nil {
		return "", "", 0, cerr
	}
	if aid == "" {
		return "", "", 0, fmt.Errorf("parent_chain: computeArtifactID returned empty id")
	}

	path := s.pathFor(traceID)
	existing := parentChainSnapshot{TraceID: traceID}
	if data, rerr := os.ReadFile(path); rerr == nil {
		_ = jsonUnmarshalStrict(data, &existing)
	}
	next := parentChainSnapshot{
		TraceID:   traceID,
		TipHash:   aid,
		Count:     existing.Count + 1,
		UpdatedAt: time.Now().UTC().Format(time.RFC3339Nano),
	}
	out, merr := CanonicalMarshal(next)
	if merr != nil {
		return "", "", 0, fmt.Errorf("parent_chain: marshal: %w", merr)
	}
	if werr := atomicWriteFile(path, out, 0o644); werr != nil {
		return "", "", 0, fmt.Errorf("parent_chain: write: %w", werr)
	}
	return parent, aid, next.Count, nil
}

// CurrentTip returns the latest tip_hash stored for traceID, or empty if no
// artifact has been chained yet. Used by --verify-bucket-chain.
func (s *ParentHashStore) CurrentTip(traceID string) (tipHash string, count int, err error) {
	if traceID == "" {
		return "", 0, fmt.Errorf("parent_chain: trace_id is empty")
	}
	m := s.lockFor(traceID)
	m.Lock()
	defer m.Unlock()

	path := s.pathFor(traceID)
	data, rerr := os.ReadFile(path)
	if rerr != nil {
		if os.IsNotExist(rerr) {
			return "", 0, nil
		}
		return "", 0, fmt.Errorf("parent_chain: read: %w", rerr)
	}
	var snap parentChainSnapshot
	if e := jsonUnmarshalStrict(data, &snap); e != nil {
		return "", 0, fmt.Errorf("parent_chain: decode: %w", e)
	}
	return snap.TipHash, snap.Count, nil
}

// pathFor returns the on-disk path for a trace_id snapshot.
func (s *ParentHashStore) pathFor(traceID string) string {
	return filepath.Join(s.rootDir, safeForFilename(traceID)+".json")
}
