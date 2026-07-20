# Global Failure Recovery Matrix

| Component | Failure | Detection | Recovery Action |
| :--- | :--- | :--- | :--- |
| **Core API** | 500 / Hang | `/health` (Core) | Watchdog Restart (<20s) |
| **EMS API** | 500 / Hang | `/health` (EMS) | Watchdog Restart (<20s) |
| **Frontend** | Asset Not Found | Vite build error | Deployment halt & rollback |
| **DB (SQL)** | Conn Pool Full | `/health` (DB) | Pool Recycle + Retry logic |
| **MongoDB** | Ping Timeout | `/health` (Warn) | Lazy Reconnection |

## Emergency Command
To restore the entire system to the last stable state, run:
`./yashika\ task/rollback_all.sh`
