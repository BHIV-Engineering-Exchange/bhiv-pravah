"""
MITRA Ecosystem Integration API
--------------------------------
Provides REST endpoints for BHIV product integration management.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.core.logging import get_logger
from app.ecosystem.adapter_registry import AdapterRegistry, register_all_adapters
from app.ecosystem.base_adapter import IntegrationRequest

logger = get_logger(__name__)

router = APIRouter()

# Initialize adapter registry at module load
register_all_adapters()


class EcosystemQueryRequest(BaseModel):
    product: str
    action: str
    payload: Optional[Dict[str, Any]] = None


class EcosystemExecuteRequest(BaseModel):
    product: str
    action: str
    payload: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@router.get("/api/ecosystem/products")
async def list_ecosystem_products(
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """List all registered BHIV products and their integration status."""
    registry = AdapterRegistry()
    return {
        "status": "ok",
        "products": registry.list_products(),
        "active_adapters": registry.list_active_adapters(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/api/ecosystem/manifests")
async def get_ecosystem_manifests(
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """Get integration manifests for all registered BHIV products."""
    registry = AdapterRegistry()
    return {
        "status": "ok",
        "manifests": registry.get_manifests(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/api/ecosystem/health")
async def ecosystem_health_check(
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """Health check for all BHIV product integrations."""
    registry = AdapterRegistry()
    health = await registry.health_check_all()
    return {
        "status": "ok",
        "integrations": health,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/api/ecosystem/query")
async def ecosystem_query(
    request: EcosystemQueryRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """Query data from a BHIV product through its adapter."""
    registry = AdapterRegistry()
    adapter = registry.get_adapter(request.product)
    if not adapter:
        raise HTTPException(
            status_code=404,
            detail=f"No adapter registered for product: {request.product}",
        )

    integration_request = IntegrationRequest(
        action=request.action,
        payload=request.payload or {},
        trace_id=f"eco_q_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        source_product="mitra",
        target_product=request.product,
    )

    result = await adapter.query(integration_request)
    return result.to_dict()


@router.post("/api/ecosystem/execute")
async def ecosystem_execute(
    request: EcosystemExecuteRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """Execute an action on a BHIV product through its adapter."""
    registry = AdapterRegistry()
    adapter = registry.get_adapter(request.product)
    if not adapter:
        raise HTTPException(
            status_code=404,
            detail=f"No adapter registered for product: {request.product}",
        )

    integration_request = IntegrationRequest(
        action=request.action,
        payload=request.payload or {},
        trace_id=f"eco_e_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        source_product="mitra",
        target_product=request.product,
        user_id=request.user_id,
        session_id=request.session_id,
    )

    result = await adapter.execute(integration_request)
    return result.to_dict()


@router.get("/api/ecosystem/snapshot")
async def ecosystem_snapshot(
    x_api_key: str = Header(..., alias="X-API-Key"),
):
    """Get full ecosystem registry snapshot for monitoring."""
    registry = AdapterRegistry()
    return {
        "status": "ok",
        "snapshot": registry.snapshot(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
