"""
BHIV Bucket v1 - Integration Boundary Validation
Document 03 - Integration Policy Enforcement
"""

from typing import Dict, List
from datetime import datetime

# Integration patterns
ALLOWED_PATTERNS = [
    "synchronous_request_response",
    "polling_for_status"
]

FORBIDDEN_PATTERNS = [
    "webhook_push",
    "bidirectional_coupling",
    "reverse_dependency"
]

# Data flow rules
DATA_FLOW_RULES = {
    "allowed_direction": "external_to_bucket",
    "forbidden_direction": "bucket_to_external",
    "principle": "one_way_only"
}

def validate_integration_pattern(pattern: str) -> Dict:
    """Validate if integration pattern is allowed"""
    if pattern in ALLOWED_PATTERNS:
        return {
            "valid": True,
            "pattern": pattern,
            "reason": "Approved integration pattern"
        }
    elif pattern in FORBIDDEN_PATTERNS:
        return {
            "valid": False,
            "pattern": pattern,
            "reason": f"Forbidden pattern: {pattern} not supported in v1.0.0"
        }
    else:
        return {
            "valid": False,
            "pattern": pattern,
            "reason": "Unknown pattern - requires owner approval"
        }

def validate_data_flow(direction: str) -> Dict:
    """Validate data flow direction"""
    if direction == "external_to_bucket":
        return {
            "valid": True,
            "direction": direction,
            "reason": "Correct one-way flow"
        }
    elif direction == "bucket_to_external":
        return {
            "valid": False,
            "direction": direction,
            "reason": "Forbidden: Bucket does not push to external systems"
        }
    else:
        return {
            "valid": False,
            "direction": direction,
            "reason": "Unknown direction"
        }

def get_integration_requirements() -> Dict:
    """Get mandatory integration requirements"""
    return {
        "requirements": [
            "own_input_output_mapping",
            "stateless_design",
            "handle_bucket_latency",
            "implement_error_handling",
            "document_data_usage"
        ],
        "latency_expectations": {
            "api_response": "<100ms",
            "single_agent": "0.1-2s",
            "two_agent_basket": "0.2-5s",
            "financial_coordinator": "1-30s"
        },
        "error_handling": {
            "network_errors": "required",
            "http_errors": "required",
            "timeout_errors": "required",
            "data_validation": "required"
        }
    }

def get_boundary_definition() -> Dict:
    """Get Bucket boundary definition"""
    return {
        "accepts": [
            "agent_specifications",
            "basket_configurations",
            "agent_input_data_json",
            "execution_requests_rest"
        ],
        "returns": [
            "agent_execution_results",
            "basket_workflow_results",
            "execution_metadata",
            "status_codes_and_errors"
        ],
        "does_not_accept": [
            "binary_data",
            "video_files",
            "large_files",
            "unstructured_documents",
            "user_credentials"
        ],
        "does_not_provide": [
            "push_notifications",
            "webhooks",
            "realtime_streams",
            "user_authentication",
            "rbac"
        ]
    }

def validate_integration_checklist(checklist: Dict) -> Dict:
    """Validate integration approval checklist"""
    required_checks = [
        "one_way_data_flow",
        "no_reverse_dependency",
        "no_bidirectional_coupling",
        "external_system_independent",
        "error_handling_in_external",
        "data_mapping_documented",
        "bucket_api_read_only"
    ]
    
    missing_checks = []
    for check in required_checks:
        if not checklist.get(check, False):
            missing_checks.append(check)
    
    if not missing_checks:
        return {
            "valid": True,
            "reason": "All required checks passed",
            "approved": True
        }
    else:
        return {
            "valid": False,
            "reason": f"Missing checks: {', '.join(missing_checks)}",
            "approved": False,
            "missing_checks": missing_checks
        }
