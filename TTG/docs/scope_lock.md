# Scope Lock — Feb 15 Demo

**Hard Freeze Date:** Feb 5, 2025  
**Public Demo Date:** Feb 15, 2025  
**Integration Partner:** Atharva Sharma (OpenGL Engine)

---

## ✅ IN SCOPE (Demo Features)

### Core Real-Time System
- Multi-user presence tracking (active/idle/disconnected)
- WebSocket-based real-time communication
- JWT authentication with handshake validation
- Action event bus with signature validation
- HMAC signatures + nonce replay protection

### Multi-Agent Orchestration
- **HintAgent** — spam detection → hint trigger
- **NavAgent** — idle detection → navigation prompt
- **PredictAgent** — pattern-based heuristics
- **RuleAgent** — backup heuristic
- Agent FSM visualization (Idle → Triggered → Cooldown)
- Agent priority ordering and collision handling

### Engine Integration
- Engine-ready world schema (v1.0 frozen)
- Job queue with strict lifecycle: `queued → dispatched → running → completed → failed`
- Dedicated `/engine` socket namespace
- Bidirectional engine messaging with acknowledgements
- Engine job types: `BUILD_SCENE`, `LOAD_ASSETS`, `SPAWN_ENTITY`
- Sample worlds: forest, desert, ocean, volcano

### Security Layer
- Per-agent key registration
- Per-agent nonce rotation
- Anti-replay table
- Heartbeat validation (agent + engine)
- Security panel showing signature failures, replay alerts, nonces

### Dashboard UI
- Presence Panel
- Actions Panel
- Agent Status Panel (FSM)
- Job Queue Panel
- JSON Config Panel
- 3D Cube Preview (Three.js)
- Security Panel
- User Preferences Panel (compact mode, dark/light, sound)

### Telemetry & Debugging
- Structured event logging
- Behaviour recording per session
- Session summaries
- Engine event telemetry
- Replay-ready deterministic logs

---

## ❌ OUT OF SCOPE (Not in Demo)

### Experimental Features
- AI-driven world generation (LLM integration)
- Dynamic quest generation
- Procedural terrain generation
- Advanced physics simulation
- Multiplayer collision detection

### Complex Engine Features
- Asset streaming
- LOD (Level of Detail) management
- Shader hot-reloading
- Advanced lighting systems
- Post-processing effects

### Advanced Security
- Rate limiting per user
- DDoS protection
- Advanced encryption (TLS termination handled by infra)
- Audit log export

### UI/UX Enhancements
- Mobile responsive design
- Accessibility (ARIA) improvements
- Internationalization (i18n)
- Custom themes beyond dark/light
- Advanced user settings

### Infrastructure
- Horizontal scaling
- Load balancing
- Database persistence (currently in-memory)
- Redis for distributed state
- Docker containerization (handled separately)

---

## 🎯 Demo Flow (One-Click)

**Demo Mode Toggle:**
1. User clicks "Demo Mode"
2. System loads pre-configured world (forest.json)
3. Jobs queued: BUILD_SCENE → LOAD_ASSETS → SPAWN_ENTITY (player, wolf)
4. Jobs dispatched to engine via `/engine` namespace
5. Engine acknowledges and processes
6. Three.js preview updates in real-time
7. Agent reactions visible (NavAgent triggers on idle, HintAgent on spam)
8. Security panel shows all validations passing

**No manual steps. No configuration required.**

---

## 🔒 Frozen Components

**No changes allowed after Feb 5:**
- Engine schema v1.0 (`engine_schema.json`)
- Job lifecycle states
- Security validation logic (JWT, HMAC, nonce)
- Agent FSM states
- Socket event names and payloads

**Bug fixes only:**
- Silent failures
- Race conditions
- Memory leaks
- UI rendering issues

---

## 📦 Handover Deliverables

1. Updated `RUN.md` (one-command startup)
2. `handover.md` (system overview for Atharva)
3. Engine schema documentation
4. Demo rehearsal video
5. System audit report
6. HHG reflection

---

## 🚫 Scope Creep Prevention

**Any request for new features must:**
1. Be approved by Ashmit (Integration Coordinator)
2. Not break existing engine contract
3. Not delay Feb 5 freeze
4. Be documented as "post-demo enhancement"

**Default answer to new features: "Post-demo backlog"**

---

**Signed Off:** Rudra Parmeshwar  
**Date:** Feb 1, 2025  
**Status:** LOCKED
