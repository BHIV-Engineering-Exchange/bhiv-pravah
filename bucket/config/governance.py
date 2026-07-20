"""
BHIV Bucket Governance Engine
Immutable governance rules enforced at code level
Document Reference: All governance documents (01-10, 14-18)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

class GovernanceEngine:
    """
    Immutable governance rules for BHIV Bucket
    These rules are CONSTITUTIONAL - cannot be relaxed without CEO approval
    """
    
    # IMMUTABLE GOVERNANCE RULES (10 core rules)
    IMMUTABLE_RULES = {
        "RULE_01_WRITE_ONLY": {
            "name": "Write-Only Semantics",
            "description": "Bucket accepts only CREATE operations, no UPDATE/DELETE",
            "enforcement": "architectural",
            "violation_action": "REJECT_IMMEDIATELY",
            "document_ref": "Document 18 - Section 1.1"
        },
        "RULE_02_APPEND_ONLY_AUDIT": {
            "name": "Append-Only Audit Trail",
            "description": "Audit trail is immutable, WORM enforced",
            "enforcement": "middleware",
            "violation_action": "HALT_OPERATIONS",
            "document_ref": "Document 18 - Section 1.2"
        },
        "RULE_03_SCHEMA_IMMUTABLE": {
            "name": "Schema Immutability",
            "description": "Schema cannot be modified without CEO approval",
            "enforcement": "governance_gate",
            "violation_action": "ESCALATE_TO_CEO",
            "document_ref": "Document 18 - Section 1.3"
        },
        "RULE_04_PROVENANCE_LOCKED": {
            "name": "Provenance Immutability",
            "description": "Artifact metadata cannot be modified after creation",
            "enforcement": "immutable_fields",
            "violation_action": "REJECT_IMMEDIATELY",
            "document_ref": "Document 18 - Section 1.4"
        },
        "RULE_05_PRODUCT_ISOLATION": {
            "name": "Product Isolation",
            "description": "Products cannot access each other's data",
            "enforcement": "middleware",
            "violation_action": "REJECT_AND_ALERT",
            "document_ref": "Document 16 - Section 3"
        },
        "RULE_06_GOVERNANCE_LOCKS": {
            "name": "Governance Violations Halt Operations",
            "description": "Any governance violation immediately halts operations",
            "enforcement": "automated",
            "violation_action": "HALT_AND_ESCALATE",
            "document_ref": "Document 18 - Section 1.6"
        },
        "RULE_07_LEGAL_DEFENSIBILITY": {
            "name": "Cryptographic Proof Required",
            "description": "All artifacts must have cryptographic integrity proof",
            "enforcement": "content_hashing",
            "violation_action": "REJECT_IMMEDIATELY",
            "document_ref": "Document 18 - Section 1.7"
        },
        "RULE_08_EXECUTOR_AUTHORITY": {
            "name": "Executor Authority Boundaries",
            "description": "Executor can only execute within defined scope",
            "enforcement": "authority_validation",
            "violation_action": "ESCALATE_TO_VIJAY",
            "document_ref": "Document 08 - Executor Lane"
        },
        "RULE_09_AI_WRITE_ONLY": {
            "name": "AI Write-Only Lock",
            "description": "AI agents can only CREATE, no other operations",
            "enforcement": "operation_validation",
            "violation_action": "ESCALATE_TO_VIJAY",
            "document_ref": "Document 17 - Scenario 2"
        },
        "RULE_10_ZERO_EXCEPTIONS": {
            "name": "Zero Governance Exceptions",
            "description": "No temporary governance relaxation allowed",
            "enforcement": "constitutional",
            "violation_action": "CEO_OVERRIDE_ONLY",
            "document_ref": "Document 18 - Section 2.4"
        }
    }
    
    # ALLOWED OPERATIONS (by actor type)
    ALLOWED_OPERATIONS = {
        "ai_agent": ["CREATE", "APPEND_AUDIT"],
        "executor": ["CREATE", "READ", "APPROVE_INTEGRATION"],
        "product": ["CREATE", "READ"],
        "auditor": ["READ"],
        "admin": ["CREATE", "READ", "MANAGE_GOVERNANCE"]
    }
    
    # FORBIDDEN OPERATIONS (always blocked)
    FORBIDDEN_OPERATIONS = ["UPDATE", "DELETE", "MODIFY_SCHEMA", "MODIFY_AUDIT"]
    
    @classmethod
    def validate_operation(cls, actor: str, operation: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate if operation is allowed for actor
        Returns: {"allowed": bool, "reason": str, "rule_violated": str or None}
        """
        context = context or {}
        
        # Check if operation is globally forbidden
        if operation in cls.FORBIDDEN_OPERATIONS:
            return {
                "allowed": False,
                "reason": f"Operation {operation} is forbidden by governance",
                "rule_violated": "RULE_01_WRITE_ONLY",
                "action": "REJECT_IMMEDIATELY"
            }
        
        # Determine actor type
        actor_type = cls._get_actor_type(actor)
        
        # Check if operation is allowed for actor type
        allowed_ops = cls.ALLOWED_OPERATIONS.get(actor_type, [])
        if operation not in allowed_ops:
            rule_violated = "RULE_08_EXECUTOR_AUTHORITY" if actor_type == "executor" else "RULE_09_AI_WRITE_ONLY"
            return {
                "allowed": False,
                "reason": f"Operation {operation} not allowed for {actor_type}",
                "rule_violated": rule_violated,
                "action": "ESCALATE_TO_VIJAY"
            }
        
        return {
            "allowed": True,
            "reason": "Operation allowed",
            "rule_violated": None,
            "action": "PROCEED"
        }
    
    @classmethod
    def validate_write_operation(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate write operation against all governance rules
        Returns: {"valid": bool, "violations": List[str], "action": str}
        """
        violations = []
        
        # RULE_04: Check provenance fields are present
        required_provenance = ["created_by", "created_at", "product_id", "artifact_type"]
        for field in required_provenance:
            if field not in data:
                violations.append(f"RULE_04_PROVENANCE_LOCKED: Missing required field {field}")
        
        # RULE_05: Check product_id is valid
        product_id = data.get("product_id")
        if not product_id:
            violations.append("RULE_05_PRODUCT_ISOLATION: product_id required")
        
        # RULE_07: Check content_hash is present
        if "content_hash" not in data and "data" in data:
            violations.append("RULE_07_LEGAL_DEFENSIBILITY: content_hash required for cryptographic proof")
        
        if violations:
            return {
                "valid": False,
                "violations": violations,
                "action": "REJECT_IMMEDIATELY"
            }
        
        return {
            "valid": True,
            "violations": [],
            "action": "PROCEED"
        }
    
    @classmethod
    def check_escalation_needed(cls, violation: str) -> Dict[str, Any]:
        """
        Determine escalation path for governance violation
        Returns: {"escalate_to": str, "timeline": str, "severity": str}
        """
        escalation_map = {
            "RULE_01_WRITE_ONLY": {"escalate_to": "Ops_Team", "timeline": "IMMEDIATE", "severity": "CRITICAL"},
            "RULE_02_APPEND_ONLY_AUDIT": {"escalate_to": "CEO", "timeline": "IMMEDIATE", "severity": "CRITICAL"},
            "RULE_03_SCHEMA_IMMUTABLE": {"escalate_to": "CEO", "timeline": "24_HOURS", "severity": "HIGH"},
            "RULE_04_PROVENANCE_LOCKED": {"escalate_to": "Ops_Team", "timeline": "IMMEDIATE", "severity": "HIGH"},
            "RULE_05_PRODUCT_ISOLATION": {"escalate_to": "Security_Team", "timeline": "1_HOUR", "severity": "CRITICAL"},
            "RULE_06_GOVERNANCE_LOCKS": {"escalate_to": "CEO", "timeline": "IMMEDIATE", "severity": "CRITICAL"},
            "RULE_07_LEGAL_DEFENSIBILITY": {"escalate_to": "Legal_Counsel", "timeline": "24_HOURS", "severity": "HIGH"},
            "RULE_08_EXECUTOR_AUTHORITY": {"escalate_to": "Vijay_Dhawan", "timeline": "IMMEDIATE", "severity": "CRITICAL"},
            "RULE_09_AI_WRITE_ONLY": {"escalate_to": "Vijay_Dhawan", "timeline": "IMMEDIATE", "severity": "CRITICAL"},
            "RULE_10_ZERO_EXCEPTIONS": {"escalate_to": "CEO", "timeline": "IMMEDIATE", "severity": "CRITICAL"}
        }
        
        return escalation_map.get(violation, {
            "escalate_to": "Ashmit_Pandey",
            "timeline": "IMMEDIATE",
            "severity": "CRITICAL"
        })
    
    @classmethod
    def validate_product_isolation(cls, product_id: str, target_product_id: str) -> Dict[str, Any]:
        """Validate product isolation (RULE_05)"""
        if product_id != target_product_id:
            return {
                "valid": False,
                "reason": f"Cross-product access denied: {product_id} cannot access {target_product_id}",
                "rule_violated": "RULE_05_PRODUCT_ISOLATION",
                "action": "REJECT_AND_ALERT"
            }
        
        return {
            "valid": True,
            "reason": "Product isolation maintained",
            "rule_violated": None,
            "action": "PROCEED"
        }
    
    @classmethod
    def validate_schema_change(cls, change_request: Dict[str, Any]) -> Dict[str, Any]:
        """Validate schema change request (RULE_03)"""
        return {
            "valid": False,
            "reason": "Schema changes require CEO approval",
            "rule_violated": "RULE_03_SCHEMA_IMMUTABLE",
            "action": "ESCALATE_TO_CEO",
            "approval_required": "CEO",
            "timeline": "24_HOURS"
        }
    
    @classmethod
    def get_all_rules(cls) -> Dict[str, Any]:
        """Get all governance rules"""
        return cls.IMMUTABLE_RULES
    
    @classmethod
    def get_rule_details(cls, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get details for specific rule"""
        return cls.IMMUTABLE_RULES.get(rule_id)
    
    @classmethod
    def _get_actor_type(cls, actor: str) -> str:
        """Determine actor type from actor string"""
        if actor.startswith("ai_"):
            return "ai_agent"
        elif actor == "akanksha_parab":
            return "executor"
        elif actor.startswith("product_"):
            return "product"
        elif actor.startswith("auditor_"):
            return "auditor"
        elif actor in ["ashmit_pandey", "vijay_dhawan"]:
            return "admin"
        else:
            return "product"  # Default to most restrictive

# Governance validation helper functions
def validate_governance_compliance(operation: str, actor: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Complete governance validation for any operation
    Returns: {"compliant": bool, "violations": List, "action": str}
    """
    violations = []
    
    # Validate operation is allowed
    op_validation = GovernanceEngine.validate_operation(actor, operation, data)
    if not op_validation["allowed"]:
        violations.append(op_validation)
    
    # Validate write operation if applicable
    if operation == "CREATE":
        write_validation = GovernanceEngine.validate_write_operation(data)
        if not write_validation["valid"]:
            violations.append(write_validation)
    
    # Validate product isolation if applicable
    if "product_id" in data and "target_product_id" in data:
        isolation_validation = GovernanceEngine.validate_product_isolation(
            data["product_id"],
            data["target_product_id"]
        )
        if not isolation_validation["valid"]:
            violations.append(isolation_validation)
    
    if violations:
        return {
            "compliant": False,
            "violations": violations,
            "action": "HALT_OPERATIONS",
            "escalation_required": True
        }
    
    return {
        "compliant": True,
        "violations": [],
        "action": "PROCEED",
        "escalation_required": False
    }

def log_governance_violation(violation: Dict[str, Any], context: Dict[str, Any]):
    """Log governance violation for audit trail"""
    logger.critical(f"GOVERNANCE_VIOLATION: {violation}")
    logger.critical(f"Context: {context}")
    
    # Determine escalation
    rule_violated = violation.get("rule_violated")
    if rule_violated:
        escalation = GovernanceEngine.check_escalation_needed(rule_violated)
        logger.critical(f"Escalation: {escalation}")
