'use strict';

/**
 * SceneManager.js
 *
 * Owns scene-level state for one simulation run.
 * Works alongside EntityRegistry — registry owns entities,
 * SceneManager owns the scene context around them.
 *
 * Responsibilities:
 *   - Track simulation status (idle → running → completed/failed)
 *   - Maintain the event log (all events emitted during the run)
 *   - Detect collisions between entities (AABB, configurable radius)
 *   - Track zone membership (which entities are inside which zones)
 *   - Produce structured scene snapshots for output / replay
 *
 * What this does NOT do:
 *   - Does not run behaviors or evaluate rules
 *   - Does not own entity state (that's EntityRegistry)
 *   - Does not know about ticks (TickLoop drives it)
 */

const STATUSES = ['idle', 'running', 'completed', 'failed'];

class SceneManager {
  constructor() {
    this._status      = 'idle';
    this._trace_id    = null;
    this._execution_id= null;
    this._seed        = null;
    this._started_at  = null;
    this._ended_at    = null;
    this._event_log   = [];       // all events emitted during the run
    this._zones       = {};       // zone_id → { position[3], radius, members: Set }
    this._tick_count  = 0;
  }

  // ── Lifecycle ─────────────────────────────────────────────────────────────

  /**
   * Initialize scene from a normalized SumScript contract.
   * Must be called before start().
   *
   * @param {Object} contract  - Normalized contract from SumScript.parse()
   */
  init(contract) {
    this._trace_id     = contract.trace_id;
    this._execution_id = contract.execution_id;
    this._seed         = contract.seed;
    this._status       = 'idle';
    this._event_log    = [];
    this._zones        = {};
    this._tick_count   = 0;
    this._started_at   = null;
    this._ended_at     = null;

    // Register zone entities from contract
    for (const entity of contract.entities) {
      if (entity.type === 'zone') {
        this._zones[entity.id] = {
          position: [...entity.position],
          radius:   entity.meta.radius || 10,
          members:  new Set()
        };
      }
    }
  }

  start() {
    this._status     = 'running';
    this._started_at = Date.now();
    this._emitInternal('sim_started', null, {
      trace_id:     this._trace_id,
      execution_id: this._execution_id,
      seed:         this._seed
    });
  }

  complete() {
    this._status   = 'completed';
    this._ended_at = Date.now();
    this._emitInternal('sim_completed', null, {
      tick_count: this._tick_count,
      duration:   this._ended_at - this._started_at,
      event_count: this._event_log.length
    });
  }

  fail(reason) {
    this._status   = 'failed';
    this._ended_at = Date.now();
    this._emitInternal('sim_failed', null, { reason });
  }

  // ── Event log ─────────────────────────────────────────────────────────────

  /**
   * Append a behavior event (from BehaviorExecutor delta.events) to the log.
   *
   * @param {Object} event   - { type, entity_id, payload, emitted_at }
   * @param {number} tick
   */
  logBehaviorEvent(event, tick) {
    this._event_log.push({
      source:    'behavior',
      type:      event.type,
      entity_id: event.entity_id,
      payload:   event.payload,
      tick,
      logged_at: Date.now()
    });
  }

  /**
   * Append a rule action result to the log.
   *
   * @param {Object} actionResult  - Output of RuleEngine.applyActions()
   * @param {number} tick
   */
  logRuleAction(actionResult, tick) {
    this._event_log.push({
      source:    'rule',
      type:      actionResult.type,
      rule_id:   actionResult.rule_id,
      entity_id: actionResult.entity_id,
      payload:   actionResult.payload,
      tick,
      logged_at: Date.now()
    });
  }

  /**
   * Append a transition to the log.
   *
   * @param {Object} transition  - Output of EntityRegistry.applyDelta()
   * @param {number} tick
   */
  logTransition(transition, tick) {
    this._event_log.push({
      source:    'transition',
      type:      `${transition.field}_changed`,
      entity_id: transition.entity_id,
      payload:   { from: transition.from, to: transition.to, reason: transition.reason },
      tick,
      logged_at: Date.now()
    });
  }

  /**
   * Get the full event log (read-only copy).
   * @returns {Object[]}
   */
  getEventLog() {
    return [...this._event_log];
  }

  // ── Collision detection ───────────────────────────────────────────────────

