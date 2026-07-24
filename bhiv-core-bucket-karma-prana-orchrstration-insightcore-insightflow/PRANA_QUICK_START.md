# 🎯 PRANA Quick Start Guide

## ✅ Integration Complete

PRANA is now integrated as the **4th pillar** of your BHIV system.

---

## 🚀 Quick Test

### 1. Start All Services

```bash
# Terminal 1 - Karma
cd karma_chain_v2-main
python main.py

# Terminal 2 - Bucket
cd BHIV_Central_Depository-main
python main.py

# Terminal 3 - Core
cd v1-BHIV_CORE-main
python mcp_bridge.py
```

### 2. Test PRANA Endpoint

```bash
curl -X POST "http://localhost:8001/bucket/prana/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "session_id": "test_session",
    "lesson_id": "test_lesson",
    "system_type": "gurukul",
    "role": "student",
    "timestamp": "2026-01-30T10:30:00Z",
    "cognitive_state": "DEEP_FOCUS",
    "active_seconds": 4.5,
    "idle_seconds": 0.5,
    "away_seconds": 0.0,
    "focus_score": 95,
    "raw_signals": {
      "mouse_velocity": 150,
      "scroll_depth": 75
    }
  }'
```

**Expected**: `{"success": true, "message": "Packet received"}`

### 3. Check Statistics

```bash
curl http://localhost:8001/bucket/prana/stats
```

### 4. Check Health

```bash
curl http://localhost:8001/health | grep prana_telemetry
```

---

## 📁 Files Modified

1. ✅ `prana-core/bucket_bridge.js` - Fixed port (8000 → 8001)
2. ✅ `BHIV_Central_Depository-main/main.py` - Added PRANA endpoints
3. ✅ `BHIV_Central_Depository-main/integration/karma_forwarder.py` - Added PRANA forwarding
4. ✅ `README.md` - Updated to 4-pillar architecture
5. ✅ `PRANA_INTEGRATION_COMPLETE.md` - Full documentation

---

## 🎯 Next Steps

### For Frontend Team
1. Add PRANA to Gurukul lesson pages
2. Add PRANA to EMS task pages
3. Initialize with user context

### Example Integration

```html
<script type="module">
  import { initPranaCore } from './prana-core/prana_packet_builder.js';

  initPranaCore({
    system_type: 'gurukul',
    role: 'student',
    user_id: 'user123',
    session_id: 'session456',
    lesson_id: 'lesson789',
    bucket_endpoint: 'http://localhost:8001/bucket/prana/ingest'
  });
</script>
```

---

## ✅ Success Indicators

- [x] Port fixed (8001)
- [x] Bucket endpoint active
- [x] Karma forwarder updated
- [x] Health check includes PRANA
- [x] MongoDB integration
- [x] Documentation complete
- [ ] Frontend integration (pending)

---

**Status**: ✅ Backend integration complete, ready for frontend integration
