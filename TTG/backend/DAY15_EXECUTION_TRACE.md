# Execution Trace Example

## Complete Execution Trace: Fast Runner Game

### Execution Metadata

```json
{
  "execution_id": "exec_e2e_1772609889664_0",
  "trace_id": "trace_e2e_1772609889664",
  "user_id": "test_user",
  "created_at": "2024-01-02T10:31:29.664Z"
}
```

### User Intent

```json
{
  "prompt": "Make a fast runner with jump and obstacles",
  "extracted_intent": {
    "genre": "runner",
    "pacing": "fast",
    "difficulty": "medium",
    "abilities": ["jump"],
    "obstacles": true,
    "pickups": false
  }
}
```

### Compiled Schema

```json
{
  "game_mode": "runner",
  "movement": {
    "speed": 8,
    "jump_height": 5
  },
  "physics": {
    "gravity": -9.8
  },
  "spawn_rules": {
    "obstacles": 2,
    "frequency": 1.5
  },
  "score_rules": {
    "distance": 1,
    "collectibles": 0
  },
  "end_conditions": ["collision"],
  "player_params": {
    "jetpack": false,
    "health": 3
  }
}
```

### Security Credentials

```json
{
  "timestamp": 1772609889664,
  "nonce": "a3f7c9e1d2b4f8a6c5e9d7b3f1a8c6e4",
  "signature": "8f3a9c7e5d1b6f4a2c8e0d9b7f5a3c1e6d4b2f8a0c7e5d3b1f9a7c5e3d1b8f6a4"
}
```

---

## Execution Timeline

### Phase 1: Submission (0-100ms)

#### T+0ms: Request Received
```json
{
  "event": "request_received",
  "timestamp": 1772609889664,
  "endpoint": "POST /core/execute",
  "payload_size": 512,
  "client_ip": "127.0.0.1"
}
```

#### T+5ms: Security Validation Started
```json
{
  "event": "security_validation_started",
  "timestamp": 1772609889669,
  "checks": [
    "signature_validation",
    "nonce_check",
    "timestamp_validation"
  ]
}
```

#### T+10ms: Signature Validated
```json
{
  "event": "signature_validated",
  "timestamp": 1772609889674,
  "result": "valid",
  "algorithm": "HMAC-SHA256",
  "expected": "8f3a9c7e...",
  "received": "8f3a9c7e..."
}
```

#### T+12ms: Nonce Checked
```json
{
  "event": "nonce_checked",
  "timestamp": 1772609889676,
  "nonce": "a3f7c9e1d2b4f8a6c5e9d7b3f1a8c6e4",
  "status": "unused",
  "action": "consumed"
}
```

#### T+15ms: Timestamp Validated
```json
{
  "event": "timestamp_validated",
  "timestamp": 1772609889679,
  "request_time": 1772609889664,
  "server_time": 1772609889679,
  "delta_ms": 15,
  "window_ms": 30000,
  "result": "valid"
}
```

#### T+20ms: Security Validation Passed
```json
{
  "event": "security_validation_passed",
  "timestamp": 1772609889684,
  "duration_ms": 15,
  "all_checks_passed": true
}
```

#### T+25ms: Execution Registered
```json
{
  "event": "execution_registered",
  "timestamp": 1772609889689,
  "execution_id": "exec_e2e_1772609889664_0",
  "trace_id": "trace_e2e_1772609889664",
  "status": "received"
}
```

#### T+30ms: Response Sent
```json
{
  "event": "response_sent",
  "timestamp": 1772609889694,
  "status_code": 200,
  "response": {
    "success": true,
    "execution_id": "exec_e2e_1772609889664_0",
    "status": "received",
    "message": "Execution schema accepted and queued for dispatch"
  }
}
```

---

### Phase 2: Dispatch (100-200ms)

#### T+100ms: Dispatch Started
```json
{
  "event": "dispatch_started",
  "timestamp": 1772609889764,
  "execution_id": "exec_e2e_1772609889664_0",
  "status": "running"
}
```