  /**
   * Detect collisions between all active entities using sphere overlap.
   * Returns pairs of colliding entity ids.
   *
   * @param {Object} entities_map  - Live entity map from EntityRegistry
   * @param {number} radius        - Collision radius (default 1.0)
   * @param {number} tick
   * @returns {Object[]} collisions - [{ entity_a, entity_b, distance, tick }]
   */
  detectCollisions(entities_map, radius, tick) {
    const r          = radius || 1.0;
    const ids        = Object.keys(entities_map).filter(id => {
      const e = entities_map[id];
      return e.state !== 'stopped' && e.state !== 'destroyed' && e.type !== 'zone';
    });
    const collisions = [];

    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        const a    = entities_map[ids[i]];
        const b    = entities_map[ids[j]];
        const dist = _distance(a.position, b.position);

        if (dist <= r * 2) {
          const col = { entity_a: ids[i], entity_b: ids[j], distance: dist, tick };
          collisions.push(col);
          this._event_log.push({
            source:    'collision',
            type:      'collision_detected',
            entity_id: ids[i],
            payload:   col,
            tick,
            logged_at: Date.now()
          });
        }
      }
    }

    return collisions;
  }

  // ── Zone tracking ─────────────────────────────────────────────────────────

  /**
   * Update zone membership for all entities.
   * Emits zone_enter / zone_exit events when membership changes.
   *
   * @param {Object} entities_map
   * @param {number} tick
   * @returns {Object[]} zone events
   */
  updateZones(entities_map, tick) {
    const events = [];

    for (const [zone_id, zone] of Object.entries(this._zones)) {
      for (const [entity_id, entity] of Object.entries(entities_map)) {
        if (entity.type === 'zone') continue;

        const dist    = _distance(entity.position, zone.position);
        const inside  = dist <= zone.radius;
        const wasIn   = zone.members.has(entity_id);

        if (inside && !wasIn) {
          zone.members.add(entity_id);
          const evt = { source: 'zone', type: 'zone_enter', entity_id, payload: { zone_id, distance: dist }, tick, logged_at: Date.now() };
          this._event_log.push(evt);
          events.push(evt);
        } else if (!inside && wasIn) {
          zone.members.delete(entity_id);
          const evt = { source: 'zone', type: 'zone_exit', entity_id, payload: { zone_id, distance: dist }, tick, logged_at: Date.now() };
          this._event_log.push(evt);
          events.push(evt);
        }
      }
    }

    return events;
  }

  // ── Tick counter ──────────────────────────────────────────────────────────

  incrementTick() {
    this._tick_count++;
  }

  // ── Snapshot ──────────────────────────────────────────────────────────────

  /**
   * Produce a structured scene snapshot.
   * Used by SimEngine to build the final result and by replay.
   *
   * @param {Object} entities_map  - Current entity state from EntityRegistry
   * @returns {Object} snapshot
   */
  snapshot(entities_map) {
    return {
      trace_id:     this._trace_id,
      execution_id: this._execution_id,
      seed:         this._seed,
      status:       this._status,
      tick_count:   this._tick_count,
      started_at:   this._started_at,
      ended_at:     this._ended_at,
      duration:     this._ended_at && this._started_at
        ? this._ended_at - this._started_at
        : null,
      entities:     entities_map,
      zones:        _serializeZones(this._zones),
      event_count:  this._event_log.length,
      event_log:    [...this._event_log]
    };
  }

  // ── Getters ───────────────────────────────────────────────────────────────

  get status()      { return this._status; }
  get tick_count()  { return this._tick_count; }
  get trace_id()    { return this._trace_id; }
  get execution_id(){ return this._execution_id; }

  // ── Internal ──────────────────────────────────────────────────────────────

  _emitInternal(type, entity_id, payload) {
    this._event_log.push({
      source:    'engine',
      type,
      entity_id: entity_id || null,
      payload,
      tick:      this._tick_count,
      logged_at: Date.now()
    });
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function _distance(a, b) {
  const dx = a[0] - b[0];
  const dy = a[1] - b[1];
  const dz = a[2] - b[2];
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

function _serializeZones(zones) {
  const out = {};
  for (const [id, z] of Object.entries(zones)) {
    out[id] = { position: z.position, radius: z.radius, members: [...z.members] };
  }
  return out;
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = SceneManager;
