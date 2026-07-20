#!/usr/bin/env python3
"""
Simple test to verify LangGraph main.py can start
"""

import sys
import os
from pathlib import Path

def test_direct_import():
    """Test importing main.py directly from the app directory"""
    print("Testing Direct Import of LangGraph main.py")
    print("=" * 50)
    
    # Set environment variables
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    os.environ["API_KEY"] = "test-api-key"
    
    # Change to app directory
    app_path = Path("services/langgraph/app")
    langgraph_path = Path("services/langgraph")
    
    if not app_path.exists():
        print("ERROR: App directory not found")
        return False
    
    # Add paths
    sys.path.insert(0, str(app_path.absolute()))
    sys.path.insert(0, str(langgraph_path.absolute()))
    
    try:
        # Import main directly
        import main
        
        print("  OK: main.py imported successfully")
        
        # Check FastAPI app
        if hasattr(main, 'app'):
            app = main.app
            print(f"  OK: FastAPI app found: {app.title}")
            print(f"  OK: Version: {app.version}")
            
            # Count routes
            routes = [r for r in app.routes if hasattr(r, 'path')]
            print(f"  OK: Routes: {len(routes)}")
            
            # Test key endpoints
            key_paths = ["/", "/health", "/workflows", "/test-integration"]
            found_paths = [r.path for r in routes if r.path in key_paths]
            print(f"  OK: Key endpoints: {found_paths}")
            
        return True
        
    except Exception as e:
        print(f"  FAIL: Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("BHIV HR LangGraph Service - Simple Import Test")
    print("=" * 55)
    
    success = test_direct_import()
    
    print("\n" + "=" * 55)
    if success:
        print("SUCCESS: LangGraph main.py imports and works!")
        print("\nTo start the service:")
        print("cd services/langgraph")
        print("uvicorn app.main:app --host 0.0.0.0 --port 9001")
    else:
        print("FAILED: Import issues remain")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)