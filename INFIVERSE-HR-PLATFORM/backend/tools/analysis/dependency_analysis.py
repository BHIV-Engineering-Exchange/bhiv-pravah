#!/usr/bin/env python3
"""
Dependency Analysis for Gateway Rectification
Checks if endpoints to be removed are used by other services
"""

import os
import re
from pathlib import Path

def analyze_dependencies():
    """Analyze dependencies before removing endpoints"""
    
    # Endpoints to be removed
    endpoints_to_remove = {
        "2fa_duplicates": [
            "/v1/2fa/setup",
            "/v1/2fa/verify-setup", 
            "/v1/2fa/login-with-2fa",
            "/v1/2fa/status/",
            "/v1/2fa/disable",
            "/v1/2fa/regenerate-backup-codes",
            "/v1/2fa/test-token/",
            "/v1/2fa/demo-setup"
        ],
        "password_duplicates": [
            "/v1/password/validate",
            "/v1/password/generate",
            "/v1/password/policy",
            "/v1/password/change",
            "/v1/password/strength-test",
            "/v1/password/security-tips"
        ],
        "csp_duplicates": [
            "/v1/csp/policies",
            "/v1/csp/violations",
            "/v1/csp/report",
            "/v1/csp/test"
        ]
    }
    
    # Services to check
    services_to_check = [
        "services/agent",
        "services/langgraph", 
        "services/portal",
        "services/client_portal",
        "services/candidate_portal",
        "services/database"
    ]
    
    print("DEPENDENCY ANALYSIS FOR GATEWAY RECTIFICATION")
    print("=" * 50)
    
    dependencies_found = {}
    
    for service_dir in services_to_check:
        service_path = Path(f"c:/BHIV HR PLATFORM/{service_dir}")
        if not service_path.exists():
            continue
            
        print(f"\nChecking {service_dir}...")
        service_dependencies = []
        
        # Check all Python files in service
        for py_file in service_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check for endpoint references
                    for category, endpoints in endpoints_to_remove.items():
                        for endpoint in endpoints:
                            # Look for URL references
                            patterns = [
                                rf'["\'].*{re.escape(endpoint)}.*["\']',
                                rf'url.*{re.escape(endpoint)}',
                                rf'endpoint.*{re.escape(endpoint)}',
                                rf'path.*{re.escape(endpoint)}'
                            ]
                            
                            for pattern in patterns:
                                if re.search(pattern, content, re.IGNORECASE):
                                    service_dependencies.append({
                                        "file": str(py_file),
                                        "endpoint": endpoint,
                                        "category": category
                                    })
                                    
            except Exception as e:
                print(f"  Error reading {py_file}: {e}")
                continue
        
        if service_dependencies:
            dependencies_found[service_dir] = service_dependencies
            print(f"  [WARNING] Found {len(service_dependencies)} dependencies")
        else:
            print(f"  [OK] No dependencies found")
    
    # Check documentation files
    print(f"\nChecking documentation files...")
    doc_dependencies = []
    docs_path = Path("c:/BHIV HR PLATFORM/docs")
    
    if docs_path.exists():
        for doc_file in docs_path.rglob("*.md"):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for category, endpoints in endpoints_to_remove.items():
                        for endpoint in endpoints:
                            if endpoint in content:
                                doc_dependencies.append({
                                    "file": str(doc_file),
                                    "endpoint": endpoint,
                                    "category": category
                                })
            except Exception as e:
                continue
    
    if doc_dependencies:
        dependencies_found["documentation"] = doc_dependencies
        print(f"  [WARNING] Found {len(doc_dependencies)} documentation references")
    else:
        print(f"  [OK] No documentation dependencies found")
    
    # Summary
    print(f"\n" + "=" * 50)
    print("DEPENDENCY ANALYSIS SUMMARY")
    print("=" * 50)
    
    if not dependencies_found:
        print("[OK] NO DEPENDENCIES FOUND")
        print("All endpoints can be safely removed")
        return True
    else:
        print(f"[WARNING] DEPENDENCIES FOUND IN {len(dependencies_found)} LOCATIONS")
        for service, deps in dependencies_found.items():
            print(f"\n{service.upper()}:")
            for dep in deps:
                print(f"  - {dep['endpoint']} in {dep['file']}")
        
        print(f"\nRECOMMENDATION:")
        print("Review dependencies before proceeding with rectification")
        return False

if __name__ == "__main__":
    safe_to_proceed = analyze_dependencies()
    print(f"\nSAFE TO PROCEED: {safe_to_proceed}")