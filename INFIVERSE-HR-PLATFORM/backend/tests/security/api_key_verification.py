#!/usr/bin/env python3
"""
🔑 BHIV HR Platform - API Key Verification Test
Test API key against localhost services
"""

import asyncio
import httpx
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APIKeyTester:
    def __init__(self):
        self.services = {
            "gateway": "http://localhost:8000",
            "agent": "http://localhost:9000", 
            "langgraph": "http://localhost:9001"
        }
        self.api_key = os.getenv("API_KEY_SECRET", "bhiv_test_api_key_2025_docker_local")
        
    async def test_gateway_api_key(self):
        """Test API key against Gateway service"""
        logger.info("🔑 Testing Gateway API key...")
        
        try:
            headers = {'X-API-Key': self.api_key}
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.services['gateway']}/v1/jobs", headers=headers)
                
                logger.info(f"Gateway response: {response.status_code}")
                if response.status_code == 200:
                    logger.info("✅ Gateway API key VALID")
                    return True
                elif response.status_code == 401:
                    logger.error("❌ Gateway API key INVALID")
                    return False
                else:
                    logger.warning(f"⚠️ Gateway unexpected response: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Gateway connection error: {e}")
            return False
    
    async def test_agent_api_key(self):
        """Test API key against Agent service"""
        logger.info("🔑 Testing Agent API key...")
        
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.services['agent']}/test-db", headers=headers)
                
                logger.info(f"Agent response: {response.status_code}")
                if response.status_code == 200:
                    logger.info("✅ Agent API key VALID")
                    return True
                elif response.status_code == 401:
                    logger.error("❌ Agent API key INVALID")
                    return False
                else:
                    logger.warning(f"⚠️ Agent unexpected response: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Agent connection error: {e}")
            return False
    
    async def test_langgraph_api_key(self):
        """Test API key against LangGraph service"""
        logger.info("🔑 Testing LangGraph API key...")
        
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.services['langgraph']}/workflows", headers=headers)
                
                logger.info(f"LangGraph response: {response.status_code}")
                if response.status_code == 200:
                    logger.info("✅ LangGraph API key VALID")
                    return True
                elif response.status_code == 401:
                    logger.error("❌ LangGraph API key INVALID")
                    return False
                else:
                    logger.warning(f"⚠️ LangGraph unexpected response: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ LangGraph connection error: {e}")
            return False
    
    async def run_verification(self):
        """Run complete API key verification"""
        logger.info("🚀 Starting API Key Verification Test")
        logger.info(f"API Key: {self.api_key}")
        logger.info("=" * 50)
        
        results = {}
        
        # Test Gateway
        results['gateway'] = await self.test_gateway_api_key()
        
        # Test Agent
        results['agent'] = await self.test_agent_api_key()
        
        # Test LangGraph
        results['langgraph'] = await self.test_langgraph_api_key()
        
        # Summary
        logger.info("=" * 50)
        logger.info("📊 API Key Verification Summary:")
        
        valid_count = sum(results.values())
        total_count = len(results)
        
        for service, valid in results.items():
            status = "✅ VALID" if valid else "❌ INVALID"
            logger.info(f"  {service.title()}: {status}")
        
        logger.info(f"Overall: {valid_count}/{total_count} services validated")
        
        if valid_count == total_count:
            logger.info("🎉 All services accept the API key!")
        else:
            logger.warning("⚠️ Some services rejected the API key")
        
        return results

async def main():
    tester = APIKeyTester()
    await tester.run_verification()

if __name__ == "__main__":
    asyncio.run(main())