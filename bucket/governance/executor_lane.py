"""
Document 08: Executor Lane (Akanksha)
Define execution boundaries for Akanksha
"""

from typing import Dict, List, Any, Optional
from enum import Enum

class ChangeCategory(Enum):
    CAN_EXECUTE = "can_execute"
    REQUIRES_APPROVAL = "requires_approval"
    FORBIDDEN = "forbidden"

# Executor role definition
EXECUTOR_ROLE = {
    "name": "Akanksha",
    "title": "Executor",
    "authority": {
        "can_do": [
            "implement_approved_decisions",
            "code_test_deploy_maintain",
            "make_day_to_day_technical_decisions"
        ],
        "cannot_do": [
            "change_governance_policies",
            "approve_new_artifact_classes",
            "weaken_provenance_guarantees",
            "skip_reviews"
        ]
    }
}

# Changes that can be executed without approval
CAN_EXECUTE_WITHOUT_APPROVAL = {
    "refactoring": {
        "description": "Code quality improvements",
        "allowed": [
            "rename_variables_functions",
            "reorganize_code_structure",
            "improve_test_coverage",
            "add_documentation",
            "fix_code_style",
            "remove_dead_code"
        ],
        "boundary": "Pure refactoring. Logic must not change."
    },
    "non_breaking_schema_extensions": {
        "description": "Add optional fields without breaking existing data",
        "allowed": [
            "add_new_optional_fields_json",
            "add_new_optional_agent",
            "extend_logging_add_fields",
            "new_query_indices_performance"
        ],
        "boundary": "Existing data still works. No migration needed."
    },
    "new_api_endpoints": {
        "description": "Add new endpoints without changing existing ones",
        "allowed": [
            "new_metrics_endpoint",
            "new_analytics_endpoint",
            "new_health_detailed_endpoint"
        ],
        "boundary": "Doesn't change existing endpoints. Doesn't affect baskets/agents."
    },
    "test_coverage": {
        "description": "Improve testing",
        "allowed": [
            "add_unit_tests",
            "add_integration_tests",
            "add_performance_tests",
            "fix_flaky_tests"
        ],
        "boundary": "Tests don't change code behavior, only verify it."
    },
    "documentation": {
        "description": "Documentation improvements",
        "allowed": [
            "readme_updates",
            "code_comments",
            "architecture_docs",
            "runbooks_operations",
            "integration_guides"
        ],
        "boundary": "Pure documentation, no code changes."
    },
    "performance_optimization": {
        "description": "Improve performance without changing behavior",
        "allowed": [
            "optimize_database_queries",
            "add_caching",
            "improve_api_response_time",
            "reduce_memory_usage"
        ],
        "boundary": "Output must be identical. No behavior change."
    },
    "dependency_updates": {
        "description": "Update dependencies (patch versions only)",
        "allowed": [
            "update_libraries_patch_versions",
            "security_patches",
            "bug_fixes_in_deps"
        ],
        "boundary": "Patch and minor versions only. Test thoroughly."
    },
    "operational_changes": {
        "description": "Operational configuration changes",
        "allowed": [
            "modify_log_rotation_config",
            "adjust_redis_ttls_within_policy",
            "scale_database_connections",
            "change_deployment_parameters"
        ],
        "boundary": "Within existing policy. If you need to change policy, escalate."
    },
    "monitoring_observability": {
        "description": "Add monitoring without changing behavior",
        "allowed": [
            "add_prometheus_metrics",
            "add_logging",
            "add_alerts",
            "improve_debugging"
        ],
        "boundary": "Doesn't change Bucket behavior."
    }
}

