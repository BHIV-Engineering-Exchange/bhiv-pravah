"""
Unit Tests for BHIV Bucket Governance Engine
Tests all governance rules and validation
"""

import pytest
from config.governance import (
    GovernanceEngine,
    validate_governance_compliance,
    log_governance_violation
)

class TestOperationValidation:
    """Test operation validation by actor type"""
    
    def test_ai_agent_create_allowed(self):
        """Test AI agent can CREATE"""
        result = GovernanceEngine.validate_operation("ai_agent", "CREATE")
        assert result["allowed"] == True
    
    def test_ai_agent_delete_forbidden(self):
        """Test AI agent cannot DELETE"""
        result = GovernanceEngine.validate_operation("ai_agent", "DELETE")
        assert result["allowed"] == False
        assert result["rule_violated"] == "RULE_01_WRITE_ONLY"
    
    def test_executor_approve_integration(self):
        """Test executor can approve integrations"""
        result = GovernanceEngine.validate_operation("akanksha_parab", "APPROVE_INTEGRATION")
        assert result["allowed"] == True
    
    def test_executor_delete_forbidden(self):
        """Test executor cannot DELETE"""
        result = GovernanceEngine.validate_operation("akanksha_parab", "DELETE")
        assert result["allowed"] == False

class TestWriteOperationValidation:
    """Test write operation validation"""
    
    def test_valid_write_operation(self):
        """Test valid write with all required fields"""
        data = {
            "created_by": "user123",
            "created_at": "2026-01-19T10:00:00Z",
            "product_id": "AI_ASSISTANT",
            "artifact_type": "ConversationArtifact",
            "content_hash": "abc123",
            "data": {"content": "test"}
        }
        result = GovernanceEngine.validate_write_operation(data)
        assert result["valid"] == True
        assert len(result["violations"]) == 0
    
    def test_missing_provenance_fields(self):
        """Test write missing provenance fields"""
        data = {"data": {"content": "test"}}
        result = GovernanceEngine.validate_write_operation(data)
        assert result["valid"] == False
        assert len(result["violations"]) > 0
    
    def test_missing_product_id(self):
        """Test write missing product_id"""
        data = {
            "created_by": "user123",
            "created_at": "2026-01-19T10:00:00Z",
            "artifact_type": "ConversationArtifact"
        }
        result = GovernanceEngine.validate_write_operation(data)
        assert result["valid"] == False
        assert any("product_id" in v for v in result["violations"])
    
    def test_missing_content_hash(self):
        """Test write missing content_hash"""
        data = {
            "created_by": "user123",
            "created_at": "2026-01-19T10:00:00Z",
            "product_id": "AI_ASSISTANT",
            "artifact_type": "ConversationArtifact",
            "data": {"content": "test"}
        }
        result = GovernanceEngine.validate_write_operation(data)
        assert result["valid"] == False
        assert any("content_hash" in v for v in result["violations"])

class TestProductIsolation:
    """Test product isolation validation"""
    
    def test_same_product_access(self):
        """Test product accessing own data"""
        result = GovernanceEngine.validate_product_isolation("AI_ASSISTANT", "AI_ASSISTANT")
        assert result["valid"] == True
    
    def test_cross_product_access(self):
        """Test cross-product access blocked"""
        result = GovernanceEngine.validate_product_isolation("AI_ASSISTANT", "GURUKUL")
        assert result["valid"] == False
        assert result["rule_violated"] == "RULE_05_PRODUCT_ISOLATION"
        assert result["action"] == "REJECT_AND_ALERT"

class TestSchemaChangeValidation:
    """Test schema change validation"""
    
    def test_schema_change_requires_ceo(self):
        """Test schema change requires CEO approval"""
        result = GovernanceEngine.validate_schema_change({"change": "add_field"})
        assert result["valid"] == False
        assert result["rule_violated"] == "RULE_03_SCHEMA_IMMUTABLE"
        assert result["approval_required"] == "CEO"

class TestEscalationPaths:
    """Test escalation path determination"""
    
    def test_write_only_violation_escalation(self):
        """Test write-only violation escalation"""
        escalation = GovernanceEngine.check_escalation_needed("RULE_01_WRITE_ONLY")
        assert escalation["escalate_to"] == "Ops_Team"
        assert escalation["severity"] == "CRITICAL"
    
    def test_executor_override_escalation(self):
        """Test executor override escalation"""
        escalation = GovernanceEngine.check_escalation_needed("RULE_08_EXECUTOR_AUTHORITY")
        assert escalation["escalate_to"] == "Vijay_Dhawan"
        assert escalation["timeline"] == "IMMEDIATE"
    
    def test_product_isolation_escalation(self):
        """Test product isolation violation escalation"""
        escalation = GovernanceEngine.check_escalation_needed("RULE_05_PRODUCT_ISOLATION")
        assert escalation["escalate_to"] == "Security_Team"
        assert escalation["severity"] == "CRITICAL"

class TestGovernanceCompliance:
    """Test complete governance compliance validation"""
    
    def test_compliant_operation(self):
        """Test fully compliant operation"""
        data = {
            "created_by": "user123",
            "created_at": "2026-01-19T10:00:00Z",
            "product_id": "AI_ASSISTANT",
            "artifact_type": "ConversationArtifact",
            "content_hash": "abc123",
            "data": {"content": "test"}
        }
        result = validate_governance_compliance("CREATE", "product_ai_assistant", data)
        assert result["compliant"] == True
        assert result["escalation_required"] == False
    
    def test_non_compliant_operation(self):
        """Test non-compliant operation"""
        data = {"data": {"content": "test"}}
        result = validate_governance_compliance("DELETE", "ai_agent", data)
        assert result["compliant"] == False
        assert result["escalation_required"] == True

class TestImmutableRules:
    """Test immutable governance rules"""
    
    def test_all_rules_defined(self):
        """Test all 10 rules are defined"""
        rules = GovernanceEngine.get_all_rules()
        assert len(rules) == 10
        assert "RULE_01_WRITE_ONLY" in rules
        assert "RULE_10_ZERO_EXCEPTIONS" in rules
    
    def test_rule_structure(self):
        """Test rule structure is correct"""
        rule = GovernanceEngine.get_rule_details("RULE_01_WRITE_ONLY")
        assert "name" in rule
        assert "description" in rule
        assert "enforcement" in rule
        assert "violation_action" in rule

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
