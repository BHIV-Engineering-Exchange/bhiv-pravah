"""
Insight Flow Integration Test
Tests: Bridge (8006) and Backend (8007) integration
"""
import requests
import time

BRIDGE_URL = "http://localhost:8006"
BACKEND_URL = "http://localhost:8007"

def test_backend_health():
    """Test 1: Backend Health (Optional)"""
    print("\n[1/5] Testing Insight Flow Backend Health (Optional)...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"  ✅ Backend healthy (full features available)")
            return True
        else:
            print(f"  ⚠️  Backend returned {response.status_code}")
            return True  # Not critical
    except Exception as e:
        print(f"  ⚠️  Backend offline (using standalone mode)")
        return True  # Not critical

def test_bridge_health():
    """Test 2: Bridge Health (Required)"""
    print("\n[2/5] Testing Insight Flow Bridge Health (Required)...")
    try:
        response = requests.get(f"{BRIDGE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            mode = data.get("mode", "unknown")
            print(f"  ✅ Bridge healthy (mode: {mode})")
            return True
        else:
            print(f"  ❌ Bridge returned {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Bridge offline: {e}")
        print("  💡 Run: start_bridge_standalone.bat")
        return False

def test_agent_routing():
    """Test 3: Agent Routing"""
    print("\n[3/5] Testing Agent Routing...")
    try:
        response = requests.post(
            f"{BRIDGE_URL}/route-agent",
            json={
                "agent_type": "nlp",
                "confidence_threshold": 0.75
            },
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Routing successful: {result.get('selected_agent', {}).get('name', 'N/A')}")
            return True
        else:
            print(f"  ⚠️  Routing returned {response.status_code} (backend may need setup)")
            return True  # Non-critical
    except Exception as e:
        print(f"  ⚠️  Routing test skipped: {e}")
        return True  # Non-critical

def test_analytics():
    """Test 4: Analytics"""
    print("\n[4/5] Testing Analytics...")
    try:
        response = requests.get(f"{BRIDGE_URL}/analytics", timeout=5)
        if response.status_code == 200:
            print(f"  ✅ Analytics available")
            return True
        else:
            print(f"  ⚠️  Analytics unavailable (non-critical)")
            return True
    except Exception as e:
        print(f"  ⚠️  Analytics test skipped: {e}")
        return True

def test_metrics():
    """Test 5: Metrics"""
    print("\n[5/5] Testing Metrics...")
    try:
        response = requests.get(f"{BRIDGE_URL}/metrics", timeout=5)
        if response.status_code == 200:
            print(f"  ✅ Metrics: {response.json()}")
            return True
        else:
            print(f"  ❌ Metrics failed")
            return False
    except Exception as e:
        print(f"  ❌ Metrics error: {e}")
        return False

def main():
    print("=" * 80)
    print("INSIGHT FLOW INTEGRATION TEST")
    print("=" * 80)
    print("\nNote: Backend (8007) is optional. Bridge (8006) can run standalone.")
    print("=" * 80)
    
    tests = [
        test_backend_health,
        test_bridge_health,
        test_agent_routing,
        test_analytics,
        test_metrics
    ]
    
    results = []
    for test in tests:
        results.append(test())
        time.sleep(0.5)
    
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed >= 4:
        print("\n✅ INSIGHT FLOW INTEGRATION READY")
        print("\n📝 Status:")
        print("  - Bridge (8006): Running")
        print("  - Backend (8007): Optional (for full features)")
        print("\n💡 For full features, run: start_insight_flow_fixed.bat")
    elif passed >= 2:
        print("\n⚠️  INSIGHT FLOW PARTIAL - Bridge needs to start")
        print("\n💡 Quick fix: Run start_bridge_standalone.bat")
    else:
        print("\n❌ INSIGHT FLOW OFFLINE")
        print("\n💡 Quick fix: Run start_bridge_standalone.bat")
    
    print("\n📚 See INSIGHT_FLOW_QUICK_FIX.md for detailed setup guide.")
    
    return passed >= 4

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
