import requests
import json
from datetime import datetime, timezone

BUCKET_URL = "http://localhost:8001"

print("=" * 60)
print("PRANA Integration Test")
print("=" * 60)

# Test 1: Ingest a packet
print("\n[1/4] Testing PRANA Ingestion...")
packet = {
    "user_id": "test_user_999",
    "session_id": "test_session_999",
    "lesson_id": "test_lesson_999",
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

try:
    response = requests.post(f"{BUCKET_URL}/bucket/prana/ingest", json=packet, timeout=5)
    if response.status_code == 200:
        print("PASS - Ingestion successful")
    else:
        print(f"FAIL - HTTP {response.status_code}: {response.text[:200]}")
except Exception as e:
    print(f"FAIL - Error: {e}")

# Test 2: Get stats
print("\n[2/4] Testing PRANA Statistics...")
try:
    response = requests.get(f"{BUCKET_URL}/bucket/prana/stats", timeout=5)
    if response.status_code == 200:
        stats = response.json()
        print(f"PASS - Total packets: {stats['stats']['total_packets']}")
    else:
        print(f"FAIL - HTTP {response.status_code}")
except Exception as e:
    print(f"FAIL - Error: {e}")

# Test 3: Get packets
print("\n[3/4] Testing PRANA Packets Retrieval...")
try:
    response = requests.get(f"{BUCKET_URL}/bucket/prana/packets?limit=10", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"PASS - Retrieved {data.get('count', 0)} packets")
    else:
        print(f"FAIL - HTTP {response.status_code}")
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"FAIL - Error: {e}")

# Test 4: Get user history
print("\n[4/4] Testing User PRANA History...")
try:
    response = requests.get(f"{BUCKET_URL}/bucket/prana/user/test_user_999", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"PASS - User packets: {data.get('count', 0)}")
    else:
        print(f"FAIL - HTTP {response.status_code}")
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"FAIL - Error: {e}")

print("\n" + "=" * 60)
print("Test Complete - Please restart Bucket service if tests fail")
print("=" * 60)
