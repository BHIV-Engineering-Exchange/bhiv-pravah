#!/bin/bash
# MITRA Load Testing Script
# Usage: bash deploy/loadtest/run_loadtest.sh [users] [spawn_rate] [duration]

USERS=${1:-50}
SPAWN_RATE=${2:-10}
DURATION=${3:-60}
HOST=${4:-http://localhost:8000}

echo "=== MITRA Load Test ==="
echo "Target: $HOST"
echo "Users: $USERS"
echo "Spawn Rate: $SPAWN_RATE/sec"
echo "Duration: ${DURATION}s"
echo ""

# Check if locust is installed
if ! command -v locust &> /dev/null; then
    echo "Installing locust..."
    pip install locust
fi

echo "Starting load test..."
locust -f "$(dirname "$0")/locustfile.py" \
    --host="$HOST" \
    --users="$USERS" \
    --spawn-rate="$SPAWN_RATE" \
    --run-time="${DURATION}s" \
    --headless \
    --csv=results/mitra_loadtest \
    --html=results/mitra_loadtest.html

echo ""
echo "=== Load Test Complete ==="
echo "Results saved to: results/mitra_loadtest.csv"
echo "HTML report: results/mitra_loadtest.html"
