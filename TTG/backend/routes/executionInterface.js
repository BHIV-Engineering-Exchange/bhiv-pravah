'use strict';

/**
 * executionInterface.js
 *
 * Phase 4 — Interface Hardening
 *
 * Defines the EXACT plug-and-play interface between pipeline and execution:
 *
 * REQUEST (pipeline → execution):
 *   POST /execute
 *   Headers: X-Trace-Id, X-Execution-Id, X-API-Key
 *   Body: engineExecutionContract_v3 (frozen)
 *
 * RESPONSE (execution → pipeline):
 *   { status: "accepted" | "rejected", trace_id, execution_id }
 *
 * EVENTS (execution → pipeline via socket):
 *   Every event MUST include: trace_id, execution_id, event_type, timestamp, data
 *   No event without trace — rejected silently if trace_id missing
 */

const express = require('express');
const router  = express.Router();

// ── Required contract fields (v3) ─────────────────────────────────────────────
const REQUIRED_FIELDS = ['execution_id', 'trace_id', 'game_mode', 'entities', 'physics', 'scoring'];

// ── POST /execute ─────────────────────────────────────────────────────────────
// Hardened execution entry point.
// Only accepts contracts that passed gateResult.passed === true upstream.
// Validates contract shape, stamps response with exact interface shape.

router.post('/execute', (req, res) => {
  const traceId     = req.headers['x-trace-id'];
  const executionId = req.headers['x-execution-id'];
  const contract    = req.body;

  // ── Header validation ──────────────────────────────────────────────────────
  if (!traceId) {
    return res.status(400).json({
      status:       'rejected',
      trace_id:     null,
      execution_id: executionId || null,
      reason:       'Missing required header: X-Trace-Id'
    });
  }

  if (!executionId) {
    return res.status(400).json({
      status:       'rejected',
      trace_id:     traceId,
      execution_id: null,
      reason:       'Missing required header: X-Execution-Id'
    });
  }

  // ── Contract body validation ───────────────────────────────────────────────
  if (!contract || typeof contract !== 'object') {
    return res.status(400).json({
      status:       'rejected',
      trace_id:     traceId,
      execution_id: executionId,
      reason:       'Request body must be a JSON object (engineExecutionContract_v3)'
    });
  }

  // Validate required fields
  const missing = REQUIRED_FIELDS.filter(f => !contract[f]);
  if (missing.length > 0) {
    return res.status(400).json({
      status:       'rejected',
      trace_id:     traceId,
      execution_id: executionId,
      reason:       `Contract missing required fields: ${missing.join(', ')}`
    });
  }

  // trace_id in body must match header
  if (contract.trace_id !== traceId) {
    return res.status(400).json({
      status:       'rejected',
      trace_id:     traceId,
      execution_id: executionId,
      reason:       `trace_id mismatch: header=${traceId} body=${contract.trace_id}`
    });
  }

  // execution_id in body must match header
  if (contract.execution_id !== executionId) {
    return res.status(400).json({
      status:       'rejected',
      trace_id:     traceId,
      execution_id: executionId,
      reason:       `execution_id mismatch: header=${executionId} body=${contract.execution_id}`
    });
  }

  // game_mode must be valid
  if (!['runner', 'sidescroller', 'open_scene'].includes(contract.game_mode)) {
    return res.status(400).json({
      status:       'rejected',
      trace_id:     traceId,
      execution_id: executionId,
      reason:       `Invalid game_mode: "${contract.game_mode}". Must be runner | sidescroller | open_scene`
    });
  }

  // entities must be non-empty array
  if (!Array.isArray(contract.entities) || contract.entities.length === 0) {
    return res.status(400).json({
      status:       'rejected',
      trace_id:     traceId,
      execution_id: executionId,
      reason:       'entities must be a non-empty array'
    });
  }

  // physics.gravity required
  if (!contract.physics?.gravity || !Array.isArray(contract.physics.gravity)) {
    return res.status(400).json({
      status:       'rejected',
      trace_id:     traceId,
      execution_id: executionId,
      reason:       'physics.gravity is required and must be [x, y, z]'
    });
  }

  // scoring.rules required
  if (!contract.scoring?.rules) {
    return res.status(400).json({
      status:       'rejected',
      trace_id:     traceId,
      execution_id: executionId,
      reason:       'scoring.rules is required'
    });
  }

  // ── Contract accepted ──────────────────────────────────────────────────────
  console.log(`[EXECUTE] ✅ accepted | trace=${traceId} | execution=${executionId} | mode=${contract.game_mode}`);

  return res.status(200).json({
    status:       'accepted',
    trace_id:     traceId,
    execution_id: executionId,
    accepted_at:  Date.now()
  });
});

// ── Event validator ───────────────────────────────────────────────────────────
// Used by engine_socket.js to validate every inbound event from execution layer.
// No event without trace_id is allowed through.

/**
 * Validate an inbound event from the execution layer.
 * Every event must have: trace_id, execution_id, event_type, timestamp, data
 *
 * @param {Object} event
 * @returns {{ valid: boolean, reason?: string }}
 */
function validateEvent(event) {
  if (!event || typeof event !== 'object') {
    return { valid: false, reason: 'event must be an object' };
  }
  if (!event.trace_id) {
    return { valid: false, reason: 'event missing trace_id — no event without trace' };
  }
  if (!event.execution_id) {
    return { valid: false, reason: 'event missing execution_id' };
  }
  if (!event.event_type) {
    return { valid: false, reason: 'event missing event_type' };
  }
  if (!event.timestamp || typeof event.timestamp !== 'number') {
    return { valid: false, reason: 'event missing or invalid timestamp' };
  }
  if (event.data === undefined) {
    return { valid: false, reason: 'event missing data field' };
  }
  return { valid: true };
}

/**
 * Build a structured event envelope.
 * Ensures every event emitted from execution has the required fields.
 *
 * @param {string} event_type
 * @param {string} trace_id
 * @param {string} execution_id
 * @param {Object} data
 * @returns {Object} structured event
 */
function buildEvent(event_type, trace_id, execution_id, data = {}) {
  if (!trace_id) throw new Error(`[INTERFACE] Cannot build event "${event_type}" — trace_id missing`);
  if (!execution_id) throw new Error(`[INTERFACE] Cannot build event "${event_type}" — execution_id missing`);

  return {
    trace_id,
    execution_id,
    event_type,
    timestamp: Date.now(),
    data
  };
}

module.exports = { router, validateEvent, buildEvent };
