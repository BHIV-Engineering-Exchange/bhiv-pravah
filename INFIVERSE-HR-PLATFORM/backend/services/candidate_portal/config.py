import os
import logging
from typing import Optional
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

class Config:
    """Configuration for Candidate Portal"""
    
    def __init__(self):
        # Environment Configuration
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Gateway API Configuration - Required
        self.GATEWAY_SERVICE_URL = os.getenv("GATEWAY_SERVICE_URL")
        if not self.GATEWAY_SERVICE_URL:
            raise ValueError("GATEWAY_SERVICE_URL environment variable is required")
        
        # API Authentication - Required
        self.API_KEY_SECRET = os.getenv("API_KEY_SECRET")
        if not self.API_KEY_SECRET:
            raise ValueError("API_KEY_SECRET environment variable is required")
        
        # JWT Configuration for candidate authentication - Required
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        if not self.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY environment variable is required")
            
        self.CANDIDATE_JWT_SECRET_KEY = os.getenv("CANDIDATE_JWT_SECRET_KEY")
        if not self.CANDIDATE_JWT_SECRET_KEY:
            raise ValueError("CANDIDATE_JWT_SECRET_KEY environment variable is required")
        
        # Database Configuration - Optional (portal uses Gateway API, not direct DB)
        # MongoDB Atlas URI for reference, but portal doesn't connect directly
        self.DATABASE_URL = os.getenv("DATABASE_URL", "")
        
        # LangGraph Service URL (optional for candidate portal)
        self.LANGGRAPH_SERVICE_URL = os.getenv("LANGGRAPH_SERVICE_URL", "https://bhiv-hr-langgraph-luy9.onrender.com")
        
        # Portal Configuration
        self.PORTAL_PORT = int(os.getenv("CANDIDATE_PORTAL_PORT", "8503"))
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        
        # File Upload Configuration
        self.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
        self.ALLOWED_EXTENSIONS = ["pdf", "docx", "txt"]
        
        # Session Configuration
        self.SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging based on environment configuration"""
        log_level = getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        
        if self.ENVIRONMENT == "production":
            logging.getLogger("streamlit").setLevel(logging.WARNING)
            logging.getLogger("requests").setLevel(logging.WARNING)
        
    def get_headers(self, token: Optional[str] = None) -> dict:
        """Get API headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token or self.API_KEY_SECRET}"
        }
        return headers
