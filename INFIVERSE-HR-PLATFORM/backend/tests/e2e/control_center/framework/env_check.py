"""Preflight validation for Control Center E2E environment."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from .config import E2EConfig


@dataclass
class EnvCheckResult:
    ok: bool
    missing_required: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    service_reachability: Dict[str, str] = field(default_factory=dict)
    message: str = ""

    def raise_if_blocked(self) -> None:
        if not self.ok:
            lines = ["Control Center E2E preflight failed.", self.message]
            if self.missing_required:
                lines.append("Missing required environment variables:")
                lines.extend(f"  - {name}" for name in self.missing_required)
            if self.warnings:
                lines.append("Warnings:")
                lines.extend(f"  - {w}" for w in self.warnings)
            raise RuntimeError("\n".join(lines))


def check_env_config(config: E2EConfig, *, require_live_gateway: bool = True) -> EnvCheckResult:
    """Validate env vars. API key is required for live E2E; Mongo is optional."""
    missing: List[str] = []
    warnings: List[str] = []

    if not config.api_key_secret:
        missing.append("API_KEY_SECRET (or API_KEY)")

    if not config.jwt_secret_key and not config.candidate_jwt_secret_key:
        warnings.append(
            "JWT_SECRET_KEY and CANDIDATE_JWT_SECRET_KEY unset — role-matrix JWT tests will be skipped"
        )

    if not config.mongodb_uri:
        warnings.append("MONGODB_URI unset — direct audit_logs count assertions skipped")

    if require_live_gateway:
        # Gateway must be reachable; checked separately in async preflight
        pass

    ok = len(missing) == 0
    message = "Environment OK for live E2E." if ok else "Fix missing variables before running live E2E."
    return EnvCheckResult(ok=ok, missing_required=missing, warnings=warnings, message=message)


async def probe_service(
    client: httpx.AsyncClient,
    base_url: str,
    *,
    path: str = "/health",
) -> str:
    try:
        response = await client.get(f"{base_url}{path}", timeout=5.0)
        if response.status_code == 200:
            return "up"
        return f"http_{response.status_code}"
    except httpx.ConnectError:
        return "down_connect"
    except httpx.TimeoutException:
        return "down_timeout"
    except Exception as exc:
        return f"error:{type(exc).__name__}"


async def check_services(
    config: E2EConfig,
    *,
    require_gateway: bool = True,
) -> EnvCheckResult:
    env = check_env_config(config, require_live_gateway=require_gateway)
    reachability: Dict[str, str] = {}

    async with httpx.AsyncClient() as client:
        reachability["gateway"] = await probe_service(client, config.gateway_url)
        reachability["agent"] = await probe_service(client, config.agent_url)
        reachability["langgraph"] = await probe_service(client, config.langgraph_url)

    env.service_reachability = reachability

    if require_gateway and reachability.get("gateway") != "up":
        env.ok = False
        env.message = (
            f"Gateway not reachable at {config.gateway_url} "
            f"(status={reachability.get('gateway')}). Start gateway on :8000."
        )
    elif reachability.get("agent") != "up":
        env.warnings.append(f"Agent optional health skip: {reachability.get('agent')}")
    elif reachability.get("langgraph") != "up":
        env.warnings.append(f"LangGraph optional health skip: {reachability.get('langgraph')}")

    return env


def run_sync_service_check(config: E2EConfig, **kwargs: Any) -> EnvCheckResult:
    return asyncio.run(check_services(config, **kwargs))
