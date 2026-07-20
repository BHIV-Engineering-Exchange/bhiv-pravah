# PRANA-G Demo Video Script

## Video Title: "PRANA-G: Gurukul Cognitive Telemetry Engine in Action"

## Duration: 2-3 minutes

---

## Scene 1: Introduction (0:00-0:20)
**Visual**: Show the Gurukul learning platform interface
**Narration**: "Welcome to PRANA-G, the cognitive telemetry engine that creates the nervous system of Gurukul. Today we'll demonstrate how it captures real human behavior and converts it into clean, machine-readable signals for the BHIV Bucket."

---

## Scene 2: Signal Layer Foundation (0:20-0:50)
**Visual**: Show browser console with live signal capture
**Code Highlight**: signals.js capturing various behaviors
**Narration**: "PRANA-G captures 8 core behavioral signals in real-time:
- dwell_time_ms: Sustained reading and focus duration
- hover_loops: Indecision and uncertainty patterns
- rapid_clicks: Anxiety and frustration indicators
- scroll_depth: Engagement level measurement
- mouse_velocity: Calm versus agitated states
- inactivity_ms: Idle and distraction periods
- tab_visible: Away from desk detection
- panel_focused: Mental focus on task"

---

## Scene 3: Cognitive State Engine (0:50-1:20)
**Visual**: Show state transitions in console
**Code Highlight**: prana_state_engine.js
**Narration**: "The deterministic state engine tracks 7 cognitive states without flickering:
- ON_TASK: Focused on current task
- THINKING: Processing information
- IDLE: Temporary pause
- DISTRACTED: Brief distraction
- AWAY: Away from desk
- OFF_TASK: Completely off-task
- DEEP_FOCUS: Intense concentration

Every state transition is logged with cooldowns to prevent flickering."

---

## Scene 4: PRANA Packet Builder (1:20-1:50)
**Visual**: Show live packet generation in console
**Code Highlight**: prana_packet_builder.js
**Narration**: "Every 5 seconds, the packet builder generates structured telemetry data containing:
- user_id: Authenticated user identifier
- session_id: Current learning session
- lesson_id: Active lesson context
- timestamp: Precise timing
- cognitive_state: Current mental state
- Time accounting: active, idle, and away seconds
- focus_score: Deterministic 0-100 score
- raw_signals: All behavioral data"

---

## Scene 5: Context Integration (1:50-2:10)
**Visual**: Show lesson creation and context propagation
**Code Highlight**: contextManager.js and AuthContext.jsx
**Narration**: "The system seamlessly integrates with backend authentication and creates proper lesson contexts. When a user starts learning, a unique lesson_id is generated and propagated through the system, ensuring all telemetry is properly attributed."

---

## Scene 6: Bucket Integration (2:10-2:30)
**Visual**: Show packets being sent to bucket
**Code Highlight**: bucket_bridge.js
**Narration**: "All packets are securely transmitted to the BHIV Bucket with retry safety, offline queuing, and no data loss. The system maintains zero UI impact while continuously streaming cognitive telemetry."

---

## Scene 7: Live Demonstration (2:30-2:50)
**Visual**: Show actual user interaction with live packet generation
**Narration**: "Here's PRANA-G in action - as the user interacts with the learning platform, you can see real-time packet generation with accurate cognitive states and behavioral signals. The system operates silently in the background without interfering with the learning experience."

---

## Scene 8: Conclusion (2:50-3:00)
**Visual**: Show complete system architecture diagram
**Narration**: "PRANA-G transforms a learning website into a learning being by creating a real-time, deterministic, non-manipulable telemetry engine that drives karma, trust, learning state, and adaptive intelligence across the entire Gurukul ecosystem."

---

## Technical Notes:
- All signals are captured passively with zero UI impact
- No fake or guessed data - all from actual user behavior
- System works across all browsers and devices
- Minimal performance overhead
- Secure authentication and session management
- Proper error handling and retry mechanisms