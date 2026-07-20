# Consequence Compiler Documentation

## Overview

The Consequence Compiler is the core module that converts runtime events into engine-safe jobs. It bridges the gap between gameplay events and engine actions by:

1. Receiving runtime events
2. Matching consequence rules
3. Evaluating conditions
4. Generating engine jobs
5. Dispatching to job queue

## Architecture

```
Runtime Event
    ↓
Validate Event
    ↓
Match Rules
    ↓
Evaluate Conditions
    ↓
Extract Actions
    ↓
Sort by Priority
    ↓
Generate Jobs
    ↓
Dispatch to Queue
    ↓
Engine Execution
```

## API Reference

### Initialize

```javascript
const { initialize } = require('./consequence/consequenceCompiler');

// Initialize compiler (loads rules)
const success = initialize();
```

### Process Event

```javascript
const { processEvent } = require('./consequence/consequenceCompiler');

const result = processEvent(event, {
  gameSessionId: 'session_123',
  userId: 'user_456',
  dispatchImmediately: true
});

// Result:
// {
//   success: true,
//   jobs: [...],
//   matchedRules: 1,
//   critical: true
// }
```

### Process and Dispatch

```javascript
const { processAndDispatch } = require('./consequence/consequenceCompiler');

// Process event and dispatch jobs in one call
const result = processAndDispatch(event, {
  gameSessionId: 'session_123',
  userId: 'user_456'
});

// Result includes dispatch status
// {
//   success: true,
//   jobs: [...],
//   dispatched: 3,
//   dispatchSuccess: true
// }
```

### Get Statistics

```javascript
const { getStatistics } = require('./consequence/consequenceCompiler');

const stats = getStatistics();
// {
//   initialized: true,
//   total_rules: 13,
//   total_actions: 19,
//   rules_by_event: { collision: 3, ... }
// }
```

## Event Processing Flow

### Step 1: Event Validation

```javascript
// Validate event structure
const validation = validateRuntimeEvent(event);
if (!validation.valid) {
  return { success: false, error: validation.errors };
}
```

### Step 2: Critical Detection

```javascript
// Check if event is critical
const critical = isCriticalEvent(event);
// Critical events: collision, player_death, game_end, timer_expired
```

### Step 3: Rule Matching

```javascript
// Get rules for event type
const candidateRules = getRulesForEvent(rules, event.event_type);

// Filter by condition
const matchedRules = candidateRules.filter(rule => {
  return evaluateCondition(rule.if, event);
});
```

### Step 4: Condition Evaluation

```javascript
// Check entity match
const hasAllEntities = condition.entities.every(requiredEntity => {
  return event.entities.includes(requiredEntity);
});

// Check context conditions
const contextMatch = Object.entries(condition.context_checks).every(
  ([key, value]) => event.context[key] === value
);
```

### Step 5: Action Extraction

```javascript
// Extract actions from matched rules
const actions = matchedRules.flatMap(rule => rule.then);
```

### Step 6: Priority Sorting

```javascript
// Sort actions by priority (critical → high → medium → low)
const sortedActions = sortActionsByPriority(actions);
```

### Step 7: Job Generation

```javascript
// Generate engine jobs from actions
const jobs = sortedActions.map((action, index) => ({
  jobId: `${action.action}_${event.event_id}_${index}`,
  jobType: action.action,
  priority: action.priority,
  payload: { ...action.payload, event_type: event.event_type },
  metadata: { rule_id: action.rule_id }
}));
```

### Step 8: Job Dispatch

```javascript
// Dispatch jobs to queue
jobs.forEach(job => {
  addJob(job, handleJobStatusUpdate, null);
});
```

## Examples

### Example 1: Collision Event

**Input Event:**
```javascript
{
  event_type: "collision",
  event_id: "evt_123",
  timestamp: 1738425600000,
  entities: ["player", "obstacle_01"],
  context: {
    velocity: 3.2,
    entity_type: "obstacle"
  }
}
```

