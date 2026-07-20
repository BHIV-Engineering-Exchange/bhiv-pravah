# Runtime Event Model Documentation

## Overview

The Runtime Event Model defines the standard format for events emitted by the game engine during gameplay. These events are the input to the Consequence Compiler, which converts them into engine-safe jobs.

## Architecture

```
Game Engine Runtime
        ↓
Runtime Events (standardized format)
        ↓
Event Validation
        ↓
Consequence Compiler (Day 1b)
        ↓
Engine Jobs
```

## Event Structure

### Standard Format

```json
{
  "event_type": "collision",
  "event_id": "evt_12345678-1234-1234-1234-123456789abc",
  "timestamp": 1738425600000,
  "game_session_id": "session_abc123",
  "entities": ["player", "obstacle_01"],
  "context": {
    "velocity": 3.2,
    "position": { "x": 10.5, "y": 2.0, "z": 0.0 },
    "collision_force": 5.8,
    "entity_type": "obstacle",
    "damage": 1
  },
  "metadata": {
    "engine_id": "engine_local_01",
    "user_id": "user_123",
    "game_mode": "runner"
  }
}
```

### Required Fields

- **event_type** (string): Type of event from EVENT_TYPES enum
- **event_id** (string): Unique identifier (UUID v4)
- **timestamp** (number): Unix timestamp in milliseconds

### Optional Fields

- **game_session_id** (string): ID of the game session
- **entities** (array): List of entity IDs involved
- **context** (object): Event-specific contextual data
- **metadata** (object): Additional metadata for debugging/telemetry

## Event Types

### Core Gameplay Events

| Event Type | Description | Critical |
|------------|-------------|----------|
| `collision` | Two entities collided | Yes |
| `entity_spawned` | New entity created | No |
| `entity_destroyed` | Entity removed from game | No |
| `score_update` | Score changed | No |
| `timer_expired` | Game timer reached zero | Yes |
| `pickup_collected` | Player collected item | No |
| `player_death` | Player died | Yes |
| `level_complete` | Level finished | No |
| `game_start` | Game session started | No |
| `game_end` | Game session ended | Yes |
| `health_changed` | Player health changed | No |
| `position_update` | Entity position changed | No |

### Critical Events

Critical events require immediate processing and cannot be delayed:
- `collision`
- `player_death`
- `game_end`
- `timer_expired`

## Entity Types

- `player` - Player character
- `enemy` - Enemy entities
- `obstacle` - Static/moving obstacles
- `collectible` - Items to collect
- `projectile` - Bullets, missiles, etc.
- `platform` - Platforms, floors, etc.

## Context Fields

### Collision Events
```javascript
{
  velocity: 3.2,              // Speed at collision
  position: { x, y, z },      // Collision location
  collision_force: 5.8,       // Impact force
  entity_type: "obstacle",    // Type of entity hit
  damage: 1                   // Damage dealt
}
```

### Score Events
```javascript
{
  score: 150,                 // New score value
  position: { x, y, z }       // Where score was earned
}
```

### Spawn Events
```javascript
{
  entity_type: "enemy",       // Type of spawned entity
  position: { x, y, z }       // Spawn location
}
```

### Timer Events
```javascript
{
  timer_value: 0              // Final timer value
}
```

## API Reference

### Validation

```javascript
const { validateRuntimeEvent } = require('./events/runtimeEvents');

const validation = validateRuntimeEvent(event);
if (!validation.valid) {
  console.error('Invalid event:', validation.errors);
}
```

### Event Creation

#### Collision Event
```javascript
const { createCollisionEvent, ENTITY_TYPES } = require('./events/runtimeEvents');

const event = createCollisionEvent('player', 'obstacle_01', {
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
```

#### Score Update Event
```javascript
const { createScoreUpdateEvent } = require('./events/runtimeEvents');

const event = createScoreUpdateEvent(150, {
  position: { x: 25.0, y: 0.0, z: 0.0 },
  gameSessionId: 'session_abc123'
});
```

#### Entity Spawned Event
```javascript
const { createEntitySpawnedEvent, ENTITY_TYPES } = require('./events/runtimeEvents');

const event = createEntitySpawnedEvent('enemy_02', ENTITY_TYPES.ENEMY, {
  position: { x: 50.0, y: 0.0, z: 0.0 },
  gameSessionId: 'session_abc123'
});
```

#### Timer Expired Event
```javascript
const { createTimerExpiredEvent } = require('./events/runtimeEvents');

const event = createTimerExpiredEvent(0, {
  gameSessionId: 'session_abc123'
});
```

