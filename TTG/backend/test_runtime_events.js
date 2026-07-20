/**
 * Test Runtime Event Model
 * Demonstrates event creation, validation, and usage
 */

const {
  EVENT_TYPES,
  ENTITY_TYPES,
  validateRuntimeEvent,
  createCollisionEvent,
  createScoreUpdateEvent,
  createEntitySpawnedEvent,
  createTimerExpiredEvent,
  createPickupCollectedEvent,
  parseEngineEvent,
  isCriticalEvent
} = require('./events/runtimeEvents');

console.log('=== Runtime Event Model Test ===\n');

// Test 1: Create collision event
console.log('Test 1: Collision Event');
const collisionEvent = createCollisionEvent('player', 'obstacle_01', {
  velocity: 3.2,
  position: { x: 10.5, y: 2.0, z: 0.0 },
  collision_force: 5.8,
  entity_type: ENTITY_TYPES.OBSTACLE,
  damage: 1,
  gameSessionId: 'session_abc123',
  metadata: {
    engine_id: 'engine_local_01',
    user_id: 'user_123',
    game_mode: 'runner'
  }
});
console.log(JSON.stringify(collisionEvent, null, 2));
console.log('Valid:', validateRuntimeEvent(collisionEvent).valid);
console.log('Critical:', isCriticalEvent(collisionEvent));
console.log();

// Test 2: Create score update event
console.log('Test 2: Score Update Event');
const scoreEvent = createScoreUpdateEvent(150, {
  position: { x: 25.0, y: 0.0, z: 0.0 },
  gameSessionId: 'session_abc123',
  metadata: {
    engine_id: 'engine_local_01',
    user_id: 'user_123',
    game_mode: 'runner'
  }
});
console.log(JSON.stringify(scoreEvent, null, 2));
console.log('Valid:', validateRuntimeEvent(scoreEvent).valid);
console.log('Critical:', isCriticalEvent(scoreEvent));
console.log();

// Test 3: Create entity spawned event
console.log('Test 3: Entity Spawned Event');
const spawnEvent = createEntitySpawnedEvent('enemy_02', ENTITY_TYPES.ENEMY, {
  position: { x: 50.0, y: 0.0, z: 0.0 },
  gameSessionId: 'session_abc123',
  metadata: {
    engine_id: 'engine_local_01',
    user_id: 'user_123',
    game_mode: 'runner'
  }
});
console.log(JSON.stringify(spawnEvent, null, 2));
console.log('Valid:', validateRuntimeEvent(spawnEvent).valid);
console.log();

// Test 4: Create timer expired event
console.log('Test 4: Timer Expired Event');
const timerEvent = createTimerExpiredEvent(0, {
  gameSessionId: 'session_abc123',
  metadata: {
    engine_id: 'engine_local_01',
    user_id: 'user_123',
    game_mode: 'runner'
  }
});
console.log(JSON.stringify(timerEvent, null, 2));
console.log('Valid:', validateRuntimeEvent(timerEvent).valid);
console.log('Critical:', isCriticalEvent(timerEvent));
console.log();

// Test 5: Create pickup collected event
console.log('Test 5: Pickup Collected Event');
const pickupEvent = createPickupCollectedEvent('coin_05', {
  position: { x: 30.0, y: 1.0, z: 0.0 },
  score: 10,
  gameSessionId: 'session_abc123',
  metadata: {
    engine_id: 'engine_local_01',
    user_id: 'user_123',
    game_mode: 'runner'
  }
});
console.log(JSON.stringify(pickupEvent, null, 2));
console.log('Valid:', validateRuntimeEvent(pickupEvent).valid);
console.log();

// Test 6: Parse legacy engine event
console.log('Test 6: Parse Legacy Engine Event');
const legacyEvent = {
  type: 'collision',
  id: 'evt_legacy_001',
  ts: Date.now(),
  sessionId: 'session_xyz',
  entities: ['player', 'wall'],
  data: {
    velocity: 2.5,
    position: { x: 5, y: 0, z: 0 }
  }
};
const parsedEvent = parseEngineEvent(legacyEvent);
console.log('Legacy format:', JSON.stringify(legacyEvent, null, 2));
console.log('Parsed format:', JSON.stringify(parsedEvent, null, 2));
console.log('Valid:', validateRuntimeEvent(parsedEvent).valid);
console.log();

// Test 7: Validation errors
console.log('Test 7: Invalid Event Validation');
const invalidEvent = {
  event_type: 'invalid_type',
  timestamp: 'not_a_number',
  entities: 'not_an_array'
};
const validation = validateRuntimeEvent(invalidEvent);
console.log('Valid:', validation.valid);
console.log('Errors:', validation.errors);
console.log();

// Test 8: Event type enumeration
console.log('Test 8: Available Event Types');
console.log('Event Types:', Object.values(EVENT_TYPES));
console.log('Entity Types:', Object.values(ENTITY_TYPES));
console.log();

console.log('=== All Tests Complete ===');
