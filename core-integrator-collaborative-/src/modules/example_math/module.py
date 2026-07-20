from typing import Dict, Any, List
import logging
from src.modules.base import BaseModule

logger = logging.getLogger(__name__)

class ExampleMathModule(BaseModule):
    """Mathematical operations module implementing BaseModule contract."""
    
    def process(self, data: Dict[str, Any], context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process mathematical operations and return result dict."""
        try:
            operation = data.get("operation", "")
            numbers = data.get("numbers", [])
            
            # Input validation
            if not operation:
                return {
                    "status": "error",
                    "message": "Missing required field: operation",
                    "result": {}
                }
            
            if not isinstance(numbers, list) or len(numbers) == 0:
                return {
                    "status": "error", 
                    "message": "Missing or invalid numbers array",
                    "result": {}
                }
            
            # Validate numbers are numeric
            try:
                nums = [float(n) for n in numbers]
            except (ValueError, TypeError):
                return {
                    "status": "error",
                    "message": "All numbers must be numeric",
                    "result": {}
                }
            
            # Perform operation
            result = None
            if operation == "add":
                result = sum(nums)
            elif operation == "multiply":
                result = 1
                for n in nums:
                    result *= n
            elif operation == "average":
                result = sum(nums) / len(nums)
            elif operation == "max":
                result = max(nums)
            elif operation == "min":
                result = min(nums)
            else:
                return {
                    "status": "error",
                    "message": f"Unsupported operation: {operation}",
                    "result": {}
                }
            
            # Log telemetry
            logger.info("Math operation completed", extra={
                "event_type": "module_math_operation",
                "module_name": "example_math",
                "operation": operation,
                "input_count": len(nums)
            })
            
            return {
                "status": "success",
                "message": f"Mathematical {operation} completed successfully",
                "result": {
                    "operation": operation,
                    "input_numbers": numbers,
                    "result": result
                }
            }
            
        except Exception as e:
            logger.error(f"Math module error: {str(e)}")
            return {
                "status": "error",
                "message": "Internal processing error",
                "result": {}
            }
    
    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "example_math",
            "version": "1.0.0",
            "description": "Mathematical operations module",
            "supported_operations": ["add", "multiply", "average", "max", "min"]
        }