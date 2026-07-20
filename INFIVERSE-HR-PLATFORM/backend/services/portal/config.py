"""
BHIV HR Platform - HR Portal Configuration
Version: 4.3.0
Updated: January 16, 2026
Status: Production Ready - MongoDB Atlas

Configuration for HR Portal Streamlit application:
- API Gateway connection settings
- HTTP client with connection pooling
- Timeout and retry configurations
- MongoDB Atlas database (via Gateway)
- Production-ready defaults
"""

import httpx
import os
import logging
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

# Service URLs - Required
GATEWAY_SERVICE_URL = os.getenv("GATEWAY_SERVICE_URL")
if not GATEWAY_SERVICE_URL:
    raise ValueError("GATEWAY_SERVICE_URL environment variable is required")

# Agent service URL (optional for HR portal - uses gateway)
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

CANDIDATE_JWT_SECRET_KEY = os.getenv("CANDIDATE_JWT_SECRET_KEY")
if not CANDIDATE_JWT_SECRET_KEY:
    raise ValueError("CANDIDATE_JWT_SECRET_KEY environment variable is required")

# API Configuration
API_BASE = GATEWAY_SERVICE_URL
API_KEY = API_KEY_SECRET

# HTTP Client Configuration with proper timeouts
timeout_config = httpx.Timeout(
    connect=15.0,  # Connection timeout
    read=60.0,     # Read timeout for long operations
    write=30.0,    # Write timeout
    pool=10.0      # Pool timeout
)

limits = httpx.Limits(
    max_keepalive_connections=10,
    max_connections=20,
    keepalive_expiry=30.0
)

headers = {"Authorization": f"Bearer {API_KEY}"}

# Global HTTP client with connection pooling
http_client = httpx.Client(
    timeout=timeout_config,
    limits=limits,
    headers=headers,
    follow_redirects=True
)

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
        logging.getLogger("httpx").setLevel(logging.WARNING)

# Portal Configuration
PORTAL_CONFIG = {
    "title": "BHIV HR Platform - Dashboard",
    "version": __version__,
    "api_endpoints": 81,  # Gateway service endpoints
    "features": [
        "Candidate Management",
        "Job Posting", 
        "AI Matching",
        "Values Assessment",
        "Interview Scheduling",
        "Offer Management"
    ],
    "status": __status__,
    "updated": __updated__,
    "database_status": "Connected",
    "gateway_url": API_BASE
}
