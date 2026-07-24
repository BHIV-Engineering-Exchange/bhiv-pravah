"""
Document 10: Owner Core Principles & Final Responsibility Check
Core principles guiding all Bucket ownership decisions
"""

from typing import Dict, List, Any
from datetime import datetime

# Document metadata
DOCUMENT_METADATA = {
    "document_id": "BHIV-BUCKET-010-PRINCIPLES",
    "version": "1.0",
    "date_issued": "2026-01-13",
    "owner": "Ashmit",
    "review_frequency": "quarterly"
}

# Core principles
CORE_PRINCIPLES = {
    "principle_1": {
        "name": "Bucket Integrity > Product Urgency",
        "core": "Storage guarantees, schema integrity, and audit trail immutability are NOT negotiable to ship faster",
        "will_say_no_to": [
            "integrations_that_violate_schema_design",
            "changes_that_weaken_provenance",
            "shortcuts_that_bypass_validation",
            "features_that_embed_logic_in_storage"
        ],
        "will_delay_shipping_to": [
            "keep_schema_clean",
            "maintain_integrity_guarantees",
            "document_before_implementing",
            "review_for_governance_compliance"
        ],
        "why": "A broken storage layer affects everyone downstream. Bad data encoded in business logic costs 10x more to fix later."
    },
    "principle_2": {
        "name": "Rejection Is Acceptable Outcome",
        "core": "It is your job to say NO. Being a gatekeeper means rejecting things that don't fit",
        "will_reject": [
            "integrations_violating_boundaries",
            "schema_changes_lacking_versioning",
            "artifact_types_not_storage_appropriate",
            "requests_without_governance_review"
        ],
        "will_not_apologize_for": [
            "taking_time_to_review",
            "asking_hard_questions",
            "requiring_documentation",
            "saying_this_doesnt_fit"
        ],
        "why": "If you approve everything, you're not a gatekeeper. You're a rubber stamp. Real gatekeeping means earning respect through integrity."
    },
    "principle_3": {
        "name": "Drift Prevention Is Success",
        "core": "Preventing drift is not a failure. It's the definition of success",
        "drift_definition": "Silent, undocumented changes to schema meaning, behavior, or guarantees",
        "winning_when": [
            "old_code_still_works_backward_compat",
            "undocumented_assumptions_become_documented",
            "schema_changes_follow_versioning_rules",
            "no_surprises_in_storage_layer"
        ],
        "failing_when": [
            "schema_meaning_silently_changes",
            "old_data_breaks_with_new_code",
            "undocumented_behavior_becomes_standard",
            "guarantees_weaken_without_notification"
        ],
        "why": "Drift is invisible until it breaks everything. Prevention = clarity + enforcement."
    },
    "principle_4": {
        "name": "Honest About Limitations",
        "core": "Be brutally honest about gaps. Don't claim immutability if MongoDB can be deleted",
        "will_document": [
            "what_is_guaranteed_doc_05_section_1",
            "what_is_not_guaranteed_doc_05_section_2",
            "why_gaps_exist_doc_05_section_3",
            "when_theyll_be_fixed_phase_2_roadmap"
        ],
        "will_not": [
            "oversell_current_capabilities",
            "hide_limitations",
            "make_aspirational_claims_as_fact",
            "update_docs_without_honesty"
        ],
        "why": "Customers design integrations based on your promises. Honesty builds trust. BS builds resentment."
    },
    "principle_5": {
        "name": "Document as You Go (Not 'Later')",
        "core": "Governance documents are living documents. Update as decisions are made",
        "after_approving_integration": [
            "add_to_integration_registry",
            "document_decision_rationale",
            "note_any_conditions_or_followups"
        ],
        "when_discovering_gap": [
            "add_to_provenance_doc",
            "link_to_phase_2_roadmap",
            "dont_wait_for_perfect_state"
        ],
        "if_someone_asks_good_question": [
            "add_answer_to_docs",
            "make_future_person_find_answer_easily"
        ],
        "why": "Documentation is your memory. Without it, next owner won't know why you decided something."
    },
    "principle_6": {
        "name": "Own Your Decisions",
        "core": "When you make a decision, you own it. You don't hide behind docs or blame predecessors",
        "you_own_decision_to": [
            "approve_reject_integrations",
            "define_artifact_classes",
            "set_retention_policies",
            "change_governance_documents"
        ],
        "you_are_accountable_for": [
            "getting_it_right_or_close",
            "revisiting_if_facts_change",
            "explaining_rationale",
            "fixing_if_you_were_wrong"
        ],
        "you_will_not": [
            "blame_doc_policy_for_bad_call",
            "avoid_responsibility_for_impacts",
            "refuse_to_evolve_if_needed"
        ],
        "why": "Ownership means accountability. That accountability is what gives your approvals weight."
    },
    "principle_7": {
        "name": "Communication Before Conflict",
        "core": "If you think a decision is wrong, say it early. Don't wait until breaking point",
        "you_will": [
            "voice_concerns_early_in_escalation_not_post_decision",
            "ask_questions_if_you_dont_understand",
            "push_back_on_bad_ideas_before_locked_in",
            "escalate_to_vijay_if_you_need_help"
        ],
        "you_will_not": [
            "quietly_think_someones_idea_is_bad",
            "hope_someone_else_stops_it",
            "complain_after_the_fact",
            "bury_concerns_in_pr_review"
        ],
        "why": "Conflicts easier to resolve early. Concern in week 1 causes redesign. Same concern in week 8 is a crisis."
    },
    "principle_8": {
        "name": "Model Behavior You Want",
        "core": "You set the standard others follow. How you handle governance sets the tone",
        "model": [
            "careful_thorough_review",
            "clear_written_communication",
            "honest_about_uncertainty",
            "respect_for_others_time",
            "quick_decisions_on_clear_cases"
        ],
        "avoid": [
            "analysis_paralysis",
            "unclear_feedback",
            "dismissing_good_ideas",
            "slow_response_times",
            "inconsistent_standards"
        ],
        "why": "People mirror what they see. If you're thoughtful, others become thoughtful."
    },
    "principle_9": {
        "name": "Know When to Ask Help",
        "core": "You're not omniscient. Escalate to Vijay when needed. Consult Akanksha on feasibility",
        "you_will_ask_for_help": [
            "high_impact_decision",
            "genuinely_uncertain",
            "multiple_valid_options",
            "need_fresh_perspective"
        ],
        "you_will_not": [
            "pretend_to_know_what_you_dont",
            "make_critical_calls_in_isolation",
            "ignore_team_input",
            "refuse_advice_from_advisors"
        ],
        "why": "Good governance is collaborative. You're the decision-maker, not the only brain."
    },
    "principle_10": {
        "name": "Celebrate Good Work",
        "core": "When Akanksha makes a great PR, or someone designs an integration well, say so",
        "you_will": [
            "acknowledge_good_governance_compliance",
            "point_out_well_documented_decisions",
            "thank_people_for_following_process",
            "recognize_when_system_works_well"
        ],
        "why": "Positive reinforcement builds culture."
    }
}

