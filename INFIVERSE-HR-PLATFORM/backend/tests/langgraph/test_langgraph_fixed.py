#!/usr/bin/env python3
"""
Test LangGraph Service After Fixes
"""

import sys
import os

def test_dependencies():
    """Test dependencies import"""
    try:
        sys.path.append("services/langgraph")
        from dependencies import validate_api_key, get_api_key
        
        # Test API key validation
        result = validate_api_key("bhiv-hr-2024-secure-api-key-v2")
        print(f"API key validation: {'PASS' if result else 'FAIL'}")
        
        return True
    except Exception as e:
        print(f"Dependencies test: FAIL - {e}")
        return False

def test_config():
    """Test configuration"""
    try:
        sys.path.append("services/langgraph")
        from config import settings
        
        print(f"Environment: {settings.environment}")
        print(f"Port: {settings.langgraph_port}")
        print(f"API Key configured: {'YES' if settings.api_key_secret != 'your-api-key' else 'NO'}")
        
        return True
    except Exception as e:
        print(f"Config test: FAIL - {e}")
        return False

def test_files():
    """Test file structure"""
    required_files = [
        "services/langgraph/Dockerfile",
        "services/langgraph/requirements.txt",
        "services/langgraph/dependencies.py",
        "services/langgraph/config.py",
        "services/langgraph/app/main.py",
        "services/langgraph/render.yaml"
    ]
    
    all_exist = True
    for file_path in required_files:
        exists = os.path.exists(file_path)
        print(f"{file_path}: {'OK' if exists else 'MISSING'}")
        if not exists:
            all_exist = False
    
    return all_exist

def main():
    print("LangGraph Service Fix Verification")
    print("=" * 35)
    
    print("\n1. Testing file structure:")
    files_ok = test_files()
    
    print("\n2. Testing configuration:")
    config_ok = test_config()
    
    print("\n3. Testing dependencies:")
    deps_ok = test_dependencies()
    
    print(f"\nOverall Status: {'PASS' if all([files_ok, config_ok, deps_ok]) else 'FAIL'}")

if __name__ == "__main__":
    main()