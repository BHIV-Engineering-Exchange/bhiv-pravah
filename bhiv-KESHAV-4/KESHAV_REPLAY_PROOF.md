# KESHAV Replay Proof

**Owner:** Rajaryan Verma
**Date:** 2026-06-17
**Status:** DETERMINISM PROVEN

---

## Purpose

This document proves KESHAV exhibits 100% deterministic replayability. Identical inputs always produce identical outputs (excluding the passive `timestamp` metadata field).

---

## Methodology

**Script:** `replay_determinism_proof.py`
**Replay count:** 10 runs per input
**Input classes:** 3 (blocked graph, clean graph, corrupted input)
**Comparison method:** Field-by-field equality + SHA-256 hash of canonical JSON serialization

---

## Test 1: Blocked Graph Replay

**Input:** 5-task blocked dependency graph with T1 as root cause.

| Run | SHA-256 Hash (first 16) | Status | Root Cause | Resolution Signal |
|-----|------------------------|--------|------------|-------------------|
| 1-10 | `0166abbe307d5f1a` | OK | T1 | UNBLOCK_DEPENDENCY:T1 |

**Full SHA-256:** `0166abbe307d5f1a34042637b9ce00e5...`

- All 10 outputs field-by-field identical
- All 10 SHA-256 hashes identical
- All 10 trace_ids preserved across all layers
- All 10 Bucket persistence records identical

---

## Test 2: Clean Graph Replay

**Input:** 2-task clean graph with no blocked tasks.

| Run | SHA-256 Hash (first 16) | Status | Root Cause | Sarathi Action |
|-----|------------------------|--------|------------|----------------|
| 1-10 | `e75610c4bd013850` | OK | None | NO_ACTION |

**Full SHA-256:** `e75610c4bd013850d41431e72677e8b2...`

- All 10 outputs field-by-field identical
- All 10 SHA-256 hashes identical

---

## Test 3: Fail-Closed Replay

**Input:** Missing `trace_id`, `tasks` is a string (corrupted).

| Run | SHA-256 Hash (first 16) | Status | Reason |
|-----|------------------------|--------|--------|
| 1-10 | `9000de7535a531f5` | FAIL | INVALID_INPUT_CONTRACT |

**Full SHA-256:** `9000de7535a531f56ab834ed41b9d15e...`

- All 10 outputs field-by-field identical
- All 10 SHA-256 hashes identical
- Zero Bucket writes across all 10 runs

---

## Cross-Input Hash Isolation

| Pair | Hash A | Hash B | Equal? |
|------|--------|--------|--------|
| Input A vs Input B | `0166abbe...` | `e75610c4...` | No |
| Input A vs Input C | `0166abbe...` | `9000de75...` | No |
| Input B vs Input C | `e75610c4...` | `9000de75...` | No |

Different inputs always produce different outputs. No hash collision.

---

## InsightFlow Event Determinism

3 identical replay runs of Input A:
- All 3 InsightFlow events have identical `trace_id`, `root_cause`, `severity`, `resolution_signal`
- Event type is always `EXECUTION` for valid inputs

---

## Structural Determinism Guarantees

KESHAV's determinism is enforced structurally, not by convention:

1. **`sorted()`** — All list outputs use `sorted()` for deterministic ordering
2. **Lexicographical tie-breakers** — `max()` operations use lexicographical tie-breaking
3. **Function-scoped stateless** — Zero global variables, zero class instances, zero mutable shared state
4. **No randomness** — No `random`, no `uuid.uuid4()`, no non-deterministic operations
5. **Timestamp exclusion** — The `timestamp` field is the only varying output (passive metadata, excluded from replay comparison)

---

## Assertions Summary

**Total:** 34/34 passed

| Test | Assertions | Result |
|------|-----------|--------|
| Blocked graph replay (10 runs) | 14 | All pass |
| Clean graph replay (10 runs) | 2 | All pass |
| Fail-closed replay (10 runs) | 12 | All pass |
| Cross-input hash isolation | 3 | All pass |
| InsightFlow event determinism | 3 | All pass |
