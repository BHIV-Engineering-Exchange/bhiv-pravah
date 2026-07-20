import requests
from typing import Dict, Any, Optional
import logging
import time
import os
from src.utils.hmac_signer import sign_payload, generate_jwt


class VideoBridgeClient:
    """Client for text-to-video service integration"""
    
    def __init__(self, base_url: Optional[str] = None):
        # Default to TTV_TTG_SERVICE_URL, fall back to VIDEO_SERVICE_URL, and then default to port 3000
        self.base_url = base_url or os.getenv(
            "TTV_TTG_SERVICE_URL",
            os.getenv("VIDEO_SERVICE_URL", "http://localhost:3000")
        )
        self.logger = logging.getLogger(__name__)
        self.timeout = int(os.getenv("VIDEO_SERVICE_TIMEOUT", "300"))
        self.max_retries = 3
    
    def generate_video(self, text: str, **kwargs) -> Dict[str, Any]:
        """Generate video from text"""
        start_time = time.time()
        try:
            if not text or not text.strip():
                self.logger.warning("Video generation failed - empty text",
                                  extra={"dependency": "video_service", "endpoint": "/generate-video",
                                         "error_type": "schema", "error": "Text cannot be empty"})
                return {
                    "success": False,
                    "error_type": "schema",
                    "error_message": "Text cannot be empty",
                    "endpoint": "/generate-video",
                    "fallback_used": False
                }
            
            payload = {
                "text": text,
                "topic": kwargs.get("topic", "general"),
                "style": kwargs.get("style", "default"),
                "duration": kwargs.get("duration", 30),
                "language": kwargs.get("language", "en")
            }
            
            self.logger.info(f"Starting video generation",
                           extra={"dependency": "video_service", "endpoint": "/generate-video",
                                  "text_length": len(text), "topic": payload["topic"]})
            
            response = requests.post(
                f"{self.base_url}/generate-video",
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            result = response.json()
            latency = round((time.time() - start_time) * 1000, 2)
            
            self.logger.info(f"Video generation successful",
                           extra={"dependency": "video_service", "endpoint": "/generate-video",
                                  "latency_ms": latency, "status_code": response.status_code,
                                  "generation_id": result.get('generation_id')})
            return result
            
        except requests.exceptions.Timeout:
            latency = round((time.time() - start_time) * 1000, 2)
            self.logger.error("Video generation failed - timeout",
                            extra={"dependency": "video_service", "endpoint": "/generate-video",
                                   "latency_ms": latency, "error_type": "network", "timeout_seconds": self.timeout})
            return {
                "success": False,
                "error_type": "network",
                "error_message": "Video service timeout",
                "endpoint": "/generate-video",
                "fallback_used": True
            }
        except requests.exceptions.ConnectionError:
            latency = round((time.time() - start_time) * 1000, 2)
            self.logger.error("Video generation failed - connection error",
                            extra={"dependency": "video_service", "endpoint": "/generate-video",
                                   "latency_ms": latency, "error_type": "network"})
            return {
                "success": False,
                "error_type": "network",
                "error_message": "Cannot connect to video service",
                "endpoint": "/generate-video",
                "fallback_used": True
            }
        except Exception as e:
            latency = round((time.time() - start_time) * 1000, 2)
            self.logger.error(f"Video generation failed - unexpected error: {str(e)}",
                            extra={"dependency": "video_service", "endpoint": "/generate-video",
                                   "latency_ms": latency, "error_type": "unexpected", "error": str(e)})
            return {
                "success": False,
                "error_type": "unexpected",
                "error_message": str(e),
                "endpoint": "/generate-video",
                "fallback_used": True
            }
    
    def get_video_status(self, generation_id: str) -> Dict[str, Any]:
        """Get video generation status (REST polling on Node.js /core/execution/:id or legacy /status/:id)"""
        start_time = time.time()
        try:
            if not generation_id:
                self.logger.warning("Video status check failed - missing generation_id",
                                  extra={"dependency": "video_service", "endpoint": "/status/{generation_id}",
                                         "error_type": "schema"})
                return {
                    "success": False,
                    "error_type": "schema",
                    "error_message": "generation_id is required"
                }
            
            headers = {"Content-Type": "application/json"}
            api_key = os.getenv("AUTH_API_KEY")
            if api_key:
                headers["X-API-Key"] = api_key
            
            # If generation_id is standard execution_id (e.g. starting with exec_ or contains it), call the Node.js endpoint
            if generation_id.startswith("exec_") or generation_id.startswith("vid_exec_"):
                clean_id = generation_id.replace("vid_exec_", "exec_")
                endpoint = f"/core/execution/{clean_id}"
            else:
                endpoint = f"/status/{generation_id}"
                
            response = requests.get(
                f"{self.base_url}{endpoint}",
                timeout=10,
                headers=headers
            )
            
            response.raise_for_status()
            result = response.json()
            latency = round((time.time() - start_time) * 1000, 2)
            
            self.logger.info(f"Video status check successful",
                           extra={"dependency": "video_service", "endpoint": f"/status/{generation_id}",
                                  "latency_ms": latency, "status_code": response.status_code,
                                  "generation_id": generation_id, "status": result.get('status')})
            return result
            
        except requests.exceptions.Timeout:
            latency = round((time.time() - start_time) * 1000, 2)
            self.logger.error("Video status check failed - timeout",
                            extra={"dependency": "video_service", "endpoint": f"/status/{generation_id}",
                                   "latency_ms": latency, "error_type": "network", "generation_id": generation_id})
            return {
                "success": False,
                "error_type": "network",
                "error_message": "Status check timeout"
            }
        except requests.exceptions.ConnectionError:
            latency = round((time.time() - start_time) * 1000, 2)
            self.logger.error("Video status check failed - connection error",
                            extra={"dependency": "video_service", "endpoint": f"/status/{generation_id}",
                                   "latency_ms": latency, "error_type": "network", "generation_id": generation_id})
            return {
                "success": False,
                "error_type": "network",
                "error_message": "Cannot connect to video service"
            }
        except Exception as e:
            latency = round((time.time() - start_time) * 1000, 2)
            self.logger.error(f"Video status check failed - unexpected error: {str(e)}",
                            extra={"dependency": "video_service", "endpoint": f"/status/{generation_id}",
                                   "latency_ms": latency, "error_type": "unexpected", "generation_id": generation_id, "error": str(e)})
            return {
                "success": False,
                "error_type": "network",
                "error_message": str(e)
            }
    
    def submit_feedback(self, generation_id: str, rating: int, 
                       comment: Optional[str] = None) -> Dict[str, Any]:
        """Submit feedback for generated video"""
        try:
            if not generation_id:
                return {
                    "success": False,
                    "error_type": "schema",
                    "error_message": "generation_id is required"
                }
            
            if not 1 <= rating <= 5:
                return {
                    "success": False,
                    "error_type": "schema",
                    "error_message": "Rating must be between 1 and 5"
                }
            
            payload = {
                "generation_id": generation_id,
                "rating": rating,
                "comment": comment or ""
            }
            
            response = requests.post(
                f"{self.base_url}/feedback",
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            self.logger.error(f"Feedback submission failed: {e}")
            return {
                "success": False,
                "error_type": "network",
                "error_message": str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check video service health"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def is_healthy(self) -> bool:
        """Check if video service is healthy"""
        health = self.health_check()
        return health.get("status") == "healthy" or health.get("status") == "ok"

    def execute_contract_v3(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an engineExecutionContract_v3 contract with the Node.js TTG/TTV microservice.
        Acts as the Hardened Phase 4 Interface (POST /execute).
        """
        start_time = time.time()
        try:
            # 1. Extract trace_id and execution_id
            trace_id = contract.get("trace_id")
            execution_id = contract.get("execution_id")
            
            if not trace_id or not execution_id:
                raise ValueError("Missing required fields: trace_id, execution_id")
                
            # 2. Strip prohibited fields (Rudra Parmeshwar Pipeline Authority rules)
            prohibited_fields = {
                "domain", "decisionEnvelope", "_source", "context", "tasks",
                "output_format", "module", "intent", "world_params", "data"
            }
            cleaned_contract = {k: v for k, v in contract.items() if k not in prohibited_fields}
            
            # 3. Generate HMAC-SHA256 signature envelope
            secret = os.getenv("ENGINE_SHARED_SECRET") or os.getenv("AUTH_SECRET_KEY") or "prod_shakti_tantra_secret_key_2026"
            signed_envelope = sign_payload(cleaned_contract, secret)
            
            # 4. Generate Bearer JWT token
            jwt_secret = os.getenv("AUTH_SECRET_KEY") or secret
            jwt_payload = {
                "iss": "bhiv_core",
                "exp": int(time.time()) + 3600,
                "user_id": "bhiv_user"
            }
            jwt_token = generate_jwt(jwt_payload, jwt_secret)
            
            # 5. Construct headers
            headers = {
                "Content-Type": "application/json",
                "X-Trace-Id": trace_id,
                "X-Execution-Id": execution_id,
                "Authorization": f"Bearer {jwt_token}"
            }
            
            # Also attach API Key if configured
            api_key = os.getenv("AUTH_API_KEY")
            if api_key:
                headers["X-API-Key"] = api_key
                
            # 6. Make request to POST /execute
            self.logger.info(f"Dispatching engineExecutionContract_v3 to TTG/TTV microservice at {self.base_url}/execute",
                             extra={"dependency": "ttg_ttv_service", "endpoint": "/execute", "trace_id": trace_id, "execution_id": execution_id})
                             
            response = requests.post(
                f"{self.base_url}/execute",
                json=signed_envelope,
                timeout=self.timeout,
                headers=headers
            )
            
            response.raise_for_status()
            result = response.json()
            latency = round((time.time() - start_time) * 1000, 2)
            
            self.logger.info(f"TTG/TTV dispatch successful",
                             extra={"dependency": "ttg_ttv_service", "endpoint": "/execute", "latency_ms": latency})
                             
            return {
                "success": True,
                "status": "success",
                "message": "Contract executed successfully",
                "result": result
            }
            
        except Exception as e:
            latency = round((time.time() - start_time) * 1000, 2)
            self.logger.error(f"TTG/TTV contract dispatch failed: {str(e)}",
                             extra={"dependency": "ttg_ttv_service", "endpoint": "/execute", "latency_ms": latency})
            return {
                "success": False,
                "status": "error",
                "message": f"Microservice dispatch failed: {str(e)}",
                "result": {}
            }
