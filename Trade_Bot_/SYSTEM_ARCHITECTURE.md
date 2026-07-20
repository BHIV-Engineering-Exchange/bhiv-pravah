## Samruddhi System Architecture (High-Level)

This document provides a high-level architecture diagram of the Samruddhi system as deployed via Docker Compose.

---

## Logical Architecture

```text
                +-----------------------------+
                |        Client Browser       |
                |   (User Trading Dashboard)  |
                +--------------+--------------+
                               |
                               |  HTTPS / HTTP (port 5173 in local)
                               v
                    +----------+-----------+
                    |   Frontend Service   |
                    |   (React, Vite)      |
                    |   Container: frontend|
                    +----------+-----------+
                               |
                               | REST / WebSocket / HTTP
                               v
      +------------------------+---------------------------+
      |                                                    |
      |                                                    |
      v                                                    v
+-----+------------------+                 +---------------+------+
|  Backend Service       |                 |  Backend-2 Service   |
|  (FastAPI)             |                 |  (HFT / secondary)   |
|  Container: backend    |                 |  Container: backend-2 |
|  Port: 8000            |                 |  Port: 5000           |
+-----------+------------+                 +-----------+-----------+
            |                                          |
            |                                          |
            |          Internal Service-to-Service     |
            |          Communication over HR_network   |
            v                                          v
     +------+------------------------------------------+------+
     |                 MongoDB Service                       |
     |                 Container: mongo                      |
     |                 Port: 27017                           |
     |                 Volume: mongo_data                    |
     +------------------------------------------------------+
```

---

## Deployment / Runtime View

All services run as containers defined in `docker-compose.yml`:

- `mongo` (database)
- `backend` (FastAPI)
- `backend-2` (HFT / secondary backend)
- `frontend` (React dashboard)

They are connected via the `HR_network` Docker bridge network.

### Ports (Local)

- `frontend`: `5173` (user accesses the dashboard here)
- `backend`: `8000` (API and health endpoint `/tools/health`)
- `backend-2`: `5000` (API and health endpoint `/api/health`)
- `mongo`: `27017` (database)

### Volumes

- `mongo_data` — stores MongoDB data to persist across container restarts.

---

## Health, Restart and Monitoring Hooks

- **Healthchecks**
  - Docker-level:
    - `mongo`: ping via `mongosh`.
    - `backend`: `curl -f http://localhost:8000/tools/health`.
    - `backend-2`: `curl -f http://localhost:5000/api/health`.
  - Script-level:
    - `scrtips/healthcheck.sh` probes each main endpoint and shows `docker compose ps`.

- **Restart Policies**
  - All main services configured with:
    - `restart: unless-stopped`
  - This provides automatic restart on crash/unhealthy state.

- **Operational Scripts**
  - `scrtips/deploy.sh` — build + up.
  - `scrtips/stop.sh` — down.
  - `scrtips/restart.sh` — restart + status.
  - `scrtips/logs.sh` — logs tail/follow.
  - `scrtips/healthcheck.sh` — consolidated health checks.

These hooks can be integrated into external monitoring / alerting systems by the internal infrastructure team.

---

## Data Flow Summary

1. **User** interacts with the **Frontend** in the browser.
2. **Frontend** calls **Backend** (and optionally **Backend-2**) over HTTP/WebSocket.
3. **Backends** read/write data in **MongoDB**.
4. **Docker** orchestrates container lifecycle, healthchecks, and restarts based on `docker-compose.yml`.

