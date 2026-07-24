"""
BHIV Bucket Scale Limits Configuration
Implements scale limits from Document 15 (Scale Readiness)
"""

from typing import Dict, Tuple, Any
from utils.logger import get_logger

logger = get_logger(__name__)

class ScaleLimits:
    """Centralized scale limits and capacity management"""
    
    # Storage Limits (from Document 15)
    MAX_TOTAL_STORAGE_GB = 1000  # 1TB total
    MAX_ARTIFACT_SIZE = 16 * 1024 * 1024  # 16MB per artifact
    STORAGE_WARNING_THRESHOLD = 0.90  # 90% capacity
    STORAGE_CRITICAL_THRESHOLD = 0.99  # 99% capacity
    
    # Write Performance Limits
    MAX_WRITE_THROUGHPUT_PER_SEC = 1000  # Maximum writes per second
    SAFE_WRITE_THROUGHPUT_PER_SEC = 500  # Safe sustained rate
    WARNING_WRITE_THROUGHPUT_PER_SEC = 900  # Warning threshold
    MAX_CONCURRENT_WRITES = 100  # Maximum concurrent writers
    SAFE_CONCURRENT_WRITES = 50  # Safe concurrent writers
    
    # Read Performance Limits
    MAX_READ_THROUGHPUT_PER_SEC = 100  # Maximum reads per second
    SAFE_READ_THROUGHPUT_PER_SEC = 50  # Safe sustained rate
    MAX_CONCURRENT_READS = 50  # Maximum concurrent readers
    SAFE_CONCURRENT_READS = 20  # Safe concurrent readers
    
    # Artifact Limits
    MAX_ARTIFACTS_PER_PRODUCT = 10_000_000  # 10M artifacts per product
    MAX_TOTAL_ARTIFACTS = 100_000_000  # 100M total artifacts
    WARNING_ARTIFACTS_PER_PRODUCT = 7_000_000  # 70% of limit
    
    # Product Limits
    MAX_PRODUCTS = 100  # Maximum number of products
    MAX_TEAMS = 1000  # Maximum number of teams
    
    # Query Performance
    MAX_QUERY_LATENCY_MS = 200  # Maximum acceptable query latency
    SAFE_QUERY_LATENCY_MS = 50  # Target query latency
    WARNING_QUERY_LATENCY_MS = 100  # Warning threshold
    MAX_RESULT_SET_SIZE = 5000  # Maximum results per query
    SAFE_RESULT_SET_SIZE = 1000  # Safe result set size
    
    # Retention
    AUDIT_RETENTION_YEARS = 7  # Audit log retention
    ARTIFACT_RETENTION_DAYS = 90  # Default artifact retention
    
    # Batch Operations
    MAX_BATCH_SIZE = 500  # Maximum batch operation size
    SAFE_BATCH_SIZE = 100  # Safe batch size
    
    # What Scales Safely
    SCALES_SAFELY = [
        "Number of artifact types (unlimited)",
        "Number of products (up to 100)",
        "Number of teams (up to 1000)",
        "Artifact count per product (up to 10M)",
        "Audit log retention (7 years unlimited entries)"
    ]
    
    # What Does Not Scale
    DOES_NOT_SCALE = [
        "Real-time queries across all products",
        "Distributed read-heavy operations (>100 reads/sec)",
        "Multi-region replication",
        "Full-text search",
        "Real-time analytics"
    ]
    
    # What Must Never Be Assumed
    NEVER_ASSUME = [
        "Eventual consistency without bounds",
        "Automatic schema migrations",
        "Backfill on failure",
        "Infinite storage",
        "Zero-downtime upgrades"
    ]
    
    @classmethod
    def get_all_limits(cls) -> Dict[str, Any]:
        """Get all scale limits"""
        return {
            "storage": {
                "max_total_gb": cls.MAX_TOTAL_STORAGE_GB,
                "max_artifact_size": cls.MAX_ARTIFACT_SIZE,
                "warning_threshold": cls.STORAGE_WARNING_THRESHOLD,
                "critical_threshold": cls.STORAGE_CRITICAL_THRESHOLD
            },
            "write_performance": {
                "max_throughput_per_sec": cls.MAX_WRITE_THROUGHPUT_PER_SEC,
                "safe_throughput_per_sec": cls.SAFE_WRITE_THROUGHPUT_PER_SEC,
                "max_concurrent": cls.MAX_CONCURRENT_WRITES,
                "safe_concurrent": cls.SAFE_CONCURRENT_WRITES
            },
            "read_performance": {
                "max_throughput_per_sec": cls.MAX_READ_THROUGHPUT_PER_SEC,
                "safe_throughput_per_sec": cls.SAFE_READ_THROUGHPUT_PER_SEC,
                "max_concurrent": cls.MAX_CONCURRENT_READS,
                "safe_concurrent": cls.SAFE_CONCURRENT_READS
            },
            "artifacts": {
                "max_per_product": cls.MAX_ARTIFACTS_PER_PRODUCT,
                "max_total": cls.MAX_TOTAL_ARTIFACTS,
                "warning_per_product": cls.WARNING_ARTIFACTS_PER_PRODUCT
            },
            "products": {
                "max_products": cls.MAX_PRODUCTS,
                "max_teams": cls.MAX_TEAMS
            },
            "query": {
                "max_latency_ms": cls.MAX_QUERY_LATENCY_MS,
                "safe_latency_ms": cls.SAFE_QUERY_LATENCY_MS,
                "max_result_set": cls.MAX_RESULT_SET_SIZE
            }
        }
    
    @classmethod
    def validate_artifact_size(cls, size_bytes: int) -> Tuple[bool, str]:
        """Validate artifact size against limits"""
        if size_bytes > cls.MAX_ARTIFACT_SIZE:
            return False, f"Artifact size {size_bytes} exceeds limit of {cls.MAX_ARTIFACT_SIZE}"
        return True, "Size within limits"
    
    @classmethod
    def validate_write_rate(cls, writes_per_sec: int) -> Tuple[bool, str]:
        """Validate write rate against limits"""
        if writes_per_sec > cls.MAX_WRITE_THROUGHPUT_PER_SEC:
            return False, f"Write rate {writes_per_sec}/sec exceeds limit of {cls.MAX_WRITE_THROUGHPUT_PER_SEC}/sec"
        elif writes_per_sec > cls.WARNING_WRITE_THROUGHPUT_PER_SEC:
            return True, f"Write rate {writes_per_sec}/sec approaching limit (warning)"
        return True, "Write rate within safe limits"
    
    @classmethod
    def validate_concurrent_writes(cls, concurrent_count: int) -> Tuple[bool, str]:
        """Validate concurrent write count"""
        if concurrent_count > cls.MAX_CONCURRENT_WRITES:
            return False, f"Concurrent writes {concurrent_count} exceeds limit of {cls.MAX_CONCURRENT_WRITES}"
        elif concurrent_count > cls.SAFE_CONCURRENT_WRITES:
            return True, f"Concurrent writes {concurrent_count} approaching limit (warning)"
        return True, "Concurrent writes within safe limits"
    
    @classmethod
    def check_storage_capacity(cls, used_gb: float, total_gb: float = None) -> Dict[str, Any]:
        """Check storage capacity status with escalation paths"""
        if total_gb is None:
            total_gb = cls.MAX_TOTAL_STORAGE_GB
        
        usage_ratio = used_gb / total_gb if total_gb > 0 else 0
        
        if usage_ratio >= cls.STORAGE_CRITICAL_THRESHOLD:
            status = "CRITICAL"
            action = "HALT_WRITES"
            escalation = "Ashmit_Pandey_and_Ops"
            timeline = "IMMEDIATE"
        elif usage_ratio >= cls.STORAGE_WARNING_THRESHOLD:
            status = "WARNING"
            action = "PLAN_EXPANSION"
            escalation = "Ops_Team"
            timeline = "6_HOURS"
        else:
            status = "HEALTHY"
            action = "NONE"
            escalation = "NONE"
            timeline = "N/A"
        
        return {
            "status": status,
            "usage_ratio": usage_ratio,
            "usage_percent": round(usage_ratio * 100, 2),
            "used_gb": used_gb,
            "total_gb": total_gb,
            "free_gb": total_gb - used_gb,
            "action_required": action,
            "escalation_path": escalation,
            "response_timeline": timeline
        }

