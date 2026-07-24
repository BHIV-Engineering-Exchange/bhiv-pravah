# Port Change Summary - Bucket 8000 → 8001

## Problem
Karma Chain v2 and Bucket both used port 8000, causing a conflict that prevented running both systems simultaneously.

## Solution
Changed Bucket port from 8000 to 8001.

---

## New Port Allocation

| Service | Port | Purpose |
|---------|------|---------|
| **Karma Chain** | 8000 | Behavioral tracking and karma analytics |
| **Bucket** | 8001 | Event storage and governance |
| **Core** | 8002 | Agent orchestration and decision making |

---

## Files Modified

### 1. Bucket Main Application
**File**: `BHIV_Central_Depository-main/main.py`
- Changed default port from 8000 → 8001
- Line: `port = int(os.getenv("FASTAPI_PORT", 8001))`

### 2. Core Bucket Client
**File**: `v1-BHIV_CORE-main/integration/bucket_client.py`
- Updated Bucket URL from `http://localhost:8000` → `http://localhost:8001`
- Line: `def __init__(self, bucket_url: str = "http://localhost:8001")`

### 3. System Startup Script
**File**: `start_system.py`
- Updated port checks from 8000 → 8001
- Updated service URLs in output messages
- Updated integration test URLs

### 4. Test Scripts
**File**: `test_simple.py`
- Updated all Bucket URLs from port 8000 → 8001
- Health check: `http://localhost:8001/health`
- Write event: `http://localhost:8001/core/write-event`
- Read context: `http://localhost:8001/core/read-context`
- Stats: `http://localhost:8001/core/stats`

### 5. Documentation
**File**: `README.md`
- Updated all port references
- Added Karma service documentation
- Updated health check URLs
- Updated monitoring commands
- Updated usage examples
- Added Karma endpoints section

---

## Verification

### Test Results
```bash
# Bucket Health Check (Port 8001)
curl http://localhost:8001/health
```

**Response**:
```json
{
  "status": "healthy",
  "bucket_version": "1.0.0",
  "core_integration": {
    "status": "active",
    "events_received": 0,
    "agents_tracked": 0
  },
  "services": {
    "mongodb": "connected",
    "redis": "connected",
    "audit_middleware": "active"
  }
}
```

✅ **Bucket successfully running on port 8001**

### Port Status
```
Port 8000: Available for Karma Chain
Port 8001: ✅ Bucket (LISTENING, PID 20460)
Port 8002: Available for Core
```

---

## Integration Flow

### Updated Data Flow
```
User Request
     ↓
Core (8002) - Processes task, runs agents
     ↓
Bucket (8001) - Stores events, validates governance
     ↓
Karma (8000) - Tracks behavior, computes karma scores
     ↓
Analytics & Feedback
```

### Service Communication
- **Core → Bucket**: `http://localhost:8001` (fire-and-forget)
- **Bucket → Karma**: `http://localhost:8000` (event forwarding)
- **Karma → Bucket**: `http://localhost:8001` (analytics feedback)

---

## Testing Checklist

### Bucket (Port 8001)
- [x] Starts without errors
- [x] Health endpoint responds
- [x] Core integration status active
- [x] MongoDB connected
- [x] Redis connected
- [x] Audit middleware active

### Core (Port 8002)
- [ ] Starts without errors
- [ ] Connects to Bucket on 8001
- [ ] Sends events successfully
- [ ] Receives context from Bucket

### Karma (Port 8000)
- [ ] Starts without errors
- [ ] Health endpoint responds
- [ ] Ready to receive events
- [ ] MongoDB connected

### Integration
- [ ] Core → Bucket communication works
- [ ] Bucket → Karma communication works
- [ ] All three services run simultaneously
- [ ] No port conflicts

---

## Next Steps

### Immediate
1. ✅ Change Bucket port to 8001
2. ✅ Verify Bucket starts successfully
3. ✅ Update all documentation
4. ⏳ Test Core → Bucket communication
5. ⏳ Start Karma on port 8000
6. ⏳ Verify all three services run together

### Short-term
1. Create Karma client in Bucket
2. Implement event forwarding (Bucket → Karma)
3. Test complete flow: Core → Bucket → Karma
4. Verify karma events are stored

### Medium-term
1. Integrate behavioral normalization
2. Add karma analytics to Bucket dashboard
3. Implement feedback loop
4. Performance testing

---

## Rollback Plan

If issues arise, rollback is simple:

1. **Revert Bucket to port 8000**:
   ```python
   # In main.py
   port = int(os.getenv("FASTAPI_PORT", 8000))
   ```

2. **Revert Core bucket_client.py**:
   ```python
   def __init__(self, bucket_url: str = "http://localhost:8000"):
   ```

3. **Restart services**

---

## Environment Variables

### Bucket (.env)
```bash
FASTAPI_PORT=8001  # Optional, defaults to 8001 now
```

### Karma (.env)
```bash
PORT=8000  # Default Karma port
```

### Core (.env)
```bash
BUCKET_URL=http://localhost:8001  # Optional override
```

---

## Status

✅ **Port change complete and verified**
✅ **Bucket running successfully on port 8001**
✅ **Ready for Karma integration**

**Date**: January 29, 2026
**Status**: Complete
**Next**: Start Karma and test three-service integration
