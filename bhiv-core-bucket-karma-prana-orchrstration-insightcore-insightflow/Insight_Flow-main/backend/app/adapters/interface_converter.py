# app/adapters/interface_converter.py
"""
Interface Converter: Convert between InsightFlow and Core API formats.

This adapter translates between:
1. InsightFlow's native request/response format
2. Core's expected API format (compatible with KSML)
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# INSIGHTFLOW API MODELS (v1 - Old Format)
# ============================================================================

class InsightFlowRoutingRequest(BaseModel):
    """InsightFlow v1 routing request format"""
    agent_type: str
    context: Optional[Dict[str, Any]] = None
    confidence_threshold: float = 0.5
    request_id: Optional[str] = None


class InsightFlowRoutingResponse(BaseModel):
    """InsightFlow v1 routing response format"""
    agent_id: str
    agent_type: str
    confidence_score: float
    request_id: Optional[str] = None


# ============================================================================
# CORE API MODELS (v2 - New Format)
# ============================================================================

class CoreRoutingRequest(BaseModel):
    """Core API routing request format"""
    task_type: str = Field(..., description="Type of task (nlp, audio, etc)")
    task_context: Optional[Dict[str, Any]] = Field(
        None, 
        description="Context for task execution"
    )
    min_confidence: float = Field(0.5, ge=0.0, le=1.0)
    correlation_id: Optional[str] = Field(None, description="Request ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Extra metadata")


class CoreRoutingResponse(BaseModel):
    """Core API routing response format"""
    selected_agent_id: str
    agent_category: str
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    correlation_id: Optional[str] = None
    score_breakdown: Optional[Dict[str, float]] = None
    timestamp: str


# ============================================================================
# INTERFACE CONVERTER
# ============================================================================

class InterfaceConverter:
    """
    Converts between InsightFlow and Core API formats.
    
    This enables backward compatibility while supporting new Core format.
    """
    
    @staticmethod
    def insight_flow_to_core(
        insight_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert InsightFlow v1 request to Core format.
        
        Field Mapping:
        - agent_type → task_type
        - confidence_threshold → min_confidence
        - request_id → correlation_id
        - context → task_context
        
        Args:
            insight_request: InsightFlow format request
        
        Returns:
            Core format request
        """
        try:
            core_request = {
                "task_type": insight_request.get("agent_type"),
                "task_context": insight_request.get("context", {}),
                "min_confidence": insight_request.get("confidence_threshold", 0.5),
                "correlation_id": insight_request.get("request_id"),
                "metadata": {
                    "source": "insightflow_v1",
                    "converted_at": datetime.utcnow().isoformat(),
                }
            }
            
            logger.debug(f"Converted InsightFlow request to Core format")
            return core_request
            
        except Exception as e:
            logger.error(f"Error converting to Core format: {str(e)}")
            raise ValueError(f"Failed to convert request: {str(e)}")
    
    @staticmethod
    def core_to_insight_flow(
        core_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert Core response back to InsightFlow format.
        
        Field Mapping:
        - selected_agent_id → agent_id
        - agent_category → agent_type
        - confidence_level → confidence_score
        - correlation_id → request_id
        
        Args:
            core_response: Core format response
        
        Returns:
            InsightFlow format response
        """
        try:
            insight_response = {
                "agent_id": core_response.get("selected_agent_id"),
                "agent_type": core_response.get("agent_category"),
                "confidence_score": core_response.get("confidence_level"),
                "request_id": core_response.get("correlation_id"),
            }
            
            logger.debug(f"Converted Core response to InsightFlow format")
            return insight_response
            
        except Exception as e:
            logger.error(f"Error converting from Core format: {str(e)}")
            raise ValueError(f"Failed to convert response: {str(e)}")
    
    @staticmethod
    def validate_field_mapping(
        source_data: Dict[str, Any],
        source_format: str
    ) -> bool:
        """
        Validate that all required fields are present for conversion.
        
        Args:
            source_data: Data to validate
            source_format: Either 'insightflow' or 'core'
        
        Returns:
            True if valid, raises ValueError otherwise
        """
        if source_format == "insightflow":
            required_fields = ["agent_type"]
            
        elif source_format == "core":
            required_fields = ["selected_agent_id", "agent_category", 
                             "confidence_level"]
        else:
            raise ValueError(f"Unknown source format: {source_format}")
        
        missing_fields = [
            field for field in required_fields 
            if field not in source_data
        ]
        
        if missing_fields:
            raise ValueError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        return True
    
    @staticmethod
    def bidirectional_convert(
        data: Dict[str, Any],
        source_format: str
    ) -> Dict[str, Any]:
        """
        Convert in either direction based on source format.
        
        Args:
            data: Data to convert
            source_format: 'insightflow' or 'core'
        
        Returns:
            Converted data in opposite format
        """
        InterfaceConverter.validate_field_mapping(data, source_format)
        
        if source_format == "insightflow":
            return InterfaceConverter.insight_flow_to_core(data)
        else:
            return InterfaceConverter.core_to_insight_flow(data)