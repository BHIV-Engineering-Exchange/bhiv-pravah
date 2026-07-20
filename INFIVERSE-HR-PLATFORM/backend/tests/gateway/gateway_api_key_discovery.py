#!/usr/bin/env python3
"""
🔍 Gateway API Key Discovery - Find the correct Gateway API key
"""

import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_gateway_keys():
    """Test various API keys against Gateway service"""
    
    gateway_service_url = "http://localhost:8000"
    
    # Test keys including environment variables and common patterns
    test_keys = [
        "<YOUR_API_KEY>",  # Docker default
        "bhiv_test_api_key_2025_docker_local",
        "your_secure_api_key_here",
        "test_api_key",
        "bhiv_api_key", 
        "api_key",
        "secret_key",
        "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o",
        "test",
        "admin",
        "bhiv",
        "key",
        "secret",
        "password",
        "docker_api_key",
        "local_api_key",
        "dev_api_key",
        "development_key",
        "",
        "null",
        "none",
        "default_api_key",
        "changeme",
        "123456",
        "admin123",
        "bhiv_hr_api_key",
        "bhiv_platform_key",
        "hr_platform_key",
        "bhiv_2025",
        "bhiv_2024",
        "api_2025",
        "gateway_key",
        "service_key"
    ]
    
    logger.info("🔍 Testing Gateway API keys...")
    logger.info("=" * 50)
    
    for i, api_key in enumerate(test_keys, 1):
        display_key = api_key if len(api_key) <= 30 else f"{api_key[:30]}..."
        logger.info(f"🔑 Testing #{i:2d}: '{display_key}'")
        
        try:
            headers = {'X-API-Key': api_key}
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{gateway_service_url}/v1/jobs", headers=headers)
                
                if response.status_code == 200:
                    logger.info(f"🎉 FOUND WORKING GATEWAY API KEY!")
                    logger.info(f"✅ API Key: '{api_key}'")
                    return api_key
                else:
                    logger.info(f"❌ Failed ({response.status_code})")
                    
        except Exception as e:
            logger.info(f"❌ Error: {str(e)[:30]}")
    
    logger.info("=" * 50)
    logger.warning("⚠️ No working Gateway API key found")
    return None

if __name__ == "__main__":
    asyncio.run(test_gateway_keys())