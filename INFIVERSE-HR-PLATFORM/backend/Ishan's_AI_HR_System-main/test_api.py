#!/usr/bin/env python3
"""Test API endpoints"""

import sys
import os
import time
import requests
import threading
import uvicorn

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def start_server():
    """Start test server"""
    from app.main import app
    uvicorn.run(app, host="127.0.0.1", port=5003, log_level="error")

def test_endpoints():
    """Test API endpoints"""
    base_url = "http://127.0.0.1:5003"
    
    # Wait for server to start
    time.sleep(3)
    
    tests = []
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        tests.append(("Health Check", response.status_code == 200))
        
        # Test system status
        response = requests.get(f"{base_url}/system/status", timeout=5)
        tests.append(("System Status", response.status_code == 200))
        
        # Test candidate list
        response = requests.get(f"{base_url}/candidate/list", timeout=5)
        tests.append(("Candidate List", response.status_code == 200))
        
        # Test feedback logs
        response = requests.get(f"{base_url}/feedback/logs", timeout=5)
        tests.append(("Feedback Logs", response.status_code == 200))
        
    except Exception as e:
        print(f"API test error: {e}")
        tests.append(("API Connection", False))
    
    return tests

def main():
    """Run API tests"""
    print("Starting API test server...")
    
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Run tests
    results = test_endpoints()
    
    print("API Endpoint Tests:")
    print("=" * 30)
    
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nAPI Tests: {passed}/{total} passed")
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"API robustness: {'ROBUST' if success else 'NEEDS ATTENTION'}")
    sys.exit(0 if success else 1)