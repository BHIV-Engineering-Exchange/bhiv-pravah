from typing import Dict, Any, List
import re
import logging
from src.modules.base import BaseModule

logger = logging.getLogger(__name__)

class ExampleValidationModule(BaseModule):
    """Data validation module implementing BaseModule contract."""
    
    def process(self, data: Dict[str, Any], context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process validation requests and return result dict."""
        try:
            validation_type = data.get("validation_type", "")
            value = data.get("value", "")
            
            # Input validation
            if not validation_type:
                return {
                    "status": "error",
                    "message": "Missing required field: validation_type",
                    "result": {}
                }
            
            if value is None or value == "":
                return {
                    "status": "error",
                    "message": "Missing required field: value",
                    "result": {}
                }
            
            # Convert value to string for validation
            str_value = str(value)
            
            # Perform validation
            is_valid = False
            validation_details = {}
            
            if validation_type == "email":
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                is_valid = bool(re.match(email_pattern, str_value))
                validation_details = {"pattern": "email_format"}
                
            elif validation_type == "phone":
                phone_pattern = r'^\+?1?-?\.?\s?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})$'
                is_valid = bool(re.match(phone_pattern, str_value))
                validation_details = {"pattern": "phone_format"}
                
            elif validation_type == "url":
                url_pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
                is_valid = bool(re.match(url_pattern, str_value))
                validation_details = {"pattern": "url_format"}
                
            elif validation_type == "length":
                min_length = data.get("min_length", 0)
                max_length = data.get("max_length", 1000)
                length = len(str_value)
                is_valid = min_length <= length <= max_length
                validation_details = {
                    "actual_length": length,
                    "min_length": min_length,
                    "max_length": max_length
                }
                
            elif validation_type == "numeric":
                try:
                    float(str_value)
                    is_valid = True
                    validation_details = {"type": "numeric"}
                except ValueError:
                    is_valid = False
                    validation_details = {"type": "non_numeric"}
                    
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported validation type: {validation_type}",
                    "result": {}
                }
            
            # Log telemetry
            logger.info("Validation completed", extra={
                "event_type": "module_validation",
                "module_name": "example_validation",
                "validation_type": validation_type,
                "is_valid": is_valid
            })
            
            return {
                "status": "success",
                "message": f"Validation {validation_type} completed successfully",
                "result": {
                    "validation_type": validation_type,
                    "value": str_value,
                    "is_valid": is_valid,
                    "details": validation_details
                }
            }
            
        except Exception as e:
            logger.error(f"Validation module error: {str(e)}")
            return {
                "status": "error",
                "message": "Internal processing error",
                "result": {}
            }
    
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "example_validation",
            "version": "1.0.0",
            "description": "Data validation module",
            "supported_validations": ["email", "phone", "url", "length", "numeric"]
        }