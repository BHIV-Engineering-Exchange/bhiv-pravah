"""
Insight Core Client - JWT Security Bridge
Provides secure communication with Bucket using JWT tokens and replay protection
"""
import jwt
import time
import uuid
import requests
import asyncio
from typing import Dict, Optional
from datetime import datetime, timezone
from utils.logger import get_logger

logger = get_logger(__name__)

class InsightClient:
    def __init__(self, insight_url: str = "http://localhost:8005", secret_key: str = "demo-secret"):
        self.insight_url = insight_url
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.timeout = 2
        
    def generate_token(self, user_id: str = "bhiv_core", ttl: int = 300) -> str:
        """Generate JWT token with expiry"""
        payload = {
            "sub": user_id,
            "iat": int(time.time()),
            "exp": int(time.time()) + ttl
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def generate_nonce(self) -> str:
        """Generate unique nonce for replay protection"""
        return f"{uuid.uuid4()}-{int(time.time())}"
    
    async def validate_request(self, payload: Dict) -> Dict:
        """Validate request through Insight Core before sending to Bucket"""
        try:
            token = self.generate_token()
            nonce = self.generate_nonce()
            
            request_data = {
                "token": token,
                "nonce": nonce,
                "payload": payload
            }
            
            response = requests.post(
                f"{self.insight_url}/ingest",
                json=request_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Insight validation: {result['decision']}")
                return {"validated": True, "decision": result}
            else:
                result = response.json()
                logger.warning(f"Insight rejected: {result['reason']}")
                return {"validated": False, "decision": result}
                
        except Exception as e:
            logger.debug(f"Insight validation failed (non-blocking): {e}")
            return {"validated": False, "error": str(e)}
    
    async def health_check(self) -> bool:
        """Check if Insight Core is available"""
        try:
            response = requests.get(f"{self.insight_url}/health", timeout=self.timeout)
            return response.status_code == 200
        except Exception:
            return False

# Global instance
insight_client = InsightClient()
