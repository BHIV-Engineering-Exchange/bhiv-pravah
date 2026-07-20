#!/usr/bin/env python3
"""
🔑 BHIV HR Platform - Enhanced API Key Verification Test
Test multiple API keys against localhost services
"""

import asyncio
import httpx
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedAPIKeyTester:
    def __init__(self):
        self.services = {
            "gateway": "http://localhost:8000",
            "agent": "http://localhost:9000", 
            "langgraph": "http://localhost:9001"
        }
        
        # Test multiple API keys
        self.api_keys_to_test = [
            os.getenv("API_KEY_SECRET", "bhiv_test_api_key_2025_docker_local"),
            "your_secure_api_key_here",
            "bhiv_test_api_key_2025_docker_local",
            "test_api_key",
            "bhiv_api_key",
            "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o"
        ]
        
    async def test_service_with_key(self, service_name: str, api_key: str):
        """Test a specific service with a specific API key"""
        service_url = self.services[service_name]
        
        try:
            if service_name == "gateway":
                headers = {'X-API-Key': api_key}
                endpoint = "/v1/jobs"
            else:
                headers = {'Authorization': f'Bearer {api_key}'}
                endpoint = "/test-db" if service_name == "agent" else "/workflows"
            
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{service_url}{endpoint}", headers=headers)
                
                if response.status_code == 200:
                    return True, "VALID"
                elif response.status_code == 401:
                    return False, "UNAUTHORIZED"
                elif response.status_code == 403:
                    return False, "FORBIDDEN"
                else:
                    return False, f"HTTP_{response.status_code}"
                    
        except Exception as e:
            return False, f"ERROR: {str(e)}"
    
    async def test_all_keys(self):
        """Test all API keys against all services"""
        logger.info("🚀 Enhanced API Key Verification Test")
        logger.info("=" * 60)
        
        results = {}
        
        for i, api_key in enumerate(self.api_keys_to_test, 1):
            logger.info(f"🔑 Testing API Key #{i}: {api_key[:20]}...")
            
            key_results = {}
            for service_name in self.services.keys():
                valid, status = await self.test_service_with_key(service_name, api_key)
                key_results[service_name] = {"valid": valid, "status": status}
                
                status_icon = "✅" if valid else "❌"
                logger.info(f"  {service_name.title()}: {status_icon} {status}")
            
            results[api_key] = key_results
            
            # Check if this key works for all services
            all_valid = all(result["valid"] for result in key_results.values())
            if all_valid:
                logger.info(f"🎉 FOUND WORKING API KEY: {api_key}")
                break
            
            logger.info("-" * 40)
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 Final Summary:")
        
        working_keys = []
        for api_key, key_results in results.items():
            valid_services = sum(1 for result in key_results.values() if result["valid"])
            total_services = len(key_results)
            
            if valid_services > 0:
                logger.info(f"🔑 {api_key[:30]}... : {valid_services}/{total_services} services")
                if valid_services == total_services:
                    working_keys.append(api_key)
        
        if working_keys:
            logger.info(f"✅ Found {len(working_keys)} fully working API key(s)")
            logger.info(f"🎯 Recommended API key: {working_keys[0]}")
        else:
            logger.warning("⚠️ No API key works for all services")
            logger.info("💡 Check if services are running and configured correctly")
        
        return results

async def main():
    tester = EnhancedAPIKeyTester()
    await tester.test_all_keys()

if __name__ == "__main__":
    asyncio.run(main())