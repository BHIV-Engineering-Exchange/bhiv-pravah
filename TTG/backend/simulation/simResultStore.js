'use strict';

const TTL_MS = 60 * 60 * 1000;
const _store = new Map(); // trace_id → { result, contract, stream_ticks, stored_at }

// Lazy-loaded to avoid circular dep (bucketWriter → storage → simResultStore)
function _bucket() { return require('../bucketWriter'); }

// Save a result. Returns false if trace_id already exists (no overwrite).
// stream_ticks: ordered array of TANTRA delta payloads emitted during the live stream.
function save(trace_id, result, contract, stream_ticks) {
  if (_store.has(trace_id)) return false;
  _store.set(trace_id, {
    result,
    contract:     contract     || null,
    stream_ticks: stream_ticks || null,  // null when saved from HTTP /run (no stream)
    stored_at:    Date.now()
  });
  return true;
}

function get(trace_id) {
  const entry = _store.get(trace_id);
  if (!entry) return null;
  if (Date.now() - entry.stored_at > TTL_MS) { _store.delete(trace_id); return null; }
  return entry.result;
}

function getWithContract(trace_id) {
  const entry = _store.get(trace_id);
  if (entry) {
    if (Date.now() - entry.stored_at > TTL_MS) { _store.delete(trace_id); }
    else return { result: entry.result, contract: entry.contract, stream_ticks: entry.stream_ticks };
  }

  // Phase 2: in-memory miss — fall back to bucket (survives restart)
  const persisted = _bucket().loadStreamTicks(trace_id);
  if (!persisted) return null;

  // Warm the in-memory cache from disk so subsequent calls are fast
  _store.set(trace_id, {
    result:       { ticks_run: persisted.stream_ticks.length, status: 'completed' },
    contract:     persisted.contract,
    stream_ticks: persisted.stream_ticks,
    stored_at:    Date.now()
  });

  return { result: _store.get(trace_id).result, contract: persisted.contract, stream_ticks: persisted.stream_ticks };
}

// Count of live (non-expired) entries — for health reporting only
function count() {
  const now = Date.now();
  let n = 0;
  for (const [trace_id, entry] of _store.entries()) {
    if (now - entry.stored_at > TTL_MS) { _store.delete(trace_id); continue; }
    n++;
  }
  return n;
}

// TTL eviction — runs every 10 minutes
setInterval(() => {
  const now = Date.now();
  for (const [trace_id, entry] of _store.entries()) {
    if (now - entry.stored_at > TTL_MS) _store.delete(trace_id);
  }
}, 10 * 60 * 1000);

// Test-only: expose internal map for memory-clear simulation
function _store_for_test() { return _store; }

module.exports = { save, get, getWithContract, count, _store_for_test };
