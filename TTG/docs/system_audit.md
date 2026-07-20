## 1. Project Purpose
This system is a real-time interaction hub designed to track authenticated
multi-user activity, enforce secure action submission, manage live presence,
and orchestrate automated agents in response to user behavior. It serves as
a foundation for future integrations such as VR clients and behavior analysis
systems.

## 2. Backend Overview

### Entry Point
The backend is initialized via a single server entry file that configures
Express, Socket.IO, security middleware, presence tracking, action ingestion,
and agent orchestration. This file acts as the real-time gateway and must not
be modified without full system understanding.

### Core Backend Modules
- auth/
  - socketAuth.js: JWT validation for socket connections
  - signature.js: HMAC/RSA signature verification for actions
- security/
  - heartbeat_monitor.js: validates agent heartbeat signals
  - nonce_registry.js: rotating nonce management per agent
- state/
  - userStates.js: in-memory per-user behavioral state tracking
- orchestrator/
  - multiAgentOrchestrator.js: evaluates actions and triggers agent responses
- eventBus.js: central pub/sub mechanism for actions
- jobQueue.js: async job handling with per-user updates

## Known Backend Gaps

- Presence and user state are stored in memory only
- No persistent storage for action history yet
- Single backend entry file handles multiple responsibilities


## Frontend Audit

### Entry Point
- File: App.jsx
- Responsibility: initializes socket connection, manages global UI state,
  handles presence detection, and coordinates all dashboard panels.

### Socket Handling
- Socket initialized in: frontend/socket.js
- JWT token stored in localStorage
- refreshSocketAuth() used after token acquisition
- All socket listeners registered in App.jsx

### Active UI Components
- CubePreview
- JsonConfigPanel
- JobQueuePanel
- ActionsPanel
- AgentPanel
- ActionLogPanel
- PresencePanel
- SecurityPanel
- UserPreferencePanel

### Real-Time Events Consumed
- presence_update
- action_update
- agent_update
- job_status
- agent_nonce
- action_error
- agent_heartbeat_result
- hint_deprioritized
- nav_idle_prompt

### Known Frontend Gaps
- JWT userId currently hardcoded for development
- State centralized in App.jsx
- Some agent events require verification (e.g. predict_update)
- Frontend assumes single active session per user


## Real-Time Flow

1. User authenticates via REST and receives a JWT
2. Frontend establishes a Socket.IO connection using the JWT
3. Socket middleware validates the token and assigns user context
4. User is joined to a per-user socket room
5. Presence state is initialized and broadcast to all clients
6. User actions are signed and submitted over the socket
7. Server verifies timestamp, signature, and nonce
8. Verified actions are published to the event bus
9. Orchestrator evaluates actions and produces agent responses
10. Agent updates and action logs are emitted back to the frontend
11. Frontend panels update in real time

## Critical Files (Do Not Break)

- Backend server entry file (Express + Socket.IO gateway)
- eventBus.js
- orchestrator/multiAgentOrchestrator.js
- auth/socketAuth.js
- auth/signature.js
- security/heartbeat_monitor.js
- security/nonce_registry.js
- state/userStates.js
- jobQueue.js
- frontend/App.jsx
- frontend/socket.js

## Dead or Legacy Files

No dead or unused files were identified during the Day 1 audit. All
reviewed frontend and backend files are currently imported and used
by the system. This will be re-evaluated in later phases if changes occur.
