import requests
import json
from datetime import datetime, timezone

print("Testing Karma Forwarding Fix...")
print("=" * 60)

# Send a PRANA packet
packet = {
    "user_id": "test_user_fix",
    "session_id": "test_session_fix",
    "lesson_id": "test_lesson_fix",
    "task_id": None,
    "system_type": "gurukul",
    "role": "student",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "cognitive_state": "DEEP_FOCUS",
    "active_seconds": 4.5,
    "idle_seconds": 0.5,
    "away_seconds": 0.0,
    "focus_score": 95,
    "raw_signals": {"mouse_velocity": 150}
}

response = requests.post(
    "http://localhost:8001/bucket/prana/ingest",
    json=packet,
    timeout=5
)

print(f"Bucket Response: {response.status_code}")
print(f"Result: {response.json()}")
print("\nCheck Bucket logs - should see NO Karma 500 warnings")
print("=" * 60)
