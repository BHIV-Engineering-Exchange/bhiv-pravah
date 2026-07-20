#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "[healthcheck.sh] Running health checks for Samruddhi stack..."

if ! command -v docker >/dev/null 2>&1; then
  echo "[healthcheck.sh] ERROR: docker is not installed or not in PATH."
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "[healthcheck.sh] WARNING: curl is not installed; HTTP health checks will be skipped."
fi

echo "[healthcheck.sh] Checking docker compose service status..."
docker compose ps

echo
echo "[healthcheck.sh] HTTP health probes (if curl is available)..."

if command -v curl > /dev/null 2>&1; then
  FRONTEND_HEALTH_URL="http://localhost:5173"

  echo
  echo "[healthcheck.sh] Checking backend via docker inspect (port not exposed on host)..."
  BACKEND_STATUS=$(docker inspect --format='{{.State.Health.Status}}' samruddhi_backend 2>/dev/null || echo "missing")
  if [ "$BACKEND_STATUS" = "healthy" ]; then
    echo "[healthcheck.sh] backend: OK (healthy)"
  else
    echo "[healthcheck.sh] backend: ${BACKEND_STATUS} (UNHEALTHY or not running)"
  fi

  echo
  echo "[healthcheck.sh] Checking backend-2 via docker inspect (port not exposed on host)..."
  BACKEND2_STATUS=$(docker inspect --format='{{.State.Health.Status}}' samruddhi_backend_2 2>/dev/null || echo "missing")
  if [ "$BACKEND2_STATUS" = "healthy" ]; then
    echo "[healthcheck.sh] backend-2: OK (healthy)"
  else
    echo "[healthcheck.sh] backend-2: ${BACKEND2_STATUS} (UNHEALTHY or not running)"
  fi

  echo
  echo "[healthcheck.sh] Checking frontend at ${FRONTEND_HEALTH_URL}..."
  if curl -fsS "$FRONTEND_HEALTH_URL" > /dev/null 2>&1; then
    echo "[healthcheck.sh] frontend: OK (root page reachable)"
  else
    echo "[healthcheck.sh] frontend: UNHEALTHY or not reachable"
  fi
else
  echo "[healthcheck.sh] Skipping HTTP health checks because curl is not available."
fi

echo
echo "[healthcheck.sh] Health checks completed."

