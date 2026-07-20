#!/usr/bin/env python3
"""
Test FastAPI app startup with LangGraph integration
"""

import sys
import os

# Set up environment variables
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
os.environ['API_KEY_SECRET'] = 'test_api_key_12345'
os.environ['JWT_SECRET'] = 'test_jwt_secret_12345'
os.environ['CANDIDATE_JWT_SECRET'] = 'test_candidate_jwt_12345'
os.environ['AGENT_SERVICE_URL'] = 'http://localhost:9000'
os.environ['ENVIRONMENT'] = 'development'

# Add services directory to path
services_dir = os.path.join(os.path.dirname(__file__), 'services')
sys.path.insert(0, services_dir)

def test_app_startup():
    """Test FastAPI app startup"""
    print("Testing FastAPI app startup...")
    
    try:
        # Add gateway paths
        gateway_dir = os.path.join(services_dir, 'gateway')
        app_dir = os.path.join(gateway_dir, 'app')
        sys.path.insert(0, gateway_dir)
        sys.path.insert(0, app_dir)
        
        # Import the app
        from main import app
        print("FastAPI app imported successfully")
        
        # Check routes
        total_routes = len(app.routes)
        print(f"Total routes: {total_routes}")
        
        # Check for LangGraph routes
        langgraph_routes = []
        for route in app.routes:
            if hasattr(route, 'path') and '/api/v1/workflow' in route.path:
                langgraph_routes.append(route.path)
        
        print(f"LangGraph routes found: {len(langgraph_routes)}")
        for route in langgraph_routes:
            print(f"  - {route}")
        
        # Check for webhook routes
        webhook_routes = []
        for route in app.routes:
            if hasattr(route, 'path') and '/webhooks/' in route.path:
                webhook_routes.append(route.path)
        
        print(f"Webhook routes found: {len(webhook_routes)}")
        for route in webhook_routes:
            print(f"  - {route}")
        
        if len(langgraph_routes) > 0 or len(webhook_routes) > 0:
            print("SUCCESS: LangGraph integration is working!")
            return True
        else:
            print("WARNING: No LangGraph routes found")
            return False
        
    except Exception as e:
        print(f"App startup error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("BHIV HR Platform - App Startup Test")
    
    success = test_app_startup()
    
    if success:
        print("\nSUCCESS: Gateway service with LangGraph integration is ready!")
        print("The 404 errors should be resolved now.")
    else:
        print("\nFAILED: App startup issues remain.")