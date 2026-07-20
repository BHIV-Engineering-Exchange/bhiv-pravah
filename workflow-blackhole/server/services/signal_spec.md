# EMS Signal Layer Specification

## Overview
The EMS (Employee Monitoring System) Signal Layer captures real-time behavioral signals from employees to determine actual work engagement vs. pretend work.

## Signal Types

### 1. Window Focus (`window_focus`)
**Purpose**: Detect if employee's browser/application is actively focused

**Meaning**:
- `true` → `working` - Window is active and focused
- `false` → `background` - Window is in background/minimized

**Capture Method**:
- Browser: `window.onfocus` / `window.onblur` events
- Desktop: Active window detection via OS APIs

**Data Structure**:
```javascript
{
  type: 'window_focus',
  timestamp: 1234567890,
  value: true/false,
  meaning: 'working' | 'background',
  metadata: {
    previousState: boolean,
    duration: number,
    visibilityState: string
  }
}
```

**Detection Triggers**:
- User switches tabs
- User minimizes browser
- User switches applications
- User locks screen

---

### 2. Keystroke Rate (`keystroke_rate`)
**Purpose**: Measure actual typing activity to detect real work

**Meaning**:
- `>= 30 keys/min` → `real_activity` - Actively typing
- `< 30 keys/min` → `low_activity` - Minimal or no typing

**Capture Method**:
- Browser: `keydown` event listener
- Desktop: Global keyboard hook

**Data Structure**:
```javascript
{
  type: 'keystroke_rate',
  timestamp: 1234567890,
  value: 45, // keystrokes per minute
  meaning: 'real_activity' | 'low_activity',
  metadata: {
    key: string,
    isTyping: boolean,
    burstMode: boolean,
    pattern: string
  }
}
```

**Calculation**:
```
keystrokes_per_minute = count(keystrokes in last 60 seconds)
```

**Thresholds**:
- `0-10/min` → Idle
- `10-30/min` → Low activity
- `30-60/min` → Normal activity
- `>60/min` → High activity (burst mode)

---

### 3. Mouse Movement (`mouse_movement`)
**Purpose**: Track engagement through mouse interaction

**Meaning**:
- `>= 20 moves/min` → `engagement` - Actively engaged
- `< 20 moves/min` → `low_engagement` - Minimal engagement

**Capture Method**:
- Browser: `mousemove`, `click`, `wheel` events
- Desktop: Global mouse hook

**Data Structure**:
```javascript
{
  type: 'mouse_movement',
  timestamp: 1234567890,
  value: 35, // movements per minute
  meaning: 'engagement' | 'low_engagement',
  metadata: {
    x: number,
    y: number,
    eventType: 'move' | 'click' | 'scroll',
    velocity: number,
    distance: number
  }
}
```

**Metrics**:
- Movement count per minute
- Mouse velocity (pixels/second)
- Click frequency
- Movement patterns (linear vs. erratic)

---

### 4. Scroll Depth (`scroll_depth`)
**Purpose**: Monitor content interaction through scrolling behavior

**Meaning**:
- `scroll events > 0` → `content_interaction` - Reading/reviewing content
- `scroll events = 0` → `no_interaction` - Static/idle

**Capture Method**:
- Browser: `scroll` event listener
- Track scroll position, direction, speed

**Data Structure**:
```javascript
{
  type: 'scroll_depth',
  timestamp: 1234567890,
  value: 65, // percentage scrolled
  meaning: 'content_interaction' | 'no_interaction',
  metadata: {
    percentage: number,
    direction: 'up' | 'down',
    scrollEventsPerMinute: number,
    documentHeight: number,
    viewportHeight: number
  }
}
```

**Metrics**:
- Current scroll position (%)
- Scroll direction
- Scroll velocity
- Time spent at each scroll position

---

### 5. Task Tab Active (`task_tab_active`)
**Purpose**: Verify if the active tab contains work-related content

**Meaning**:
- `true` → `real_task` - Work-related tab is active
- `false` → `non_task` - Non-work tab is active

**Capture Method**:
- Browser: Track active tab URL and title
- Compare against whitelist/blacklist

**Data Structure**:
```javascript
{
  type: 'task_tab_active',
  timestamp: 1234567890,
  value: true/false,
  meaning: 'real_task' | 'non_task',
  metadata: {
    url: string,
    title: string,
    domain: string,
    tabId: string,
    isActive: boolean
  }
}
```

