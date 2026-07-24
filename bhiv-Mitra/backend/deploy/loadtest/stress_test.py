"""
MITRA Stress & Failover Test
-----------------------------
Tests system resilience under heavy load and failure scenarios.
"""
import asyncio
import httpx
import time
import json
from concurrent.futures import ThreadPoolExecutor
import threading

BASE_URL = "http://localhost:8000"
API_KEY = "mitra_production_api_key_2026_secure_random_value"


def health_check():
    """Single health check."""
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def send_message(msg_id):
    """Send a single chat message."""
    try:
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        payload = {
            "version": "3.0.0",
            "input": {"message": f"Stress test message {msg_id}"},
            "context": {"platform": "web", "device": "desktop"},
        }
        start = time.time()
        resp = httpx.post(
            f"{BASE_URL}/api/assistant",
            headers=headers,
            json=payload,
            timeout=30,
        )
        latency = (time.time() - start) * 1000
        return {
            "status": resp.status_code,
            "latency_ms": latency,
            "success": resp.status_code == 200,
        }
    except Exception as e:
        return {"status": 0, "latency_ms": 0, "success": False, "error": str(e)}


def test_concurrent_users(num_users=100):
    """Test with concurrent users."""
    print(f"\n=== Concurrent User Test ({num_users} users) ===")
    results = []
    with ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(send_message, i) for i in range(num_users)]
        for f in futures:
            results.append(f.result())

    successes = sum(1 for r in results if r["success"])
    avg_latency = sum(r["latency_ms"] for r in results) / len(results)
    p95_latency = sorted(r["latency_ms"] for r in results)[int(len(results) * 0.95)]

    print(f"  Success Rate: {successes}/{num_users} ({successes/num_users*100:.1f}%)")
    print(f"  Avg Latency: {avg_latency:.1f}ms")
    print(f"  P95 Latency: {p95_latency:.1f}ms")
    return {"success_rate": successes/num_users, "avg_latency": avg_latency, "p95_latency": p95_latency}


def test_health_under_load(num_checks=50):
    """Test health endpoint under load."""
    print(f"\n=== Health Check Under Load ({num_checks} checks) ===")
    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(health_check) for _ in range(num_checks)]
        results = [f.result() for f in futures]

    successes = sum(1 for r in results if r)
    print(f"  Health Checks: {successes}/{num_checks} passed ({successes/num_checks*100:.1f}%)")
    return successes/num_checks


def test_recovery_after_pause():
    """Test recovery after a brief pause."""
    print("\n=== Recovery Test ===")
    # First, verify healthy
    pre_health = health_check()
    print(f"  Pre-pause health: {'OK' if pre_health else 'FAIL'}")

    # Pause
    time.sleep(5)

    # Check again
    post_health = health_check()
    print(f"  Post-pause health: {'OK' if post_health else 'FAIL'}")

    # Send a message
    result = send_message("recovery_test")
    print(f"  Post-pause message: {'OK' if result['success'] else 'FAIL'}")

    return pre_health and post_health and result["success"]


def run_all_tests():
    """Run all stress and failover tests."""
    print("=" * 60)
    print("MITRA Stress & Failover Test Suite")
    print("=" * 60)

    # Initial health check
    if not health_check():
        print("ERROR: Server not reachable at", BASE_URL)
        return

    print("Server is reachable. Starting tests...")

    results = {}

    # Test 1: Concurrent users
    results["concurrent_50"] = test_concurrent_users(50)
    results["concurrent_100"] = test_concurrent_users(100)

    # Test 2: Health under load
    results["health_under_load"] = test_health_under_load(50)

    # Test 3: Recovery
    results["recovery"] = test_recovery_after_pause()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test, result in results.items():
        if isinstance(result, dict):
            print(f"  {test}: {result.get('success_rate', 'N/A')}")
        else:
            print(f"  {test}: {'PASS' if result else 'FAIL'}")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
