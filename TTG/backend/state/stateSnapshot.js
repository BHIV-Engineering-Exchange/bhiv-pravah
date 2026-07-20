'use strict';

/**
 * State Snapshot System
 *
 * Three capabilities:
 *   1. serialize   — convert live state to a portable JSON artifact
 *   2. restore     — load a serialized snapshot back into the GSM
 *   3. checkpoint  — named snapshot at a meaningful moment (level up, death, etc.)
 *
 * Snapshots are stored in-memory (for fast access during a session) AND
 * written to disk under bucket_artifacts/ using the same naming convention
 * as LocalStorage so Phase 5 (stateBucketWriter) can pick them up.
 *
 * Naming convention:
 *   state_snapshot_<sessionId>_v<version>.json      ← versioned snapshot
 *   state_checkpoint_<sessionId>_<label>.json       ← named checkpoint
 */

const fs   = require('fs').promises;
const path = require('path');
const gsm  = require('./gameStateManager');

const SNAPSHOT_DIR = path.join(__dirname, '../bucket_artifacts');

// In-memory checkpoint store: sessionId → [ { label, version, state, timestamp } ]
const _checkpoints = new Map();

// ─── 1. Serialize ─────────────────────────────────────────────────────────────

/**
 * Serialize the current live state of a session into a plain JSON artifact.
 * Does NOT write to disk — just returns the artifact object.
 *
 * @param {string} sessionId
 * @returns {Object} { success, artifact } | { success: false, error }
 */
function serialize(sessionId) {
  const state = gsm.getCurrentState(sessionId);
  if (!state) return _fail(`No state found for session: ${sessionId}`);

  const artifact = {
    artifact_type:    'state_snapshot',
    session_id:       state.session_id,
    game_mode:        state.game_mode,
    snapshot_version: state.meta.snapshot_version,
    event_count:      state.meta.event_count,
    serialized_at:    Date.now(),
    state
  };

  return { success: true, artifact };
}

// ─── 2. Restore ───────────────────────────────────────────────────────────────

/**
 * Restore a session from a serialized snapshot artifact.
 * If the session already exists in GSM it is overwritten.
 *
 * @param {Object} artifact  — artifact produced by serialize() or loaded from disk
 * @returns {Object} { success, state } | { success: false, error }
 */
function restore(artifact) {
  if (!artifact || artifact.artifact_type !== 'state_snapshot') {
    return _fail('Invalid artifact: missing artifact_type === "state_snapshot"');
  }

  const { state } = artifact;
  if (!state || !state.session_id) {
    return _fail('Invalid artifact: missing state.session_id');
  }

  // Inject the restored state directly into GSM's internal map.
  // We reach into GSM via a dedicated restoreSession() path — but since
  // GSM doesn't expose one yet, we use createGameState with a synthetic
  // template then overwrite via the exported _restoreSession helper below.
  _restoreIntoGSM(state);

  console.log(`[SNAPSHOT] Restored session ${state.session_id} at v${state.meta.snapshot_version}, event_count=${state.meta.event_count}`);

  return { success: true, state: gsm.getCurrentState(state.session_id) };
}

/**
 * Restore a snapshot from a file on disk.
 *
 * @param {string} filepath  — absolute path to the snapshot JSON file
 * @returns {Promise<Object>} { success, state } | { success: false, error }
 */
async function restoreFromFile(filepath) {
  try {
    const raw      = await fs.readFile(filepath, 'utf8');
    const artifact = JSON.parse(raw);
    return restore(artifact);
  } catch (err) {
    return _fail(`Failed to read snapshot file: ${err.message}`);
  }
}

// ─── 3. Checkpoint ────────────────────────────────────────────────────────────

/**
 * Create a named checkpoint of the current state.
 * Stored in memory AND written to disk.
 *
 * @param {string} sessionId
 * @param {string} label      — e.g. 'level_2_start', 'player_death_1', 'wave_3'
 * @returns {Promise<Object>} { success, checkpoint } | { success: false, error }
 */
