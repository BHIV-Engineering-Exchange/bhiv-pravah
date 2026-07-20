'use strict';

/**
 * deltaComputer.js
 *
 * Computes which entities changed between the previous tick state
 * and the current entity map.
 *
 * Rules:
 *   - Only entities whose position, state, or attributes changed are included
 *   - Output shape is the locked TANTRA delta schema
 *   - position is always { x, y, z } — never array
 *   - Never emits a full snapshot — delta only
 */

function compute(trace_id, tick_id, current_map, prev_map) {
  const changed = [];

  for (const [id, entity] of Object.entries(current_map)) {
    const prev = prev_map[id];
    if (!prev || _entityChanged(prev, entity)) {
      changed.push(_toTantraEntity(entity));
    }
  }

  return {
    trace_id,
    tick_id,
    timestamp: new Date().toISOString(),
    entities:  changed
  };
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function _entityChanged(prev, curr) {
  if (prev.state !== curr.state) return true;
  if (_posChanged(prev.position, curr.position)) return true;
  if (JSON.stringify(prev.meta || {}) !== JSON.stringify(curr.meta || {})) return true;
  return false;
}

function _posChanged(a, b) {
  if (!a || !b) return true;
  return a[0] !== b[0] || a[1] !== b[1] || a[2] !== b[2];
}

function _toTantraEntity(entity) {
  const pos = entity.position || [0, 0, 0];
  return {
    id:         entity.id,
    type:       entity.type,
    position:   { x: pos[0], y: pos[1], z: pos[2] },
    state:      entity.state,
    attributes: entity.meta || {}
  };
}

// ─── Snapshot helper ──────────────────────────────────────────────────────────

function snapshot(current_map) {
  const out = {};
  for (const [id, e] of Object.entries(current_map)) {
    out[id] = {
      state:    e.state,
      position: [...(e.position || [0, 0, 0])],
      meta:     JSON.parse(JSON.stringify(e.meta || {}))
    };
  }
  return out;
}

// ─── Phase 6: Delta validation ────────────────────────────────────────────────

const VALID_STATES = new Set(['active', 'idle', 'stopped', 'destroyed']);

/**
 * Validate a computed TANTRA delta payload before emission.
 *
 * Failure boundaries (Phase 6):
 *   MALFORMED_DELTA      — missing/wrong top-level fields or entity shape
 *   BROKEN_TRACE_ID      — trace_id null, empty, wrong type, or mismatched
 *   MISSING_ENTITY_STATE — entity state absent or not in valid set
 *   INVALID_POSITION     — position not {x,y,z} with finite numbers
 *
 * @param {Object} delta     — output of compute()
 * @param {string} trace_id  — expected trace_id from contract
 * @returns {{ code, reason }|null}  null = valid, object = hard-fail
 */
function validate(delta, trace_id) {
  // Malformed delta — top-level shape
  if (!delta || typeof delta !== 'object') {
    return { code: 'MALFORMED_DELTA', reason: 'delta is null or not an object' };
  }
  if (!Array.isArray(delta.entities)) {
    return { code: 'MALFORMED_DELTA', reason: `tick ${delta.tick_id}: entities is not an array` };
  }
  if (typeof delta.timestamp !== 'string' || !delta.timestamp) {
    return { code: 'MALFORMED_DELTA', reason: `tick ${delta.tick_id}: timestamp missing or not a string` };
  }

  // Broken trace_id
  if (!delta.trace_id || typeof delta.trace_id !== 'string') {
    return { code: 'BROKEN_TRACE_ID', reason: `tick ${delta.tick_id}: trace_id is missing or not a string` };
  }
  if (delta.trace_id !== trace_id) {
    return { code: 'BROKEN_TRACE_ID', reason: `tick ${delta.tick_id}: trace_id mismatch — expected "${trace_id}" got "${delta.trace_id}"` };
  }

  // Invalid tick_id
  if (!Number.isInteger(delta.tick_id) || delta.tick_id < 1) {
    return { code: 'MALFORMED_DELTA', reason: `tick_id must be a positive integer, got: ${delta.tick_id}` };
  }

  // Per-entity checks
  for (let i = 0; i < delta.entities.length; i++) {
    const e      = delta.entities[i];
    const prefix = `tick ${delta.tick_id} entity[${i}] (id=${e?.id})`;

    if (!e || typeof e !== 'object') {
      return { code: 'MALFORMED_DELTA', reason: `${prefix}: entity is not an object` };
    }
    if (!e.id || typeof e.id !== 'string') {
      return { code: 'MALFORMED_DELTA', reason: `${prefix}: id missing or not a string` };
    }

    // Missing entity state
    if (!e.state || !VALID_STATES.has(e.state)) {
      return { code: 'MISSING_ENTITY_STATE', reason: `${prefix}: state "${e.state}" is missing or invalid (must be active|idle|stopped|destroyed)` };
    }

    // Invalid position shape
    const p = e.position;
    if (!p || typeof p !== 'object' || Array.isArray(p)) {
      return { code: 'INVALID_POSITION', reason: `${prefix}: position must be {x,y,z} object, got: ${JSON.stringify(p)}` };
    }
    if (typeof p.x !== 'number' || !isFinite(p.x) ||
        typeof p.y !== 'number' || !isFinite(p.y) ||
        typeof p.z !== 'number' || !isFinite(p.z)) {
      return { code: 'INVALID_POSITION', reason: `${prefix}: position {x,y,z} must be finite numbers, got: ${JSON.stringify(p)}` };
    }
  }

  return null;  // valid
}

module.exports = { compute, snapshot, validate };
