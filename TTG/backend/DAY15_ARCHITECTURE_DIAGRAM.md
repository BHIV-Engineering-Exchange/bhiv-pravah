# System Architecture Diagram

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│                            USER INTERFACE                                │
│                         (React + Vite + Tailwind)                        │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐│
│  │   Intent     │  │  Job Queue   │  │  Execution   │  │   Agent     ││
│  │   Input      │  │   Monitor    │  │   Monitor    │  │   Status    ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘│
│                                                                          │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                    Socket.IO WebSocket
                             │
┌────────────────────────────┴─────────────────────────────────────────────┐
│                                                                           │
│                          BACKEND SERVER                                   │
│                      (Node.js + Express + Socket.IO)                      │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                        HTTP API Layer                                ││
│  │  • POST /api/intent/compile  - Compile prompt to schema             ││
│  │  • POST /core/execute        - Submit execution request             ││
│  │  • GET  /core/execution/:id  - Query execution status               ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                  │                                        │
│                                  ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                       Security Layer                                 ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             ││
│  │  │ HMAC Sig     │  │ Nonce Store  │  │  Timestamp   │             ││
│  │  │ Validation   │  │ (Replay      │  │  Validation  │             ││
│  │  │              │  │  Protection) │  │  (±30s)      │             ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘             ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                  │                                        │
│                                  ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    Execution Pipeline                                ││
│  │                                                                       ││
│  │  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐     ││
│  │  │  Execution   │──────▶│  Dispatcher  │──────▶│  Job Queue   │     ││
│  │  │  Registry    │      │  (Schema →   │      │  (FIFO)      │     ││
│  │  │              │      │   Jobs)      │      │              │     ││
│  │  └──────────────┘      └──────────────┘      └──────────────┘     ││
│  │                                                       │              ││
│  │                                                       ▼              ││
│  │                                              ┌──────────────┐       ││
│  │                                              │ BUILD_SCENE  │       ││
│  │                                              │ SPAWN_ENTITY │       ││
│  │                                              │ START_LOOP   │       ││
│  │                                              └──────────────┘       ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                  │                                        │
│                                  ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                  Socket.IO Engine Namespace                          ││
│  │                        (/engine)                                     ││
│  │  • job:dispatch    - Send jobs to engine                            ││
│  │  • job_started     - Receive job start events                       ││
│  │  • job_completed   - Receive job completion                         ││
│  │  • telemetry       - Receive game telemetry                         ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                           │
└────────────────────────────┬──────────────────────────────────────────────┘
                             │
                    Socket.IO Connection
                             │
┌────────────────────────────┴──────────────────────────────────────────────┐
│                                                                            │
│                          PYTHON BRIDGE                                     │
│                       (python_bridge.py)                                   │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐│
│  │                    Bidirectional Forwarding                           ││
│  │                                                                        ││
│  │  Backend (Socket.IO) ◄──────────────────────────► Engine (WebSocket) ││
│  │                                                                        ││
│  │  • Receives jobs from backend                                         ││
│  │  • Forwards to engine via WebSocket                                   ││
│  │  • Receives telemetry from engine                                     ││
│  │  • Forwards to backend via Socket.IO                                  ││
│  │  • HMAC signature generation                                          ││
│  └──────────────────────────────────────────────────────────────────────┘│
│                                                                            │
│  WebSocket Server: ws://localhost:8080                                    │
│                                                                            │
└────────────────────────────┬───────────────────────────────────────────────┘
                             │
                    WebSocket Connection
                             │
┌────────────────────────────┴───────────────────────────────────────────────┐
│                                                                             │
│                          GAME ENGINE                                        │
│                      (fake_cpp_engine.py)                                   │
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │                       Job Processing                                    ││
│  │                                                                          ││
│  │  BUILD_SCENE:                                                           ││
│  │    • Setup physics (gravity)                                            ││
│  │    • Configure lighting                                                 ││
│  │    • Initialize world                                                   ││
│  │                                                                          ││
│  │  SPAWN_ENTITY:                                                          ││
│  │    • Create player entity                                               ││
│  │    • Set transform (position, rotation, scale)                          ││
│  │    • Attach components (mesh, collider, script)                         ││
│  │                                                                          ││
│  │  START_LOOP:                                                            ││
│  │    • Begin game loop                                                    ││
│  │    • Process game logic                                                 ││
│  │    • Stream telemetry (FPS, score, lives)                               ││
│  └────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌──────────┐
│  User    │
│  Types   │
│  Prompt  │
└────┬─────┘
     │
     ▼
