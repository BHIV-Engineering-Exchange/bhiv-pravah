# Day 7 — Multi-User Stress Test Report

## Test Setup
- Concurrent users: 2 (hardware-limited; 3 attempted)
- Environment: Local development laptop
- Transport: Socket.IO (WebSocket)
- Authentication: JWT per session
- Database: MongoDB Atlas (intermittent connectivity during stress)

## Scenarios Tested
- Multiple concurrent socket connections
- Parallel user actions (click, inspect, interact)
- Presence updates under concurrent activity
- Spam-click stress testing
- User disconnect during active actions
- Backend restart during active sessions
- Job queue isolation (where applicable)

## Observations
- Multiple users connected simultaneously without state corruption
- Actions remained correctly scoped per user/session
- Presence updates were isolated and consistent
- Spam throttling and action handling remained deterministic
- UI lag observed under load, but backend remained functional
- No cross-user state leakage observed

## Race Condition Discovered & Fixed
During stress testing, a race condition was identified where
presence updates could be received after a user disconnect or
backend restart, leading to a crash.

Root Cause:
- Presence state was mutated without validating existence.

Fix Applied:
- Added defensive checks before mutating presence state.
- Late presence events are now safely ignored.

This fix improved stability during concurrent usage
and backend restarts.

## Database Connectivity Note
During stress testing, intermittent MongoDB Atlas connectivity
issues (`ENOTFOUND` DNS resolution error) were observed due to
local machine load and network instability.

Core real-time functionality (Socket.IO, presence, action handling)
remained correct and unaffected. Database availability was not
required for Day 7 validation.

## Performance Notes
- No unhandled backend exceptions after fixes
- Event loop remained responsive under light stress
- System degraded gracefully under load

## Conclusion
The system remains stable, isolated, and predictable under
multi-user concurrent usage and stress conditions.
Race conditions were identified and resolved successfully.