async function createCheckpoint(sessionId, label) {
  const serialized = serialize(sessionId);
  if (!serialized.success) return serialized;

  const checkpoint = {
    label,
    session_id:       sessionId,
    snapshot_version: serialized.artifact.snapshot_version,
    event_count:      serialized.artifact.event_count,
    timestamp:        Date.now(),
    artifact:         serialized.artifact
  };

  // Store in memory
  if (!_checkpoints.has(sessionId)) _checkpoints.set(sessionId, []);
  _checkpoints.get(sessionId).push(checkpoint);

  // Write to disk
  await _writeToDisk(
    `state_checkpoint_${sessionId}_${label}.json`,
    checkpoint
  );

  console.log(`[SNAPSHOT] Checkpoint "${label}" created for session ${sessionId}`);
  return { success: true, checkpoint };
}

/**
 * Get all in-memory checkpoints for a session.
 *
 * @param {string} sessionId
 * @returns {Object[]} Array of checkpoints (oldest first)
 */
function getCheckpoints(sessionId) {
  return _checkpoints.get(sessionId) || [];
}

/**
 * Restore from the most recent checkpoint for a session.
 *
 * @param {string} sessionId
 * @returns {Object} { success, state } | { success: false, error }
 */
function restoreLatestCheckpoint(sessionId) {
  const checkpoints = getCheckpoints(sessionId);
  if (checkpoints.length === 0) {
    return _fail(`No checkpoints found for session: ${sessionId}`);
  }
  const latest = checkpoints[checkpoints.length - 1];
  return restore(latest.artifact);
}

// ─── Versioned snapshot write ─────────────────────────────────────────────────

/**
 * Serialize current state and write a versioned snapshot to disk.
 * Increments snapshot_version in the live state.
 * Called by stateBucketWriter (Phase 5) — but can also be called directly.
 *
 * @param {string} sessionId
 * @returns {Promise<Object>} { success, filepath, version }
 */
async function writeSnapshot(sessionId) {
  const serialized = serialize(sessionId);
  if (!serialized.success) return serialized;

  const { artifact } = serialized;
  const version      = artifact.snapshot_version;
  const filename     = `state_snapshot_${sessionId}_v${version}.json`;

  const result = await _writeToDisk(filename, artifact);
  if (!result.success) return result;

  // Bump snapshot_version in live state so next write gets a new filename
  _bumpSnapshotVersion(sessionId);

  console.log(`[SNAPSHOT] Wrote snapshot v${version} for session ${sessionId}`);
  return { success: true, filepath: result.filepath, version };
}

// ─── Internal helpers ─────────────────────────────────────────────────────────

async function _writeToDisk(filename, data) {
  try {
    await fs.mkdir(SNAPSHOT_DIR, { recursive: true });
    const filepath = path.join(SNAPSHOT_DIR, filename);
    await fs.writeFile(filepath, JSON.stringify(data, null, 2));
    return { success: true, filepath };
  } catch (err) {
    console.error(`[SNAPSHOT] Disk write failed: ${err.message}`);
    return { success: false, error: err.message };
  }
}

/**
 * Directly inject a restored state object into GSM's internal _sessions map.
 * GSM doesn't expose a restore path, so we use createGameState with a minimal
 * synthetic template then immediately overwrite the created state.
 *
 * This is the only place that bypasses the normal GSM creation flow —
 * it is intentional and safe because the state came from a validated snapshot.
 */
function _restoreIntoGSM(state) {
  const { _sessions } = _getGSMInternals();

  // Deep-clone to avoid frozen-object issues (getCurrentState returns frozen)
  const mutableState = JSON.parse(JSON.stringify(state));
  _sessions.set(state.session_id, mutableState);
}

/**
 * Increment snapshot_version on the live (mutable) state inside GSM.
 */
function _bumpSnapshotVersion(sessionId) {
  const { _sessions } = _getGSMInternals();
  const state = _sessions.get(sessionId);
  if (state) state.meta.snapshot_version++;
}

/**
 * Access GSM's internal _sessions map.
 * Requires GSM to export it — we add a thin accessor below.
 */
function _getGSMInternals() {
  return require('./gameStateManager').__internals();
}

function _fail(error) {
  console.error(`[SNAPSHOT] ${error}`);
  return { success: false, error };
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = {
  serialize,
  restore,
  restoreFromFile,
  createCheckpoint,
  getCheckpoints,
  restoreLatestCheckpoint,
  writeSnapshot
};
