"""
Core-Bucket Integration Configuration
Manages connection settings and integration behavior
"""

import os
from typing import Dict, Any

# Integration settings
INTEGRATION_CONFIG = {
    # Bucket connection
    "bucket_url": os.getenv("BUCKET_URL", "http://localhost:8000"),
    "bucket_timeout": float(os.getenv("BUCKET_TIMEOUT", "2.0")),
    
    # Integration behavior
    "enable_bucket_writes": os.getenv("ENABLE_BUCKET_WRITES", "true").lower() == "true",
    "enable_bucket_reads": os.getenv("ENABLE_BUCKET_READS", "true").lower() == "true",
    "fail_silently": True,  # Core continues if Bucket fails
    
    # Event types to send to Bucket
    "tracked_events": [
        "rl_outcome",
        "agent_result", 
        "task_error",
        "agent_selection"
    ],
    
    # Core identity
    "core_identity": "bhiv_core_v1",
    
    # Retry settings (minimal)
    "max_retries": 1,
    "retry_delay": 0.1
}

def get_integration_config() -> Dict[str, Any]:
    """Get current integration configuration"""
    return INTEGRATION_CONFIG.copy()

def is_bucket_integration_enabled() -> bool:
    """Check if Bucket integration is enabled"""
    return INTEGRATION_CONFIG["enable_bucket_writes"] or INTEGRATION_CONFIG["enable_bucket_reads"]

def get_bucket_url() -> str:
    """Get Bucket URL"""
    return INTEGRATION_CONFIG["bucket_url"]