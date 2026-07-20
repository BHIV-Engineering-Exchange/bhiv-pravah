# Inbound Telemetry Testing Guide

## Quick Test

### Test Locally
```bash
cd backend
test_inbound.bat
```

### Test on Render
```bash
cd backend
test_inbound_render.bat
```

---

## What to Expect

### 1. Connection Phase
```
[MOCK ENGINE] Starting...
[MOCK ENGINE] JWT generated
[MOCK ENGINE] Connecting to: http://localhost:3000/engine
[MOCK ENGINE] ✅ Connected to backend
[MOCK ENGINE] Socket ID: <socket_id>
[MOCK ENGINE] Sent engine_ready
[MOCK ENGINE] Received ready_ack: { status: 'acknowledged', ts: ... }
```

### 2. Heartbeat Phase
```
[MOCK ENGINE] 💓 Heartbeat sent
[MOCK ENGINE] Heartbeat acknowledged
```

### 3. Job Execution Phase (after submitting job from dashboard)
```
[MOCK ENGINE] 📦 Received job:
  Job ID: <uuid>
  Job Type: BUILD_SCENE
  User ID: <user_id>
  World: <world_name>

[MOCK ENGINE] ▶️  Job <job_id> started
[MOCK ENGINE] 📊 Job <job_id> progress: 25%
[MOCK ENGINE] 📊 Job <job_id> progress: 50%
[MOCK ENGINE] 📊 Job <job_id> progress: 75%
[MOCK ENGINE] ✅ Job <job_id> completed
```

---

## Backend Logs to Check

Your backend should show:

```
[ENGINE CONNECTED] <socket_id> engine_test_01
[ENGINE READY] engine_test_01
[ENGINE] Sending 0 pending jobs
[ENGINE HEARTBEAT] engine_test_01
[ENGINE] Dispatched job <job_id> (BUILD_SCENE)
[ENGINE TELEMETRY] Job started: <job_id>
[ENGINE TELEMETRY] Job <job_id>: 25%
[ENGINE TELEMETRY] Job <job_id>: 50%
[ENGINE TELEMETRY] Job <job_id>: 75%
[ENGINE TELEMETRY] Job completed: <job_id>
```

---

## How to Submit Test Job

### Option 1: From Dashboard
1. Open frontend: http://localhost:5173
2. Login
3. Go to Job Queue panel
4. Click "Submit Job" or "Generate World"

### Option 2: Using curl
```bash
curl -X POST http://localhost:3000/api/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_jwt>" \
  -d '{
    "jobType": "BUILD_SCENE",
    "userId": "test_user",
    "worldSpec": {
      "schema_version": "1.0",
      "world": {"id": "test_world", "name": "Test", "gravity": [0, -9.8, 0]},
      "scene": {"id": "test_scene", "ambientLight": [1,1,1], "skybox": "default"},
      "entities": [],
      "quests": []
    }
  }'
```

### Option 3: From Frontend Socket
Open browser console on dashboard:
```javascript
socket.emit('submit_job', {
  jobType: 'BUILD_SCENE',
  worldSpec: { /* ... */ }
});
```

---

## Troubleshooting

### Mock Engine Won't Connect
- Check backend is running
- Verify JWT_SECRET in .env matches
- Check URL (localhost vs Render)

### No Jobs Received
- Submit a job from dashboard
- Check backend logs for "Dispatched job"
- Verify engine emitted "engine_ready"

### Telemetry Not Showing
- Check backend logs for "[ENGINE TELEMETRY]"
- Verify job_id matches between dispatch and telemetry
- Check mock engine is sending correct event names

---

## Success Criteria

✅ Mock engine connects successfully  
✅ Backend logs "[ENGINE CONNECTED]"  
✅ Heartbeats working (every 5s)  
✅ Jobs dispatched to mock engine  
✅ Telemetry received: job_started, job_progress, job_completed  
✅ Backend updates job status based on telemetry  

---

## Files Modified

- `backend/test_mock_engine.js` - Updated JWT issuer and dynamic URL
- `backend/test_inbound.bat` - Local test script
- `backend/test_inbound_render.bat` - Render test script
