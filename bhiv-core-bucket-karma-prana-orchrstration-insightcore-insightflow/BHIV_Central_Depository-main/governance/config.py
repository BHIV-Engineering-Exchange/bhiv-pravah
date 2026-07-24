"""
BHIV Bucket v1 Governance Configuration
Document 01 - Ownership & Custodianship Implementation
"""

from datetime import datetime
from typing import Dict

BUCKET_VERSION = "1.0.0"
BUCKET_EFFECTIVE_DATE = "2026-01-13"
PRIMARY_OWNER = "Ashmit"
EXECUTOR = "Akanksha"
TECHNICAL_ADVISOR = "Vijay Dhawan"

APPROVED_ARTIFACTS = [
    "agent_specifications",
    "basket_configurations",
    "execution_metadata",
    "agent_outputs",
    "logs",
    "state_data",
    "event_records",
    "configuration_metadata",
    "audit_trails"
]

REJECTED_ARTIFACTS = [
    "ai_model_weights",
    "video_files",
    "business_logic_code",
    "user_credentials",
    "long_term_application_state",
    "unstructured_binary_data",
    "user_personal_data_pii"
]

def get_bucket_info() -> Dict:
    return {
        "bucket_version": BUCKET_VERSION,
        "owner": PRIMARY_OWNER,
        "executor": EXECUTOR,
        "technical_advisor": TECHNICAL_ADVISOR,
        "effective_date": BUCKET_EFFECTIVE_DATE,
        "approved_artifacts": APPROVED_ARTIFACTS,
        "governance_active": True
    }

def validate_artifact_class(artifact_class: str) -> Dict:
    if artifact_class in APPROVED_ARTIFACTS:
        return {"approved": True, "reason": "Approved artifact class"}
    elif artifact_class in REJECTED_ARTIFACTS:
        return {"approved": False, "reason": f"Rejected: {artifact_class} not allowed in Bucket v1"}
    else:
        return {"approved": False, "reason": "Unknown artifact class - requires owner approval"}
