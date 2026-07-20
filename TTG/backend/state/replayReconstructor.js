'use strict';

/**
 * Replay Reconstructor
 *
 * Rebuilds a full gameplay session from bucket artifacts.
 *
 * Two reconstruction modes:
 *   1. Full replay   — load initial snapshot, re-apply every event in order
 *   2. Seek replay   — replay up to a specific event_count or timestamp
 *
 * Artifacts read from bucket_artifacts/:
 *   state_snapshot_<sessionId>.json          ← initial state (v0)
 *   state_event_trace_<sessionId>.jsonl      ← ordered event log
 *
 * Output:
 *   { frames }  — array of { event, stateBefore, stateAfter, changes }
 *                 one frame per event — the full state timeline
 */

const fs   = require('fs').promises;
const path = require('path');
const gsm  = require('./gameStateManager');
const snap = require('./stateSnapshot');

const BUCKET_DIR = path.join(__dirname, '../bucket_artifacts');

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Reconstruct a full session replay from bucket artifacts.
 *
 * @param {string} sessionId
 * @returns {Promise<Object>} { success, sessionId, frames, finalState, summary }
 */
async function reconstruct(sessionId) {
  // Step 1 — load initial snapshot (v0)
  const snapResult = await _loadInitialSnapshot(sessionId);
  if (!snapResult.success) return snapResult;

  // Step 2 — load event trace
  const traceResult = await _loadEventTrace(sessionId);
  if (!traceResult.success) return traceResult;

  const { events } = traceResult;
  if (events.length === 0) {
    return {
      success:    true,
      sessionId,
      frames:     [],
      finalState: snapResult.state,
      summary:    _buildSummary(sessionId, [], snapResult.state)
    };
  }

  // Step 3 — restore initial snapshot into a replay session
  const replaySessionId = `replay_${sessionId}_${Date.now()}`;
  const restoreResult   = snap.restore({
    ...snapResult.artifact,
    state: { ...snapResult.artifact.state, session_id: replaySessionId }
  });
  if (!restoreResult.success) return _fail(`Failed to restore snapshot: ${restoreResult.error}`);

  // Step 4 — replay events in order, capture frames
  const frames = [];

  for (const entry of events) {
    const stateBefore = gsm.getCurrentState(replaySessionId);

    // Reconstruct the event object from the trace entry
    const event = {
      event_type:      entry.event_type,
      event_id:        entry.event_id,
      timestamp:       entry.timestamp,
      game_session_id: replaySessionId,
      entities:        entry.entities || [],
      context:         entry.context  || {},
      metadata:        {}
    };

    const applyResult = gsm.applyEventToState(replaySessionId, event);

    frames.push({
      event_index:  frames.length,
      event_type:   entry.event_type,
      event_id:     entry.event_id,
      timestamp:    entry.timestamp,
      stateBefore,
      stateAfter:   applyResult.success ? gsm.getCurrentState(replaySessionId) : stateBefore,
      changes:      applyResult.changes || entry.changes || {},
      applied:      applyResult.success
    });
  }

  const finalState = gsm.getCurrentState(replaySessionId);

  // Clean up replay session from memory
  gsm.destroySession(replaySessionId);

  console.log(`[REPLAY] Reconstructed session ${sessionId}: ${frames.length} frames`);

  return {
    success:    true,
    sessionId,
    frames,
    finalState,
    summary:    _buildSummary(sessionId, frames, finalState)
  };
}

/**
 * Reconstruct up to a specific event index (seek).
 * Returns state at that point in time.
 *
 * @param {string} sessionId
 * @param {number} targetEventIndex  — 0-based, inclusive
 * @returns {Promise<Object>} { success, state, frame }
 */
async function reconstructAt(sessionId, targetEventIndex) {
  const result = await reconstruct(sessionId);
  if (!result.success) return result;

  if (targetEventIndex >= result.frames.length) {
    return { success: true, state: result.finalState, frame: result.frames[result.frames.length - 1] };
  }

  const frame = result.frames[targetEventIndex];
  return { success: true, state: frame.stateAfter, frame };
}

/**
 * Load all bucket artifacts for a session and return them raw.
 * Useful for inspection without replaying.
 *
 * @param {string} sessionId
 * @returns {Promise<Object>} { success, snapshot, events, schema }
 */
async function loadArtifacts(sessionId) {
  const [snapResult, traceResult, schemaResult] = await Promise.all([
    _loadInitialSnapshot(sessionId),
    _loadEventTrace(sessionId),
    _loadExecutionSchema(sessionId)
  ]);

  return {
    success:  snapResult.success,
    snapshot: snapResult.artifact  || null,
    events:   traceResult.events   || [],
    schema:   schemaResult.schema  || null
  };
}

// ─── Artifact loaders ─────────────────────────────────────────────────────────

async function _loadInitialSnapshot(sessionId) {
  // Try stable latest file first, then v0
  const candidates = [
    `state_snapshot_${sessionId}.json`,
    `state_snapshot_${sessionId}_v0.json`
  ];

  for (const filename of candidates) {
    const filepath = path.join(BUCKET_DIR, filename);
    try {
      const raw      = await fs.readFile(filepath, 'utf8');
      const artifact = JSON.parse(raw);
      if (artifact.artifact_type === 'state_snapshot' && artifact.state) {
        return { success: true, artifact, state: artifact.state };
      }
    } catch { /* try next */ }
  }

  return _fail(`No snapshot found for session: ${sessionId}`);
}

async function _loadEventTrace(sessionId) {
  const filepath = path.join(BUCKET_DIR, `state_event_trace_${sessionId}.jsonl`);
  try {
    const raw   = await fs.readFile(filepath, 'utf8');
    const lines = raw.trim().split('\n').filter(Boolean);
    const events = lines
      .map(l => { try { return JSON.parse(l); } catch { return null; } })
      .filter(Boolean)
      .sort((a, b) => a.timestamp - b.timestamp); // deterministic order by timestamp
    return { success: true, events };
  } catch (err) {
    // No trace file = zero events (valid for brand-new sessions)
    if (err.code === 'ENOENT') return { success: true, events: [] };
    return _fail(`Failed to read event trace: ${err.message}`);
  }
}

async function _loadExecutionSchema(sessionId) {
  const filepath = path.join(BUCKET_DIR, `state_exec_schema_${sessionId}.json`);
  try {
    const raw    = await fs.readFile(filepath, 'utf8');
    const schema = JSON.parse(raw);
    return { success: true, schema };
  } catch {
    return { success: true, schema: null }; // schema is optional for replay
  }
}

// ─── Summary builder ──────────────────────────────────────────────────────────

function _buildSummary(sessionId, frames, finalState) {
  const eventCounts = {};
  frames.forEach(f => {
    eventCounts[f.event_type] = (eventCounts[f.event_type] || 0) + 1;
  });

  return {
    session_id:    sessionId,
    total_events:  frames.length,
    events_by_type: eventCounts,
    final_score:   finalState?.player?.score   ?? 0,
    final_health:  finalState?.player?.health  ?? 0,
    final_lives:   finalState?.player?.lives   ?? 0,
    final_level:   finalState?.world?.level    ?? 1,
    final_status:  finalState?.status          ?? 'unknown'
  };
}

function _fail(error) {
  console.error(`[REPLAY] ${error}`);
  return { success: false, error };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  reconstruct,
  reconstructAt,
  loadArtifacts
};
