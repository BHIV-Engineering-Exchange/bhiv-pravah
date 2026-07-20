"""
BHIV Bucket Scale Limits Configuration
Defines all hard boundaries for production deployment
Document Reference: 15_scale_readiness_implementation.md
"""

from typing import Dict, Any, Tuple
from datetime import datetime

class BucketLimits:
    """
    Centralized scale limits for BHIV Bucket
    All limits are HARD BOUNDARIES - violations halt operations
    """
    
    # STORAGE LIMITS (Document 15)
    MAX_ARTIFACT_SIZE_MB = 500  # 500 MB per artifact (tested 2026-01-19)
    MAX_ARTIFACT_SIZE_BYTES = MAX_ARTIFACT_SIZE_MB * 1024 * 1024
    MAX_TOTAL_STORAGE_GB = 1000  # 1 TB total (Supabase tier spec)
    MAX_TOTAL_STORAGE_BYTES = MAX_TOTAL_STORAGE_GB * 1024 * 1024 * 1024
    
    # WRITE PERFORMANCE LIMITS
    MAX_CONCURRENT_WRITES = 100  # Load tested 2026-01-19
    SAFE_CONCURRENT_WRITES = 50  # Safe sustained level
    WARNING_CONCURRENT_WRITES = 75  # Warning threshold
    MAX_WRITE_THROUGHPUT_PER_SEC = 1000  # Calculated from DB pool
    SAFE_WRITE_THROUGHPUT_PER_SEC = 500  # Safe sustained rate
    
    # ARTIFACT COUNT LIMITS
    MAX_ARTIFACTS_PER_PRODUCT = 10_000_000  # 10M per product
    MAX_TOTAL_ARTIFACTS = 100_000_000  # 100M total
    WARNING_ARTIFACTS_PER_PRODUCT = 7_000_000  # 70% threshold
    
    # QUERY PERFORMANCE LIMITS
    MAX_QUERY_LATENCY_MS = 5000  # 5 seconds SLA
    SAFE_QUERY_LATENCY_MS = 1000  # Target latency
    WARNING_QUERY_LATENCY_MS = 3000  # Warning threshold
    
    # PRODUCT LIMITS
    MAX_PRODUCTS = 100  # Maximum products supported
    CERTIFIED_PRODUCTS = 4  # Currently certified
    
    # AUDIT TRAIL LIMITS
    AUDIT_RETENTION_DAYS = 2555  # 7 years (legal requirement)
    AUDIT_ENTRY_MAX_SIZE_KB = 100  # 100 KB per entry
    
    # METADATA LIMITS
    METADATA_FIELD_MAX_SIZE_KB = 16  # 16 KB per metadata field
    METADATA_FIELD_MAX_SIZE_BYTES = METADATA_FIELD_MAX_SIZE_KB * 1024
    
    @classmethod
    def validate_artifact_size(cls, size_bytes: int) -> Tuple[bool, str]:
        """Validate artifact size against limits"""
        if size_bytes > cls.MAX_ARTIFACT_SIZE_BYTES:
            return False, f"Artifact size {size_bytes} bytes exceeds limit of {cls.MAX_ARTIFACT_SIZE_BYTES} bytes ({cls.MAX_ARTIFACT_SIZE_MB} MB)"
        return True, "Size within limits"
    
    @classmethod
    def validate_metadata_size(cls, size_bytes: int) -> Tuple[bool, str]:
        """Validate metadata field size"""
        if size_bytes > cls.METADATA_FIELD_MAX_SIZE_BYTES:
            return False, f"Metadata field size {size_bytes} bytes exceeds limit of {cls.METADATA_FIELD_MAX_SIZE_BYTES} bytes ({cls.METADATA_FIELD_MAX_SIZE_KB} KB)"
        return True, "Metadata size within limits"
    
    @classmethod
    def check_concurrent_writes(cls, current: int) -> Dict[str, Any]:
        """Check concurrent writes status"""
        if current >= cls.MAX_CONCURRENT_WRITES:
            status = "RED"
            action = "PAUSE_NEW_WRITES"
        elif current >= cls.WARNING_CONCURRENT_WRITES:
            status = "ORANGE"
            action = "ALERT_OPS"
        elif current >= cls.SAFE_CONCURRENT_WRITES:
            status = "YELLOW"
            action = "MONITOR"
        else:
            status = "GREEN"
            action = "NONE"
        
        return {
            "current": current,
            "limit": cls.MAX_CONCURRENT_WRITES,
            "status": status,
            "action": action,
            "percentage": (current / cls.MAX_CONCURRENT_WRITES * 100) if cls.MAX_CONCURRENT_WRITES > 0 else 0
        }
    
    @classmethod
    def check_storage_capacity(cls, used_gb: float) -> Dict[str, Any]:
        """Check storage capacity with escalation paths"""
        usage_ratio = used_gb / cls.MAX_TOTAL_STORAGE_GB
        usage_percent = usage_ratio * 100
        
        if usage_ratio >= 0.99:
            status = "CRITICAL"
            action = "HALT_WRITES"
            escalation = "Ashmit_Pandey_and_Ops"
            timeline = "IMMEDIATE"
        elif usage_ratio >= 0.90:
            status = "WARNING"
            action = "PLAN_EXPANSION"
            escalation = "Ops_Team"
            timeline = "6_HOURS"
        elif usage_ratio >= 0.70:
            status = "CAUTION"
            action = "MONITOR_CLOSELY"
            escalation = "Ops_Team"
            timeline = "24_HOURS"
        else:
            status = "HEALTHY"
            action = "NONE"
            escalation = "NONE"
            timeline = "N/A"
        
        return {
            "status": status,
            "usage_ratio": usage_ratio,
            "usage_percent": round(usage_percent, 2),
            "used_gb": used_gb,
            "total_gb": cls.MAX_TOTAL_STORAGE_GB,
            "free_gb": cls.MAX_TOTAL_STORAGE_GB - used_gb,
            "action_required": action,
            "escalation_path": escalation,
            "response_timeline": timeline
        }
    
    @classmethod
    def get_all_limits(cls) -> Dict[str, Any]:
        """Get all limits as dictionary"""
        return {
            "storage": {
                "max_artifact_size_mb": cls.MAX_ARTIFACT_SIZE_MB,
                "max_total_storage_gb": cls.MAX_TOTAL_STORAGE_GB,
                "metadata_field_max_kb": cls.METADATA_FIELD_MAX_SIZE_KB
            },
            "performance": {
                "max_concurrent_writes": cls.MAX_CONCURRENT_WRITES,
                "safe_concurrent_writes": cls.SAFE_CONCURRENT_WRITES,
                "max_write_throughput_per_sec": cls.MAX_WRITE_THROUGHPUT_PER_SEC,
                "safe_write_throughput_per_sec": cls.SAFE_WRITE_THROUGHPUT_PER_SEC
            },
            "artifacts": {
                "max_per_product": cls.MAX_ARTIFACTS_PER_PRODUCT,
                "max_total": cls.MAX_TOTAL_ARTIFACTS
            },
            "query": {
                "max_latency_ms": cls.MAX_QUERY_LATENCY_MS,
                "safe_latency_ms": cls.SAFE_QUERY_LATENCY_MS
            },
            "audit": {
                "retention_days": cls.AUDIT_RETENTION_DAYS,
                "max_entry_size_kb": cls.AUDIT_ENTRY_MAX_SIZE_KB
            }
        }

