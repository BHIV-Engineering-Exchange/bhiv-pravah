"""Outbound Sampada SETU dispatcher — additive side-effect (2026-07-02 closeout)."""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

SAMPADA_SIGNAL_TYPE = "crm_participation"


def _enabled() -> bool:
    return os.getenv("SAMPADA_SETU_ENABLED", "false").lower() == "true"


def build_sampada_body(
    event: Dict[str, Any],
    *,
    subsystem: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    payload = dict(event)
    if subsystem:
        payload["subsystem"] = subsystem
    trace_id = event.get("trace_id") or str(uuid.uuid4())
    cid = correlation_id or event.get("correlation_id") or str(uuid.uuid4())
    return {
        "signal_type": SAMPADA_SIGNAL_TYPE,
        "payload": payload,
        "workforce_ref_id": event.get("workforce_ref_id"),
        "source_declaration": "crm participation",
        "origin_system": "crm",
        "owning_system": "crm",
        "trace_id": trace_id,
        "correlation_id": cid,
        "trust_classification": "observed",
        "visibility_scope": "tenant",
    }


async def dispatch_to_sampada(
    event: Dict[str, Any],
    *,
    subsystem: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """POST crm_participation to Sampada live gateway. Real HTTP only."""
    if not _enabled():
        return {"dispatched": False, "reason": "SAMPADA_SETU_ENABLED is false"}

    base = (os.getenv("SAMPADA_SETU_BASE_URL") or "").rstrip("/")
    api_key = os.getenv("SAMPADA_SETU_API_KEY") or ""
    if not base or not api_key:
        return {"dispatched": False, "reason": "missing SAMPADA_SETU_BASE_URL or SAMPADA_SETU_API_KEY"}

    body = build_sampada_body(event, subsystem=subsystem, correlation_id=correlation_id)
    url = f"{base}/v1/setu/signals/{SAMPADA_SIGNAL_TYPE}"
    timeout = float(os.getenv("SAMPADA_SETU_TIMEOUT_S", "30"))

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                url,
                json=body,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            )
        result: Dict[str, Any] = {
            "dispatched": response.status_code == 200,
            "request": {"method": "POST", "url": url, "body": body},
            "response": {"status": response.status_code, "body": response.json() if response.content else None},
        }
        if response.status_code != 200:
            result["reason"] = f"HTTP {response.status_code}"
        return result
    except Exception as exc:  # noqa: BLE001 — capture wire failure for evidence
        logger.warning("Sampada SETU dispatch failed: %s", exc)
        return {
            "dispatched": False,
            "reason": str(exc),
            "request": {"method": "POST", "url": url, "body": body},
        }
