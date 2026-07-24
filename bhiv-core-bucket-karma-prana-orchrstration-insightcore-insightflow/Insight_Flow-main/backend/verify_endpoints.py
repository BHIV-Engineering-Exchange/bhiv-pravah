# verify_endpoints.py
"""
Endpoint verification script for InsightFlow.
"""

import requests
import json
import time
import sys
from datetime import datetime


def test_endpoint(method, url, data=None, description=""):
    """Test an endpoint and return result"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ {description} - Unsupported method: {method}")
            return False
        
        if response.status_code == 200:
            print(f"✅ {description} - Status: {response.status_code}")
            return True
        else:
            print(f"❌ {description} - Status: {response.status_code}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"❌ {description} - Error: {e}")
        return False


def verify_server_running(base_url):
    """Check if server is running"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def main():
    """Verify all endpoints"""
    
    base_url = "http://localhost:8000"
    
    print("=== InsightFlow Endpoint Verification ===\n")
    
    # Check if server is running
    if not verify_server_running(base_url):
        print("❌ Server not running. Please start with:")
        print("   uvicorn app.main:app --reload")
        return 1
    
    print("✅ Server is running\n")
    
    failed_tests = []
    
    # Test route-agent endpoint
    route_data = {
        "agent_type": "nlp",
        "context": {"text": "test"},
        "confidence_threshold": 0.5
    }
    
    if not test_endpoint("POST", f"{base_url}/api/v1/routing/route-agent", 
                        route_data, "Route Agent Endpoint"):
        failed_tests.append("Route Agent")
    
    # Test dashboard endpoints
    dashboard_endpoints = [
        ("GET", f"{base_url}/dashboard/metrics/performance?hours=24", None, "Dashboard Performance"),
        ("GET", f"{base_url}/dashboard/metrics/accuracy", None, "Dashboard Accuracy"),
        ("GET", f"{base_url}/dashboard/metrics/agents", None, "Dashboard Agents")
    ]
    
    for method, url, data, desc in dashboard_endpoints:
        if not test_endpoint(method, url, data, desc):
            failed_tests.append(desc)
    
    # Test public routing endpoints
    routing_endpoints = [
        ("GET", f"{base_url}/api/routing/decisions?limit=5", None, "Routing Decisions"),
        ("GET", f"{base_url}/api/routing/statistics", None, "Routing Statistics")
    ]
    
    for method, url, data, desc in routing_endpoints:
        if not test_endpoint(method, url, data, desc):
            failed_tests.append(desc)
    
    # Test health endpoints
    health_endpoints = [
        ("GET", f"{base_url}/health", None, "Health Check"),
        ("GET", f"{base_url}/api/version", None, "API Version Info")
    ]
    
    for method, url, data, desc in health_endpoints:
        if not test_endpoint(method, url, data, desc):
            failed_tests.append(desc)
    
    # Summary
    print(f"\n=== Endpoint Verification Summary ===")
    if failed_tests:
        print(f"❌ {len(failed_tests)} endpoints failed:")
        for test in failed_tests:
            print(f"  - {test}")
        return 1
    else:
        print("✅ All endpoints verified successfully!")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)