**Matched Rule:**
```json
{
  "rule_id": "collision_player_obstacle",
  "on": "collision",
  "if": {
    "condition": "player_hits_obstacle",
    "entities": ["player", "obstacle"],
    "context_checks": { "entity_type": "obstacle" }
  },
  "then": [
    {
      "action": "END_GAME",
      "priority": "critical",
      "payload": { "reason": "collision_with_obstacle" }
    }
  ]
}
```

**Generated Job:**
```javascript
{
  jobId: "end_game_evt_123_0",
  jobType: "END_GAME",
  priority: "critical",
  critical: true,
  payload: {
    reason: "collision_with_obstacle",
    show_game_over: true,
    event_type: "collision",
    event_id: "evt_123",
    final_score: 0,
    game_session_id: "session_123"
  },
  metadata: {
    rule_id: "collision_player_obstacle",
    source: "consequence_compiler"
  }
}
```

### Example 2: Enemy Killed Event

**Input Event:**
```javascript
{
  event_type: "entity_destroyed",
  event_id: "evt_456",
  entities: ["enemy_02"],
  context: {
    entity_type: "enemy",
    position: { x: 50, y: 0, z: 0 }
  }
}
```

**Generated Jobs:**
```javascript
[
  {
    jobType: "UPDATE_SCORE",
    priority: "medium",
    payload: { score_delta: 100, reason: "enemy_killed" }
  },
  {
    jobType: "SPAWN_ENTITY",
    priority: "low",
    payload: { entity_type: "enemy", delay: 2000 }
  },
  {
    jobType: "PLAY_SOUND",
    priority: "low",
    payload: { sound_id: "enemy_death" }
  }
]
```

### Example 3: Pickup Collected Event

**Input Event:**
```javascript
{
  event_type: "pickup_collected",
  event_id: "evt_789",
  entities: ["player", "coin_05"],
  context: {
    entity_type: "collectible",
    score: 10
  }
}
```

**Generated Jobs:**
```javascript
[
  {
    jobType: "UPDATE_SCORE",
    priority: "medium",
    payload: { score_delta: 10, reason: "coin_collected" }
  },
  {
    jobType: "PLAY_SOUND",
    priority: "low",
    payload: { sound_id: "coin_pickup" }
  },
  {
    jobType: "SPAWN_ENTITY",
    priority: "low",
    payload: { entity_type: "collectible", delay: 1000 }
  }
]
```

## Condition Evaluation

### Entity Matching

```javascript
// Exact match
entities: ["player", "obstacle"]
event.entities: ["player", "obstacle_01"]
// ✅ Matches (obstacle_01 contains "obstacle")

// Type match
entities: ["player", "enemy"]
event.entities: ["player", "enemy_02"]
// ✅ Matches (enemy_02 starts with "enemy")
```

### Context Checks

```javascript
// Direct value match
context_checks: { entity_type: "obstacle" }
event.context: { entity_type: "obstacle" }
// ✅ Matches

// Operator-based check
context_checks: { 
  score: { operator: ">=", value: 1000 }
}
event.context: { score: 1500 }
// ✅ Matches (1500 >= 1000)
```

### Supported Operators

- `>=` - Greater than or equal
- `<=` - Less than or equal
- `>` - Greater than
- `<` - Less than
- `==` - Equal
- `!=` - Not equal

## Job Enrichment

The compiler automatically enriches job payloads based on action type:

### END_GAME
```javascript
payload: {
  ...action.payload,
  final_score: event.context?.score || 0,
  game_session_id: event.game_session_id
}
```

### UPDATE_SCORE
```javascript
payload: {
  ...action.payload,
  current_score: event.context?.score || 0,
  position: event.context?.position
}
```

### SPAWN_ENTITY
```javascript
payload: {
  ...action.payload,
  position: event.context?.position || { x: 0, y: 0, z: 0 },
  spawn_reason: event.event_type
}
```

### DAMAGE_PLAYER
```javascript
payload: {
  ...action.payload,
  source_entity: event.entities?.[1] || 'unknown',
  collision_force: event.context?.collision_force || 0
}
```