def get_scale_limits_dict() -> Dict[str, Any]:
    """Get scale limits as dictionary"""
    return ScaleLimits.get_all_limits()

def get_performance_targets_dict() -> Dict[str, Any]:
    """Get performance targets"""
    return {
        "write_latency_p99_ms": 100,
        "read_latency_p99_ms": 50,
        "query_latency_p99_ms": 200,
        "availability_target": 0.999,  # 99.9% uptime
        "durability_target": 0.999999999  # 9 nines
    }

def validate_operation_scale(operation_type: str, data_size: int, frequency: int) -> Tuple[bool, str]:
    """Validate if operation is within scale limits"""
    limits = ScaleLimits()
    
    # Validate data size
    if data_size > limits.MAX_ARTIFACT_SIZE:
        return False, f"Data size {data_size} exceeds limit of {limits.MAX_ARTIFACT_SIZE}"
    
    # Validate frequency
    if operation_type == "write":
        if frequency > limits.MAX_WRITE_THROUGHPUT_PER_SEC:
            return False, f"Write frequency {frequency}/sec exceeds limit of {limits.MAX_WRITE_THROUGHPUT_PER_SEC}/sec"
    elif operation_type == "read":
        if frequency > limits.MAX_READ_THROUGHPUT_PER_SEC:
            return False, f"Read frequency {frequency}/sec exceeds limit of {limits.MAX_READ_THROUGHPUT_PER_SEC}/sec"
    
    return True, "Operation within scale limits"

def check_scale_limit_proximity(current_value: int, limit_name: str) -> Dict[str, Any]:
    """Check how close current value is to scale limit"""
    limits = ScaleLimits()
    
    limit_map = {
        "artifacts_per_product": limits.MAX_ARTIFACTS_PER_PRODUCT,
        "total_artifacts": limits.MAX_TOTAL_ARTIFACTS,
        "products": limits.MAX_PRODUCTS,
        "teams": limits.MAX_TEAMS,
        "concurrent_writes": limits.MAX_CONCURRENT_WRITES,
        "concurrent_reads": limits.MAX_CONCURRENT_READS
    }
    
    if limit_name not in limit_map:
        return {"error": f"Unknown limit: {limit_name}"}
    
    limit_value = limit_map[limit_name]
    usage_ratio = current_value / limit_value if limit_value > 0 else 0
    
    if usage_ratio >= 0.90:
        status = "CRITICAL"
    elif usage_ratio >= 0.70:
        status = "WARNING"
    else:
        status = "HEALTHY"
    
    return {
        "limit_name": limit_name,
        "current_value": current_value,
        "limit_value": limit_value,
        "usage_ratio": usage_ratio,
        "usage_percent": usage_ratio * 100,
        "remaining": limit_value - current_value,
        "status": status
    }
