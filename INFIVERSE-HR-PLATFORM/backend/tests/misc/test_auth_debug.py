#!/usr/bin/env python3
"""
Debug Authentication Issue
"""

import httpx
import os
from dotenv import load_dotenv

load_dotenv()

def debug_auth():
    """Debug authentication issue"""
    
    base_url = "http://localhost:9001"
    api_key = os.getenv("API_KEY_SECRET")
    
    print(f"Local API key: {api_key}")
    print(f"Key length: {len(api_key) if api_key else 'None'}")
    
    # Test with different header formats
    test_cases = [
        {"Authorization": f"Bearer {api_key}"},
        {"Authorization": f"{api_key}"},
        {"X-API-Key": api_key},
    ]
    
    for i, headers in enumerate(test_cases, 1):
        print(f"\nTest {i}: {headers}")
        try:
            response = httpx.get(f"{base_url}/workflows/stats", headers=headers, timeout=10.0)
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text[:100]}")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Test service info to see what environment it's using
    try:
        response = httpx.get(f"{base_url}/", timeout=10.0)
        print(f"\nService info: {response.json()}")
    except Exception as e:
        print(f"Service info error: {e}")

if __name__ == "__main__":
    debug_auth()