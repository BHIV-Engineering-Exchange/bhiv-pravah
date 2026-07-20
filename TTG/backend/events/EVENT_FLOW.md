# Runtime Event Flow Diagram

## Complete Event Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     GAME ENGINE RUNTIME                          │
│                      (Atharva's Code)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Emits Runtime Events
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SOCKET.IO TRANSPORT                           │
│                  socket.emit('runtime_event')                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EVENT RECEPTION LAYER                          │
│              backend/engine/engine_socket.js                     │
│                                                                  │
│  engineSocket.on('runtime_event', (rawEvent) => {               │
│    const event = parseEngineEvent(rawEvent);                    │
│    const validation = validateRuntimeEvent(event);              │
│    if (validation.valid) {                                      │
│      processEvent(event);                                       │
│    }                                                             │
│  });                                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   RUNTIME EVENT MODEL                            │
│              backend/events/runtimeEvents.js                     │
│                                                                  │
│  ✅ Parse Event                                                  │
│  ✅ Validate Structure                                           │
│  ✅ Check Event Type                                             │
│  ✅ Detect Critical Events                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────┴─────────┐
                    │                   │
              Critical?              Standard?
                    │                   │
                    ▼                   ▼
          ┌─────────────────┐   ┌─────────────────┐
          │  IMMEDIATE      │   │  QUEUE FOR      │
          │  PROCESSING     │   │  BATCH          │
          └─────────────────┘   └─────────────────┘
                    │                   │
                    └─────────┬─────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CONSEQUENCE COMPILER                            │
│          backend/consequence/consequenceCompiler.js              │
│                      (Day 1c - TODO)                             │
│                                                                  │
│  1. Match event to consequence rules                            │
│  2. Generate engine-safe jobs                                   │
│  3. Apply safety guards                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     JOB DISPATCHER                               │
│              backend/executionDispatcher.js                      │
│                      (Day 2a - TODO)                             │
│                                                                  │
│  1. Queue generated jobs                                        │
│  2. Dispatch to engine                                          │
│  3. Track job lifecycle                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GAME ENGINE                                  │
│                  Receives & Executes Jobs                        │
│                                                                  │
│  Examples:                                                       │
│  - END_GAME                                                      │
│  - SPAWN_ENEMY                                                   │
│  - UPDATE_SCORE                                                  │
│  - RESET_LEVEL                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Event Type Flow Examples

### Example 1: Collision Event

```
Player hits obstacle
        │
        ▼
Engine emits:
{
  event_type: "collision",
  entities: ["player", "obstacle_01"],
  context: { velocity: 3.2, damage: 1 }
}
        │
        ▼
Runtime Event Model validates ✅
        │
        ▼
Detected as CRITICAL event
        │
        ▼
Immediate processing
        │
        ▼
Consequence Compiler matches rule:
"collision + player + obstacle → END_GAME"
        │
        ▼
Generate job: { jobType: "END_GAME" }
        │
        ▼
Dispatcher sends to engine
        │
        ▼
Game ends
```

### Example 2: Score Update Event

```
Player collects coin
        │
        ▼
Engine emits:
{
  event_type: "pickup_collected",
  entities: ["player", "coin_05"],
  context: { score: 10 }
}
        │
        ▼
Runtime Event Model validates ✅
        │
        ▼
Detected as STANDARD event
        │
        ▼
Queued for batch processing
        │
        ▼
Consequence Compiler matches rule:
"pickup_collected → UPDATE_SCORE + SPAWN_NEXT"
        │
        ▼
Generate jobs:
1. { jobType: "UPDATE_SCORE", score: +10 }
2. { jobType: "SPAWN_ENTITY", type: "coin" }
        │
        ▼
Dispatcher sends to engine
        │
        ▼
Score updates, new coin spawns
```

### Example 3: Timer Expired Event

```
Game timer reaches 0
        │
        ▼
Engine emits:
{
  event_type: "timer_expired",
  context: { timer_value: 0 }
}
        │
        ▼
Runtime Event Model validates ✅
        │
        ▼
Detected as CRITICAL event
        │
        ▼
Immediate processing
        │
        ▼
Consequence Compiler matches rule:
"timer_expired → END_ROUND + SHOW_RESULTS"
        │
        ▼
Generate jobs:
1. { jobType: "END_ROUND" }
2. { jobType: "SHOW_RESULTS" }
        │
        ▼
Dispatcher sends to engine
        │
        ▼
Round ends, results displayed
```

## Event Validation Flow

```
Raw Event from Engine
        │
        ▼
┌─────────────────────┐
│ parseEngineEvent()  │
│                     │
│ - Normalize format  │
│ - Add defaults      │
│ - Generate event_id │
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ validateRuntimeEvent│
│                     │
│ ✓ event_type valid? │
│ ✓ timestamp number? │
│ ✓ event_id exists?  │
│ ✓ entities array?   │
│ ✓ context object?   │
└─────────────────────┘
        │
        ├─── Valid ──────────────────────────┐
        │                                    │
        └─── Invalid ──> Log Error          │
                         Reject Event        │
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │ isCriticalEvent │
                                    │                 │
                                    │ collision?      │
                                    │ player_death?   │
                                    │ game_end?       │
                                    │ timer_expired?  │
                                    └─────────────────┘
                                             │
                                    ┌────────┴────────┐
                                    │                 │
                              Critical          Standard
                                    │                 │
                                    ▼                 ▼
                            Process Now      Queue for Batch
```

## Data Flow

### Input (from Engine)
```javascript
{
  event_type: "collision",
  event_id: "evt_123",
  timestamp: 1738425600000,
  entities: ["player", "obstacle"],
  context: { velocity: 3.2 }
}
```

### Processing (Runtime Event Model)
```javascript
// Parse
const event = parseEngineEvent(rawEvent);

// Validate
const validation = validateRuntimeEvent(event);
// { valid: true, errors: [] }

// Check criticality
const critical = isCriticalEvent(event);
// true
```

### Output (to Consequence Compiler)
```javascript
{
  event_type: "collision",
  event_id: "evt_123",
  timestamp: 1738425600000,
  game_session_id: "session_abc",
  entities: ["player", "obstacle"],
  context: {
    velocity: 3.2,
    position: { x: 10, y: 2, z: 0 },
    collision_force: 5.8,
    entity_type: "obstacle",
    damage: 1
  },
  metadata: {
    engine_id: "engine_local_01",
    user_id: "user_123",
    game_mode: "runner"
  }
}
```

## Integration Points

### 1. Engine Socket (Atharva)
```javascript
// backend/engine/engine_socket.js
engineSocket.on('runtime_event', (rawEvent) => {
  const { parseEngineEvent, validateRuntimeEvent } = require('./events/runtimeEvents');
  
  const event = parseEngineEvent(rawEvent);
  const validation = validateRuntimeEvent(event);
  
  if (!validation.valid) {
    console.error('Invalid event:', validation.errors);
    return;
  }
  
  // Pass to consequence system
  consequenceSystem.processEvent(event);
});
```

### 2. Consequence Compiler (Day 1c - Rudra)
```javascript
// backend/consequence/consequenceCompiler.js
function processEvent(event) {
  // Match rules
  const rules = matchConsequenceRules(event);
  
  // Generate jobs
  const jobs = generateJobsFromRules(rules, event);
  
  // Dispatch
  dispatcher.queueJobs(jobs);
}
```

### 3. Job Dispatcher (Day 2a - Rudra)
```javascript
// backend/executionDispatcher.js
function queueJobs(jobs) {
  jobs.forEach(job => {
    jobQueue.add(job);
  });
}
```

## File Structure

```
backend/
├── events/                          ✅ Day 1a Complete
│   ├── runtimeEvents.js            ✅ Event model
│   ├── runtime_event_schema.json   ✅ JSON schema
│   ├── README.md                    ✅ Documentation
│   ├── DAY1A_DELIVERABLE.md        ✅ Summary
│   └── EVENT_FLOW.md               ✅ This file
│
├── consequence/                     🔄 Day 1b-1c TODO
│   ├── consequenceRules.json       ⏳ Rule definitions
│   ├── consequenceCompiler.js      ⏳ Compiler logic
│   ├── gameplayRules.json          ⏳ Game-specific rules
│   └── eventSafetyGuard.js         ⏳ Safety layer
│
├── engine/
│   └── engine_socket.js            🔄 Integration point
│
└── executionDispatcher.js          🔄 Day 2a integration
```

## Status Legend
- ✅ Complete
- 🔄 Integration needed
- ⏳ TODO (upcoming tasks)

---

**Current Status:** Day 1a Complete ✅  
**Next Step:** Day 1b - Consequence Rule Definition
