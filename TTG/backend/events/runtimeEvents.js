/**
 * Runtime Event Model
 * Defines standard format for events emitted by the game engine during gameplay
 * These events will be processed by the Consequence Compiler to generate engine jobs
 */

const { v4: uuidv4 } = require('uuid');

/**
 * Standard Runtime Event Types
 */
const EVENT_TYPES = {
  COLLISION: 'collision',
  ENTITY_SPAWNED: 'entity_spawned',
  ENTITY_DESTROYED: 'entity_destroyed',
  SCORE_UPDATE: 'score_update',
  TIMER_EXPIRED: 'timer_expired',
  PICKUP_COLLECTED: 'pickup_collected',
  PLAYER_DEATH: 'player_death',
  LEVEL_COMPLETE: 'level_complete',
  GAME_START: 'game_start',
  GAME_END: 'game_end',
  HEALTH_CHANGED: 'health_changed',
  POSITION_UPDATE: 'position_update'
};

/**
 * Entity Types
 */
const ENTITY_TYPES = {
  PLAYER: 'player',
  ENEMY: 'enemy',
  OBSTACLE: 'obstacle',
  COLLECTIBLE: 'collectible',
  PROJECTILE: 'projectile',
  PLATFORM: 'platform'
};

/**
 * Validate runtime event structure
 * @param {Object} event - Runtime event to validate
 * @returns {Object} { valid: boolean, errors: string[] }
 */
