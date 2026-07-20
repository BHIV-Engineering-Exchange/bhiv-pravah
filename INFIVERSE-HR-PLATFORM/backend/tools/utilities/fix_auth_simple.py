#!/usr/bin/env python3
"""
Simple Authentication Fix for BHIV HR Platform Portals
"""

import os
import sys
from pathlib import Path

def create_auth_fix():
    """Create authentication fix code"""
    return '''"""
Authentication Fix for BHIV HR Platform
"""
import streamlit as st
import os
import requests
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self):
        self.api_key = os.getenv("API_KEY_SECRET", "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o")
        self.gateway_service_url = os.getenv("GATEWAY_SERVICE_URL", "http://localhost:8000")
        
    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def make_request(self, url, method="GET", json_data=None, timeout=30.0):
        try:
            headers = self.get_headers()
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            return response
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise

auth_manager = AuthManager()

def get_auth_headers():
    return auth_manager.get_headers()

def make_authenticated_request(url, method="GET", json_data=None, timeout=30.0):
    return auth_manager.make_request(url, method, json_data, timeout)

def init_auth():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = True
    return auth_manager
'''

def fix_hr_portal():
    """Fix HR Portal authentication"""
    print("Fixing HR Portal...")
    
    # Create auth file
    with open("services/portal/auth_manager.py", "w") as f:
        f.write(create_auth_fix())
    
    # Update app.py
    app_path = Path("services/portal/app.py")
    if app_path.exists():
        content = app_path.read_text()
        
        # Add import
        if "from auth_manager import" not in content:
            content = content.replace(
                "from auth_fix import init_authentication, make_authenticated_request, get_auth_headers, ensure_authenticated",
                "from auth_manager import init_auth, make_authenticated_request, get_auth_headers"
            )
            
            content = content.replace(
                "# Initialize authentication\ninit_authentication()",
                "# Initialize authentication\nauth_manager = init_auth()"
            )
            
            app_path.write_text(content)
    
    print("HR Portal fixed")

def fix_client_portal():
    """Fix Client Portal authentication"""
    print("Fixing Client Portal...")
    
    # Create auth file
    with open("services/client_portal/auth_manager.py", "w") as f:
        f.write(create_auth_fix())
    
    # Update app.py
    app_path = Path("services/client_portal/app.py")
    if app_path.exists():
        content = app_path.read_text()
        
        # Add import after config import
        if "from auth_manager import" not in content:
            content = content.replace(
                "from config import API_BASE_URL, http_session, API_KEY_SECRET, LANGGRAPH_SERVICE_URL, setup_logging",
                "from config import API_BASE_URL, http_session, API_KEY_SECRET, LANGGRAPH_SERVICE_URL, setup_logging\nfrom auth_manager import init_auth, get_auth_headers"
            )
            
            # Update headers
            content = content.replace(
                'UNIFIED_HEADERS = {\n    "Authorization": f"Bearer {API_KEY_SECRET}",\n    "Content-Type": "application/json"\n}',
                "UNIFIED_HEADERS = get_auth_headers()\nauth_manager = init_auth()"
            )
            
            app_path.write_text(content)
    
    print("Client Portal fixed")

def fix_candidate_portal():
    """Fix Candidate Portal authentication"""
    print("Fixing Candidate Portal...")
    
    # Create auth file
    with open("services/candidate_portal/auth_manager.py", "w") as f:
        f.write(create_auth_fix())
    
    # Update app.py
    app_path = Path("services/candidate_portal/app.py")
    if app_path.exists():
        content = app_path.read_text()
        
        # Add import
        if "from auth_manager import" not in content:
            content = content.replace(
                "from config import Config",
                "from config import Config\nfrom auth_manager import init_auth, get_auth_headers"
            )
            
            # Add initialization in main function
            content = content.replace(
                "config = Config()",
                "config = Config()\nauth_manager = init_auth()"
            )
            
            app_path.write_text(content)
    
    print("Candidate Portal fixed")

def test_ishan_integration():
    """Test Ishan's AI integration"""
    print("Testing Ishan AI integration...")
    
    try:
        import requests
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("Ishan AI system is running")
            
            # Test sync endpoint
            test_data = {
                "full_name": "Test User",
                "email_address": "test@example.com",
                "skills": ["Python"]
            }
            
            sync_response = requests.post("http://localhost:5000/integration/sync-candidate", json=test_data, timeout=10)
            print(f"Sync test: {sync_response.status_code}")
            
        else:
            print(f"Ishan AI not responding: {response.status_code}")
            
    except Exception as e:
        print(f"Ishan AI test failed: {e}")

def main():
    print("BHIV HR Platform - Authentication Fix")
    print("=" * 40)
    
    fix_hr_portal()
    fix_client_portal()
    fix_candidate_portal()
    test_ishan_integration()
    
    print("\nAuthentication fixes applied!")
    print("Restart portal services to apply changes.")

if __name__ == "__main__":
    main()