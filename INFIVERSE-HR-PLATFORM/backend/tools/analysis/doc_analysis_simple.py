#!/usr/bin/env python3
"""
Simple documentation analysis for BHIV HR PLATFORM
"""

import os
import re

def find_all_docs():
    """Find all documentation files"""
    docs = []
    
    # Root level MD files
    for file in os.listdir('.'):
        if file.endswith('.md') and os.path.isfile(file):
            docs.append(file)
    
    # Docs directory
    if os.path.exists('docs'):
        for root, dirs, files in os.walk('docs'):
            for file in files:
                if file.endswith('.md'):
                    docs.append(os.path.join(root, file))
    
    return sorted(docs)

def analyze_content(filepath):
    """Check for outdated content"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Version checks
        if '4.1.0' in content or '4.0.0' in content:
            issues.append("Outdated version numbers")
        
        # Endpoint count checks
        if re.search(r'79 endpoints|82 endpoints|85 endpoints', content):
            issues.append("Outdated endpoint counts (should be 94)")
        
        # Service count checks  
        if re.search(r'5 services|4 services', content):
            issues.append("Outdated service counts (should be 6)")
        
        # LangGraph integration
        if 'workflow' in content.lower() and 'langgraph' not in content.lower():
            issues.append("Missing LangGraph integration info")
        
        # Date checks
        if '2024' in content or 'October 2025' in content:
            issues.append("Contains old dates")
            
    except Exception as e:
        issues.append(f"Read error: {str(e)[:50]}")
    
    return issues

def main():
    print("BHIV HR PLATFORM - Documentation Analysis")
    print("=" * 50)
    
    docs = find_all_docs()
    print(f"\nFound {len(docs)} documentation files")
    
    # Categorize files
    categories = {
        'root': [],
        'architecture': [],
        'api': [],
        'deployment': [],
        'testing': [],
        'reports': [],
        'guides': [],
        'other': []
    }
    
    for doc in docs:
        if not doc.startswith('docs/'):
            categories['root'].append(doc)
        elif 'architecture' in doc:
            categories['architecture'].append(doc)
        elif 'api' in doc.lower():
            categories['api'].append(doc)
        elif 'deployment' in doc:
            categories['deployment'].append(doc)
        elif 'test' in doc.lower():
            categories['testing'].append(doc)
        elif 'report' in doc.lower():
            categories['reports'].append(doc)
        elif 'guide' in doc.lower():
            categories['guides'].append(doc)
        else:
            categories['other'].append(doc)
    
    print("\nDOCUMENTATION CATEGORIES:")
    for category, files in categories.items():
        if files:
            print(f"\n{category.upper()} ({len(files)} files):")
            for file in files:
                print(f"  - {file}")
    
    # Analyze key files
    key_files = [
        'README.md',
        'docs/QUICK_START_GUIDE.md', 
        'docs/CURRENT_FEATURES.md',
        'docs/architecture/PROJECT_STRUCTURE.md',
        'docs/architecture/DEPLOYMENT_STATUS.md'
    ]
    
    print("\nKEY FILES ANALYSIS:")
    needs_update = []
    
    for file in key_files:
        if os.path.exists(file):
            issues = analyze_content(file)
            if issues:
                needs_update.append((file, issues))
                print(f"\n{file} - NEEDS UPDATE:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print(f"\n{file} - OK")
        else:
            print(f"\n{file} - NOT FOUND")
    
    print(f"\nSUMMARY:")
    print(f"Total docs: {len(docs)}")
    print(f"Need updates: {len(needs_update)}")
    
    print(f"\nPRIORITY UPDATES:")
    print("1. Update version to 4.2.0")
    print("2. Update endpoint count to 94") 
    print("3. Add LangGraph integration")
    print("4. Update service count to 6")
    print("5. Update dates to November 2025")

if __name__ == "__main__":
    main()