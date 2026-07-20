"""Non-destructive Control Center pipeline actions (audit + refresh proxy)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from .config import E2EConfig


@dataclass
class PipelineResult:
    correlation_id: str
    actions: List[Dict[str, Any]] = field(default_factory=list)
    ok: bool = True
    errors: List[str] = field(default_factory=list)


async def run_control_center_pipeline(
    client: httpx.AsyncClient,
    config: E2EConfig,
    auth_headers: Dict[str, str],
    *,
    correlation_id: Optional[str] = None,
) -> PipelineResult:
    """
    Simulate Control Center data flow without destructive writes.

    Pipeline proxy:
    1. POST control_center_view audit event
    2. POST control_center_refresh audit event
    3. Re-read stats (refresh path through gateway)
    """
    cid = correlation_id or str(uuid.uuid4())
    headers = {**auth_headers, "X-Correlation-ID": cid}
    result = PipelineResult(correlation_id=cid)
    gw = config.gateway_url

    events = [
        {
            "action": "control_center_view",
            "outcome": "success",
            "detail": "e2e baseline pipeline view",
            "correlation_id": cid,
            "context": {"service": "e2e", "op": "view"},
        },
        {
            "action": "control_center_refresh",
            "outcome": "success",
            "detail": "e2e pipeline refresh",
            "correlation_id": cid,
            "context": {"service": "e2e", "op": "refresh"},
        },
    ]

    for event in events:
        try:
            response = await client.post(
                f"{gw}/v1/control-center/audit-events",
                headers=headers,
                json=event,
                timeout=config.request_timeout_s,
            )
            action_record = {
                "action": event["action"],
                "status_code": response.status_code,
                "ok": response.status_code == 200,
            }
            if response.status_code == 200:
                try:
                    action_record["body"] = response.json()
                except Exception:
                    action_record["body"] = {}
            else:
                result.ok = False
                result.errors.append(f"{event['action']}: http_{response.status_code}")
            result.actions.append(action_record)
        except Exception as exc:
            result.ok = False
            result.errors.append(f"{event['action']}: {exc}")
            result.actions.append({"action": event["action"], "ok": False, "error": str(exc)})

    try:
        stats_resp = await client.get(
            f"{gw}/v1/candidates/stats",
            headers=headers,
            timeout=config.request_timeout_s,
        )
        result.actions.append(
            {
                "action": "stats_refresh_read",
                "status_code": stats_resp.status_code,
                "ok": stats_resp.status_code == 200,
            }
        )
        if stats_resp.status_code != 200:
            result.ok = False
    except Exception as exc:
        result.ok = False
        result.errors.append(f"stats_refresh: {exc}")

    return result
