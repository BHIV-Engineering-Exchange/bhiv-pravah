'use strict';

/**
 * State Bucket Writer
 *
 * Persists the three state artifact types required by the task spec:
 *   1. state snapshots   — full serialized game state at a point in time
 *   2. execution schema  — the schema that initialized this session's state
 *   3. event traces      — append-only log of every runtime event applied
 *
 * Pattern mirrors bucketWriter.js exactly:
 *   - Always writes to local storage first (bucket_artifacts/)
 *   - If USE_PRIMARY_BUCKET=true, also sends to the Primary Bucket endpoint
 *   - Primary Bucket failures are non-fatal (logged, not thrown)
 */

const fs            = require('fs').promises;
const path          = require('path');
const primaryBucket = require('../primaryBucketAdapter');
const snapshot      = require('./stateSnapshot');

const BUCKET_DIR         = path.join(__dirname, '../bucket_artifacts');
const USE_PRIMARY_BUCKET = process.env.USE_PRIMARY_BUCKET === 'true';

// ─── 1. State Snapshot ────────────────────────────────────────────────────────

/**
 * Serialize current session state and write it to the bucket.
 * Writes two files:
 *   state_snapshot_<sessionId>_v<N>.json  — versioned (via stateSnapshot.writeSnapshot)
 *   state_snapshot_<sessionId>.json       — stable "latest" for easy lookup
 *
 * @param {string} sessionId
 * @returns {Promise<Object>} { success, filepath, version }
 */
async function writeStateSnapshot(sessionId) {
  const snapResult = await snapshot.writeSnapshot(sessionId);
  if (!snapResult.success) return snapResult;

  const serialized = snapshot.serialize(sessionId);
  if (!serialized.success) return serialized;

  const latestFile  = `state_snapshot_${sessionId}.json`;
  const localResult = await _writeToDisk(latestFile, serialized.artifact);

  if (USE_PRIMARY_BUCKET) {
    await _sendToPrimaryBucket('state_snapshot', sessionId, serialized.artifact)
      .catch(err => console.error('[STATE_BUCKET] Primary Bucket snapshot sync failed:', err.message));
  }

  console.log(`[STATE_BUCKET] Snapshot written — session: ${sessionId}, v${snapResult.version}`);
  return { success: true, filepath: localResult.filepath, version: snapResult.version };
}

// ─── 2. Execution Schema ──────────────────────────────────────────────────────

/**
 * Write the execution schema that initialized this session's state.
 * Filename: state_exec_schema_<sessionId>.json
 *
 * @param {string} sessionId
 * @param {string} executionId  — from Prompt Runner output
 * @param {string} traceId
 * @param {Object} executionSchema
 * @returns {Promise<Object>} { success, filepath }
 */
async function writeExecutionSchema(sessionId, executionId, traceId, executionSchema) {
  const artifact = {
    artifact_type: 'state_execution_schema',
    session_id:    sessionId,
    execution_id:  executionId,
    trace_id:      traceId,
    executionSchema,
    written_at:    Date.now(),
    source:        'game_state_engine'
  };

  const filename    = `state_exec_schema_${sessionId}.json`;
  const localResult = await _writeToDisk(filename, artifact);

  if (USE_PRIMARY_BUCKET) {
    await primaryBucket.sendExecutionSchema(executionId, traceId, executionSchema, Date.now())
      .catch(err => console.error('[STATE_BUCKET] Primary Bucket schema sync failed:', err.message));
  }

  console.log(`[STATE_BUCKET] Execution schema written — session: ${sessionId}`);
  return localResult;
}

// ─── 3. Event Trace ───────────────────────────────────────────────────────────

/**
 * Append a single runtime event to the session's event trace log.
 * Filename: state_event_trace_<sessionId>.jsonl  (newline-delimited JSON)
 *
 * @param {string} sessionId
 * @param {Object} event    — the runtime event that was applied
 * @param {Object} changes  — state changes produced by applyEventToState
 * @returns {Promise<Object>} { success, filepath }
 */
async function appendEventTrace(sessionId, event, changes) {
  const entry = {
    session_id: sessionId,
    event_id:   event.event_id,
    event_type: event.event_type,
    timestamp:  event.timestamp,
    entities:   event.entities || [],
    context:    event.context  || {},
    changes,
    traced_at:  Date.now()
  };

  const filename = `state_event_trace_${sessionId}.jsonl`;
  const filepath = path.join(BUCKET_DIR, filename);

  try {
    await fs.mkdir(BUCKET_DIR, { recursive: true });
    await fs.appendFile(filepath, JSON.stringify(entry) + '\n');
  } catch (err) {
    console.error(`[STATE_BUCKET] Event trace write failed: ${err.message}`);
    return { success: false, error: err.message };
  }

  if (USE_PRIMARY_BUCKET) {
    await primaryBucket.sendExecutionLog(
      event.game_session_id || sessionId,
      event.event_id,
      event.event_type,
      entry
    ).catch(err => console.error('[STATE_BUCKET] Primary Bucket trace sync failed:', err.message));
  }

  return { success: true, filepath };
}

// ─── Convenience: write all artifacts at session end ─────────────────────────

/**
 * Write final snapshot + schema together when a session ends.
 * Call this on game_over or completed status.
 *
 * @param {string} sessionId
 * @param {string} executionId
 * @param {string} traceId
 * @param {Object} executionSchema
 * @returns {Promise<Object>} { success, snapshot, schema }
 */
async function writeSessionEnd(sessionId, executionId, traceId, executionSchema) {
  const [snapResult, schemaResult] = await Promise.all([
    writeStateSnapshot(sessionId),
    writeExecutionSchema(sessionId, executionId, traceId, executionSchema)
  ]);

  const success = snapResult.success && schemaResult.success;
  console.log(`[STATE_BUCKET] Session end artifacts written — session: ${sessionId}, success: ${success}`);
  return { success, snapshot: snapResult, schema: schemaResult };
}

// ─── Internal helpers ─────────────────────────────────────────────────────────

async function _writeToDisk(filename, data) {
  try {
    await fs.mkdir(BUCKET_DIR, { recursive: true });
    const filepath = path.join(BUCKET_DIR, filename);
    await fs.writeFile(filepath, JSON.stringify(data, null, 2));
    return { success: true, filepath };
  } catch (err) {
    console.error(`[STATE_BUCKET] Disk write failed (${filename}): ${err.message}`);
    return { success: false, error: err.message };
  }
}

async function _sendToPrimaryBucket(artifactClass, sessionId, artifact) {
  const axios = require('axios');
  const PRIMARY_BUCKET_URL = process.env.PRIMARY_BUCKET_URL || 'http://localhost:8000';

  const response = await axios.post(
    `${PRIMARY_BUCKET_URL}/governance/validate-artifact-admission`,
    { artifact_class: artifactClass, session_id: sessionId, ...artifact, source: 'game_state_engine' },
    { params: { artifact_class: artifactClass } }
  );

  if (response.data.admitted) {
    console.log(`[STATE_BUCKET] Primary Bucket admitted: ${artifactClass} for ${sessionId}`);
    return { success: true };
  }
  console.warn(`[STATE_BUCKET] Primary Bucket rejected: ${response.data.reason}`);
  return { success: false, error: response.data.reason };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  writeStateSnapshot,
  writeExecutionSchema,
  appendEventTrace,
  writeSessionEnd
};
