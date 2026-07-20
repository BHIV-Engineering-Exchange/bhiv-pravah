#!/usr/bin/env bash

set -euo pipefail

# Local deployment helper for running docker compose on your machine

# Resolve project root (one level up from this script directory)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "[deploy.sh] Running local docker compose deployment from: $(pwd)"

docker compose build
docker compose up -d

echo "[deploy.sh] Local stack is starting in the background."
