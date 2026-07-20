"""
Multi-Product Adapter Validator
Enforces blueprint validation and adapter intelligence for all BHIV products
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from ..utils.logger import setup_logger

class ProductType(Enum):
    """BHIV product types"""
    CONTENT = "content"
    FINANCE = "finance" 
    WORKFLOW = "workflow"
    EDUCATION = "education"

class AdapterValidator:
    """Validates blueprints and enforces adapter intelligence"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
        self.product_adapters = {
            ProductType.CONTENT: "sample_text",
            ProductType.FINANCE: "finance", 
            ProductType.WORKFLOW: "creator",
            ProductType.EDUCATION: "education"
        }
        
        # Blueprint validation rules per product
        self.blueprint_rules = {
            ProductType.CONTENT: {
                "required_payload_fields": ["text"],
                "valid_intent_types": ["generate", "analyze", "process"],
                "max_payload_size": 10000
            },
            ProductType.FINANCE: {
                "required_payload_fields": ["report_type"],
                "valid_intent_types": ["generate", "analyze", "calculate"],
                "max_payload_size": 5000
            },
            ProductType.WORKFLOW: {
                "required_payload_fields": ["workflow_type"],
                "valid_intent_types": ["execute", "validate", "process"],
                "max_payload_size": 8000
            },
            ProductType.EDUCATION: {
                "required_payload_fields": ["content_type"],
                "valid_intent_types": ["generate", "explain", "assess"],
                "max_payload_size": 12000
            }
        }
    
    def validate_blueprint_structure(self, instruction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate blueprint structure for target product
        
        Args:
            instruction: Creator Core instruction
            
        Returns:
            Validation result with adapter routing
        """
        target_product = instruction.get("target_product")
        intent_type = instruction.get("intent_type")
        payload = instruction.get("payload", {})
        
        # Validate target product
        try:
            product_enum = ProductType(target_product)
        except ValueError:
            return {
                "valid": False,
                "error": f"Invalid target_product: {target_product}",
                "error_type": "invalid_product",
                "supported_products": [p.value for p in ProductType]
            }
        
        # Get validation rules for product
        rules = self.blueprint_rules.get(product_enum, {})
        issues = []
        
        # Validate intent type
        valid_intents = rules.get("valid_intent_types", [])
        if intent_type not in valid_intents:
            issues.append(f"Invalid intent_type '{intent_type}' for {target_product}. Valid: {valid_intents}")
        
        # Validate required payload fields
        required_fields = rules.get("required_payload_fields", [])
        for field in required_fields:
            if field not in payload:
                issues.append(f"Missing required payload field: {field}")
        
        # Validate payload size
        max_size = rules.get("max_payload_size", 10000)
        payload_size = len(str(payload))
        if payload_size > max_size:
            issues.append(f"Payload too large: {payload_size} > {max_size}")
        
        # Get adapter mapping
        adapter_module = self.product_adapters.get(product_enum)
        
        validation_result = {
            "valid": len(issues) == 0,
            "issues": issues,
            "target_product": target_product,
            "adapter_module": adapter_module,
            "blueprint_validated": True
        }
        
        if not validation_result["valid"]:
            self.logger.error(
                f"Blueprint validation failed for {target_product}",
                extra={
                    "event_type": "adapter.blueprint_validation_failed",
                    "target_product": target_product,
                    "intent_type": intent_type,
                    "issues": issues,
                    "telemetry_target": "insightflow"
                }
            )
        else:
            self.logger.info(
                f"Blueprint validated for {target_product}",
                extra={
                    "event_type": "adapter.blueprint_validated",
                    "target_product": target_product,
                    "adapter_module": adapter_module,
                    "telemetry_target": "insightflow"
                }
            )
        
        return validation_result
    
    def transform_payload_for_adapter(self, instruction: Dict[str, Any], adapter_module: str) -> Dict[str, Any]:
        """
        Transform payload for specific adapter requirements
        
        Args:
            instruction: Validated instruction
            adapter_module: Target adapter module
            
        Returns:
            Transformed payload for adapter
        """
        target_product = instruction.get("target_product")
        payload = instruction.get("payload", {})
        
        # Product-specific payload transformations
        if target_product == "content":
            return {
                "text": payload.get("text", ""),
                "type": payload.get("type", "generation"),
                "context": payload.get("context", {})
            }
        
        elif target_product == "finance":
            return {
                "report_type": payload.get("report_type", "general"),
                "period": payload.get("period", "current"),
                "data": payload.get("data", {})
            }
        
        elif target_product == "workflow":
            return {
                "workflow_type": payload.get("workflow_type", "standard"),
                "steps": payload.get("steps", []),
                "config": payload.get("config", {})
            }
        
        elif target_product == "education":
            return {
                "content_type": payload.get("content_type", "lesson"),
                "subject": payload.get("subject", "general"),
                "level": payload.get("level", "intermediate")
            }
        
        # Default: return original payload
        return payload
    
    def validate_adapter_response(self, response: Dict[str, Any], target_product: str) -> Dict[str, Any]:
        """
        Validate adapter response meets product requirements
        
        Args:
            response: Adapter response
            target_product: Expected product type
            
        Returns:
            Validation result
        """
        issues = []
        
        # Check required response structure
        if "status" not in response:
            issues.append("Missing required field: status")
        
        if "result" not in response and response.get("status") == "success":
            issues.append("Missing result field for successful response")
        
        # Product-specific response validation
        if target_product == "content":
            result = response.get("result", {})
            if "generated_text" not in result and response.get("status") == "success":
                issues.append("Content response missing generated_text")
        
        elif target_product == "finance":
            result = response.get("result", {})
            if "report_data" not in result and response.get("status") == "success":
                issues.append("Finance response missing report_data")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "target_product": target_product,
            "response_validated": True
        }
    
    def get_supported_products(self) -> List[Dict[str, Any]]:
        """Get list of supported products with their adapters"""
        return [
            {
                "product": product.value,
                "adapter_module": adapter,
                "valid_intents": self.blueprint_rules.get(product, {}).get("valid_intent_types", []),
                "required_fields": self.blueprint_rules.get(product, {}).get("required_payload_fields", [])
            }
            for product, adapter in self.product_adapters.items()
        ]
    
    def reject_invalid_blueprint(self, instruction: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured rejection for invalid blueprint
        
        Args:
            instruction: Original instruction
            validation_result: Validation failure details
            
        Returns:
            Structured rejection response
        """
        return {
            "status": "error",
            "error_type": "blueprint_validation_failed",
            "instruction_id": instruction.get("instruction_id"),
            "target_product": instruction.get("target_product"),
            "message": f"Blueprint validation failed: {validation_result['issues']}",
            "issues": validation_result["issues"],
            "supported_products": [p.value for p in ProductType],
            "rejection_reason": "invalid_blueprint_structure"
        }