**Work-Related Domains** (Whitelist):
- `main-workflow.vercel.app`
- `github.com`
- `stackoverflow.com`
- `docs.google.com`
- `notion.so`
- `figma.com`
- `slack.com`
- `localhost`

**Non-Work Domains** (Blacklist):
- `facebook.com`
- `twitter.com`
- `instagram.com`
- `youtube.com`
- `netflix.com`
- `reddit.com`
- `tiktok.com`

---

### 6. Idle Time (`idle_time`)
**Purpose**: Detect periods of complete inactivity

**Meaning**:
- `>= 2 minutes` → `inactivity` - Employee is idle
- `< 2 minutes` → `active` - Employee is active

**Capture Method**:
- Monitor time since last keyboard/mouse/scroll event
- Automatic calculation every 30 seconds

**Data Structure**:
```javascript
{
  type: 'idle_time',
  timestamp: 1234567890,
  value: 180000, // milliseconds
  meaning: 'inactivity' | 'active',
  metadata: {
    idleSeconds: number,
    lastActivity: timestamp,
    threshold: number,
    isIdle: boolean
  }
}
```

**Thresholds**:
- `0-30s` → Active
- `30s-2min` → Low activity
- `2-5min` → Idle (warning)
- `>5min` → Extended idle (alert)

---

### 7. App Switch (`app_switch`)
**Purpose**: Track application/window switching as distraction indicator

**Meaning**:
- Always → `distraction` - Context switching detected

**Capture Method**:
- Desktop: Monitor active window changes
- Browser: Track tab switching

**Data Structure**:
```javascript
{
  type: 'app_switch',
  timestamp: 1234567890,
  value: 5, // total switches
  meaning: 'distraction',
  metadata: {
    fromApp: string,
    toApp: string,
    fromTitle: string,
    toTitle: string,
    switchCount: number,
    isWorkApp: boolean
  }
}
```

**Analysis**:
- High switch rate (>20/hour) → Distracted
- Normal switch rate (5-20/hour) → Context switching
- Low switch rate (<5/hour) → Focused

---

### 8. Browser Hidden (`browser_hidden`)
**Purpose**: Detect when browser is minimized or visibility is hidden

**Meaning**:
- `true` → `pretending` - Browser is hidden but should be visible
- `false` → `visible` - Browser is visible and active

**Capture Method**:
- Browser: `document.visibilityState` API
- Events: `visibilitychange` event

**Data Structure**:
```javascript
{
  type: 'browser_hidden',
  timestamp: 1234567890,
  value: true/false,
  meaning: 'pretending' | 'visible',
  metadata: {
    visibilityState: 'visible' | 'hidden',
    documentHidden: boolean,
    reason: string
  }
}
```

**Detection Scenarios**:
- User minimizes browser
- User switches to another app
- User opens another window on top
- Screen lock/sleep mode

---

## Signal Processing

### Activity Score Calculation
```javascript
Activity Score (0-100) = 
  (keystroke_score × 0.3) +
  (mouse_score × 0.2) +
  (scroll_score × 0.1) +
  (focus_score × 0.2) +
  (task_tab_score × 0.2)
```

### Productivity Indicator
| Condition | Indicator |
|-----------|-----------|
| `idle_time >= 2min` | `idle` |
| `window_focus = false` | `distracted` |
| `task_tab_active = false` | `off-task` |
| `activity_score >= 70` | `highly-productive` |
| `activity_score >= 40` | `productive` |
| `activity_score < 40` | `low-productivity` |

### Risk Level
| Score | Level | Triggers |
|-------|-------|----------|
| `>= 70` | High | Not focused, browser hidden, wrong tab, idle, many switches |
| `40-69` | Medium | Some red flags present |
| `< 40` | Low | Normal productive behavior |

---

## Signal Collection Workflow

### 1. Initialization
```javascript
// Server-side
const emsSignals = require('./ems_signals');
emsSignals.initializeEmployee(employeeId, sessionId);
```

### 2. Signal Capture (Browser)
```javascript
// Client-side (Browser)
// Window focus
window.addEventListener('focus', () => {
  sendSignal('window_focus', true);
});

// Keystroke
document.addEventListener('keydown', (e) => {
  sendSignal('keystroke', { key: e.key });
});

// Mouse movement
document.addEventListener('mousemove', (e) => {
  sendSignal('mouse_movement', { x: e.clientX, y: e.clientY });
});

// Scroll
document.addEventListener('scroll', () => {
  const percentage = (window.scrollY / document.body.scrollHeight) * 100;
  sendSignal('scroll_depth', { percentage });
});

// Visibility
document.addEventListener('visibilitychange', () => {
  sendSignal('browser_hidden', document.hidden);
});
```

