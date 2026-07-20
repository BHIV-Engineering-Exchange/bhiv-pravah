"""Auth helpers for E2E: API key headers, optional JWT minting and client login."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

import httpx

from .config import E2EConfig

try:
    import jwt as pyjwt
except ImportError:  # pragma: no cover
    pyjwt = None  # type: ignore


def api_key_headers(api_key: str, *, correlation_id: Optional[str] = None) -> Dict[str, str]:
    headers = {"Authorization": f"Bearer {api_key}"}
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    return headers


def mint_jwt(
    *,
    secret: str,
    user_id: str,
    role: str,
    secret_kind: str = "client",
    ttl_seconds: int = 3600,
) -> Optional[str]:
    if not pyjwt or not secret:
        return None
    now = int(time.time())
    payload: Dict[str, Any] = {
        "sub": user_id,
        "user_id": user_id,
        "role": role,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    if secret_kind == "client":
        payload["client_id"] = user_id
    if secret_kind == "candidate":
        payload["candidate_id"] = user_id
    return pyjwt.encode(payload, secret, algorithm="HS256")


async def login_client_token(
    client: httpx.AsyncClient,
    config: E2EConfig,
) -> Optional[str]:
    if not config.client_login_id or not config.client_login_password:
        return None
    try:
        response = await client.post(
            f"{config.gateway_url}/v1/client/login",
            json={
                "client_id": config.client_login_id,
                "password": config.client_login_password,
            },
            timeout=config.request_timeout_s,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        if data.get("success") and data.get("access_token"):
            return str(data["access_token"])
    except Exception:
        return None
    return None


def bearer_headers(token: str, *, correlation_id: Optional[str] = None) -> Dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    return headers


def build_role_tokens(config: E2EConfig) -> Dict[str, Optional[str]]:
    """Return tokens keyed by role label (None when cannot mint)."""
    tokens: Dict[str, Optional[str]] = {
        "api_key": config.api_key_secret or None,
        "client_jwt": None,
        "recruiter_jwt": None,
        "candidate_jwt": None,
        "admin_jwt": None,
    }
    if config.jwt_secret_key:
        tokens["client_jwt"] = mint_jwt(
            secret=config.jwt_secret_key,
            user_id=config.client_login_id or "TECH001",
            role="client",
            secret_kind="client",
        )
        tokens["admin_jwt"] = mint_jwt(
            secret=config.jwt_secret_key,
            user_id="e2e-admin",
            role="admin",
            secret_kind="client",
        )
    if config.candidate_jwt_secret_key:
        tokens["candidate_jwt"] = mint_jwt(
            secret=config.candidate_jwt_secret_key,
            user_id="e2e-candidate-1",
            role="candidate",
            secret_kind="candidate",
        )
        tokens["recruiter_jwt"] = mint_jwt(
            secret=config.candidate_jwt_secret_key,
            user_id="e2e-recruiter-1",
            role="recruiter",
            secret_kind="candidate",
        )
    return tokens
