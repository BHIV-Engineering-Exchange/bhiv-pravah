# 🎯 PRANA Frontend Integration Guide

**For**: Frontend Team (Soham)  
**Status**: Backend Ready ✅  
**Estimated Time**: 2-4 hours

---

## 📋 Prerequisites

1. ✅ Backend services running (Bucket on port 8001)
2. ✅ PRANA core files in `prana-core/` directory
3. ✅ User authentication system (to get user_id, session_id)
4. ✅ Modern browser with ES6 module support

---

## 🚀 Quick Integration (3 Steps)

### Step 1: Copy PRANA Core Files

Ensure these files are accessible from your frontend:
```
prana-core/
├── signals.js
├── prana_state_engine.js
├── prana_packet_builder.js
└── bucket_bridge.js
```

### Step 2: Add PRANA to Your HTML

```html
<script type="module">
  import { initPranaCore } from './prana-core/prana_packet_builder.js';

  // Initialize PRANA
  initPranaCore({
    system_type: 'gurukul',  // or 'ems'
    role: 'student',          // or 'employee'
    user_id: getCurrentUserId(),
    session_id: getCurrentSessionId(),
    lesson_id: getCurrentLessonId(),  // optional
    bucket_endpoint: 'http://localhost:8001/bucket/prana/ingest'
  });
</script>
```

### Step 3: Test It

Open browser console (F12) and look for:
```
[PRANA] Unified SignalCapture initialized
[PRANA] Cognitive State Engine initialized
[PRANA] Packet Builder initialized
[PRANA_PACKET] { user_id: "...", cognitive_state: "ON_TASK", ... }
```

---

## 📚 Detailed Integration

### For Gurukul (Learning Platform)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Gurukul Lesson</title>
</head>
<body>
    <div id="lesson-content">
        <!-- Your lesson content here -->
    </div>

    <script type="module">
        import { initPranaCore } from './prana-core/prana_packet_builder.js';

        // Get user context from your auth system
        const userContext = {
            system_type: 'gurukul',
            role: 'student',
            user_id: window.currentUser.id,           // From your auth
            session_id: window.currentSession.id,     // From your session
            lesson_id: window.currentLesson.id,       // From your lesson system
            bucket_endpoint: 'http://localhost:8001/bucket/prana/ingest'
        };

        // Initialize PRANA
        const prana = initPranaCore(userContext);

        console.log('✅ PRANA initialized for Gurukul');
    </script>
</body>
</html>
```

### For EMS (Employee Management System)

```html
<!DOCTYPE html>
<html>
<head>
    <title>EMS Task Manager</title>
</head>
<body>
    <div id="task-panel">
        <!-- Your task panel here -->
    </div>

    <script type="module">
        import { initPranaCore } from './prana-core/prana_packet_builder.js';

        // Get employee context from your auth system
        const employeeContext = {
            system_type: 'ems',
            role: 'employee',
            user_id: window.currentEmployee.id,       // From your auth
            session_id: window.currentSession.id,     // From your session
            task_id: window.currentTask.id,           // From your task system
            bucket_endpoint: 'http://localhost:8001/bucket/prana/ingest'
        };

        // Initialize PRANA
        const prana = initPranaCore(employeeContext);

        console.log('✅ PRANA initialized for EMS');
    </script>
</body>
</html>
```

---

## 🔧 Configuration Options

### Required Fields

```javascript
{
  system_type: 'gurukul' | 'ems',  // REQUIRED
  role: 'student' | 'employee',     // REQUIRED
  user_id: string,                  // REQUIRED
  session_id: string,               // REQUIRED
  bucket_endpoint: string           // REQUIRED
}
```

### Optional Fields

```javascript
{
  lesson_id: string,    // For Gurukul (optional)
  task_id: string,      // For EMS (optional)
}
```

---

## 🎯 Context Provider Pattern (Recommended)

For dynamic context (e.g., changing lessons/tasks):

```javascript
import { initPranaCore, getPacketBuilder } from './prana-core/prana_packet_builder.js';

// Initialize PRANA once
const prana = initPranaCore({
    system_type: 'gurukul',
    role: 'student',
    user_id: 'user123',
    session_id: 'session456',
    bucket_endpoint: 'http://localhost:8001/bucket/prana/ingest'
});

// Register a context provider for dynamic updates
const packetBuilder = getPacketBuilder();
packetBuilder.registerContextProvider({
    getContext: () => ({
        user_id: window.currentUser.id,
        session_id: window.currentSession.id,
        lesson_id: window.currentLesson.id  // Updates dynamically
    })
});
```

---

## 🧪 Testing Your Integration

### 1. Check Console Logs

Open browser console (F12) and verify:
```
✅ [PRANA] Unified SignalCapture initialized
✅ [PRANA] Cognitive State Engine initialized
✅ [PRANA] Packet Builder initialized
✅ [PRANA_PACKET] { ... }  (every 5 seconds)
```

### 2. Check Network Tab

Open Network tab (F12) and filter by "prana":
- You should see POST requests to `/bucket/prana/ingest` every 5 seconds
- Status should be 200 OK
- Response: `{"success": true, "message": "Packet received"}`

### 3. Verify Backend

```bash
# Check if packets are being received
curl http://localhost:8001/bucket/prana/stats

