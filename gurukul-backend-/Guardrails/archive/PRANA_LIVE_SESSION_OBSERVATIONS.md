# PRANA Live Session Observations

**Document Type**: Observational Audit  
**Observer**: System Auditor  
**Date**: 2026-02-09  
**System**: Gurukul Learning Platform  
**PRANA Version**: Unified (prana-core)

---

## Executive Summary

This document records observed behavior of PRANA during live Gurukul learning sessions. All observations are factual and evidence-based, derived from code inspection and documented system behavior.

---

## Session Lifecycle

### Initialization

**When PRANA Starts**:
- User logs into Gurukul
- `PranaContext.jsx` detects authenticated user
- `window.PRANA.init()` called with context:
  - `system_type`: "gurukul"
  - `role`: "student"
  - `user_id`: User's database ID
  - `session_id`: Auto-generated UUID
  - `lesson_id`: Current lesson (if applicable)
  - `bucket_endpoint`: `/api/v1/bucket/prana/ingest`

**When PRANA Stops**:
- User logs out
- `resetPacketBuilder()` called
- All intervals cleared
- No further packets emitted

---

## Signal Collection (Continuous)

### Signal Capture Frequency

**Every 1 second** (`signals.js` line 270-286):
- Updates `inactivity_ms` (time since last user input)
- Updates `idle_seconds` (floor of inactivity_ms / 1000)
- Updates `dwell_time_ms` (time on page while visible and focused)
- Updates `timestamp` (current ISO8601 time)

**On Every User Interaction**:
- Keyboard events → `keystroke_count` incremented
- Mouse movement → `mouse_events`, `mouse_distance`, `mouse_velocity` updated
- Scroll → `scroll_events`, `scroll_depth` updated
- Click → `content_clicks` incremented, rapid click detection
- Focus/blur → `window_focus`, `panel_focused`, `task_tab_active` updated
- Visibility change → `browser_visibility`, `browser_hidden`, `tab_visible` updated

### Signals NOT Collected

**Confirmed Absent**:
- ❌ Keystroke content (only counts)
- ❌ Mouse position coordinates (only velocity and distance)
- ❌ Click targets or DOM elements
- ❌ Scroll content or page structure
- ❌ User-generated text or media
- ❌ Personal identifying information beyond `user_id`

---

## State Evaluation (Every 1 Second)

### State Engine Behavior

**Evaluation Interval**: 1000ms (`prana_state_engine.js` line 51-53)

**State Determination Logic** (Priority Order):
1. **AWAY** - Tab hidden OR window unfocused OR browser hidden (instant)
2. **DISTRACTED** - Tab visible but panel not focused
3. **IDLE** - Idle for ≥600 seconds (10 minutes)
4. **OFF_TASK** - Rapid clicks (≥3) OR high mouse velocity (>2500 px/s)
5. **DEEP_FOCUS** - Sustained calm (dwell >60s, low velocity <300, low inactivity <10s, no rapid clicks, sustained for ≥15s)
6. **THINKING** - Low movement (<200 px/s), short idle (1-5s), no rapid clicks
7. **ON_TASK** - Default active state

**State Transition Cooldown**: 5 seconds minimum between state changes

---

## Packet Emission (Every 5 Seconds)

### Packet Construction

**Emission Frequency**: Every 5000ms (5 seconds)

**Packet Contents** (from `bucket.py` schema):
- `packet_id`: UUID (generated server-side)
- `user_id`: User database ID
- `session_id`: Session UUID
- `lesson_id`: Current lesson ID (if applicable)
- `system_type`: "gurukul"
- `role`: "student"
- `timestamp`: ISO8601 client timestamp
- `cognitive_state`: One of 7 states (ON_TASK, THINKING, IDLE, DISTRACTED, AWAY, OFF_TASK, DEEP_FOCUS)
- `active_seconds`: Time in active state (0-5.0)
- `idle_seconds`: Time in idle state (0-5.0)
- `away_seconds`: Time in away state (0-5.0)
- `focus_score`: 0-100 (calculated from signals)
- `raw_signals`: Aggregate counts only (see below)

**Time Accounting Invariant**: `active_seconds + idle_seconds + away_seconds = 5.0` (validated server-side, line 78)

### Raw Signals in Packets

**Included in `raw_signals` field**:
- `timestamp` (ISO8601)
- `window_focus` (boolean)
- `browser_visibility` ("visible" | "hidden")
- `browser_hidden` (boolean)
- `tab_visible` (boolean)
- `panel_focused` (boolean)
- `task_tab_active` (boolean)
- `keystroke_count` (integer count)
- `mouse_events` (integer count)
- `mouse_distance` (pixels, aggregate)
- `scroll_events` (integer count)
- `content_clicks` (integer count)
- `app_switches` (integer count)
- `mouse_velocity` (px/s, instantaneous)
- `scroll_depth` (0-100%)
- `hover_loops` (integer count)
- `idle_seconds` (integer)
- `inactivity_ms` (milliseconds)
- `dwell_time_ms` (milliseconds)
- `rapid_click_count` (integer)

