from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, List
from datetime import datetime
from app.schemas.routing import RouteRequest, RouteResponse, FeedbackRequest
from app.services.decision_engine import decision_engine
from app.core.security import get_current_user, get_current_user_optional
from app.core.dependencies import get_feedback_service
from app.ml.weighted_scoring import get_scoring_engine
from app.adapters.ksml_adapter import KSMLAdapter, KSMLPacketType
from app.utils.routing_decision_logger import get_routing_logger
from app.middleware.stp_middleware import get_stp_middleware, STPPacketType
from app.services.karma_service import KarmaServiceClient
from app.core.config import settings
from app.telemetry_bus.service import get_telemetry_service
from app.telemetry_bus.models import (
    TelemetryPacket,
    DecisionPayload,
    FeedbackPayload,
    TracePayload
)
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)

# Initialize Karma service
karma_service = KarmaServiceClient(
    karma_endpoint=settings.KARMA_ENDPOINT,
    cache_ttl=settings.KARMA_CACHE_TTL,
    timeout=settings.KARMA_TIMEOUT,
    enabled=settings.KARMA_ENABLED
)

# Initialize WeightedScoringEngine with Karma service
scoring_engine = get_scoring_engine(karma_service=karma_service)

router = APIRouter(prefix="/api/v1/routing", tags=["routing"])


