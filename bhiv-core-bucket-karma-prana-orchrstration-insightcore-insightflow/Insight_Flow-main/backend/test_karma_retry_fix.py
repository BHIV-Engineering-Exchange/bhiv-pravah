#!/usr/bin/env python3
"""
Test script to verify Karma service retry logic improvements
"""

import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock
import aiohttp

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_karma_retry_logic():
    """Test improved Karma service retry logic"""
    
    print("🧪 Testing Karma service retry logic improvements...")
    
    try:
        from services.karma_service import KarmaServiceClient
        
        # Create test client
        client = KarmaServiceClient(
            karma_endpoint="http://test-endpoint",
            max_retries=3,
            timeout=1
        )
        
        # Test 1: Should retry logic for different error types
        print("\n1. Testing retry decision logic...")
        
        # Should NOT retry 4xx errors
        should_retry_404 = client._should_retry(None, 404)
        print(f"   404 error retry: {should_retry_404} (should be False)")
        
        should_retry_400 = client._should_retry(None, 400)
        print(f"   400 error retry: {should_retry_400} (should be False)")
        
        # Should retry 5xx errors
        should_retry_500 = client._should_retry(None, 500)
        print(f"   500 error retry: {should_retry_500} (should be True)")
        
        should_retry_503 = client._should_retry(None, 503)
        print(f"   503 error retry: {should_retry_503} (should be True)")
        
        # Should retry timeout errors
        should_retry_timeout = client._should_retry(asyncio.TimeoutError())
        print(f"   Timeout error retry: {should_retry_timeout} (should be True)")
        
        # Should retry network errors
        should_retry_network = client._should_retry(aiohttp.ClientError())
        print(f"   Network error retry: {should_retry_network} (should be True)")
        
        # Test 2: Metrics tracking
        print("\n2. Testing metrics tracking...")
        initial_metrics = client.get_metrics()
        print(f"   Initial metrics: {initial_metrics}")
        
        # Check if new metric is present
        if "non_retryable_errors" in initial_metrics:
            print("   ✅ Non-retryable errors metric added")
        else:
            print("   ❌ Non-retryable errors metric missing")
        
        print("\n🎉 Karma retry logic testing completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the backend directory")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_karma_retry_logic())