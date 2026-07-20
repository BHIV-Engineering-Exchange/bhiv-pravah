#!/usr/bin/env python3
"""
Agent Service Diagnostic Tool
Diagnoses why the Agent Service is unavailable
"""

import requests
import json
import time
from datetime import datetime

# Configuration
AGENT_URL = "https://bhiv-hr-agent-nhgg.onrender.com"
API_KEY = "<YOUR_API_KEY>"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_agent_health():
    """Test Agent service health endpoint"""
    print("1. Testing Agent Service Health...")
    try:
        response = requests.get(f"{AGENT_URL}/health", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("   ERROR: Timeout - Service may be sleeping or overloaded")
        return False
    except requests.exceptions.ConnectionError:
        print("   ERROR: Connection failed - Service may be down")
        return False
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        return False

def test_agent_root():
    """Test Agent service root endpoint"""
    print("\n2. Testing Agent Service Root...")
    try:
        response = requests.get(f"{AGENT_URL}/", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        return False

def test_agent_match():
    """Test Agent service match endpoint"""
    print("\n3. Testing Agent Service Match Endpoint...")
    try:
        payload = {"job_id": 1, "candidate_ids": []}
        response = requests.post(
            f"{AGENT_URL}/match", 
            json=payload, 
            headers=HEADERS, 
            timeout=60
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Algorithm: {data.get('algorithm_version', 'unknown')}")
            print(f"   Candidates: {len(data.get('top_candidates', []))}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        return False

def test_agent_batch():
    """Test Agent service batch endpoint"""
    print("\n4. Testing Agent Service Batch Endpoint...")
    try:
        payload = {"job_ids": [1, 2]}
        response = requests.post(
            f"{AGENT_URL}/batch-match", 
            json=payload, 
            headers=HEADERS, 
            timeout=60
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Jobs Processed: {data.get('total_jobs_processed', 0)}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        return False

def check_render_service():
    """Check if it's a Render service issue"""
    print("\n5. Checking Render Service Status...")
    try:
        # Try to wake up the service with multiple requests
        for i in range(3):
            print(f"   Wake-up attempt {i+1}/3...")
            response = requests.get(f"{AGENT_URL}/", timeout=45)
            if response.status_code == 200:
                print("   Service is awake!")
                return True
            time.sleep(5)
        return False
    except Exception as e:
        print(f"   ERROR: {str(e)}")
        return False

def diagnose_connection():
    """Diagnose connection issues"""
    print("\n6. Connection Diagnostics...")
    
    # Test DNS resolution
    try:
        import socket
        host = "bhiv-hr-agent-nhgg.onrender.com"
        ip = socket.gethostbyname(host)
        print(f"   DNS Resolution: {host} -> {ip}")
    except Exception as e:
        print(f"   DNS Error: {str(e)}")
    
    # Test basic connectivity
    try:
        response = requests.head(AGENT_URL, timeout=10)
        print(f"   Basic Connectivity: {response.status_code}")
    except Exception as e:
        print(f"   Connectivity Error: {str(e)}")

def main():
    """Run complete Agent Service diagnosis"""
    print("Agent Service Diagnostic Report")
    print("=" * 50)
    print(f"Target URL: {AGENT_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Run all diagnostic tests
    health_ok = test_agent_health()
    root_ok = test_agent_root()
    
    if not health_ok and not root_ok:
        # Service appears to be down, try to wake it up
        render_ok = check_render_service()
        if render_ok:
            # Retry health check after wake-up
            health_ok = test_agent_health()
    
    if health_ok:
        # Service is up, test AI endpoints
        match_ok = test_agent_match()
        batch_ok = test_agent_batch()
    else:
        match_ok = False
        batch_ok = False
    
    # Connection diagnostics
    diagnose_connection()
    
    # Summary
    print("\n" + "=" * 50)
    print("DIAGNOSIS SUMMARY")
    print("=" * 50)
    
    if health_ok:
        print("✅ Agent Service: ONLINE")
        if match_ok and batch_ok:
            print("✅ AI Endpoints: WORKING")
            print("\n🎉 RESOLUTION: Agent Service is fully operational!")
            print("   The Gateway should now connect successfully.")
        else:
            print("❌ AI Endpoints: FAILING")
            print("\n🔧 ISSUE: Service is online but AI endpoints are not working")
            print("   Possible causes:")
            print("   - Database connection issues in Agent service")
            print("   - Authentication problems")
            print("   - Internal service errors")
    else:
        print("❌ Agent Service: OFFLINE")
        print("\n🔧 ISSUE: Agent Service is not responding")
        print("   Possible causes:")
        print("   - Render free tier service sleeping (most likely)")
        print("   - Service deployment issues")
        print("   - Resource limitations")
        print("   - Service crashed")
        
        print("\n💡 SOLUTIONS:")
        print("   1. Wait 30-60 seconds and try again (service may be starting)")
        print("   2. Check Render dashboard for service status")
        print("   3. Redeploy the Agent service if needed")
        print("   4. Use Gateway fallback matching (currently active)")

if __name__ == "__main__":
    main()