@router.post("/route", response_model=RouteResponse, status_code=status.HTTP_200_OK)
async def route_request(
    request: RouteRequest,
    current_user: Dict = Depends(get_current_user_optional)
):
    """
    Route a request to the most suitable agent
    
    Args:
        request: Routing request data
        current_user: Current authenticated user
        
    Returns:
        Routing decision with agent information
    """
    try:
        # Add user context
        context = request.context or {}
        context["user_id"] = current_user.get("user_id")
        
        # Start timing for telemetry
        start_time = time.time()
        
        # Route the request
        routing_decision = await decision_engine.route_request(
            input_data=request.input_data,
            input_type=request.input_type,
            context=context,
            strategy=request.strategy
        )
        
        # Emit telemetry for standard routing
        if settings.TELEMETRY_ENABLED:
            try:
                latency_ms = (time.time() - start_time) * 1000
                telemetry_service = get_telemetry_service()
                
                telemetry_packet = TelemetryPacket(
                    request_id=routing_decision.get("request_id", "unknown"),
                    decision=DecisionPayload(
                        selected_agent=routing_decision.get("agent_id", "unknown"),
                        alternatives=[],  # Not available in standard routing
                        confidence=routing_decision.get("confidence_score", 0.0),
                        latency_ms=latency_ms,
                        strategy=routing_decision.get("routing_strategy", "unknown")
                    ),
                    feedback=FeedbackPayload(
                        reward_signal=None,
                        last_outcome="pending"
                    ),
                    trace=TracePayload(
                        version=settings.APP_VERSION,
                        node="insightflow-router",
                        ts=datetime.utcnow().isoformat() + "Z"
                    )
                )
                
                await telemetry_service.emit_packet(telemetry_packet)
                
            except Exception as e:
                logger.error(f"Standard routing telemetry failed: {str(e)}")
        
        return RouteResponse(**routing_decision)
        
    except ValueError as e:
        logger.error("Routing validation error", extra={
            'error': str(e),
            'input_type': request.input_type,
            'strategy': request.strategy,
            'user_id': current_user.get("user_id")
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Routing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal routing error"
        )


@router.post("/route-stp")
async def route_request_stp(
    request: RouteRequest,
    current_user: Dict = Depends(get_current_user_optional)
):
    """
    Route a request with STP wrapping enabled
    
    Args:
        request: Routing request data
        current_user: Current authenticated user
        
    Returns:
        STP-wrapped routing decision
    """
    try:
        # Add user context
        context = request.context or {}
        context["user_id"] = current_user.get("user_id")
        
        # Start timing for telemetry
        start_time = time.time()
        
        # Route the request
        routing_decision = await decision_engine.route_request(
            input_data=request.input_data,
            input_type=request.input_type,
            context=context,
            strategy=request.strategy
        )
        
        # Emit telemetry for STP routing
        if settings.TELEMETRY_ENABLED:
            try:
                latency_ms = (time.time() - start_time) * 1000
                telemetry_service = get_telemetry_service()
                
                telemetry_packet = TelemetryPacket(
                    request_id=routing_decision.get("request_id", "unknown"),
                    decision=DecisionPayload(
                        selected_agent=routing_decision.get("agent_id", "unknown"),
                        alternatives=[],  # Not available in STP routing
                        confidence=routing_decision.get("confidence_score", 0.0),
                        latency_ms=latency_ms,
                        strategy=routing_decision.get("routing_strategy", "unknown")
                    ),
                    feedback=FeedbackPayload(
                        reward_signal=None,
                        last_outcome="pending"
                    ),
                    trace=TracePayload(
                        version=settings.APP_VERSION,
                        node="insightflow-router-stp",
                        ts=datetime.utcnow().isoformat() + "Z"
                    )
                )
                
                await telemetry_service.emit_packet(telemetry_packet)
                
            except Exception as e:
                logger.error(f"STP routing telemetry failed: {str(e)}")
        
        # Wrap in STP format
        stp_middleware = get_stp_middleware(enable_stp=True)
        stp_wrapped_response = stp_middleware.wrap(
            payload=routing_decision,
            packet_type=STPPacketType.ROUTING_DECISION.value,
            destination=settings.STP_DESTINATION,
            priority=settings.STP_DEFAULT_PRIORITY,
            requires_ack=settings.STP_REQUIRE_ACK
        )
        
        return stp_wrapped_response
        
    except ValueError as e:
        logger.error("STP routing validation error", extra={
            'error': str(e),
            'input_type': request.input_type,
            'strategy': request.strategy,
            'user_id': current_user.get("user_id")
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"STP routing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal STP routing error"
        )


@router.post("/feedback", status_code=status.HTTP_200_OK)
async def submit_feedback(
    feedback: FeedbackRequest,
    current_user: Dict = Depends(get_current_user_optional)
):
    """
    Submit feedback for a routing decision
    
    Args:
        feedback: Feedback data
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        await decision_engine.process_feedback(
            routing_log_id=feedback.routing_log_id,
            feedback_data=feedback.model_dump(exclude={"routing_log_id"})
        )
        
        return {
            "message": "Feedback processed successfully",
            "routing_log_id": feedback.routing_log_id
        }
        
    except ValueError as e:
        logger.error(f"Feedback validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Feedback processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal feedback processing error"
        )


@router.post("/route-agent")
async def route_agent(
    request: dict,
    feedback_service = Depends(get_feedback_service)
):
    # Start timing
    start_time = time.time()
    """
    Route incoming task to best agent using weighted scoring.
    
    Accepts both v1 (InsightFlow) and v2 (Core) formats.
    Returns standard format without STP wrapping for compatibility.
    
    Request body:
    {
        "agent_type": "nlp",  # or "task_type" for v2
        "context": {},
        "confidence_threshold": 0.75
    }
    
    Response:
    {
        "agent_id": "nlp-001",
        "confidence_score": 0.87,
        "score_breakdown": {
            "rule_based_score": 0.80,
            "feedback_based_score": 0.90,
            "availability_score": 0.85,
            ...
        },
        "routing_reasoning": "Selected based on weighted scores"
    }
    """
    
    try:
        # Extract agent type (support both v1 and v2 formats)
        agent_type = request.get("agent_type") or request.get("task_type")
        if not agent_type:
            raise HTTPException(
                status_code=400,
                detail="Missing 'agent_type' or 'task_type'"
            )
        
        confidence_threshold = request.get("confidence_threshold", 0.5)
        context = request.get("context", {})
        request_id = request.get("request_id") or request.get("correlation_id")
        
        # Step 1: Get candidate agents for this type
        candidates = await _get_candidate_agents(agent_type)
        
        if not candidates:
            raise HTTPException(
                status_code=404,
                detail=f"No agents available for type: {agent_type}"
            )
        
        # Step 2: Calculate scores for each candidate
        best_agent = None
        best_confidence = 0.0
        all_scores = {}
        
        for agent in candidates:
            agent_id = agent["id"]
            
            # Get rule-based score (from existing logic)
            rule_score = _calculate_rule_based_score(agent, context)
            
            # Get feedback-based score from Core
            feedback_score = await feedback_service.get_agent_score(agent_id)
            
            # Get availability score
            availability_score = await _get_availability_score(agent_id)
            
            # Calculate final confidence using Karma-weighted scoring
            confidence = await scoring_engine.calculate_confidence_with_karma(
                agent_id=agent_id,
                rule_based_score=rule_score,
                feedback_score=feedback_score,
                availability_score=availability_score
            )
            
            all_scores[agent_id] = {
                "confidence": confidence.final_score,
                "breakdown": confidence.get_breakdown(),
                "rule_score": rule_score,
                "feedback_score": feedback_score,
                "availability_score": availability_score,
            }
            
            # Track best agent
            if confidence.final_score > best_confidence:
                best_confidence = confidence.final_score
                best_agent = agent_id
        
        if not best_agent or best_confidence < confidence_threshold:
            raise HTTPException(
                status_code=503,
                detail="No suitable agent found meeting confidence threshold"
            )
        
        # Step 3: Prepare response
        best_scores = all_scores[best_agent]
        response = {
            "agent_id": best_agent,
            "confidence_score": best_confidence,
            "score_breakdown": {
                "rule_based_score": best_scores["rule_score"],
                "feedback_based_score": best_scores["feedback_score"],
                "availability_score": best_scores["availability_score"],
                "rule_weight": 0.4,
                "feedback_weight": 0.4,
                "availability_weight": 0.2,
            },
            "alternative_agents": [
                {
                    "agent_id": aid,
                    "confidence_score": scores["confidence"]
                }
                for aid, scores in sorted(
                    all_scores.items(),
                    key=lambda x: x[1]["confidence"],
                    reverse=True
                )[1:3]  # Top 2 alternatives
            ],
            "routing_reasoning": (
                f"Selected {best_agent} based on weighted scoring: "
                f"rule={best_scores['rule_score']:.2f}, "
                f"feedback={best_scores['feedback_score']:.2f}, "
                f"availability={best_scores['availability_score']:.2f}"
            ),
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Log routing decision with detailed breakdown
        routing_logger = get_routing_logger()
        routing_logger.log_decision(
            agent_selected=best_agent,
            confidence_score=best_confidence,
            request_id=request_id,
            context=context,
            score_breakdown=best_scores["breakdown"],
            alternatives=[alt["agent_id"] for alt in response["alternative_agents"]],
            response_time_ms=response_time_ms,
            reasoning=response["routing_reasoning"]
        )
        
        # Legacy telemetry broadcast (kept for backward compatibility)
        # Note: Enhanced telemetry emission is now handled below
        
        # Also log to standard logger
        _log_routing_decision(
            agent_id=best_agent,
            confidence=best_confidence,
            request_id=request_id,
            context=context
        )
        
        # Calculate final latency
        final_latency_ms = (time.time() - start_time) * 1000
        
        # Emit telemetry packet
        if settings.TELEMETRY_ENABLED:
            try:
                telemetry_service = get_telemetry_service()
                
                telemetry_packet = TelemetryPacket(
                    request_id=request_id or "unknown",
                    decision=DecisionPayload(
                        selected_agent=best_agent,
                        alternatives=[
                            alt["agent_id"] 
                            for alt in response.get("alternative_agents", [])[:5]
                        ],
                        confidence=best_confidence,
                        latency_ms=final_latency_ms,
                        strategy="weighted_scoring"
                    ),
                    feedback=FeedbackPayload(
                        reward_signal=None,
                        last_outcome="pending"
                    ),
                    trace=TracePayload(
                        version=settings.APP_VERSION,
                        node="insightflow-router",
                        ts=datetime.utcnow().isoformat() + "Z"
                    )
                )
                
                # Emit packet (non-blocking)
                await telemetry_service.emit_packet(telemetry_packet)
                
                logger.debug(
                    f"Telemetry emitted: {request_id}, "
                    f"agent={best_agent}, latency={final_latency_ms:.1f}ms"
                )
            
            except Exception as e:
                # Don't fail the request if telemetry fails
                logger.error(f"Telemetry emission failed: {str(e)}")
        
        # Return unwrapped response for compatibility
        # Note: STP wrapping disabled for this endpoint to maintain compatibility
        # with existing clients expecting standard JSON format
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in route_agent: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _get_candidate_agents(agent_type: str) -> List[Dict]:
    """Get list of agents for given type"""
    from app.services.agent_service import agent_service
    
    try:
        # Get all active agents
        all_agents = await agent_service.get_active_agents()
        
        # Filter by type
        candidates = [
            agent for agent in all_agents 
            if agent.get("type") == agent_type
        ]
        
        return candidates
    except Exception as e:
        logger.error(f"Error getting candidate agents: {e}")
        return []


def _calculate_rule_based_score(agent: Dict, context: Dict) -> float:
    """Calculate score using traditional rules"""
    base_score = 0.8
    
    # Adjust based on context
    if context.get("priority") == "high":
        base_score += 0.1
    
    # Performance bonus
    performance_score = agent.get("performance_score", 0.5)
    base_score = (base_score + performance_score) / 2
    
    # Success rate bonus
    success_rate = agent.get("success_rate", 0.5)
    base_score = (base_score + success_rate) / 2
    
    return min(1.0, base_score)


async def _get_availability_score(agent_id: str) -> float:
    """Get agent availability score"""
    from app.services.agent_service import agent_service
    
    try:
        agent = await agent_service.get_agent_by_id(agent_id)
        if not agent:
            return 0.3
        
        # Base availability on status
        status = agent.get("status", "inactive")
        if status == "active":
            return 1.0
        elif status == "maintenance":
            return 0.5
        else:
            return 0.3
    except Exception as e:
        logger.warning(f"Error getting availability for {agent_id}: {e}")
        return 0.5


def _log_routing_decision(
    agent_id: str,
    confidence: float,
    request_id: str,
    context: Dict
):
    """Log routing decision for audit trail"""
    logger.info(
        f"Routing decision: agent={agent_id}, "
        f"confidence={confidence:.2f}, "
        f"request_id={request_id}"
    )