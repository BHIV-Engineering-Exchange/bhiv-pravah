'use strict';

/**
 * SimEngine.js
 *
 * Main simulation engine entry point.
 *
 * Wires together:
 *   SumScript runtime  → contract + behavior/rule/transform execution
 *   EntityRegistry     → entity state + transitions
 *   SceneManager       → scene state + event log + collision + zones
 *   TickLoop           → deterministic tick execution
 *
 * Single public method: run(contract, opts)
 *
 * Flow:
 *   1. Parse + validate SumScript contract
 *   2. Build entity registry from contract
 *   3. Apply initial transforms
 *   4. Init scene
 *   5. Run N ticks via TickLoop
 *   6. Collect final state + event log
 *   7. Return structured SimResult
 *
 * SimResult is the output consumed by:
 *   - NicaiFormatter  (Phase 7)
 *   - SamruddhiFormatter (Phase 7)
 *   - Replay engine
 *   - Bucket artifact writer
 */

const SumScript        = require('../sumscript');
const EntityRegistry   = require('./EntityRegistry');
const SceneManager     = require('./SceneManager');
const TickLoop         = require('./TickLoop');
const stateFormatter   = require('../stateFormatter.v1');

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Run a simulation from a raw SumScript contract.
 *
 * @param {Object} rawContract  - Raw SumScript contract (validated internally)
 * @param {Object} [opts]
 * @param {number} [opts.ticks=10]  - Number of ticks to simulate
 * @returns {SimResult}
 */
function run(rawContract, opts = {}) {
  const ticks = opts.ticks || 10;

  // ── Step 1: Parse + validate ──────────────────────────────────────────────
  const parsed = SumScript.parse(rawContract);
  if (!parsed.valid) {
    return _failResult(null, null, `Invalid SumScript contract: ${parsed.errors.join('; ')}`);
  }

  const { runtime }  = parsed;
  const { contract } = runtime;

  // ── Step 2: Build entity registry ────────────────────────────────────────
  const registry = new EntityRegistry();
  const initial_map = runtime.buildEntitiesMap();
  registry.load(initial_map);

  // ── Step 3: Apply initial transforms ─────────────────────────────────────
  const { entities_map: transformed, events: transform_events } =
    runtime.applyTransforms(registry.getLiveMap());
  registry.load(transformed);

  // ── Step 4: Init scene ────────────────────────────────────────────────────
  const scene = new SceneManager();
  scene.init(contract);

  // Log transform events into scene
  for (const evt of transform_events) {
    scene.logBehaviorEvent({ ...evt, emitted_at: 0 }, 0);
  }

  scene.start();

  // ── Step 5: Run tick loop ─────────────────────────────────────────────────
  const loop = new TickLoop(registry, scene, runtime);

  try {
    loop.run(ticks);
  } catch (err) {
    scene.fail(err.message);
    return _failResult(contract.trace_id, contract.execution_id, `Tick loop error: ${err.message}`);
  }

  // ── Step 6: Complete scene ────────────────────────────────────────────────
  scene.complete();

  // ── Step 7: Build SimResult ───────────────────────────────────────────────
  const final_entities = registry.getAll();
  const snapshot       = scene.snapshot(final_entities);

  // Build raw result — internal shape, not exposed outside engine
  const raw = {
    success:        true,
    trace_id:       contract.trace_id,
    execution_id:   contract.execution_id,
    seed:           contract.seed,
    ticks_run:      ticks,
    entities:       final_entities,
    transitions:    registry.getTransitions(),
    flags:          registry.getFlags(),
    blocked:        registry.getBlocked(),
    event_log:      snapshot.event_log,
    event_count:    snapshot.event_count,
    tick_snapshots: loop.tickSnapshots,
    zones:          snapshot.zones,
    started_at:     snapshot.started_at,
    ended_at:       snapshot.ended_at,
    duration:       snapshot.duration
  };

  // Format to simulationState.v1 — this is what every consumer receives
  return stateFormatter.format(raw);
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function _failResult(trace_id, execution_id, error) {
  return stateFormatter.format({
    success:      false,
    trace_id:     trace_id     || null,
    execution_id: execution_id || null,
    error
  });
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = { run };
