"""
EVALUATOR VERIFICATION TEST CASES
Defines exact criteria for verifying evaluator decisions
"""
import sys
import os
import json
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from app.services.hybrid_evaluation_pipeline import HybridEvaluationPipeline

class EvaluatorVerifier:
    """
    Comprehensive evaluator verification framework
    """
    
    def __init__(self):
        self.pipeline = HybridEvaluationPipeline()
        self.tolerance_ms = 50  # Timing tolerance
        
    def verify_decision_correctness(self, input_data, output_data):
        """
        Verify if a decision is correct based on defined criteria
        """
        checks = {
            "score_range": self._check_score_range(output_data),
            "status_alignment": self._check_status_alignment(output_data),
            "contract_compliance": self._check_contract_compliance(output_data),
            "hierarchy_respected": self._check_hierarchy_rules(input_data, output_data),
            "required_fields": self._check_required_fields(output_data)
        }
        
        return all(checks.values()), checks
    
    def verify_exact_match(self, output_1, output_2):
        """
        Verify what MUST match exactly in replay
        """
        exact_matches = {
            "score": output_1["score"] == output_2["score"],
            "status": output_1["status"] == output_2["status"],
            "failure_reasons": output_1["failure_reasons"] == output_2["failure_reasons"],
            "technical_quality": output_1["analysis"]["technical_quality"] == output_2["analysis"]["technical_quality"],
            "clarity": output_1["analysis"]["clarity"] == output_2["analysis"]["clarity"],
            "discipline_signals": output_1["analysis"]["discipline_signals"] == output_2["analysis"]["discipline_signals"]
        }
        
        # Timing tolerance check
        timing_ok = abs(output_1["meta"]["evaluation_time_ms"] - 
                       output_2["meta"]["evaluation_time_ms"]) <= self.tolerance_ms
        
        return all(exact_matches.values()) and timing_ok, exact_matches
    
    def identify_mismatch_type(self, output_1, output_2):
        """
        Identify specific type of mismatch
        """
        mismatches = []
        
        if output_1["score"] != output_2["score"]:
            mismatches.append(f"SCORE_MISMATCH: {output_1['score']} != {output_2['score']}")
        
        if output_1["status"] != output_2["status"]:
            mismatches.append(f"STATUS_MISMATCH: {output_1['status']} != {output_2['status']}")
        
        if output_1["failure_reasons"] != output_2["failure_reasons"]:
            mismatches.append(f"FAILURE_REASONS_MISMATCH: Lists differ")
        
        if output_1["analysis"] != output_2["analysis"]:
            mismatches.append(f"ANALYSIS_MISMATCH: Analysis values differ")
        
        return mismatches
    
    def _check_score_range(self, output):
        """Score must be 0-100"""
        return 0 <= output.get("score", -1) <= 100
    
    def _check_status_alignment(self, output):
        """Status must align with score"""
        score = output.get("score", 0)
        status = output.get("status", "")
        
        if score >= 80:
            return status == "pass"
        elif score >= 50:
            return status == "borderline"
        else:
            return status == "fail"
    
    def _check_contract_compliance(self, output):
        """Output must comply with contract"""
        required_fields = [
            "score", "status", "failure_reasons", "improvement_hints",
            "analysis", "meta", "accuracy_score", "completeness_score"
        ]
        
        return all(field in output for field in required_fields)
    
    def _check_hierarchy_rules(self, input_data, output):
        """Assignment hierarchy must be respected"""
        # If assignment would fail, final must be fail
        # This is a simplified check - in practice would call assignment engine
        title = input_data.get("task_title", "")
        description = input_data.get("task_description", "")
        
        # Very basic assignment failure detection
        if len(title) < 10 and len(description) < 50:
            return output["status"] == "fail"
        
        return True  # More complex logic would go here
    
    def _check_required_fields(self, output):
        """All required fields must be present"""
        analysis = output.get("analysis", {})
        meta = output.get("meta", {})
        
        analysis_fields = ["technical_quality", "clarity", "discipline_signals"]
        meta_fields = ["evaluation_time_ms", "mode", "contract_version"]
        
        return (all(field in analysis for field in analysis_fields) and
                all(field in meta for field in meta_fields))

