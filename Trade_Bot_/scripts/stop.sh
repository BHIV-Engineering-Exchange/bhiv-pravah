#!/usr/bin/env bash

set -euo pipefail

# Local helper to stop the docker compose stack

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "[stop.sh] Stopping local docker compose stack from: $(pwd)"

docker compose down

echo "[stop.sh] Stack stopped."

