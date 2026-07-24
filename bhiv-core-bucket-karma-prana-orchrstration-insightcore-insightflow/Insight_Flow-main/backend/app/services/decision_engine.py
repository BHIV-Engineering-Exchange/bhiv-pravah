from typing import Dict, List, Tuple, Optional
from app.services.agent_service import AgentService
from app.services.q_learning import q_learning_router
from app.core.dependencies import get_feedback_service
from app.ml.weighted_scoring import get_scoring_engine
from app.core.database import get_db
from app.services.stp_service import get_stp_service
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Core routing decision engine"""
    
    def __init__(self):
        self.agent_service = AgentService()
        self.feedback_score_service = get_feedback_service()
        self.scoring_engine = get_scoring_engine()
        self.stp_service = get_stp_service()
    
    async def route_request(
        self,
        input_data: Dict,
        input_type: str,
        context: Dict = None,
        strategy: str = "q_learning"
    ) -> Dict:
        """
        Route request to appropriate agent
        
        Args:
            input_data: Input data dictionary
            input_type: Type of input (text, audio, image, etc.)
            context: Additional context information
            strategy: Routing strategy (rule_based, semantic, q_learning)
            
        Returns:
            Routing decision dictionary
        """
        request_id = str(uuid.uuid4())
        context = context or {}
        context["input_type"] = input_type
        
        logger.info(f"Routing request {request_id} with strategy '{strategy}'")
        
        # Get available agents with feedback scores
        try:
            available_agents = await self.agent_service.get_active_agents(include_feedback_scores=True)
        except Exception as e:
            logger.error(f"Failed to get active agents from database: {e}")
            # Fallback to mock agents for demo
            available_agents = [
                {"id": "nlp-001", "name": "NLP Processor", "type": "nlp", "status": "active", "performance_score": 0.94, "success_rate": 0.96},
                {"id": "tts-001", "name": "TTS Generator", "type": "tts", "status": "active", "performance_score": 0.89, "success_rate": 0.91},
                {"id": "cv-001", "name": "Vision Analyzer", "type": "computer_vision", "status": "active", "performance_score": 0.87, "success_rate": 0.88}
            ]
            logger.info("Using fallback mock agents for routing")
        
        if not available_agents:
            raise ValueError("No active agents available for routing")
        
        # Select routing strategy
        if strategy == "rule_based":
            agent_id, confidence, reason = await self._route_rule_based(
                input_type, available_agents, context
            )
        elif strategy == "semantic":
            agent_id, confidence, reason = await self._route_semantic(
                input_data, available_agents, context
            )
        elif strategy == "q_learning":
            agent_id, confidence, reason = await self._route_q_learning(
                available_agents, context
            )
        else:
            # Default to rule-based
            agent_id, confidence, reason = await self._route_rule_based(
                input_type, available_agents, context
            )
        
        # Get agent details
        try:
            agent = await self.agent_service.get_agent_by_id(agent_id)
            if not agent:
                # Fallback: find agent in available_agents list
                agent = next((a for a in available_agents if a.get("id") == agent_id), None)
                if not agent:
                    raise ValueError(f"Selected agent {agent_id} not found")
        except Exception as e:
            logger.error(f"Failed to get agent details from database: {e}")
            # Fallback: find agent in available_agents list
            agent = next((a for a in available_agents if a.get("id") == agent_id), None)
            if not agent:
                raise ValueError(f"Selected agent {agent_id} not found in fallback data")
        
        # Create routing log
        valid_statuses = ["pending", "processing", "completed", "failed"]
        try:
            routing_log = {
                "id": str(uuid.uuid4()),
                "request_id": request_id,
                "user_id": context.get("user_id"),
                "input_type": input_type,
                "input_data": input_data,
                "selected_agent_id": agent_id,
                "agent_name": agent.get("name"),
                "confidence_score": confidence,
                "routing_reason": reason,
                "routing_strategy": strategy,
                "status": "pending" if "pending" in valid_statuses else "failed",
                "context": context,
                "created_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to create routing log: {e}")
            raise ValueError("Failed to create routing log with valid status")
        
        # Save to database (with fallback)
        try:
            db = get_db()
            db.table("routing_logs").insert(routing_log).execute()
            logger.info(f"Routing log saved to database: {routing_log['id']}")
        except Exception as e:
            logger.error(f"Failed to save routing log to database: {e}")
            # Continue without database logging for demo purposes
            logger.warning("Continuing routing without database logging (fallback mode)")
        
        logger.info(f"Routed request {request_id} to agent {agent_id} "
                   f"(confidence: {confidence:.3f})")
        
        # Log decision with routing decision logger
        from app.utils.routing_decision_logger import get_routing_logger
        
        routing_logger = get_routing_logger()
        routing_logger.log_decision(
            agent_selected=agent_id,
            confidence_score=confidence,
            request_id=request_id,
            context=context,
            reasoning=reason
        )
        
        # Broadcast to telemetry bus with agent fingerprinting
        from app.telemetry_bus.service import get_telemetry_service
        telemetry_service = get_telemetry_service()
        await telemetry_service.broadcast_decision({
            "agent_id": agent_id,
            "confidence_score": confidence,
            "routing_strategy": strategy,
            "execution_time_ms": 0.0,  # Will be calculated in actual implementation
            "context": context,
            "request_id": request_id
        }, agent_fingerprint=agent_id)  # Use agent_id as fingerprint
        
        # Create routing decision response
        routing_decision = {
            "request_id": request_id,
            "routing_log_id": routing_log["id"],
            "agent_id": agent_id,
            "agent_name": agent.get("name"),
            "agent_type": agent.get("type"),
            "confidence_score": confidence,
            "routing_reason": reason,
            "routing_strategy": strategy
        }
        
        # Return unwrapped decision for standard API compatibility
        # STP wrapping is handled at the endpoint level when needed
        return routing_decision
    
    async def _route_rule_based(
        self,
        input_type: str,
        agents: List[Dict],
        context: Dict
    ) -> Tuple[str, float, str]:
        """Rule-based routing logic with feedback score integration"""
        
        # Map input types to agent types
        type_mapping = {
            "text": "nlp",
            "audio": "tts",
            "image": "computer_vision",
            "video": "computer_vision"
        }
        
        preferred_type = type_mapping.get(input_type, "general")
        
        # Get agent IDs for feedback score lookup
        agent_ids = [agent["id"] for agent in agents if agent.get("id")]
        
        # Fetch real-time feedback scores
        try:
            feedback_scores = await self.feedback_score_service.get_agent_scores(agent_ids)
            logger.info(f"Retrieved feedback scores for {len(feedback_scores)} agents")
        except Exception as e:
            logger.warning(f"Failed to get feedback scores: {e}")
            feedback_scores = {}
        
        # Score agents using weighted scoring engine
        scored_agents = []
        for agent in agents:
            if not agent.get("id"):
                continue
            
            agent_id = agent["id"]
            
            # Calculate rule-based score
            rule_score = 0.0
            if agent["type"] == preferred_type:
                rule_score += 0.5
            rule_score += agent.get("performance_score", 0.5) * 0.3
            rule_score += agent.get("success_rate", 0.5) * 0.2
            
            # Get feedback score
            feedback_score = feedback_scores.get(agent_id, 0.5)
            
            # Calculate availability score (based on agent status and health)
            availability_score = 1.0 if agent.get("status") == "active" else 0.3
            
            # Use weighted scoring engine for final confidence
            confidence_result = self.scoring_engine.calculate_confidence(
                agent_id=agent_id,
                rule_based_score=rule_score,
                feedback_score=feedback_score,
                availability_score=availability_score
            )
            
            scored_agents.append((agent_id, confidence_result))
        
        if not scored_agents:
            raise ValueError("No valid agents available for rule-based routing")
        
        # Select agent with highest confidence score
        best_agent_id, best_confidence = max(scored_agents, key=lambda x: x[1].final_score)
        
        reason = f"Weighted scoring: {input_type} match (confidence: {best_confidence.final_score:.2f})"
        
        return best_agent_id, best_confidence.final_score, reason
    
    async def _route_semantic(
        self,
        input_data: Dict,
        agents: List[Dict],
        context: Dict
    ) -> Tuple[str, float, str]:
        """Semantic routing using NLP embeddings"""
        
        # Simplified semantic routing
        # In production, use actual embeddings and similarity search
        
        text_content = input_data.get("text", "")
        
        # Score agents based on capability tags
        scored_agents = []
        for agent in agents:
            if not agent.get("id"):
                continue
            score = agent.get("performance_score", 0.5)
            
            # Check capability match (simplified)
            tags = agent.get("tags", [])
            for tag in tags:
                if tag.lower() in text_content.lower():
                    score += 0.2
            
            scored_agents.append((agent["id"], min(1.0, score)))
        
        if not scored_agents:
            raise ValueError("No valid agents available for semantic routing")
        
        best_agent_id, best_score = max(scored_agents, key=lambda x: x[1])
        
        reason = "Semantic: High capability match for input content"
        
        return best_agent_id, best_score, reason
    
    async def _route_q_learning(
        self,
        agents: List[Dict],
        context: Dict
    ) -> Tuple[str, float, str]:
        """Q-learning based routing"""
        
        agent_ids = [agent["id"] for agent in agents if agent.get("id")]
        
        if not agent_ids:
            raise ValueError("No valid agents available for Q-learning routing")
        
        # Use Q-learning router
        try:
            selected_agent_id, confidence = q_learning_router.select_agent(
                available_agents=agent_ids,
                context=context,
                explore=True
            )
        except Exception as e:
            logger.error(f"Q-learning routing failed: {e}")
            raise
        
        reason = "Q-Learning: Optimal agent based on learned policy"
        
        return selected_agent_id, confidence, reason
    
    async def process_feedback(
        self,
        routing_log_id: str,
        feedback_data: Dict
    ):
        """
        Process feedback for a routing decision
        
        Args:
            routing_log_id: ID of routing log
            feedback_data: Feedback data
        """
        db = get_db()
        
        try:
            # Get routing log
            routing_log = db.table("routing_logs").select("*").eq("id", routing_log_id).execute()
            
            if not routing_log.data:
                # Create a mock routing log for testing purposes
                log_data = {
                    "id": routing_log_id,
                    "selected_agent_id": "nlp-001",
                    "routing_strategy": "q_learning",
                    "context": {}
                }
                logger.warning(f"Routing log {routing_log_id} not found, using mock data")
            else:
                log_data = routing_log.data[0]
            
            # Update routing log status
            status = "success" if feedback_data.get("success") else "failed"
            db.table("routing_logs").update({
                "status": status,
                "execution_time_ms": feedback_data.get("latency_ms"),
                "response_data": feedback_data.get("response_data")
            }).eq("id", routing_log_id).execute()
            
            # Save feedback
            feedback_record = {
                "id": str(uuid.uuid4()),
                "routing_log_id": routing_log_id,
                "agent_id": log_data["selected_agent_id"],
                "feedback_type": "success" if feedback_data.get("success") else "failure",
                "success": feedback_data.get("success", False),
                "latency_ms": feedback_data.get("latency_ms", 0),
                "accuracy_score": feedback_data.get("accuracy_score"),
                "user_satisfaction": feedback_data.get("user_satisfaction"),
                "metadata": feedback_data.get("metadata", {}),
                "created_at": datetime.utcnow().isoformat()
            }
            
            db.table("feedback_events").insert(feedback_record).execute()
            
            # Wrap feedback in STP format for external systems
            try:
                wrapped_feedback = await self.stp_service.wrap_feedback_packet(
                    feedback_data=feedback_record,
                    requires_ack=True
                )
                logger.debug(f"Feedback wrapped in STP format: {wrapped_feedback.get('stp_token')}")
            except Exception as stp_error:
                logger.warning(f"STP feedback wrapping failed: {stp_error}")
                
        except ConnectionError as e:
            logger.error(f"Database connection failed during feedback processing: {e}")
            raise ConnectionError("Database unavailable - feedback not processed")
        except ValueError as e:
            if "not found" in str(e):
                logger.error(f"Routing log not found: {routing_log_id}")
                raise ValueError(f"Invalid routing log ID: {routing_log_id}")
            else:
                logger.error(f"Invalid feedback data: {e}")
                raise ValueError(f"Feedback validation failed: {e}")
        except Exception as e:
            error_msg = str(e).lower()
            if "foreign key" in error_msg or "constraint" in error_msg:
                logger.error(f"Database constraint violation in feedback: {e}")
                raise ValueError(f"Invalid agent or routing log reference: {e}")
            elif "timeout" in error_msg:
                logger.error(f"Database timeout during feedback processing: {e}")
                raise TimeoutError("Database operation timed out")
            else:
                logger.error(f"Unexpected database error in feedback processing: {e}")
                raise RuntimeError(f"Database operation failed: {e}")
        
        # Update agent performance
        try:
            await self.agent_service.update_agent_performance(
                agent_id=log_data["selected_agent_id"],
                success=feedback_data.get("success", False),
                latency_ms=feedback_data.get("latency_ms", 0)
            )
        except Exception as e:
            logger.error(f"Failed to update agent performance: {e}")
        
        # Update Q-learning if strategy was q_learning
        if log_data.get("routing_strategy") == "q_learning":
            try:
                available_agents = await self.agent_service.get_active_agents()
                agent_ids = [agent["id"] for agent in available_agents]
                
                q_learning_router.process_feedback(
                    routing_log_id=routing_log_id,
                    feedback=feedback_record,
                    context=log_data.get("context", {}),
                    available_agents=agent_ids
                )
            except Exception as e:
                logger.error(f"Failed to update Q-learning: {e}")
        
        logger.info(f"Processed feedback for routing {routing_log_id}")


# Global decision engine instance
decision_engine = DecisionEngine()