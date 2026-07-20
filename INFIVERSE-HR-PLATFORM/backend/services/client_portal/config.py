"""
BHIV HR Platform - Client Portal Configuration
Version: 4.3.0
Updated: January 16, 2026
Status: Production Ready - MongoDB Atlas

Configuration for Client Portal Streamlit application:
- API Gateway connection settings
- JWT authentication configuration
- HTTP session with retry strategy
- MongoDB Atlas database (via Gateway)
"""

import requests
import os
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path

# Load .env file for local development
if os.getenv("ENVIRONMENT", "development") == "development":
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ.setdefault(key, value)

# Version Information
__version__ = "4.3.0"
__updated__ = "2026-01-16"
__status__ = "Production Ready - MongoDB Atlas"

# Environment Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
PYTHON_VERSION = os.getenv("PYTHON_VERSION", "3.12.7")

# Service URLs - Required
GATEWAY_SERVICE_URL = os.getenv("GATEWAY_SERVICE_URL")
if not GATEWAY_SERVICE_URL:
    raise ValueError("GATEWAY_SERVICE_URL environment variable is required")

# Agent service URL (optional for client portal)
AGENT_SERVICE_URL = os.getenv("AGENT_SERVICE_URL", "http://localhost:9000")

# LangGraph service URL (required for automation)
LANGGRAPH_SERVICE_URL = os.getenv("LANGGRAPH_SERVICE_URL")
if not LANGGRAPH_SERVICE_URL:
    raise ValueError("LANGGRAPH_SERVICE_URL environment variable is required for automation")

# Authentication - Required
API_KEY_SECRET = os.getenv("API_KEY_SECRET")
if not API_KEY_SECRET:
    raise ValueError("API_KEY_SECRET environment variable is required")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is required")

# Candidate JWT Secret (optional for client portal)
CANDIDATE_JWT_SECRET_KEY = os.getenv("CANDIDATE_JWT_SECRET_KEY", "candidate_jwt_secret_key_2025")

# Database URL (optional for client portal - uses gateway for all DB operations)
# MongoDB Atlas connection - not used directly by client portal
DATABASE_URL = os.getenv("DATABASE_URL", "")

# API Configuration
API_BASE_URL = GATEWAY_SERVICE_URL
API_KEY = API_KEY_SECRET

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Configure session with retry strategy and timeouts
def create_session():
    session = requests.Session()
    
    # Retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    # Mount adapter with retry strategy
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=20
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(headers)
    
    # Set timeouts
    session.timeout = (15, 60)  # (connect, read)
    
    return session

# Global session
http_session = create_session()

# Logging Configuration
def setup_logging():
    """Setup logging based on environment configuration"""
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    if ENVIRONMENT == "production":
        logging.getLogger("streamlit").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)

# Client Portal Configuration
CLIENT_PORTAL_CONFIG = {
    "title": "BHIV HR Platform - Client Portal",
    "version": __version__,
    "authentication": "JWT Token-based",
    "features": [
        "Job Posting",
        "Candidate Review", 
        "Interview Scheduling",
        "Offer Management",
        "Real-time Sync with HR Portal"
    ],
    "status": __status__,
    "updated": __updated__,
    "gateway_url": API_BASE_URL
}
