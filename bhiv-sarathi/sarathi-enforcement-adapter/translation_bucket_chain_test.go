package main

// translation_bucket_chain_test.go — v15.5 Sovereign Translational Layer.
//
// Verifies the per-trace parent_hash chain store. Tests cover genesis,
// successive appends, count progression, and re-read consistency.

import (
	"path/filepath"
	"testing"
)

func TestParentHashStore_GenesisOnFirstLookup(t *testing.T) {
	dir := t.TempDir()
	store := NewParentHashStore(filepath.Join(dir, "parent_chain"))

	parent, isGenesis, err := store.LookupParent("trace-fresh-001")
	if err != nil {
		t.Fatalf("LookupParent: %v", err)
	}
	if !isGenesis {
		t.Error("first lookup should be genesis")
	}
	if parent != BucketArtifactGenesisHash {
		t.Errorf("genesis parent: want %q got %q", BucketArtifactGenesisHash, parent)
	}
}

func TestParentHashStore_AppendAdvancesChain(t *testing.T) {
	dir := t.TempDir()
	store := NewParentHashStore(filepath.Join(dir, "parent_chain"))

	traceID := "trace-append-001"
	count, err := store.AppendParent(traceID, "artifact-A")
	if err != nil {
		t.Fatalf("AppendParent A: %v", err)
	}
	if count != 1 {
		t.Errorf("count after first append: want 1 got %d", count)
	}

	// After append, the next lookup should return artifact-A as the parent.
	parent, isGenesis, err := store.LookupParent(traceID)
	if err != nil {
		t.Fatalf("LookupParent: %v", err)
	}
	if isGenesis {
		t.Error("after first append, lookup should NOT be genesis")
	}
	if parent != "artifact-A" {
		t.Errorf("parent after append: want artifact-A got %q", parent)
	}

	count2, err := store.AppendParent(traceID, "artifact-B")
	if err != nil {
		t.Fatalf("AppendParent B: %v", err)
	}
	if count2 != 2 {
		t.Errorf("count after second append: want 2 got %d", count2)
	}
}

func TestParentHashStore_LookupAndAppend_Atomic(t *testing.T) {
	dir := t.TempDir()
	store := NewParentHashStore(filepath.Join(dir, "parent_chain"))

	traceID := "trace-atomic-001"

	// First call ⇒ genesis parent, artifact-id derived from a fixed string.
	parent, aid, count, err := store.LookupAndAppend(traceID, func(p string, isGenesis bool) (string, error) {
		if !isGenesis {
			t.Error("expected genesis on first atomic call")
		}
		if p != BucketArtifactGenesisHash {
			t.Errorf("expected genesis hash, got %q", p)
		}
		return "atomic-A", nil
	})
	if err != nil {
		t.Fatalf("LookupAndAppend 1: %v", err)
	}
	if parent != BucketArtifactGenesisHash {
		t.Errorf("returned parent != genesis on first call: %q", parent)
	}
	if aid != "atomic-A" {
		t.Errorf("returned artifact_id: want atomic-A got %q", aid)
	}
	if count != 1 {
		t.Errorf("count: want 1 got %d", count)
	}

	// Second call ⇒ parent = atomic-A.
	parent2, aid2, count2, err := store.LookupAndAppend(traceID, func(p string, isGenesis bool) (string, error) {
		if isGenesis {
			t.Error("expected NON-genesis on second atomic call")
		}
		if p != "atomic-A" {
			t.Errorf("expected parent atomic-A, got %q", p)
		}
		return "atomic-B", nil
	})
	if err != nil {
		t.Fatalf("LookupAndAppend 2: %v", err)
	}
	if parent2 != "atomic-A" {
		t.Errorf("returned parent on 2nd: want atomic-A got %q", parent2)
	}
	if aid2 != "atomic-B" {
		t.Errorf("returned artifact_id on 2nd: want atomic-B got %q", aid2)
	}
	if count2 != 2 {
		t.Errorf("count on 2nd: want 2 got %d", count2)
	}
}

func TestParentHashStore_CurrentTip(t *testing.T) {
	dir := t.TempDir()
	store := NewParentHashStore(filepath.Join(dir, "parent_chain"))
	traceID := "trace-tip-001"

	// Empty trace.
	tip, count, err := store.CurrentTip(traceID)
	if err != nil {
		t.Fatalf("CurrentTip empty: %v", err)
	}
	if tip != "" || count != 0 {
		t.Errorf("expected empty/0, got %q/%d", tip, count)
	}

	_, _ = store.AppendParent(traceID, "tip-A")
	_, _ = store.AppendParent(traceID, "tip-B")

	tip, count, err = store.CurrentTip(traceID)
	if err != nil {
		t.Fatalf("CurrentTip: %v", err)
	}
	if tip != "tip-B" {
		t.Errorf("tip: want tip-B got %q", tip)
	}
	if count != 2 {
		t.Errorf("count: want 2 got %d", count)
	}
}

func TestParentHashStore_DistinctTracesIndependent(t *testing.T) {
	dir := t.TempDir()
	store := NewParentHashStore(filepath.Join(dir, "parent_chain"))

	_, _ = store.AppendParent("trace-X", "X-1")
	_, _ = store.AppendParent("trace-Y", "Y-1")
	_, _ = store.AppendParent("trace-X", "X-2")

	tipX, countX, _ := store.CurrentTip("trace-X")
	tipY, countY, _ := store.CurrentTip("trace-Y")

	if tipX != "X-2" || countX != 2 {
		t.Errorf("trace-X: want tip=X-2 count=2 got %q/%d", tipX, countX)
	}
	if tipY != "Y-1" || countY != 1 {
		t.Errorf("trace-Y: want tip=Y-1 count=1 got %q/%d", tipY, countY)
	}
}

// BuildBucketArtifact end-to-end is exercised by the live-integration tests
// because constructing a sealed PropagationEnvelope from scratch requires a
// full enforcement pipeline. The chain primitives above cover the
// concurrency-sensitive surface; the BHIV-shaped wrapper is a thin assembly
// step verified in VC_VALIDATION_SCRIPT.md.
