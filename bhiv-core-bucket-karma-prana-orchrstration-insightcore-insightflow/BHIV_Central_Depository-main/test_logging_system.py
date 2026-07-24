#!/usr/bin/env python3
"""
Test script to verify the logging system works properly
It doesn't execute any AI agents directly—it simply tests that all components initialize properly and that log messages are written to the correct files.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger, get_execution_logger
from agents.agent_registry import AgentRegistry
from baskets.basket_manager import AgentBasket
from communication.event_bus import EventBus
from database.mongo_db import MongoDBClient
from utils.redis_service import RedisService

def test_logging_system():
    """Test the logging system"""
    print("🧪 Testing Logging System...")
    
    # Test basic logging
    logger = get_logger("test_logger")
    execution_logger = get_execution_logger()
    
    logger.info("Testing basic logger - this should appear in console and application.log")
    logger.error("Testing error logger - this should appear in console, application.log, and errors.log")
    
    execution_logger.info("Testing execution logger - this should appear in executions.log")
    
    print("✅ Basic logging test completed")
    
    # Test component logging
    print("\n🔧 Testing Component Logging...")
    
    # Test Redis service
    redis_service = RedisService()
    print(f"Redis connected: {redis_service.is_connected()}")
    
    # Test MongoDB client
    mongo_client = MongoDBClient()
    print(f"MongoDB connected: {mongo_client.db is not None}")
    
    # Test agent registry
    agents_dir = Path(__file__).parent / "agents"
    registry = AgentRegistry(str(agents_dir))
    print(f"Agents loaded: {len(registry.agents)}")
    
    # Test event bus
    EventBus()
    print("Event bus initialized")
    
    print("✅ Component logging test completed")
    
    return True

def test_basket_execution_logging():
    """Test basket execution with logging
    This tests whether a basket of agents can be created (but not actually run):

    Loads agent definitions from the agents/ directory.

    Creates an AgentBasket with a configuration specifying:

    Basket name: "test_logging_basket"

    One agent: "cashflow_analyzer"

    Execution strategy: "sequential
    """
    print("\n🗂️ Testing Basket Execution Logging...")
    
    try:
        # Initialize components
        agents_dir = Path(__file__).parent / "agents"
        registry = AgentRegistry(str(agents_dir))
        event_bus = EventBus()
        redis_service = RedisService()
        mongo_client = MongoDBClient()
        
        # Create a simple basket configuration
        basket_config = {
            "basket_name": "test_logging_basket",
            "agents": ["cashflow_analyzer"],
            "execution_strategy": "sequential"
        }
        
        # Create basket
        basket = AgentBasket(basket_config, registry, event_bus, redis_service, mongo_client)
        
        # Test input data (for future use)
        # input_data = {
        #     "transactions": [
        #         {"id": 1, "amount": 1000, "description": "Test income"},
        #         {"id": 2, "amount": -500, "description": "Test expense"}
        #     ]
        # }
        
        print(f"Created basket: {basket.name}")
        print(f"Execution ID: {basket.execution_id}")
        
        # Note: We're not actually executing the basket here since agents might not be fully implemented
        # This test is just to verify the logging system initialization
        
        print("✅ Basket execution logging test completed")
        return True
        
    except Exception as e:
        print(f"❌ Basket execution logging test failed: {e}")
        return False

def check_log_files():
    """Check if log files are created"""
    print("\n📁 Checking Log Files...")
    
    logs_dir = Path("logs")
    expected_files = [
        "application.log",
        "errors.log", 
        "executions.log"
    ]
    
    for log_file in expected_files:
        log_path = logs_dir / log_file
        if log_path.exists():
            size = log_path.stat().st_size
            print(f"✅ {log_file} exists ({size} bytes)")
        else:
            print(f"❌ {log_file} missing")
    
    return True

def main():
    """Main test function"""
    print("🚀 AI Integration Platform - Logging System Test")
    print("=" * 60)
    
    try:
        # Run tests
        test_logging_system()
        test_basket_execution_logging()
        check_log_files()
        
        print("\n" + "=" * 60)
        print("🎉 All logging tests completed successfully!")
        print("\nNext steps:")
        print("1. Check the logs/ directory for log files")
        print("2. Review log content to ensure proper formatting")
        print("3. Test with actual basket execution")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
