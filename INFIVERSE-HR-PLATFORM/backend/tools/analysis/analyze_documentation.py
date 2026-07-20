#!/usr/bin/env python3
"""
Analyze all documentation files in BHIV HR PLATFORM for updates needed
"""

import os
import re
from datetime import datetime

def scan_documentation_files():
    """Scan all documentation files and categorize them"""
    
    doc_files = {
        'main_docs': [],
        'architecture': [],
        'api_docs': [],
        'deployment': [],
        'testing': [],
        'reports': [],
        'guides': [],
        'outdated': [],
        'needs_update': [],
        'can_delete': []
    }
    
    # Scan root directory
    for file in os.listdir('.'):
        if file.endswith('.md') and os.path.isfile(file):
            doc_files['main_docs'].append(file)
    
    # Scan docs directory
    if os.path.exists('docs'):
        for root, dirs, files in os.walk('docs'):
            for file in files:
                if file.endswith('.md'):
                    full_path = os.path.join(root, file)
                    category = categorize_doc_file(full_path)
                    doc_files[category].append(full_path)
    
    return doc_files

def categorize_doc_file(filepath):
    """Categorize documentation file based on path and content"""
    
    path_lower = filepath.lower()
    
    if 'architecture' in path_lower:
        return 'architecture'
    elif 'api' in path_lower:
        return 'api_docs'
    elif 'deployment' in path_lower:
        return 'deployment'
    elif 'testing' in path_lower or 'test' in path_lower:
        return 'testing'
    elif 'report' in path_lower:
        return 'reports'
    elif 'guide' in path_lower:
        return 'guides'
    else:
        return 'main_docs'

def analyze_file_content(filepath):
    """Analyze file content for outdated information"""
    
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for outdated version numbers
        if '4.1.0' in content or '4.0.0' in content:
            issues.append("Contains outdated version numbers")
        
        # Check for old endpoint counts
        if re.search(r'79 endpoints|82 endpoints|85 endpoints', content):
            issues.append("Contains outdated endpoint counts (should be 94)")
        
        # Check for missing LangGraph integration
        if 'langgraph' not in content.lower() and 'workflow' in content.lower():
            issues.append("Missing LangGraph integration information")
        
        # Check for old service counts
        if re.search(r'5 services|4 services', content):
            issues.append("Contains outdated service counts (should be 6)")
        
        # Check for old dates
        if re.search(r'2024|October 2025|September 2025', content):
            issues.append("Contains outdated dates")
        
        # Check for broken links or references
        if 'bhiv-hr-gateway-ltg0.onrender.com' not in content and 'render.com' in content:
            issues.append("May contain outdated deployment URLs")
        
    except Exception as e:
        issues.append(f"Error reading file: {e}")
    
    return issues

def main():
    print("BHIV HR PLATFORM - Documentation Analysis")
    print("=" * 60)
    
    doc_files = scan_documentation_files()
    
    print("\n📁 DOCUMENTATION INVENTORY")
    print("-" * 40)
    
    for category, files in doc_files.items():
        if files:
            print(f"\n{category.upper().replace('_', ' ')} ({len(files)} files):")
            for file in files[:5]:  # Show first 5
                print(f"  - {file}")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more")
    
    print(f"\n📊 TOTAL DOCUMENTATION FILES: {sum(len(files) for files in doc_files.values())}")
    
    # Analyze key files for issues
    print("\n🔍 ANALYZING KEY FILES FOR ISSUES")
    print("-" * 40)
    
    key_files = [
        'README.md',
        'docs/QUICK_START_GUIDE.md',
        'docs/CURRENT_FEATURES.md',
        'docs/architecture/PROJECT_STRUCTURE.md',
        'docs/architecture/DEPLOYMENT_STATUS.md'
    ]
    
    needs_update = []
    
    for file in key_files:
        if os.path.exists(file):
            issues = analyze_file_content(file)
            if issues:
                needs_update.append((file, issues))
                print(f"\n❌ {file}:")
                for issue in issues:
                    print(f"   - {issue}")
            else:
                print(f"\n✅ {file}: Up to date")
        else:
            print(f"\n⚠️  {file}: File not found")
    
    # Generate recommendations
    print("\n📋 DOCUMENTATION UPDATE RECOMMENDATIONS")
    print("=" * 60)
    
    print("\n🔄 FILES NEEDING UPDATES:")
    for file, issues in needs_update:
        print(f"  - {file} ({len(issues)} issues)")
    
    print(f"\n📈 PRIORITY UPDATES NEEDED:")
    print("  1. Update version numbers to 4.2.0")
    print("  2. Update endpoint counts to 94")
    print("  3. Add LangGraph integration documentation")
    print("  4. Update service counts to 6")
    print("  5. Update dates to November 2025")
    print("  6. Verify deployment URLs")
    
    return needs_update

if __name__ == "__main__":
    main()