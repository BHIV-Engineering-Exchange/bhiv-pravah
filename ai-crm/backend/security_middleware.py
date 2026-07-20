
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from collections import defaultdict

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    def __init__(self, app, rate_limit_rpm: int = 60):
        super().__init__(app)
        self.rate_limit_rpm = rate_limit_rpm
        self.request_counts = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        # Rate limiting
        client_ip = request.client.host
        now = time.time()
        
        # Clean old requests
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if now - req_time < 60
        ]
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.rate_limit_rpm:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Record request
        self.request_counts[client_ip].append(now)
        
        # Security headers
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
