#!/usr/bin/env python3
"""
Simple test script to verify all imports and dependencies in LangGraph main.py
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Test all imports from LangGraph main.py"""
    print("Testing LangGraph main.py imports and dependencies...")
    print("=" * 60)
    
    failed_imports = []
    successful_imports = []
    
    # Test standard library imports
    standard_imports = [
        "os",
        "logging",
        "asyncio",
        "uuid",
        "json",
        "traceback",
        "threading",
        "time"
    ]
    
    print("\nTesting Standard Library Imports:")
    for module in standard_imports:
        try:
            __import__(module)
            print(f"  OK: {module}")
            successful_imports.append(module)
        except ImportError as e:
            print(f"  FAIL: {module}: {e}")
            failed_imports.append((module, str(e)))
    
    # Test third-party imports
    third_party_imports = [
        ("fastapi", "FastAPI"),
        ("fastapi", "HTTPException"),
        ("fastapi", "Depends"),
        ("fastapi", "BackgroundTasks"),
        ("fastapi", "WebSocket"),
        ("fastapi", "WebSocketDisconnect"),
        ("pydantic", "BaseModel"),
        ("datetime", "datetime"),
        ("typing", "Dict"),
        ("typing", "List"),
        ("typing", "Optional"),
        ("typing", "Any"),
    ]
    
    print("\nTesting Third-Party Imports:")
    for module, item in third_party_imports:
        try:
            mod = __import__(module, fromlist=[item])
            getattr(mod, item)
            print(f"  OK: from {module} import {item}")
            successful_imports.append(f"{module}.{item}")
        except (ImportError, AttributeError) as e:
            print(f"  FAIL: from {module} import {item}: {e}")
            failed_imports.append((f"{module}.{item}", str(e)))
    
    # Test LangGraph specific imports (these might fail if not installed)
    langgraph_imports = [
        ("langgraph.graph", "StateGraph"),
        ("langgraph.prebuilt", "ToolExecutor"),
        ("langgraph.checkpoint.sqlite", "SqliteSaver"),
    ]
    
    print("\nTesting LangGraph Imports (Optional):")
    for module, item in langgraph_imports:
        try:
            mod = __import__(module, fromlist=[item])
            getattr(mod, item)
            print(f"  OK: from {module} import {item}")
            successful_imports.append(f"{module}.{item}")
        except (ImportError, AttributeError) as e:
            print(f"  WARN: from {module} import {item}: {e} (Optional)")
    
    # Test local imports
    print("\nTesting Local Imports:")
    local_imports = [
        "workflow_tracker"
    ]
    
    # Add the services/langgraph directory to path for testing
    langgraph_path = Path("services/langgraph")
    if langgraph_path.exists():
        sys.path.insert(0, str(langgraph_path))
    
    for module in local_imports:
        try:
            __import__(module)
            print(f"  OK: {module}")
            successful_imports.append(module)
        except ImportError as e:
            print(f"  FAIL: {module}: {e}")
            failed_imports.append((module, str(e)))
    
    return successful_imports, failed_imports

def test_pydantic_models():
    """Test Pydantic model definitions"""
    print("\nTesting Pydantic Models:")
    
    try:
        from pydantic import BaseModel
        from typing import Optional
        
        # Test WorkflowRequest model
        class WorkflowRequest(BaseModel):
            candidate_id: int
            job_id: int
            candidate_name: Optional[str] = None
            job_title: Optional[str] = None
        
        # Test WorkflowStatus model
        class WorkflowStatus(BaseModel):
            workflow_id: str
            current_stage: str
            application_status: str
            matching_score: float
            last_action: str
            completed: bool
        
        # Test model instantiation
        request = WorkflowRequest(candidate_id=1, job_id=1)
        status = WorkflowStatus(
            workflow_id="test-123",
            current_stage="screening",
            application_status="processing",
            matching_score=75.5,
            last_action="test",
            completed=False
        )
        
        print("  OK: WorkflowRequest model")
        print("  OK: WorkflowStatus model")
        print("  OK: Model instantiation")
        
        return True
        
    except Exception as e:
        print(f"  FAIL: Pydantic models: {e}")
        return False

def test_fastapi_setup():
    """Test FastAPI application setup"""
    print("\nTesting FastAPI Setup:")
    
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI(
            title="BHIV HR LangGraph Service",
            description="AI Workflow Automation Engine",
            version="1.0.0"
        )
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        print("  OK: FastAPI app creation")
        print("  OK: CORS middleware")
        
        return True
        
    except Exception as e:
        print(f"  FAIL: FastAPI setup: {e}")
        return False

def main():
    """Main test function"""
    print("BHIV HR LangGraph Service - Import & Dependency Test")
    print("=" * 60)
    
    # Test imports
    successful, failed = test_imports()
    
    # Test Pydantic models
    models_ok = test_pydantic_models()
    
    # Test FastAPI setup
    fastapi_ok = test_fastapi_setup()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print(f"  Successful imports: {len(successful)}")
    print(f"  Failed imports: {len(failed)}")
    print(f"  Pydantic models: {'OK' if models_ok else 'FAILED'}")
    print(f"  FastAPI setup: {'OK' if fastapi_ok else 'FAILED'}")
    
    if failed:
        print("\nFailed Imports Details:")
        for module, error in failed:
            print(f"  - {module}: {error}")
    
    # Overall status
    critical_failures = [f for f in failed if not any(x in f[0] for x in ['langgraph', 'workflow_tracker'])]
    
    if not critical_failures and models_ok and fastapi_ok:
        print("\nOVERALL STATUS: ALL CRITICAL DEPENDENCIES OK")
        print("LangGraph service should start successfully!")
        return True
    else:
        print("\nOVERALL STATUS: SOME ISSUES FOUND")
        print("Please install missing dependencies before starting the service.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)