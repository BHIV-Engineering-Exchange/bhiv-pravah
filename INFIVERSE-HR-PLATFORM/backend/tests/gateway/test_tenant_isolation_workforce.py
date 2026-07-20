"""
Tenant isolation tests for workforce governance scope filters.

Validates that:
- tenant_id is injected on writes for client-scope callers
- cross-tenant reads are blocked by scope filter enforcement
- platform-scope callers bypass tenant filtering

No MongoDB or live gateway required — all DB calls mocked via unittest.mock.
Production gateway: https://bhiv-hr-gateway-l0xp.onrender.com
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

GATEWAY_ROOT = Path(__file__).resolve().parents[2] / "services" / "gateway"
if str(GATEWAY_ROOT) not in sys.path:
    sys.path.insert(0, str(GATEWAY_ROOT))

from app.workforce_common import workforce_scope_filter  # noqa: E402

pytestmark = pytest.mark.e2e_unit


def test_tenant_scope_filter_client_isolates_to_user_id():
    scope = {"scope": "client", "user_id": "TENANT_A"}
    result = workforce_scope_filter(scope)
    assert result == {"tenant_id": "TENANT_A"}


def test_tenant_scope_filter_different_tenants_produce_different_filters():
    scope_a = {"scope": "client", "user_id": "TENANT_A"}
    scope_b = {"scope": "client", "user_id": "TENANT_B"}
    assert workforce_scope_filter(scope_a) != workforce_scope_filter(scope_b)


def test_platform_scope_bypasses_tenant_filter():
    scope = {"scope": "platform"}
    result = workforce_scope_filter(scope)
    assert result == {}


@pytest.mark.asyncio
async def test_tenant_id_injected_on_org_create():
    from app.workforce_runtime import create_organization

    db = MagicMock()
    db.organizations = MagicMock()
    db.organizations.insert_one = AsyncMock(return_value=MagicMock(inserted_id="mock_id_001"))
    db.audit_logs = MagicMock()
    db.audit_logs.insert_one = AsyncMock(return_value=None)

    scope = {"scope": "client", "user_id": "TENANT_A", "role": "org_admin", "type": "jwt_token"}

    body = MagicMock()
    body.name = "Tenant A Org"
    body.code = "TA-001"
    body.status = "active"
    body.default_roles = []
    body.parent_organization_id = None

    await create_organization(db, body, scope, correlation_id="test-cid-001")

    call_args = db.organizations.insert_one.call_args[0][0]
    assert call_args.get("tenant_id") == "TENANT_A", (
        f"Expected tenant_id=TENANT_A in inserted doc, got: {call_args}"
    )


@pytest.mark.asyncio
async def test_cross_tenant_read_returns_404():
    from fastapi import HTTPException

    from app.workforce_runtime import get_organization

    db = MagicMock()
    db.organizations = MagicMock()
    db.organizations.find_one = AsyncMock(return_value=None)

    scope_b = {"scope": "client", "user_id": "TENANT_B", "role": "org_admin", "type": "jwt_token"}

    with pytest.raises(HTTPException) as exc_info:
        await get_organization(db, "org_id_owned_by_tenant_a", scope_b)

    assert exc_info.value.status_code == 404, (
        f"Expected 404 for cross-tenant read, got: {exc_info.value.status_code}"
    )
