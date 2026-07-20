'use strict';

/**
 * SimEngineStream.js
 *
 * Streaming variant of SimEngine.
 *
 * Instead of running all ticks and returning a full result,
 * this engine runs one tick at a time and calls onTick(delta)
 * after each tick with the TANTRA-schema delta payload.
 *
 * The trace_id is ALWAYS taken from the contract — never generated here.
 *
 * Flow:
 *   1. Parse + validate SumScript contract
 *   2. Build entity registry + apply initial transforms
 *   3. Init + start scene
 *   4. For each tick:
 *        a. Run one tick via TickLoop._runOneTick()
 *        b. Compute delta vs previous entity snapshot
 *        c. Call onTick(delta)  ← caller emits over WebSocket
 *   5. Complete scene
 *   6. Call onComplete(summary)
 *
 * On any error: calls onError(err) and stops immediately.
 * No partial continuation after error.
 */

const SumScript      = require('../sumscript');
const EntityRegistry = require('./EntityRegistry');
const SceneManager   = require('./SceneManager');
const TickLoop       = require('./TickLoop');
const delta          = require('./deltaComputer');
const store          = require('../simResultStore');
const registry_      = require('../streamRegistry');  // tick integrity enforcement
const bucket         = require('../../bucketWriter'); // Phase 2: append-only bucket persistence

/**
 * Run a streaming simulation.
 *
 * @param {Object}   rawContract
 * @param {Object}   opts
 * @param {number}   [opts.ticks=10]
 * @param {Function} opts.onTick      - Called with (deltaPayload) after each tick
 * @param {Function} opts.onComplete  - Called with (summary) when all ticks finish
 * @param {Function} opts.onError     - Called with ({ code, reason, trace_id }) on hard fail
 */
function runStream(rawContract, opts = {}) {
  const { onTick, onComplete, onError } = opts;
  const ticks = opts.ticks || 10;
  const isReplay = opts._isReplay === true;  // Phase 2: skip bucket writes during replay

  // ── Step 1: Parse + validate ──────────────────────────────────────────────
  const parsed = SumScript.parse(rawContract);
  if (!parsed.valid) {
    return onError({
      code:     'INVALID_CONTRACT',
      reason:   `Invalid SumScript contract: ${parsed.errors.join('; ')}`,
      trace_id: rawContract?.trace_id || null
    });
  }

  const { runtime }  = parsed;
  const { contract } = runtime;
  const trace_id     = contract.trace_id;  // always from contract — never generated

  // ── Step 2: Build entity registry ────────────────────────────────────────
  const registry = new EntityRegistry();
  const initial_map = runtime.buildEntitiesMap();
  registry.load(initial_map);

  const { entities_map: transformed } = runtime.applyTransforms(registry.getLiveMap());
  registry.load(transformed);

  // ── Step 3: Init + start scene ────────────────────────────────────────────
  const scene = new SceneManager();
  scene.init(contract);
  scene.start();

  // ── Step 4: Tick loop with per-tick delta emission ────────────────────────
  const loop = new TickLoop(registry, scene, runtime);

  let prev_snapshot = delta.snapshot(registry.getAll());
  const emitted_ticks = [];  // ordered record of every delta emitted — used for replay parity

  for (let i = 0; i < ticks; i++) {
    loop._tick++;  // mirror TickLoop.run() — must increment before _runOneTick()
    try {
      loop._runOneTick();
    } catch (err) {
      scene.fail(err.message);
      return onError({
        code:     'TICK_ERROR',
        reason:   `Tick ${loop.currentTick} failed: ${err.message}`,
        trace_id
      });
    }

    const current_map    = registry.getAll();
    const tick_delta     = delta.compute(trace_id, loop.currentTick, current_map, prev_snapshot);
    prev_snapshot        = delta.snapshot(current_map);

    // ── Phase 6: Failure boundary — validate delta before emission ──────────────
    // Hard fail on malformed delta, broken trace_id, missing state, invalid position.
    // No partial stream continuation allowed.
    const fault = delta.validate(tick_delta, trace_id);
    if (fault) {
      scene.fail(fault.reason);
      return onError({
        code:     fault.code,
        reason:   fault.reason,
        trace_id,
        tick_id:  loop.currentTick
      });
    }

    // Phase 3: Tick integrity enforcement (skip during replay — no registry session)
    if (!isReplay) {
      const violation = registry_.recordTick(trace_id, tick_delta.tick_id);
      if (violation) {
        scene.fail(violation.reason);
        return onError({
          code:     violation.code,
          reason:   violation.reason,
          trace_id,
          tick_id:  tick_delta.tick_id,
          expected: violation.expected
        });
      }
    }

    emitted_ticks.push(tick_delta);  // record before emitting
    onTick(tick_delta);

    // Phase 2: append tick to bucket — append-only, survives restart (skip during replay)
    if (!isReplay) bucket.appendStreamTick(trace_id, tick_delta);
  }

  // ── Step 5: Complete ──────────────────────────────────────────────────────
  scene.complete();

  if (!isReplay) {
    // Phase 2: persist contract to bucket — no-op if already exists (idempotent)
    bucket.writeStreamContract(trace_id, rawContract);
    // Persist stream ticks for replay parity — only saves if not already stored (idempotent)
    store.save(trace_id, { ticks_run: ticks, status: 'completed' }, rawContract, emitted_ticks);
  }

  onComplete({
    trace_id,
    execution_id: contract.execution_id,
    ticks_run:    ticks,
    status:       'completed'
  });
}

module.exports = { runStream };
