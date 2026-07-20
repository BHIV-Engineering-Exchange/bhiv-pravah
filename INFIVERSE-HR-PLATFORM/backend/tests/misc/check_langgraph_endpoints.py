#!/usr/bin/env python3
"""
Check LangGraph Available Endpoints
"""

import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

LANGGRAPH_URL = "https://bhiv-hr-langgraph.onrender.com"
API_KEY = os.getenv("API_KEY_SECRET", "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

async def check_endpoints():
    """Check available endpoints"""
    print("Checking LangGraph Available Endpoints...")
    print("=" * 50)
    
    # Try to get OpenAPI docs
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{LANGGRAPH_URL}/docs")
            print(f"OpenAPI Docs: {response.status_code}")
            
            # Try root endpoint
            response = await client.get(f"{LANGGRAPH_URL}/", headers=HEADERS)
            print(f"Root endpoint: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Root data: {data}")
            
            # Check common endpoints
            endpoints_to_check = [
                "/health",
                "/test-integration", 
                "/workflows",
                "/tools/send-notification",
                "/test/send-email",
                "/test/send-whatsapp", 
                "/test/send-telegram"
            ]
            
            print("\nEndpoint Status Check:")
            print("-" * 30)
            
            for endpoint in endpoints_to_check:
                try:
                    response = await client.get(f"{LANGGRAPH_URL}{endpoint}", headers=HEADERS)
                    print(f"{endpoint:25} {response.status_code}")
                except Exception as e:
                    print(f"{endpoint:25} ERROR: {str(e)}")
                    
    except Exception as e:
        print(f"Error checking endpoints: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_endpoints())