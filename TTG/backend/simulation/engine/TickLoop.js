'use strict';

/**
 * TickLoop.js
 *
 * Deterministic tick engine. NOT a frame loop, NOT setInterval.
 *
 * Design:
 *   - Runs N ticks synchronously in a single call
 *   - Each tick is identical given the same seed + contract
 *   - Seed is derived from trace_id — same trace = same run
 *   - Provides a seeded RNG for any stochastic behavior (currently unused,
 *     but available so behaviors can use it without breaking determinism)
 *   - Emits a tick_snapshot after every tick for the event log
 *
 * Per-tick order (fixed, non-negotiable):
 *   1. on_tick rules evaluated → action results
 *   2. Rule actions applied to EntityRegistry
 *   3. Behaviors executed per entity → deltas
 *   4. Deltas applied to EntityRegistry
 *   5. Collision detection
 *   6. Zone membership update
 *   7. on_collision rules evaluated (if collisions found)
 *   8. on_zone_enter / on_zone_exit rules evaluated (if zone events found)
 *   9. All events logged to SceneManager
 *  10. Tick snapshot appended
 */

// ─── Seeded RNG (Mulberry32 — fast, deterministic, no deps) ──────────────────

function _makeRng(seed) {
  let s = seed >>> 0;
  return function () {
    s += 0x6D2B79F5;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t ^= t + Math.imul(t ^ (t >>> 7), 61 | t);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ─── Public API ───────────────────────────────────────────────────────────────

class TickLoop {
  /**
   * @param {Object} registry  - EntityRegistry instance
   * @param {Object} scene     - SceneManager instance
   * @param {Object} runtime   - SumScript runtime (from SumScript.parse())
   */
  constructor(registry, scene, runtime) {
    this._registry = registry;
    this._scene    = scene;
    this._runtime  = runtime;
    this._rng      = _makeRng(runtime.contract.seed);
    this._ticks    = [];          // per-tick snapshots
    this._tick     = 0;
  }

  // ── Run ───────────────────────────────────────────────────────────────────

  /**
   * Run exactly `count` ticks synchronously.
   * Returns the array of per-tick snapshots.
   *
   * @param {number} count  - Number of ticks to run
   * @returns {Object[]}    - Per-tick snapshots
   */
  run(count) {
    for (let i = 0; i < count; i++) {
      this._tick++;
      this._runOneTick();
    }
    return this._ticks;
  }

  get currentTick() { return this._tick; }
  get tickSnapshots() { return [...this._ticks]; }

  // ── Single tick ───────────────────────────────────────────────────────────

  _runOneTick() {
    const tick     = this._tick;
    const registry = this._registry;
    const scene    = this._scene;
    const runtime  = this._runtime;

    const entities_map = registry.getLiveMap();
    const simState     = { entities_map, tick, events: scene.getEventLog() };
    const tickEvents   = [];

    // ── Step 1: on_tick rules ─────────────────────────────────────────────
    const ruleResults = runtime.evaluateRules('on_tick', simState);

    // ── Step 2: Apply rule actions to registry ────────────────────────────
    const ruleTransitions = registry.applyRuleActions(ruleResults, tick);
    for (const result of ruleResults) {
      scene.logRuleAction(result, tick);
      tickEvents.push({ source: 'rule', type: result.type, entity_id: result.entity_id });
    }
    for (const t of ruleTransitions) {
      scene.logTransition(t, tick);
    }

    // ── Step 3 + 4: Behaviors → deltas → apply ───────────────────────────
    const context = {
      tick,
      dt:           1,
      entities_map: registry.getLiveMap(),   // live ref — behaviors see current state
      rng:          this._rng
    };

    for (const entity of Object.values(registry.getLiveMap())) {
      // Skip stopped/destroyed entities
      if (entity.state === 'stopped' || entity.state === 'destroyed') continue;

      const delta = runtime.executeBehaviors(entity, context);

      // Log behavior events before applying delta
      for (const evt of delta.events) {
        scene.logBehaviorEvent(evt, tick);
        tickEvents.push({ source: 'behavior', type: evt.type, entity_id: evt.entity_id });
      }

      const { transitions } = registry.applyDelta(entity.id, delta, tick);
      for (const t of transitions) {
        scene.logTransition(t, tick);
        tickEvents.push({ source: 'transition', type: `${t.field}_changed`, entity_id: t.entity_id });
      }
    }

    // ── Step 5: Collision detection ───────────────────────────────────────
    const collisions = scene.detectCollisions(registry.getLiveMap(), 1.0, tick);

    // ── Step 6: Zone membership ───────────────────────────────────────────
    const zoneEvents = scene.updateZones(registry.getLiveMap(), tick);

    // ── Step 7: on_collision rules ────────────────────────────────────────
    if (collisions.length > 0) {
      const colState   = { entities_map: registry.getLiveMap(), tick, events: scene.getEventLog() };
      const colResults = runtime.evaluateRules('on_collision', colState);
      registry.applyRuleActions(colResults, tick);
      for (const r of colResults) scene.logRuleAction(r, tick);
    }

    // ── Step 8: Zone rules ────────────────────────────────────────────────
    for (const ze of zoneEvents) {
      const trigger    = ze.type === 'zone_enter' ? 'on_zone_enter' : 'on_zone_exit';
      const zoneState  = { entities_map: registry.getLiveMap(), tick, events: scene.getEventLog() };
      const zoneResults= runtime.evaluateRules(trigger, zoneState);
      registry.applyRuleActions(zoneResults, tick);
      for (const r of zoneResults) scene.logRuleAction(r, tick);
    }

    // ── Step 9: Increment scene tick counter ──────────────────────────────
    scene.incrementTick();

    // ── Step 10: Tick snapshot ────────────────────────────────────────────
    const snapshot = {
      tick,
      entity_count:    registry.count(),
      events_this_tick: tickEvents.length,
      collisions:      collisions.length,
      zone_events:     zoneEvents.length,
      flags:           Object.keys(registry.getFlags()).length,
      blocked:         Object.keys(registry.getBlocked()).length,
      entity_states:   _summarizeEntities(registry.getLiveMap())
    };

    this._ticks.push(snapshot);
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function _summarizeEntities(entities_map) {
  const out = {};
  for (const [id, e] of Object.entries(entities_map)) {
    out[id] = {
      state:    e.state,
      position: [...e.position],
      velocity: [...e.velocity]
    };
  }
  return out;
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = TickLoop;
