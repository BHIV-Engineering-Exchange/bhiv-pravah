# app/routers/telemetry_security.py
"""
Telemetry Security API Endpoints

Provides endpoints for managing telemetry packet signing and verification.
Maintains backward compatibility with existing telemetry endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

from app.core.security import get_current_user
from app.telemetry_bus.service import get_telemetry_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telemetry/security", tags=["telemetry-security"])


class PacketVerificationRequest(BaseModel):
    """Request model for packet verification"""
    signed_packet: Dict[str, Any]


class PacketVerificationResponse(BaseModel):
    """Response model for packet verification"""
    is_valid: bool
    error_message: Optional[str] = None
    verification_timestamp: str


class SecurityMetricsResponse(BaseModel):
    """Response model for security metrics"""
    packet_signing_enabled: bool
    packets_signed: int
    signing_errors: int
    verification_requests: int
    verification_failures: int
    last_signing_error: Optional[str] = None


@router.get("/status", response_model=Dict[str, Any])
async def get_security_status(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get telemetry security status and configuration.
    
    Returns:
        Security status information
    """
    try:
        telemetry_service = get_telemetry_service()
        
        status_info = {
            "packet_signing_enabled": telemetry_service.enable_packet_signing,
            "security_version": "v1",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service_status": "active"
        }
        
        # Add signer status if enabled
        from app.core.config import settings
        signing_enabled = (getattr(settings, 'ENABLE_TELEMETRY_SIGNING', False) or 
                          getattr(settings, 'TELEMETRY_PACKET_SIGNING', False))
        
        if signing_enabled and telemetry_service._telemetry_signer:
            status_info.update({
                "signer_initialized": True,
                "max_timestamp_drift_seconds": telemetry_service._telemetry_signer.max_drift,
                "nonce_cache_size": len(telemetry_service._telemetry_signer._used_nonces),
                "config_max_drift": getattr(settings, 'TELEMETRY_MAX_TIMESTAMP_DRIFT', 5)
            })
        else:
            status_info["signer_initialized"] = False
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error getting security status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security status"
        )


@router.post("/verify", response_model=PacketVerificationResponse)
async def verify_packet(
    request: PacketVerificationRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Verify a signed telemetry packet.
    
    Args:
        request: Packet verification request
        current_user: Current authenticated user
        
    Returns:
        Verification result
    """
    try:
        telemetry_service = get_telemetry_service()
        
        # Check if signing is enabled
        from app.core.config import settings
        signing_enabled = (getattr(settings, 'ENABLE_TELEMETRY_SIGNING', False) or 
                          getattr(settings, 'TELEMETRY_PACKET_SIGNING', False))
        
        if not signing_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Packet signing is not enabled"
            )
        
        # Verify packet
        is_valid, error_message = telemetry_service._telemetry_signer.verify_packet(
            request.signed_packet
        )
        
        # Update metrics (if verification service had metrics)
        if hasattr(telemetry_service, '_verification_metrics'):
            telemetry_service._verification_metrics['verification_requests'] += 1
            if not is_valid:
                telemetry_service._verification_metrics['verification_failures'] += 1
        
        return PacketVerificationResponse(
            is_valid=is_valid,
            error_message=error_message,
            verification_timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying packet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Packet verification failed"
        )


@router.get("/metrics", response_model=SecurityMetricsResponse)
async def get_security_metrics(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get telemetry security metrics.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Security metrics
    """
    try:
        telemetry_service = get_telemetry_service()
        
        # Get base metrics from telemetry service
        base_metrics = telemetry_service.metrics
        
        # Initialize verification metrics if not present
        if not hasattr(telemetry_service, '_verification_metrics'):
            telemetry_service._verification_metrics = {
                'verification_requests': 0,
                'verification_failures': 0,
                'last_signing_error': None
            }
        
        verification_metrics = telemetry_service._verification_metrics
        
        from app.core.config import settings
        signing_enabled = (getattr(settings, 'ENABLE_TELEMETRY_SIGNING', False) or 
                          getattr(settings, 'TELEMETRY_PACKET_SIGNING', False))
        
        return SecurityMetricsResponse(
            packet_signing_enabled=signing_enabled,
            packets_signed=base_metrics.get("packets_signed", 0),
            signing_errors=base_metrics.get("signing_errors", 0),
            verification_requests=verification_metrics.get("verification_requests", 0),
            verification_failures=verification_metrics.get("verification_failures", 0),
            last_signing_error=verification_metrics.get("last_signing_error")
        )
        
    except Exception as e:
        logger.error(f"Error getting security metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security metrics"
        )


@router.post("/toggle")
async def toggle_packet_signing(
    enabled: bool,
    current_user: Dict = Depends(get_current_user)
):
    """
    Toggle packet signing on/off (admin only).
    
    Args:
        enabled: Whether to enable packet signing
        current_user: Current authenticated user
        
    Returns:
        Updated status
    """
    try:
        # Check admin permissions
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        telemetry_service = get_telemetry_service()
        
        # Update signing status
        old_status = telemetry_service.enable_packet_signing
        telemetry_service.enable_packet_signing = enabled
        
        # Initialize or clear signer
        if enabled and not telemetry_service._telemetry_signer:
            try:
                from app.telemetry_bus.telemetry_security import get_telemetry_signer
                telemetry_service._telemetry_signer = get_telemetry_signer()
                logger.info("Telemetry signer initialized")
            except Exception as e:
                logger.error(f"Failed to initialize signer: {e}")
                telemetry_service.enable_packet_signing = False
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to initialize packet signer"
                )
        
        logger.info(
            f"Packet signing toggled: {old_status} -> {enabled} "
            f"by user {current_user.get('user_id')}"
        )
        
        return {
            "packet_signing_enabled": telemetry_service.enable_packet_signing,
            "previous_status": old_status,
            "message": f"Packet signing {'enabled' if enabled else 'disabled'}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling packet signing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle packet signing"
        )


@router.delete("/nonce-cache")
async def clear_nonce_cache(
    current_user: Dict = Depends(get_current_user)
):
    """
    Clear the nonce cache (admin only).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Cache clear status
    """
    try:
        # Check admin permissions
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        telemetry_service = get_telemetry_service()
        
        if not telemetry_service.enable_packet_signing or not telemetry_service._telemetry_signer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Packet signing is not enabled"
            )
        
        # Clear nonce cache
        cache_size = len(telemetry_service._telemetry_signer._used_nonces)
        telemetry_service._telemetry_signer._used_nonces.clear()
        
        logger.info(
            f"Nonce cache cleared ({cache_size} entries) "
            f"by user {current_user.get('user_id')}"
        )
        
        return {
            "cache_cleared": True,
            "entries_removed": cache_size,
            "message": f"Cleared {cache_size} nonce entries",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing nonce cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear nonce cache"
        )