#!/usr/bin/env python3
"""
Security Hardening Middleware
Rate limiting: Redis-backed when available, falls back to in-memory.
WARNING: In-memory fallback is single-process only.
"""

import re
import time
import hmac
import hashlib
import os
from collections import defaultdict, deque
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

# Security logger
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.WARNING)

# --- Redis-backed rate limiter with in-memory fallback ---
_redis_client = None
_redis_available = False

REDIS_URL = os.getenv("REDIS_URL", "")

if REDIS_URL:
    try:
        import redis
        _redis_client = redis.from_url(REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
        _redis_client.ping()
        _redis_available = True
        security_logger.warning("Rate limiter: Redis backend active")
    except Exception as _e:
        security_logger.warning(f"Rate limiter: Redis unavailable ({_e}), falling back to in-memory")


class RateLimiter:
    """Sliding window rate limiter. Uses Redis when available."""

    def __init__(self, window_seconds: int = 60):
        self.window = window_seconds
        self._fallback: Dict[str, deque] = defaultdict(lambda: deque())

    def is_allowed(self, key: str, limit: int) -> bool:
        if _redis_available and _redis_client:
            try:
                now = time.time()
                pipe = _redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, now - self.window)
                pipe.zadd(key, {str(now): now})
                pipe.zcard(key)
                pipe.expire(key, self.window + 1)
                results = pipe.execute()
                count = results[2]
                return count <= limit
            except Exception:
                pass  # fall through to in-memory on transient Redis error

        # In-memory fallback
        now = time.time()
        dq = self._fallback[key]
        while dq and dq[0] < now - self.window:
            dq.popleft()
        if len(dq) >= limit:
            return False
        dq.append(now)
        return True


_ip_limiter = RateLimiter()
_user_limiter = RateLimiter()

IP_RATE_LIMIT = int(os.getenv("RATE_LIMIT_IP_PER_MIN", "60"))
USER_RATE_LIMIT = int(os.getenv("RATE_LIMIT_USER_PER_MIN", "30"))


class SecurityHardening:
    def __init__(self):
        self.cross_user_access: Dict[str, set] = defaultdict(set)
        self.enumeration_attempts: Dict[str, int] = defaultdict(int)
        self.valid_user_id_pattern = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')

    def validate_user_id(self, user_id: str) -> bool:
        if not user_id or not isinstance(user_id, str):
            return False
        return bool(self.valid_user_id_pattern.match(user_id))

    def check_rate_limits(self, request: Request, user_id: Optional[str] = None) -> bool:
        client_ip = getattr(request.client, "host", "unknown")
        if client_ip in ("127.0.0.1", "::1", "localhost"):
            return True
        if not _ip_limiter.is_allowed(f"ip:{client_ip}", IP_RATE_LIMIT):
            security_logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return False
        if user_id and not _user_limiter.is_allowed(f"user:{user_id}", USER_RATE_LIMIT):
            security_logger.warning(f"Rate limit exceeded for user: {user_id[:8]}...")
            return False
        return True

    def detect_enumeration(self, request: Request, user_id: str) -> bool:
        client_ip = getattr(request.client, "host", "unknown")
        self.cross_user_access[client_ip].add(user_id)
        if len(self.cross_user_access[client_ip]) > 10:
            security_logger.warning(f"Potential enumeration from IP: {client_ip}")
            self.enumeration_attempts[client_ip] += 1
            if self.enumeration_attempts[client_ip] > 3:
                return False
        return True

    def sanitize_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(response_data, dict):
            return response_data
        safe_fields = {'status', 'message', 'result', 'timestamp',
                       'integration_ready', 'integration_score', 'execution_envelope'}
        sanitized = {}
        for key, value in response_data.items():
            if key in safe_fields:
                if isinstance(value, dict):
                    sanitized[key] = self.sanitize_nested_dict(value)
                elif isinstance(value, list):
                    sanitized[key] = [
                        self.sanitize_nested_dict(item) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    sanitized[key] = value
        return sanitized

    def sanitize_nested_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        dangerous_fields = {
            'db_path', 'adapter_type', 'module_load_status',
            'memory', 'failing_components', 'readiness_reason',
            'signature', 'insightflow_event', 'connection_string'
        }
        return {k: v for k, v in data.items() if k not in dangerous_fields}


security = SecurityHardening()


async def security_middleware(request: Request, call_next):
    try:
        if not security.check_rate_limits(request):
            return JSONResponse(status_code=429, content={"error": "Rate limit exceeded"})
        return await call_next(request)
    except Exception as e:
        security_logger.error(f"Security middleware error: {e}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


def validate_user_request(user_id: str, request: Request) -> str:
    if not security.validate_user_id(user_id):
        raise HTTPException(status_code=400, detail="Invalid user identifier format")
    if not security.detect_enumeration(request, user_id):
        raise HTTPException(status_code=429, detail="Access pattern blocked")
    if not security.check_rate_limits(request, user_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return user_id