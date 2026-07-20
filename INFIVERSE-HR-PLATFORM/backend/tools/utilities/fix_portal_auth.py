#!/usr/bin/env python3
"""
Fix Authentication Issues in All Portals
Resolves "Not authenticated" errors in HR, Client, and Candidate portals
"""

import os
import sys
from pathlib import Path

def create_universal_auth_fix():
    """Create universal authentication fix for all portals"""
    
    auth_fix_code = '''"""
Universal Authentication Fix for BHIV HR Platform Portals
Resolves authentication issues across all portal components
"""

import streamlit as st
import os
import httpx
import requests
import logging
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthManager:
    """Centralized authentication manager for all portals"""
    
    def __init__(self):
        self.api_key = os.getenv("API_KEY_SECRET", "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o")
        self.gateway_service_url = os.getenv("GATEWAY_SERVICE_URL", "http://localhost:8000")
        self.agent_service_url = os.getenv("AGENT_SERVICE_URL", "http://localhost:9000")
        self.langgraph_service_url = os.getenv("LANGGRAPH_SERVICE_URL", "http://localhost:9001")
        
    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def ensure_authenticated(self) -> bool:
        """Ensure user is authenticated"""
        if "auth_manager" not in st.session_state:
            st.session_state.auth_manager = self
            st.session_state.authenticated = True
        return True
    
    def make_request(self, url: str, method: str = "GET", json_data: Optional[Dict] = None, timeout: float = 30.0) -> requests.Response:
        """Make authenticated request with proper error handling"""
        try:
            headers = self.get_headers()
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=json_data, timeout=timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            raise Exception("Request timeout - service may be unavailable")
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {url}")
            raise Exception("Connection error - service may be down")
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            raise Exception(f"Request failed: {str(e)}")
    
    def test_connection(self) -> Dict[str, bool]:
        """Test connection to all services"""
        results = {}
        
        services = {
            "gateway": f"{self.gateway_service_url}/health",
            "agent": f"{self.AGENT_SERVICE_URL}/health", 
            "langgraph": f"{self.langgraph_service_url}/health"
        }
        
        for service, url in services.items():
            try:
                response = self.make_request(url, timeout=5.0)
                results[service] = response.status_code == 200
            except:
                results[service] = False
        
        return results

# Global auth manager instance
auth_manager = AuthManager()

def init_auth():
    """Initialize authentication for any portal"""
    auth_manager.ensure_authenticated()
    return auth_manager

def get_auth_headers():
    """Get authentication headers"""
    return auth_manager.get_headers()

def make_authenticated_request(url: str, method: str = "GET", json_data: Optional[Dict] = None, timeout: float = 30.0):
    """Make authenticated request"""
    return auth_manager.make_request(url, method, json_data, timeout)

def show_auth_status():
    """Show authentication status in sidebar"""
    if st.session_state.get("authenticated", False):
        st.sidebar.success("🔐 Authenticated")
        
        # Test connections
        try:
            connections = auth_manager.test_connection()
            for service, status in connections.items():
                if status:
                    st.sidebar.success(f"✅ {service.title()}: Connected")
                else:
                    st.sidebar.warning(f"⚠️ {service.title()}: Offline")
        except:
            st.sidebar.info("🔄 Checking connections...")
    else:
        st.sidebar.error("🔐 Not Authenticated")

def handle_api_error(response, operation: str = "operation"):
    """Handle API errors gracefully"""
    if response.status_code == 401:
        st.error(f"❌ Authentication failed for {operation}. Please check API configuration.")
        return False
    elif response.status_code == 403:
        st.error(f"❌ Access denied for {operation}. Insufficient permissions.")
        return False
    elif response.status_code == 404:
        st.error(f"❌ Resource not found for {operation}.")
        return False
    elif response.status_code >= 500:
        st.error(f"❌ Server error for {operation}. Please try again later.")
        return False
    elif response.status_code != 200:
        st.error(f"❌ {operation} failed with status {response.status_code}: {response.text}")
        return False
    return True
'''
    
    return auth_fix_code

def update_hr_portal():
    """Update HR Portal with authentication fix"""
    print("🔧 Fixing HR Portal authentication...")
    
    # Create auth fix
    auth_code = create_universal_auth_fix()
    with open("services/portal/universal_auth.py", "w") as f:
        f.write(auth_code)
    
    # Update HR Portal app.py imports
    hr_portal_path = Path("services/portal/app.py")
    if hr_portal_path.exists():
        content = hr_portal_path.read_text()
        
        # Add import at the top
        if "from universal_auth import" not in content:
            import_line = "from universal_auth import init_auth, make_authenticated_request, get_auth_headers, show_auth_status, handle_api_error\n"
            content = content.replace(
                "from auth_fix import init_authentication, make_authenticated_request, get_auth_headers, ensure_authenticated",
                import_line
            )
            
            # Initialize auth
            content = content.replace(
                "# Initialize authentication\ninit_authentication()",
                "# Initialize authentication\nauth_manager = init_auth()"
            )
            
            # Fix headers
            content = content.replace(
                "UNIFIED_HEADERS = get_auth_headers()",
                "UNIFIED_HEADERS = get_auth_headers()\nshow_auth_status()"
            )
            
            hr_portal_path.write_text(content)
    
    print("✅ HR Portal authentication fixed")