# Final responsibility checklist
RESPONSIBILITY_CHECKLIST = {
    "bucket_integrity_over_urgency": {
        "statements": [
            "I understand I may delay shipping to protect storage integrity",
            "I will say no to requests violating schema design",
            "I will not compromise provenance guarantees for speed"
        ],
        "confirmation": "I am comfortable with this"
    },
    "rejection_is_acceptable": {
        "statements": [
            "I will reject integrations that don't fit",
            "I will not apologize for careful gating",
            "I will push back on bad ideas"
        ],
        "confirmation": "I am comfortable with this"
    },
    "drift_prevention_is_success": {
        "statements": [
            "I will document schema changes carefully",
            "I will enforce versioning discipline",
            "I will catch undocumented behavior"
        ],
        "confirmation": "I am comfortable with this"
    },
    "honest_about_limitations": {
        "statements": [
            "I will not oversell current capabilities",
            "I will document what we don't guarantee",
            "I will be truthful about gaps"
        ],
        "confirmation": "I am comfortable with this"
    },
    "own_your_decisions": {
        "statements": [
            "I will take responsibility for approvals",
            "I will not hide behind docs",
            "I will be accountable for impacts"
        ],
        "confirmation": "I am comfortable with this"
    },
    "escalate_when_needed": {
        "statements": [
            "I will ask Vijay for perspective on hard decisions",
            "I will consult Akanksha on feasibility",
            "I will not pretend to know what I don't"
        ],
        "confirmation": "I am comfortable with this"
    },
    "communicate_early": {
        "statements": [
            "I will voice concerns early, not late",
            "I will have hard conversations before conflicts",
            "I will not wait until breaking point"
        ],
        "confirmation": "I am comfortable with this"
    },
    "model_good_behavior": {
        "statements": [
            "I will set the standard others follow",
            "I will be thoughtful, clear, responsive",
            "I will be consistent"
        ],
        "confirmation": "I am comfortable with this"
    }
}

