#!/usr/bin/env python3
"""
Endpoint Counter for BHIV HR Platform Services
Analyzes code to count actual API endpoints
"""

import re
import os
from pathlib import Path

def count_endpoints_in_file(file_path: str) -> dict:
    """Count endpoints in a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Patterns for different HTTP methods
        patterns = {
            'GET': r'@app\.get\s*\(',
            'POST': r'@app\.post\s*\(',
            'PUT': r'@app\.put\s*\(',
            'DELETE': r'@app\.delete\s*\(',
            'PATCH': r'@app\.patch\s*\(',
            'WEBSOCKET': r'@app\.websocket\s*\('
        }
        
        counts = {}
        total = 0
        
        for method, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            count = len(matches)
            if count > 0:
                counts[method] = count
                total += count
        
        return {'methods': counts, 'total': total}
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {'methods': {}, 'total': 0}

def analyze_services():
    """Analyze all services and count endpoints"""
    services_dir = Path("c:/BHIV HR PLATFORM/services")
    
    results = {}
    
    # Gateway Service
    gateway_main = services_dir / "gateway" / "app" / "main.py"
    if gateway_main.exists():
        gateway_count = count_endpoints_in_file(str(gateway_main))
        results['gateway'] = {
            'file': str(gateway_main),
            'endpoints': gateway_count,
            'type': 'FastAPI'
        }
    
    # Agent Service  
    agent_app = services_dir / "agent" / "app.py"
    if agent_app.exists():
        agent_count = count_endpoints_in_file(str(agent_app))
        results['agent'] = {
            'file': str(agent_app),
            'endpoints': agent_count,
            'type': 'FastAPI'
        }
    
    # LangGraph Service
    langgraph_main = services_dir / "langgraph" / "app" / "main.py"
    if langgraph_main.exists():
        langgraph_count = count_endpoints_in_file(str(langgraph_main))
        results['langgraph'] = {
            'file': str(langgraph_main),
            'endpoints': langgraph_count,
            'type': 'FastAPI'
        }
    
    # Portal Services (Streamlit apps)
    portal_services = ['portal', 'client_portal', 'candidate_portal']
    for service in portal_services:
        app_file = services_dir / service / "app.py"
        if app_file.exists():
            results[service] = {
                'file': str(app_file),
                'endpoints': {'methods': {}, 'total': 1},  # Streamlit apps have 1 main endpoint
                'type': 'Streamlit'
            }
    
    return results

def print_results(results):
    """Print endpoint analysis results"""
    print("BHIV HR Platform - Endpoint Analysis")
    print("=" * 50)
    
    total_endpoints = 0
    
    for service_name, data in results.items():
        endpoints = data['endpoints']
        service_total = endpoints['total']
        total_endpoints += service_total
        
        print(f"\n{service_name.upper()} SERVICE ({data['type']})")
        print(f"   File: {data['file']}")
        print(f"   Total Endpoints: {service_total}")
        
        if endpoints['methods']:
            print("   Methods breakdown:")
            for method, count in endpoints['methods'].items():
                print(f"     {method}: {count}")
    
    print(f"\nTOTAL ENDPOINTS ACROSS ALL SERVICES: {total_endpoints}")
    
    # Compare with documented counts
    documented_counts = {
        'gateway': 94,
        'agent': 6, 
        'langgraph': 7,
        'portal': 1,
        'client_portal': 1,
        'candidate_portal': 1
    }
    
    documented_total = sum(documented_counts.values())
    
    print(f"\nCOMPARISON WITH DOCUMENTATION:")
    print(f"   Documented Total: {documented_total}")
    print(f"   Actual Total: {total_endpoints}")
    print(f"   Difference: {total_endpoints - documented_total}")
    
    print(f"\nSERVICE-BY-SERVICE COMPARISON:")
    for service_name, data in results.items():
        actual = data['endpoints']['total']
        documented = documented_counts.get(service_name, 0)
        diff = actual - documented
        status = "OK" if diff == 0 else "WARN" if abs(diff) <= 5 else "ERROR"
        print(f"   {status} {service_name}: {actual} actual vs {documented} documented (diff: {diff:+d})")

if __name__ == "__main__":
    results = analyze_services()
    print_results(results)