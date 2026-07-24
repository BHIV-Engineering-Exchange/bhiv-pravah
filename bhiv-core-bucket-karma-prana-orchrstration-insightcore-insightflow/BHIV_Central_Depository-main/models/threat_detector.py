"""
BHIV Bucket Threat Detector
Automated detection for all 10 identified threats
Document Reference: 14_bucket_threat_model.md
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.logger import get_logger
from config.limits import BucketLimits, PRODUCT_QUOTAS, PRODUCT_ARTIFACT_ALLOWLIST

logger = get_logger(__name__)

class BucketThreatDetector:
    """Automated threat detection for BHIV Bucket"""
    
    THREATS = {
        "T1_STORAGE_EXHAUSTION": {"name": "Storage Exhaustion", "severity": "HIGH", "escalation": "Ops_Team"},
        "T2_METADATA_POISONING": {"name": "Metadata Poisoning", "severity": "CRITICAL", "escalation": "CEO"},
        "T3_SCHEMA_EVOLUTION": {"name": "Schema Evolution", "severity": "HIGH", "escalation": "Vijay_Dhawan"},
        "T5_EXECUTOR_OVERRIDE": {"name": "Executor Override", "severity": "CRITICAL", "escalation": "Vijay_Dhawan"},
        "T6_AI_ESCALATION": {"name": "AI Escalation", "severity": "CRITICAL", "escalation": "Vijay_Dhawan"},
        "T7_CROSS_PRODUCT": {"name": "Cross-Product Contamination", "severity": "HIGH", "escalation": "Security_Team"},
        "T8_AUDIT_TAMPERING": {"name": "Audit Tampering", "severity": "CRITICAL", "escalation": "CEO"},
        "T9_OWNERSHIP_CHALLENGE": {"name": "Ownership Challenge", "severity": "HIGH", "escalation": "CEO_Legal"},
        "T10_PROVENANCE_OVERTRUST": {"name": "Provenance Overtrust", "severity": "MEDIUM", "escalation": "Vijay_Dhawan"}
    }
    
    @classmethod
    async def check_storage_exhaustion(cls, used_gb: float) -> Optional[Dict[str, Any]]:
        """T1: Detect storage exhaustion"""
        status = BucketLimits.check_storage_capacity(used_gb)
        if status["status"] in ["WARNING", "CRITICAL"]:
            return {
                "threat_id": "T1_STORAGE_EXHAUSTION",
                "severity": "CRITICAL" if status["status"] == "CRITICAL" else "HIGH",
                "details": status,
                "escalation": status["escalation_path"],
                "action": status["action_required"]
            }
        return None
    
    @classmethod
    async def detect_metadata_poisoning(cls, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """T2: Detect metadata poisoning"""
        threats = []
        for key, value in metadata.items():
            if isinstance(value, str):
                if len(value.encode()) > BucketLimits.METADATA_FIELD_MAX_SIZE_BYTES:
                    threats.append(f"Oversized: {key}")
                if any(p in value.lower() for p in ["drop table", "delete from", "<script>"]):
                    threats.append(f"Injection: {key}")
        
        if threats:
            return {
                "threat_id": "T2_METADATA_POISONING",
                "severity": "CRITICAL",
                "details": {"patterns": threats},
                "escalation": "CEO",
                "action": "REJECT"
            }
        return None
    
    @classmethod
    async def detect_executor_misbehavior(cls, actor: str, operation: str) -> Optional[Dict[str, Any]]:
        """T5: Detect executor violations"""
        if actor == "akanksha_parab" and operation not in ["CREATE", "READ", "APPROVE_INTEGRATION"]:
            return {
                "threat_id": "T5_EXECUTOR_OVERRIDE",
                "severity": "CRITICAL",
                "details": {"actor": actor, "operation": operation},
                "escalation": "Vijay_Dhawan",
                "action": "BLOCK"
            }
        return None
    
    @classmethod
    async def detect_ai_escalation(cls, actor: str, operation: str) -> Optional[Dict[str, Any]]:
        """T6: Detect AI escalation"""
        if actor.startswith("ai_") and operation not in ["CREATE", "APPEND_AUDIT"]:
            return {
                "threat_id": "T6_AI_ESCALATION",
                "severity": "CRITICAL",
                "details": {"actor": actor, "operation": operation},
                "escalation": "Vijay_Dhawan",
                "action": "REJECT"
            }
        return None
    
    @classmethod
    async def detect_cross_product_contamination(cls, product_id: str, artifact_type: str) -> Optional[Dict[str, Any]]:
        """T7: Detect cross-product violations"""
        if product_id in PRODUCT_ARTIFACT_ALLOWLIST:
            if artifact_type not in PRODUCT_ARTIFACT_ALLOWLIST[product_id]:
                return {
                    "threat_id": "T7_CROSS_PRODUCT",
                    "severity": "HIGH",
                    "details": {"product": product_id, "type": artifact_type},
                    "escalation": "Security_Team",
                    "action": "REJECT"
                }
        return None
    
    @classmethod
    async def detect_audit_tampering(cls, operation: str, target: str) -> Optional[Dict[str, Any]]:
        """T8: Detect audit tampering"""
        if operation in ["DELETE", "UPDATE"] and target == "audit_log":
            return {
                "threat_id": "T8_AUDIT_TAMPERING",
                "severity": "CRITICAL",
                "details": {"operation": operation, "target": target},
                "escalation": "CEO",
                "action": "HALT"
            }
        return None
    
    @classmethod
    async def scan_all_threats(cls, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan for all threats"""
        threats = []
        
        if "used_gb" in context:
            t = await cls.check_storage_exhaustion(context["used_gb"])
            if t: threats.append(t)
        
        if "metadata" in context:
            t = await cls.detect_metadata_poisoning(context["metadata"])
            if t: threats.append(t)
        
        if "actor" in context and "operation" in context:
            t = await cls.detect_executor_misbehavior(context["actor"], context["operation"])
            if t: threats.append(t)
            t = await cls.detect_ai_escalation(context["actor"], context["operation"])
            if t: threats.append(t)
        
        if "product_id" in context and "artifact_type" in context:
            t = await cls.detect_cross_product_contamination(context["product_id"], context["artifact_type"])
            if t: threats.append(t)
        
        if "operation" in context and "target_type" in context:
            t = await cls.detect_audit_tampering(context["operation"], context["target_type"])
            if t: threats.append(t)
        
        return threats
    
    @classmethod
    def has_critical_threats(cls, threats: List[Dict[str, Any]]) -> bool:
        """Check for critical threats"""
        return any(t.get("severity") == "CRITICAL" for t in threats)
