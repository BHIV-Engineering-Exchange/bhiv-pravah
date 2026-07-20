#!/usr/bin/env python3
"""
🔍 Gateway Authentication Analysis
"""

import asyncio
import httpx
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def analyze_gateway_auth():
    """Analyze Gateway authentication requirements"""
    
    gateway_service_url = "http://localhost:8000"
    
    logger.info("🔍 Analyzing Gateway Authentication")
    logger.info("=" * 50)
    
    # Test 1: No authentication
    logger.info("🔑 Test 1: No authentication")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{gateway_service_url}/v1/jobs")
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Response: {response.text[:200]}")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    # Test 2: With X-API-Key header
    logger.info("\n🔑 Test 2: With X-API-Key header")
    try:
        headers = {'X-API-Key': '<YOUR_API_KEY>'}
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{gateway_service_url}/v1/jobs", headers=headers)
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Response: {response.text[:200]}")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    # Test 3: With Bearer token
    logger.info("\n🔑 Test 3: With Bearer token")
    try:
        headers = {'Authorization': 'Bearer <YOUR_API_KEY>'}
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{gateway_service_url}/v1/jobs", headers=headers)
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Response: {response.text[:200]}")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    # Test 4: Check health endpoint (should be public)
    logger.info("\n🔑 Test 4: Health endpoint (public)")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{gateway_service_url}/health")
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Response: {response.text[:200]}")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    # Test 5: Check OpenAPI docs (should be public)
    logger.info("\n🔑 Test 5: OpenAPI docs (public)")
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{gateway_service_url}/docs")
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_gateway_auth())