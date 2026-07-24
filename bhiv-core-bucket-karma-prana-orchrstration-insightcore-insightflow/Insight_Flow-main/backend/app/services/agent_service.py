from typing import List, Dict, Optional
from app.core.database import get_db
from app.core.dependencies import get_feedback_service
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentService:
    """Service for managing agents"""
    
    def __init__(self):
        self.feedback_score_service = get_feedback_service()
    
    async def get_active_agents(self, include_feedback_scores: bool = False) -> List[Dict]:
        """Get all active agents with optional feedback scores"""
        db = get_db()
        result = db.table("agents").select("*").eq("status", "active").execute()
        agents = result.data
        
        if include_feedback_scores and agents:
            try:
                agent_ids = [agent["id"] for agent in agents]
                feedback_scores = await self.feedback_score_service.get_agent_scores(agent_ids)
                
                # Enrich agents with feedback scores
                for agent in agents:
                    agent["feedback_score"] = feedback_scores.get(agent["id"], 0.5)
                    
                logger.info(f"Enriched {len(agents)} agents with feedback scores")
            except Exception as e:
                logger.warning(f"Failed to get feedback scores: {e}")
                # Add default feedback scores
                for agent in agents:
                    agent["feedback_score"] = 0.5
        
        return agents
    
    async def get_agent_by_id(self, agent_id: str) -> Optional[Dict]:
        """Get agent by ID"""
        db = get_db()
        result = db.table("agents").select("*").eq("id", agent_id).execute()
        return result.data[0] if result.data else None
    
    async def create_agent(self, agent_data: Dict) -> Dict:
        """Create new agent"""
        db = get_db()
        agent_data["created_at"] = datetime.utcnow().isoformat()
        agent_data["updated_at"] = datetime.utcnow().isoformat()
        result = db.table("agents").insert(agent_data).execute()
        if not result.data:
            raise ValueError("Failed to create agent")
        return result.data[0]
    
    async def update_agent_performance(
        self,
        agent_id: str,
        success: bool,
        latency_ms: float
    ):
        """Update agent performance metrics"""
        db = get_db()
        
        # Get current agent data
        agent = await self.get_agent_by_id(agent_id)
        if not agent:
            logger.warning(f"Agent {agent_id} not found")
            return
        
        # Update metrics
        total_requests = agent.get("total_requests", 0) + 1
        successful_requests = agent.get("successful_requests", 0) + (1 if success else 0)
        failed_requests = agent.get("failed_requests", 0) + (0 if success else 1)
        
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        # Update average latency (running average)
        current_avg_latency = agent.get("average_latency", 0)
        new_avg_latency = (
            (current_avg_latency * (total_requests - 1) + latency_ms) / total_requests
        )
        
        # Update performance score (weighted combination)
        performance_score = (0.7 * success_rate) + (0.3 * max(0, 1 - (new_avg_latency / 1000)))
        
        # Update database
        db.table("agents").update({
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": success_rate,
            "average_latency": new_avg_latency,
            "performance_score": performance_score,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", agent_id).execute()
        
        logger.info(f"Updated performance for agent {agent_id}: "
                   f"success_rate={success_rate:.3f}, latency={new_avg_latency:.1f}ms")


# Global agent service instance
agent_service = AgentService()