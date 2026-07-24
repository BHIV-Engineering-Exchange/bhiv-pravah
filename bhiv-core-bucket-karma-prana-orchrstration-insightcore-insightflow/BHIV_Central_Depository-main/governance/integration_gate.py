"""
Document 07: Integration Gate Checklist
Integration approval process and criteria
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from enum import Enum

class ApprovalStatus(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"
    PENDING = "pending"

# Integration request requirements
INTEGRATION_REQUIREMENTS = {
    "integration_overview": {
        "required": True,
        "fields": ["system_name", "purpose", "owner_contact", "timeline"],
        "description": "System name, purpose (1-2 sentences), owner/team contact, timeline/urgency"
    },
    "data_requirements": {
        "required": True,
        "fields": ["bucket_data_needed", "usage_description", "access_frequency"],
        "description": "What Bucket data needed, how used, frequency of access"
    },
    "architecture_diagram": {
        "required": True,
        "fields": ["connection_method", "data_flow", "reverse_dependencies"],
        "description": "How system connects to Bucket, data flow (one-way), any reverse dependencies"
    },
    "api_usage_plan": {
        "required": True,
        "fields": ["endpoints", "call_frequency", "error_handling", "timeout_handling"],
        "description": "Which endpoints, call frequency/volume, error handling, timeout handling"
    },
    "error_handling_document": {
        "required": True,
        "fields": ["bucket_down_strategy", "error_response_strategy", "slow_response_strategy", "graceful_degradation"],
        "description": "What if Bucket is down/errors/slow, how system degrades gracefully"
    }
}

# 50-item approval checklist
APPROVAL_CHECKLIST = {
    "section_a_requirements": {
        "name": "Requirements Completeness",
        "items": [
            "integration_overview_provided",
            "data_requirements_specified",
            "architecture_diagram_provided",
            "api_usage_plan_documented",
            "error_handling_plan_provided"
        ],
        "decision": "If ANY missing → Request and wait. Do not proceed."
    },
    "section_b_directionality": {
        "name": "Data Directionality",
        "items": [
            "data_flows_one_way",
            "no_reverse_dependency",
            "no_bidirectional_coupling",
            "system_works_if_bucket_down",
            "no_embedded_bucket_logic"
        ],
        "decision": "If ANY fail → REJECT. One-way requirement is non-negotiable."
    },
    "section_c_artifacts": {
        "name": "Artifact Classes Validation",
        "items": [
            "only_approved_artifact_classes",
            "not_storing_rejected_classes",
            "data_size_reasonable",
            "no_pii_or_credentials",
            "no_binary_or_video_files"
        ],
        "decision": "If ANY fail → REJECT. Artifact classes are defined boundaries."
    },
    "section_d_provenance": {
        "name": "Provenance Understanding",
        "items": [
            "understands_bucket_guarantees",
            "acknowledges_gaps",
            "not_relying_on_phase2_features",
            "willing_to_implement_own_audit",
            "can_document_assumptions"
        ],
        "decision": "If ANY fail → Request clarification. You need informed consent."
    },
    "section_e_retention": {
        "name": "Data Retention Compliance",
        "items": [
            "understands_1year_retention",
            "agrees_1hour_redis_ttl",
            "gdpr_process_understood",
            "will_handle_deletion_requests",
            "no_indefinite_storage_requirement"
        ],
        "decision": "If ANY fail → REJECT or negotiate. Retention is non-negotiable."
    },
    "section_f_security": {
        "name": "Security & Compliance",
        "items": [
            "https_only",
            "no_credentials_in_urls",
            "rate_limiting_implemented",
            "no_excessive_caching",
            "understands_no_hipaa_pci_compliance"
        ],
        "decision": "If ANY fail → REJECT. Security is mandatory."
    },
    "section_g_architecture": {
        "name": "Integration Architecture",
        "items": [
            "architecture_diagram_approved",
            "no_circular_dependencies",
            "clear_ownership",
            "monitoring_alerting_plan",
            "graceful_degradation_plan"
        ],
        "decision": "If ANY fail → Request redesign."
    },
    "section_h_testing": {
        "name": "Testing & Validation",
        "items": [
            "load_testing_done",
            "error_scenario_testing_done",
            "end_to_end_testing_done",
            "rollback_plan_documented",
            "performance_acceptable"
        ],
        "decision": "If ANY fail → Request testing before approval."
    },
    "section_i_documentation": {
        "name": "Documentation & Support",
        "items": [
            "integration_documented",
            "runbook_created",
            "support_model_clear"
        ],
        "decision": "If ANY fail → Request documentation."
    },
    "section_j_governance": {
        "name": "Ongoing Governance",
        "items": [
            "agrees_to_notify_changes",
            "will_participate_quarterly_review"
        ],
        "decision": "If ANY fail → Add as approval condition."
    }
}

# Blocking criteria (automatic rejection)
BLOCKING_CRITERIA = {
    "bidirectional_dependency": {
        "description": "Bucket calls back to your system",
        "severity": "critical"
    },
    "rejected_artifact_classes": {
        "description": "Trying to store rejected artifact classes",
        "severity": "critical"
    },
    "pii_without_anonymization": {
        "description": "Contains PII without anonymization plan",
        "severity": "critical"
    },
    "reverse_dependency_on_availability": {
        "description": "Reverse dependency on Bucket availability",
        "severity": "critical"
    },
    "no_error_handling": {
        "description": "No error handling documented",
        "severity": "critical"
    },
    "violates_one_way_flow": {
        "description": "Violates one-way data flow",
        "severity": "critical"
    },
    "requires_unavailable_guarantees": {
        "description": "Requires data integrity guarantees Bucket doesn't provide",
        "severity": "critical"
    },
    "embedded_bucket_logic": {
        "description": "Embedded Bucket business logic (belongs in agent)",
        "severity": "critical"
    }
}

# Approval timeline
APPROVAL_TIMELINE = {
    "day_1": "Team submits integration request",
    "day_2": "Ashmit checks completeness, requests missing info or approves",
    "day_3_5": "Team provides clarification if needed",
    "day_6_7": "Ashmit makes final decision (approve/reject/conditional)",
    "approved": "Team can begin implementation",
    "max_timeline_days": 7
}

# Quick reference: what gets approved
APPROVAL_LIKELIHOOD = {
    "likely_approved": [
        "read_only_access_to_execution_data",
        "using_only_approved_artifact_classes",
        "one_way_data_flow",
        "clear_error_handling",
        "reasonable_volume_under_1000_calls_per_day"
    ],
    "likely_rejected": [
        "bidirectional_coupling",
        "storing_pii_without_anonymization",
        "relying_on_phase2_guarantees",
        "no_error_handling",
        "very_high_volume_over_10000_calls_per_day_without_planning"
    ],
    "likely_conditional": [
        "high_volume_integration_approve_if_monitoring",
        "personally_identifiable_data_approve_if_anonymized",
        "novel_use_case_approve_if_documented_properly"
    ]
}


def get_integration_requirements() -> Dict[str, Any]:
    """Get integration request requirements"""
    return {
        "requirements": INTEGRATION_REQUIREMENTS,
        "note": "All requirements are mandatory before Ashmit will review"
    }


def get_approval_checklist() -> Dict[str, Any]:
    """Get 50-item approval checklist"""
    total_items = sum(len(section["items"]) for section in APPROVAL_CHECKLIST.values())
    return {
        "checklist": APPROVAL_CHECKLIST,
        "total_items": total_items,
        "sections": len(APPROVAL_CHECKLIST)
    }


def get_blocking_criteria() -> Dict[str, Any]:
    """Get automatic rejection criteria"""
    return {
        "blocking_criteria": BLOCKING_CRITERIA,
        "count": len(BLOCKING_CRITERIA),
        "note": "If ANY of these are true, integration is REJECTED immediately"
    }


def get_approval_timeline() -> Dict[str, Any]:
    """Get approval timeline"""
    return {
        "timeline": APPROVAL_TIMELINE,
        "max_days": APPROVAL_TIMELINE["max_timeline_days"]
    }


def get_approval_likelihood() -> Dict[str, Any]:
    """Get quick reference for approval likelihood"""
    return {
        "likely_approved": APPROVAL_LIKELIHOOD["likely_approved"],
        "likely_rejected": APPROVAL_LIKELIHOOD["likely_rejected"],
        "likely_conditional": APPROVAL_LIKELIHOOD["likely_conditional"]
    }


def validate_integration_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate integration request completeness"""
    missing_requirements = []
    incomplete_requirements = []
    
    for req_name, req_info in INTEGRATION_REQUIREMENTS.items():
        if req_name not in request_data:
            missing_requirements.append(req_name)
        else:
            # Check if all required fields are present
            req_data = request_data[req_name]
            missing_fields = [field for field in req_info["fields"] if field not in req_data]
            if missing_fields:
                incomplete_requirements.append({
                    "requirement": req_name,
                    "missing_fields": missing_fields
                })
    
    is_complete = len(missing_requirements) == 0 and len(incomplete_requirements) == 0
    
    return {
        "complete": is_complete,
        "missing_requirements": missing_requirements,
        "incomplete_requirements": incomplete_requirements,
        "decision": "PROCEED" if is_complete else "REQUEST_MORE_INFO"
    }