#### Pickup Collected Event
```javascript
const { createPickupCollectedEvent } = require('./events/runtimeEvents');

const event = createPickupCollectedEvent('coin_05', {
  position: { x: 30.0, y: 1.0, z: 0.0 },
  score: 10,
  gameSessionId: 'session_abc123'
});
```

### Parsing Legacy Events

```javascript
const { parseEngineEvent } = require('./events/runtimeEvents');

// Convert non-standard engine event to standard format
const legacyEvent = {
  type: 'collision',
  ts: Date.now(),
  entities: ['player', 'wall']
};

const standardEvent = parseEngineEvent(legacyEvent);
```

### Critical Event Check

```javascript
const { isCriticalEvent } = require('./events/runtimeEvents');

if (isCriticalEvent(event)) {
  // Process immediately
  processEventNow(event);
} else {
  // Can be queued
  queueEvent(event);
}
```

## Integration with Engine

### Engine Event Emission

The engine should emit events via Socket.IO:

```javascript
// Engine side (Atharva's implementation)
socket.emit('runtime_event', {
  event_type: 'collision',
  event_id: uuidv4(),
  timestamp: Date.now(),
  game_session_id: sessionId,
  entities: ['player', 'obstacle_01'],
  context: {
    velocity: 3.2,
    position: { x: 10.5, y: 2.0, z: 0.0 }
  }
});
```

### Server Event Reception

```javascript
// Server side (backend/engine/engine_socket.js)
engineSocket.on('runtime_event', (rawEvent) => {
  // Parse and validate
  const event = parseEngineEvent(rawEvent);
  const validation = validateRuntimeEvent(event);
  
  if (!validation.valid) {
    console.error('Invalid runtime event:', validation.errors);
    return;
  }
  
  // Pass to Consequence Compiler (Day 1b)
  consequenceCompiler.processEvent(event);
});
```

## Testing

Run the test suite:

```bash
cd backend
node test_runtime_events.js
```

Expected output:
- ✅ Collision event creation and validation
- ✅ Score update event creation
- ✅ Entity spawn event creation
- ✅ Timer expired event creation
- ✅ Pickup collected event creation
- ✅ Legacy event parsing
- ✅ Invalid event detection
- ✅ Event type enumeration

## Schema Validation

The JSON schema is available at:
```
backend/events/runtime_event_schema.json
```

Use it for:
- API documentation
- Client-side validation
- Contract testing
- Code generation

## Next Steps

### Day 1b: Consequence Rules
Define rules that map events to actions:
```json
{
  "on": "collision",
  "if": "player_hits_obstacle",
  "then": ["END_GAME"]
}
```

### Day 1c: Consequence Compiler
Build the compiler that:
1. Receives runtime events
2. Matches consequence rules
3. Generates engine jobs

## Security Considerations

1. **Event Validation**: All events must pass validation before processing
2. **Rate Limiting**: Implement per-session event rate limits
3. **Event Spam Protection**: Detect and reject duplicate events
4. **Timestamp Validation**: Reject events with timestamps too far in past/future
5. **Session Validation**: Verify game_session_id exists and is active

## Performance Considerations

1. **Critical Events**: Process immediately, bypass queue
2. **Non-Critical Events**: Can be batched and processed in groups
3. **Event Deduplication**: Track recent event_ids to prevent duplicates
4. **Memory Management**: Limit event history retention

## Error Handling

```javascript
try {
  const event = parseEngineEvent(rawEvent);
  const validation = validateRuntimeEvent(event);
  
  if (!validation.valid) {
    throw new Error(`Invalid event: ${validation.errors.join(', ')}`);
  }
  
  processEvent(event);
} catch (error) {
  console.error('Event processing error:', error);
  // Log to telemetry
  // Send error response to engine
}
```

## Telemetry

All runtime events should be logged for:
- Gameplay analytics
- Bug reproduction
- Performance monitoring
- Player behavior analysis

```javascript
telemetry.logRuntimeEvent({
  event_type: event.event_type,
  event_id: event.event_id,
  timestamp: event.timestamp,
  game_session_id: event.game_session_id,
  user_id: event.metadata?.user_id
});
```

## Examples

See `backend/test_runtime_events.js` for complete examples of:
- Event creation
- Validation
- Parsing
- Critical event detection
- Error handling

## Support

For questions or issues:
1. Check the schema: `runtime_event_schema.json`
2. Review examples: `test_runtime_events.js`
3. See integration guide above
4. Contact: Rudra (Gameplay Consequence System)
