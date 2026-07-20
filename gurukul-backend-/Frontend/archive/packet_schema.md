# PRANA Packets

What gets sent every 5 seconds.

## Packet Structure

```javascript
{
  user_id,           
  session_id,        
  lesson_id,         // optional (null | string)
  system_type,       // "gurukul" | "ems"
  role,              // "student" | "employee"
  timestamp,         
  cognitive_state,   
  active_seconds,    
  idle_seconds,      
  away_seconds,      
  focus_score,       // 0-100, deterministic
  raw_signals        
}
```

## Key Fields

### Context Fields
- **user_id** - From backend auth (JWT token)
- **session_id** - From backend auth (JWT token, session UUID)
- **lesson_id** - Optional, from current lesson context (null | string)
- **system_type** - System identifier: "gurukul" or "ems"
- **role** - User role: "student" (Gurukul) or "employee" (EMS)

### Time Accounting (Always = 5.0 seconds)
- **active_seconds** - Learning time
- **idle_seconds** - No interaction time
- **away_seconds** - Tab hidden time

**Rule:** active + idle + away = exactly 5.0

### cognitive_state
Your current mental state (one of 7):
- ON_TASK, THINKING, IDLE, DISTRACTED, AWAY, OFF_TASK, DEEP_FOCUS

### focus_score (0-100)
Quality of attention:
- 95 = Deep focus, perfect
- 75 = On task, good
- 30 = Distracted
- 0 = Away/hidden tab

**How calculated:**
1. Base score from state
2. Penalties for anxiety/high velocity
3. Multiply by active time ratio

### raw_signals
All 8 behavior signals:
- dwell_time_ms
- hover_loops  
- rapid_click_count
- scroll_depth
- mouse_velocity
- inactivity_ms
- tab_visible
- panel_focused

## Example Packets

### Active Learning (Gurukul)
```json
{
  "user_id": "d0e9e650-1ee1-49c3-b278-bd6b903b8848",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "lesson_id": "lesson_123",
  "system_type": "gurukul",
  "role": "student",
  "timestamp": "2026-01-15T12:45:23.456Z",
  "cognitive_state": "ON_TASK",
  "active_seconds": 5.0,
  "idle_seconds": 0.0,
  "away_seconds": 0.0,
  "focus_score": 72,
  "raw_signals": {
    "dwell_time_ms": 145670,
    "scroll_depth": 45,
    "mouse_velocity": 650,
    "inactivity_ms": 890,
    "tab_visible": true,
    "panel_focused": true
  }
}
```

### Tab Switched Away (EMS)
```json
{
  "user_id": "employee_456",
  "session_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "lesson_id": null,
  "system_type": "ems",
  "role": "employee",
  "timestamp": "2026-01-15T12:45:28.456Z",
  "cognitive_state": "AWAY",
  "active_seconds": 1.2,
  "idle_seconds": 0.0,
  "away_seconds": 3.8,
  "focus_score": 0,
  "raw_signals": {
    "tab_visible": false,
    "inactivity_ms": 3800,
    "window_focus": false,
    "browser_visibility": "hidden"
  }
}
```

## Timing

**Emits:** Every 5 seconds exactly  
**Window:** Each packet = previous 5 seconds  
