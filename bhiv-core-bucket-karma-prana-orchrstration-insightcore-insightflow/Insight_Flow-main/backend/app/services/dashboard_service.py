# app/services/dashboard_service.py
"""
Dashboard Service: Provides metrics for frontend dashboard.

Aggregates performance data for real-time visualization.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.utils.routing_decision_logger import get_routing_logger

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard metrics aggregation"""
    
    def __init__(self):
        """Initialize dashboard service"""
        from app.utils.routing_decision_logger import RoutingDecisionLogger
        self.decision_logger = RoutingDecisionLogger()
    
    async def get_performance_metrics(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get overall performance metrics for past N hours.
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            Performance metrics
        """
        try:
            # Calculate time window
            date_from = (
                datetime.utcnow() - timedelta(hours=hours)
            ).isoformat() + "Z"
            
            # Get all decisions in window
            decisions = self.decision_logger.query_decisions(
                date_from=date_from,
                limit=10000
            )
            
            if not decisions:
                return self._empty_metrics()
            
            # Calculate metrics
            confidences = [d.get("confidence_score", 0) for d in decisions]
            response_times = [
                d.get("response_time_ms", 0) 
                for d in decisions 
                if "response_time_ms" in d
            ]
            
            metrics = {
                "total_decisions": len(decisions),
                "time_window_hours": hours,
                "average_confidence": sum(confidences) / len(confidences),
                "min_confidence": min(confidences),
                "max_confidence": max(confidences),
                "confidence_distribution": self._get_distribution(confidences),
                "avg_response_time_ms": (
                    sum(response_times) / len(response_times) 
                    if response_times else 0
                ),
                "top_agents": self._get_top_agents(decisions, limit=5),
            }
            
            logger.debug(f"Performance metrics calculated: {len(decisions)} decisions")
            return metrics
        
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return self._empty_metrics()
    
    async def get_routing_accuracy(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get routing accuracy metrics.
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            Accuracy metrics
        """
        try:
            date_from = (
                datetime.utcnow() - timedelta(hours=hours)
            ).isoformat() + "Z"
            
            decisions = self.decision_logger.query_decisions(
                date_from=date_from,
                limit=10000
            )
            
            if not decisions:
                return {"accuracy": 0, "total": 0}
            
            # Count high-confidence decisions (accuracy proxy)
            high_confidence_count = sum(
                1 for d in decisions 
                if d.get("confidence_score", 0) >= 0.75
            )
            
            accuracy = {
                "total_decisions": len(decisions),
                "high_confidence_decisions": high_confidence_count,
                "accuracy_percentage": (
                    (high_confidence_count / len(decisions) * 100)
                    if decisions else 0
                ),
                "time_window_hours": hours,
            }
            
            return accuracy
        
        except Exception as e:
            logger.error(f"Error getting routing accuracy: {str(e)}")
            return {"accuracy": 0, "total": 0}
    
    async def get_agent_performance(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get per-agent performance metrics.
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            List of agent metrics
        """
        try:
            date_from = (
                datetime.utcnow() - timedelta(hours=hours)
            ).isoformat() + "Z"
            
            decisions = self.decision_logger.query_decisions(
                date_from=date_from,
                limit=10000
            )
            
            # Aggregate by agent
            agent_stats = {}
            
            for decision in decisions:
                agent_id = decision.get("agent_selected", "unknown")
                confidence = decision.get("confidence_score", 0)
                
                if agent_id not in agent_stats:
                    agent_stats[agent_id] = {
                        "agent_id": agent_id,
                        "total_decisions": 0,
                        "avg_confidence": 0,
                        "min_confidence": 1.0,
                        "max_confidence": 0.0,
                        "confidences": []
                    }
                
                stats = agent_stats[agent_id]
                stats["total_decisions"] += 1
                stats["confidences"].append(confidence)
                stats["min_confidence"] = min(stats["min_confidence"], confidence)
                stats["max_confidence"] = max(stats["max_confidence"], confidence)
            
            # Calculate averages and clean up
            for agent_id, stats in agent_stats.items():
                confidences = stats.pop("confidences")
                stats["avg_confidence"] = (
                    sum(confidences) / len(confidences) if confidences else 0
                )
            
            return list(agent_stats.values())
        
        except Exception as e:
            logger.error(f"Error getting agent performance: {str(e)}")
            return []
    
    @staticmethod
    def _empty_metrics() -> Dict[str, Any]:
        """Return empty metrics template"""
        return {
            "total_decisions": 0,
            "average_confidence": 0,
            "min_confidence": 0,
            "max_confidence": 0,
            "confidence_distribution": {},
            "avg_response_time_ms": 0,
            "top_agents": [],
        }
    
    @staticmethod
    def _get_distribution(values: List[float]) -> Dict[str, int]:
        """Get confidence distribution (0-0.25, 0.25-0.5, etc.)"""
        distribution = {
            "0-0.25": 0,
            "0.25-0.5": 0,
            "0.5-0.75": 0,
            "0.75-1.0": 0,
        }
        
        for value in values:
            if value < 0.25:
                distribution["0-0.25"] += 1
            elif value < 0.5:
                distribution["0.25-0.5"] += 1
            elif value < 0.75:
                distribution["0.5-0.75"] += 1
            else:
                distribution["0.75-1.0"] += 1
        
        return distribution
    
    @staticmethod
    def _get_top_agents(decisions: List, limit: int = 5) -> List[Dict]:
        """Get top agents by frequency"""
        agent_counts = {}
        
        for decision in decisions:
            agent_id = decision.get("agent_selected", "unknown")
            agent_counts[agent_id] = agent_counts.get(agent_id, 0) + 1
        
        sorted_agents = sorted(
            agent_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [
            {"agent_id": aid, "count": count}
            for aid, count in sorted_agents
        ]


# Global dashboard service instance
_dashboard_service = None


def get_dashboard_service() -> DashboardService:
    """Get or create dashboard service instance"""
    global _dashboard_service
    if _dashboard_service is None:
        _dashboard_service = DashboardService()
    return _dashboard_service