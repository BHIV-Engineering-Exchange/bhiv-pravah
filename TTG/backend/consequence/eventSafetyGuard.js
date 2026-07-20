/**
 * Event Safety Guard
 * Protects the consequence system from:
 *   1. Event spam       - max events per second per session
 *   2. Duplicate events - same event_id seen twice
 *   3. Recursive loops  - action chain that re-triggers itself
 *   4. Invalid types    - event_type not in allowed list
 */

const { EVENT_TYPES } = require('../events/runtimeEvents');

// ─── Config ──────────────────────────────────────────────────────────────────

const CONFIG = {
  // Rate limiting
  MAX_EVENTS_PER_SECOND: 20,       // per session
  MAX_CRITICAL_PER_SECOND: 5,      // critical events are stricter
  RATE_WINDOW_MS: 1000,

  // Duplicate detection
  SEEN_EVENT_TTL_MS: 30_000,       // forget seen IDs after 30 s
  MAX_SEEN_EVENTS: 5000,           // cap memory usage

  // Loop detection
  MAX_CHAIN_DEPTH: 5,              // max rule triggers per originating event
  LOOP_WINDOW_MS: 2000,            // window to detect a loop

  // Timestamp validation
  MAX_EVENT_AGE_MS: 30_000,        // reject events older than 30 s
  MAX_FUTURE_SKEW_MS: 5_000        // reject events more than 5 s in the future
};

// ─── State ────────────────────────────────────────────────────────────────────

// { sessionId → { count, criticalCount, windowStart } }
const rateLimitState = new Map();

// { event_id → expiresAt }
const seenEventIds = new Map();

// { originEventId → { depth, lastSeen } }
const chainDepthTracker = new Map();

// Violation counters for monitoring
const violations = {
  rate_limit: 0,
  duplicate: 0,
  loop: 0,
  invalid_type: 0,
  stale_timestamp: 0,
  future_timestamp: 0
};

// ─── Allowed event types (whitelist) ─────────────────────────────────────────

const ALLOWED_EVENT_TYPES = new Set(Object.values(EVENT_TYPES));

// ─── Cleanup ──────────────────────────────────────────────────────────────────

// Periodically purge expired seen-event IDs to prevent memory leak
setInterval(() => {
  const now = Date.now();
  for (const [id, expiresAt] of seenEventIds) {
    if (now >= expiresAt) seenEventIds.delete(id);
  }
  // Also purge stale chain entries
  for (const [id, entry] of chainDepthTracker) {
    if (now - entry.lastSeen > CONFIG.LOOP_WINDOW_MS * 3) {
      chainDepthTracker.delete(id);
    }
  }
}, 10_000).unref(); // .unref() so this timer never keeps the process alive in tests

// ─── Individual checks ────────────────────────────────────────────────────────

/**
 * 1. Validate event type against whitelist
 */
function checkEventType(event) {
  if (!event.event_type || !ALLOWED_EVENT_TYPES.has(event.event_type)) {
    violations.invalid_type++;
    return {
      allowed: false,
      reason: `invalid_event_type: "${event.event_type}" is not a recognised event type`
    };
  }
  return { allowed: true };
}

/**
 * 2. Validate timestamp – reject stale or future events
 */
function checkTimestamp(event) {
  const now = Date.now();
  const age = now - event.timestamp;

  if (age > CONFIG.MAX_EVENT_AGE_MS) {
    violations.stale_timestamp++;
    return {
      allowed: false,
      reason: `stale_timestamp: event is ${age}ms old (max ${CONFIG.MAX_EVENT_AGE_MS}ms)`
    };
  }

  if (age < -CONFIG.MAX_FUTURE_SKEW_MS) {
    violations.future_timestamp++;
    return {
      allowed: false,
      reason: `future_timestamp: event timestamp is ${-age}ms in the future`
    };
  }

  return { allowed: true };
}

/**
 * 3. Duplicate detection – reject if event_id already seen
 */
function checkDuplicate(event) {
  const id = event.event_id;

  if (seenEventIds.has(id)) {
    violations.duplicate++;
    return {
      allowed: false,
      reason: `duplicate_event: event_id "${id}" already processed`
    };
  }

  // Cap memory before inserting
  if (seenEventIds.size >= CONFIG.MAX_SEEN_EVENTS) {
    // Remove the oldest entry
    const firstKey = seenEventIds.keys().next().value;
    seenEventIds.delete(firstKey);
  }

  seenEventIds.set(id, Date.now() + CONFIG.SEEN_EVENT_TTL_MS);
  return { allowed: true };
}

/**
 * 4. Rate limiting – max events per second per session
 */
