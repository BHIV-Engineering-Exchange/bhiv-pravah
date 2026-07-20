#!/usr/bin/env python3
"""
Test script to verify the actual main.py file can be imported
"""

import sys
import os
from pathlib import Path

def test_main_py_import():
    """Test importing the actual main.py file"""
    print("Testing LangGraph main.py File Import")
    print("=" * 45)
    
    # Set environment variables to avoid database connection issues
    os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    os.environ.setdefault("API_KEY", "test-api-key-12345")
    os.environ.setdefault("LANGGRAPH_API_KEY", "test-langgraph-key")
    
    # Add the services/langgraph directory to Python path
    langgraph_path = Path("services/langgraph")
    if langgraph_path.exists():
        sys.path.insert(0, str(langgraph_path))
        print(f"Added to path: {langgraph_path.absolute()}")
    else:
        print("ERROR: services/langgraph directory not found")
        return False
    
    # Add the app subdirectory to path
    app_path = Path("services/langgraph/app")
    if app_path.exists():
        sys.path.insert(0, str(app_path))
        print(f"Added to path: {app_path.absolute()}")
    
    try:
        print("\nAttempting to import main.py...")
        
        # Try to import the main module
        import main
        
        print("  OK: main.py imported successfully")
        
        # Check if the FastAPI app exists
        if hasattr(main, 'app'):
            print("  OK: FastAPI app found")
            
            # Check app configuration
            app = main.app
            print(f"  OK: App title: {app.title}")
            print(f"  OK: App version: {app.version}")
            
            # Check if routes are registered
            routes = [route.path for route in app.routes]
            print(f"  OK: Found {len(routes)} routes")
            
            # Check for key endpoints
            key_endpoints = ["/", "/health", "/workflows/application/start", "/workflows", "/test-integration"]
            found_endpoints = [endpoint for endpoint in key_endpoints if endpoint in routes]
            print(f"  OK: Key endpoints found: {len(found_endpoints)}/{len(key_endpoints)}")
            
            for endpoint in found_endpoints:
                print(f"    - {endpoint}")
            
        else:
            print("  WARN: FastAPI app not found in main module")
        
        # Check for key functions/classes
        key_components = ['WorkflowRequest', 'WorkflowStatus', 'get_api_key']
        found_components = [comp for comp in key_components if hasattr(main, comp)]
        print(f"  OK: Key components found: {len(found_components)}/{len(key_components)}")
        
        for comp in found_components:
            print(f"    - {comp}")
        
        return True
        
    except ImportError as e:
        print(f"  FAIL: Import error: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_tracker_import():
    """Test importing workflow_tracker separately"""
    print("\nTesting workflow_tracker.py Import:")
    
    # Set a mock database URL to avoid connection errors
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    
    try:
        import workflow_tracker
        print("  OK: workflow_tracker imported successfully")
        
        # Check if WorkflowTracker class exists
        if hasattr(workflow_tracker, 'WorkflowTracker'):
            print("  OK: WorkflowTracker class found")
        else:
            print("  WARN: WorkflowTracker class not found")
        
        return True
        
    except Exception as e:
        print(f"  FAIL: workflow_tracker import error: {e}")
        return False

def main():
    """Main test function"""
    print("BHIV HR LangGraph Service - Main.py Import Test")
    print("=" * 55)
    
    # Test workflow_tracker first (it's a dependency)
    tracker_ok = test_workflow_tracker_import()
    
    # Test main.py import
    main_ok = test_main_py_import()
    
    # Summary
    print("\n" + "=" * 55)
    print("IMPORT TEST SUMMARY:")
    print(f"  workflow_tracker.py: {'OK' if tracker_ok else 'FAILED'}")
    print(f"  main.py: {'OK' if main_ok else 'FAILED'}")
    
    if main_ok and tracker_ok:
        print("\nOVERALL STATUS: MAIN.PY CAN BE IMPORTED SUCCESSFULLY")
        print("The LangGraph service is ready to start!")
        print("\nTo start the service:")
        print("cd services/langgraph")
        print("uvicorn app.main:app --host 0.0.0.0 --port 9001")
        return True
    else:
        print("\nOVERALL STATUS: IMPORT ISSUES FOUND")
        if not tracker_ok:
            print("- Fix workflow_tracker.py database connection issues")
        if not main_ok:
            print("- Fix main.py import issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)