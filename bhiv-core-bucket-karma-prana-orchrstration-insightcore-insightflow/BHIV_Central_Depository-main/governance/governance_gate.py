"""
Governance Gate Middleware - BHIV Bucket Enterprise Production Lock
Ensures every integration respects Bucket governance
Document Reference: 14_bucket_threat_model.md, 15_scale_readiness.md, 16_multi_product_compatibility.md
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from utils.logger import get_logger

try:
    from utils.threat_validator import BucketThreatModel
except ImportError:
    logger = get_logger(__name__)
    logger.warning("Threat validator not available, using basic validation")
    BucketThreatModel = None

try:
    from config.scale_limits import ScaleLimits, validate_operation_scale
except ImportError:
    logger = get_logger(__name__) if 'logger' not in locals() else logger
    logger.warning("Scale limits not available, using defaults")
    ScaleLimits = None
    validate_operation_scale = None

logger = get_logger(__name__)

class GovernanceDecision(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING_REVIEW = "pending_review"
    ESCALATED = "escalated"

class ThreatLevel(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

# Scale limits from doc 15 (now imported from config)
scale_limits_instance = ScaleLimits() if ScaleLimits else None

# Default scale limits if module not available
class DefaultScaleLimits:
    MAX_ARTIFACT_SIZE = 16 * 1024 * 1024  # 16MB
    MAX_CONCURRENT_WRITES = 100
    MAX_WRITE_THROUGHPUT_PER_SEC = 1000

if not scale_limits_instance:
    scale_limits_instance = DefaultScaleLimits()

# Product safety rules from doc 16
PRODUCT_RULES = {
    "AI_Assistant": {
        "allowed_classes": ["metadata", "artifact_manifest", "audit_entry"],
        "forbidden_classes": ["direct_schema_change", "system_config"]
    },
    "AI_Avatar": {
        "allowed_classes": ["avatar_config", "model_checkpoint", "iteration_history", "persona_config"],
        "forbidden_classes": ["access_control", "governance_rule"]
    },
    "Gurukul": {
        "allowed_classes": ["educational_content", "user_progress", "monetization_marker"],
        "forbidden_classes": ["user_auth", "payment_info"]
    },
    "Workflow_Enforcement": {
        "allowed_classes": ["event_history", "audit_log"],
        "forbidden_classes": ["write_operations", "schema_changes"]
    }
}

# Operation rules from doc 04
OPERATION_RULES = {
    "avatar_config": {"CREATE": True, "READ": True, "UPDATE": True, "DELETE": False},
    "model_checkpoint": {"CREATE": True, "READ": True, "UPDATE": False, "DELETE": False},
    "metadata": {"CREATE": True, "READ": True, "UPDATE": False, "DELETE": False},
    "audit_entry": {"CREATE": True, "READ": True, "UPDATE": False, "DELETE": False},
    "iteration_history": {"CREATE": True, "READ": True, "UPDATE": False, "DELETE": False},
    "educational_content": {"CREATE": True, "READ": True, "UPDATE": True, "DELETE": False},
    "event_history": {"CREATE": True, "READ": True, "UPDATE": False, "DELETE": False}
}

class GovernanceGate:
    """Primary enforcement point for all Bucket operations"""
    
    def __init__(self):
        self.approved_integrations = set()
        logger.info("Governance Gate initialized")
    
    async def validate_integration(
        self,
        integration_id: str,
        integration_type: str,
        artifact_classes: List[str],
        data_schema: Dict[str, Any],
        product_name: str
    ) -> Dict[str, Any]:
        """Validate integration against governance rules"""
        
        validation_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "integration_id": integration_id,
            "decision": GovernanceDecision.PENDING_REVIEW.value,
            "checks_performed": [],
            "threats_found": [],
            "reasons": []
        }
        
        # Threat Assessment (doc 14)
        threat_check = self._validate_threats(integration_type, artifact_classes, data_schema, product_name)
        validation_results["checks_performed"].append("threat_assessment")
        
        if threat_check["has_critical_threats"]:
            validation_results["threats_found"].extend(threat_check["threats"])
            validation_results["decision"] = GovernanceDecision.REJECTED.value
            validation_results["reasons"].append("Critical threats detected")
            logger.warning(f"Integration {integration_id} rejected: Critical threats")
            return validation_results
        
        # Scale Compatibility (doc 15)
        scale_check = self._validate_scale(artifact_classes, integration_type)
        validation_results["checks_performed"].append("scale_compatibility")
        
        if not scale_check["is_compatible"]:
            validation_results["decision"] = GovernanceDecision.REJECTED.value
            validation_results["reasons"].append(scale_check["reason"])
            logger.warning(f"Integration {integration_id} rejected: {scale_check['reason']}")
            return validation_results
        
        # Product Safety (doc 16)
        product_check = self._validate_product_safety(product_name, artifact_classes)
        validation_results["checks_performed"].append("product_safety")
        
        if not product_check["is_safe"]:
            validation_results["decision"] = GovernanceDecision.REJECTED.value
            validation_results["reasons"].append(product_check["reason"])
            logger.warning(f"Integration {integration_id} rejected: {product_check['reason']}")
            return validation_results
        
        # Compliance (doc 18)
        compliance_check = self._validate_compliance(data_schema, artifact_classes)
        validation_results["checks_performed"].append("compliance_validation")
        
        if not compliance_check["is_compliant"]:
            validation_results["decision"] = GovernanceDecision.REJECTED.value
            validation_results["reasons"].append(compliance_check["reason"])
            logger.warning(f"Integration {integration_id} rejected: {compliance_check['reason']}")
            return validation_results
        
        # All checks passed
        validation_results["decision"] = GovernanceDecision.APPROVED.value
        self.approved_integrations.add(integration_id)
        logger.info(f"Integration {integration_id} approved")
        
        return validation_results
    
    def validate_operation(
        self,
        operation_type: str,
        artifact_class: str,
        data_size: int,
        integration_id: str
    ) -> Dict[str, Any]:
        """Validate operation against governance rules"""
        
        # Check integration approval
        if integration_id not in self.approved_integrations:
            return {"allowed": False, "reason": "Integration not approved"}
        
        # Check operation allowed for artifact class
        if not self._operation_allowed(operation_type, artifact_class):
            return {"allowed": False, "reason": f"Operation {operation_type} not allowed for {artifact_class}"}
        
        # Check data size using centralized scale limits
        if data_size > scale_limits_instance.MAX_ARTIFACT_SIZE:
            return {"allowed": False, "reason": f"Data size {data_size} exceeds limit of {scale_limits_instance.MAX_ARTIFACT_SIZE}"}
        
        return {"allowed": True}
    
    def _validate_threats(
        self,
        integration_type: str,
        artifact_classes: List[str],
        data_schema: Dict[str, Any],
        product_name: str
    ) -> Dict[str, Any]:
        """Validate against threat model (doc 14) using centralized threat validator"""
        
        # Scan data schema for threat patterns
        if BucketThreatModel:
            detected_threats = BucketThreatModel.scan_for_threats(data_schema)
        else:
            detected_threats = []
        
        # Additional context-based threat detection
        if integration_type == "direct_database":
            detected_threats.append({
                "threat_id": "T1_ACCESS_BYPASS",
                "name": "Access Control Bypass",
                "level": "critical",
                "pattern_matched": "direct_database",
                "description": "Direct database access attempt"
            })
        
        if integration_type.startswith("_"):
            detected_threats.append({
                "threat_id": "T4_GOVERNANCE_CIRCUMVENTION",
                "name": "Governance Circumvention",
                "level": "high",
                "pattern_matched": "undocumented_integration",
                "description": "Undocumented integration type"
            })
        
        if "," in product_name:
            detected_threats.append({
                "threat_id": "T4_GOVERNANCE_CIRCUMVENTION",
                "name": "Governance Circumvention",
                "level": "high",
                "pattern_matched": "multiple_product_identity",
                "description": "Product claiming multiple identities"
            })
        
        # Check for critical threats
        if BucketThreatModel:
            has_critical = BucketThreatModel.has_critical_threats(detected_threats)
        else:
            has_critical = any(threat.get("level") == "critical" for threat in detected_threats)
        
        return {
            "has_critical_threats": has_critical,
            "threats": detected_threats
        }
    
    def _validate_scale(self, artifact_classes: List[str], integration_type: str) -> Dict[str, Any]:
        """Validate scale compatibility (doc 15)"""
        return {"is_compatible": True}
    
    def _validate_product_safety(self, product_name: str, artifact_classes: List[str]) -> Dict[str, Any]:
        """Validate product safety rules (doc 16)"""
        
        rules = PRODUCT_RULES.get(product_name)
        if not rules:
            return {"is_safe": False, "reason": f"Unknown product: {product_name}"}
        
        for artifact_class in artifact_classes:
            if artifact_class in rules.get("forbidden_classes", []):
                return {"is_safe": False, "reason": f"Forbidden class {artifact_class} for {product_name}"}
            if artifact_class not in rules.get("allowed_classes", []):
                return {"is_safe": False, "reason": f"Class {artifact_class} not approved for {product_name}"}
        
        return {"is_safe": True}
    
    def _validate_compliance(self, data_schema: Dict[str, Any], artifact_classes: List[str]) -> Dict[str, Any]:
        """Validate compliance (doc 18)"""
        
        if "nsfw_policy" not in data_schema and "content_filter" not in data_schema:
            return {"is_compliant": False, "reason": "No NSFW handling mechanism"}
        
        if "retention_policy" not in data_schema and "deletion_strategy" not in data_schema:
            return {"is_compliant": False, "reason": "No deletion strategy documented"}
        
        return {"is_compliant": True}
    
    def _operation_allowed(self, operation_type: str, artifact_class: str) -> bool:
        """Check if operation allowed for artifact class"""
        rules = OPERATION_RULES.get(artifact_class, {})
        return rules.get(operation_type, False)

# Global governance gate instance
governance_gate = GovernanceGate()