#### T+110ms: Schema to Jobs Conversion
```json
{
  "event": "schema_to_jobs_conversion",
  "timestamp": 1772609889774,
  "jobs_created": [
    {
      "job_id": "build_exec_e2e_1772609889664_0",
      "job_type": "BUILD_SCENE",
      "payload": {
        "sceneId": "scene_runner",
        "gravity": [0, -9.8, 0]
      }
    },
    {
      "job_id": "spawn_player_exec_e2e_1772609889664_0",
      "job_type": "SPAWN_ENTITY",
      "payload": {
        "id": "player_1",
        "type": "player"
      }
    },
    {
      "job_id": "start_exec_e2e_1772609889664_0",
      "job_type": "START_LOOP",
      "payload": {
        "game_mode": "runner",
        "params": {
          "movement_speed": 8
        }
      }
    }
  ]
}
```

#### T+120ms: Job 1 Queued
```json
{
  "event": "job_queued",
  "timestamp": 1772609889784,
  "job_id": "build_exec_e2e_1772609889664_0",
  "job_type": "BUILD_SCENE",
  "queue_position": 1,
  "status": "queued"
}
```

#### T+125ms: Job 2 Queued
```json
{
  "event": "job_queued",
  "timestamp": 1772609889789,
  "job_id": "spawn_player_exec_e2e_1772609889664_0",
  "job_type": "SPAWN_ENTITY",
  "queue_position": 2,
  "status": "queued"
}
```

#### T+130ms: Job 3 Queued
```json
{
  "event": "job_queued",
  "timestamp": 1772609889794,
  "job_id": "start_exec_e2e_1772609889664_0",
  "job_type": "START_LOOP",
  "queue_position": 3,
  "status": "queued"
}
```

#### T+150ms: Dispatch Completed
```json
{
  "event": "dispatch_completed",
  "timestamp": 1772609889814,
  "execution_id": "exec_e2e_1772609889664_0",
  "jobs_dispatched": 3,
  "duration_ms": 50
}
```

---

### Phase 3: Job Execution (200-2000ms)

#### Job 1: BUILD_SCENE

##### T+200ms: Job Dispatched to Engine
```json
{
  "event": "job_dispatched_to_engine",
  "timestamp": 1772609889864,
  "job_id": "build_exec_e2e_1772609889664_0",
  "job_type": "BUILD_SCENE",
  "target": "engine_local_01"
}
```

##### T+250ms: Job Started
```json
{
  "event": "job_started",
  "timestamp": 1772609889914,
  "job_id": "build_exec_e2e_1772609889664_0",
  "job_type": "BUILD_SCENE",
  "status": "running",
  "engine_id": "engine_local_01"
}
```

##### T+300ms: Job Progress (25%)
```json
{
  "event": "job_progress",
  "timestamp": 1772609889964,
  "job_id": "build_exec_e2e_1772609889664_0",
  "progress": 25,
  "message": "Initializing scene..."
}
```

##### T+400ms: Job Progress (50%)
```json
{
  "event": "job_progress",
  "timestamp": 1772609890064,
  "job_id": "build_exec_e2e_1772609889664_0",
  "progress": 50,
  "message": "Setting up physics..."
}
```

##### T+500ms: Job Progress (75%)
```json
{
  "event": "job_progress",
  "timestamp": 1772609890164,
  "job_id": "build_exec_e2e_1772609889664_0",
  "progress": 75,
  "message": "Configuring lighting..."
}
```

##### T+600ms: Job Completed
```json
{
  "event": "job_completed",
  "timestamp": 1772609890264,
  "job_id": "build_exec_e2e_1772609889664_0",
  "job_type": "BUILD_SCENE",
  "status": "completed",
  "duration_ms": 350,
  "result": {
    "success": true,
    "scene_id": "scene_runner"
  }
}
```

#### Job 2: SPAWN_ENTITY

##### T+650ms: Job Dispatched to Engine
```json
{
  "event": "job_dispatched_to_engine",
  "timestamp": 1772609890314,
  "job_id": "spawn_player_exec_e2e_1772609889664_0",
  "job_type": "SPAWN_ENTITY"
}
```

##### T+700ms: Job Started
```json
{
  "event": "job_started",
  "timestamp": 1772609890364,
  "job_id": "spawn_player_exec_e2e_1772609889664_0",
  "job_type": "SPAWN_ENTITY",
  "status": "running"
}
```

##### T+800ms: Job Progress (50%)
```json
{
  "event": "job_progress",
  "timestamp": 1772609890464,
  "job_id": "spawn_player_exec_e2e_1772609889664_0",
  "progress": 50,
  "message": "Creating player entity..."
}
```

