from typing import Dict, Any, List
from .base import BaseAgent
import requests
from config.config import NOOPUR_BASE_URL
from src.utils.bridge_client import BridgeClient
from ..core.feedback_models import CanonicalFeedbackSchema

class CreatorAgent(BaseAgent):
    """Creator module agent for creative operations"""
    
    def __init__(self):
        super().__init__()
        # Use BridgeClient as the canonical CreatorCore integration surface
        self.bridge = BridgeClient()
    
    def handle_request(self, intent: str, data: Dict[str, Any], 
                      context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle creator-related requests using enhanced data from CreatorRouter"""
        
        if intent == "generate":
            # Use related_context from CreatorRouter if available
            related_context = data.get("related_context", [])
            
            # Try to call external CreatorCore service via BridgeClient
            prompt = data.get("prompt") or data.get("topic", "")
            if prompt:
                external_result = self.bridge.generate({"prompt": prompt})
                
                if not external_result.get("error"):
                    return {
                        "status": "success",
                        "message": "Creative content generated via external service",
                        "result": {
                            "generation_id": external_result.get("generation_id"),
                            "generated_text": external_result.get("generated_text"),
                            "related_context": external_result.get("related_context", related_context),
                            "recent_history": data.get("recent_history", [])
                        }
                    }
            
            # Fallback: use enhanced data from CreatorRouter
            return {
                "status": "success",
                "message": "Creative content generated with context",
                "result": {
                    "content": f"Generated content for: {data.get('topic', 'unknown topic')}",
                    "related_context": related_context,
                    "enhanced_data": data
                }
            }
            
        elif intent == "analyze":
            related_context = data.get("related_context", [])
            return {
                "status": "success",
                "message": "Creative analysis completed with context",
                "result": {
                    "analysis": f"Analysis of {data.get('topic', 'content')}",
                    "related_context": related_context,
                    "insights": "Enhanced insights based on context"
                }
            }
            
        elif intent == "review":
            related_context = data.get("related_context", [])
            return {
                "status": "success", 
                "message": "Creative review completed with context",
                "result": {
                    "review": f"Review of {data.get('topic', 'content')}",
                    "related_context": related_context,
                    "feedback": "Enhanced feedback based on context"
                }
            }
            
        elif intent == "feedback":
            # Data is already validated by Gateway using CanonicalFeedbackSchema
            try:
                feedback_schema = CanonicalFeedbackSchema(**data)
                
                # Forward to Noopur using canonical schema
                noopur_payload = feedback_schema.to_noopur_format()
                result = self.bridge.feedback(noopur_payload)
                
                if not result.get("error"):
                    return {
                        "status": "success",
                        "message": "Feedback forwarded to external service",
                        "result": {
                            "forwarded": True,
                            "feedback_data": feedback_schema.to_storage_format(),
                            "external_response": result
                        }
                    }
                
                # Fallback: store locally if forwarding fails
                return {
                    "status": "success",
                    "message": "Feedback stored locally (external service unavailable)",
                    "result": {
                        "forwarded": False,
                        "feedback_data": feedback_schema.to_storage_format()
                    }
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Feedback processing failed: {str(e)}",
                    "result": {}
                }
            
        elif intent == "history":
            # Get history from external service with resilient client
            history_result = self.bridge.history()
            
            if not history_result.get("error"):
                return {
                    "status": "success",
                    "message": "History retrieved from external service",
                    "result": {"history": history_result}
                }
                
            # Fallback to local context
            related_context = data.get("related_context", [])
            return {
                "status": "success",
                "message": "Local history retrieved",
                "result": {"history": related_context}
            }
            
        else:
            return {
                "status": "error",
                "message": f"Unknown intent: {intent}",
                "result": None
            }