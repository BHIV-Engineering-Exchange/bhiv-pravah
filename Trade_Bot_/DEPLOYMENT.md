## Samruddhi Deployment Guide (Local Docker)

This document explains how to run the Samruddhi system locally using Docker and Docker Compose.
It is designed so that an authorised engineer can bring the system up or down in under 10 minutes.

> **Security note**: Do not put real credentials or production secrets into `.env` files or this document.

---

## Prerequisites

- Docker Engine installed
- Docker Compose v2 (bundled with recent Docker Desktop)
- Git (optional, for pulling updates)

---

## Project Structure (Deployment-Relevant)

- `docker-compose.yml` — defines all runtime services:
  - `mongo` (database)
  - `backend` (FastAPI)
  - `backend-2` (HFT / secondary backend)
  - `frontend` (React trading dashboard)
- `backend/` — main backend service source and Dockerfile.
- `backend/hft2/backend/` — secondary backend (HFT) service and Dockerfile.
- `trading-dashboard/` — React frontend and Dockerfile.
- `.env` and related env files — **dummy / local values only**.
- `scrtips/` — helper scripts for Day-5 deployment and health management:
  - `deploy.sh`
  - `stop.sh`
  - `restart.sh`
  - `logs.sh`
  - `healthcheck.sh`

---

## Services Overview

All services are defined in `docker-compose.yml` and connected via the `HR_network` bridge network.

- **mongo**
  - Image: `mongo:7`
  - Port: `27017:27017`
  - Uses local volume `mongo_data` for persistence.
  - Healthcheck: MongoDB ping using `mongosh`.
  - Restart policy: `restart: unless-stopped`

- **backend**
  - Build context: `./backend`
  - Port: `8000:8000`
  - Healthcheck: `curl -f http://localhost:8000/tools/health`
  - Restart policy: `restart: unless-stopped`

- **backend-2**
  - Build context: `./backend/hft2/backend`
  - Port: `5000:5000`
  - Healthcheck: `curl -f http://localhost:5000/api/health`
  - Restart policy: `restart: unless-stopped`

- **frontend**
  - Build context: `./trading-dashboard`
  - Port: `5173:5173`
  - `env_file`: `./trading-dashboard/.env` (dummy values only)
  - Depends on: `backend`
  - Restart policy: `restart: unless-stopped`

---

## Environment Configuration

Environment variables are injected using `.env` files. Only dummy / local values should be committed.

- Root `.env` and any `.env` files inside services must **not** contain production secrets.
- For production, an internal deployment authority must inject real credentials at deploy time.

Suggested pattern (already aligned with the task PDF):

- `.env.example` — example values for local development.
- `.env.development.template` — template for development environments.
- `.env.production.template` — template for production environments (without real secrets).

---

## Basic Local Lifecycle (Using Scripts)

From the `Trade_Bot_` project root:

### Start / Deploy

```bash
bash scrtips/deploy.sh
```

This will:

- Build all images defined in `docker-compose.yml`:
  - `mongo`, `backend`, `backend-2`, `frontend`
- Start all services in detached mode via:
  - `docker compose build`
  - `docker compose up -d`

### Stop

```bash
bash scrtips/stop.sh
```

This will:

- Stop and remove the running containers using:
  - `docker compose down`

### Restart

```bash
bash scrtips/restart.sh
```

This will:

- Restart all running services:
  - `docker compose restart`
- Show current container status:
  - `docker compose ps`

### View Logs

```bash
bash scrtips/logs.sh
```

This will:

- Tail the last 200 lines of logs for all services.
- Follow logs in real time until you press `Ctrl + C`.

You can optionally pass service names to narrow logs:

```bash
bash scrtips/logs.sh backend
```

---

## Health Checks and Failure Recovery

### Docker-Level Healthchecks

`docker-compose.yml` defines healthchecks for:

- `mongo` (ping)
- `backend` (`/tools/health`)
- `backend-2` (`/api/health`)

These are used by Docker to track container health and work together with:

- `restart: unless-stopped`

to automatically restart unhealthy or crashed containers.

### Script-Level Health Checks

```bash
bash scrtips/healthcheck.sh
```

This script:

- Shows `docker compose ps` (status of all services).
- Uses `curl` (if available) to probe:
  - `http://localhost:8000/tools/health` (backend)
  - `http://localhost:5000/api/health` (backend-2)
  - `http://localhost:5173` (frontend)

If any endpoint is unreachable, it will print an "UNHEALTHY or not reachable" message.

---

## Monitoring Integration Readiness (No External Tools)

This system is prepared for monitoring integration by:

- Providing consistent health endpoints for backends.
- Enabling Docker healthchecks on critical services.
- Using `restart: unless-stopped` for auto-restart on crash.
- Offering scriptable entry points:
  - `deploy.sh`, `stop.sh`, `restart.sh`, `logs.sh`, `healthcheck.sh`

An internal team can plug in:

- Centralised logging (Docker log drivers, sidecar containers, etc.).
- Metrics exporters (Prometheus, etc.) behind the defined endpoints.
- Dashboards built on top of these health and log signals.

---

## Crash Recovery Test (Manual)

To validate crash recovery manually:

1. Start the stack:
   ```bash
   bash scrtips/deploy.sh
   ```
2. Confirm services:
   ```bash
   docker compose ps
   ```
3. Simulate a crash by stopping one container, for example:
   ```bash
   docker stop trade_bot-backend-1   # name will vary; check docker compose ps
   ```
4. Observe Docker automatically restarting the container due to:
   ```yaml
   restart: unless-stopped
   ```
5. Run:
   ```bash
   bash scrtips/healthcheck.sh
   ```
   to confirm everything is healthy again.

> Container names depend on your Docker Compose project name; use `docker compose ps` to see exact names.

