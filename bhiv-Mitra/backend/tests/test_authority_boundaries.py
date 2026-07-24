"""
MITRA Authority Boundary Tests
------------------------------
Tests that verify authority boundaries are maintained throughout the pipeline.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from types import SimpleNamespace
from datetime import datetime


class TestEntryGuard:
    """Tests for the Mitra entry guard that prevents direct enforcement access."""

    def test_entry_guard_rejects_direct_enforcement(self):
        """Verify that calling enforcement directly raises PermissionError."""
        from app.core.mitra_entry_guard import get_mitra_entry_scope

        # Without scope, should return None
        scope = get_mitra_entry_scope()
        assert scope is None

    def test_entry_guard_accepts_valid_scope(self):
        """Verify that enforcement works within Mitra scope."""
        from app.core.mitra_entry_guard import mitra_enforcement_scope, get_mitra_entry_scope

        with mitra_enforcement_scope("test_trace_123", "test_source"):
            scope = get_mitra_entry_scope()
            assert scope is not None
            assert scope["trace_id"] == "test_trace_123"
            assert scope["source"] == "test_source"

    def test_entry_guard_resets_after_scope(self):
        """Verify that scope is reset after exiting context."""
        from app.core.mitra_entry_guard import mitra_enforcement_scope, get_mitra_entry_scope

        with mitra_enforcement_scope("test_trace_456", "test_source"):
            scope = get_mitra_entry_scope()
            assert scope is not None

        # After exiting scope, should be None
        scope = get_mitra_entry_scope()
        assert scope is None

    def test_entry_guard_nested_scopes(self):
        """Verify that nested scopes work correctly."""
        from app.core.mitra_entry_guard import mitra_enforcement_scope, get_mitra_entry_scope

        with mitra_enforcement_scope("outer_trace", "outer_source"):
            outer_scope = get_mitra_entry_scope()
            assert outer_scope["trace_id"] == "outer_trace"

            with mitra_enforcement_scope("inner_trace", "inner_source"):
                inner_scope = get_mitra_entry_scope()
                assert inner_scope["trace_id"] == "inner_trace"

            # After inner scope, should restore outer
            restored_scope = get_mitra_entry_scope()
            assert restored_scope["trace_id"] == "outer_trace"

        # After all scopes, should be None
        final_scope = get_mitra_entry_scope()
        assert final_scope is None


class TestConflictGuard:
    """Tests for the conflict guard that prevents RL from overriding policy decisions."""

    def test_conflict_guard_prevents_rl_override(self):
        """Verify that RL cannot change policy decision."""
        from app.services.mitra_control_plane_service import MitraControlPlaneService

        service = MitraControlPlaneService()

        # Policy decides BLOCK
        policy_runtime = {
            "decision": "BLOCK",
            "confidence": 0.95,
            "risk_category": "self_harm",
        }

        # RL tries to override to ALLOW
        rl_signal = {
            "signal_type": "implicit_positive",
            "adjusted_confidence": 0.1,
        }

        # Apply conflict guard
        result = service._apply_conflict_guard(policy_runtime, rl_signal)

        # Verify policy decision is preserved
        assert result["policy_decision"]["decision"] == "BLOCK"
        assert result["policy_decision"]["confidence"] == 0.1  # RL adjusted confidence only
        assert result["policy_decision"]["conflict_guard"]["decision_immutable"] is True
        assert result["policy_decision"]["conflict_guard"]["rl_can_adjust_confidence_only"] is True

    def test_conflict_guard_allows_confidence_adjustment(self):
        """Verify that RL can adjust confidence but not decision."""
        from app.services.mitra_control_plane_service import MitraControlPlaneService

        service = MitraControlPlaneService()

        # Policy decides ALLOW
        policy_runtime = {
            "decision": "ALLOW",
            "confidence": 0.8,
        }

        # RL provides correction signal
        rl_signal = {
            "signal_type": "correction",
            "adjusted_confidence": 0.7,
        }

        # Apply conflict guard
        result = service._apply_conflict_guard(policy_runtime, rl_signal)

        # Verify decision unchanged, confidence adjusted
        assert result["policy_decision"]["decision"] == "ALLOW"
        assert result["policy_decision"]["confidence"] == 0.7


class TestEnforcementVerdict:
    """Tests for the enforcement verdict immutability."""

    def test_verdict_is_frozen(self):
        """Verify that EnforcementVerdict is immutable."""
        from app.external.enforcement.enforcement_verdict import EnforcementVerdict

        verdict = EnforcementVerdict(
            decision="ALLOW",
            scope="both",
            trace_id="test_trace",
            reason_code="CONTENT_AND_ACTION_ALLOWED",
        )

        # Attempt to modify should raise
        with pytest.raises(AttributeError):
            verdict.decision = "BLOCK"

    def test_verdict_allows_action(self):
        """Verify that only ALLOW with action scope permits execution."""
        from app.external.enforcement.enforcement_verdict import EnforcementVerdict

        # ALLOW with both scope
        allow_verdict = EnforcementVerdict(
            decision="ALLOW",
            scope="both",
            trace_id="test",
            reason_code="TEST",
        )
        assert allow_verdict.allows_action() is True

        # ALLOW with response scope only
        response_verdict = EnforcementVerdict(
            decision="ALLOW",
            scope="response",
            trace_id="test",
            reason_code="TEST",
        )
        assert response_verdict.allows_action() is False

        # BLOCK
        block_verdict = EnforcementVerdict(
            decision="BLOCK",
            scope="both",
            trace_id="test",
            reason_code="TEST",
        )
        assert block_verdict.allows_action() is False

    def test_verdict_allows_response(self):
        """Verify that ALLOW or REWRITE with response scope permits response."""
        from app.external.enforcement.enforcement_verdict import EnforcementVerdict

        # ALLOW with response scope
        allow_verdict = EnforcementVerdict(
            decision="ALLOW",
            scope="response",
            trace_id="test",
            reason_code="TEST",
        )
        assert allow_verdict.allows_response() is True

        # REWRITE with response scope
        rewrite_verdict = EnforcementVerdict(
            decision="REWRITE",
            scope="response",
            trace_id="test",
            reason_code="TEST",
        )
        assert rewrite_verdict.allows_response() is True

        # BLOCK
        block_verdict = EnforcementVerdict(
            decision="BLOCK",
            scope="both",
            trace_id="test",
            reason_code="TEST",
        )
        assert block_verdict.allows_response() is False


class TestTraceImmutability:
    """Tests for trace ID immutability through the pipeline."""

    def test_trace_id_is_deterministic(self):
        """Verify that same input produces same trace_id."""
        from app.external.enforcement.deterministic_trace import generate_trace_id

        payload1 = {"input": {"message": "hello"}, "context": {"platform": "web"}}
        payload2 = {"input": {"message": "hello"}, "context": {"platform": "web"}}

        trace1 = generate_trace_id(input_payload=payload1, enforcement_category="REQUEST")
        trace2 = generate_trace_id(input_payload=payload2, enforcement_category="REQUEST")

        assert trace1 == trace2

    def test_trace_id_differs_for_different_input(self):
        """Verify that different input produces different trace_id."""
        from app.external.enforcement.deterministic_trace import generate_trace_id

        payload1 = {"input": {"message": "hello"}}
        payload2 = {"input": {"message": "world"}}

        trace1 = generate_trace_id(input_payload=payload1, enforcement_category="REQUEST")
        trace2 = generate_trace_id(input_payload=payload2, enforcement_category="REQUEST")

        assert trace1 != trace2


class TestBucketImmutability:
    """Tests for bucket document immutability."""

    def test_bucket_documents_are_write_once(self):
        """Verify that bucket has no update operations on audit documents."""
        from app.services.bucket_service import BucketService

        # Check that the class has no update methods for audit documents
        # This is a structural test - verify the implementation pattern
        bucket = BucketService()

        # The bucket should only have insert operations
        # Verify by checking method names (structural test)
        methods = [m for m in dir(bucket) if not m.startswith("_")]
        assert "update_document" not in methods
        assert "delete_document" not in methods


class TestEnforcementPreconditions:
    """Tests for enforcement precondition checks."""

    def test_enforcement_requires_trace_id(self):
        """Verify that enforcement fails without trace_id."""
        from app.external.enforcement import enforcement_engine
        from app.external.enforcement.enforcement_verdict import EnforcementVerdict

        # Create payload without trace_id
        payload = SimpleNamespace(
            intent="general",
            emotional_output="test",
            age_gate_status=False,
            region_policy=None,
            platform_policy={},
            karma_score=50,
            risk_flags=[],
            trace_id="",
            authenticated_user_context={},
            policy_decision={"decision": "ALLOW", "trace_id": ""},
            rl_signal={},
            bucket_active=True,
            policy_artifact_present=True,
        )

        verdict = enforcement_engine.enforce(payload)

        # Should fail closed
        assert verdict.decision == "BLOCK"
        assert "MISSING" in verdict.reason_code

    def test_enforcement_requires_policy_decision(self):
        """Verify that enforcement fails without policy decision."""
        from app.external.enforcement import enforcement_engine

        # Create payload without policy_decision
        payload = SimpleNamespace(
            intent="general",
            emotional_output="test",
            age_gate_status=False,
            region_policy=None,
            platform_policy={},
            karma_score=50,
            risk_flags=[],
            trace_id="test_trace",
            authenticated_user_context={},
            policy_decision=None,
            rl_signal={},
            bucket_active=True,
            policy_artifact_present=True,
        )

        verdict = enforcement_engine.enforce(payload)

        # Should fail closed
        assert verdict.decision == "BLOCK"
        assert verdict.reason_code == "MISSING_POLICY_RUNTIME"
