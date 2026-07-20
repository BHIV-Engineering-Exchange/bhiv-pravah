"""
Unit Tests for BHIV Bucket Threat Detector
Tests all threat detection mechanisms
"""

import pytest
from models.threat_detector import BucketThreatDetector

class TestStorageExhaustionDetection:
    """Test T1: Storage exhaustion detection"""
    
    @pytest.mark.asyncio
    async def test_no_threat_at_50_percent(self):
        """Test no threat at 50% storage"""
        threat = await BucketThreatDetector.check_storage_exhaustion(500)
        assert threat is None
    
    @pytest.mark.asyncio
    async def test_warning_at_95_percent(self):
        """Test warning at 95% storage"""
        threat = await BucketThreatDetector.check_storage_exhaustion(950)
        assert threat is not None
        assert threat["threat_id"] == "T1_STORAGE_EXHAUSTION"
        assert threat["severity"] in ["HIGH", "CRITICAL"]
    
    @pytest.mark.asyncio
    async def test_critical_at_99_percent(self):
        """Test critical at 99% storage"""
        threat = await BucketThreatDetector.check_storage_exhaustion(990)
        assert threat is not None
        assert threat["severity"] == "CRITICAL"
        assert threat["action"] == "HALT_WRITES"

class TestMetadataPoisoningDetection:
    """Test T2: Metadata poisoning detection"""
    
    @pytest.mark.asyncio
    async def test_clean_metadata(self):
        """Test clean metadata passes"""
        metadata = {"key1": "value1", "key2": "value2"}
        threat = await BucketThreatDetector.detect_metadata_poisoning(metadata)
        assert threat is None
    
    @pytest.mark.asyncio
    async def test_oversized_metadata(self):
        """Test oversized metadata detected"""
        metadata = {"key1": "x" * 20000}  # 20KB
        threat = await BucketThreatDetector.detect_metadata_poisoning(metadata)
        assert threat is not None
        assert threat["threat_id"] == "T2_METADATA_POISONING"
    
    @pytest.mark.asyncio
    async def test_sql_injection_pattern(self):
        """Test SQL injection pattern detected"""
        metadata = {"query": "DROP TABLE users"}
        threat = await BucketThreatDetector.detect_metadata_poisoning(metadata)
        assert threat is not None
        assert threat["severity"] == "CRITICAL"
    
    @pytest.mark.asyncio
    async def test_script_injection_pattern(self):
        """Test script injection pattern detected"""
        metadata = {"content": "<script>alert('xss')</script>"}
        threat = await BucketThreatDetector.detect_metadata_poisoning(metadata)
        assert threat is not None

class TestExecutorMisbehaviorDetection:
    """Test T5: Executor misbehavior detection"""
    
    @pytest.mark.asyncio
    async def test_executor_allowed_operation(self):
        """Test executor allowed operation"""
        threat = await BucketThreatDetector.detect_executor_misbehavior("akanksha_parab", "CREATE")
        assert threat is None
    
    @pytest.mark.asyncio
    async def test_executor_forbidden_operation(self):
        """Test executor forbidden operation"""
        threat = await BucketThreatDetector.detect_executor_misbehavior("akanksha_parab", "DELETE")
        assert threat is not None
        assert threat["threat_id"] == "T5_EXECUTOR_OVERRIDE"
        assert threat["escalation"] == "Vijay_Dhawan"

class TestAIEscalationDetection:
    """Test T6: AI escalation detection"""
    
    @pytest.mark.asyncio
    async def test_ai_allowed_operation(self):
        """Test AI allowed operation"""
        threat = await BucketThreatDetector.detect_ai_escalation("ai_agent", "CREATE")
        assert threat is None
    
    @pytest.mark.asyncio
    async def test_ai_forbidden_operation(self):
        """Test AI forbidden operation"""
        threat = await BucketThreatDetector.detect_ai_escalation("ai_agent", "DELETE")
        assert threat is not None
        assert threat["threat_id"] == "T6_AI_ESCALATION"
        assert threat["severity"] == "CRITICAL"
    
    @pytest.mark.asyncio
    async def test_ai_update_forbidden(self):
        """Test AI UPDATE forbidden"""
        threat = await BucketThreatDetector.detect_ai_escalation("ai_assistant", "UPDATE")
        assert threat is not None

