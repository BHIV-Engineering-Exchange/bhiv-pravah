"""
PRANA Integration Verification Test
Tests all PRANA endpoints and integration points
"""

import requests
import json
from datetime import datetime, timezone

BUCKET_URL = "http://localhost:8001"

def test_prana_ingestion():
    """Test PRANA packet ingestion"""
    print("\n🧪 Testing PRANA Ingestion...")
    
    packet = {
        "user_id": "test_user_123",
        "session_id": "test_session_456",
        "lesson_id": "test_lesson_789",
        "task_id": None,
        "system_type": "gurukul",
        "role": "student",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cognitive_state": "DEEP_FOCUS",
        "active_seconds": 4.5,
        "idle_seconds": 0.5,
        "away_seconds": 0.0,
        "focus_score": 95,
        "raw_signals": {
            "mouse_velocity": 150,
            "scroll_depth": 75,
            "keystroke_count": 45,
            "window_focus": True,
            "tab_visible": True
        }
    }
    
    try:
        response = requests.post(
            f"{BUCKET_URL}/bucket/prana/ingest",
            json=packet,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ PRANA ingestion successful")
                return True
            else:
                print(f"❌ PRANA ingestion failed: {result}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_prana_stats():
    """Test PRANA statistics endpoint"""
    print("\n🧪 Testing PRANA Statistics...")
    
    try:
        response = requests.get(f"{BUCKET_URL}/bucket/prana/stats", timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ PRANA stats retrieved:")
            print(f"   - Total packets: {stats['stats']['total_packets']}")
            print(f"   - Unique users: {stats['stats']['unique_users']}")
            print(f"   - Systems: {stats['stats']['systems']}")
            return True
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_prana_packets():
    """Test PRANA packets retrieval"""
    print("\n🧪 Testing PRANA Packets Retrieval...")
    
    try:
        response = requests.get(
            f"{BUCKET_URL}/bucket/prana/packets",
            params={"limit": 10},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {data['count']} packets")
            return True
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_user_history():
    """Test user PRANA history"""
    print("\n🧪 Testing User PRANA History...")
    
    try:
        response = requests.get(
            f"{BUCKET_URL}/bucket/prana/user/test_user_123",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User history retrieved:")
            print(f"   - Packets: {data['count']}")
            if data['count'] > 0:
                analytics = data.get('analytics', {})
                print(f"   - Avg focus: {analytics.get('average_focus_score', 0)}")
                print(f"   - States: {analytics.get('state_distribution', {})}")
            return True
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_health_check():
    """Test health check includes PRANA"""
    print("\n🧪 Testing Health Check (PRANA)...")
    
    try:
        response = requests.get(f"{BUCKET_URL}/health", timeout=5)
        
        if response.status_code == 200:
            health = response.json()
            prana = health.get('prana_telemetry', {})
            
            if prana:
                print(f"✅ PRANA telemetry in health check:")
                print(f"   - Status: {prana.get('status')}")
                print(f"   - Packets: {prana.get('packets_received')}")
                print(f"   - Users: {prana.get('users_tracked')}")
                return True
            else:
                print("❌ PRANA telemetry not in health check")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_multiple_packets():
    """Test multiple packet ingestion"""
    print("\n🧪 Testing Multiple Packet Ingestion...")
    
    states = ["DEEP_FOCUS", "ON_TASK", "THINKING", "IDLE", "DISTRACTED"]
    success_count = 0
    
    for i, state in enumerate(states):
        packet = {
            "user_id": "test_user_123",
            "session_id": "test_session_456",
            "lesson_id": "test_lesson_789",
            "system_type": "gurukul",
            "role": "student",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cognitive_state": state,
            "active_seconds": 4.0,
            "idle_seconds": 1.0,
            "away_seconds": 0.0,
            "focus_score": 90 - (i * 10),
            "raw_signals": {}
        }
        
        try:
            response = requests.post(
                f"{BUCKET_URL}/bucket/prana/ingest",
                json=packet,
                timeout=5
            )
            if response.status_code == 200:
                success_count += 1
        except:
            pass
    
    print(f"✅ Ingested {success_count}/{len(states)} packets")
    return success_count == len(states)

def run_all_tests():
    """Run all PRANA integration tests"""
    print("=" * 60)
    print("🎯 PRANA Integration Verification")
    print("=" * 60)
    
    tests = [
        ("PRANA Ingestion", test_prana_ingestion),
        ("PRANA Statistics", test_prana_stats),
        ("PRANA Packets", test_prana_packets),
        ("User History", test_user_history),
        ("Health Check", test_health_check),
        ("Multiple Packets", test_multiple_packets),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 60)
    print(f"🎯 Final Score: {passed}/{total} tests passed ({int(passed/total*100)}%)")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! PRANA integration is working correctly.")
    elif passed >= total * 0.8:
        print("\n✅ Most tests passed. PRANA integration is functional.")
    else:
        print("\n⚠️ Some tests failed. Check the logs above.")
    
    return passed == total

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite crashed: {e}")
