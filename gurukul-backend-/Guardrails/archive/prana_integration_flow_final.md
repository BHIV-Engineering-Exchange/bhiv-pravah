# PRANA Integration Flow - Final Canonical Specification

## Purpose

Single canonical integration flow: signal capture to bucket append. No alternative paths or branches.

## Flow Steps

### Step 1: Signal Capture
- Frontend loads PRANA signal capture module
- Event listeners attached to DOM events (keyboard, mouse, touch, scroll, focus, route, search, content)
- Events generate signal objects with type and timestamp
- Signals emitted to collection system

### Step 2: Signal Collection
- Signals received and timestamped
- Added to current observation window buffer
- Signal counters incremented per type
- Continues until window boundary

### Step 3: Observation Window Boundary
- Timer fires every 2 seconds
- Current window marked complete
- Window buffer frozen
- New buffer created for next window
- Frozen buffer passed to state evaluation

### Step 4: State Evaluation
- Extract signal counts from frozen buffer
- Evaluate signals against state definitions
- Apply state priority order if multiple match
- Select highest-priority matching state
- If no match → IDLE

### Step 5: Packet Construction
- Receive state, signal counts, timestamp, duration
- Retrieve system metadata (system_id, prana_version, window_id)
- Construct JSON payload per schema
- Validate and serialize to JSON
- Emit to transmission layer

### Step 6: Packet Transmission
- Receive JSON packet
- Retrieve endpoint URL and auth token
- Construct HTTP POST request
- Send request (timeout: 5s)
- On success (200/201/202) → Success
- On failure (4xx/5xx/timeout) → Discard packet

### Step 7: Bucket Append
- Bucket receives HTTP POST
- Validates authentication and payload
- If valid → Store packet, return 200/201/202
- If invalid → Reject, return 400/401/403

## Flow Completion

**Success:** Signal capture → Collection → Window → State → Packet → Transmission → Bucket (success) → Next window

**Failure:** Any step fails → Failure handling → Packet discarded → Next window

## Flow Guarantees

- **Determinism:** Same signals → Same state → Same packet
- **Non-Blocking:** Failures do not block application
- **Fail-Open:** Failures → Silent packet discard
- **Ephemeral:** No persistent state between windows

## Flow Timing

- **Window Duration:** Fixed 2 seconds
- **Step Timing:** < 1.5s typical, 5s max (transmission timeout)
- **Total Duration:** Completes before next window begins

## Flow Dependencies

**External:**
- Frontend browser environment (DOM, JavaScript, Timer API)
- Network infrastructure (HTTPS, DNS, TLS)
- Bucket system (endpoint, auth, storage)

**Internal:**
- Signal capture → Collection (emission mechanism)
- Collection → Window (timer, buffer freezing)
- Window → State (buffer passing)
- State → Packet (metadata retrieval)
- Packet → Transmission (JSON serialization, HTTP client)
- Transmission → Bucket (network, endpoint availability)