# Owner confirmation
OWNER_CONFIRMATION = {
    "owner": "Ashmit",
    "confirmations": [
        "I have read and understood all governance documents (01-10)",
        "I commit to the principles outlined above",
        "I accept the responsibility of Primary Bucket Owner for BHIV Central Depository"
    ],
    "understands": [
        "storage_integrity_is_non_negotiable",
        "rejection_is_part_of_my_job",
        "i_own_my_decisions",
        "i_will_communicate_clearly",
        "i_will_ask_for_help_when_needed",
        "i_model_the_behavior_i_want_to_see"
    ],
    "date": "2026-01-13"
}


def get_document_metadata() -> Dict[str, Any]:
    """Get document metadata"""
    return {
        "metadata": DOCUMENT_METADATA,
        "note": "Review quarterly to check if principles still hold"
    }


def get_core_principles() -> Dict[str, Any]:
    """Get all 10 core principles"""
    return {
        "principles": CORE_PRINCIPLES,
        "count": len(CORE_PRINCIPLES),
        "note": "Core principles guiding all Bucket ownership decisions"
    }


def get_principle_details(principle_number: int) -> Dict[str, Any]:
    """Get details of a specific principle"""
    principle_key = f"principle_{principle_number}"
    
    if principle_key not in CORE_PRINCIPLES:
        return {"error": f"Principle {principle_number} not found. Valid range: 1-10"}
    
    return {
        "principle_number": principle_number,
        "principle": CORE_PRINCIPLES[principle_key]
    }


def get_responsibility_checklist() -> Dict[str, Any]:
    """Get final responsibility checklist"""
    return {
        "checklist": RESPONSIBILITY_CHECKLIST,
        "count": len(RESPONSIBILITY_CHECKLIST),
        "note": "Before formally accepting role, explicitly confirm each item"
    }


def get_owner_confirmation() -> Dict[str, Any]:
    """Get owner confirmation details"""
    return {
        "confirmation": OWNER_CONFIRMATION,
        "note": "Ashmit's formal acceptance of Primary Bucket Owner role"
    }


def validate_principle_adherence(principle_number: int, scenario: str) -> Dict[str, Any]:
    """Validate if a scenario adheres to a specific principle"""
    principle_key = f"principle_{principle_number}"
    
    if principle_key not in CORE_PRINCIPLES:
        return {"error": f"Principle {principle_number} not found"}
    
    principle = CORE_PRINCIPLES[principle_key]
    
    # Simple keyword-based validation
    scenario_lower = scenario.lower()
    
    # Check for violations based on principle
    violations = []
    
    if principle_number == 1:  # Bucket Integrity > Product Urgency
        if any(keyword in scenario_lower for keyword in ["bypass validation", "skip review", "ship faster"]):
            violations.append("May violate bucket integrity for speed")
    
    elif principle_number == 2:  # Rejection Is Acceptable
        if "approve everything" in scenario_lower or "rubber stamp" in scenario_lower:
            violations.append("Not exercising gatekeeper responsibility")
    
    elif principle_number == 3:  # Drift Prevention
        if "undocumented change" in scenario_lower or "silent change" in scenario_lower:
            violations.append("May introduce drift")
    
    elif principle_number == 4:  # Honest About Limitations
        if "oversell" in scenario_lower or "hide limitation" in scenario_lower:
            violations.append("Not being honest about capabilities")
    
    adheres = len(violations) == 0
    
    return {
        "principle_number": principle_number,
        "principle_name": principle["name"],
        "scenario": scenario,
        "adheres": adheres,
        "violations": violations if not adheres else [],
        "recommendation": "Proceed" if adheres else "Review against principle"
    }


def get_closing_thought() -> Dict[str, Any]:
    """Get closing thought"""
    return {
        "message": "You now have the governance framework and the principles to guide BHIV Bucket. The hard part isn't the documents. It's the daily decision-making, the pushback on bad ideas, and the care you put into keeping storage clean and integrity high. This is valuable work. Do it well.",
        "note": "Governance is about daily discipline, not just documentation"
    }


def check_confirmation_status(checklist_responses: Dict[str, bool]) -> Dict[str, Any]:
    """Check if all checklist items are confirmed"""
    required_items = list(RESPONSIBILITY_CHECKLIST.keys())
    confirmed_items = []
    missing_items = []
    
    for item in required_items:
        if checklist_responses.get(item, False):
            confirmed_items.append(item)
        else:
            missing_items.append(item)
    
    all_confirmed = len(missing_items) == 0
    
    return {
        "all_confirmed": all_confirmed,
        "confirmed_items": confirmed_items,
        "missing_items": missing_items,
        "confirmation_rate": f"{len(confirmed_items)}/{len(required_items)}",
        "ready_to_accept_role": all_confirmed
    }
