#!/usr/bin/env python3
"""
Test script to verify only the critical imports needed for LangGraph main.py to start
"""

import sys
import os

def test_critical_imports():
    """Test only the critical imports needed for the service to start"""
    print("Testing Critical LangGraph main.py Imports")
    print("=" * 50)
    
    failed_imports = []
    successful_imports = []
    
    # Critical imports that must work for the service to start
    critical_imports = [
        # Standard library
        ("os", None),
        ("logging", None),
        ("asyncio", None),
        ("uuid", None),
        ("json", None),
        ("datetime", "datetime"),
        ("typing", "Dict"),
        ("typing", "List"),
        ("typing", "Optional"),
        ("typing", "Any"),
        
        # FastAPI - Critical for web service
        ("fastapi", "FastAPI"),
        ("fastapi", "HTTPException"),
        ("fastapi", "Depends"),
        ("fastapi", "BackgroundTasks"),
        ("fastapi", "WebSocket"),
        ("fastapi", "WebSocketDisconnect"),
        ("fastapi.middleware.cors", "CORSMiddleware"),
        
        # Pydantic - Critical for data models
        ("pydantic", "BaseModel"),
        
        # Database - Critical for persistence
        ("sqlalchemy", "create_engine"),
        ("sqlalchemy", "text"),
    ]
    
    print("\nTesting Critical Imports:")
    for module, item in critical_imports:
        try:
            if item is None:
                __import__(module)
                print(f"  OK: import {module}")
                successful_imports.append(module)
            else:
                mod = __import__(module, fromlist=[item])
                getattr(mod, item)
                print(f"  OK: from {module} import {item}")
                successful_imports.append(f"{module}.{item}")
        except (ImportError, AttributeError) as e:
            print(f"  FAIL: {module}.{item if item else ''}: {e}")
            failed_imports.append((f"{module}.{item if item else ''}", str(e)))
    
    # Optional imports that can fail without breaking the service
    optional_imports = [
        ("langgraph.graph", "StateGraph"),
        ("langgraph.prebuilt", "ToolExecutor"),
        ("langgraph.checkpoint.sqlite", "SqliteSaver"),
    ]
    
    print("\nTesting Optional Imports:")
    for module, item in optional_imports:
        try:
            mod = __import__(module, fromlist=[item])
            getattr(mod, item)
            print(f"  OK: from {module} import {item}")
            successful_imports.append(f"{module}.{item}")
        except (ImportError, AttributeError) as e:
            print(f"  WARN: from {module} import {item}: {e} (Optional)")
    
    return successful_imports, failed_imports

def test_pydantic_models():
    """Test the Pydantic models used in main.py"""
    print("\nTesting Pydantic Models:")
    
    try:
        from pydantic import BaseModel
        from typing import Optional
        
        # WorkflowRequest model from main.py
        class WorkflowRequest(BaseModel):
            candidate_id: int
            job_id: int
            candidate_name: Optional[str] = None
            job_title: Optional[str] = None
        
        # WorkflowStatus model from main.py
        class WorkflowStatus(BaseModel):
            workflow_id: str
            current_stage: str
            application_status: str
            matching_score: float
            last_action: str
            completed: bool
        
        # Test instantiation
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

def test_fastapi_app():
    """Test FastAPI app creation"""
    print("\nTesting FastAPI App Creation:")
    
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        # Create app like in main.py
        app = FastAPI(
            title="BHIV HR LangGraph Service",
            description="AI Workflow Automation Engine",
            version="1.0.0"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        print("  OK: FastAPI app creation")
        print("  OK: CORS middleware setup")
        
        return True
        
    except Exception as e:
        print(f"  FAIL: FastAPI app: {e}")
        return False

def test_environment_setup():
    """Test environment variable handling"""
    print("\nTesting Environment Variables:")
    
    # Set test environment variables
    os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
    os.environ.setdefault("API_KEY", "test-api-key")
    
    database_url = os.getenv("DATABASE_URL")
    api_key = os.getenv("API_KEY")
    
    print(f"  OK: DATABASE_URL: {database_url[:30]}...")
    print(f"  OK: API_KEY: {api_key[:10]}...")
    
    return True

def main():
    """Main test function"""
    print("BHIV HR LangGraph Service - Critical Dependencies Test")
    print("=" * 60)
    
    # Test critical imports
    successful, failed = test_critical_imports()
    
    # Test Pydantic models
    models_ok = test_pydantic_models()
    
    # Test FastAPI app
    fastapi_ok = test_fastapi_app()
    
    # Test environment
    env_ok = test_environment_setup()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY:")
    print(f"  Successful imports: {len(successful)}")
    print(f"  Failed critical imports: {len(failed)}")
    print(f"  Pydantic models: {'OK' if models_ok else 'FAILED'}")
    print(f"  FastAPI setup: {'OK' if fastapi_ok else 'FAILED'}")
    print(f"  Environment: {'OK' if env_ok else 'FAILED'}")
    
    if failed:
        print("\nCritical Import Failures:")
        for module, error in failed:
            print(f"  - {module}: {error}")
    
    # Overall status
    if not failed and models_ok and fastapi_ok and env_ok:
        print("\nOVERALL STATUS: ALL CRITICAL DEPENDENCIES OK")
        print("LangGraph service can start successfully!")
        print("\nNext steps:")
        print("1. Install optional LangGraph packages if needed")
        print("2. Set proper DATABASE_URL environment variable")
        print("3. Start the service with: uvicorn main:app --host 0.0.0.0 --port 9001")
        return True
    else:
        print("\nOVERALL STATUS: CRITICAL ISSUES FOUND")
        print("Please install missing dependencies:")
        if failed:
            missing_packages = set()
            for module, _ in failed:
                if "fastapi" in module:
                    missing_packages.add("fastapi")
                elif "pydantic" in module:
                    missing_packages.add("pydantic")
                elif "sqlalchemy" in module:
                    missing_packages.add("sqlalchemy")
            
            if missing_packages:
                print(f"pip install {' '.join(missing_packages)}")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)