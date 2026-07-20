#!/usr/bin/env python3
"""
Database URL Consistency Checker
"""

import os
import re

def check_database_urls():
    """Check database URLs across all services and config files"""
    
    files_to_check = {
        "HR Portal Config": "c:\\BHIV-HR-Platform\\services\\portal\\config.py",
        "Client Portal Config": "c:\\BHIV-HR-Platform\\services\\client_portal\\config.py", 
        "Candidate Portal Config": "c:\\BHIV-HR-Platform\\services\\candidate_portal\\config.py",
        "Gateway Dependencies": "c:\\BHIV-HR-Platform\\services\\gateway\\dependencies.py",
        "Render Config": "c:\\BHIV-HR-Platform\\config\\.env.render",
        "Production Config": "c:\\BHIV-HR-Platform\\config\\production.env",
        "Example Config": "c:\\BHIV-HR-Platform\\.env.example"
    }
    
    db_urls = {}
    
    for name, path in files_to_check.items():
        try:
            with open(path, 'r') as f:
                content = f.read()
            
            # Find database URLs
            patterns = [
                r'postgresql://[^"\'\\s]+',
                r'DATABASE_URL[=:]([^\\s\\n]+)',
                r'"postgresql://[^"]+',
                r"'postgresql://[^']+"
            ]
            
            found_urls = []
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[1] if len(match) > 1 else ""
                    if match and 'postgresql://' in match:
                        found_urls.append(match.strip('"\''))
            
            db_urls[name] = found_urls
            
        except Exception as e:
            db_urls[name] = [f"ERROR: {str(e)}"]
    
    # Print results
    print("Database URL Analysis:")
    print("=" * 50)
    
    all_urls = set()
    for name, urls in db_urls.items():
        print(f"\n{name}:")
        if urls:
            for url in urls:
                if not url.startswith("ERROR:"):
                    all_urls.add(url)
                print(f"  {url}")
        else:
            print("  No database URLs found")
    
    print(f"\nUnique Database URLs Found: {len(all_urls)}")
    print("=" * 50)
    
    for i, url in enumerate(all_urls, 1):
        print(f"{i}. {url}")
    
    # Check for consistency
    if len(all_urls) > 1:
        print(f"\nWARNING: {len(all_urls)} different database URLs found!")
        print("Services should use the same database URL for consistency.")
    else:
        print("\nOK: All services use consistent database URL")
    
    return all_urls

if __name__ == "__main__":
    check_database_urls()