# Product-specific quotas (Document 16)
PRODUCT_QUOTAS = {
    "AI_ASSISTANT": 400_000_000_000,  # 400 GB
    "AI_AVATAR": 300_000_000_000,     # 300 GB
    "GURUKUL": 200_000_000_000,       # 200 GB
    "ENFORCEMENT": 100_000_000_000    # 100 GB
}

# Product-to-artifact-type allowlist (Document 16)
PRODUCT_ARTIFACT_ALLOWLIST = {
    "AI_ASSISTANT": ["ConversationArtifact"],
    "AI_AVATAR": ["MediaArtifact"],
    "GURUKUL": ["ContentArtifact"],
    "ENFORCEMENT": ["DecisionArtifact"],
    "WORKFLOW": ["WorkflowArtifact"]
}

def validate_product_quota(product_id: str, current_usage: int) -> Tuple[bool, str]:
    """Validate product storage quota"""
    if product_id not in PRODUCT_QUOTAS:
        return False, f"Product {product_id} not registered"
    
    quota = PRODUCT_QUOTAS[product_id]
    if current_usage >= quota:
        return False, f"Product {product_id} quota exceeded: {current_usage} >= {quota}"
    
    usage_percent = (current_usage / quota * 100) if quota > 0 else 0
    if usage_percent >= 90:
        return True, f"WARNING: Product {product_id} at {usage_percent:.1f}% quota"
    
    return True, "Quota within limits"

def validate_product_artifact_type(product_id: str, artifact_type: str) -> Tuple[bool, str]:
    """Validate artifact type for product"""
    if product_id not in PRODUCT_ARTIFACT_ALLOWLIST:
        return False, f"Product {product_id} not registered"
    
    allowed_types = PRODUCT_ARTIFACT_ALLOWLIST[product_id]
    if artifact_type not in allowed_types:
        return False, f"Artifact type {artifact_type} not allowed for product {product_id}. Allowed: {allowed_types}"
    
    return True, "Artifact type allowed"
