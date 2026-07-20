# Architecture Overview

This document describes the architecture of the Real-time Dashboard system, including
event flow, agent behavior, and security checkpoints.

---

## High-Level Overview

The system is a real-time micro-bridge that connects users to a multi-agent
orchestration layer. Users interact through a dashboard UI, actions are transmitted
via WebSockets, and a central orchestrator evaluates and arbitrates agent responses.

The design emphasizes modularity, real-time behavior, and security discipline.

---

## Core Components

### Frontend (React)
- Real-time dashboard UI
- User action triggers (click, inspect, idle)
- Displays agent decisions, logs, queue status, and security indicators
- Communicates with backend via Socket.IO

### Backend (Node.js + Socket.IO)
- Receives user actions in real time
- Maintains isolated per-user state
- Hosts centralized orchestration and agent arbitration logic
- Enforces security validation before agent evaluation

---

## Event Flow

1. User performs an action in the frontend
2. Action is emitted to the backend via Socket.IO
3. Orchestrator receives the action and performs security validation
4. Validated actions are passed to all registered agents
5. Each agent evaluates the action based on its finite state machine
6. Orchestrator applies priority and cooldown rules to select a single response
7. Final agent decision is emitted back to the frontend

---

## Agent Architecture

Each agent operates independently and follows a finite state machine:

Idle → Watching → Triggered → Cooldown

Agents implemented:
- **HintAgent** – provides contextual hints based on interaction patterns
- **NavAgent** – assists users when idle or disoriented
- **PredictAgent** – predicts likely next actions using simple heuristics
- **RuleAgent** – applies baseline rule-based guidance

The orchestrator ensures:
- Deterministic agent arbitration
- Single-agent response per event
- Cooldown enforcement to prevent spamming

---

## Multi-User Handling

- Each user is identified by a unique `userId`
- User state is isolated and managed independently
- Actions and agent decisions are scoped per user
- Multiple users can interact concurrently without state collision

---

## Security Checkpoints

The system enforces multiple security primitives:

- JWT validation for authenticated communication
- Per-agent HMAC signatures for message integrity
- Nonce tracking to prevent replay attacks
- Agent heartbeats to verify liveness and uptime

All security checks are validated before any agent logic is executed.

---

## Queue & Preview System

- A lightweight job queue simulates long-running tasks
- Job status updates are emitted in real time
- A simple Three.js preview visualizes build state changes

---

## Design Rationale

- Modular agents enable future expansion without refactoring
- Central orchestration prevents agent conflicts
- Event-driven real-time communication mirrors production pipelines
- Security-first design aligns with Sovereign Core principles

---

## Integration Readiness

This module is handover-safe and designed to integrate with:
- TTG Micro-Bridge Layer
- Sovereign Core security interfaces
-   Future multi-agent and preview pipelines
