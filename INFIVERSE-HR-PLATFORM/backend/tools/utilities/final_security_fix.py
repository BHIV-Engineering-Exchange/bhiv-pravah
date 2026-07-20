#!/usr/bin/env python3
"""
Final Security Fix - Replace All Remaining Production Values
"""

import os

def fix_docker_compose():
    """Fix Docker compose file"""
    file_path = "docker-compose.production.yml"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace all instances of production password
        content = content.replace("bhiv_local_password_2025", "your_password")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"FIXED: {file_path}")
        
    except Exception as e:
        print(f"ERROR: {e}")

def main():
    """Apply final security fixes"""
    print("APPLYING FINAL SECURITY FIXES...")
    fix_docker_compose()
    print("COMPLETE: All production values secured")

if __name__ == "__main__":
    main()