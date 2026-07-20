#!/usr/bin/env python3
"""
Test script to verify Gateway service imports work correctly
"""

import sys
import os

# Add services directory to path
services_dir = os.path.join(os.path.dirname(__file__), 'services')
sys.path.insert(0, services_dir)

def test_gateway_imports():
    """Test all gateway service imports"""
    print("🧪 Testing Gateway Service Imports...")
    
    try:
        # Test config import
        sys.path.insert(0, os.path.join(services_dir, 'gateway'))
        from config import validate_config, setup_logging, ENVIRONMENT
        print("✅ Config import successful")
        
        # Test monitoring import
        from monitoring import monitor, log_resume_processing
        print("✅ Monitoring import successful")
        
        # Test dependencies import
        from dependencies import get_api_key, get_auth
        print("✅ Dependencies import successful")
        
        # Test LangGraph integration import
        from langgraph_integration import router as langgraph_router
        print("✅ LangGraph integration import successful")
        
        # Test auth routes import
        sys.path.insert(0, os.path.join(services_dir, 'gateway', 'routes'))
        from auth import router as auth_router
        print("✅ Auth routes import successful")
        
        print("\n🎉 All Gateway imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_main_app_import():
    """Test main FastAPI app import"""
    print("\n🧪 Testing Main App Import...")
    
    try:
        # Set required environment variables for testing
        os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')
        os.environ.setdefault('API_KEY_SECRET', 'test_api_key')
        os.environ.setdefault('JWT_SECRET', 'test_jwt_secret')
        os.environ.setdefault('CANDIDATE_JWT_SECRET', 'test_candidate_jwt')
        os.environ.setdefault('AGENT_SERVICE_URL', 'http://localhost:9000')
        
        # Test main app import
        sys.path.insert(0, os.path.join(services_dir, 'gateway', 'app'))
        from main import app
        print("✅ Main FastAPI app import successful")
        
        # Check if LangGraph routes are included
        route_paths = [route.path for route in app.routes]
        langgraph_routes = [path for path in route_paths if '/api/v1/workflow' in path]
        
        if langgraph_routes:
            print(f"✅ LangGraph routes found: {len(langgraph_routes)} routes")
        else:
            print("⚠️ No LangGraph routes found - check integration")
        
        print(f"📊 Total routes in app: {len(route_paths)}")
        return True
        
    except ImportError as e:
        print(f"❌ Main app import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Main app error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 BHIV HR Platform - Gateway Import Test\n")
    
    success1 = test_gateway_imports()
    success2 = test_main_app_import()
    
    if success1 and success2:
        print("\n🎯 All tests passed! Gateway service is ready.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the errors above.")
        sys.exit(1)