def validate_checklist_section(section_name: str, checklist_data: Dict[str, bool]) -> Dict[str, Any]:
    """Validate a specific checklist section"""
    if section_name not in APPROVAL_CHECKLIST:
        return {"error": f"Unknown section: {section_name}"}
    
    section = APPROVAL_CHECKLIST[section_name]
    items = section["items"]
    
    passed_items = []
    failed_items = []
    
    for item in items:
        if checklist_data.get(item, False):
            passed_items.append(item)
        else:
            failed_items.append(item)
    
    all_passed = len(failed_items) == 0
    
    return {
        "section": section_name,
        "section_name": section["name"],
        "passed": all_passed,
        "passed_items": passed_items,
        "failed_items": failed_items,
        "decision": section["decision"],
        "total_items": len(items),
        "passed_count": len(passed_items)
    }


def check_blocking_criteria(integration_data: Dict[str, Any]) -> Dict[str, Any]:
    """Check if integration meets any blocking criteria"""
    violations = []
    
    # Check each blocking criterion
    if integration_data.get("bidirectional_dependency", False):
        violations.append("bidirectional_dependency")
    
    if integration_data.get("uses_rejected_artifacts", False):
        violations.append("rejected_artifact_classes")
    
    if integration_data.get("has_pii_without_anonymization", False):
        violations.append("pii_without_anonymization")
    
    if integration_data.get("reverse_dependency", False):
        violations.append("reverse_dependency_on_availability")
    
    if not integration_data.get("has_error_handling", True):
        violations.append("no_error_handling")
    
    if integration_data.get("violates_one_way_flow", False):
        violations.append("violates_one_way_flow")
    
    if integration_data.get("requires_unavailable_guarantees", False):
        violations.append("requires_unavailable_guarantees")
    
    if integration_data.get("has_embedded_bucket_logic", False):
        violations.append("embedded_bucket_logic")
    
    is_blocked = len(violations) > 0
    
    return {
        "blocked": is_blocked,
        "violations": violations,
        "violation_details": [BLOCKING_CRITERIA[v] for v in violations],
        "decision": "REJECT" if is_blocked else "CONTINUE_REVIEW"
    }


