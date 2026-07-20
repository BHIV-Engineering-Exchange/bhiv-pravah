"""
Artifact Schema Validator
Enforces strict schema validation for all artifact types before Bucket writes
"""

import json
import jsonschema
from typing import Dict, Any, List, Optional
from ..utils.logger import setup_logger

class ArtifactSchemaValidator:
    """Validates artifacts against BHIV schema registry"""
    
    def __init__(self, schema_registry_path: str = "artifact_schema_registry.json"):
        self.logger = setup_logger(__name__)
        self.schema_registry = self._load_schema_registry(schema_registry_path)
        self.validator_cache = {}
    
    def _load_schema_registry(self, schema_path: str) -> Dict[str, Any]:
        """Load artifact schema registry"""
        try:
            with open(schema_path, 'r') as f:
                registry = json.load(f)
            
            self.logger.info(f"Loaded artifact schema registry: {registry['version']}")
            return registry
            
        except Exception as e:
            self.logger.error(f"Failed to load schema registry: {e}")
            # Return minimal schema as fallback
            return {
                "version": "fallback",
                "artifact_types": {
                    "blueprint": {"required": ["artifact_id", "artifact_type"]},
                    "execution": {"required": ["artifact_id", "artifact_type"]}, 
                    "result": {"required": ["artifact_id", "artifact_type"]}
                }
            }
    
    def validate_artifact(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate artifact against schema registry
        
        Args:
            artifact: Artifact to validate
            
        Returns:
            Validation result with issues if any
        """
        artifact_type = artifact.get("artifact_type")
        
        if not artifact_type:
            return {
                "valid": False,
                "issues": ["Missing required field: artifact_type"],
                "artifact_id": artifact.get("artifact_id", "unknown")
            }
        
        # Get schema for artifact type
        type_schema = self.schema_registry.get("artifact_types", {}).get(artifact_type)
        
        if not type_schema:
            return {
                "valid": False,
                "issues": [f"Unknown artifact type: {artifact_type}"],
                "artifact_id": artifact.get("artifact_id", "unknown")
            }
        
        issues = []
        
        # Validate required fields
        required_fields = type_schema.get("required", [])
        for field in required_fields:
            if field not in artifact:
                issues.append(f"Missing required field: {field}")
        
        # Validate field properties
        properties = type_schema.get("properties", {})
        for field, field_schema in properties.items():
            if field in artifact:
                field_issues = self._validate_field(field, artifact[field], field_schema)
                issues.extend(field_issues)
        
        # Validate BHIV contract requirements
        contract_issues = self._validate_bucket_contract(artifact)
        issues.extend(contract_issues)
        
        validation_result = {
            "valid": len(issues) == 0,
            "issues": issues,
            "artifact_id": artifact.get("artifact_id", "unknown"),
            "artifact_type": artifact_type
        }
        
        if not validation_result["valid"]:
            self.logger.error(
                f"Artifact validation failed: {artifact_type}",
                extra={
                    "event_type": "validation.artifact_failed",
                    "artifact_id": artifact.get("artifact_id"),
                    "artifact_type": artifact_type,
                    "issues": issues,
                    "telemetry_target": "insightflow"
                }
            )
        
        return validation_result
    
    def _validate_field(self, field_name: str, field_value: Any, field_schema: Dict[str, Any]) -> List[str]:
        """Validate individual field against its schema"""
        issues = []
        
        # Type validation
        expected_type = field_schema.get("type")
        if expected_type:
            if expected_type == "string" and not isinstance(field_value, str):
                issues.append(f"{field_name}: expected string, got {type(field_value).__name__}")
            elif expected_type == "object" and not isinstance(field_value, dict):
                issues.append(f"{field_name}: expected object, got {type(field_value).__name__}")
            elif expected_type == "integer" and not isinstance(field_value, int):
                issues.append(f"{field_name}: expected integer, got {type(field_value).__name__}")
        
        # Pattern validation
        pattern = field_schema.get("pattern")
        if pattern and isinstance(field_value, str):
            import re
            if not re.match(pattern, field_value):
                issues.append(f"{field_name}: does not match required pattern {pattern}")
        
        # Enum validation
        enum_values = field_schema.get("enum")
        if enum_values and field_value not in enum_values:
            issues.append(f"{field_name}: must be one of {enum_values}, got '{field_value}'")
        
        # Minimum validation
        minimum = field_schema.get("minimum")
        if minimum is not None and isinstance(field_value, (int, float)):
            if field_value < minimum:
                issues.append(f"{field_name}: must be >= {minimum}, got {field_value}")
        
        return issues
    
    def _validate_bucket_contract(self, artifact: Dict[str, Any]) -> List[str]:
        """Validate artifact against BHIV Bucket contract"""
        issues = []
        
        # Check required fields for all artifacts
        bucket_contract = self.schema_registry.get("bucket_contract", {})
        required_fields = bucket_contract.get("required_fields_all_artifacts", [])
        
        for field in required_fields:
            if field not in artifact:
                issues.append(f"Bucket contract violation: missing {field}")
        
        # Validate hash linking for non-root artifacts
        if artifact.get("artifact_type") in ["execution", "result"]:
            if not artifact.get("parent_hash"):
                issues.append("Bucket contract violation: non-root artifact must have parent_hash")
        
        # Validate immutability markers
        if "created_at" not in artifact and "timestamp" not in artifact:
            issues.append("Bucket contract violation: missing immutability timestamp")
        
        return issues
    
    def validate_artifact_chain(self, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate complete artifact chain (blueprint → execution → result)
        
        Args:
            artifacts: List of artifacts in chain
            
        Returns:
            Chain validation result
        """
        issues = []
        
        # Check for required artifact types
        artifact_types = [a.get("artifact_type") for a in artifacts]
        required_types = ["blueprint", "execution", "result"]
        
        for required_type in required_types:
            if required_type not in artifact_types:
                issues.append(f"Missing required artifact type in chain: {required_type}")
        
        # Validate individual artifacts
        for artifact in artifacts:
            validation = self.validate_artifact(artifact)
            if not validation["valid"]:
                issues.extend([f"{artifact.get('artifact_type', 'unknown')}: {issue}" for issue in validation["issues"]])
        
        # Validate hash linking
        artifacts_by_type = {a["artifact_type"]: a for a in artifacts if "artifact_type" in a}
        
        if "blueprint" in artifacts_by_type and "execution" in artifacts_by_type:
            blueprint = artifacts_by_type["blueprint"]
            execution = artifacts_by_type["execution"]
            
            if execution.get("parent_hash") != blueprint.get("artifact_hash"):
                issues.append("Hash linking broken: execution parent_hash != blueprint artifact_hash")
        
        if "execution" in artifacts_by_type and "result" in artifacts_by_type:
            execution = artifacts_by_type["execution"]
            result = artifacts_by_type["result"]
            
            if result.get("parent_hash") != execution.get("artifact_hash"):
                issues.append("Hash linking broken: result parent_hash != execution artifact_hash")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "artifact_count": len(artifacts),
            "chain_complete": len(artifact_types) == 3 and all(t in artifact_types for t in required_types)
        }
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema registry information"""
        return {
            "version": self.schema_registry.get("version"),
            "artifact_types": list(self.schema_registry.get("artifact_types", {}).keys()),
            "bucket_contract_rules": self.schema_registry.get("bucket_contract", {}).get("rules", []),
            "insightflow_required_fields": self.schema_registry.get("insightflow_contract", {}).get("required_trace_fields", [])
        }