function checkRateLimit(event, sessionId) {
  const key = sessionId || event.game_session_id || 'global';
  const now = Date.now();
  const isCritical = ['collision', 'player_death', 'game_end', 'timer_expired']
    .includes(event.event_type);

  let state = rateLimitState.get(key);

  // Reset window if expired
  if (!state || now - state.windowStart >= CONFIG.RATE_WINDOW_MS) {
    state = { count: 0, criticalCount: 0, windowStart: now };
    rateLimitState.set(key, state);
  }

  state.count++;
  if (isCritical) state.criticalCount++;

  if (state.count > CONFIG.MAX_EVENTS_PER_SECOND) {
    violations.rate_limit++;
    return {
      allowed: false,
      reason: `rate_limit: session "${key}" exceeded ${CONFIG.MAX_EVENTS_PER_SECOND} events/s (got ${state.count})`
    };
  }

  if (isCritical && state.criticalCount > CONFIG.MAX_CRITICAL_PER_SECOND) {
    violations.rate_limit++;
    return {
      allowed: false,
      reason: `rate_limit: session "${key}" exceeded ${CONFIG.MAX_CRITICAL_PER_SECOND} critical events/s`
    };
  }

  return { allowed: true };
}

/**
 * 5. Recursive loop detection
 *    Each event carries an optional `origin_event_id` when it was spawned
 *    by a consequence job. We track how deep that chain has gone.
 */
function checkLoopDepth(event) {
  // originId is the root event that started this chain
  const originId = event.metadata?.origin_event_id || event.event_id;
  const now = Date.now();

  let entry = chainDepthTracker.get(originId);

  if (!entry) {
    chainDepthTracker.set(originId, { depth: 1, lastSeen: now });
    return { allowed: true };
  }

  // Reset if outside the loop window (chain has cooled down)
  if (now - entry.lastSeen > CONFIG.LOOP_WINDOW_MS) {
    entry.depth = 1;
    entry.lastSeen = now;
    return { allowed: true };
  }

  entry.depth++;
  entry.lastSeen = now;

  if (entry.depth > CONFIG.MAX_CHAIN_DEPTH) {
    violations.loop++;
    return {
      allowed: false,
      reason: `recursive_loop: origin event "${originId}" has triggered a chain of depth ${entry.depth} (max ${CONFIG.MAX_CHAIN_DEPTH})`
    };
  }

  return { allowed: true };
}

// ─── Main guard ───────────────────────────────────────────────────────────────

/**
 * Run all safety checks on an incoming runtime event.
 *
 * @param {Object} event     - Runtime event object
 * @param {string} sessionId - Optional override for session key
 * @returns {{ allowed: boolean, reason?: string, checks: Object }}
 */
function guardEvent(event, sessionId = null) {
  const checks = {};

  // 1. Event type whitelist
  const typeCheck = checkEventType(event);
  checks.event_type = typeCheck.allowed;
  if (!typeCheck.allowed) {
    return { allowed: false, reason: typeCheck.reason, checks };
  }

  // 2. Timestamp validation
  const tsCheck = checkTimestamp(event);
  checks.timestamp = tsCheck.allowed;
  if (!tsCheck.allowed) {
    return { allowed: false, reason: tsCheck.reason, checks };
  }

  // 3. Duplicate detection
  const dupCheck = checkDuplicate(event);
  checks.duplicate = dupCheck.allowed;
  if (!dupCheck.allowed) {
    return { allowed: false, reason: dupCheck.reason, checks };
  }

  // 4. Rate limiting
  const rateCheck = checkRateLimit(event, sessionId);
  checks.rate_limit = rateCheck.allowed;
  if (!rateCheck.allowed) {
    return { allowed: false, reason: rateCheck.reason, checks };
  }

  // 5. Loop detection
  const loopCheck = checkLoopDepth(event);
  checks.loop_depth = loopCheck.allowed;
  if (!loopCheck.allowed) {
    return { allowed: false, reason: loopCheck.reason, checks };
  }

  return { allowed: true, checks };
}

// ─── Utilities ────────────────────────────────────────────────────────────────

/** Return current violation counters */
function getViolations() {
  return { ...violations };
}

/** Return current config */
function getConfig() {
  return { ...CONFIG };
}

/** Update config values at runtime (useful for tests / tuning) */
function updateConfig(overrides) {
  Object.assign(CONFIG, overrides);
}

/** Reset all state (useful between tests) */
function reset() {
  rateLimitState.clear();
  seenEventIds.clear();
  chainDepthTracker.clear();
  Object.keys(violations).forEach(k => { violations[k] = 0; });
}

module.exports = {
  guardEvent,
  getViolations,
  getConfig,
  updateConfig,
  reset,
  // Expose individual checks for unit testing
  checkEventType,
  checkTimestamp,
  checkDuplicate,
  checkRateLimit,
  checkLoopDepth
};
