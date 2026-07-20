# HANDOVER — Real-Time Micro-Bridge + Multi-Agent Orchestrator Dashboard

---

## 🚀 Quick Start (Fresh Machine)

### Prerequisites
- **Node.js v18+** ([Download](https://nodejs.org))
- **npm v9+** (comes with Node.js)

### One-Command Start

**Windows (PowerShell):**
```powershell
.\start.bat
```

**Windows (Command Prompt):**
```bash
start.bat
```

**Mac/Linux:**
```bash
chmod +x start.sh
./start.sh
```

The script will:
1. Check Node.js installation
2. Install backend dependencies (if needed)
3. Install frontend dependencies (if needed)
4. Create `.env` files from examples
5. Start both servers
6. Open dashboard in browser

**URLs:**
- Backend: `http://localhost:3000`
- Frontend: `http://localhost:5173`

---

##  What Works

### Core Functionality
- Real-time presence tracking (active / idle / disconnected).
- Frontend dashboard shows live updates of actions, agent decisions, job queue, and presence. 
- Multi-agent orchestration (Hint, Nav, Predict, Rule agents) with priority ordering and deterministic final decisions.
- Action bus and collision handling (e.g., spam click deprioritization).
- JWT authentication for socket connections. 

### Security & Audit
- HMAC signatures on actions validated in backend. 
- Timestamp window ensures action freshness. 
- Per-session nonce rotation and anti-replay protection in place. 
- Heartbeat verification for agent liveness. 
- `/health` and `/security/status` endpoints for integration readiness. 

### Job Queue
- Users can submit jobs (e.g., `generate_world`). 
- Backend processes jobs and reports status via socket events.
- Cube preview updates based on job completion. 

### Frontend UI
- Panels for presence, actions, agent events, job queue, and security indicators. 
- Supports multi-user simulation (`/simulate`). 
- Security panel captures:
  - signature failures
  - replay alerts
  - agent nonces
  - heartbeat status.
---

##  What Does *Not* Work

- In-memory state only — state **does not persist** across server restarts.
- Anti-replay protection is session-scoped; replay across reconnects looks like new sessions. 
- No horizontal scalability (e.g., Redis for shared socket state or queue).
- Socket events cannot be invoked via curl (real-time only).  
  (WebSocket tooling required for interactive tests.)

---

##  Known Limitations

- No automated regression testing suite.
- Nonce replay protection does **not** reject replay across reconnects by design to prevent false positives.
- Agent logic does not support dynamic rule reconfiguration at runtime.
- Frontend notifications for certain agent results (e.g., PredictAgent) may lag under high interaction due to event batching.

---

##  Assumptions Made

- Users are identified by a simple userId from JWT (no role/permission tiers).
- Local environment, single server instance — no distributed cluster support.
- Clients resend the same nonce only within the same socket session.
- Security rating values are moderate and not meant for high-risk production (suitable for internal prototypes).

---

##  Integration Notes

### Endpoints
- **GET** `/health` — service status.
- **GET** `/security/status` — security configuration and agent health.
- **POST** `/auth/token` — issues JWT for test users.

### WebSocket Events
| Event | Direction | Description |
|-------|-----------|-------------|
| `action` | client → server | User action submission (signed). |
| `agent_update` | server → client | Agent reaction to actions. |
| `action_error` | server → client | Invalid signature / replay / timestamp fail. |
| `agent_nonce` | server → client | Initial nonce per agent. |
| `agent_heartbeat` | client → server | Heartbeat from agent. |
| `agent_heartbeat_result` | server → client | Heartbeat validation result. |
| `job_status` | server → client | Job queue progress. |
| `presence` | client → server | User presence state. |

---

##  Dependencies

- Node 18+
- Socket.IO
- express, cors
- dotenv
- React frontend
- (optional) Postman/curl for REST checks.

---

##  Deployment Notes

### Fresh Machine Setup
1. Clone repository
2. Run `start.bat` (Windows) or `./start.sh` (Mac/Linux)
3. System auto-installs dependencies and starts servers
4. Dashboard opens at `http://localhost:5173`

### Manual Setup (Alternative)
```bash
# Backend
cd backend
npm install
npm run dev

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Production Deployment
- Use environment variables for secrets (JWT_SECRET, agent HMAC keys).
- Consider persisting state (Redis/Mongo) for production scaling.
- Use a process manager (PM2/docker) for reliability.
- Set `NODE_ENV=production`

### Engine Integration
- Backend exposes socket events for engine connection
- Job queue ready to receive external engine jobs
- Telemetry events logged to `engine/engine_event_log.json`

---

## 📦 Handover Checklist

- [x] One-command startup scripts (`start.bat`, `start.sh`)
- [x] Auto-dependency installation
- [x] Auto `.env` file creation
- [x] Complete documentation (`README.md`, `RUN.md`, `handover.md`)
- [x] Architecture diagrams and security audit
- [x] Multi-user simulator for testing
- [x] Demo Mode for quick demonstration
- [x] Job queue with real-time updates
- [x] Security primitives (JWT, HMAC, nonce, heartbeat)
- [x] Multi-agent orchestration with priority handling

---

## 📞 Support

For questions or issues:
1. Check `README.md` for feature overview
2. Check `RUN.md` for detailed setup
3. Check `docs/architecture.md` for system design
4. Check `docs/security_readiness.md` for security details

---


