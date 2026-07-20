#!/usr/bin/env python3
"""
Exact Endpoint Count from Browser Documentation
"""

# Exact count from browser documentation
gateway_endpoints = {
    "Authentication": 4,
    "LangGraph Workflows": 7,
    "Monitoring": 3,
    "Core API Endpoints": 5,
    "Job Management": 2,
    "Candidate Management": 5,
    "AI Matching Engine": 2,
    "Assessment & Workflow": 6,
    "Analytics & Statistics": 3,
    "Client Portal API": 2,
    "Security Testing": 12,
    "CSP Management": 4,
    "Two-Factor Authentication": 8,
    "Password Management": 6,
    "Candidate Portal": 8,
    "Recruiter Portal": 1
}

# Other services
agent_endpoints = 6
langgraph_endpoints = 25  # Standalone service
portal_endpoints = 3  # Web interfaces

def main():
    print("EXACT ENDPOINT COUNT FROM BROWSER DOCUMENTATION")
    print("=" * 60)
    
    gateway_total = sum(gateway_endpoints.values())
    system_total = gateway_total + agent_endpoints + langgraph_endpoints
    
    print(f"GATEWAY SERVICE BREAKDOWN:")
    print("-" * 30)
    for category, count in gateway_endpoints.items():
        print(f"{category:25} : {count:2d}")
    print("-" * 30)
    print(f"{'GATEWAY TOTAL':25} : {gateway_total:2d}")
    
    print()
    print("COMPLETE SYSTEM:")
    print("-" * 30)
    print(f"Gateway Service    : {gateway_total}")
    print(f"Agent Service      : {agent_endpoints}")
    print(f"LangGraph Service  : {langgraph_endpoints}")
    print(f"Portal Services    : {portal_endpoints} (web interfaces)")
    print("-" * 30)
    print(f"TOTAL ENDPOINTS    : {system_total}")
    print(f"TOTAL WITH PORTALS : {system_total + portal_endpoints}")
    
    return {
        "gateway": gateway_total,
        "agent": agent_endpoints,
        "langgraph": langgraph_endpoints,
        "portals": portal_endpoints,
        "total_endpoints": system_total,
        "total_with_portals": system_total + portal_endpoints
    }

if __name__ == "__main__":
    counts = main()
    print(f"\nFINAL COUNTS:")
    print(f"Gateway: {counts['gateway']} endpoints")
    print(f"Total System: {counts['total_endpoints']} endpoints")