# Changes that require Ashmit's approval
REQUIRES_APPROVAL = {
    "schema_changes_breaking": {
        "description": "Remove/rename fields, change field types",
        "reason": "Changes existing data format. Consumers may break.",
        "process": [
            "you_propose_change_with_migration_plan",
            "ashmit_reviews_impact",
            "ashmit_approves_with_versioning_strategy",
            "you_implement_with_migration",
            "you_test_migration_thoroughly"
        ]
    },
    "new_agent_addition": {
        "description": "Adding a new agent to Bucket",
        "reason": "Changes agent inventory, affects all consumers.",
        "process": [
            "you_implement_agent_code",
            "ashmit_reviews_agent_spec",
            "ashmit_approves_or_requests_changes",
            "you_update_agent_spec_json",
            "you_deploy_with_registration"
        ]
    },
    "basket_configuration_changes": {
        "description": "Change agent order, add new basket",
        "reason": "Changes orchestration logic, affects consumers.",
        "process": [
            "you_propose_change_with_rationale",
            "ashmit_reviews_impact",
            "ashmit_approves_or_suggests_alternatives",
            "you_implement_and_test",
            "you_deploy"
        ]
    },
    "provenance_guarantee_changes": {
        "description": "Reduce log retention, remove audit trail, change TTLs",
        "reason": "Affects what Bucket guarantees.",
        "process": [
            "you_propose_with_rationale",
            "ashmit_consults_compliance_vijay_if_needed",
            "ashmit_decides_may_require_phase2_planning",
            "you_implement_if_approved"
        ]
    },
    "api_endpoint_changes_breaking": {
        "description": "Change request format, remove endpoint",
        "reason": "Breaks existing integrations.",
        "process": [
            "you_propose_with_migration_plan",
            "ashmit_reviews_impact_on_integrations",
            "ashmit_approves_versioning_strategy",
            "you_implement_v1_and_v2_both_work",
            "you_sunset_v1_after_migration_window"
        ]
    },
    "major_dependency_updates": {
        "description": "Major version updates (e.g., FastAPI 0.100 → 1.0)",
        "reason": "May introduce breaking changes.",
        "process": [
            "you_test_in_staging_document_breaking_changes",
            "ashmit_reviews_breaking_changes",
            "ashmit_approves_update",
            "you_deploy_carefully_with_rollback_plan"
        ]
    },
    "storage_layer_changes": {
        "description": "Add MongoDB sharding, change Redis cluster",
        "reason": "Affects scalability and reliability.",
        "process": [
            "you_propose_with_capacity_analysis",
            "ashmit_consults_vijay_if_complex",
            "ashmit_approves_plan",
            "you_execute_with_testing_and_rollback"
        ]
    },
    "retention_policy_changes": {
        "description": "Change retention periods (e.g., 1 year → 6 months)",
        "reason": "Policy decision, affects compliance.",
        "process": [
            "you_propose_with_rationale",
            "ashmit_reviews_compliance_impact",
            "ashmit_decides_may_consult_legal_compliance",
            "you_implement_if_approved"
        ]
    }
}

# Forbidden actions
FORBIDDEN_ACTIONS = {
    "owner_authority": {
        "description": "Cannot exercise owner authority",
        "forbidden": [
            "approve_reject_integrations",
            "change_governance_documents",
            "set_bucket_policy",
            "override_ashmit_decisions"
        ],
        "reason": "Ashmit owns Bucket. You don't."
    },
    "bypass_reviews": {
        "description": "Cannot bypass review processes",
        "forbidden": [
            "merge_without_code_review",
            "deploy_without_testing",
            "bypass_approval_gates",
            "push_directly_to_main"
        ],
        "reason": "Quality and safety depend on review."
    },
    "unsafe_deployment": {
        "description": "Cannot deploy unsafely",
        "forbidden": [
            "deploy_without_rollback_plan",
            "deploy_to_production_untested",
            "deploy_during_critical_hours",
            "deploy_multiple_changes_together_untested"
        ],
        "reason": "Bucket affects all teams. Failure impacts everyone."
    },
    "data_deletion": {
        "description": "Cannot delete data without formal process",
        "forbidden": [
            "delete_logs_without_formal_process",
            "hard_delete_data_only_ashmit_can_authorize",
            "modify_past_execution_data",
            "bypass_retention_policy"
        ],
        "reason": "Audit trail integrity requires formal process."
    },
    "change_governance_without_process": {
        "description": "Cannot change governance unilaterally",
        "forbidden": [
            "update_governance_docs_unilaterally",
            "change_approval_criteria",
            "weaken_provenance_guarantees",
            "promise_phase2_features_as_current"
        ],
        "reason": "Governance must be intentional, documented, consistent."
    },
    "scope_creep": {
        "description": "Cannot add unapproved features",
        "forbidden": [
            "add_features_ashmit_didnt_approve",
            "store_new_artifact_classes",
            "change_integration_boundaries",
            "modify_approved_baskets_without_approval"
        ],
        "reason": "These are policy decisions, not technical decisions."
    }
}

# Code review checkpoints
CODE_REVIEW_CHECKPOINTS = {
    "checkpoint_1": {
        "name": "Does This Change Require Approval?",
        "check": "Read section 2 & 3 - CAN_EXECUTE vs REQUIRES_APPROVAL",
        "action": "If approval needed → Include @ashmit in PR. If not → Proceed with review"
    },
    "checkpoint_2": {
        "name": "Is the Code Quality Good?",
        "checks": [
            "tests_added_for_new_code",
            "documentation_updated_if_needed",
            "no_dead_code",
            "no_security_issues",
            "follows_code_style"
        ]
    },
    "checkpoint_3": {
        "name": "Will This Break Anything?",
        "checks": [
            "backward_compatibility_checked",
            "api_contracts_honored",
            "dependency_versions_compatible",
            "database_migrations_tested_if_needed"
        ]
    },
    "checkpoint_4": {
        "name": "Is the Approach Sound?",
        "checks": [
            "solution_makes_sense_architecturally",
            "no_over_engineering",
            "no_under_engineering",
            "maintainable_long_term"
        ]
    },
    "checkpoint_5": {
        "name": "Who Reviews?",
        "reviewers": {
            "code_quality": "any_team_member",
            "approval_decisions": "ashmit_if_needed",
            "architecture": "ashmit_if_complex"
        }
    }
}