function validateRuntimeEvent(event) {
  const errors = [];

  // Required fields
  if (!event.event_type) {
    errors.push('Missing required field: event_type');
  } else if (!Object.values(EVENT_TYPES).includes(event.event_type)) {
    errors.push(`Invalid event_type: ${event.event_type}`);
  }

  if (!event.timestamp) {
    errors.push('Missing required field: timestamp');
  } else if (typeof event.timestamp !== 'number') {
    errors.push('timestamp must be a number');
  }

  if (!event.event_id) {
    errors.push('Missing required field: event_id');
  }

  // Optional but recommended fields
  if (event.entities && !Array.isArray(event.entities)) {
    errors.push('entities must be an array');
  }

  if (event.context && typeof event.context !== 'object') {
    errors.push('context must be an object');
  }

  if (event.metadata && typeof event.metadata !== 'object') {
    errors.push('metadata must be an object');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Create a standard runtime event
 * @param {string} eventType - Type of event
 * @param {Object} options - Event options
 * @returns {Object} Formatted runtime event
 */
function createRuntimeEvent(eventType, options = {}) {
  const {
    entities = [],
    context = {},
    metadata = {},
    gameSessionId = null,
    timestamp = Date.now()
  } = options;

  return {
    event_type: eventType,
    event_id: uuidv4(),
    timestamp,
    game_session_id: gameSessionId,
    entities,
    context,
    metadata
  };
}

/**
 * Create a collision event
 * @param {string} entity1 - First entity ID
 * @param {string} entity2 - Second entity ID
 * @param {Object} context - Collision context
 * @returns {Object} Collision event
 */
function createCollisionEvent(entity1, entity2, context = {}) {
  return createRuntimeEvent(EVENT_TYPES.COLLISION, {
    entities: [entity1, entity2],
    context: {
      velocity: context.velocity || 0,
      position: context.position || { x: 0, y: 0, z: 0 },
      collision_force: context.collision_force || 0,
      entity_type: context.entity_type || 'unknown',
      damage: context.damage || 0
    },
    metadata: context.metadata || {},
    gameSessionId: context.gameSessionId
  });
}

/**
 * Create a score update event
 * @param {number} score - New score value
 * @param {Object} context - Score context
 * @returns {Object} Score update event
 */
function createScoreUpdateEvent(score, context = {}) {
  return createRuntimeEvent(EVENT_TYPES.SCORE_UPDATE, {
    entities: ['player'],
    context: {
      score,
      position: context.position || { x: 0, y: 0, z: 0 }
    },
    metadata: context.metadata || {},
    gameSessionId: context.gameSessionId
  });
}

/**
 * Create an entity spawned event
 * @param {string} entityId - ID of spawned entity
 * @param {string} entityType - Type of entity
 * @param {Object} context - Spawn context
 * @returns {Object} Entity spawned event
 */
function createEntitySpawnedEvent(entityId, entityType, context = {}) {
  return createRuntimeEvent(EVENT_TYPES.ENTITY_SPAWNED, {
    entities: [entityId],
    context: {
      entity_type: entityType,
      position: context.position || { x: 0, y: 0, z: 0 }
    },
    metadata: context.metadata || {},
    gameSessionId: context.gameSessionId
  });
}

/**
 * Create an entity destroyed event
 * @param {string} entityId - ID of destroyed entity
 * @param {string} entityType - Type of entity
 * @param {Object} context - Destruction context
 * @returns {Object} Entity destroyed event
 */
function createEntityDestroyedEvent(entityId, entityType, context = {}) {
  return createRuntimeEvent(EVENT_TYPES.ENTITY_DESTROYED, {
    entities: [entityId],
    context: {
      entity_type: entityType,
      position: context.position || { x: 0, y: 0, z: 0 }
    },
    metadata: context.metadata || {},
    gameSessionId: context.gameSessionId
  });
}

/**
 * Create a timer expired event
 * @param {number} timerValue - Final timer value
 * @param {Object} context - Timer context
 * @returns {Object} Timer expired event
 */
function createTimerExpiredEvent(timerValue, context = {}) {
  return createRuntimeEvent(EVENT_TYPES.TIMER_EXPIRED, {
    entities: [],
    context: {
      timer_value: timerValue
    },
    metadata: context.metadata || {},
    gameSessionId: context.gameSessionId
  });
}

/**
 * Create a pickup collected event
 * @param {string} pickupId - ID of collected pickup
 * @param {Object} context - Pickup context
 * @returns {Object} Pickup collected event
 */
function createPickupCollectedEvent(pickupId, context = {}) {
  return createRuntimeEvent(EVENT_TYPES.PICKUP_COLLECTED, {
    entities: ['player', pickupId],
    context: {
      entity_type: 'collectible',
      position: context.position || { x: 0, y: 0, z: 0 },
      score: context.score || 0
    },
    metadata: context.metadata || {},
    gameSessionId: context.gameSessionId
  });
}

/**
 * Parse incoming engine event and convert to standard format
 * @param {Object} rawEvent - Raw event from engine
 * @returns {Object} Standardized runtime event
 */
function parseEngineEvent(rawEvent) {
  // If already in standard format, validate and return
  const validation = validateRuntimeEvent(rawEvent);
  if (validation.valid) {
    return rawEvent;
  }

  // Attempt to convert legacy/non-standard formats
  const standardEvent = {
    event_type: rawEvent.type || rawEvent.event_type || 'unknown',
    event_id: rawEvent.id || rawEvent.event_id || uuidv4(),
    timestamp: rawEvent.timestamp || rawEvent.ts || Date.now(),
    game_session_id: rawEvent.sessionId || rawEvent.game_session_id || null,
    entities: rawEvent.entities || [],
    context: rawEvent.context || rawEvent.data || {},
    metadata: rawEvent.metadata || {}
  };

  return standardEvent;
}

/**
 * Check if event is critical (requires immediate processing)
 * @param {Object} event - Runtime event
 * @returns {boolean} True if event is critical
 */
function isCriticalEvent(event) {
  const criticalEvents = [
    EVENT_TYPES.COLLISION,
    EVENT_TYPES.PLAYER_DEATH,
    EVENT_TYPES.GAME_END,
    EVENT_TYPES.TIMER_EXPIRED
  ];
  return criticalEvents.includes(event.event_type);
}

module.exports = {
  EVENT_TYPES,
  ENTITY_TYPES,
  validateRuntimeEvent,
  createRuntimeEvent,
  createCollisionEvent,
  createScoreUpdateEvent,
  createEntitySpawnedEvent,
  createEntityDestroyedEvent,
  createTimerExpiredEvent,
  createPickupCollectedEvent,
  parseEngineEvent,
  isCriticalEvent
};
