# Hardened Global Startup Sequence Table

| Order | Service | Layer | Action | Protection |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Infrastructure | Docker/Network | Bridge creation & Sec-headers | Docker Runtime |
| 2 | Core Backend | API | Watchdog Init + Auth Router | 20s Watchdog |
| 3 | EMS Backend | API | PostgreSQL Handshake | 20s Watchdog |
| 4 | DB Tier | SQL/Mongo | Connection Pool Priming | Pool Pre-ping |
| 5 | PRANA | Logic | Telemetry Check | Self-Healing |
| 6 | Frontend | Client | Env-audit (`VITE_API_URL`) | Build-stop |
| 7 | All | Health | Unified `/health` Reporting | Real-time Dashboard |

**Orchestrator Verdict**: If any critical service fails the startup handshake, the system logs a `FATAL_WATCHDOG_EXIT` and prevents the ingress from routing traffic to the unstable node.
