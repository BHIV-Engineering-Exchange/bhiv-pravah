#!/usr/bin/env python3
"""
Test Docker Network Connectivity
Quick test to verify service-to-service communication
"""

import httpx
import os

def test_connection():
    """Test connection to LangGraph service"""
    
    # Test URLs to try
    urls = [
        "http://localhost:9001/health",  # External access
        "http://langgraph:9001/health",  # Docker internal (won't work from host)
        "http://127.0.0.1:9001/health"   # Localhost
    ]
    
    headers = {
        "Authorization": f"Bearer {os.getenv('API_KEY_SECRET', 'prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o')}"
    }
    
    print("🔍 Testing LangGraph Service Connectivity")
    print("=" * 50)
    
    for url in urls:
        try:
            print(f"\n🔄 Testing: {url}")
            response = httpx.get(url, headers=headers, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS: {response.status_code}")
                print(f"   Service: {data.get('service', 'Unknown')}")
                print(f"   Status: {data.get('status', 'Unknown')}")
                print(f"   Uptime: {data.get('uptime_seconds', 0)} seconds")
            else:
                print(f"⚠️ HTTP {response.status_code}: {response.text[:100]}")
        except httpx.ConnectError as e:
            print(f"❌ CONNECTION ERROR: {str(e)}")
        except httpx.TimeoutException:
            print(f"⏰ TIMEOUT: Service not responding within 5 seconds")
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 50)
    print("💡 If localhost works but langgraph:9001 fails:")
    print("   - This is normal when running from host machine")
    print("   - Docker containers use internal network")
    print("   - HR Portal should use 'http://langgraph:9001' internally")

if __name__ == "__main__":
    test_connection()