# PRANA Failure Reality Report

**Status**: Verified via `bucket_bridge.js` logic and ingestion simulation.

## Failure Scenarios & Observation

### 1. Network Interruption
- **Reality**: PRANA uses an `offlineQueue` backed by `localStorage`.
- **Behavior**: If `fetch` fails or `navigator.onLine` is false, packets are persisted locally.
- **Recovery**: Automatic re-transmission of the offline queue occurs when connectivity is restored or every 30 seconds.

### 2. Rapid Activity Transitions
- **Reality**: PRANA throttles emission strictly to 5-second intervals via `setInterval`.
- **Behavior**: High-frequency signals (mouse/keyboard) are aggregated numerically.
- **Storm Traffic**: No storm traffic observed. Emission frequency is detached from interaction frequency.

### 3. Backend Restart / Failure
- **Reality**: `bucket_bridge.js` implements a retry mechanism:
  - **Max Retries**: 3 attempts per packet.
  - **Backoff**: Exponential (1s, 2s, 4s).
  - **Fail-Open**: If the backend remains down after retries, the packet is moved back to the offline queue to prevent data loss.

### 4. Tab Refresh
- **Reality**: Refresh clears the in-memory packet builder.
- **Behavior**: The current 5-second window is lost, but no partial or corrupt packets are emitted. A new window starts immediately on reload.

## Failure Posture: Fail-Safe & Durable
PRANA currently operates with a **Fail-Safe** posture rather than the "Fail-Open (Discard)" posture mentioned in the Canon. It prioritizes data integrity through local persistence and retries.

- **Retry Policy**: YES (3 retries).
- **Storm Traffic**: NO (Strict 5s throttle).
- **Packet Loss**: Extremely low (Buffered in `localStorage`).
- **Duplicates**: Possible if ingestion succeeds but acknowledgement fails.
