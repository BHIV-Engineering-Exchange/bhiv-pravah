#!/usr/bin/env python3
"""
🏥 BHIV HR Platform - Service Health Check
Check if localhost services are running
"""

import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServiceHealthChecker:
    def __init__(self):
        self.services = {
            "gateway": "http://localhost:8000",
            "agent": "http://localhost:9000", 
            "langgraph": "http://localhost:9001",
            "hr_portal": "http://localhost:8501",
            "client_portal": "http://localhost:8502",
            "candidate_portal": "http://localhost:8503"
        }
        
    async def check_service_health(self, service_name: str, url: str):
        """Check if a service is running"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Try health endpoint first
                try:
                    response = await client.get(f"{url}/health")
                    if response.status_code == 200:
                        return True, "HEALTHY", response.status_code
                except:
                    pass
                
                # Try root endpoint
                try:
                    response = await client.get(url)
                    if response.status_code in [200, 404, 403]:  # Service is up
                        return True, f"UP (HTTP {response.status_code})", response.status_code
                except:
                    pass
                
                return False, "DOWN", 0
                
        except Exception as e:
            return False, f"ERROR: {str(e)[:30]}", 0
    
    async def run_health_check(self):
        """Run health check on all services"""
        logger.info("🏥 BHIV HR Platform - Service Health Check")
        logger.info("=" * 50)
        
        results = {}
        
        for service_name, url in self.services.items():
            logger.info(f"🔍 Checking {service_name} at {url}...")
            
            is_up, status, status_code = await self.check_service_health(service_name, url)
            results[service_name] = {"up": is_up, "status": status, "code": status_code}
            
            status_icon = "✅" if is_up else "❌"
            logger.info(f"  {status_icon} {service_name.title()}: {status}")
        
        # Summary
        logger.info("=" * 50)
        logger.info("📊 Health Check Summary:")
        
        up_count = sum(1 for result in results.values() if result["up"])
        total_count = len(results)
        
        logger.info(f"Services Running: {up_count}/{total_count}")
        
        if up_count == 0:
            logger.error("❌ No services are running!")
            logger.info("💡 Start services with: docker-compose up -d")
        elif up_count < total_count:
            logger.warning(f"⚠️ Only {up_count} services are running")
            
            down_services = [name for name, result in results.items() if not result["up"]]
            logger.info(f"Down services: {', '.join(down_services)}")
        else:
            logger.info("🎉 All services are running!")
        
        return results

async def main():
    checker = ServiceHealthChecker()
    await checker.run_health_check()

if __name__ == "__main__":
    asyncio.run(main())