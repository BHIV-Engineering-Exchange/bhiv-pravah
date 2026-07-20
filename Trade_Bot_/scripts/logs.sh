#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v docker >/dev/null 2>&1; then
  echo "[logs.sh] ERROR: docker is not installed or not in PATH."
  exit 1
fi

echo "[logs.sh] Streaming logs for all services (last 200 lines)."
echo "[logs.sh] Press Ctrl+C to stop following logs."

docker compose logs --tail=200 -f "$@"

