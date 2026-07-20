#!/usr/bin/env python3
"""
Test Each LangGraph File Functionality
"""

import sys
import os
sys.path.append('services/langgraph')
sys.path.append('services/langgraph/app')

def test_file_imports():
    """Test if each LangGraph file can be imported and works"""
    
    results = {}
    
    print("=== TESTING LANGGRAPH FILES ===\n")
    
    # Test 1: Communication.py
    try:
        from services.langgraph.app.communication import comm_manager
        results["communication.py"] = "WORKS - Communication manager initialized"
        print(f"WORKS communication.py: {comm_manager}")
    except Exception as e:
        results["communication.py"] = f"FAILS - {str(e)}"
        print(f"FAILS communication.py: {str(e)}")
    
    # Test 2: Main.py (FastAPI app)
    try:
        from services.langgraph.app.main import app
        results["main.py"] = "WORKS - FastAPI app created"
        print(f"WORKS main.py: FastAPI app with {len(app.routes)} routes")
    except Exception as e:
        results["main.py"] = f"FAILS - {str(e)}"
        print(f"FAILS main.py: {str(e)}")
    
    # Test 3: Tools.py
    try:
        from services.langgraph.app.tools import get_ai_matching_score
        results["tools.py"] = "WORKS - LangChain tools loaded"
        print(f"WORKS tools.py: LangChain tools available")
    except Exception as e:
        results["tools.py"] = f"FAILS - {str(e)}"
        print(f"FAILS tools.py: {str(e)}")
    
    # Test 4: Graphs.py (LangGraph workflow)
    try:
        from services.langgraph.app.graphs import create_application_workflow
        workflow = create_application_workflow()
        results["graphs.py"] = "WORKS - LangGraph workflow created"
        print(f"WORKS graphs.py: Workflow created successfully")
    except Exception as e:
        results["graphs.py"] = f"FAILS - {str(e)}"
        print(f"FAILS graphs.py: {str(e)}")
    
    # Test 5: Agents.py
    try:
        from services.langgraph.app.agents import application_screener_agent
        results["agents.py"] = "WORKS - AI agents loaded"
        print(f"WORKS agents.py: AI agents available")
    except Exception as e:
        results["agents.py"] = f"FAILS - {str(e)}"
        print(f"FAILS agents.py: {str(e)}")
    
    # Test 6: State.py
    try:
        from services.langgraph.app.state import CandidateApplicationState
        results["state.py"] = "WORKS - State definitions loaded"
        print(f"WORKS state.py: State management available")
    except Exception as e:
        results["state.py"] = f"FAILS - {str(e)}"
        print(f"FAILS state.py: {str(e)}")
    
    # Summary
    working = len([r for r in results.values() if "WORKS" in r])
    total = len(results)
    
    print(f"\n=== SUMMARY ===")
    print(f"Working files: {working}/{total}")
    
    for file, status in results.items():
        print(f"  {file}: {status}")
    
    return results

if __name__ == "__main__":
    test_file_imports()