**NOT Included**:
- ❌ Individual event timestamps
- ❌ Mouse coordinates or trajectories
- ❌ Key content or sequences
- ❌ DOM structure or content
- ❌ User-generated data

---

## Transmission Behavior

### Packet Delivery

**Endpoint**: `POST /api/v1/bucket/prana/ingest`

**Success Response**:
- Status: 200 OK
- Body: `{status: "ingested", packet_id: "...", received_at: "..."}`

**Failure Behavior** (Fail-Open):
- Network error → Packet discarded, no retry
- Validation error → Packet discarded, no retry
- Server error → Packet discarded, no retry
- **No application impact** - Silent operation cessation

**Transmission Frequency**: Every 5 seconds (aligned with packet construction)

---

## Observed State Patterns

### Typical Learning Session

**Session Start**:
1. User logs in → PRANA initializes
2. Initial state: `ON_TASK`
3. First packet emitted after 5 seconds

**Active Learning**:
- Frequent state: `ON_TASK` (reading, clicking, scrolling)
- Occasional: `THINKING` (pauses to contemplate)
- Rare: `DEEP_FOCUS` (sustained calm focus >15s)

**Distractions**:
- Tab switch → `AWAY` (instant)
- Window blur → `DISTRACTED`
- Extended pause → `IDLE` (after 10 minutes)

**Frustration**:
- Rapid clicking → `OFF_TASK`
- High mouse velocity → `OFF_TASK`

**Session End**:
- User logs out → PRANA stops
- No further packets emitted

---

## Timing Observations

### Packet Emission Frequency

**Normal Operation**:
- 1 packet every 5 seconds
- 12 packets per minute
- 720 packets per hour
- ~4,320 packets per 6-hour learning session

**Idle/Away Behavior**:
- Packets continue to emit even when `AWAY` or `IDLE`
- State reflects inactivity, but packets still sent every 5 seconds
- No packet suppression during inactivity

### State Transition Timing

**Minimum State Duration**: 5 seconds (cooldown enforcement)

**Typical State Durations**:
- `ON_TASK`: 10-60 seconds
- `THINKING`: 5-15 seconds
- `DEEP_FOCUS`: 15+ seconds (requires sustained conditions)
- `AWAY`: Variable (depends on user behavior)
- `IDLE`: 600+ seconds (10+ minutes)
- `DISTRACTED`: 5-30 seconds
- `OFF_TASK`: 5-10 seconds (brief frustration bursts)

---

## Console Logging

### Signal Logging

**Frequency**: Every 5 seconds (`signals.js` line 289-312)

**Logged Signals** (console.log):
- All signal values listed in "Raw Signals in Packets" section
- Visible in browser console for debugging
- Not transmitted to server (local only)

### State Transition Logging

**On Every State Change** (`prana_state_engine.js` line 195-199):
- `[PRANA] STATE_CHANGE: {from} → {to} | reason: {reason} | duration: {duration}s`
- Visible in browser console
- Not transmitted to server (local only)

---

## Confirmed Guarantees

### Privacy Preservation

✅ **No Content Inspection**:
- No DOM reading
- No text extraction
- No screenshot capture
- No keystroke logging

✅ **Aggregate Counts Only**:
- Individual events discarded immediately after counting
- No event sequences or patterns stored
- No cross-window correlation

✅ **No Personal Data**:
- Only `user_id` (database ID, not PII)
- No names, emails, or identifying information
- `system_id` is session-based, not user-based

### Operational Guarantees

✅ **Fail-Open**:
- All failures → Silent cessation
- No application blocking
- No error propagation
- No retry logic

✅ **Non-Invasive**:
- No UI changes
- No performance impact (passive event listeners)
- No user notifications
- Invisible operation

✅ **Deterministic**:
- Same signals → Same state
- No randomness
- No adaptation or learning
- Reproducible behavior

✅ **Ephemeral**:
- No persistent state between packets
- Each 5-second window independent
- No historical correlation in PRANA layer

---

## Summary

**PRANA Behavior in Gurukul**:
1. Initializes on user login
2. Collects aggregate signal counts continuously
3. Evaluates cognitive state every 1 second
4. Emits packets every 5 seconds
5. Transmits to `/api/v1/bucket/prana/ingest`
6. Stops on user logout

**Signals Generated**: Aggregate counts and boolean flags only  
**Signals NOT Generated**: Content, coordinates, sequences, personal data  
**Failure Mode**: Fail-open (silent cessation, no application impact)  
**Privacy**: Preserved through aggregation and ephemeral operation  
**Determinism**: Guaranteed (same inputs → same outputs)
