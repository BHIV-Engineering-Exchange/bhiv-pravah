"""
Control Center E2E suite — localhost pipeline validation.

Requires: Gateway :8000, API_KEY_SECRET, optional Mongo/JWT secrets.
Run: cd backend && python -m pytest tests/e2e/control_center/test_control_center_e2e.py -v -m e2e
"""

from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path

import httpx
import pytest

_E2E_ROOT = Path(__file__).resolve().parent
if str(_E2E_ROOT) not in sys.path:
    sys.path.insert(0, str(_E2E_ROOT))

from framework.auth_helpers import api_key_headers, bearer_headers, login_client_token
from framework.env_check import probe_service
from framework.pipeline_runner import run_control_center_pipeline
from framework.reporter import E2EReporter
from framework.state_capture import capture_state
from framework.state_compare import compare_states

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_env_configuration_documented(e2e_config, e2e_reporter: E2EReporter, env_preflight):
    start = time.perf_counter()
    vite = e2e_config.optional_vite_documentation()
    ok = env_preflight.ok
    e2e_reporter.record(
        "env_preflight",
        passed=ok,
        duration_ms=(time.perf_counter() - start) * 1000,
        detail=env_preflight.message,
        metadata={"warnings": env_preflight.warnings, "vite_vars": vite},
    )
    assert ok


@pytest.mark.asyncio
async def test_service_health_matrix(
    http_client: httpx.AsyncClient,
    e2e_config,
    e2e_reporter: E2EReporter,
    live_services,
):
    for name, url in (
        ("health_gateway", e2e_config.gateway_url),
        ("health_agent", e2e_config.agent_url),
        ("health_langgraph", e2e_config.langgraph_url),
    ):
        start = time.perf_counter()
        status = await probe_service(http_client, url)
        optional = name != "health_gateway"
        passed = status == "up" or optional
        skipped = optional and status != "up"
        e2e_reporter.record(
            name,
            passed=passed,
            duration_ms=(time.perf_counter() - start) * 1000,
            detail=f"{url}/health -> {status}",
            skipped=skipped,
        )
        if name == "health_gateway":
            assert status == "up"


@pytest.mark.asyncio
async def test_unauthenticated_denied(http_client, e2e_config, e2e_reporter: E2EReporter, live_services):
    start = time.perf_counter()
    response = await http_client.get(f"{e2e_config.gateway_url}/metrics/dashboard")
    passed = response.status_code in (401, 403)
    e2e_reporter.record(
        "unauthenticated_metrics_dashboard",
        passed=passed,
        duration_ms=(time.perf_counter() - start) * 1000,
        detail=f"status={response.status_code}",
    )
    assert passed


@pytest.mark.asyncio
async def test_api_key_control_center_endpoints(
    http_client,
    e2e_config,
    api_key_headers_fixture,
    e2e_reporter: E2EReporter,
    live_services,
):
    cid = str(uuid.uuid4())
    headers = {**api_key_headers_fixture, "X-Correlation-ID": cid}
    endpoints = [
        ("GET", "/metrics/dashboard", None),
        ("GET", "/v1/candidates/stats", None),
        ("GET", "/v1/control-center/dashboard-aggregates", None),
        ("GET", "/v1/control-center/audit-events", {"limit": 5}),
        ("GET", "/v1/control-center/audit-replay", None),
    ]
    for method, path, params in endpoints:
        start = time.perf_counter()
        response = await http_client.request(
            method,
            f"{e2e_config.gateway_url}{path}",
            headers=headers,
            params=params,
        )
        corr = response.headers.get("x-correlation-id") or response.headers.get("X-Correlation-ID")
        policy = response.headers.get("x-policy-scope") or response.headers.get("X-Policy-Scope")
        passed = response.status_code == 200
        detail = f"status={response.status_code} correlation={bool(corr)} policy_scope={policy or 'n/a'}"
        if path == "/metrics/dashboard":
            body = response.json() if passed else {}
            passed = passed and "policy_scope" in body
            detail += f" keys={list(body.keys())[:4]}"
        e2e_reporter.record(
            f"api_key_{path.strip('/').replace('/', '_')}",
            passed=passed,
            duration_ms=(time.perf_counter() - start) * 1000,
            detail=detail,
            metadata={"correlation_id": corr},
        )
        assert response.status_code == 200, detail


@pytest.mark.asyncio
async def test_post_audit_event_writes(
    http_client,
    e2e_config,
    api_key_headers_fixture,
    e2e_reporter: E2EReporter,
    live_services,
):
    cid = str(uuid.uuid4())
    headers = {**api_key_headers_fixture, "X-Correlation-ID": cid}
    start = time.perf_counter()
    response = await http_client.post(
        f"{e2e_config.gateway_url}/v1/control-center/audit-events",
        headers=headers,
        json={
            "action": "control_center_view",
            "outcome": "success",
            "detail": "e2e isolated audit write",
            "correlation_id": cid,
        },
    )
    passed = response.status_code == 200 and (response.json() or {}).get("ok") is True
    e2e_reporter.record(
        "post_audit_events",
        passed=passed,
        duration_ms=(time.perf_counter() - start) * 1000,
        detail=f"status={response.status_code}",
    )
    assert passed


