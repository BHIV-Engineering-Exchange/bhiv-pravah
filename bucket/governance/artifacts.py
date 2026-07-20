"""
BHIV Bucket v1 - Artifact Admission Policy
Document 04 - Artifact Class Definitions and Validation
"""

from typing import Dict, List
from datetime import datetime

# Approved Artifact Classes (12 classes)
APPROVED_ARTIFACT_CLASSES = {
    "agent_specifications": {
        "status": "approved",
        "description": "JSON defining agent metadata, schema, capabilities",
        "location": "agents/{agent_name}/agent_spec.json",
        "retention": "permanent",
        "constraint": "Must be valid JSON matching agent_spec schema",
        "max_size": "1MB"
    },
    "basket_configurations": {
        "status": "approved",
        "description": "JSON defining workflow (agent sequence, strategy)",
        "location": "baskets/{basket_name}.json",
        "retention": "permanent",
        "constraint": "Must reference existing agents",
        "max_size": "1MB"
    },
    "execution_metadata": {
        "status": "approved",
        "description": "Execution ID, timestamps, status, duration",
        "location": "Redis (1hr TTL), MongoDB (permanent)",
        "retention": "1-24 hours Redis, 1 year MongoDB",
        "constraint": "Auto-generated, no manual creation",
        "max_size": "10KB"
    },
    "agent_outputs": {
        "status": "approved",
        "description": "JSON result from single agent execution",
        "location": "Redis (1hr TTL), MongoDB logs",
        "retention": "1 hour Redis, 1 year MongoDB",
        "constraint": "Max 10MB per output (soft limit)",
        "max_size": "10MB"
    },
    "logs": {
        "status": "approved",
        "description": "Timestamped event records",
        "location": "Files (application.log, executions.log)",
        "retention": "Files permanent, rolled over",
        "constraint": "Append-only in files",
        "max_size": "unlimited"
    },
    "state_data": {
        "status": "approved",
        "description": "Optional persistence data between executions",
        "location": "Redis (1hr TTL)",
        "retention": "1 hour (agent-scoped)",
        "constraint": "Optional, per-agent decision",
        "max_size": "1MB"
    },
    "event_records": {
        "status": "approved",
        "description": "Agent event history (input/output events)",
        "location": "Redis, MongoDB",
        "retention": "1 hour Redis, varies MongoDB",
        "constraint": "Published via EventBus",
        "max_size": "10MB"
    },
    "configuration_metadata": {
        "status": "approved",
        "description": "Point-in-time config for audit trail",
        "location": "Logs, MongoDB",
        "retention": "With execution logs",
        "constraint": "Immutable once recorded",
        "max_size": "1MB"
    },
    "audit_trails": {
        "status": "approved",
        "description": "Who did what, when (limited version)",
        "location": "Execution logs with user context",
        "retention": "1 year",
        "constraint": "Limited (no user tracking yet)",
        "max_size": "10MB"
    },
    "error_records": {
        "status": "approved",
        "description": "Exception details, stack traces, failure info",
        "location": "errors.log, MongoDB",
        "retention": "1 year",
        "constraint": "PII must be redacted",
        "max_size": "10MB"
    },
    "performance_metrics": {
        "status": "approved",
        "description": "Execution duration, throughput, latency",
        "location": "Logs, MongoDB",
        "retention": "1 month to 1 year",
        "constraint": "Aggregate only, no per-user",
        "max_size": "1MB"
    },
    "agent_dependency_metadata": {
        "status": "approved",
        "description": "Agent version, dependencies, compatibility info",
        "location": "agent_spec.json",
        "retention": "permanent",
        "constraint": "Read-only reference",
        "max_size": "1MB"
    }
}

# Conditional Artifact Classes
CONDITIONAL_ARTIFACT_CLASSES = {
    "persona_configurations": {
        "status": "conditional",
        "description": "Avatar system persona definitions",
        "when_approved": "IF properly anonymized, IF no PII",
        "when_rejected": "If contains user data, credentials, or private info",
        "constraint": "Requires special review, anonymization proof",
        "review_status": "pending_specification"
    }
}

