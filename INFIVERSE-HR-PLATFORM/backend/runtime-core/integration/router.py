"""
REST API Router for Integration Module

Provides REST endpoints for managing and executing integration adapters
with proper authentication and authorization.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from ..auth.auth_service import get_auth, get_api_key
from .adapter_manager import sar_integration
from .integration import execute_secure_adapter, get_adapter_execution_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integration", tags=["integration"])

@router.get("/")
async def get_integration_status():
    """Get the status of the integration framework"""
    if not sar_integration:
        raise HTTPException(status_code=500, detail="Integration framework not initialized")
    
    active_adapters = sar_integration.get_active_adapters()
    all_adapters = list(sar_integration.adapters.keys())
    
    return {
        "status": "active",
        "active_adapters": active_adapters,
        "total_adapters": len(all_adapters),
        "available_adapters": all_adapters
    }

@router.get("/adapters")
async def list_adapters(api_key: str = Depends(get_api_key)):
    """List all available adapters"""
    if not sar_integration:
        raise HTTPException(status_code=500, detail="Integration framework not initialized")
    
    adapters_info = {}
    for name, adapter in sar_integration.adapters.items():
        adapters_info[name] = {
            "name": adapter.name,
            "enabled": adapter.enabled,
            "type": type(adapter).__name__
        }
    
    return {
        "adapters": adapters_info,
        "total": len(adapters_info)
    }

@router.post("/execute-all")
async def execute_all_adapters(
    event: Dict[str, Any], 
    auth: Dict[str, Any] = Depends(get_auth)
):
    """Execute all enabled adapters with the provided event"""
    if not sar_integration:
        raise HTTPException(status_code=500, detail="Integration framework not initialized")
    
    try:
        results = sar_integration.execute_all_adapters(event)
        return {
            "status": "success",
            "results": results,
            "executed_by": auth.get("user_id"),
            "timestamp": event.get("timestamp")
        }
    except Exception as e:
        logger.error(f"Error executing all adapters: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute adapters: {str(e)}")

@router.post("/execute/{adapter_name}")
async def execute_adapter(
    adapter_name: str,
    event: Dict[str, Any],
    auth: Dict[str, Any] = Depends(get_auth)
):
    """Execute a specific adapter with the provided event"""
    if not sar_integration:
        raise HTTPException(status_code=500, detail="Integration framework not initialized")
    
    # Check if adapter exists
    if adapter_name not in sar_integration.adapters:
        raise HTTPException(status_code=404, detail=f"Adapter '{adapter_name}' not found")
    
    try:
        # Use the secure execution function that includes tenant validation
        result = execute_secure_adapter(
            adapter_name=adapter_name,
            event=event,
            requesting_user_id=auth.get("user_id")
        )
        
        return {
            "status": "success",
            "adapter": adapter_name,
            "result": result,
            "executed_by": auth.get("user_id"),
            "timestamp": event.get("timestamp")
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing adapter {adapter_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute adapter: {str(e)}")

@router.patch("/adapters/{adapter_name}/toggle")
async def toggle_adapter(
    adapter_name: str,
    enabled: bool,
    api_key: str = Depends(get_api_key)
):
    """Enable or disable an adapter"""
    if not sar_integration:
        raise HTTPException(status_code=500, detail="Integration framework not initialized")
    
    # Check if adapter exists
    if adapter_name not in sar_integration.adapters:
        raise HTTPException(status_code=404, detail=f"Adapter '{adapter_name}' not found")
    
    success = sar_integration.toggle_adapter(adapter_name, enabled)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to toggle adapter '{adapter_name}'")
    
    return {
        "status": "success",
        "adapter": adapter_name,
        "enabled": enabled
    }

@router.get("/context")
async def get_execution_context(
    event: Dict[str, Any],
    auth: Dict[str, Any] = Depends(get_auth)
):
    """Get the execution context for an event (for debugging purposes)"""
    context = get_adapter_execution_context(event)
    return {
        "context": context,
        "user_info": auth
    }