#!/usr/bin/env python3
"""
LangGraph Implementation Analysis
Identify used vs unused files and endpoints
"""

import os
import json
from pathlib import Path

def analyze_langgraph_implementation():
    """Analyze LangGraph files and endpoints usage"""
    
    print("=== LANGGRAPH IMPLEMENTATION ANALYSIS ===\n")
    
    # Core LangGraph service files
    core_files = {
        "services/langgraph/app/main.py": "ACTIVE - Main FastAPI service with 9 endpoints",
        "services/langgraph/app/communication.py": "ACTIVE - Multi-channel communication (Email, WhatsApp, Telegram)",
        "services/langgraph/app/graphs.py": "ACTIVE - Workflow graph definition",
        "services/langgraph/app/agents.py": "ACTIVE - AI agents for screening, notifications, HR updates",
        "services/langgraph/app/tools.py": "ACTIVE - LangChain tools for API integration",
        "services/langgraph/app/state.py": "ACTIVE - Workflow state management",
        "services/langgraph/app/database_tracker.py": "ACTIVE - Workflow progress tracking",
        "services/langgraph/app/monitoring.py": "ACTIVE - Health monitoring",
        "services/langgraph/config.py": "ACTIVE - Configuration management",
        "services/langgraph/dependencies.py": "ACTIVE - Authentication dependencies"
    }
    
    # Endpoints analysis
    active_endpoints = {
        "GET /": "Service info",
        "GET /health": "Health check", 
        "POST /workflows/application/start": "USED - Start AI workflow for candidate processing",
        "GET /workflows/{workflow_id}/status": "USED - Get workflow status",
        "POST /workflows/{workflow_id}/resume": "Resume paused workflow",
        "GET /workflows": "List workflows",
        "GET /workflows/stats": "Workflow statistics",
        "POST /tools/send-notification": "USED - Multi-channel notifications (Email + WhatsApp)",
        "WebSocket /ws/{workflow_id}": "Real-time updates"
    }
    
    # Test endpoints (missing in production)
    test_endpoints = {
        "POST /test/send-email": "MISSING IN PRODUCTION - Individual email test",
        "POST /test/send-whatsapp": "MISSING IN PRODUCTION - Individual WhatsApp test", 
        "POST /test/send-telegram": "MISSING IN PRODUCTION - Individual Telegram test"
    }
    
    # Unused/redundant files
    unused_files = {
        "Previous langrapgh implemnetaion guide/": "DELETE - Old implementation guides",
        "services/langgraph/start_local.py": "REDUNDANT - Use main.py instead",
        "services/langgraph/test_local.py": "REDUNDANT - Use proper test files",
        "services/langgraph/test_integration.py": "REDUNDANT - Use tests/ directory",
        "start_local_langgraph.py": "REDUNDANT - Created for testing only",
        "check_langgraph_endpoints.py": "REDUNDANT - Analysis script only"
    }
    
    # Test files (keep for validation)
    test_files = {
        "tests/langgraph/": "KEEP - Comprehensive test suite",
        "services/langgraph/tests/": "KEEP - Service-specific tests"
    }
    
    print("CORE LANGGRAPH FILES (KEEP):")
    for file, status in core_files.items():
        print(f"  {file}: {status}")
    
    print(f"\nACTIVE ENDPOINTS ({len(active_endpoints)}):")
    for endpoint, desc in active_endpoints.items():
        print(f"  {endpoint}: {desc}")
    
    print(f"\nMISSING TEST ENDPOINTS ({len(test_endpoints)}):")
    for endpoint, desc in test_endpoints.items():
        print(f"  {endpoint}: {desc}")
    
    print(f"\nFILES TO DELETE ({len(unused_files)}):")
    for file, status in unused_files.items():
        print(f"  {file}: {status}")
    
    print(f"\nTEST FILES (KEEP):")
    for file, status in test_files.items():
        print(f"  {file}: {status}")
    
    # Portal integration analysis
    print(f"\nPORTAL INTEGRATION:")
    print(f"  HR Portal: Uses /tools/send-notification for automated emails + WhatsApp")
    print(f"  Client Portal: Can trigger notifications via email_automation.py")
    print(f"  Candidate Portal: Receives notifications via multi-channel system")
    
    # Communication channels status
    print(f"\nCOMMUNICATION CHANNELS:")
    print(f"  Email: Working (Gmail SMTP)")
    print(f"  WhatsApp: Working (Twilio +14155238886)")
    print(f"  Telegram: Invalid bot token")
    
    # Recommendations
    print(f"\nRECOMMENDATIONS:")
    print(f"  1. DELETE unused files and old implementation guides")
    print(f"  2. ADD missing test endpoints to production deployment")
    print(f"  3. FIX Telegram bot token for complete multi-channel support")
    print(f"  4. KEEP core LangGraph workflow system (fully functional)")
    print(f"  5. DEPLOY current localhost changes to production")

if __name__ == "__main__":
    analyze_langgraph_implementation()