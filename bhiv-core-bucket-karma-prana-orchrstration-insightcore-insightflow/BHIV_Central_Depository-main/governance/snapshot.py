"""
BHIV Bucket v1 - Schema Snapshot
Document 02 - Baseline State Captured January 13, 2026
"""

from typing import Dict, List
from datetime import datetime, timezone

# Snapshot metadata
SNAPSHOT_DATE = "2026-01-13"
SNAPSHOT_VERSION = "1.0.0"

# MongoDB Schema Definitions
MONGODB_SCHEMAS = {
    "logs": {
        "collection": "logs",
        "schema": {
            "_id": "ObjectId",
            "agent": "string",
            "message": "string",
            "timestamp": "ISODate",
            "level": "string (info|warning|error)",
            "execution_id": "string (optional)",
            "basket_name": "string (optional)",
            "duration_ms": "number (optional)",
            "additional_details": "object (optional)"
        },
        "indexes": [
            {"field": "agent", "order": "ascending"},
            {"field": "timestamp", "order": "descending"},
            {"field": "execution_id", "order": "ascending"},
            {"field": "level", "order": "ascending"}
        ],
        "ttl": None
    }
}

# Redis Data Structure Definitions
REDIS_STRUCTURES = {
    "execution_logs": {
        "key_pattern": "execution:{execution_id}:logs",
        "type": "List<Dict>",
        "ttl_hours": 24,
        "structure": ["agent", "step", "data", "status", "timestamp"]
    },
    "agent_outputs": {
        "key_pattern": "execution:{execution_id}:outputs:{agent_name}",
        "type": "Dict",
        "ttl_hours": 1,
        "structure": ["result", "status", "timestamp"]
    },
    "agent_state": {
        "key_pattern": "agent:{agent_name}:state:{execution_id}",
        "type": "Dict",
        "ttl_hours": 1,
        "structure": "key-value state data"
    },
    "basket_execution": {
        "key_pattern": "basket:{basket_name}:execution:{execution_id}",
        "type": "Dict",
        "ttl_hours": 24,
        "structure": ["status", "agents_completed", "result", "errors"]
    },
    "basket_executions_list": {
        "key_pattern": "basket:{basket_name}:executions",
        "type": "List<str>",
        "ttl_hours": None,
        "max_items": 100,
        "description": "Rolling list of last 100 execution IDs"
    }
}

def get_snapshot_info() -> Dict:
    """Get snapshot metadata"""
    return {
        "snapshot_date": SNAPSHOT_DATE,
        "snapshot_version": SNAPSHOT_VERSION,
        "mongodb_collections": list(MONGODB_SCHEMAS.keys()),
        "redis_structures": list(REDIS_STRUCTURES.keys()),
        "captured_at": datetime.now(timezone.utc).isoformat()
    }

def validate_mongodb_schema(collection: str, document: Dict) -> Dict:
    """Validate document against snapshot schema"""
    if collection not in MONGODB_SCHEMAS:
        return {"valid": False, "reason": f"Unknown collection: {collection}"}
    
    schema = MONGODB_SCHEMAS[collection]["schema"]
    required_fields = ["agent", "message", "timestamp", "level"]
    
    for field in required_fields:
        if field not in document:
            return {"valid": False, "reason": f"Missing required field: {field}"}
    
    return {"valid": True, "reason": "Schema validation passed"}

def validate_redis_key(key: str) -> Dict:
    """Validate Redis key against snapshot patterns"""
    for structure_name, structure in REDIS_STRUCTURES.items():
        pattern = structure["key_pattern"]
        # Simple pattern matching
        if ":" in pattern:
            parts = pattern.split(":")
            key_parts = key.split(":")
            if len(parts) == len(key_parts):
                return {
                    "valid": True,
                    "structure": structure_name,
                    "ttl_hours": structure.get("ttl_hours")
                }
    
    return {"valid": False, "reason": "Key does not match any known pattern"}
