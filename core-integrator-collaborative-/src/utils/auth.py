"""
JWT / API-Key authentication middleware.

Public endpoints (no auth required):
  GET  /
  GET  /system/health

All other endpoints require either:
  - Header: Authorization: Bearer <JWT>
  - Header: X-API-Key: <api_key>

Environment variables:
  AUTH_SECRET_KEY   — HS256 signing secret (required when AUTH_ENABLED=true)
  AUTH_API_KEY      — static API key alternative
  AUTH_ENABLED      — set to "true" to enforce auth (default: true)
"""

import os
import time
import hmac
import hashlib
import base64
import json
from typing import Optional, Tuple
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() in ("1", "true", "yes")
AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "")
AUTH_API_KEY = os.getenv("AUTH_API_KEY", "")

# Endpoints that do NOT require authentication
PUBLIC_PATHS = {"/", "/system/health", "/docs", "/openapi.json", "/redoc", "/pipeline/health", "/health", "/bucket/stats"}


def _b64url_decode(s: str) -> bytes:
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _verify_jwt(token: str) -> Tuple[bool, Optional[dict]]:
    """Minimal HS256 JWT verification without external libraries."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False, None
        header_b64, payload_b64, sig_b64 = parts
        expected_sig = hmac.new(
            AUTH_SECRET_KEY.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256,
        ).digest()
        expected_b64 = base64.urlsafe_b64encode(expected_sig).rstrip(b"=").decode()
        if not hmac.compare_digest(expected_b64, sig_b64):
            return False, None
        payload = json.loads(_b64url_decode(payload_b64))
        exp = payload.get("exp")
        if exp and time.time() > exp:
            return False, None
        return True, payload
    except Exception:
        return False, None


def _extract_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


async def auth_middleware(request: Request, call_next):
    """FastAPI middleware that enforces authentication on protected paths."""
    if not AUTH_ENABLED:
        return await call_next(request)

    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    # API Key check
    api_key_header = request.headers.get("X-API-Key", "")
    if AUTH_API_KEY and api_key_header:
        if hmac.compare_digest(api_key_header, AUTH_API_KEY):
            request.state.auth_payload = {"user": "api_key_client", "auth_method": "api_key"}
            return await call_next(request)
        return JSONResponse(status_code=401, content={"error": "Invalid API key"})

    # JWT check
    token = _extract_token(request)
    if not token:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required. Provide Authorization: Bearer <token> or X-API-Key header."},
        )

    if not AUTH_SECRET_KEY:
        return JSONResponse(
            status_code=500,
            content={"error": "Server misconfiguration: AUTH_SECRET_KEY not set"},
        )

    valid, payload = _verify_jwt(token)
    if not valid:
        return JSONResponse(status_code=401, content={"error": "Invalid or expired token"})

    # Attach decoded payload to request state for downstream use
    request.state.auth_payload = payload
    return await call_next(request)


def require_auth(request: Request) -> dict:
    """FastAPI dependency that returns the auth payload or raises 401."""
    if not AUTH_ENABLED:
        return {}
    if not hasattr(request.state, "auth_payload"):
        raise HTTPException(status_code=401, detail="Authentication required")
    return request.state.auth_payload
