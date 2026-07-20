# RUN.md — Quick Start Guide

**System**: Real-Time Micro-Bridge + Multi-Agent Orchestrator  


---

## 🚀 One-Command Startup (Recommended)

### Windows
```bash
start.bat
```

### Mac/Linux
```bash
chmod +x start.sh
./start.sh
```

**What it does**:
1. Checks Node.js installation (v18+ required)
2. Installs backend dependencies (if needed)
3. Installs frontend dependencies (if needed)
4. Creates `.env` files from examples
5. Starts backend server (port 3000)
6. Starts frontend server (port 5173)
7. Opens dashboard in browser

**URLs**:
- Backend: `http://localhost:3000`
- Frontend: `http://localhost:5173`

---

## 📋 Prerequisites

### Required
- **Node.js v18+** ([Download](https://nodejs.org))
- **npm v9+** (comes with Node.js)

### Verify Installation
```bash
node --version  # Should show v18.x.x or higher
npm --version   # Should show v9.x.x or higher
```

---

## 🔧 Manual Setup (Alternative)

If you prefer manual control or the startup script fails:

### Step 1: Clone Repository
```bash
git clone https://github.com/Rudra212545/Real-time-Dashboard.git
cd Real-Time-Micro-Bridge
```

### Step 2: Backend Setup
```bash
cd backend
npm install
cp .env.example .env
npm start
```

Backend runs at: `http://localhost:3000`

### Step 3: Frontend Setup
Open a **new terminal** (keep backend running):
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

---

## ⚙️ Configuration

### Backend Configuration
**File**: `backend/.env`

```env
# JWT Authentication
JWT_SECRET=microbridge_jwt_secret_dev_12345
JWT_ISSUER=microbridge.internal
JWT_EXP=1h

# Action Signatures
HMAC_SECRET=HMAC_SECRET_987654321
HMAC_WINDOW_MS=15000

# Agent Secrets
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

**Important**: Change secrets in production!

### Frontend Configuration
**File**: `frontend/.env` (optional)

```env
VITE_API_URL=http://localhost:3000
```

---

## 🎯 System Usage

### 1. Open Dashboard
Navigate to `http://localhost:5173` in your browser.

### 2. Demo Mode (Quickest Way)
- Locate the **Demo Mode** panel
- Click **"Launch Demo"**
- Watch the full pipeline execute:
  - Random world generation
  - Job queue processing
  - Engine simulation
  - Preview update

### 3. Manual World Generation
- Open **JSON Config Panel**
- Select a sample world (Forest, Desert, Ocean, Volcano)
- Click **"Generate World"**
- Watch jobs in **Job Queue Panel**
- See preview update in **Cube Preview**

### 4. Multi-User Testing
- Open multiple browser tabs
- Each tab = separate user
- Watch **Presence Panel** update
- Trigger actions in different tabs
- Observe agent reactions

---

## 🧪 Testing

### Health Check
```bash
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": 1738742400000
}
```

### Security Status
```bash
curl http://localhost:3000/security/status
```

---

## 🔌 Engine Integration

### Overview
The system integrates with external game engines via Socket.IO on the `/engine` namespace. All engine communication is secured with JWT authentication, HMAC signatures, nonce replay protection, and timestamp validation.

### Engine Connection Steps

#### Step 1: Generate Engine JWT
```javascript
const jwt = require('jsonwebtoken');

const engineToken = jwt.sign(
  { engineId: 'your_engine_id', role: 'engine' },
  process.env.JWT_SECRET,
  { expiresIn: '1h' }
);
```

#### Step 2: Connect to Engine Namespace
```javascript
const io = require('socket.io-client');

const socket = io('http://localhost:3000/engine', {
  auth: { token: engineToken }
});
```

#### Step 3: Send Ready Signal
```javascript
socket.on('connect', () => {
  socket.emit('engine_ready');
  
  // Start heartbeat (every 3 seconds)
  setInterval(() => {
    socket.emit('engine_heartbeat');
  }, 3000);
});
```

#### Step 4: Receive Jobs
```javascript
socket.on('engine_job', (job) => {
  // job contains: job_id, job_type, world_spec, payload, user_id
  processJob(job);
});
```

#### Step 5: Send Signed Messages
All engine messages must be signed:

```javascript
const crypto = require('crypto');

function signMessage(payload) {
  const nonce = crypto.randomBytes(16).toString('hex');
  const ts = Date.now();
  const sig = crypto
    .createHmac('sha256', process.env.ENGINE_SHARED_SECRET)
    .update(JSON.stringify(payload) + nonce + ts)
    .digest('hex');
  
  return { payload, nonce, ts, sig };
}

// Send job acknowledgement
socket.emit('job_ack', signMessage({ 
  jobId: job.job_id, 
  status: 'received' 
}));

// Send job started
socket.emit('job_started', signMessage({ 
  job_id: job.job_id, 
  timestamp: Date.now() 
}));

// Send progress
socket.emit('job_progress', signMessage({ 
  job_id: job.job_id, 
  progress: 50,
  timestamp: Date.now() 
}));

// Send completion
socket.emit('job_completed', signMessage({ 
  job_id: job.job_id, 
  result: { success: true },
  timestamp: Date.now() 
}));
```

### Message Types

**Outbound (Bridge → Engine):**
- `engine_job` - Job dispatch with world_spec

**Inbound (Engine → Bridge):**
- `engine_ready` - Engine initialization complete
- `engine_heartbeat` - Liveness signal (every 3s)
- `job_ack` - Job received acknowledgement
- `job_started` - Job execution started
- `job_progress` - Job progress update (0-100)
- `job_completed` - Job finished successfully
- `job_failed` - Job execution failed
- `engine_error` - Error reporting

### Security Requirements

**All inbound messages must include:**
```javascript
{
  payload: { /* actual data */ },
  nonce: "unique_hex_string",
  ts: 1234567890,
  sig: "hmac_signature"
}
```

**Signature Calculation:**
```javascript
HMAC-SHA256(JSON.stringify(payload) + nonce + timestamp)
```

**Validation:**
- JWT must have `role: "engine"`
- Signature must be valid
- Nonce must be unique (not reused)
- Timestamp must be within ±30 seconds

### Environment Variables

Add to `backend/.env`:
```env
ENGINE_SHARED_SECRET=your_secure_secret_here
```

### Example: Complete Engine Client

See `backend/test_mock_engine_secure.js` for a full working example.

### Troubleshooting

**Connection Rejected:**
- Check JWT token is valid
- Verify `role: "engine"` in JWT payload
- Ensure JWT_SECRET matches backend

**Messages Rejected:**
- Verify ENGINE_SHARED_SECRET matches
- Check signature calculation includes payload + nonce + timestamp
- Ensure nonce is unique per message
- Verify timestamp is current (±30s)

**Heartbeat Timeout:**
- Send heartbeat every 3 seconds
- Check network connectivity
- Verify socket connection is active

---

## 🧪 Testing Engine Integration

### Test 1: Single Job Execution

**Terminal 1 - Backend:**
```bash
cd backend
npm start
```

**Terminal 2 - Mock Engine:**
```bash
cd backend
node test_single_job.js
```

**Terminal 3 - Submit Job:**
Open `http://localhost:5173`, login, and submit a "Generate World" job.

**Expected**: Job processes through all stages (queued → dispatched → running → completed)

---

### Test 2: Concurrent Jobs

**Terminal 1 - Backend:**
```bash
cd backend
npm start
```

**Terminal 2 - Mock Engine:**
```bash
cd backend
node test_concurrent_jobs.js
```

**Terminal 3 - Submit Multiple Jobs:**
Open `http://localhost:5173`, submit 3 jobs quickly.

**Expected**: All jobs process concurrently, engine handles multiple jobs simultaneously.

---

### Test 3: Engine Disconnect Simulation

**Terminal 1 - Backend:**
```bash
cd backend
npm start
```

**Terminal 2 - Mock Engine:**
```bash
cd backend
node test_engine_disconnect.js
```

**Expected**: 
- Engine connects and processes jobs
- After 8 seconds, engine disconnects
- Active jobs fail gracefully
- After 5 seconds, engine reconnects
- System recovers and accepts new jobs

---

### Test 4: Full Integration (Recommended)

**Terminal 1 - Backend:**
```bash
cd backend
npm start
```

**Terminal 2 - Secure Mock Engine:**
```bash
cd backend
node test_mock_engine_secure.js
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

**Browser:**
1. Open `http://localhost:5173`
2. Login
3. Submit "Generate World" job
4. Watch Terminal 2 process jobs with signed messages
5. Observe telemetry in UI (Engine Status Panel)

**Expected**: All messages accepted, jobs complete, UI updates in real-time.

---

### Other Tests

#### Telemetry Replay
```bash
cd backend
node test_telemetry_replay.js
```

#### Failure Simulation
```bash
cd backend
node test_failures.js
```

#### Engine Security Tests
```bash
cd backend
node test_engine_security_live.js
```

---

## 🐛 Troubleshooting

### Port Already in Use
**Error**: `EADDRINUSE: address already in use :::3000`

**Solution**:
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:3000 | xargs kill -9
```

Or change port in `backend/.env`:
```env
PORT=3001
```

### Socket Connection Failed
**Error**: `WebSocket connection failed`

**Solution**:
1. Ensure backend is running first
2. Check backend console for errors
3. Verify `FRONTEND_ORIGIN` in `backend/.env` matches frontend URL

### JWT Authentication Failed
**Error**: `JWT verification failed`

**Solution**:
1. Check `JWT_SECRET` in `backend/.env`
2. Clear browser localStorage
3. Refresh page

### Dependencies Installation Failed
**Error**: `npm install` fails

**Solution**:
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### Frontend Not Loading
**Error**: Blank page or build errors

**Solution**:
```bash
cd frontend
rm -rf node_modules .vite
npm install
npm run dev
```

---

## 📦 Project Structure

```
Real-Time-Micro-Bridge/
├── backend/
│   ├── agents/              # Multi-agent logic
│   ├── auth/                # JWT & signatures
│   ├── engine/              # Engine integration
│   ├── security/            # Nonce, heartbeat
│   ├── telemetry/           # Behaviour tracking
│   ├── .env.example         # Config template
│   ├── index.js             # Entry point
│   ├── socket.js            # Socket.IO handlers
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── data/            # Sample worlds
│   │   ├── hooks/           # Custom hooks
│   │   └── socket/          # Socket client
│   ├── .env.example
│   └── package.json
├── docs/                    # Documentation
├── start.bat                # Windows startup
├── start.sh                 # Mac/Linux startup
├── RUN.md                   # This file
└── README.md                # Project overview
```

---

## 🔄 Development Workflow

### Backend Development
```bash
cd backend
npm run dev  # Uses nodemon for auto-restart
```

### Frontend Development
```bash
cd frontend
npm run dev  # Vite hot reload
```

### Build for Production
```bash
# Frontend
cd frontend
npm run build
npm run preview  # Test production build

# Backend
cd backend
NODE_ENV=production npm start
```

---

## 🚀 Deployment

### Environment Variables
**Production**: Set secure values for:
- `JWT_SECRET` (use strong random string)
- `HMAC_SECRET` (use strong random string)
- All agent secrets (unique per agent)
- `ENGINE_SHARED_SECRET` (coordinate with engine team)

### Process Manager (PM2)
```bash
npm install -g pm2

# Backend
cd backend
pm2 start index.js --name microbridge-backend

# Frontend (after build)
cd frontend
pm2 serve dist 5173 --name microbridge-frontend
```



---

## 📊 Monitoring

### Logs
```bash
# Backend logs
tail -f backend/logs/app.log

# Telemetry
tail -f backend/telemetry_samples.json

# Engine events
tail -f backend/engine/engine_event_log.json
```

### Health Endpoints
- `GET /health` - Service status
- `GET /security/status` - Security config

---

## 🔗 Quick Links

- **README.md** - Project overview
- **docs/handover.md** - Complete handover guide
- **docs/architecture.md** - System architecture
- **docs/security_readiness.md** - Security details
- **docs/demo_mode.md** - Demo mode guide
- **docs/failure_simulation_report.md** - Failure handling

---

## ✅ Verification Checklist

After setup, verify:
- [ ] Backend running at `http://localhost:3000`
- [ ] Frontend running at `http://localhost:5173`
- [ ] Dashboard loads in browser
- [ ] Demo Mode button works
- [ ] Job Queue shows jobs
- [ ] Cube Preview updates
- [ ] No console errors
- [ ] Health endpoint responds
- [ ] Engine integration tests pass

---

**System Ready!** 🎉

For questions, check `docs/handover.md` or open an issue.