@pytest.mark.asyncio
async def test_baseline_pipeline_final_compare(
    http_client,
    e2e_config,
    api_key_headers_fixture,
    e2e_reporter: E2EReporter,
    live_services,
):
    headers = api_key_headers_fixture
    start = time.perf_counter()

    baseline = await capture_state(http_client, e2e_config, label="baseline", auth_headers=headers)
    pipeline = await run_control_center_pipeline(
        http_client, e2e_config, headers, correlation_id=str(uuid.uuid4())
    )
    final = await capture_state(
        http_client,
        e2e_config,
        label="final",
        auth_headers=headers,
        correlation_filter=pipeline.correlation_id,
    )
    comparison = compare_states(
        baseline,
        final,
        pipeline_correlation_id=pipeline.correlation_id,
        require_audit_increase=True,
    )

    e2e_reporter.report.pipeline = {
        "correlation_id": pipeline.correlation_id,
        "ok": pipeline.ok,
        "actions": pipeline.actions,
        "errors": pipeline.errors,
    }
    e2e_reporter.report.compare_result = {
        "passed": comparison.passed,
        "deltas": comparison.deltas,
        "findings": [
            {"name": f.name, "passed": f.passed, "detail": f.detail, "severity": f.severity}
            for f in comparison.findings
        ],
    }

    duration = (time.perf_counter() - start) * 1000
    e2e_reporter.record(
        "baseline_pipeline_final_compare",
        passed=comparison.passed and pipeline.ok,
        duration_ms=duration,
        detail=f"audit_delta={comparison.deltas.get('audit_event_count', {})}",
        metadata={"baseline_errors": baseline.errors, "final_errors": final.errors},
    )
    assert pipeline.ok, pipeline.errors
    assert comparison.passed


@pytest.mark.asyncio
async def test_role_matrix_candidate_denied(
    http_client,
    e2e_config,
    role_tokens,
    e2e_reporter: E2EReporter,
    live_services,
):
    token = role_tokens.get("candidate_jwt")
    if not token:
        e2e_reporter.record(
            "role_candidate_metrics_denied",
            passed=True,
            duration_ms=0,
            detail="CANDIDATE_JWT_SECRET_KEY unset — skipped",
            skipped=True,
        )
        pytest.skip("CANDIDATE_JWT_SECRET_KEY not set")
    start = time.perf_counter()
    response = await http_client.get(
        f"{e2e_config.gateway_url}/metrics/dashboard",
        headers=bearer_headers(token),
    )
    passed = response.status_code == 403
    e2e_reporter.record(
        "role_candidate_metrics_denied",
        passed=passed,
        duration_ms=(time.perf_counter() - start) * 1000,
        detail=f"status={response.status_code}",
    )
    assert passed


@pytest.mark.asyncio
async def test_role_matrix_client_allowed(
    http_client,
    e2e_config,
    role_tokens,
    e2e_reporter: E2EReporter,
    live_services,
):
    token = role_tokens.get("client_jwt")
    if not token:
        token = await login_client_token(http_client, e2e_config)
    if not token:
        e2e_reporter.record(
            "role_client_stats_allowed",
            passed=True,
            duration_ms=0,
            detail="No client JWT — skipped",
            skipped=True,
        )
        pytest.skip("No client JWT available")
    start = time.perf_counter()
    response = await http_client.get(
        f"{e2e_config.gateway_url}/v1/candidates/stats",
        headers=bearer_headers(token),
    )
    body = response.json() if response.status_code == 200 else {}
    scope = (body.get("policy_scope") or {}).get("scope")
    passed = response.status_code == 200 and scope == "client"
    e2e_reporter.record(
        "role_client_stats_allowed",
        passed=passed,
        duration_ms=(time.perf_counter() - start) * 1000,
        detail=f"status={response.status_code} scope={scope}",
    )
    assert passed


@pytest.mark.asyncio
async def test_correlation_id_echo_on_health(
    http_client,
    e2e_config,
    e2e_reporter: E2EReporter,
    live_services,
):
    cid = f"e2e-{uuid.uuid4()}"
    start = time.perf_counter()
    response = await http_client.get(
        f"{e2e_config.gateway_url}/health",
        headers={"X-Correlation-ID": cid},
    )
    echoed = response.headers.get("x-correlation-id") or response.headers.get("X-Correlation-ID")
    passed = response.status_code == 200 and echoed == cid
    e2e_reporter.record(
        "correlation_id_gateway_health",
        passed=passed,
        duration_ms=(time.perf_counter() - start) * 1000,
        detail=f"sent={cid} echoed={echoed}",
    )
    assert passed


@pytest.mark.asyncio
async def test_agent_langgraph_correlation_optional(
    http_client,
    e2e_config,
    e2e_reporter: E2EReporter,
    live_services,
):
    cid = f"e2e-{uuid.uuid4()}"
    for name, base in (("agent", e2e_config.agent_url), ("langgraph", e2e_config.langgraph_url)):
        start = time.perf_counter()
        try:
            response = await http_client.get(
                f"{base}/health",
                headers={"X-Correlation-ID": cid},
                timeout=5.0,
            )
        except httpx.RequestError as exc:
            e2e_reporter.record(
                f"correlation_{name}_health",
                passed=True,
                duration_ms=(time.perf_counter() - start) * 1000,
                detail=f"service down: {exc}",
                skipped=True,
            )
            continue
        if response.status_code != 200:
            e2e_reporter.record(
                f"correlation_{name}_health",
                passed=True,
                duration_ms=(time.perf_counter() - start) * 1000,
                detail=f"http_{response.status_code} — skipped",
                skipped=True,
            )
            continue
        body = response.json()
        echoed = (
            response.headers.get("x-correlation-id")
            or response.headers.get("X-Correlation-ID")
            or body.get("correlation_id")
        )
        passed = bool(echoed)
        e2e_reporter.record(
            f"correlation_{name}_health",
            passed=passed,
            duration_ms=(time.perf_counter() - start) * 1000,
            detail=f"echoed={echoed}",
            skipped=not passed,
        )