def generate_approval_decision(
    system_name: str,
    status: str,
    rationale: str,
    conditions: Optional[List[str]] = None,
    owner_contact: Optional[str] = None
) -> Dict[str, Any]:
    """Generate approval decision document"""
    decision = {
        "decision": status.upper(),
        "date": datetime.now(timezone.utc).isoformat(),
        "approved_by": "Ashmit",
        "integration": f"{system_name} → Bucket API",
        "rationale": rationale,
        "go_live_checklist": [
            "architecture_diagram_reviewed",
            "testing_completed",
            "monitoring_in_place",
            "documentation_done",
            "ashmit_sign_off"
        ],
        "points_of_contact": {
            "integration_owner": owner_contact or "Not provided",
            "bucket_owner": "Ashmit"
        }
    }
    
    if conditions:
        decision["conditions"] = conditions
    
    return decision


def generate_rejection_feedback(
    system_name: str,
    issues: List[Dict[str, str]],
    path_forward: List[str]
) -> Dict[str, Any]:
    """Generate rejection feedback document"""
    return {
        "decision": "REJECTED",
        "date": datetime.now(timezone.utc).isoformat(),
        "reviewed_by": "Ashmit",
        "system_name": system_name,
        "reason_for_rejection": f"Integration does not meet approval criteria ({len(issues)} issues found)",
        "specific_issues": issues,
        "path_forward": path_forward,
        "next_steps": [
            "team_reviews_feedback",
            "team_resolves_issues",
            "team_resubmits_for_review"
        ]
    }


def calculate_approval_deadline(submission_date: Optional[datetime] = None) -> Dict[str, Any]:
    """Calculate approval timeline deadlines"""
    if submission_date is None:
        submission_date = datetime.now(timezone.utc)
    
    return {
        "submission_date": submission_date.isoformat(),
        "completeness_check": (submission_date + timedelta(days=1)).isoformat(),
        "clarification_period_end": (submission_date + timedelta(days=5)).isoformat(),
        "final_decision": (submission_date + timedelta(days=7)).isoformat(),
        "max_timeline_days": 7
    }


def get_conditional_approval_examples() -> Dict[str, Any]:
    """Get examples of conditional approvals"""
    return {
        "example_1_anonymization": {
            "condition": "We approve storing Persona configs IF data is anonymized",
            "requirement": "Submit anonymization proof before deployment",
            "timeline": "2 weeks"
        },
        "example_2_monitoring": {
            "condition": "We approve high-volume integration IF monitoring is in place",
            "requirement": "Deploy monitoring, alert on errors",
            "timeline": "Must have before go-live"
        },
        "example_3_versioning": {
            "condition": "We approve integration IF you version your API consumers",
            "requirement": "Submit versioning plan",
            "timeline": "Before next API change"
        }
    }
