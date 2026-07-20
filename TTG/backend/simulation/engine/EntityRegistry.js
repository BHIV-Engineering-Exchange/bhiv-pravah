'use strict';

/**
 * EntityRegistry.js
 *
 * Owns all entity state for one simulation run.
 * Single source of truth — nothing else mutates entities directly.
 *
 * Responsibilities:
 *   - Store entities keyed by id
 *   - Apply deltas produced by BehaviorExecutor
 *   - Apply action results produced by RuleEngine (set_state, flag, block)
 *   - Record every state transition with tick + reason
 *   - Expose read-only snapshots
 *
 * What this does NOT do:
 *   - Does not run behaviors
 *   - Does not evaluate rules
 *   - Does not know about ticks or time
 */

// ─── Public API ───────────────────────────────────────────────────────────────

class EntityRegistry {
  constructor() {
    this._entities    = {};   // entity_id → entity state
    this._transitions = [];   // full transition log
    this._flags       = {};   // entity_id → { reason, flagged_at }
    this._blocked     = {};   // entity_id → { reason, blocked_at }
  }

  // ── Load ──────────────────────────────────────────────────────────────────

  /**
   * Load entities from a SumScript entities_map (output of runtime.buildEntitiesMap()).
   * Replaces any existing state — call once at sim init.
   *
   * @param {Object} entities_map  - { [id]: entity }
   */
  load(entities_map) {
    this._entities = {};
    for (const [id, entity] of Object.entries(entities_map)) {
      this._entities[id] = { ...entity };
    }
  }

  // ── Read ──────────────────────────────────────────────────────────────────

  /**
   * Get a read-only snapshot of one entity.
   * Returns null if not found.
   *
   * @param {string} id
   * @returns {Object|null}
   */
  get(id) {
    const e = this._entities[id];
    return e ? Object.freeze({ ...e }) : null;
  }

  /**
   * Get a read-only snapshot of all entities as a plain map.
   * @returns {Object}
   */
  getAll() {
    const out = {};
    for (const [id, e] of Object.entries(this._entities)) {
      out[id] = Object.freeze({ ...e });
    }
    return out;
  }

  /**
   * Get all entities as a live map (for behavior context — read carefully).
   * Used by BehaviorExecutor context only — do not mutate.
   * @returns {Object}
   */
  getLiveMap() {
    return this._entities;
  }

  /**
   * Get all state transitions recorded so far.
   * @returns {Object[]}
   */
  getTransitions() {
    return [...this._transitions];
  }

  /**
   * Get all flagged entities.
   * @returns {Object}
   */
  getFlags() {
    return { ...this._flags };
  }

  /**
   * Get all blocked entities.
   * @returns {Object}
   */
  getBlocked() {
    return { ...this._blocked };
  }

  count() {
    return Object.keys(this._entities).length;
  }

  has(id) {
    return id in this._entities;
  }

  // ── Write — delta application ─────────────────────────────────────────────

  /**
   * Apply a behavior delta to one entity.
   * Delta fields that are null are skipped (not applied).
   *
   * @param {string} entity_id
   * @param {Object} delta      - Output of BehaviorExecutor.executeAll()
   * @param {number} tick
   * @returns {{ changed: boolean, transitions: Object[] }}
   */
  applyDelta(entity_id, delta, tick) {
    const entity = this._entities[entity_id];
    if (!entity) return { changed: false, transitions: [] };

    const transitions = [];

    // position: add velocity to position (integration step)
    if (delta.velocity !== null) {
      const prev = [...entity.position];
      entity.position = [
        entity.position[0] + delta.velocity[0],
        entity.position[1] + delta.velocity[1],
        entity.position[2] + delta.velocity[2]
      ];
      entity.velocity = [...delta.velocity];
      if (_posChanged(prev, entity.position)) {
        transitions.push(_transition(entity_id, 'position', prev, entity.position, tick, 'behavior'));
      }
    }

    if (delta.position !== null) {
      const prev = [...entity.position];
      entity.position = [...delta.position];
      entity.velocity = [0, 0, 0];
      if (_posChanged(prev, entity.position)) {
        transitions.push(_transition(entity_id, 'position', prev, entity.position, tick, 'teleport'));
      }
    }

    if (delta.rotation !== null) {
      entity.rotation = [...delta.rotation];
    }

    if (delta.state !== null && delta.state !== entity.state) {
      const prev = entity.state;
      entity.state = delta.state;
      transitions.push(_transition(entity_id, 'state', prev, delta.state, tick, 'behavior'));
    }

    if (delta.meta !== null) {
      entity.meta = { ...entity.meta, ...delta.meta };
    }

    // Stamp emitted_at on behavior events
    for (const evt of delta.events) {
      evt.emitted_at = tick;
    }

    this._transitions.push(...transitions);
    return { changed: transitions.length > 0, transitions };
  }

  // ── Write — rule action application ──────────────────────────────────────

  /**
   * Apply a list of rule action results to entity state.
   *
   * @param {Object[]} actionResults  - Output of RuleEngine.applyActions()
   * @param {number}   tick
   * @returns {Object[]} transitions
   */
  applyRuleActions(actionResults, tick) {
    const transitions = [];

    for (const result of actionResults) {
      const entity = this._entities[result.entity_id];
      if (!entity) continue;

      switch (result.type) {

        case 'set_state': {
          const prev = entity.state;
          const next = result.payload.state;
          if (prev !== next) {
            entity.state = next;
            const t = _transition(result.entity_id, 'state', prev, next, tick, `rule:${result.rule_id}`);
            transitions.push(t);
            this._transitions.push(t);
          }
          break;
        }

        case 'flag_entity': {
          this._flags[result.entity_id] = {
            reason:     result.payload.reason,
            rule_id:    result.rule_id,
            flagged_at: tick
          };
          const t = _transition(result.entity_id, 'flag', null, 'flagged', tick, `rule:${result.rule_id}`);
          transitions.push(t);
          this._transitions.push(t);
          break;
        }

        case 'block_entity': {
          const prev = entity.state;
          entity.state = 'stopped';
          this._blocked[result.entity_id] = {
            reason:     result.payload.reason,
            rule_id:    result.rule_id,
            blocked_at: tick
          };
          const t = _transition(result.entity_id, 'state', prev, 'stopped', tick, `rule:${result.rule_id}`);
          transitions.push(t);
          this._transitions.push(t);
          break;
        }

        // emit_event and log don't mutate entity state — handled by SceneManager
      }
    }

    return transitions;
  }

  // ── Destroy ───────────────────────────────────────────────────────────────

  /**
   * Mark an entity as destroyed and remove it from active tracking.
   * Transition is recorded.
   *
   * @param {string} entity_id
   * @param {number} tick
   * @param {string} reason
   */
  destroy(entity_id, tick, reason = 'destroyed') {
    const entity = this._entities[entity_id];
    if (!entity) return;

    const prev = entity.state;
    entity.state = 'destroyed';
    const t = _transition(entity_id, 'state', prev, 'destroyed', tick, reason);
    this._transitions.push(t);

    delete this._entities[entity_id];
  }

  /**
   * Reset registry to empty state.
   */
  reset() {
    this._entities    = {};
    this._transitions = [];
    this._flags       = {};
    this._blocked     = {};
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function _transition(entity_id, field, from, to, tick, reason) {
  return { entity_id, field, from, to, tick, reason, recorded_at: Date.now() };
}

function _posChanged(prev, next) {
  return prev[0] !== next[0] || prev[1] !== next[1] || prev[2] !== next[2];
}

// ─── Exports ──────────────────────────────────────────────────────────────────

module.exports = EntityRegistry;
