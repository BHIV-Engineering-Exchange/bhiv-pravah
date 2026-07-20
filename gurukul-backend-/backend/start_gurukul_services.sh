#!/bin/bash
# ============================================================
# start_gurukul_services.sh
# Gurukul 24x7 Deterministic Service Orchestrator
#
# Starts all services in the correct dependency order:
#   1. Database verification
#   2. Vaani Voice Engine (Port 8008)
#   3. Gurukul Backend API (Port 3000)
#   4. Watchdog Supervisor
#
# Usage: bash start_gurukul_services.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VAANI_DIR="$(cd "$SCRIPT_DIR/../vaani-engine" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"

mkdir -p "$LOG_DIR"

echo "===================================================="
echo " Gurukul 24x7 Infrastructure Orchestrator"
echo " Started at: $(date)"
echo "===================================================="
echo ""

# ── Helper: wait for a service to become healthy ──────────
wait_for_service() {
    local name="$1"
    local url="$2"
    local max_wait="$3"
    local elapsed=0

    echo "    Waiting for $name to become healthy..."
    while [ $elapsed -lt $max_wait ]; do
        if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
            echo "    ✓ $name is healthy (took ${elapsed}s)"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done

    echo "    ✗ $name did not start within ${max_wait}s"
    return 1
}

# ── Step 1: Database Verification ─────────────────────────
echo "[1/4] Checking Database Connectivity..."
cd "$SCRIPT_DIR"

python3 -c "
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
    print('    ✓ SQL database is reachable')
" 2>/dev/null || echo "    ! SQL database check skipped (will retry on backend start)"

python3 -c "
from app.core.karma_database import get_db
db = get_db()
db.command('ping')
print('    ✓ MongoDB is reachable')
" 2>/dev/null || echo "    ! MongoDB check skipped (non-critical)"

echo ""

# ── Step 2: Start Vaani Voice Engine ──────────────────────
echo "[2/4] Starting Vaani Sovereign Voice Engine (Port 8008)..."
cd "$VAANI_DIR"
nohup python3 voice_service_api.py > "$LOG_DIR/vaani.log" 2>&1 &
VAANI_PID=$!
echo "    PID: $VAANI_PID"
echo "$VAANI_PID" > "$LOG_DIR/vaani.pid"

# Wait for Vaani to load model (can take 30-60s on first boot)
wait_for_service "Vaani Engine" "http://localhost:8008/health" 120
echo ""

# ── Step 3: Start Gurukul Backend ─────────────────────────
echo "[3/4] Starting Gurukul Backend API (Port 3000)..."
cd "$SCRIPT_DIR"
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 3000 > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "    PID: $BACKEND_PID"
echo "$BACKEND_PID" > "$LOG_DIR/backend.pid"

wait_for_service "Gurukul Backend" "http://localhost:3000/health" 30
echo ""

# ── Step 4: Start Watchdog Supervisor ─────────────────────
echo "[4/4] Starting Uptime Watchdog..."
cd "$SCRIPT_DIR"
nohup python3 watchdog_runner.py > "$LOG_DIR/watchdog.log" 2>&1 &
WATCHDOG_PID=$!
echo "    PID: $WATCHDOG_PID"
echo "$WATCHDOG_PID" > "$LOG_DIR/watchdog.pid"
echo ""

# ── Summary ───────────────────────────────────────────────
echo "===================================================="
echo " All Gurukul services are RUNNING"
echo ""
echo " Services:"
echo "   Backend:  http://localhost:3000  (PID: $BACKEND_PID)"
echo "   Vaani:    http://localhost:8008  (PID: $VAANI_PID)"
echo "   Watchdog: (PID: $WATCHDOG_PID)"
echo ""
echo " Health:     http://localhost:3000/system/health"
echo " API Docs:   http://localhost:3000/docs"
echo " Logs:       $LOG_DIR/"
echo "===================================================="