class TestCrossProductContamination:
    """Test T7: Cross-product contamination detection"""
    
    @pytest.mark.asyncio
    async def test_valid_product_artifact_type(self):
        """Test valid artifact type for product"""
        threat = await BucketThreatDetector.detect_cross_product_contamination(
            "AI_ASSISTANT", "ConversationArtifact"
        )
        assert threat is None
    
    @pytest.mark.asyncio
    async def test_invalid_product_artifact_type(self):
        """Test invalid artifact type for product"""
        threat = await BucketThreatDetector.detect_cross_product_contamination(
            "AI_ASSISTANT", "MediaArtifact"
        )
        assert threat is not None
        assert threat["threat_id"] == "T7_CROSS_PRODUCT"
        assert threat["escalation"] == "Security_Team"

class TestAuditTamperingDetection:
    """Test T8: Audit tampering detection"""
    
    @pytest.mark.asyncio
    async def test_normal_operation(self):
        """Test normal operation"""
        threat = await BucketThreatDetector.detect_audit_tampering("CREATE", "artifact")
        assert threat is None
    
    @pytest.mark.asyncio
    async def test_audit_delete_attempt(self):
        """Test audit log delete attempt"""
        threat = await BucketThreatDetector.detect_audit_tampering("DELETE", "audit_log")
        assert threat is not None
        assert threat["threat_id"] == "T8_AUDIT_TAMPERING"
        assert threat["severity"] == "CRITICAL"
        assert threat["action"] == "HALT"
    
    @pytest.mark.asyncio
    async def test_audit_update_attempt(self):
        """Test audit log update attempt"""
        threat = await BucketThreatDetector.detect_audit_tampering("UPDATE", "audit_log")
        assert threat is not None

class TestComprehensiveThreatScanning:
    """Test comprehensive threat scanning"""
    
    @pytest.mark.asyncio
    async def test_clean_context(self):
        """Test clean context with no threats"""
        context = {
            "used_gb": 500,
            "metadata": {"key": "value"},
            "actor": "product_ai_assistant",
            "operation": "CREATE",
            "product_id": "AI_ASSISTANT",
            "artifact_type": "ConversationArtifact"
        }
        threats = await BucketThreatDetector.scan_all_threats(context)
        assert len(threats) == 0
    
    @pytest.mark.asyncio
    async def test_multiple_threats(self):
        """Test context with multiple threats"""
        context = {
            "used_gb": 990,  # Storage threat
            "metadata": {"key": "DROP TABLE users"},  # Poisoning threat
            "actor": "ai_agent",
            "operation": "DELETE",  # AI escalation threat
            "product_id": "AI_ASSISTANT",
            "artifact_type": "MediaArtifact"  # Cross-product threat
        }
        threats = await BucketThreatDetector.scan_all_threats(context)
        assert len(threats) > 0
    
    @pytest.mark.asyncio
    async def test_has_critical_threats(self):
        """Test critical threat detection"""
        threats = [
            {"severity": "HIGH"},
            {"severity": "CRITICAL"},
            {"severity": "MEDIUM"}
        ]
        assert BucketThreatDetector.has_critical_threats(threats) == True
    
    @pytest.mark.asyncio
    async def test_no_critical_threats(self):
        """Test no critical threats"""
        threats = [
            {"severity": "HIGH"},
            {"severity": "MEDIUM"}
        ]
        assert BucketThreatDetector.has_critical_threats(threats) == False

class TestThreatDefinitions:
    """Test threat definitions"""
    
    def test_all_threats_defined(self):
        """Test all threats are defined"""
        threats = BucketThreatDetector.THREATS
        assert len(threats) >= 9  # At least 9 threats
        assert "T1_STORAGE_EXHAUSTION" in threats
        assert "T8_AUDIT_TAMPERING" in threats
    
    def test_threat_structure(self):
        """Test threat structure"""
        threat = BucketThreatDetector.get_threat_details("T1_STORAGE_EXHAUSTION")
        assert "name" in threat
        assert "severity" in threat
        assert "escalation" in threat

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