┌─────────────────────────────────────────┐
│ "Make a fast runner with jump"          │
└────┬────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Intent Compiler                         │
│  • Extract genre: runner                 │
│  • Extract speed: 8 (fast)               │
│  • Extract abilities: [jump]             │
└────┬────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Compiled Schema (JSON)                  │
│  {                                       │
│    "game_mode": "runner",                │
│    "movement": { "speed": 8 },           │
│    ...                                   │
│  }                                       │
└────┬────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Generate Security Credentials           │
│  • execution_id                          │
│  • trace_id                              │
│  • nonce (random)                        │
│  • timestamp                             │
│  • HMAC signature                        │
└────┬────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  POST /core/execute                      │
│  {                                       │
│    execution_id, trace_id,               │
│    executionSchema,                      │
│    signature, nonce, timestamp           │
│  }                                       │
└────┬────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Security Validation                     │
│  ✓ Signature valid?                      │
│  ✓ Nonce unused?                         │
│  ✓ Timestamp fresh?                      │
└────┬────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Execution Registry                      │
│  • Store execution metadata              │
│  • Status: received                      │
└────┬────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Dispatcher                              │
│  • Convert schema → 3 jobs               │
│  • Status: running                       │
└────┬────────────────────────────────────┘
     │
     ├──────────────┬──────────────┐
     ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ BUILD_   │  │ SPAWN_   │  │ START_   │
│ SCENE    │  │ ENTITY   │  │ LOOP     │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Job Queue                               │
│  • Queue: [job1, job2, job3]             │
│  • Dispatch to engine                    │
└────┬────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Socket.IO → Python Bridge               │
│  • Forward jobs via WebSocket            │
└────┬────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Game Engine                             │
│  • Process BUILD_SCENE                   │
│  • Process SPAWN_ENTITY                  │
│  • Process START_LOOP                    │
│  • Stream telemetry                      │
└────┬────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Telemetry Stream                        │
│  • job_started                           │
│  • job_completed                         │
│  • game_telemetry (FPS, score, lives)   │
└────┬────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Backend Updates                         │
│  • Job status: completed                 │
│  • Execution status: completed           │
│  • Emit Socket.IO events                 │
└────┬────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────┐
│  Frontend Updates                        │
│  • Display completion                    │
│  • Show duration                         │
│  • Update UI panels                      │
└─────────────────────────────────────────┘
```

## Component Interaction

```
Frontend                Backend              Bridge               Engine
   │                       │                    │                    │
   │  Compile Prompt       │                    │                    │
   ├──────────────────────►│                    │                    │
   │                       │                    │                    │
   │  Schema               │                    │                    │
   │◄──────────────────────┤                    │                    │
   │                       │                    │                    │
   │  Execute              │                    │                    │
   ├──────────────────────►│                    │                    │
   │                       │                    │                    │
   │                       │  Validate Security │                    │
   │                       ├───────────┐        │                    │
   │                       │           │        │                    │
   │                       │◄──────────┘        │                    │
   │                       │                    │                    │
   │                       │  Dispatch Jobs     │                    │
   │                       ├───────────┐        │                    │
   │                       │           │        │                    │
   │                       │◄──────────┘        │                    │
   │                       │                    │                    │
   │                       │  job:dispatch      │                    │
   │                       ├───────────────────►│                    │
   │                       │                    │                    │
   │                       │                    │  Forward Job       │
   │                       │                    ├───────────────────►│
   │                       │                    │                    │
   │                       │                    │                    │  Process
   │                       │                    │                    ├─────┐
   │                       │                    │                    │     │
   │                       │                    │                    │◄────┘
   │                       │                    │                    │
   │                       │                    │  job_started       │
   │                       │                    │◄───────────────────┤
   │                       │                    │                    │
   │                       │  job_started       │                    │
   │                       │◄───────────────────┤                    │
   │                       │                    │                    │
   │  job_started          │                    │                    │
   │◄──────────────────────┤                    │                    │
   │                       │                    │                    │
   │                       │                    │  job_completed     │
   │                       │                    │◄───────────────────┤
   │                       │                    │                    │
   │                       │  job_completed     │                    │
   │                       │◄───────────────────┤                    │
   │                       │                    │                    │
   │  execution:completed  │                    │                    │
   │◄──────────────────────┤                    │                    │
   │                       │                    │                    │
```
