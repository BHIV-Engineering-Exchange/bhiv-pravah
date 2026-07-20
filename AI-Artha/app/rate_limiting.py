#!/usr/bin/env python3
"""
Rate limiting middleware and utilities - In-memory only
"""
import time
from typing import Dict, Optional, Tuple
from fastapi import HTTPException, Request
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)


class InMemoryRateLimit:
    """In-memory rate limiting"""

    def __init__(self):
        self.requests = defaultdict(deque)
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()

    def is_rate_limited(self, identifier: str, limit: int, window_seconds: int) -> Tuple[bool, Dict]:
        """Check if identifier is rate limited"""

        current_time = time.time()

        # Periodic cleanup
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired_entries(current_time)

        # Get request history for this identifier
        request_times = self.requests[identifier]

        # Remove expired entries
        cutoff_time = current_time - window_seconds
        while request_times and request_times[0] <= cutoff_time:
            request_times.popleft()

        # Check if limit exceeded
        if len(request_times) >= limit:
            oldest_request = request_times[0]
            retry_after = int(oldest_request + window_seconds - current_time) + 1

            return True, {
                "limit": limit,
                "window_seconds": window_seconds,
                "current_requests": len(request_times),
                "retry_after": retry_after
            }

        # Add current request
        request_times.append(current_time)

        return False, {
            "limit": limit,
            "window_seconds": window_seconds,
            "current_requests": len(request_times),
            "remaining": limit - len(request_times)
        }

    def _cleanup_expired_entries(self, current_time: float):
        """Remove expired entries from all identifiers"""
        expired_identifiers = []

        for identifier, request_times in self.requests.items():
            cutoff_time = current_time - 3600
            while request_times and request_times[0] <= cutoff_time:
                request_times.popleft()

            if not request_times:
                expired_identifiers.append(identifier)

        for identifier in expired_identifiers:
            del self.requests[identifier]

        self.last_cleanup = current_time


class RateLimiter:
    """Main rate limiter"""

    def __init__(self):
        self.memory_limiter = InMemoryRateLimit()

        # Rate limit configurations
        self.rate_limits = {
            "default": {"limit": 100, "window": 3600},
            "upload": {"limit": 10, "window": 3600},
            "generate": {"limit": 5, "window": 3600},
            "login": {"limit": 5, "window": 900},
            "register": {"limit": 3, "window": 3600},
            "feedback": {"limit": 50, "window": 3600},
            "analytics": {"limit": 200, "window": 3600},
        }

    def get_identifier(self, request: Request, per_user: bool = True) -> str:
        """Get rate limiting identifier"""

        if per_user:
            try:
                if hasattr(request.state, 'user') and request.state.user:
                    user = request.state.user
                    if hasattr(user, 'user_id'):
                        return f"user:{user.user_id}"
                    elif isinstance(user, dict):
                        return f"user:{user.get('user_id', 'unknown')}"
            except Exception:
                pass

        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        if request.client:
            return request.client.host

        return "unknown"

    def check_rate_limit(self, request: Request, endpoint_type: str = "default", per_user: bool = True) -> None:
        """Check rate limit and raise HTTPException if exceeded"""

        config = self.rate_limits.get(endpoint_type, self.rate_limits["default"])
        limit = config["limit"]
        window = config["window"]

        identifier = self.get_identifier(request, per_user)

        is_limited, info = self.memory_limiter.is_rate_limited(identifier, limit, window)

        if is_limited:
            retry_after = info.get("retry_after", window)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for {endpoint_type}. Try again in {retry_after} seconds.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Window": str(window),
                    "X-RateLimit-Remaining": "0"
                }
            )

        remaining = info.get("remaining", 0)
        if not hasattr(request.state, 'rate_limit_headers'):
            request.state.rate_limit_headers = {}

        request.state.rate_limit_headers.update({
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Window": str(window),
            "X-RateLimit-Remaining": str(remaining)
        })


# Global rate limiter instance
rate_limiter = RateLimiter()


# Dependency functions
def rate_limit_default(request: Request):
    """Default rate limiting"""
    rate_limiter.check_rate_limit(request, "default")

def rate_limit_upload(request: Request):
    """Rate limit for upload endpoints"""
    rate_limiter.check_rate_limit(request, "upload", per_user=True)

def rate_limit_generate(request: Request):
    """Rate limit for video generation"""
    rate_limiter.check_rate_limit(request, "generate", per_user=True)

def rate_limit_login(request: Request):
    """Rate limit for login attempts"""
    rate_limiter.check_rate_limit(request, "login", per_user=False)

def rate_limit_register(request: Request):
    """Rate limit for registration"""
    rate_limiter.check_rate_limit(request, "register", per_user=False)

def rate_limit_feedback(request: Request):
    """Rate limit for feedback submission"""
    rate_limiter.check_rate_limit(request, "feedback", per_user=True)

def rate_limit_analytics(request: Request):
    """Rate limit for analytics endpoints"""
    rate_limiter.check_rate_limit(request, "analytics", per_user=True)