# Check your user's history
curl http://localhost:8001/bucket/prana/user/YOUR_USER_ID
```

---

## 🎨 UI Integration (Optional)

Show PRANA status to users:

```html
<div id="prana-status">
    <span id="cognitive-state">Loading...</span>
    <span id="focus-score">0</span>
</div>

<script type="module">
    import { getStateEngine } from './prana-core/prana_state_engine.js';

    // Update UI every second
    setInterval(() => {
        const stateEngine = getStateEngine();
        if (stateEngine) {
            const state = stateEngine.getCurrentState();
            document.getElementById('cognitive-state').textContent = state;
            
            // Estimate focus score
            const focusScores = {
                'DEEP_FOCUS': 95,
                'ON_TASK': 75,
                'THINKING': 65,
                'DISTRACTED': 30,
                'IDLE': 10,
                'OFF_TASK': 5,
                'AWAY': 0
            };
            document.getElementById('focus-score').textContent = focusScores[state];
        }
    }, 1000);
</script>
```

---

## 🔒 Privacy & Security

### What PRANA Captures

✅ **Captures**:
- Mouse movement patterns (velocity, not position)
- Keyboard activity rate (not content)
- Scroll behavior
- Window focus/visibility
- Time spent active/idle/away

❌ **Does NOT Capture**:
- Keystroke content
- Mouse coordinates
- Screen content
- DOM structure
- Personal data

### Kill Switch

Disable PRANA globally:
```javascript
window.PRANA_DISABLED = true;
```

---

## 🐛 Troubleshooting

### Issue: PRANA not initializing

**Check**:
1. Are PRANA core files accessible?
2. Is browser console showing errors?
3. Is ES6 module support enabled?

**Fix**:
```javascript
// Add error handling
try {
    const prana = initPranaCore(config);
    console.log('✅ PRANA initialized');
} catch (error) {
    console.error('❌ PRANA initialization failed:', error);
}
```

### Issue: Packets not reaching backend

**Check**:
1. Is Bucket running on port 8001?
2. Is CORS configured correctly?
3. Is network tab showing 200 OK?

**Fix**:
```javascript
// Check endpoint
const config = {
    ...otherConfig,
    bucket_endpoint: 'http://localhost:8001/bucket/prana/ingest'  // Verify port
};
```

### Issue: High CPU usage

**Check**:
1. Are there multiple PRANA instances?
2. Is page being reloaded frequently?

**Fix**:
```javascript
// Initialize only once
if (!window.PRANA_INITIALIZED) {
    initPranaCore(config);
    window.PRANA_INITIALIZED = true;
}
```

---

## 📊 Examples

See working examples:
- `prana-core/example_gurukul.html` - Gurukul integration
- `prana-core/example_ems.html` - EMS integration

To run examples:
```bash
# Start a simple HTTP server
cd prana-core
python -m http.server 8080

# Open in browser
http://localhost:8080/example_gurukul.html
http://localhost:8080/example_ems.html
```

---

## ✅ Integration Checklist

- [ ] PRANA core files copied to frontend
- [ ] User authentication provides user_id, session_id
- [ ] PRANA initialized in HTML pages
- [ ] Console shows PRANA logs
- [ ] Network tab shows packets being sent
- [ ] Backend receives packets (check `/bucket/prana/stats`)
- [ ] Tested in development environment
- [ ] Tested with different user interactions
- [ ] Error handling added
- [ ] Documentation updated

---

## 🚀 Deployment

### Production Configuration

```javascript
const config = {
    system_type: 'gurukul',
    role: 'student',
    user_id: getUserId(),
    session_id: getSessionId(),
    lesson_id: getLessonId(),
    bucket_endpoint: process.env.BUCKET_URL + '/bucket/prana/ingest'  // Use env var
};
```

### Environment Variables

```env
# .env.production
BUCKET_URL=https://your-production-bucket.com
```

---

## 📞 Support

**Issues?** Check:
1. Console logs (F12)
2. Network tab (F12)
3. Backend logs (`BHIV_Central_Depository-main/logs/`)
4. Test script: `python test_prana_integration.py`

**Questions?** Contact:
- Backend Team: Ashmit (PRANA integration)
- Frontend Team: Soham (UI integration)

---

## 🎉 Success Indicators

✅ Console shows PRANA initialization  
✅ Packets sent every 5 seconds  
✅ Backend receives packets (200 OK)  
✅ User behavior tracked correctly  
✅ No performance impact  
✅ No errors in console  

**When all indicators are green, PRANA is fully integrated! 🚀**
