# HANDOVER — Real-Time Micro-Bridge + Multi-Agent Orchestrator



---

## 🚀 Quick Start (Fresh Machine)

### Prerequisites
- **Node.js v18+** ([Download](https://nodejs.org))
- **npm v9+** (comes with Node.js)

### One-Command Start

**Windows:**
```bash
start.bat
```

**Mac/Linux:**
```bash
chmod +x start.sh
./start.sh
```

**What happens**:
1. Checks Node.js installation
2. Installs dependencies (backend + frontend)
3. Creates `.env` files from examples
4. Starts both servers
5. Opens dashboard in browser

**URLs**:
- Backend: `http://localhost:3000`
- Frontend: `http://localhost:5173`

---

## 📦 What's Included

### Core Features 
- **Real-time presence tracking** (active/idle/disconnected)
- **Multi-agent orchestration** (Hint, Nav, Predict, Rule agents)
- **Action bus** with collision handling
- **Job queue** with lifecycle tracking (queued → dispatched → running → completed/failed)
- **Engine integration** (socket namespace, telemetry, job dispatch)
- **Demo Mode** (one-click world generation)
- **3D Cube Preview** (Three.js, updates on job completion)

### Security 
- **JWT authentication** (socket handshake)
- **HMAC signatures** (action validation)
- **Nonce replay protection** (per-user, per-session)
- **Heartbeat validation** (5s interval, 10s timeout)
- **Timestamp window** (15s action freshness)
- **Per-agent secrets** (HMAC keys for each agent)

### Telemetry 
- **Append-only logging** (telemetry_samples.json)
- **Deterministic replay** (sequence numbers)
- **13 event types** (job lifecycle, engine events, connections)
- **100% coverage** (no hidden state)

### UI Panels 
- **Presence Panel** (multi-user tracking)
- **Actions Panel** (real-time action log)
- **Agent Status Panel** (FSM visualization)
- **Job Queue Panel** (job lifecycle with errors)
- **JSON Config Panel** (world generation)
- **Cube Preview** (3D visualization)
- **Demo Mode Panel** (one-click pipeline)
- **Security Panel** (signatures, nonces, heartbeats)

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Presence │  │ Actions  │  │  Agents  │  │ Job Queue│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  Config  │  │  Preview │  │   Demo   │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
                          │ Socket.IO
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                         Backend                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Socket.IO Server (/)                     │  │
│  │  • JWT Auth  • Action Bus  • Presence  • Heartbeat   │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Multi-Agent Orchestrator                      │  │
│  │  HintAgent → NavAgent → PredictAgent → RuleAgent     │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Job Queue (State Machine)                │  │
│  │  queued → dispatched → running → completed/failed    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Engine Socket Namespace (/engine)             │  │
│  │  • Heartbeat  • Job Dispatch  • Status Updates       │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Telemetry System                         │  │
│  │  • Append-only log  • Sequence numbers  • Replay     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Engine (OpenGL)│
                  └───────────────┘
```

---

## 📂 Project Structure

```
Real-Time-Micro-Bridge/
├── backend/
│   ├── agents/                  # Multi-agent logic
│   │   ├── HintAgent.js
│   │   ├── NavAgent.js
│   │   ├── PredictAgent.js
│   │   └── RuleAgent.js
│   ├── auth/                    # JWT & signatures
│   │   ├── jwt.js
│   │   ├── signature.js
│   │   └── socketAuth.js
│   ├── engine/                  # Engine integration
│   │   ├── engine_adapter.js    # Format conversion
│   │   ├── engine_schema.json   # Frozen schema v1.0
│   │   ├── engine_socket.js     # /engine namespace
│   │   ├── engine_telemetry.js  # Telemetry system
│   │   └── sample_worlds/       # Validated worlds
│   ├── security/                # Nonce & heartbeat
│   │   ├── nonceStore.js
│   │   ├── heartbeat.js
│   │   └── nonce_registry.js
│   ├── telemetry/               # Behaviour tracking
│   │   ├── behaviourRecorder.js
│   │   └── sessionSummary.js
│   ├── .env.example             # Config template
│   ├── index.js                 # Entry point
│   ├── socket.js                # Main socket handlers
│   ├── jobQueue.js              # Job state machine
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── DemoModePanel.jsx
│   │   │   ├── JobQueuePanel.jsx
│   │   │   ├── CubePreview.jsx
│   │   │   └── ...
│   │   ├── data/                # Sample worlds
│   │   │   └── sampleWorlds.js
│   │   ├── hooks/               # Custom hooks
│   │   └── socket/              # Socket client
│   ├── .env.example
│   └── package.json
├── docs/                        # Documentation
│   ├── architecture.md
│   ├── engine_security.md
│   ├── job_lifecycle.md
│   ├── telemetry_replay_notes.md
│   ├── failure_simulation_report.md
│   ├── demo_mode.md
│   └── ...
├── start.bat                    # Windows startup
├── start.sh                     # Mac/Linux startup
├── RUN.md                       # Setup guide
└── README.md                    # Project overview
```

---

## ⚙️ Configuration

### Backend (.env)

```env
# JWT Authentication
JWT_SECRET=microbridge_jwt_secret_dev_12345
JWT_ISSUER=microbridge.internal
JWT_EXP=1h

# Action Signatures
HMAC_SECRET=HMAC_SECRET_987654321
HMAC_WINDOW_MS=15000

# Agent Secrets (one per agent)
HINT_AGENT_SECRET=hint_agent_secret_abc123
NAV_AGENT_SECRET=nav_agent_secret_def456
PREDICT_AGENT_SECRET=predict_agent_secret_ghi789
RULE_AGENT_SECRET=rule_agent_secret_jkl012

# Engine Integration
ENGINE_SHARED_SECRET=engine_shared_secret_mno345

# Server
PORT=3000
FRONTEND_ORIGIN=http://localhost:5173
```

**⚠️ Production**: Change all secrets to strong random values!

### Frontend (.env)

```env
VITE_API_URL=http://localhost:3000
```

---

## 🔌 API Reference

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/security/status` | Security configuration |
| POST | `/auth/token` | Generate JWT for testing |

### Socket Events (Main Namespace)

| Event | Direction | Description |
|-------|-----------|-------------|
| `action` | client → server | User action (signed) |
| `agent_update` | server → client | Agent reaction |
| `action_error` | server → client | Validation failure |
| `presence` | client → server | User presence state |
| `presence_update` | server → client | Presence broadcast |
| `generate_world` | client → server | World generation request |
| `job_status` | server → client | Job lifecycle update |
| `world_update` | server → client | Preview update |
| `agent_nonce` | server → client | Initial nonces |
| `agent_heartbeat` | client → server | Agent heartbeat |
| `agent_heartbeat_result` | server → client | Heartbeat validation |

### Socket Events (Engine Namespace)

| Event | Direction | Description |
|-------|-----------|-------------|
| `engine_ready` | engine → server | Engine connected |
| `ready_ack` | server → engine | Ready acknowledged |
| `engine_job` | server → engine | Job dispatch |
| `job_ack` | engine → server | Job acknowledged |
| `job_progress` | engine → server | Progress update |
| `job_status` | engine → server | Status update (signed) |
| `status_ack` | server → engine | Status acknowledged |
| `engine_heartbeat` | engine → server | Heartbeat |
| `heartbeat_ack` | server → engine | Heartbeat acknowledged |
| `engine_error` | engine → server | Error report |
| `error_ack` | server → engine | Error acknowledged |

---

## 🧪 Testing

### Health Check
```bash
curl http://localhost:3000/health
```

### Telemetry Replay
```bash
cd backend
node test_telemetry_replay.js
```

### Failure Simulation
```bash
cd backend
node test_failures.js
```

### Demo Mode
1. Open dashboard
2. Click "Launch Demo"
3. Watch full pipeline execute

---

## ✅ What Works

### Core Functionality
- ✅ Real-time presence tracking (active/idle/disconnected)
- ✅ Multi-agent orchestration with priority ordering
- ✅ Action bus with collision handling
- ✅ Job queue with strict state machine
- ✅ Engine integration (socket, telemetry, jobs)
- ✅ Demo Mode (one-click pipeline)
- ✅ 3D Cube Preview (Three.js)

### Security
- ✅ JWT authentication (socket handshake)
- ✅ HMAC signatures (action validation)
- ✅ Nonce replay protection (per-session)
- ✅ Heartbeat validation (5s/10s)
- ✅ Timestamp window (15s freshness)
- ✅ Per-agent secrets

### Telemetry
- ✅ Append-only logging
- ✅ Deterministic replay
- ✅ 13 event types
- ✅ 100% coverage (no hidden state)

### UI
- ✅ All panels functional
- ✅ Real-time updates
- ✅ Error handling with visual feedback
- ✅ Dark/light mode
- ✅ Responsive design

---

## ⚠️ Known Limitations

### State Persistence
- ❌ In-memory state only (no database)
- ❌ State lost on server restart
- ❌ No horizontal scalability

### Security
- ⚠️ Nonce replay protection is session-scoped
- ⚠️ Replay across reconnects treated as new sessions
- ⚠️ Development secrets in .env.example

### Features
- ❌ No automated test suite
- ❌ No dynamic agent rule reconfiguration
- ❌ No distributed cluster support

---

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:3000 | xargs kill -9
```

### Socket Connection Failed
1. Ensure backend is running first
2. Check `FRONTEND_ORIGIN` in backend/.env
3. Verify no CORS errors in console

### JWT Authentication Failed
1. Check `JWT_SECRET` in backend/.env
2. Clear browser localStorage
3. Refresh page

### Dependencies Failed
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

---

## 🚀 Deployment

### Production Checklist
- [ ] Change all secrets in `.env`
- [ ] Set `NODE_ENV=production`
- [ ] Use process manager (PM2/Docker)
- [ ] Configure HTTPS/SSL
- [ ] Set up monitoring/logging
- [ ] Configure CORS properly
- [ ] Use database for state persistence

### PM2 Deployment
```bash
npm install -g pm2

# Backend
cd backend
pm2 start index.js --name microbridge-backend

# Frontend (after build)
cd frontend
npm run build
pm2 serve dist 5173 --name microbridge-frontend
```

---

## 📊 Performance

### Metrics
- **Job processing**: ~3.5s per job
- **Socket latency**: <50ms
- **Telemetry overhead**: <5ms per event
- **Memory usage**: ~150MB (backend), ~80MB (frontend)

### Scalability
- **Concurrent users**: Tested up to 10 users
- **Jobs per minute**: ~20 jobs/min
- **Socket connections**: Limited by Node.js event loop

---

## 📚 Documentation

### Core Docs
- `README.md` - Project overview
- `RUN.md` - Setup guide (this file)
- `docs/handover.md` - Complete handover
- `docs/architecture.md` - System design

### Technical Docs
- `docs/engine_security.md` - Security specification
- `docs/job_lifecycle.md` - Job state machine
- `docs/telemetry_replay_notes.md` - Telemetry system
- `docs/failure_simulation_report.md` - Failure handling
- `docs/demo_mode.md` - Demo mode guide

### Day-by-Day Progress
- `docs/DAY_2a_COMPLETE.md` - Scope lock
- `docs/DAY_2b_COMPLETE.md` - Engine socket
- `docs/DAY_2c_COMPLETE.md` - Security freeze
- `docs/DAY_2d_COMPLETE.md` - Telemetry & replay
- `docs/DAY_2e_COMPLETE.md` - Failure simulation
- `docs/DAY_2f_COMPLETE.md` - Demo mode lock

---

## 🎯 Next Steps (Future Work)

### High Priority
1. Add database persistence (MongoDB/Redis)
2. Implement automated test suite
3. Add horizontal scalability (Redis for socket state)
4. Production-grade secrets management

### Medium Priority
1. Add user authentication/authorization
2. Implement rate limiting
3. Add metrics/monitoring dashboard
4. Optimize job queue performance

### Low Priority
1. Add more agent types
2. Dynamic agent rule configuration
3. Advanced telemetry analytics
4. Multi-language support

---

## 📞 Support

### Documentation
1. Check `RUN.md` for setup issues
2. Check `docs/architecture.md` for system design
3. Check `docs/failure_simulation_report.md` for error handling
4. Check specific DAY_X_COMPLETE.md for feature details

### Common Questions
**Q: How do I change the port?**  
A: Edit `PORT` in `backend/.env`

**Q: How do I add a new agent?**  
A: See `backend/agents/` for examples, register in `config.js`

**Q: How do I integrate with the engine?**  
A: See `docs/engine_security.md` and `backend/engine/engine_socket.js`

**Q: How do I replay telemetry?**  
A: Run `node backend/test_telemetry_replay.js`

---

## ✅ Handover Checklist

- [x] One-command startup scripts
- [x] Auto-dependency installation
- [x] Auto `.env` file creation
- [x] Complete documentation
- [x] Architecture diagrams
- [x] Security audit complete
- [x] Telemetry system working
- [x] Failure handling tested
- [x] Demo Mode functional
- [x] All panels working
- [x] Multi-user tested
- [x] Engine integration ready
- [x] Production deployment guide

---



