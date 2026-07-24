"""
API v2 Routing endpoints - Enhanced with migration features and improved responses.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from typing import Dict, List
from app.services.interface_service import interface_service
from app.services.ksml_service import ksml_service
from app.services.validation_service import validation_service
from app.services.stp_service import get_stp_service
from app.core.security import get_current_user
from app.api.middleware.version_detector import detect_api_version, add_version_headers
from pydantic import BaseModel
import logging
import time
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/routing", tags=["routing-v2"])


class EnhancedRouteRequest(BaseModel):
    """Enhanced v2 routing request with additional features"""
    input_data: Dict
    input_type: str
    strategy: str = "q_learning"
    context: Dict = {}
    preferences: Dict = {}
    

class BatchRouteRequest(BaseModel):
    """Batch routing request for multiple inputs"""
    requests: List[EnhancedRouteRequest]
    strategy: str = "q_learning"


@router.post("/route", status_code=status.HTTP_200_OK)
async def route_request_v2(
    request: EnhancedRouteRequest,
    http_request: Request,
    response: Response,
    current_user: Dict = Depends(get_current_user)
):
    """
    Enhanced v2 routing with alternatives and metadata
    
    Args:
        request: Enhanced routing request data
        http_request: HTTP request for version detection
        response: HTTP response for headers
        current_user: Current authenticated user
        
    Returns:
        Enhanced routing decision with alternatives and metadata
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        # Detect API version and add headers
        api_version = detect_api_version(http_request)
        add_version_headers(response, api_version)
        
        # Enhanced context with preferences
        context = request.context or {}
        context.update({
            "user_id": current_user.get("user_id"),
            "preferences": request.preferences,
            "api_version": api_version,
            "request_id": request_id
        })
        
        # Get primary routing decision
        from app.services.decision_engine import decision_engine
        routing_decision = await decision_engine.route_request(
            input_data=request.input_data,
            input_type=request.input_type,
            context=context,
            strategy=request.strategy
        )
        
        # Get alternative agents for v2
        alternatives = await _get_alternative_agents(
            request.input_data,
            request.input_type,
            context,
            exclude_agent_id=routing_decision["agent_id"]
        )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Build enhanced v2 response
        enhanced_response = {
            "routing_decision": {
                "agent_id": routing_decision["agent_id"],
                "agent_name": routing_decision["agent_name"],
                "agent_type": routing_decision["agent_type"],
                "confidence_score": routing_decision["confidence_score"],
                "routing_reason": routing_decision["routing_reason"],
                "estimated_latency_ms": 150  # Default estimate
            },
            "alternatives": alternatives,
            "metadata": {
                "request_id": request_id,
                "processing_time_ms": round(processing_time, 2),
                "api_version": api_version,
                "timestamp": time.time(),
                "strategy_used": request.strategy
            }
        }
        
        # Check if client requests STP format via header
        stp_requested = http_request.headers.get("X-STP-Format", "false").lower() == "true"
        
        if stp_requested:
            try:
                stp_service = get_stp_service()
                wrapped_response = await stp_service.wrap_routing_decision(
                    routing_decision=enhanced_response,
                    requires_ack=request.preferences.get("requires_ack", False)
                )
                logger.info(f"V2 STP routing completed for user {current_user.get('user_id')}")
                return wrapped_response
            except Exception as e:
                logger.warning(f"STP wrapping failed in v2 endpoint: {e}")
        
        logger.info(f"V2 enhanced routing completed for user {current_user.get('user_id')}")
        return enhanced_response
        
    except ValueError as e:
        logger.error(f"v2 Routing validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e),
                    "request_id": request_id,
                    "timestamp": time.time()
                }
            }
        )
    except Exception as e:
        logger.error(f"v2 Routing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal routing error",
                    "request_id": request_id,
                    "timestamp": time.time()
                }
            }
        )


async def _get_alternative_agents(
    input_data: Dict,
    input_type: str,
    context: Dict,
    exclude_agent_id: str,
    max_alternatives: int = 3
) -> List[Dict]:
    """Get alternative agent suggestions for v2 response"""
    try:
        from app.services.agent_service import agent_service
        
        # Get all active agents except the selected one
        all_agents = await agent_service.get_active_agents()
        alternative_agents = [
            agent for agent in all_agents 
            if agent.get("id") != exclude_agent_id
        ]
        
        # Score alternatives using rule-based strategy
        scored_alternatives = []
        for agent in alternative_agents[:max_alternatives]:
            score = agent.get("performance_score", 0.5)
            scored_alternatives.append({
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "confidence_score": round(score, 3),
                "reason": f"Alternative option with {score:.1%} performance"
            })
        
        return sorted(scored_alternatives, key=lambda x: x["confidence_score"], reverse=True)
        
    except Exception as e:
        logger.warning(f"Failed to get alternatives: {e}")
        return []


