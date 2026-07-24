#!/usr/bin/env python3
"""
Test script for Law Agent integration with LLM baskets project

This script tests:
1. Law agent can be loaded by the agent registry
2. Law agent can process queries through the basket system
3. Law agent can run as a standalone FastAPI server
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

async def test_law_agent_basket_integration():
    """Test law agent integration with basket system"""
    try:
        print("🔍 Testing Law Agent basket integration...")

        # Import required modules
        from agents.agent_registry import AgentRegistry
        from baskets.basket_manager import AgentBasket
        from communication.event_bus import EventBus
        from database.mongo_db import MongoDBClient
        from utils.redis_service import RedisService
        from utils.logger import logger

        # Initialize components
        print("📚 Initializing agent registry...")
        registry = AgentRegistry("agents")

        # Check if law agent was loaded
        law_agent_spec = registry.get_agent("law_agent")
        if not law_agent_spec:
            print("❌ Law agent not found in registry")
            return False

        print("✅ Law agent found in registry:")
        print(f"   - Name: {law_agent_spec.get('name')}")
        print(f"   - Domains: {law_agent_spec.get('domains')}")
        print(f"   - Module path: {law_agent_spec.get('module_path')}")

        # Create test input
        test_input = {
            "query": "I was wrongfully terminated from my job. What are my rights?",
            "agent_type": "enhanced",
            "location": "California, USA",
            "feedback": True
        }

        # Test agent compatibility
        is_compatible = registry.validate_compatibility("law_agent", test_input)
        print(f"✅ Input compatibility check: {'PASS' if is_compatible else 'FAIL'}")

        if not is_compatible:
            print("❌ Law agent input validation failed")
            return False

        # Initialize basket components
        print("🏗️ Initializing basket components...")
        event_bus = EventBus()
        mongo_client = MongoDBClient()
        redis_service = RedisService()

        # Create basket specification
        basket_spec = {
            "basket_name": "law_agent_test",
            "description": "Test basket for Law Agent",
            "agents": ["law_agent"],
            "execution_strategy": "sequential"
        }

        # Create and execute basket
        print("🚀 Executing test basket...")
        basket = AgentBasket(basket_spec, registry, event_bus, redis_service, mongo_client)

        result = await basket.execute(test_input)

        # Check result
        if "error" in result:
            print(f"❌ Basket execution failed: {result['error']}")
            return False

        print("✅ Basket execution successful!")
        print("📋 Law Agent Results:")
        print(f"   - Domain: {result.get('domain', 'N/A')}")
        print(f"   - Confidence: {result.get('confidence', 'N/A')}")
        print(f"   - Legal Route: {result.get('legal_route', 'N/A')}")
        print(f"   - Timeline: {result.get('timeline', 'N/A')}")

        # Clean up
        basket.close()
        mongo_client.close()

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_law_agent_standalone():
    """Test law agent standalone functionality"""
    try:
        print("\n🔍 Testing Law Agent standalone functionality...")

        # Import law agent module
        from agents.law_agent.law_agent import process

        # Test basic query processing
        test_input = {
            "query": "I need help with a tenant-landlord dispute",
            "agent_type": "basic"
        }

        print("🧠 Testing basic agent processing...")
        result = await process(test_input)

        if "error" in result:
            print(f"❌ Standalone processing failed: {result['error']}")
            return False

        print("✅ Standalone processing successful!")
        print(f"   - Domain: {result.get('domain', 'N/A')}")
        print(f"   - Confidence: {result.get('confidence', 'N/A')}")

        return True

    except Exception as e:
        print(f"❌ Standalone test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fastapi_availability():
    """Test if FastAPI server can be started"""
    try:
        print("\n🔍 Testing FastAPI server availability...")

        # Try to import FastAPI components
        from agents.law_agent.law_agent import app

        if app is not None:
            print("✅ FastAPI app is available")
            print("📚 API Documentation would be available at: http://localhost:8000/docs")
            return True
        else:
            print("⚠️ FastAPI app not available (dependencies may be missing)")
            return False

    except ImportError as e:
        print(f"⚠️ FastAPI not available: {e}")
        return False

async def main():
    """Main test function"""
    print("🧑‍⚖️ Law Agent Integration Test Suite")
    print("=" * 50)

    # Test 1: Basket integration
    basket_test_passed = await test_law_agent_basket_integration()

    # Test 2: Standalone functionality
    standalone_test_passed = await test_law_agent_standalone()

    # Test 3: FastAPI availability
    fastapi_available = test_fastapi_availability()

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Basket Integration: {'✅ PASS' if basket_test_passed else '❌ FAIL'}")
    print(f"   Standalone Processing: {'✅ PASS' if standalone_test_passed else '❌ FAIL'}")
    print(f"   FastAPI Server: {'✅ AVAILABLE' if fastapi_available else '⚠️ UNAVAILABLE'}")

    overall_success = basket_test_passed and standalone_test_passed
    print(f"\n🏆 Overall Result: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")

    if overall_success:
        print("\n🎉 Law Agent has been successfully integrated!")
        print("   - Can be used in basket configurations")
        print("   - Supports standalone processing")
        if fastapi_available:
            print("   - FastAPI server available for web API")
        print("\n💡 Usage Examples:")
        print("   1. Basket: Include 'law_agent' in your basket configuration")
        print("   2. Standalone: Import and call process() function")
        if fastapi_available:
            print("   3. Web API: Run 'python law_agent.py' to start server")
    else:
        print("\n❌ Integration issues detected. Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())