## Event Handling

### Success Response
```javascript
{
  success: true,
  jobs: [...],
  matchedRules: 1,
  critical: true
}
```

### No Rules Matched
```javascript
{
  success: true,
  jobs: [],
  message: 'No matching rules'
}
```

### Invalid Event
```javascript
{
  success: false,
  jobs: [],
  error: 'Invalid event: Missing required field: event_type'
}
```

### Processing Error
```javascript
{
  success: false,
  jobs: [],
  error: 'Consequence compiler not initialized'
}
```

## Events

The compiler emits events for monitoring:

```javascript
const { consequenceEvents } = require('./consequence/consequenceCompiler');

// Jobs generated
consequenceEvents.on('jobs_generated', (data) => {
  console.log(`Generated ${data.jobs} jobs from ${data.matchedRules} rules`);
});

// Job status updated
consequenceEvents.on('job_status_updated', (data) => {
  console.log(`Job ${data.jobId} → ${data.status}`);
});
```

## Integration

### With Engine Socket

```javascript
// backend/engine/engine_socket.js
const { processAndDispatch } = require('./consequence/consequenceCompiler');

engineSocket.on('runtime_event', (rawEvent) => {
  const result = processAndDispatch(rawEvent, {
    gameSessionId: sessionId,
    userId: userId
  });
  
  if (result.success) {
    console.log(`Dispatched ${result.dispatched} jobs`);
  }
});
```

### With Job Queue

```javascript
// Jobs are automatically dispatched to the queue
const { addJob } = require('./jobQueue');

jobs.forEach(job => {
  addJob(job, handleJobStatusUpdate, null);
});
```

## Testing

Run the test suite:

```bash
cd backend
node test_consequence_compiler.js
```

Expected output:
- ✅ Compiler initialization
- ✅ Collision event processing
- ✅ Enemy killed event processing
- ✅ Pickup collected event processing
- ✅ Timer expired event processing
- ✅ No-match event handling
- ✅ Invalid event rejection
- ✅ Condition evaluation
- ✅ Job structure validation
- ✅ Statistics retrieval
- ✅ Priority ordering
- ✅ Payload enrichment

## Performance

- Event validation: < 1ms
- Rule matching: < 2ms
- Job generation: < 1ms per job
- Total processing: < 5ms per event

## Security

- Event validation prevents malformed data
- Rule-based processing (no code execution)
- Action whitelist enforcement
- Payload sanitization
- No direct engine access

## Error Handling

```javascript
try {
  const result = processEvent(event);
  
  if (!result.success) {
    console.error('Processing failed:', result.error);
    // Handle error
  }
  
  if (result.jobs.length === 0) {
    console.log('No jobs generated');
    // Handle no-op
  }
  
} catch (error) {
  console.error('Unexpected error:', error);
  // Handle exception
}
```

## Best Practices

1. **Always validate events** before processing
2. **Check critical flag** for priority handling
3. **Monitor job dispatch** for failures
4. **Log processing results** for debugging
5. **Handle no-match cases** gracefully
6. **Use event emitters** for monitoring
7. **Test rule changes** thoroughly

## Troubleshooting

### No Rules Matched
- Check event type matches rule `on` field
- Verify entities are present in event
- Check context values match rule conditions

### Invalid Event
- Ensure all required fields present
- Validate event_type is in enum
- Check timestamp is a number

### Jobs Not Dispatched
- Verify job queue is initialized
- Check engine connection status
- Review job dispatcher logs

## Next Steps

### Day 2a: Dispatcher Integration
Integrate consequence compiler with execution dispatcher:
- Add event processing endpoint
- Connect to engine socket
- Handle job lifecycle
- Add telemetry

## Files

- `consequenceCompiler.js` - Main compiler module
- `test_consequence_compiler.js` - Test suite
- `README.md` - This documentation

## Support

For questions or issues:
1. Check the test file for examples
2. Review rule definitions in `consequenceRules.json`
3. See event format in `runtimeEvents.js`
4. Contact: Rudra (Gameplay Consequence System)