### 3. Signal Processing (Server)
```javascript
// Process received signals
emsSignals.captureKeystroke(employeeId, keystrokeData);
emsSignals.captureMouseMovement(employeeId, mouseData);
emsSignals.captureScrollDepth(employeeId, scrollData);
// ... etc

// Get current state
const state = emsSignals.getSignalState(employeeId);
```

### 4. Live Capture Proof
```javascript
// Console logging proof
const proof = emsSignals.getLiveCaptureProof(employeeId);
// Outputs detailed signal capture information to console
```

---

## API Endpoints

### POST `/api/monitoring/signals`
Receive signals from client

**Request**:
```json
{
  "employeeId": "507f1f77bcf86cd799439011",
  "sessionId": "session_123",
  "signals": [
    {
      "type": "keystroke_rate",
      "value": 45,
      "metadata": { "key": "a" }
    },
    {
      "type": "mouse_movement",
      "value": 35,
      "metadata": { "x": 100, "y": 200 }
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "received": 2,
  "currentState": {
    "window_focus": true,
    "keystroke_rate": 45,
    "mouse_movement": 35,
    "activityScore": 78,
    "productivityIndicator": "highly-productive"
  }
}
```

### GET `/api/monitoring/signals/:employeeId`
Get signal state for employee

**Response**:
```json
{
  "employeeId": "507f1f77bcf86cd799439011",
  "currentState": { ... },
  "lastSignals": [ ... ],
  "statistics": {
    "totalSignals": 1234,
    "signalsLastMinute": 45,
    "activityScore": 78,
    "productivityIndicator": "highly-productive",
    "riskLevel": "low"
  }
}
```

---

## Implementation Checklist

- [x] `ems_signals.js` - Core signal layer implementation
- [x] `signal_spec.md` - Complete specification document
- [ ] Browser signal collector script
- [ ] API endpoints for signal reception
- [ ] Real-time console logging
- [ ] Signal storage/persistence
- [ ] Signal analysis dashboard
- [ ] Alert triggers based on signals

---

## Testing & Validation

### Console Proof Commands
```javascript
// Initialize employee
emsSignals.initializeEmployee('emp001', 'session_001');

// Simulate signals
emsSignals.captureKeystroke('emp001', { key: 'a' });
emsSignals.captureMouseMovement('emp001', { x: 100, y: 200 });
emsSignals.captureWindowFocus('emp001', true);

// View live capture proof
emsSignals.getLiveCaptureProof('emp001');
```

### Expected Console Output
```
🚀 [EMS] Signal Layer initialized
✅ [EMS] Employee emp001 signal tracking initialized
⌨️  [SIGNAL] keystroke_rate - Employee emp001: 1/min - low_activity
🖱️  [SIGNAL] mouse_movement - Employee emp001: 1/min - low_engagement
🔍 [SIGNAL] window_focus - Employee emp001: working

================================================================================
📊 LIVE CAPTURE PROOF - EMS Signal Layer
================================================================================
{
  "timestamp": "2026-01-16T...",
  "employeeId": "emp001",
  "signals_captured": 3,
  "current_state": { ... },
  "live_status": "✅ CAPTURING"
}
================================================================================
```

---

## Performance Considerations

1. **Signal Buffering**: Keep only last 100 signals per employee in memory
2. **Batch Processing**: Send signals in batches every 10 seconds
3. **Throttling**: Throttle mouse/scroll events to max 10/second
4. **Storage**: Persist signals to database every 30 seconds
5. **Memory**: Clear old signals beyond retention period

---

## Security & Privacy

1. **Consent**: Require explicit employee consent before monitoring
2. **Transparency**: Employees can view their own signals
3. **Data Minimization**: Only capture necessary signals
4. **Encryption**: Encrypt signal data in transit and at rest
5. **Access Control**: Only authorized admins can view signals
6. **Retention**: Auto-delete signals after 90 days

---

## Future Enhancements

1. **AI Analysis**: Use ML to detect anomalous behavior patterns
2. **Productivity Scoring**: Advanced scoring algorithms
3. **Team Analytics**: Aggregate signals across teams
4. **Mobile Support**: Extend to mobile devices
5. **Smart Alerts**: Context-aware alerting system
