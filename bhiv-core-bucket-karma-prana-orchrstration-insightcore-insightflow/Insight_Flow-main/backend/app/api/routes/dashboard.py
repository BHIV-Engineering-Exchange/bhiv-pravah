# app/api/routes/dashboard.py
"""
Dashboard API endpoints for metrics visualization.
"""

from fastapi import APIRouter, Query
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
dashboard_service = DashboardService()


@router.get("/metrics/performance")
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=720, description="Hours to look back")
):
    """
    Get performance metrics for dashboard.
    
    Returns:
    - total_decisions: Number of routing decisions
    - average_confidence: Mean confidence score
    - confidence_distribution: Histogram of confidence scores
    - top_agents: Best performing agents
    """
    return await dashboard_service.get_performance_metrics(hours=hours)


@router.get("/metrics/accuracy")
async def get_routing_accuracy(
    hours: int = Query(24, ge=1, le=720, description="Hours to look back")
):
    """
    Get routing accuracy metrics.
    
    Returns:
    - accuracy_percentage: % of high-confidence decisions
    - total_decisions: Number of decisions
    """
    return await dashboard_service.get_routing_accuracy(hours=hours)


@router.get("/metrics/agents")
async def get_agent_performance(
    hours: int = Query(24, ge=1, le=720, description="Hours to look back")
):
    """
    Get per-agent performance breakdown.
    
    Returns:
    List of agents with their metrics:
    - total_decisions: How many times selected
    - avg_confidence: Average confidence score
    - min_confidence: Minimum confidence
    - max_confidence: Maximum confidence
    """
    return await dashboard_service.get_agent_performance(hours=hours)