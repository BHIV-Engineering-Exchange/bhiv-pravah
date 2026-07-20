#!/usr/bin/env python3
"""
🔍 BHIV HR Platform - API Key Discovery
Try to discover the correct API key by testing common patterns
"""

import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APIKeyDiscovery:
    def __init__(self):
        self.gateway_url = "http://localhost:8000"
        
        # Common API key patterns to test
        self.test_keys = [
            # Environment-based keys
            "bhiv_test_api_key_2025_docker_local",
            "your_secure_api_key_here", 
            "test_api_key",
            "bhiv_api_key",
            "api_key",
            "secret_key",
            
            # Production keys from .env.example
            "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o",
            
            # Simple test keys
            "test",
            "admin",
            "bhiv",
            "key",
            "secret",
            "password",
            
            # Docker/local development keys
            "docker_api_key",
            "local_api_key",
            "dev_api_key",
            "development_key",
            
            # Empty/null keys
            "",
            "null",
            "none",
            
            # Common default keys
            "default_api_key",
            "changeme",
            "123456",
            "admin123",
            
            # BHIV specific patterns
            "bhiv_hr_api_key",
            "bhiv_platform_key",
            "hr_platform_key",
            
            # Date-based keys
            "bhiv_2025",
            "bhiv_2024",
            "api_2025",
            
            # Service-specific keys
            "gateway_key",
            "service_key"
        ]
        
    async def test_gateway_key(self, api_key: str):
        """Test API key against Gateway service"""
        try:
            headers = {'X-API-Key': api_key}
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.gateway_url}/v1/jobs", headers=headers)
                return response.status_code == 200
        except:
            return False
    
    async def discover_api_key(self):
        """Try to discover the correct API key"""
        logger.info("🔍 BHIV HR Platform - API Key Discovery")
        logger.info("Testing common API key patterns...")
        logger.info("=" * 50)
        
        for i, api_key in enumerate(self.test_keys, 1):
            display_key = api_key if len(api_key) <= 30 else f"{api_key[:30]}..."
            logger.info(f"🔑 Testing #{i:2d}: '{display_key}'")
            
            if await self.test_gateway_key(api_key):
                logger.info(f"🎉 FOUND WORKING API KEY!")
                logger.info(f"✅ API Key: '{api_key}'")
                logger.info("=" * 50)
                return api_key
            else:
                logger.info(f"❌ Failed")
        
        logger.info("=" * 50)
        logger.warning("⚠️ No working API key found from common patterns")
        logger.info("💡 The API key might be:")
        logger.info("   - Set in environment variables")
        logger.info("   - Configured in Docker compose")
        logger.info("   - Using a custom/random value")
        logger.info("   - Not required (authentication disabled)")
        
        return None

async def main():
    discovery = APIKeyDiscovery()
    await discovery.discover_api_key()

if __name__ == "__main__":
    asyncio.run(main())