def run_verification_tests():
    """
    Run comprehensive verification tests
    """
    print("=" * 70)
    print("EVALUATOR VERIFICATION TEST CASES")
    print("Testing decision correctness and determinism")
    print("=" * 70)
    
    verifier = EvaluatorVerifier()
    
    # Test Case 1: High Quality Task
    print("\n1. HIGH QUALITY TASK VERIFICATION")
    print("-" * 40)
    
    high_quality_input = {
        "task_title": "Implement Secure REST API Authentication System with JWT and Database Integration",
        "task_description": """
        Objective: Build comprehensive authentication system
        
        Deliverables:
        - JWT token generation and validation
        - User registration and login endpoints
        - Secure password hashing
        - Database integration for user management
        
        Timeline: 3 weeks development
        
        Scope: Authentication module only
        
        Technical Requirements:
        - RESTful API design
        - Secure password storage
        - Token expiration handling
        - Input validation
        """,
        "submitted_by": "Test Developer"
    }
    
    try:
        # Run evaluation
        output_1 = verifier.pipeline.evaluate(
            high_quality_input["task_title"],
            high_quality_input["task_description"]
        )
        
        print(f"   Result: Score={output_1['score']}, Status={output_1['status']}")
        
        # Verify decision correctness
        is_correct, checks = verifier.verify_decision_correctness(high_quality_input, output_1)
        print(f"   Decision Correct: {is_correct}")
        for check, result in checks.items():
            print(f"     {check}: {'PASS' if result else 'FAIL'}")
        
        # Test determinism
        output_2 = verifier.pipeline.evaluate(
            high_quality_input["task_title"],
            high_quality_input["task_description"]
        )
        
        is_deterministic, matches = verifier.verify_exact_match(output_1, output_2)
        print(f"   Deterministic: {is_deterministic}")
        
        if not is_deterministic:
            mismatches = verifier.identify_mismatch_type(output_1, output_2)
            print(f"   Mismatches: {mismatches}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test Case 2: Poor Quality Task
    print("\n2. POOR QUALITY TASK VERIFICATION")
    print("-" * 40)
    
    poor_quality_input = {
        "task_title": "Fix bug",
        "task_description": "Fix the bug in the system",
        "submitted_by": "Developer"
    }
    
    try:
        # Run evaluation
        output_1 = verifier.pipeline.evaluate(
            poor_quality_input["task_title"],
            poor_quality_input["task_description"]
        )
        
        print(f"   Result: Score={output_1['score']}, Status={output_1['status']}")
        
        # Verify decision correctness
        is_correct, checks = verifier.verify_decision_correctness(poor_quality_input, output_1)
        print(f"   Decision Correct: {is_correct}")
        for check, result in checks.items():
            print(f"     {check}: {'PASS' if result else 'FAIL'}")
        
        # Test determinism
        output_2 = verifier.pipeline.evaluate(
            poor_quality_input["task_title"],
            poor_quality_input["task_description"]
        )
        
        is_deterministic, matches = verifier.verify_exact_match(output_1, output_2)
        print(f"   Deterministic: {is_deterministic}")
        
        if not is_deterministic:
            mismatches = verifier.identify_mismatch_type(output_1, output_2)
            print(f"   Mismatches: {mismatches}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test Case 3: Borderline Quality Task
    print("\n3. BORDERLINE QUALITY TASK VERIFICATION")
    print("-" * 40)
    
    borderline_input = {
        "task_title": "Database API Implementation",
        "task_description": """
        Objective: Create database API endpoints
        
        Deliverables:
        - CRUD operations for user data
        - Basic API documentation
        
        Timeline: 1 week development
        """,
        "submitted_by": "Developer"
    }
    
    try:
        # Run evaluation
        output_1 = verifier.pipeline.evaluate(
            borderline_input["task_title"],
            borderline_input["task_description"]
        )
        
        print(f"   Result: Score={output_1['score']}, Status={output_1['status']}")
        
        # Verify decision correctness
        is_correct, checks = verifier.verify_decision_correctness(borderline_input, output_1)
        print(f"   Decision Correct: {is_correct}")
        for check, result in checks.items():
            print(f"     {check}: {'PASS' if result else 'FAIL'}")
        
        # Test determinism
        output_2 = verifier.pipeline.evaluate(
            borderline_input["task_title"],
            borderline_input["task_description"]
        )
        
        is_deterministic, matches = verifier.verify_exact_match(output_1, output_2)
        print(f"   Deterministic: {is_deterministic}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION FRAMEWORK SUMMARY")
    print("=" * 70)
    
    print("\nDECISION CORRECTNESS CRITERIA:")
    print("  ✓ Score range: 0-100")
    print("  ✓ Status alignment: score ↔ status mapping")
    print("  ✓ Contract compliance: all required fields present")
    print("  ✓ Hierarchy respected: assignment authority maintained")
    print("  ✓ Required fields: analysis and meta complete")
    
    print("\nEXACT MATCH REQUIREMENTS:")
    print("  ✓ score (integer)")
    print("  ✓ status (string)")
    print("  ✓ failure_reasons (list)")
    print("  ✓ analysis.technical_quality (integer)")
    print("  ✓ analysis.clarity (integer)")
    print("  ✓ analysis.discipline_signals (integer)")
    
    print("\nTOLERANCE ALLOWED:")
    print("  ~ evaluation_time_ms (±50ms)")
    print("  ~ determinism_hash (regeneratable)")
    
    print("\nMISMATCH INDICATORS:")
    print("  ✗ Score differs")
    print("  ✗ Status changes")
    print("  ✗ Core analysis values differ")
    print("  ✗ Failure reasons change")
    
    print("\n" + "=" * 70)
    print("VERIFICATION FRAMEWORK: COMPLETE")
    print("Clear criteria defined for evaluator verification")
    print("=" * 70)

if __name__ == "__main__":
    run_verification_tests()