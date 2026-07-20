#!/usr/bin/env python3
"""
Quick Integration Test Runner
Runs comprehensive tests for LangGraph and Gateway integration
"""

import subprocess
import sys
import time
import requests
from datetime import datetime

def check_service(url, name):
    """Check if a service is running"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name} is running")
            return True
        else:
            print(f"❌ {name} returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name} is not accessible: {e}")
        return False

def main():
    print("🚀 BHIV HR Platform - Integration Test Runner")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if services are running
    print("🔍 Checking service availability...")
    
    gateway_ok = check_service("http://localhost:8000/health", "Gateway Service")
    langgraph_ok = check_service("http://localhost:9001/health", "LangGraph Service")
    
    if not gateway_ok or not langgraph_ok:
        print("\n⚠️  Some services are not running. Please start them first:")
        if not gateway_ok:
            print("   Gateway: cd services/gateway && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        if not langgraph_ok:
            print("   LangGraph: cd services/langgraph && python -m uvicorn app.main:app --host 0.0.0.0 --port 9001")
        print()
        return False
    
    print("\n✅ All services are running! Starting integration tests...")
    print("-" * 50)
    
    # Run the comprehensive integration test
    try:
        result = subprocess.run([
            sys.executable, "test_integration.py"
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n🎉 Integration tests completed successfully!")
        else:
            print(f"\n❌ Integration tests failed with return code: {result.returncode}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"\n❌ Failed to run integration tests: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)