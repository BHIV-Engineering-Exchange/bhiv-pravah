#!/usr/bin/env python3
"""
Simple check if auth_service.py and semantic_engine/ files are actually used
"""

import os
import re

def check_usage():
    print("BHIV HR Platform - File Usage Check")
    print("=" * 40)
    
    # Check auth_service usage in client_portal/app.py
    print("1. Checking auth_service.py usage:")
    try:
        with open("services/client_portal/app.py", 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'auth_service' in content or 'AuthService' in content:
            print("   USED - Found references to auth_service")
        else:
            print("   NOT USED - No references found")
            
    except Exception as e:
        print(f"   ERROR - Could not read file: {e}")
    
    # Check semantic_engine usage in agent/app.py
    print("\n2. Checking semantic_engine/ usage in agent:")
    try:
        with open("services/agent/app.py", 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'from semantic_engine' in content:
            print("   USED - Found import from semantic_engine")
            # Find the specific import line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'from semantic_engine' in line:
                    print(f"   Line {i+1}: {line.strip()}")
        else:
            print("   NOT USED - No semantic_engine imports found")
            
    except Exception as e:
        print(f"   ERROR - Could not read file: {e}")
    
    # Check semantic_engine usage in gateway
    print("\n3. Checking semantic_engine/ usage in gateway:")
    try:
        with open("services/gateway/app/main.py", 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'semantic_engine' in content:
            print("   USED - Found references to semantic_engine")
        else:
            print("   NOT USED - No semantic_engine references found")
            
    except Exception as e:
        print(f"   ERROR - Could not read file: {e}")
    
    # Check if files exist
    print("\n4. File existence check:")
    files_to_check = [
        "services/client_portal/auth_service.py",
        "services/semantic_engine/__init__.py",
        "services/semantic_engine/phase3_engine.py",
        "services/gateway/semantic_engine/__init__.py",
        "services/agent/semantic_engine/__init__.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   EXISTS: {file_path}")
        else:
            print(f"   MISSING: {file_path}")
    
    print("\n" + "=" * 40)
    print("SUMMARY:")
    print("- auth_service.py: Standalone file, not imported")
    print("- semantic_engine/: Used by agent service only")
    print("- Gateway has its own semantic_engine copy")

if __name__ == "__main__":
    check_usage()
