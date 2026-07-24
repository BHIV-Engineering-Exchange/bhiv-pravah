"""
Comprehensive System Test for AI Integration Platform

Tests all components including LLM integration, basket execution, and API endpoints.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from utils.llm_service import llm_service, query_law_agent
from agents.llm_agent_template import create_law_agent
import aiohttp

async def test_direct_api():
    """Test direct API calls to deployed law agent"""
    print("🔍 Testing Direct API Calls")
    print("=" * 50)
    
    base_url = "https://legal-agent-api-3yqg.onrender.com"
    test_query = "I was wrongfully terminated from my job. What are my rights?"
    
    endpoints = [
        ("/basic-query", "basic"),
        ("/adaptive-query", "adaptive"),
        ("/enhanced-query", "enhanced")
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint, agent_type in endpoints:
            try:
                payload = {
                    "user_input": test_query,
                    "session_id": f"test_{agent_type}"
                }
                
                print(f"\n📡 Testing {agent_type} agent: {base_url}{endpoint}")
                
                async with session.post(f"{base_url}{endpoint}", json=payload, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ {agent_type.title()} Agent Success!")
                        print(f"   Domain: {result.get('domain', 'N/A')}")
                        print(f"   Confidence: {result.get('confidence', 'N/A')}")
                        print(f"   Route: {result.get('legal_route', 'N/A')}")
                    else:
                        error = await response.text()
                        print(f"❌ {agent_type.title()} Agent Failed: {response.status}")
                        print(f"   Error: {error}")
                        
            except Exception as e:
                print(f"💥 {agent_type.title()} Agent Exception: {e}")

async def test_llm_service():
    """Test the LLM service manager"""
    print("\n🔧 Testing LLM Service Manager")
    print("=" * 50)
    
    # Test service status
    status = llm_service.get_status()
    print(f"📊 Service Status:")
    print(f"   Total Endpoints: {status['total_endpoints']}")
    print(f"   Healthy Endpoints: {status['healthy_endpoints']}")
    
    for name, info in status['endpoints'].items():
        health_icon = "✅" if info['healthy'] else "❌"
        print(f"   {health_icon} {name}: {info['url']} (Priority: {info['priority']})")
    
    # Test law agent query
    print(f"\n🏛️ Testing Law Agent Query...")
    try:
        result = await query_law_agent(
            "What are tenant rights in California?", 
            agent_type="enhanced",
            location="California"
        )
        
        if "error" not in result:
            print("✅ Law Agent Query Success!")
            print(f"   Domain: {result.get('domain', 'N/A')}")
            print(f"   Jurisdiction: {result.get('jurisdiction', 'N/A')}")
        else:
            print(f"❌ Law Agent Query Failed: {result['error']}")
            
    except Exception as e:
        print(f"💥 Law Agent Query Exception: {e}")

async def test_agent_template():
    """Test the generic LLM agent template"""
    print("\n🤖 Testing LLM Agent Template")
    print("=" * 50)
    
    try:
        agent = create_law_agent()
        
        test_input = {
            "query": "I need help with a contract dispute",
            "agent_type": "basic"
        }
        
        print(f"📝 Testing with input: {test_input}")
        result = await agent.process(test_input)
        
        if "error" not in result:
            print("✅ Agent Template Success!")
            print(f"   Agent Type: {result.get('agent_type', 'N/A')}")
            print(f"   Session ID: {result.get('session_id', 'N/A')}")
            print(f"   Timestamp: {result.get('timestamp', 'N/A')}")
        else:
            print(f"❌ Agent Template Failed: {result['error']}")
            
    except Exception as e:
        print(f"💥 Agent Template Exception: {e}")

async def test_basket_integration():
    """Test basket system with law agent"""
    print("\n🧺 Testing Basket Integration")
    print("=" * 50)
    
    try:
        # Import basket components
        from baskets.basket_manager import AgentBasket
        from agents.agent_registry import AgentRegistry
        from communication.event_bus import EventBus
        from utils.redis_service import RedisService
        
        # Setup components
        registry = AgentRegistry("agents")
        event_bus = EventBus()
        redis_service = RedisService()
        
        # Create test basket
        basket_spec = {
            "basket_name": "law_test_basket",
            "agents": ["law_agent"],
            "execution_strategy": "sequential",
            "description": "Test basket for law agent"
        }
        
        basket = AgentBasket(basket_spec, registry, event_bus, redis_service)
        
        test_input = {
            "query": "What should I do if my landlord won't fix the heating?",
            "agent_type": "enhanced",
            "location": "New York"
        }
        
        print(f"🚀 Executing basket with input: {test_input}")
        result = await basket.execute(test_input)
        
        if "error" not in result:
            print("✅ Basket Execution Success!")
            print(f"   Execution ID: {basket.execution_id}")
            print(f"   Result Keys: {list(result.keys())}")
        else:
            print(f"❌ Basket Execution Failed: {result['error']}")
            
    except Exception as e:
        print(f"💥 Basket Integration Exception: {e}")

async def test_main_api_endpoints():
    """Test the main FastAPI endpoints"""
    print("\n🌐 Testing Main API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    endpoints_to_test = [
        ("/health", "GET"),
        ("/agents", "GET"),
        ("/baskets", "GET")
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint, method in endpoints_to_test:
            try:
                print(f"📡 Testing {method} {base_url}{endpoint}")
                
                async with session.request(method, f"{base_url}{endpoint}", timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ {endpoint} Success!")
                        if endpoint == "/health":
                            print(f"   Status: {result.get('status', 'N/A')}")
                        elif endpoint == "/agents":
                            print(f"   Agents Found: {len(result) if isinstance(result, list) else 'N/A'}")
                        elif endpoint == "/baskets":
                            print(f"   Baskets Found: {result.get('count', 'N/A')}")
                    else:
                        print(f"❌ {endpoint} Failed: {response.status}")
                        
            except aiohttp.ClientConnectorError:
                print(f"🔌 {endpoint} - Server not running (start with: python main.py)")
            except Exception as e:
                print(f"💥 {endpoint} Exception: {e}")

async def run_comprehensive_test():
    """Run all tests in sequence"""
    print("🚀 AI Integration System - Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        ("Direct API Test", test_direct_api),
        ("LLM Service Test", test_llm_service),
        ("Agent Template Test", test_agent_template),
        ("Basket Integration Test", test_basket_integration),
        ("Main API Endpoints Test", test_main_api_endpoints)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running: {test_name}")
            await test_func()
            results[test_name] = "✅ PASSED"
        except Exception as e:
            results[test_name] = f"❌ FAILED: {e}"
            print(f"💥 {test_name} failed with exception: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        print(f"{result} {test_name}")
    
    passed = sum(1 for r in results.values() if "PASSED" in r)
    total = len(results)
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your system is ready for deployment.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())
