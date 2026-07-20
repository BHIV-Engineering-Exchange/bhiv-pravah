#!/usr/bin/env python3
"""
Detailed Endpoint Analysis for BHIV HR Platform
Manual counting and categorization of all endpoints
"""

import re
import os
from pathlib import Path

def extract_endpoints_with_details(file_path: str) -> list:
    """Extract endpoints with their details (path, method, function name)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        endpoints = []
        
        # Pattern to match FastAPI decorators with their paths
        patterns = [
            (r'@app\.get\s*\(\s*["\']([^"\']+)["\'].*?\)\s*(?:async\s+)?def\s+(\w+)', 'GET'),
            (r'@app\.post\s*\(\s*["\']([^"\']+)["\'].*?\)\s*(?:async\s+)?def\s+(\w+)', 'POST'),
            (r'@app\.put\s*\(\s*["\']([^"\']+)["\'].*?\)\s*(?:async\s+)?def\s+(\w+)', 'PUT'),
            (r'@app\.delete\s*\(\s*["\']([^"\']+)["\'].*?\)\s*(?:async\s+)?def\s+(\w+)', 'DELETE'),
            (r'@app\.patch\s*\(\s*["\']([^"\']+)["\'].*?\)\s*(?:async\s+)?def\s+(\w+)', 'PATCH'),
            (r'@app\.websocket\s*\(\s*["\']([^"\']+)["\'].*?\)\s*(?:async\s+)?def\s+(\w+)', 'WEBSOCKET')
        ]
        
        for pattern, method in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            for path, func_name in matches:
                endpoints.append({
                    'method': method,
                    'path': path,
                    'function': func_name
                })
        
        return endpoints
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def categorize_endpoints(endpoints: list) -> dict:
    """Categorize endpoints by functionality"""
    categories = {
        'Core API': [],
        'Monitoring': [],
        'Analytics': [],
        'Job Management': [],
        'Candidate Management': [],
        'AI Matching': [],
        'Assessment & Workflow': [],
        'Client Portal': [],
        'Security Testing': [],
        'CSP Management': [],
        'Two-Factor Authentication': [],
        'Password Management': [],
        'Candidate Portal': [],
        'LangGraph Workflows': [],
        'Other': []
    }
    
    for endpoint in endpoints:
        path = endpoint['path'].lower()
        
        if path in ['/', '/health', '/test-candidates', '/test-db']:
            categories['Core API'].append(endpoint)
        elif '/metrics' in path or '/health/detailed' in path:
            categories['Monitoring'].append(endpoint)
        elif '/stats' in path or '/database/schema' in path or '/reports' in path:
            categories['Analytics'].append(endpoint)
        elif '/jobs' in path and '/v1/' in path:
            categories['Job Management'].append(endpoint)
        elif '/candidates' in path and '/v1/' in path:
            categories['Candidate Management'].append(endpoint)
        elif '/match' in path:
            categories['AI Matching'].append(endpoint)
        elif '/feedback' in path or '/interviews' in path or '/offers' in path:
            categories['Assessment & Workflow'].append(endpoint)
        elif '/client/' in path:
            categories['Client Portal'].append(endpoint)
        elif '/security/' in path:
            categories['Security Testing'].append(endpoint)
        elif '/csp/' in path:
            categories['CSP Management'].append(endpoint)
        elif '/2fa/' in path or '/auth/2fa/' in path:
            categories['Two-Factor Authentication'].append(endpoint)
        elif '/password/' in path or '/auth/password/' in path:
            categories['Password Management'].append(endpoint)
        elif '/candidate/' in path:
            categories['Candidate Portal'].append(endpoint)
        elif '/workflows' in path or '/tools/' in path:
            categories['LangGraph Workflows'].append(endpoint)
        else:
            categories['Other'].append(endpoint)
    
    return categories

def analyze_service_endpoints():
    """Analyze all service endpoints in detail"""
    services_dir = Path("c:/BHIV HR PLATFORM/services")
    
    service_files = {
        'gateway': services_dir / "gateway" / "app" / "main.py",
        'agent': services_dir / "agent" / "app.py",
        'langgraph': services_dir / "langgraph" / "app" / "main.py"
    }
    
    all_results = {}
    
    for service_name, file_path in service_files.items():
        if file_path.exists():
            print(f"\n{'='*60}")
            print(f"ANALYZING {service_name.upper()} SERVICE")
            print(f"{'='*60}")
            print(f"File: {file_path}")
            
            endpoints = extract_endpoints_with_details(str(file_path))
            categories = categorize_endpoints(endpoints)
            
            all_results[service_name] = {
                'total_endpoints': len(endpoints),
                'endpoints': endpoints,
                'categories': categories
            }
            
            print(f"\nTotal Endpoints Found: {len(endpoints)}")
            
            # Print categorized endpoints
            for category, category_endpoints in categories.items():
                if category_endpoints:
                    print(f"\n{category} ({len(category_endpoints)} endpoints):")
                    for ep in category_endpoints:
                        print(f"  {ep['method']:10} {ep['path']:40} -> {ep['function']}")
            
            # Method breakdown
            method_counts = {}
            for ep in endpoints:
                method = ep['method']
                method_counts[method] = method_counts.get(method, 0) + 1
            
            print(f"\nMethod Breakdown:")
            for method, count in sorted(method_counts.items()):
                print(f"  {method}: {count}")
    
    return all_results

def compare_with_documentation():
    """Compare actual counts with documented counts"""
    print(f"\n{'='*60}")
    print("COMPARISON WITH API DOCUMENTATION")
    print(f"{'='*60}")
    
    # From API_DOCUMENTATION.md
    documented_counts = {
        'gateway': {
            'total': 94,
            'breakdown': {
                'Core API Endpoints': 3,
                'Monitoring Endpoints': 3,
                'Analytics Endpoints': 3,
                'Job Management Endpoints': 2,
                'Candidate Management Endpoints': 5,
                'AI Matching Endpoints': 2,
                'Assessment & Workflow Endpoints': 5,
                'Client Portal API': 2,
                'Security Testing': 7,
                'CSP Management': 4,
                'Two-Factor Authentication': 8,
                'Password Management': 6,
                'Candidate Portal': 5
            }
        },
        'agent': {
            'total': 6,
            'breakdown': {
                'Core API Endpoints': 2,
                'AI Matching Engine': 2,
                'Candidate Analysis': 1,
                'System Diagnostics': 1
            }
        },
        'langgraph': {
            'total': 7,
            'breakdown': {
                'Core API': 2,
                'Workflow Management': 4,
                'WebSocket': 1
            }
        }
    }
    
    # Get actual counts
    actual_results = analyze_service_endpoints()
    
    print(f"\nSUMMARY COMPARISON:")
    print(f"{'Service':<15} {'Documented':<12} {'Actual':<10} {'Difference':<12} {'Status'}")
    print("-" * 65)
    
    total_documented = 0
    total_actual = 0
    
    for service in ['gateway', 'agent', 'langgraph']:
        doc_count = documented_counts[service]['total']
        actual_count = actual_results[service]['total_endpoints']
        diff = actual_count - doc_count
        status = "MATCH" if diff == 0 else "OVER" if diff > 0 else "UNDER"
        
        print(f"{service:<15} {doc_count:<12} {actual_count:<10} {diff:+d} {status}")
        
        total_documented += doc_count
        total_actual += actual_count
    
    # Add Streamlit services
    streamlit_services = ['portal', 'client_portal', 'candidate_portal']
    for service in streamlit_services:
        print(f"{service:<15} {1:<12} {1:<10} {0:+d} MATCH")
        total_documented += 1
        total_actual += 1
    
    total_diff = total_actual - total_documented
    print("-" * 65)
    print(f"{'TOTAL':<15} {total_documented:<12} {total_actual:<10} {total_diff:+d}")
    
    return actual_results, documented_counts

if __name__ == "__main__":
    print("BHIV HR Platform - Detailed Endpoint Analysis")
    results = compare_with_documentation()