# Success metrics
SUCCESS_METRICS = {
    "code_quality": "Code is clean and well-tested",
    "deployment_safety": "Deployments are smooth and safe",
    "scope_discipline": "Zero surprise scope changes",
    "approval_rate": "Ashmit approves >90% of PRs quickly",
    "stability": "Bucket stays stable and performant",
    "trust": "Team trusts your work quality"
}


def get_executor_role() -> Dict[str, Any]:
    """Get executor role definition"""
    return {
        "executor": EXECUTOR_ROLE,
        "note": "Akanksha is the Executor - responsible for implementing approved decisions"
    }


def get_can_execute_changes() -> Dict[str, Any]:
    """Get changes that can be executed without approval"""
    return {
        "can_execute": CAN_EXECUTE_WITHOUT_APPROVAL,
        "count": len(CAN_EXECUTE_WITHOUT_APPROVAL),
        "note": "These changes require no approval from Ashmit. You can do them immediately."
    }


def get_requires_approval_changes() -> Dict[str, Any]:
    """Get changes that require Ashmit's approval"""
    return {
        "requires_approval": REQUIRES_APPROVAL,
        "count": len(REQUIRES_APPROVAL),
        "note": "These changes need Ashmit's approval before you can merge."
    }


def get_forbidden_actions() -> Dict[str, Any]:
    """Get forbidden actions"""
    return {
        "forbidden": FORBIDDEN_ACTIONS,
        "count": len(FORBIDDEN_ACTIONS),
        "note": "These are off-limits. Don't do them. Don't negotiate. Don't bypass."
    }


def get_code_review_checkpoints() -> Dict[str, Any]:
    """Get code review checkpoints"""
    return {
        "checkpoints": CODE_REVIEW_CHECKPOINTS,
        "count": len(CODE_REVIEW_CHECKPOINTS)
    }


def get_success_metrics() -> Dict[str, Any]:
    """Get success metrics for executor role"""
    return {
        "metrics": SUCCESS_METRICS,
        "note": "You're succeeding if all these metrics are met"
    }


def categorize_change(change_description: str) -> Dict[str, Any]:
    """Categorize a change as can_execute, requires_approval, or forbidden"""
    # Simple keyword-based categorization
    change_lower = change_description.lower()
    
    # Check forbidden first
    forbidden_keywords = ["delete data", "bypass", "governance", "override", "policy change"]
    for keyword in forbidden_keywords:
        if keyword in change_lower:
            return {
                "category": ChangeCategory.FORBIDDEN.value,
                "recommendation": "This change is forbidden. Do not proceed.",
                "escalate_to": "Ashmit"
            }
    
    # Check requires approval
    approval_keywords = ["breaking", "remove field", "new agent", "major version", "retention policy"]
    for keyword in approval_keywords:
        if keyword in change_lower:
            return {
                "category": ChangeCategory.REQUIRES_APPROVAL.value,
                "recommendation": "This change requires Ashmit's approval before proceeding.",
                "escalate_to": "Ashmit"
            }
    
    # Default to can execute (with caution)
    return {
        "category": ChangeCategory.CAN_EXECUTE.value,
        "recommendation": "This change appears to be executable without approval. If unsure, ask Ashmit.",
        "note": "Default rule: If unsure, ask"
    }


def get_escalation_path() -> Dict[str, Any]:
    """Get escalation path for disagreements or blocks"""
    return {
        "if_decision_seems_wrong": [
            "ask_for_clarification_may_be_miscommunication",
            "suggest_alternative_approach",
            "if_still_disagree_escalate_to_vijay",
            "respect_final_decision"
        ],
        "if_blocked_on_approval": [
            "ashmit_responds_within_24_hours_typical",
            "if_delayed_follow_up",
            "if_critical_escalate_to_vijay"
        ]
    }


def get_default_rule() -> Dict[str, Any]:
    """Get default rule for uncertainty"""
    return {
        "rule": "IF UNSURE, ASK",
        "guidance": [
            "ask_ashmit_before_implementing",
            "better_to_ask_than_to_implement_wrong",
            "use_example_this_is_similar_to_approved_change_should_i_ask",
            "timeline_ashmit_responds_within_24_hours"
        ]
    }


def validate_change_request(change_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate if a change request is properly categorized"""
    change_type = change_data.get("change_type", "")
    has_approval = change_data.get("has_ashmit_approval", False)
    
    # Check if change type requires approval
    requires_approval_types = list(REQUIRES_APPROVAL.keys())
    forbidden_types = list(FORBIDDEN_ACTIONS.keys())
    
    if change_type in forbidden_types:
        return {
            "valid": False,
            "reason": "This change is forbidden",
            "action": "Do not proceed"
        }
    
    if change_type in requires_approval_types and not has_approval:
        return {
            "valid": False,
            "reason": "This change requires Ashmit's approval",
            "action": "Get approval before proceeding"
        }
    
    return {
        "valid": True,
        "reason": "Change is properly categorized and approved (if needed)",
        "action": "Proceed with implementation"
    }
