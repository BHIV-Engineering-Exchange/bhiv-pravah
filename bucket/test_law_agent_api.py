import asyncio
import aiohttp
import json

async def test_law_agent_api():
    """Test the deployed law agent API directly"""
    base_url = "https://legal-agent-api-3yqg.onrender.com"
    
    # Test basic query
    test_payload = {
        "user_input": "I was wrongfully terminated from my job. What are my rights?",
        "feedback": None,
        "session_id": "test_session_123"
    }
    
    endpoints = [
        f"{base_url}/basic-query",
        f"{base_url}/adaptive-query", 
        f"{base_url}/enhanced-query"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            try:
                print(f"\n🔍 Testing endpoint: {endpoint}")
                print(f"📤 Payload: {json.dumps(test_payload, indent=2)}")
                
                async with session.post(endpoint, json=test_payload, timeout=30) as response:
                    print(f"📊 Status Code: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Success! Response: {json.dumps(result, indent=2)}")
                    else:
                        error_text = await response.text()
                        print(f"❌ Error: {error_text}")
                        
            except asyncio.TimeoutError:
                print(f"⏰ Timeout connecting to {endpoint}")
            except Exception as e:
                print(f"💥 Exception: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_law_agent_api())