##### T+1000ms: Job Completed
```json
{
  "event": "job_completed",
  "timestamp": 1772609890664,
  "job_id": "spawn_player_exec_e2e_1772609889664_0",
  "job_type": "SPAWN_ENTITY",
  "status": "completed",
  "duration_ms": 300,
  "result": {
    "success": true,
    "entity_id": "player_1"
  }
}
```

#### Job 3: START_LOOP

##### T+1050ms: Job Dispatched to Engine
```json
{
  "event": "job_dispatched_to_engine",
  "timestamp": 1772609890714,
  "job_id": "start_exec_e2e_1772609889664_0",
  "job_type": "START_LOOP"
}
```

##### T+1100ms: Job Started
```json
{
  "event": "job_started",
  "timestamp": 1772609890764,
  "job_id": "start_exec_e2e_1772609889664_0",
  "job_type": "START_LOOP",
  "status": "running"
}
```

##### T+1200ms: Game Loop Started
```json
{
  "event": "game_loop_started",
  "timestamp": 1772609890864,
  "game_mode": "runner",
  "movement_speed": 8,
  "initial_state": {
    "score": 0,
    "lives": 3,
    "fps": 60
  }
}
```

##### T+1500ms: Job Completed
```json
{
  "event": "job_completed",
  "timestamp": 1772609891164,
  "job_id": "start_exec_e2e_1772609889664_0",
  "job_type": "START_LOOP",
  "status": "completed",
  "duration_ms": 400,
  "result": {
    "success": true,
    "game_started": true
  }
}
```

---

### Phase 4: Completion (2000ms+)

#### T+1600ms: All Jobs Completed Check
```json
{
  "event": "all_jobs_completed_check",
  "timestamp": 1772609891264,
  "execution_id": "exec_e2e_1772609889664_0",
  "jobs_total": 3,
  "jobs_completed": 3,
  "jobs_failed": 0,
  "all_completed": true
}
```

#### T+1617ms: Execution Completed
```json
{
  "event": "execution_completed",
  "timestamp": 1772609891281,
  "execution_id": "exec_e2e_1772609889664_0",
  "trace_id": "trace_e2e_1772609889664",
  "status": "completed",
  "total_duration_ms": 1617,
  "jobs": {
    "total": 3,
    "completed": 3,
    "failed": 0
  }
}
```

#### T+1620ms: Socket.IO Event Emitted
```json
{
  "event": "socket_event_emitted",
  "timestamp": 1772609891284,
  "event_name": "execution:completed",
  "payload": {
    "execution_id": "exec_e2e_1772609889664_0",
    "trace_id": "trace_e2e_1772609889664",
    "duration": 1617
  }
}
```

---

## Summary Statistics

```json
{
  "execution_summary": {
    "execution_id": "exec_e2e_1772609889664_0",
    "trace_id": "trace_e2e_1772609889664",
    "status": "completed",
    "total_duration_ms": 1617,
    "phases": {
      "submission": {
        "duration_ms": 100,
        "events": 8
      },
      "dispatch": {
        "duration_ms": 100,
        "events": 6
      },
      "execution": {
        "duration_ms": 1400,
        "events": 18
      },
      "completion": {
        "duration_ms": 17,
        "events": 3
      }
    },
    "jobs": {
      "total": 3,
      "completed": 3,
      "failed": 0,
      "average_duration_ms": 350
    },
    "security": {
      "signature_valid": true,
      "nonce_consumed": true,
      "timestamp_valid": true
    },
    "performance": {
      "submission_to_dispatch_ms": 100,
      "dispatch_to_first_job_ms": 100,
      "first_job_to_last_job_ms": 1300,
      "last_job_to_completion_ms": 117
    }
  }
}
```

---

## Telemetry Stream (During Execution)

```json
[
  {
    "timestamp": 1772609891300,
    "type": "game_telemetry",
    "data": {
      "fps": 60,
      "score": 0,
      "lives": 3,
      "duration": 0.1
    }
  },
  {
    "timestamp": 1772609891400,
    "type": "game_telemetry",
    "data": {
      "fps": 59,
      "score": 16,
      "lives": 3,
      "duration": 0.2
    }
  },
  {
    "timestamp": 1772609891500,
    "type": "game_telemetry",
    "data": {
      "fps": 60,
      "score": 32,
      "lives": 3,
      "duration": 0.3
    }
  }
]
```
