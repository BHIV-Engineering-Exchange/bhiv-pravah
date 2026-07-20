# Execution Schema → Job Queue Mapping

## Visual Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: Core Execution Schema                                    │
├─────────────────────────────────────────────────────────────────┤
│ {                                                               │
│   trace_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"            │
│   execution_id: "abc12345"                                     │
│   executionSchema: {                                           │
│     game_mode: "runner",                                       │
│     movement: { speed: 8, jump_height: 5 },                   │
│     physics: { gravity: -9.8 },                               │
│     spawn_rules: { obstacles: 2, frequency: 2 }               │
│   }                                                            │
│ }                                                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                   executionDispatcher.js
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌───────────────┐  ┌────────────────┐  ┌──────────────┐
│ Job 1         │  │ Job 2          │  │ Job 3        │
│ BUILD_SCENE   │  │ SPAWN_ENTITY   │  │ START_LOOP   │
├───────────────┤  ├────────────────┤  ├──────────────┤
│ jobId: build_ │  │ jobId: spawn_  │  │ jobId: start_│
│ traceId: ...  │  │ traceId: ...   │  │ traceId: ... │
│ executionId   │  │ executionId    │  │ executionId  │
│ payload: {    │  │ payload: {     │  │ payload: {   │
│   sceneId,    │  │   id: player_1 │  │   game_mode  │
│   gravity     │  │   type: player │  │   params     │
│ }             │  │ }              │  │ }            │
└───────────────┘  └────────────────┘  └──────────────┘
        ↓                   ↓                   ↓
┌─────────────────────────────────────────────────────────────────┐
│ OUTPUT: Job Queue (jobQueue.js)                                 │
├─────────────────────────────────────────────────────────────────┤
│ Status: queued → dispatched → running → completed               │
│ Retry: Max 2 attempts                                           │
│ Telemetry: Recorded via behaviourRecorder.js                    │
│ Bucket: Written via bucketWriter.js                             │
└─────────────────────────────────────────────────────────────────┘
```

## Field Mapping Table

| Execution Schema Field | Job Type | Job Payload Field |
|------------------------|----------|-------------------|
| `game_mode` | START_LOOP | `payload.game_mode` |
| `movement.speed` | START_LOOP | `payload.params.movement_speed` |
| `movement.jump_height` | SPAWN_ENTITY | `payload.components.script` config |
| `physics.gravity` | BUILD_SCENE | `payload.gravity[1]` |
| `physics.friction` | BUILD_SCENE | `payload.physics.friction` |
| `spawn_rules.obstacles` | START_LOOP | `payload.params.spawn_rules` |
| `spawn_rules.frequency` | START_LOOP | `payload.params.spawn_rules.interval` |
| `score_rules.distance` | START_LOOP | `payload.params.scoring.points_per_second` |
| `score_rules.collectibles` | START_LOOP | `payload.params.scoring.obstacle_bonus` |
| `player_params.health` | START_LOOP | `payload.params.end_condition.value` |
| `camera.type` | BUILD_SCENE | `payload.camera.type` |
| `camera.distance` | BUILD_SCENE | `payload.camera.distance` |

## Execution Lifecycle

```
1. POST /core/execute receives schema
   ↓
2. Validate signature + nonce
   ↓
3. Store in execution registry
   ↓
4. executionDispatcher.mapSchemaToJobs()
   ↓
5. For each job: addJob(job, onStatus)
   ↓
6. jobQueue processes: queued → dispatched → running
   ↓
7. Engine executes job
   ↓
8. Job completes: running → completed
   ↓
9. Write to Bucket (bucketWriter.js)
   ↓
10. Send telemetry (behaviourRecorder.js)
```

## State Tracking

```
Execution Registry:
{
  "abc12345": {
    executionId: "abc12345",
    traceId: "a1b2c3d4-...",
    status: "running",
    jobs: ["build_abc12345", "spawn_player_abc12345", "start_abc12345"],
    startedAt: 1708123456789,
    completedAt: null
  }
}

Job Queue:
{
  "build_abc12345": { status: "completed", ... },
  "spawn_player_abc12345": { status: "completed", ... },
  "start_abc12345": { status: "running", ... }
}
```

## Error Handling

```
Execution Failure Scenarios:

1. Invalid Schema
   → Return 400 Bad Request
   → Do NOT create jobs

2. Signature Validation Failed
   → Return 401 Unauthorized
   → Log security event

3. Job Execution Failed
   → Retry (max 2)
   → If still fails: mark execution as "failed"
   → Write failure to Bucket

4. Engine Disconnected
   → Jobs remain in "queued" state
   → Retry when engine reconnects
```

## Telemetry Events

```
Event: execution_started
{
  event: "execution_started",
  executionId: "abc12345",
  traceId: "a1b2c3d4-...",
  timestamp: 1708123456789,
  schema: { game_mode: "runner", ... }
}

Event: job_dispatched
{
  event: "job_dispatched",
  jobId: "build_abc12345",
  executionId: "abc12345",
  traceId: "a1b2c3d4-...",
  jobType: "BUILD_SCENE"
}

Event: execution_completed
{
  event: "execution_completed",
  executionId: "abc12345",
  traceId: "a1b2c3d4-...",
  duration: 5234,
  jobsCompleted: 3
}
```
