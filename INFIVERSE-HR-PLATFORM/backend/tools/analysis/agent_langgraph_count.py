#!/usr/bin/env python3
"""
Exact Agent and LangGraph Endpoint Count
"""

# Agent Service endpoints from browser documentation
agent_endpoints = {
    "Core API Endpoints": 2,  # GET /, GET /health
    "AI Matching Engine": 2,  # POST /match, POST /batch-match
    "Candidate Analysis": 1,  # GET /analyze/{candidate_id}
    "System Diagnostics": 1   # GET /test-db
}

# LangGraph Service endpoints from browser documentation
langgraph_endpoints = {
    "Default": 2,             # GET /, GET /health
    "Workflow Management": 5, # POST /workflows/application/start, GET /workflows/{workflow_id}/status, POST /workflows/{workflow_id}/resume, GET /workflows, GET /workflows/stats
    "Tools": 1,               # POST /tools/send-notification
    "Integration": 1          # GET /test-integration
}

def main():
    print("EXACT ENDPOINT COUNT - AGENT & LANGGRAPH SERVICES")
    print("=" * 60)
    
    agent_total = sum(agent_endpoints.values())
    langgraph_total = sum(langgraph_endpoints.values())
    
    print("AGENT SERVICE BREAKDOWN:")
    print("-" * 30)
    for category, count in agent_endpoints.items():
        print(f"{category:20} : {count:2d}")
    print("-" * 30)
    print(f"{'AGENT TOTAL':20} : {agent_total:2d}")
    
    print()
    print("LANGGRAPH SERVICE BREAKDOWN:")
    print("-" * 30)
    for category, count in langgraph_endpoints.items():
        print(f"{category:20} : {count:2d}")
    print("-" * 30)
    print(f"{'LANGGRAPH TOTAL':20} : {langgraph_total:2d}")
    
    print()
    print("UPDATED SYSTEM TOTALS:")
    print("-" * 30)
    gateway_total = 74  # From previous count
    system_total = gateway_total + agent_total + langgraph_total
    
    print(f"Gateway Service  : {gateway_total}")
    print(f"Agent Service    : {agent_total}")
    print(f"LangGraph Service: {langgraph_total}")
    print(f"Portal Services  : 3 (web interfaces)")
    print("-" * 30)
    print(f"TOTAL ENDPOINTS  : {system_total}")
    
    return {
        "agent": agent_total,
        "langgraph": langgraph_total,
        "gateway": gateway_total,
        "total": system_total
    }

if __name__ == "__main__":
    counts = main()
    print(f"\nFINAL COUNTS:")
    print(f"Agent: {counts['agent']} endpoints")
    print(f"LangGraph: {counts['langgraph']} endpoints")
    print(f"Total System: {counts['total']} endpoints")