# Rejected Artifact Classes
REJECTED_ARTIFACT_CLASSES = {
    "ai_model_weights": {
        "status": "rejected",
        "reason": "Too large (GBs), not metadata, belongs in model storage",
        "alternative": "Store reference to model version, not the weights",
        "example": '{"model": "gpt-4", "version": "2026-01"}'
    },
    "video_files": {
        "status": "rejected",
        "reason": "Binary, large, streaming-specific, not orchestration data",
        "alternative": "Store reference to video URL or video_id",
        "example": '{"video_id": "abc123"}'
    },
    "business_logic_code": {
        "status": "rejected",
        "reason": "Belongs in agent implementations, not storage",
        "alternative": "Store agent_spec (metadata), not code itself",
        "example": "agent_spec.json describes what code does, not the code"
    },
    "user_credentials": {
        "status": "rejected",
        "reason": "Security risk, belongs in secret management",
        "alternative": "Reference credential by key, manage separately",
        "example": '{"credential_ref": "api_key_123"}'
    },
    "long_term_application_state": {
        "status": "rejected",
        "reason": "Not orchestration metadata, belongs in app databases",
        "alternative": "Store orchestration state, not application state",
        "example": "Store execution history, not user preferences"
    },
    "unstructured_binary_data": {
        "status": "rejected",
        "reason": "Not structured, large, not execution/provenance related",
        "alternative": "Store reference to binary object storage",
        "example": '{"s3_bucket": "...", "key": "..."}'
    },
    "user_personal_data_pii": {
        "status": "rejected",
        "reason": "Compliance, privacy, not orchestration data",
        "alternative": "Reference user by ID, manage PII separately",
        "example": '{"user_id": "12345"}'
    },
    "unversioned_breaking_data": {
        "status": "rejected",
        "reason": "No versioning strategy, could break consumers",
        "alternative": "Version schema changes, migrate carefully",
        "example": "Use v1, v2 naming for incompatible changes"
    }
}

def get_artifact_admission_policy() -> Dict:
    """Get complete artifact admission policy"""
    return {
        "approved_classes": list(APPROVED_ARTIFACT_CLASSES.keys()),
        "conditional_classes": list(CONDITIONAL_ARTIFACT_CLASSES.keys()),
        "rejected_classes": list(REJECTED_ARTIFACT_CLASSES.keys()),
        "total_approved": len(APPROVED_ARTIFACT_CLASSES),
        "total_conditional": len(CONDITIONAL_ARTIFACT_CLASSES),
        "total_rejected": len(REJECTED_ARTIFACT_CLASSES)
    }

def get_artifact_details(artifact_class: str) -> Dict:
    """Get detailed information about an artifact class"""
    if artifact_class in APPROVED_ARTIFACT_CLASSES:
        return {
            "artifact_class": artifact_class,
            "status": "approved",
            **APPROVED_ARTIFACT_CLASSES[artifact_class]
        }
    elif artifact_class in CONDITIONAL_ARTIFACT_CLASSES:
        return {
            "artifact_class": artifact_class,
            "status": "conditional",
            **CONDITIONAL_ARTIFACT_CLASSES[artifact_class]
        }
    elif artifact_class in REJECTED_ARTIFACT_CLASSES:
        return {
            "artifact_class": artifact_class,
            "status": "rejected",
            **REJECTED_ARTIFACT_CLASSES[artifact_class]
        }
    else:
        return {
            "artifact_class": artifact_class,
            "status": "unknown",
            "reason": "Not in policy - requires owner approval"
        }

def validate_artifact_admission(artifact_class: str, data: Dict = None) -> Dict:
    """Validate if artifact can be admitted to Bucket"""
    details = get_artifact_details(artifact_class)
    
    if details["status"] == "approved":
        # Check size constraint if data provided
        if data and "max_size" in details:
            # Simplified size check (would need actual implementation)
            return {
                "admitted": True,
                "artifact_class": artifact_class,
                "reason": "Approved artifact class",
                "retention": details.get("retention"),
                "location": details.get("location")
            }
        return {
            "admitted": True,
            "artifact_class": artifact_class,
            "reason": "Approved artifact class"
        }
    elif details["status"] == "conditional":
        return {
            "admitted": False,
            "artifact_class": artifact_class,
            "reason": "Conditional approval required",
            "requirements": details.get("when_approved"),
            "action": "Submit for special review"
        }
    elif details["status"] == "rejected":
        return {
            "admitted": False,
            "artifact_class": artifact_class,
            "reason": details.get("reason"),
            "alternative": details.get("alternative"),
            "example": details.get("example")
        }
    else:
        return {
            "admitted": False,
            "artifact_class": artifact_class,
            "reason": "Unknown artifact class",
            "action": "Submit to owner for approval"
        }

def get_decision_criteria() -> Dict:
    """Get artifact admission decision criteria"""
    return {
        "criteria": [
            {
                "question": "Is it metadata or application data?",
                "rule": "Metadata = approved, Application = rejected",
                "explanation": "Metadata = Orchestration, provenance, execution context"
            },
            {
                "question": "Is it structured (JSON/YAML) or binary?",
                "rule": "Structured = approved, Binary = rejected",
                "explanation": "Structured can be stored as-is, Binary needs object storage"
            },
            {
                "question": "Does it relate to execution/orchestration?",
                "rule": "Yes = approved, No = rejected",
                "explanation": "Bucket is for orchestration, not general storage"
            },
            {
                "question": "What's the size?",
                "rule": "<10MB = approved, >100MB = rejected",
                "explanation": "Small items only, large items need separate storage"
            },
            {
                "question": "Does it contain sensitive data?",
                "rule": "Anonymized = approved, Sensitive = rejected",
                "explanation": "PII must be anonymized, credentials externalized"
            }
        ]
    }
