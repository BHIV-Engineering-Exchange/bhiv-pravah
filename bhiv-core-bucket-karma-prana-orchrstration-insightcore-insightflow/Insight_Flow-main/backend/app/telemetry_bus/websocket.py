# app/telemetry_bus/websocket.py
"""
Telemetry Bus WebSocket Endpoints

WebSocket routes for real-time telemetry streaming.
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.telemetry_bus.service import get_telemetry_service, TelemetryBusService

logger = logging.getLogger(__name__)

# Create router
telemetry_router = APIRouter(prefix="/telemetry", tags=["telemetry"])

# Security
security = HTTPBearer()


async def verify_token_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """
    Optional JWT token verification for WebSocket authentication.
    
    Args:
        credentials: Optional HTTP Bearer credentials
    
    Returns:
        Decoded token payload or None
    """
    if not credentials:
        return None
    
    try:
        from app.core.security import verify_token
        return verify_token(credentials)
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        return None


@telemetry_router.websocket("/decisions")
async def websocket_decisions(
    websocket: WebSocket,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for streaming routing decisions.
    
    Connect: ws://localhost:8000/telemetry/decisions?token=<jwt>
    
    Streams:
    - Real-time routing decision packets
    - Confidence scores
    - Alternative agents
    - Latency metrics
    """
    # Get telemetry service
    telemetry_service = get_telemetry_service()
    
    # Accept WebSocket connection
    await websocket.accept()
    
    # Register connection
    registered = await telemetry_service.register_connection(websocket)
    
    if not registered:
        await websocket.close(code=1008, reason="Max connections reached")
        return
    
    logger.info("WebSocket connection established: /decisions")
    
    try:
        # Keep connection alive and listen for client messages
        while True:
            # Wait for client message (ping/pong or commands)
            data = await websocket.receive_text()
            
            # Handle client commands
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "status":
                health = telemetry_service.get_health()
                await websocket.send_json(health.model_dump())
            elif data.startswith("history:"):
                # Send recent packets
                try:
                    limit = int(data.split(":")[1]) if ":" in data else 100
                    limit = min(limit, 100)  # Cap at 100
                    recent = await telemetry_service.get_recent_packets(limit)
                    await websocket.send_json({"history": recent})
                except (ValueError, IndexError):
                    await websocket.send_json({"error": "Invalid history command"})
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: /decisions")
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    
    finally:
        # Unregister connection
        await telemetry_service.unregister_connection(websocket)


@telemetry_router.websocket("/metrics")
async def websocket_metrics(
    websocket: WebSocket,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for streaming aggregated metrics.
    
    Connect: ws://localhost:8000/telemetry/metrics?token=<jwt>
    
    Streams:
    - Aggregated routing metrics
    - Performance statistics
    - Health indicators
    """
    telemetry_service = get_telemetry_service()
    
    await websocket.accept()
    
    registered = await telemetry_service.register_connection(websocket)
    
    if not registered:
        await websocket.close(code=1008, reason="Max connections reached")
        return
    
    logger.info("WebSocket connection established: /metrics")
    
    try:
        while True:
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "health":
                health = telemetry_service.get_health()
                await websocket.send_json(health.model_dump())
            elif data == "metrics":
                metrics = telemetry_service.get_metrics()
                await websocket.send_json({"metrics": metrics})
    
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: /metrics")
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    
    finally:
        await telemetry_service.unregister_connection(websocket)


# Legacy WebSocket endpoint for backward compatibility
@telemetry_router.websocket("/stream")
async def telemetry_stream(websocket: WebSocket):
    """Legacy WebSocket endpoint for backward compatibility"""
    
    # Use enhanced connection management
    await websocket.accept()
    success = await get_telemetry_service().register_connection(websocket)
    
    if not success:
        await websocket.close(code=1013, reason="Max connections reached")
        return
    
    try:
        while True:
            # Keep connection alive and listen for client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        await get_telemetry_service().unregister_connection(websocket)
    except Exception as e:
        logger.error(f"Legacy telemetry WebSocket error: {e}")
        await get_telemetry_service().unregister_connection(websocket)


@telemetry_router.get("/health")
async def telemetry_health(
    telemetry_service: TelemetryBusService = Depends(get_telemetry_service)
):
    """
    Health check endpoint for telemetry service.
    
    Returns:
    - status: ok|degraded|error
    - queue_size: Current packets in queue
    - max_queue_size: Maximum queue capacity
    - active_connections: Number of active WebSocket connections
    - messages_sent: Total messages broadcasted
    - messages_dropped: Messages dropped due to backpressure
    - uptime_seconds: Service uptime
    """
    health = telemetry_service.get_health()
    
    return health


@telemetry_router.get("/metrics")
async def get_telemetry_metrics():
    """Get telemetry service metrics"""
    telemetry_service = get_telemetry_service()
    return {
        "telemetry_metrics": telemetry_service.get_metrics(),
        "status": "active"
    }


@telemetry_router.get("/recent")
async def get_recent_packets(limit: int = 50):
    """Get recent telemetry packets for debugging"""
    telemetry_service = get_telemetry_service()
    packets = await telemetry_service.get_recent_packets(limit=min(limit, 100))
    return {
        "packets": packets,
        "count": len(packets),
        "limit": limit
    }


@telemetry_router.get("/connections")
async def get_connection_info():
    """Get WebSocket connection information"""
    telemetry_service = get_telemetry_service()
    health = telemetry_service.get_health()
    
    return {
        "active_connections": health.active_connections,
        "max_connections": 100,  # From config
        "total_connections": telemetry_service.get_metrics().get("total_connections", 0),
        "connection_limit_reached": health.active_connections >= 100
    }


@telemetry_router.post("/test")
async def test_telemetry_broadcast():
    """Test endpoint to trigger telemetry broadcast"""
    telemetry_service = get_telemetry_service()
    
    # Create test decision data
    test_data = {
        "agent_id": "test-agent",
        "confidence_score": 0.85,
        "routing_strategy": "test",
        "execution_time_ms": 100.0,
        "context": {"test": True},
        "request_id": "test-request",
        "alternatives": ["alt-agent-1", "alt-agent-2"]
    }
    
    await telemetry_service.broadcast_decision(test_data)
    
    return {
        "message": "Test telemetry packet broadcasted",
        "active_connections": telemetry_service.get_health().active_connections
    }