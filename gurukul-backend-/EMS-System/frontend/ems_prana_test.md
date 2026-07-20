## EMS + PRANA-E Manual Test Scenarios

All tests assume:
- EMS frontend is running and `ems_signals.js`, `prana_e_packet_builder.js`, and `bucket_bridge.js` are active.
- EMS backend Bucket endpoint is running at `http://localhost:8000/bucket/prana/ingest`.
- DevTools Console is open (for logs).

---

### 1. Active typing → WORKING

- **Setup**: Log in as any user (teacher/student/admin/parent). Stay on a dashboard or task page.
- **Action**: For at least 10 seconds:
  - Type into an input (search, form, etc.).
  - Scroll occasionally.
- **Expected EMSSignals behavior**:
  - `window_focus = true`
  - `browser_visibility = "visible"`
  - `idle_seconds` stays low (< 10)
  - `keystroke_count`, `mouse_events`, `scroll_events` > 0 across windows
- **Expected PRANA-E packets**:
  - `state = "WORKING"` in recent packets
  - `active_seconds ≈ 5`, `idle_seconds = 0`, `away_seconds = 0`
  - `integrity_score` close to `1.0`

---

### 2. Tab open, no interaction → IDLE → FAKING

- **Setup**: Log in and open a dashboard page. Stop interacting.
- **Action**:
  - Do nothing in the EMS tab for at least 40–70 seconds.
- **Expected EMSSignals behavior**:
  - `window_focus = true`
  - `browser_visibility = "visible"`
  - `idle_seconds` increases steadily past 10, 30, and beyond
  - Activity counts (`keystroke_count`, `scroll_events`, `content_clicks`) stay at 0
- **Expected PRANA-E packets**:
  - For `idle_seconds` between 10 and 30:
    - `state = "IDLE"`
    - `active_seconds = 0`, `idle_seconds ≈ 5`
  - After `idle_seconds >= 30` with almost no activity:
    - `state = "FAKING"`
    - `active_seconds = 0`, `idle_seconds ≈ 5`
    - `integrity_score` reduced by at least `0.4` for FAKING and by `0.2` for high idle time.

---

### 3. App switch / other tab → DISTRACTED

- **Setup**: Log in and actively work for a few seconds.
- **Action**:
  - Click into another browser tab or app while keeping EMS visible in the background.
  - Frequently switch away and back within a short period.
- **Expected EMSSignals behavior**:
  - `app_switches` increases when focus/visibility changes.
  - Periods where `window_focus` may be true but `task_tab_active` becomes false.
- **Expected PRANA-E packets**:
  - Some packets with:
    - `state = "DISTRACTED"`
    - `active_seconds = 0`, `idle_seconds ≈ 5`
  - If `app_switches > 3` within the window:
    - `integrity_score` reduced by `0.2` for app switching.

---

### 4. Tab minimized / backgrounded → AWAY

- **Setup**: Log in and open EMS dashboard.
- **Action**:
  - Minimize the browser window OR switch to a different application and leave EMS completely in the background for at least 60 seconds.
- **Expected EMSSignals behavior**:
  - `browser_visibility = "hidden"` when minimized/backgrounded.
  - `idle_seconds` climbs above 60.
- **Expected PRANA-E packets**:
  - `state = "AWAY"` once both conditions meet:
    - `!window_focus` OR `browser_visibility === "hidden"`
    - **and** `idle_seconds >= 60`
  - `away_seconds ≈ 5`, `active_seconds = 0`, `idle_seconds = 0`
  - `integrity_score` reduced by `0.5` for AWAY.

---

### 5. Fake mouse movement → Integrity drop

- **Setup**: Log in and open EMS.
- **Action**:
  - Do not type or scroll.
  - Occasionally wiggle the mouse (minimal movement) every few seconds to try to look “active”.
- **Expected EMSSignals behavior**:
  - `mouse_events` > 0 in windows.
  - `keystroke_count = 0`, `scroll_events = 0`, `content_clicks` ~ 0.
- **Expected PRANA-E packets**:
  - State may be `IDLE` or `FAKING` depending on `idle_seconds`.
  - Integrity rule: “mouse_events only (no keys/scroll)” triggers:
    - `integrity_score` reduced by `0.1` even if not AWAY/FAKING.

---

### 6. Bucket ingestion verification

- **Setup**: Ensure EMS backend is running (`http://localhost:8000`) and the `/bucket/prana/ingest` route is available.
- **Action**:
  - With EMS frontend open for at least 15–30 seconds, perform any normal activity.
- **Expected Backend behavior**:
  - Console or logs show POSTs to `/bucket/prana/ingest`.
  - Response body from backend similar to:
    - `{ "status": "success", "received": <number_of_packets> }`
- **Expected Frontend behavior**:
  - DevTools console logs from `BucketBridge`:
    - `[PRANA-E][BucketBridge] first-attempt success: { status: "success", received: ... }`
  - On network failure, a retry attempt is logged once, then a clear error.


