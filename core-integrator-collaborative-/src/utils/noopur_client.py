import httpx
import asyncio
from typing import Optional, Dict, Any
from config.config import NOOPUR_BASE_URL, NOOPUR_API_KEY, INTEGRATOR_USE_NOOPUR
import logging

logger = logging.getLogger(__name__)


class NoopurClient:
    """Async HTTP client for Noopur backend integration.

    Methods used by the integrator:
      - generate (POST /generate) returns related_context
      - feedback (POST /feedback)
      - history (GET /history or /history/<topic>)
    """

    def __init__(self, base_url: str = NOOPUR_BASE_URL, api_key: Optional[str] = NOOPUR_API_KEY, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content with related context."""
        if not INTEGRATOR_USE_NOOPUR:
            return {"related_context": []}

        try:
            client = await self._get_client()
            response = await client.post("/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info("Noopur generate successful", extra={
                "dependency": "noopur",
                "endpoint": "/generate",
                "latency_ms": response.elapsed.total_seconds() * 1000 if response.elapsed else None
            })
            return result
        except httpx.TimeoutException:
            logger.error("Noopur generate timeout", extra={
                "dependency": "noopur",
                "endpoint": "/generate",
                "error_type": "timeout",
                "timeout_seconds": self.timeout
            })
            return {"related_context": []}
        except httpx.HTTPStatusError as e:
            logger.error("Noopur generate HTTP error", extra={
                "dependency": "noopur",
                "endpoint": "/generate",
                "status_code": e.response.status_code,
                "error_type": "http_error"
            })
            return {"related_context": []}
        except Exception as e:
            logger.error("Noopur generate failed", extra={
                "dependency": "noopur",
                "endpoint": "/generate",
                "error_type": "unexpected",
                "error": str(e)
            })
            return {"related_context": []}

    async def feedback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit feedback to Noopur."""
        if not INTEGRATOR_USE_NOOPUR:
            return {"status": "disabled"}

        try:
            client = await self._get_client()
            response = await client.post("/feedback", json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info("Noopur feedback successful", extra={
                "dependency": "noopur",
                "endpoint": "/feedback",
                "latency_ms": response.elapsed.total_seconds() * 1000 if response.elapsed else None
            })
            return result
        except httpx.TimeoutException:
            logger.error("Noopur feedback timeout", extra={
                "dependency": "noopur",
                "endpoint": "/feedback",
                "error_type": "timeout"
            })
            return {"status": "timeout"}
        except httpx.HTTPStatusError as e:
            logger.error("Noopur feedback HTTP error", extra={
                "dependency": "noopur",
                "endpoint": "/feedback",
                "status_code": e.response.status_code,
                "error_type": "http_error"
            })
            return {"status": "error"}
        except Exception as e:
            logger.error("Noopur feedback failed", extra={
                "dependency": "noopur",
                "endpoint": "/feedback",
                "error_type": "unexpected",
                "error": str(e)
            })
            return {"status": "error"}

    async def history(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """Fetch generation history from Noopur."""
        if not INTEGRATOR_USE_NOOPUR:
            return []

        try:
            client = await self._get_client()
            endpoint = f"/history/{topic}" if topic else "/history"
            response = await client.get(endpoint)
            response.raise_for_status()
            result = response.json()
            logger.info("Noopur history successful", extra={
                "dependency": "noopur",
                "endpoint": endpoint,
                "latency_ms": response.elapsed.total_seconds() * 1000 if response.elapsed else None
            })
            return result
        except httpx.TimeoutException:
            logger.error("Noopur history timeout", extra={
                "dependency": "noopur",
                "endpoint": endpoint,
                "error_type": "timeout"
            })
            return []
        except httpx.HTTPStatusError as e:
            logger.error("Noopur history HTTP error", extra={
                "dependency": "noopur",
                "endpoint": endpoint,
                "status_code": e.response.status_code,
                "error_type": "http_error"
            })
            return []
        except Exception as e:
            logger.error("Noopur history failed", extra={
                "dependency": "noopur",
                "endpoint": endpoint,
                "error_type": "unexpected",
                "error": str(e)
            })
            return []

    async def health_check(self) -> str:
        """Check Noopur service health. Returns 'up', 'down', or 'disabled'."""
        if not INTEGRATOR_USE_NOOPUR:
            return "disabled"

        try:
            client = await self._get_client()
            response = await client.get("/system/health", timeout=5)
            if response.status_code == 200:
                return "up"
            else:
                return "down"
        except Exception:
            return "down"
