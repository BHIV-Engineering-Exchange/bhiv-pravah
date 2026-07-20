#!/usr/bin/env python3
"""
🔑 Test the default API key from Docker compose
"""

import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_default_api_key():
    """Test the default API key from docker-compose.yml"""
    
    # The default API key from docker-compose.yml
    api_key = "<YOUR_API_KEY>"
    
    logger.info("🔑 Testing default Docker compose API key")
    logger.info(f"API Key: '{api_key}'")
    logger.info("=" * 50)
    
    services = {
        "gateway": ("http://localhost:8000", "/v1/jobs", "X-API-Key"),
        "agent": ("http://localhost:9000", "/test-db", "Authorization"),
        "langgraph": ("http://localhost:9001", "/workflows", "Authorization")
    }
    
    results = {}
    
    for service_name, (url, endpoint, auth_header) in services.items():
        logger.info(f"🔍 Testing {service_name}...")
        
        try:
            if auth_header == "X-API-Key":
                headers = {'X-API-Key': api_key}
            else:
                headers = {'Authorization': f'Bearer {api_key}'}
            
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{url}{endpoint}", headers=headers)
                
                if response.status_code == 200:
                    logger.info(f"✅ {service_name}: SUCCESS (200)")
                    results[service_name] = True
                else:
                    logger.info(f"❌ {service_name}: FAILED ({response.status_code})")
                    results[service_name] = False
                    
        except Exception as e:
            logger.error(f"❌ {service_name}: ERROR - {e}")
            results[service_name] = False
    
    logger.info("=" * 50)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    if success_count == total_count:
        logger.info("🎉 SUCCESS! Default API key works for all services")
        logger.info(f"✅ Working API key: '{api_key}'")
        return api_key
    else:
        logger.warning(f"⚠️ API key works for {success_count}/{total_count} services")
        return None

if __name__ == "__main__":
    asyncio.run(test_default_api_key())