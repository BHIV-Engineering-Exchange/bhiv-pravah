# app/api/routes/admin.py
"""
Admin API endpoints for logging and monitoring.

Endpoints for querying routing decisions and viewing analytics.
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from datetime import datetime

from app.utils.routing_decision_logger import get_routing_logger
from app.core.security import get_current_user
from app.services.karma_service import KarmaServiceClient
from app.ml.q_learning_updater import get_q_updater

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/routing-logs")
async def get_routing_logs(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    date_from: Optional[str] = Query(None, description="From date (ISO format)"),
    date_to: Optional[str] = Query(None, description="To date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Result limit"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get routing decision logs.
    
    Query Parameters:
    - agent_id: Filter by specific agent
    - date_from: Start date (ISO format, e.g., 2025-10-29T12:00:00Z)
    - date_to: End date (ISO format)
    - limit: Max results (1-1000)
    
    Returns:
    List of routing decisions with full details.
    """
    try:
        routing_logger = get_routing_logger()
        decisions = routing_logger.query_decisions(
            agent_id=agent_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(decisions),
            "decisions": decisions,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving logs: {str(e)}"
        )


@router.get("/routing-statistics")
async def get_routing_statistics(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get routing decision statistics.
    
    Returns:
    - total_decisions: Total number of decisions
    - avg_confidence: Average confidence score
    - min_confidence: Minimum confidence
    - max_confidence: Maximum confidence
    - avg_response_time_ms: Average response time
    - unique_agents: Number of agents used
    """
    try:
        routing_logger = get_routing_logger()
        stats = routing_logger.get_statistics(agent_id=agent_id)
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating statistics: {str(e)}"
        )


@router.post("/cleanup-logs")
async def cleanup_old_logs(
    current_user: dict = Depends(get_current_user)
):
    """
    Clean up routing logs older than retention period (30 days).
    
    Returns:
    Number of deleted log entries.
    """
    try:
        routing_logger = get_routing_logger()
        deleted_count = routing_logger.cleanup_old_logs()
        
        return {
            "success": True,
            "deleted_entries": deleted_count,
            "message": f"Deleted {deleted_count} old log entries",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error cleaning logs: {str(e)}"
        )


@router.get("/system-health")
async def get_system_health(
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive system health status.
    
    Returns:
    System health including services, logs, and performance metrics.
    """
    try:
        from app.core.dependencies import get_feedback_service
        from app.ml.weighted_scoring import get_scoring_engine
        
        # Check feedback service
        feedback_service = get_feedback_service()
        feedback_healthy = await feedback_service.health_check()
        feedback_metrics = feedback_service.get_metrics()
        
        # Check scoring engine
        scoring_engine = get_scoring_engine()
        
        # Check routing logs
        routing_logger = get_routing_logger()
        recent_stats = routing_logger.get_statistics()
        
        return {
            "success": True,
            "system_status": "healthy" if feedback_healthy else "degraded",
            "services": {
                "feedback_service": {
                    "status": "healthy" if feedback_healthy else "unhealthy",
                    "metrics": feedback_metrics
                },
                "scoring_engine": {
                    "status": "healthy",
                    "weights": scoring_engine.weights
                },
                "routing_logger": {
                    "status": "healthy",
                    "recent_stats": recent_stats
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking system health: {str(e)}"
        )


@router.post("/karma/toggle")
async def toggle_karma_weighting(
    enabled: bool = Query(..., description="Enable or disable Karma weighting")
):
    """
    Toggle Karma weighting ON/OFF.
    
    This allows for A/B testing and experiments.
    
    Args:
        enabled: True to enable, False to disable
    
    Returns:
        Status of Karma weighting
    """
    try:
        # Get global Karma service instance
        from app.routers.routing import karma_service
        
        karma_service.toggle_karma_weighting(enabled)
        
        return {
            "success": True,
            "karma_enabled": enabled,
            "message": f"Karma weighting {'enabled' if enabled else 'disabled'}"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error toggling Karma: {str(e)}"
        )


@router.get("/karma/metrics")
async def get_karma_metrics():
    """
    Get Karma service metrics.
    
    Returns:
    - requests: Total Karma requests made
    - cache_hits: Cache hit count
    - cache_misses: Cache miss count
    - errors: Error count
    - enabled: Whether Karma is enabled
    """
    try:
        from app.routers.routing import karma_service
        
        metrics = karma_service.get_metrics()
        
        return {
            "success": True,
            "metrics": metrics
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving metrics: {str(e)}"
        )


@router.delete("/karma/cache")
async def clear_karma_cache(
    agent_id: Optional[str] = Query(None, description="Agent ID to clear, or all if None")
):
    """
    Clear Karma cache for specific agent or all agents.
    
    Args:
        agent_id: Agent ID to clear cache for, or None to clear all
    
    Returns:
        Confirmation message
    """
    try:
        from app.routers.routing import karma_service
        
        karma_service.clear_cache(agent_id)
        
        return {
            "success": True,
            "message": f"Karma cache cleared for {'all agents' if agent_id is None else agent_id}"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing cache: {str(e)}"
        )


@router.get("/q-learning/trace")
async def get_learning_trace(limit: int = Query(100, ge=1, le=1000)):
    """
    Get Q-learning trace history.
    
    Returns recent Q-updates with before/after confidence values.
    """
    try:
        q_updater = get_q_updater()
        trace = q_updater.get_learning_trace(limit=limit)
        
        return {
            "success": True,
            "count": len(trace),
            "trace": trace
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trace: {str(e)}"
        )


@router.post("/q-learning/save")
async def save_q_table():
    """Save Q-table to disk"""
    try:
        q_updater = get_q_updater()
        q_updater.save_q_table()
        
        return {
            "success": True,
            "message": "Q-table saved successfully"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving Q-table: {str(e)}"
        )


@router.post("/q-learning/load")
async def load_q_table():
    """Load Q-table from disk"""
    try:
        q_updater = get_q_updater()
        q_updater.load_q_table()
        
        return {
            "success": True,
            "message": "Q-table loaded successfully"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading Q-table: {str(e)}"
        )