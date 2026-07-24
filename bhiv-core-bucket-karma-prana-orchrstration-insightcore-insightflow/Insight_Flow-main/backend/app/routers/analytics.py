from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Dict, List
from app.core.security import get_current_user
from app.core.database import get_db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


def _get_time_delta(time_range: str) -> timedelta:
    """Get timedelta for given time range string"""
    time_deltas = {
        "1h": timedelta(hours=1),
        "24h": timedelta(days=1),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30)
    }
    return time_deltas[time_range]


@router.get("/overview")
async def get_analytics_overview(
    time_range: str = Query("24h", pattern="^(1h|24h|7d|30d)$"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get analytics overview for dashboard
    
    Args:
        time_range: Time range filter (1h, 24h, 7d, 30d)
        current_user: Current authenticated user
        
    Returns:
        Analytics overview data
    """
    try:
        db = get_db()
        
        threshold = datetime.utcnow() - _get_time_delta(time_range)
        
        # Get routing statistics
        routing_logs = db.table("routing_logs").select("*").gte(
            "created_at", threshold.isoformat()
        ).execute()
        
        total_routings = len(routing_logs.data)
        successful_routings = len([r for r in routing_logs.data if r.get("status") == "success"])
        failed_routings = len([r for r in routing_logs.data if r.get("status") == "failed"])
        
        # Calculate success rate
        success_rate = (successful_routings / total_routings * 100) if total_routings > 0 else 0
        
        # Calculate average confidence
        confidences = [r.get("confidence_score", 0) for r in routing_logs.data]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Calculate average latency
        latencies = [
            r.get("execution_time_ms", 0)
            for r in routing_logs.data
            if r.get("execution_time_ms") is not None
        ]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Get agent performance
        agents = db.table("agents").select("*").execute()
        active_agents = len([a for a in agents.data if a.get("status") == "active"])
        
        return {
            "time_range": time_range,
            "total_routings": total_routings,
            "successful_routings": successful_routings,
            "failed_routings": failed_routings,
            "success_rate": round(success_rate, 2),
            "average_confidence": round(avg_confidence, 3),
            "average_latency_ms": round(avg_latency, 2),
            "active_agents": active_agents,
            "total_agents": len(agents.data)
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving analytics"
        )


@router.get("/agent-performance")
async def get_agent_performance(
    time_range: str = Query("24h", pattern="^(1h|24h|7d|30d)$"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get agent performance metrics
    
    Args:
        time_range: Time range filter
        current_user: Current authenticated user
        
    Returns:
        Agent performance data
    """
    try:
        db = get_db()
        agents = db.table("agents").select("*").execute()
        
        if not agents.data:
            return {"time_range": time_range, "agents": []}
        
        performance_data = []
        for agent in agents.data:
            performance_data.append({
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "agent_type": agent["type"],
                "status": agent["status"],
                "performance_score": agent.get("performance_score", 0),
                "success_rate": agent.get("success_rate", 0),
                "average_latency": agent.get("average_latency", 0),
                "total_requests": agent.get("total_requests", 0)
            })
        
        return {
            "time_range": time_range,
            "agents": performance_data
        }
        
    except Exception as e:
        logger.error(f"Error getting agent performance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving agent performance"
        )