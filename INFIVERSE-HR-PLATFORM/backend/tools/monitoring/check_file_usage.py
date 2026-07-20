#!/usr/bin/env python3
"""
Check if auth_service.py and semantic_engine/ files are actually used in the codebase
"""

import os
import re

def check_file_usage():
    print("BHIV HR Platform - File Usage Analysis")
    print("=" * 50)
    
    # Files to check
    files_to_check = [
        "services/client_portal/auth_service.py",
        "services/semantic_engine/",
        "services/gateway/semantic_engine/",
        "services/agent/semantic_engine/"
    ]
    
    # Source files to search in
    source_files = []
    for root, dirs, files in os.walk("services"):
        for file in files:
            if file.endswith(('.py', '.txt', '.yml', '.yaml')):
                source_files.append(os.path.join(root, file))
    
    print(f"Scanning {len(source_files)} source files...")
    print()
    
    # Check each file
    for file_to_check in files_to_check:
        print(f"Checking usage of: {file_to_check}")
        print("-" * 40)
        
        # Extract filename/module name for searching
        if file_to_check.endswith('/'):
            search_terms = [
                os.path.basename(file_to_check.rstrip('/')),
                file_to_check.replace('/', '.').rstrip('.')
            ]
        else:
            search_terms = [
                os.path.basename(file_to_check).replace('.py', ''),
                file_to_check.replace('/', '.').replace('.py', '')
            ]
        
        found_usage = False
        
        for source_file in source_files:
            # Skip the file itself
            if file_to_check in source_file:
                continue
                
            try:
                with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    for term in search_terms:
                        # Look for imports and references
                        patterns = [
                            rf'from\s+{re.escape(term)}',
                            rf'import\s+{re.escape(term)}',
                            rf'from\s+.*{re.escape(term)}',
                            rf'{re.escape(term)}\.',
                            rf'"{re.escape(term)}"',
                            rf"'{re.escape(term)}'"
                        ]
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                print(f"  ✓ Found in {source_file}: {matches[0]}")
                                found_usage = True
                                break
                        
                        if found_usage:
                            break
                    
                    if found_usage:
                        break
                        
            except Exception as e:
                continue
        
        if not found_usage:
            print(f"  ❌ NO USAGE FOUND - File appears to be unused")
        
        print()
    
    # Check specific imports in key files
    print("Detailed Import Analysis")
    print("-" * 40)
    
    key_files = [
        "services/client_portal/app.py",
        "services/gateway/app/main.py", 
        "services/agent/app.py"
    ]
    
    for key_file in key_files:
        if os.path.exists(key_file):
            print(f"\nImports in {key_file}:")
            try:
                with open(key_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines[:30], 1):  # Check first 30 lines
                    if 'import' in line and ('auth_service' in line or 'semantic_engine' in line):
                        print(f"  Line {i}: {line.strip()}")
                        
            except Exception as e:
                print(f"  Error reading file: {e}")
    
    print("\n" + "=" * 50)
    print("ANALYSIS COMPLETE")

if __name__ == "__main__":
    check_file_usage()