@router.post("/batch", status_code=status.HTTP_200_OK)
async def batch_route_requests(
    batch_request: BatchRouteRequest,
    http_request: Request,
    response: Response,
    current_user: Dict = Depends(get_current_user)
):
    """
    Process multiple routing requests in batch (v2 feature)
    
    Args:
        batch_request: Batch of routing requests
        http_request: HTTP request for version detection
        response: HTTP response for headers
        current_user: Current authenticated user
        
    Returns:
        List of routing decisions
    """
    start_time = time.time()
    batch_id = str(uuid.uuid4())
    
    try:
        api_version = detect_api_version(http_request)
        add_version_headers(response, api_version)
        
        results = []
        
        for i, req in enumerate(batch_request.requests):
            try:
                context = req.context or {}
                context.update({
                    "user_id": current_user.get("user_id"),
                    "batch_id": batch_id,
                    "batch_index": i,
                    "api_version": api_version
                })
                
                from app.services.decision_engine import decision_engine
                routing_decision = await decision_engine.route_request(
                    input_data=req.input_data,
                    input_type=req.input_type,
                    context=context,
                    strategy=batch_request.strategy
                )
                
                results.append({
                    "index": i,
                    "success": True,
                    "routing_decision": routing_decision
                })
                
            except Exception as e:
                logger.error(f"Batch item {i} failed: {e}")
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e)
                })
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "batch_id": batch_id,
            "total_requests": len(batch_request.requests),
            "successful_requests": sum(1 for r in results if r["success"]),
            "failed_requests": sum(1 for r in results if not r["success"]),
            "processing_time_ms": round(processing_time, 2),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "BATCH_PROCESSING_ERROR",
                    "message": "Batch processing failed",
                    "batch_id": batch_id,
                    "timestamp": time.time()
                }
            }
        )


@router.post("/ksml/route", status_code=status.HTTP_200_OK)
async def route_ksml_request_v2(
    ksml_packet: Dict,
    current_user: Dict = Depends(get_current_user)
):
    """
    Route a KSML-formatted request using API v2
    
    Args:
        ksml_packet: KSML-formatted routing request
        current_user: Current authenticated user
        
    Returns:
        KSML-formatted routing response
    """
    try:
        # Validate KSML packet structure
        is_valid, errors = validation_service.validate_incoming_request(
            ksml_packet, "ksml"
        )
        if not is_valid:
            raise ValueError(f"KSML packet validation failed: {', '.join(errors)}")
        
        # Add user context
        user_context = {
            "user_id": current_user.get("user_id"),
            "api_version": "v2"
        }
        
        # Process KSML routing request
        ksml_response = await ksml_service.process_routing_request(
            ksml_packet=ksml_packet,
            user_context=user_context
        )
        
        # Validate KSML response
        is_valid, errors = validation_service.validate_outgoing_response(
            ksml_response, "ksml"
        )
        if not is_valid:
            logger.warning(f"KSML response validation failed: {errors}")
        
        logger.info(f"V2 KSML routing completed for user {current_user.get('user_id')}")
        return ksml_response
        
    except ValueError as e:
        logger.error(f"V2 KSML routing validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"V2 KSML routing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal KSML routing error"
        )


@router.post("/feedback", status_code=status.HTTP_200_OK)
async def submit_feedback_v2(
    feedback_data: Dict,
    http_request: Request,
    response: Response,
    current_user: Dict = Depends(get_current_user)
):
    """
    Enhanced v2 feedback submission with better error handling
    
    Args:
        feedback_data: Enhanced feedback data
        http_request: HTTP request for version detection
        response: HTTP response for headers
        current_user: Current authenticated user
        
    Returns:
        Enhanced success response
    """
    try:
        api_version = detect_api_version(http_request)
        add_version_headers(response, api_version)
        
        # Process feedback using existing engine
        from app.services.decision_engine import decision_engine
        await decision_engine.process_feedback(
            routing_log_id=feedback_data.get("routing_log_id"),
            feedback_data=feedback_data
        )
        
        return {
            "success": True,
            "message": "Feedback processed successfully",
            "routing_log_id": feedback_data.get("routing_log_id"),
            "api_version": api_version,
            "timestamp": time.time()
        }
        
    except ValueError as e:
        logger.error(f"v2 Feedback validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "ROUTING_LOG_NOT_FOUND",
                    "message": str(e),
                    "routing_log_id": feedback_data.get("routing_log_id"),
                    "timestamp": time.time()
                }
            }
        )
    except Exception as e:
        logger.error(f"v2 Feedback processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "FEEDBACK_PROCESSING_ERROR",
                    "message": "Internal feedback processing error",
                    "routing_log_id": feedback_data.get("routing_log_id"),
                    "timestamp": time.time()
                }
            }
        )