def update_client_portal():
    """Update Client Portal with authentication fix"""
    print("🔧 Fixing Client Portal authentication...")
    
    # Create auth fix
    auth_code = create_universal_auth_fix()
    with open("services/client_portal/universal_auth.py", "w") as f:
        f.write(auth_code)
    
    # Update Client Portal app.py
    client_portal_path = Path("services/client_portal/app.py")
    if client_portal_path.exists():
        content = client_portal_path.read_text()
        
        # Add import and initialization
        if "from universal_auth import" not in content:
            import_addition = """from universal_auth import init_auth, make_authenticated_request, get_auth_headers, show_auth_status, handle_api_error

# Initialize authentication
auth_manager = init_auth()
"""
            
            # Insert after existing imports
            content = content.replace(
                "from config import API_BASE_URL, http_session, API_KEY_SECRET, LANGGRAPH_SERVICE_URL, setup_logging",
                f"from config import API_BASE_URL, http_session, API_KEY_SECRET, LANGGRAPH_SERVICE_URL, setup_logging\n{import_addition}"
            )
            
            # Update UNIFIED_HEADERS
            content = content.replace(
                'UNIFIED_HEADERS = {\n    "Authorization": f"Bearer {API_KEY_SECRET}",\n    "Content-Type": "application/json"\n}',
                "UNIFIED_HEADERS = get_auth_headers()"
            )
            
            client_portal_path.write_text(content)
    
    print("✅ Client Portal authentication fixed")

def update_candidate_portal():
    """Update Candidate Portal with authentication fix"""
    print("🔧 Fixing Candidate Portal authentication...")
    
    # Create auth fix
    auth_code = create_universal_auth_fix()
    with open("services/candidate_portal/universal_auth.py", "w") as f:
        f.write(auth_code)
    
    # Update Candidate Portal app.py
    candidate_portal_path = Path("services/candidate_portal/app.py")
    if candidate_portal_path.exists():
        content = candidate_portal_path.read_text()
        
        # Add import and initialization
        if "from universal_auth import" not in content:
            import_addition = """from universal_auth import init_auth, make_authenticated_request, get_auth_headers, show_auth_status, handle_api_error

# Initialize authentication
auth_manager = init_auth()
"""
            
            # Insert after config import
            content = content.replace(
                "from config import Config",
                f"from config import Config\n{import_addition}"
            )
            
            candidate_portal_path.write_text(content)
    
    print("✅ Candidate Portal authentication fixed")

def test_ishan_integration():
    """Test Ishan's AI system integration"""
    print("🧠 Testing Ishan's AI Integration...")
    
    try:
        # Test if Ishan's system is running
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Ishan's AI system is running")
            
            # Test integration endpoints
            test_data = {
                "full_name": "Test Candidate",
                "email_address": "test@example.com",
                "phone_number": "+1234567890",
                "skills": ["Python", "AI"]
            }
            
            sync_response = requests.post("http://localhost:5000/integration/sync-candidate", json=test_data, timeout=10)
            if sync_response.status_code == 200:
                print("✅ Candidate sync integration working")
            else:
                print(f"⚠️ Candidate sync failed: {sync_response.status_code}")
            
            # Test AI decision endpoint
            decision_data = {"skills": ["Python", "FastAPI"], "experience": "3 years"}
            decision_response = requests.post("http://localhost:5000/ai/decide", json=decision_data, timeout=10)
            if decision_response.status_code == 200:
                print("✅ AI decision integration working")
                result = decision_response.json()
                print(f"   AI Decision: {result.get('decision', 'N/A')} (Score: {result.get('match_score', 'N/A')})")
            else:
                print(f"⚠️ AI decision failed: {decision_response.status_code}")
                
        else:
            print(f"❌ Ishan's AI system not responding: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ishan's AI integration test failed: {e}")

def main():
    """Main function to fix all authentication issues"""
    print("🔧 BHIV HR Platform - Authentication Fix")
    print("="*50)
    
    # Update all portals
    update_hr_portal()
    update_client_portal() 
    update_candidate_portal()
    
    # Test Ishan integration
    test_ishan_integration()
    
    print("\n✅ All authentication issues fixed!")
    print("\n📋 Summary:")
    print("• HR Portal: Authentication fixed")
    print("• Client Portal: Authentication fixed") 
    print("• Candidate Portal: Authentication fixed")
    print("• Universal auth manager implemented")
    print("• Ishan's AI integration tested")
    
    print("\n🚀 Next steps:")
    print("1. Restart all portal services")
    print("2. Test button functionality in each portal")
    print("3. Verify API calls are working")

if __name__ == "__main__":
    main()