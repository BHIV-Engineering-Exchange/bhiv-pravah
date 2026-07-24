"""
API v1 Routing endpoints - Legacy InsightFlow format for backward compatibility.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict
from app.schemas.routing import RouteRequest, RouteResponse, FeedbackRequest
from app.services.decision_engine import decision_engine
from app.services.validation_service import validation_service
from app.core.security import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/routing", tags=["routing-v1"])


@router.post("/route", response_model=RouteResponse, status_code=status.HTTP_200_OK)
async def route_request_v1(
    request: RouteRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Route a request using legacy InsightFlow v1 format
    
    Args:
        request: Legacy routing request data
        current_user: Current authenticated user
        
    Returns:
        Legacy routing response format
    """
    try:
        # Validate legacy request format
        is_valid, errors = validation_service.validate_incoming_request(
            request.model_dump(), "insightflow"
        )
        if not is_valid:
            raise ValueError(f"Request validation failed: {', '.join(errors)}")
        
        # Add user context
        context = request.context or {}
        context["user_id"] = current_user.get("user_id")
        context["api_version"] = "v1"
        
        # Route using existing decision engine
        routing_decision = await decision_engine.route_request(
            input_data=request.input_data,
            input_type=request.input_type,
            context=context,
            strategy=request.strategy
        )
        
        response = RouteResponse(**routing_decision)
        
        # Validate legacy response format
        is_valid, errors = validation_service.validate_outgoing_response(
            response.model_dump(), "insightflow"
        )
        if not is_valid:
            logger.warning(f"Response validation failed: {errors}")
        
        logger.info(f"V1 routing completed for user {current_user.get('user_id')}")
        return response
        
    except ValueError as e:
        logger.error(f"V1 routing validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"V1 routing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal routing error"
        )


@router.post("/feedback", status_code=status.HTTP_200_OK)
async def submit_feedback_v1(
    feedback: FeedbackRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Submit feedback using legacy InsightFlow v1 format
    
    Args:
        feedback: Legacy feedback data
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        await decision_engine.process_feedback(
            routing_log_id=feedback.routing_log_id,
            feedback_data=feedback.model_dump(exclude={"routing_log_id"})
        )
        
        logger.info(f"V1 feedback processed for user {current_user.get('user_id')}")
        return {
            "message": "Feedback processed successfully",
            "routing_log_id": feedback.routing_log_id,
            "api_version": "v1"
        }
        
    except ValueError as e:
        logger.error(f"V1 feedback validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"V1 feedback processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal feedback processing error"
        )