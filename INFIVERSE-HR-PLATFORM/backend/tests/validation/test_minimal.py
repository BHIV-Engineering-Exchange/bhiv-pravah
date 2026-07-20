#!/usr/bin/env python3
"""
Minimal test to verify Gateway service can start
"""

import sys
import os

# Set up environment variables first
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
os.environ['API_KEY_SECRET'] = 'test_api_key_12345'
os.environ['JWT_SECRET'] = 'test_jwt_secret_12345'
os.environ['CANDIDATE_JWT_SECRET'] = 'test_candidate_jwt_12345'
os.environ['AGENT_SERVICE_URL'] = 'http://localhost:9000'
os.environ['ENVIRONMENT'] = 'development'

# Add services directory to path
services_dir = os.path.join(os.path.dirname(__file__), 'services')
sys.path.insert(0, services_dir)

def test_basic_imports():
    """Test basic imports without full app initialization"""
    print("Testing basic imports...")
    
    try:
        # Test gateway directory imports
        gateway_dir = os.path.join(services_dir, 'gateway')
        sys.path.insert(0, gateway_dir)
        
        # Test config
        import config
        print("Config module imported")
        
        # Test dependencies
        import dependencies
        print("Dependencies module imported")
        
        # Test LangGraph integration
        import langgraph_integration
        print("LangGraph integration imported")
        
        # Test monitoring
        import monitoring
        print("Monitoring module imported")
        
        return True
        
    except Exception as e:
        print(f"Import error: {e}")
        return False

def test_langgraph_router():
    """Test LangGraph router specifically"""
    print("Testing LangGraph router...")
    
    try:
        gateway_dir = os.path.join(services_dir, 'gateway')
        sys.path.insert(0, gateway_dir)
        
        from langgraph_integration import router as langgraph_router
        print(f"LangGraph router imported with {len(langgraph_router.routes)} routes")
        
        # List the routes
        for route in langgraph_router.routes:
            print(f"  - {route.methods} {route.path}")
        
        return True
        
    except Exception as e:
        print(f"LangGraph router error: {e}")
        return False

if __name__ == "__main__":
    print("BHIV HR Platform - Minimal Import Test")
    
    success1 = test_basic_imports()
    success2 = test_langgraph_router()
    
    if success1 and success2:
        print("SUCCESS: All basic imports work!")
        print("Gateway service imports are fixed.")
    else:
        print("FAILED: Some imports still have issues.")