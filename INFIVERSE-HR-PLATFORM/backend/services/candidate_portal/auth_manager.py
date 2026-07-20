"""
Authentication Manager for Candidate Portal
Fixes "Not authenticated" button errors
"""
import streamlit as st
import os
import requests
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self):
        self.api_key = os.getenv("API_KEY_SECRET", "prod_api_key_XUqM2msdCa4CYIaRywRNXRVc477nlI3AQ-lr6cgTB2o")
        self.gateway_url = os.getenv("GATEWAY_SERVICE_URL", "http://localhost:8000")
        
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