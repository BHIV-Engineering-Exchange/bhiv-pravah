"""
Document 09: Escalation Protocol (Vijay)
Advisory escalation protocol with Vijay Dhawan
"""

from typing import Dict, List, Any, Optional
from enum import Enum

class EscalationUrgency(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RiskLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Vijay's role definition
ADVISOR_ROLE = {
    "name": "Vijay Dhawan",
    "title": "Technical Advisor",
    "authority": {
        "can_do": [
            "provide_expert_perspective_on_complex_decisions",
            "identify_risks_and_mitigation_strategies",
            "challenge_assumptions_constructively",
            "respond_to_escalations_from_ashmit"
        ],
        "cannot_do": [
            "make_final_decisions",
            "enforce_recommendations",
            "bypass_ashmit_authority"
        ]
    }
}

# Escalation triggers
ESCALATION_TRIGGERS = {
    "major_architecture_changes": {
        "description": "Significant change to Bucket core architecture",
        "examples": [
            "significant_change_to_bucket_core_architecture",
            "new_major_subsystem_or_component",
            "fundamental_workflow_changes",
            "introduces_new_critical_dependency"
        ],
        "what_needed": [
            "risk_assessment_probability_impact",
            "pros_cons_of_each_option",
            "recommendation_with_rationale",
            "questions_for_ashmit_to_consider"
        ]
    },
    "product_wide_integration_requests": {
        "description": "Integration affects multiple teams",
        "examples": [
            "integration_affects_multiple_teams",
            "requires_cross_team_coordination",
            "potential_conflicts_with_other_systems",
            "strategic_importance_to_roadmap"
        ],
        "what_needed": [
            "architecture_approach",
            "conflict_resolution_strategy",
            "coordination_plan"
        ]
    },
    "compliance_legal_ambiguity": {
        "description": "PII handling, data retention, GDPR implications",
        "examples": [
            "pii_handling_questions",
            "data_retention_vs_deletion_conflict",
            "gdpr_privacy_implications",
            "legal_holds_or_subpoenas",
            "regulatory_compliance_needs"
        ],
        "what_needed": [
            "compliance_assessment",
            "risk_mitigation_strategy",
            "balance_audit_trail_with_privacy"
        ]
    },
    "provenance_guarantees_weakened": {
        "description": "Proposed change affects audit trails",
        "examples": [
            "affects_audit_trails",
            "reduces_immutability_guarantees",
            "weakens_error_tracking",
            "removes_logging_or_monitoring",
            "changes_data_retention_downward"
        ],
        "what_needed": [
            "risk_acceptability_assessment",
            "impact_on_audit_capabilities",
            "alternative_approaches"
        ]
    },
    "performance_scale_issues": {
        "description": "Bucket approaching capacity limits",
        "examples": [
            "approaching_capacity_limits",
            "performance_degradation_observed",
            "need_to_optimize_for_scale",
            "architectural_bottlenecks_identified"
        ],
        "what_needed": [
            "architectural_solution",
            "scaling_strategy",
            "performance_optimization_approach"
        ]
    },
    "unresolved_technical_conflicts": {
        "description": "Two teams have conflicting needs",
        "examples": [
            "two_teams_conflicting_needs",
            "no_clear_technical_winner",
            "decision_has_high_impact",
            "ashmit_genuinely_uncertain"
        ],
        "what_needed": [
            "conflict_resolution_approach",
            "technical_recommendation",
            "trade_off_analysis"
        ]
    },
    "novel_integration_review": {
        "description": "Integration in new domain or unusual architecture",
        "examples": [
            "integration_in_new_domain",
            "unusual_data_flow_or_architecture",
            "high_impact_if_failure_occurs",
            "ashmit_wants_experienced_perspective"
        ],
        "what_needed": [
            "risk_assessment",
            "feasibility_analysis",
            "recommendation_on_proceeding"
        ]
    },
    "cto_level_strategic_decision": {
        "description": "Decision impacts strategic direction",
        "examples": [
            "impacts_strategic_direction",
            "fundamental_design_choice_needed",
            "executive_visibility_appropriate",
            "policy_setting_decision"
        ],
        "what_needed": [
            "strategic_perspective",
            "long_term_implications",
            "executive_recommendation"
        ]
    }
}

# Response timeline expectations
RESPONSE_TIMELINE = {
    EscalationUrgency.CRITICAL.value: {
        "timeline": "4 hours",
        "expectation": "Quick assessment + recommendation"
    },
    EscalationUrgency.HIGH.value: {
        "timeline": "1-2 days",
        "expectation": "Thorough analysis + recommendation"
    },
    EscalationUrgency.MEDIUM.value: {
        "timeline": "3-5 days",
        "expectation": "Thoughtful input + recommendation"
    },
    EscalationUrgency.LOW.value: {
        "timeline": "Up to 2 weeks",
        "expectation": "Whenever you can"
    }
}

# Response format template
RESPONSE_FORMAT = {
    "summary": "Bottom line: I recommend [X] because [reason]",
    "risk_assessment": {
        "what_could_go_wrong": "Description of risks",
        "probability": "high/medium/low",
        "impact": "high/medium/low",
        "mitigations": "List of mitigation strategies"
    },
    "options_analysis": [
        {
            "option": "Option A",
            "description": "Description",
            "pros": ["Pro 1", "Pro 2"],
            "cons": ["Con 1", "Con 2"],
            "risk_level": "high/medium/low"
        }
    ],
    "recommendation": "I recommend Option B because [specific reasons]",
    "questions_for_ashmit": [
        "Have you considered [X]?",
        "What if [Y happens]?",
        "How does this interact with [Z]?"
    ],
    "disclaimer": "This is advisory input. Ashmit makes the final decision."
}

# Decision authority boundaries
DECISION_AUTHORITY = {
    "approve_reject_integration": {"ashmit": "final_call", "vijay": "consult_if_complex"},
    "change_governance_policy": {"ashmit": "final_call", "vijay": "consult_if_strategic"},
    "weaken_provenance_guarantees": {"ashmit": "final_call", "vijay": "consult_on_risks"},
    "architecture_decision": {"ashmit": "final_call", "vijay": "consulted_always"},
    "risk_acceptance": {"ashmit": "final_call", "vijay": "assess_risks"},
    "conflict_resolution": {"ashmit": "final_call", "vijay": "offer_perspective"},
    "strategic_direction": {"ashmit": "final_call", "vijay": "provide_guidance"}
}

# Disagreement protocol
DISAGREEMENT_PROTOCOL = {
    "step_1": "understand_why - Ask clarifying questions",
    "step_2": "state_disagreement_clearly - I disagree because [reason]",
    "step_3": "explain_reasoning - What's the risk? How likely/severe?",
    "step_4": "escalate_if_critical - If safety/compliance critical → Escalate to CTO",
    "step_5": "respect_decision - Ashmit is owner, support implementation"
}

# Success metrics
SUCCESS_METRICS = {
    "timely_response": "You respond timely to escalations",
    "thorough_analysis": "Your analysis is thorough and clear",
    "concrete_recommendations": "You offer concrete recommendations",
    "hard_questions": "You ask hard questions",
    "no_bulldozing": "You don't bulldoze your views",
    "respect_decisions": "You respect final decisions",
    "support_implementation": "You support implementation after decision"
}


def get_advisor_role() -> Dict[str, Any]:
    """Get advisor role definition"""
    return {
        "advisor": ADVISOR_ROLE,
        "note": "Vijay is the Technical Advisor - provides expert perspective, does NOT make final decisions"
    }


def get_escalation_triggers() -> Dict[str, Any]:
    """Get escalation triggers"""
    return {
        "triggers": ESCALATION_TRIGGERS,
        "count": len(ESCALATION_TRIGGERS),
        "note": "When Ashmit will escalate to Vijay"
    }


def get_response_timeline() -> Dict[str, Any]:
    """Get response timeline expectations"""
    return {
        "timeline": RESPONSE_TIMELINE,
        "note": "Expected response times based on urgency"
    }


def get_response_format() -> Dict[str, Any]:
    """Get response format template"""
    return {
        "format": RESPONSE_FORMAT,
        "note": "Expected format for escalation responses"
    }


def get_decision_authority() -> Dict[str, Any]:
    """Get decision authority boundaries"""
    return {
        "authority": DECISION_AUTHORITY,
        "note": "Ashmit makes final decisions, Vijay provides advisory input"
    }


def get_disagreement_protocol() -> Dict[str, Any]:
    """Get disagreement protocol"""
    return {
        "protocol": DISAGREEMENT_PROTOCOL,
        "note": "Steps to follow when disagreeing with Ashmit's decision"
    }


def get_success_metrics() -> Dict[str, Any]:
    """Get success metrics for advisor role"""
    return {
        "metrics": SUCCESS_METRICS,
        "note": "You're succeeding if all these metrics are met"
    }


def create_escalation(
    trigger_type: str,
    context: str,
    options: List[str],
    urgency: str,
    timeline: Optional[str] = None
) -> Dict[str, Any]:
    """Create an escalation to Vijay"""
    if trigger_type not in ESCALATION_TRIGGERS:
        return {"error": f"Unknown trigger type: {trigger_type}"}
    
    trigger = ESCALATION_TRIGGERS[trigger_type]
    
    escalation = {
        "trigger_type": trigger_type,
        "description": trigger["description"],
        "context": context,
        "options": options,
        "urgency": urgency,
        "timeline": timeline or RESPONSE_TIMELINE.get(urgency, {}).get("timeline", "Not specified"),
        "what_needed": trigger["what_needed"],
        "escalated_to": "vijay_dhawan",
        "escalated_by": "ashmit",
        "status": "pending_response"
    }
    
    return escalation


def validate_escalation_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate if escalation response has all required components"""
    required_components = ["summary", "risk_assessment", "options_analysis", "recommendation", "disclaimer"]
    missing_components = []
    
    for component in required_components:
        if component not in response_data:
            missing_components.append(component)
    
    is_complete = len(missing_components) == 0
    
    return {
        "complete": is_complete,
        "missing_components": missing_components,
        "note": "Complete response includes: summary, risk_assessment, options_analysis, recommendation, questions, disclaimer"
    }


def assess_conflict_of_interest(advisor_data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess if advisor has conflict of interest"""
    has_conflict = advisor_data.get("has_conflict_of_interest", False)
    conflict_description = advisor_data.get("conflict_description", "")
    
    if has_conflict:
        return {
            "has_conflict": True,
            "conflict_description": conflict_description,
            "action": "disclose_immediately_and_recuse",
            "note": "Ashmit will make decision independently or escalate to CTO"
        }
    
    return {
        "has_conflict": False,
        "action": "proceed_with_advisory_input"
    }


def get_escalation_process() -> Dict[str, Any]:
    """Get escalation process flow"""
    return {
        "process": [
            "complex_decision_arises",
            "ashmit_thinks_this_needs_vijay_perspective",
            "ashmit_opens_escalation_with_context_options_timeline",
            "vijay_responds_with_risk_assessment_options_recommendation",
            "ashmit_reviews_input_may_change_mind_or_decide_differently",
            "ashmit_makes_final_decision",
            "ashmit_communicates_to_stakeholders_thanks_vijay_deciding_x_because_reason"
        ],
        "note": "Vijay provides advisory input, Ashmit makes final decision"
    }
