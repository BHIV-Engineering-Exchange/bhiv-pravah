#!/usr/bin/env python3
"""
Find Exposed Production Keys for Git Security
"""

import os
import re

def scan_file_for_keys(file_path):
    """Scan file for exposed production keys"""
    exposed_keys = []
    
    # Production key patterns
    patterns = {
        "API_KEY": r"prod_api_key_[A-Za-z0-9\-_]+",
        "JWT_SECRET": r"prod_jwt_[A-Za-z0-9\-_]+", 
        "TWILIO_SID": r"AC[a-f0-9]{32}",
        "TWILIO_TOKEN": r"[a-f0-9]{32}",
        "GMAIL_PASSWORD": r"[a-z]{4}\s[a-z]{4}\s[a-z]{4}\s[a-z]{4}",
        "TELEGRAM_TOKEN": r"\d+:[A-Za-z0-9\-_]+",
        "GEMINI_KEY": r"AIza[A-Za-z0-9\-_]+",
        "DATABASE_URL": r"postgresql://[^@]+@[^/]+/[^\"'\s]+"
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for key_type, pattern in patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                exposed_keys.append({
                    "file": file_path,
                    "type": key_type,
                    "matches": matches
                })
                
    except Exception as e:
        pass
        
    return exposed_keys

def main():
    """Scan project for exposed keys"""
    
    # Files to scan
    files_to_scan = [
        ".env",
        "services/langgraph/config.py",
        "services/langgraph/dependencies.py", 
        "docker-compose.production.yml",
        "config/.env.render",
        "config/production.env"
    ]
    
    print("SCANNING FOR EXPOSED PRODUCTION KEYS\n")
    
    all_exposed = []
    
    for file_path in files_to_scan:
        if os.path.exists(file_path):
            exposed = scan_file_for_keys(file_path)
            if exposed:
                all_exposed.extend(exposed)
                print(f"EXPOSED KEYS FOUND: {file_path}")
                for item in exposed:
                    print(f"   {item['type']}: {len(item['matches'])} matches")
            else:
                print(f"SECURE: {file_path}")
        else:
            print(f"NOT FOUND: {file_path}")
    
    print(f"\nSUMMARY:")
    print(f"Total files with exposed keys: {len(set([item['file'] for item in all_exposed]))}")
    print(f"Total exposed credentials: {sum([len(item['matches']) for item in all_exposed])}")
    
    if all_exposed:
        print(f"\nSECURITY RISK: Production keys are exposed in code!")
        print(f"These files need to be secured before Git push:")
        for item in all_exposed:
            print(f"  - {item['file']} ({item['type']})")
    else:
        print(f"\nSECURE: No exposed production keys found")

if __name__ == "__main__":
    main()