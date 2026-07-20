# Demo Recording Notes (10-15 minutes)

1. Start from cold:
   - `python -m runtime_manager` (with sprint folder added to `PYTHONPATH`).
   - Show all 10 services healthy in startup output and `runtime_status.json`.

2. Crash recovery:
   - Kill one service (`bhiv_core` or `telemetry`) with `taskkill`.
   - Show auto-restart in runtime logs and incremented restart counters in `/dashboard/runtime`.

3. Run production demo:
   - Execute `python "SHAKTI Production Convergence Sprint (Energy Intelligence Platform Production Transition)/demo/production_demo.py"`.
   - Narrate chain: telemetry received -> signal generated -> decision -> alert -> dashboard -> audit -> replay.

4. Show observability APIs:
   - `GET /metrics`
   - `GET /system/status`
   - `GET /dashboard/executive`
   - `GET /dashboard/operations`
   - `GET /dashboard/alerts`
   - `GET /dashboard/runtime`
   - `GET /dashboard/telemetry`

5. Graceful stop:
   - Send stop signal to runtime manager process (SIGTERM equivalent on Windows shell termination).
   - Show services terminate and no orphan listeners remain.

6. Close with paper trail:
   - Open root `REVIEW_PACKET.md`.
   - Open sprint `Implementation.md`.
