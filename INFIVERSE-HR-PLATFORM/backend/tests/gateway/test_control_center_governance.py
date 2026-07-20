"""
Unit tests for control-center governance (offline, no localhost required).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

GATEWAY_ROOT = Path(__file__).resolve().parents[2] / "services" / "gateway"
if str(GATEWAY_ROOT) not in sys.path:
    sys.path.insert(0, str(GATEWAY_ROOT))

from app.control_center_governance import (  # noqa: E402
    assert_control_center_access,
    audit_doc_to_trace_event,
    resolve_policy_scope,
)

pytestmark = pytest.mark.e2e_unit


def test_resolve_policy_scope_api_key_platform():
    scope = resolve_policy_scope({"type": "api_key"})
    assert scope["scope"] == "platform"
    assert scope["role"] == "admin"


def test_resolve_policy_scope_client():
    scope = resolve_policy_scope({"type": "jwt_token", "role": "client", "user_id": "TECH001"})
    assert scope["scope"] == "client"
    assert scope["scope_label"] == "client:TECH001"


def test_resolve_policy_scope_recruiter():
    scope = resolve_policy_scope({"type": "jwt_token", "role": "recruiter", "user_id": "REC01"})
    assert scope["scope"] == "recruiter"
    assert scope["workforce_category"] == "recruiter_workforce"


def test_assert_control_center_access_candidate_raises():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        assert_control_center_access({"type": "jwt_token", "role": "candidate", "user_id": "c1"})
    assert exc.value.status_code == 403


def test_assert_control_center_access_admin_ok():
    scope = assert_control_center_access({"type": "jwt_token", "role": "admin", "user_id": "a1"})
    assert scope["scope"] == "platform"


def test_audit_doc_to_trace_event_success():
    event = audit_doc_to_trace_event(
        {
            "action": "control_center_view",
            "outcome": "success",
            "correlation_id": "cid-1",
            "context": {"source_system": "gateway"},
            "actor": {"role": "client"},
        }
    )
    assert event["status"] == "success"
    assert event["op"] == "control_center_view"
    assert event["correlation_id"] == "cid-1"


def test_scoped_empty_stats_shape():
    from app.control_center_governance import _empty_stats

    scope = resolve_policy_scope({"type": "jwt_token", "role": "client", "user_id": "X"})
    stats = _empty_stats(scope, "scoped_empty")
    assert stats["total_candidates"] == 0
    assert stats["policy_scope"]["scope"] == "client"
    assert stats["data_source"] == "scoped_empty"
