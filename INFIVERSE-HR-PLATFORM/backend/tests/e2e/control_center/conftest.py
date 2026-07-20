"""Pytest fixtures for Control Center E2E (localhost)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import pytest

# Ensure framework imports resolve when running from repo root or backend/
_E2E_ROOT = Path(__file__).resolve().parent
if str(_E2E_ROOT) not in sys.path:
    sys.path.insert(0, str(_E2E_ROOT))

from framework.auth_helpers import api_key_headers, build_role_tokens
from framework.config import E2EConfig
from framework.env_check import check_env_config, check_services
from framework.reporter import E2EReporter

pytestmark = [pytest.mark.e2e]


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: Control Center localhost end-to-end tests")
    config.addinivalue_line("markers", "e2e_unit: offline unit tests for E2E helpers")


@pytest.fixture(scope="session")
def e2e_config() -> E2EConfig:
    return E2EConfig.from_env()


@pytest.fixture(scope="session")
def e2e_reporter(e2e_config: E2EConfig) -> E2EReporter:
    return E2EReporter(gateway_url=e2e_config.gateway_url)


@pytest.fixture(scope="session")
def env_preflight(e2e_config: E2EConfig):
    """Fail fast when API key missing; skip live tests if gateway down."""
    env = check_env_config(e2e_config)
    env.raise_if_blocked()
    return env


@pytest.fixture(scope="session")
async def live_services(e2e_config: E2EConfig, env_preflight):
    """Probe gateway/agent/langgraph; skip E2E if gateway unavailable."""
    result = await check_services(e2e_config, require_gateway=True)
    if not result.ok:
        pytest.skip(result.message)
    return result


@pytest.fixture
async def http_client(e2e_config: E2EConfig):
    timeout = httpx.Timeout(e2e_config.request_timeout_s)
    async with httpx.AsyncClient(timeout=timeout) as client:
        yield client


@pytest.fixture
def api_key_headers_fixture(e2e_config: E2EConfig):
    return api_key_headers(e2e_config.api_key_secret)


@pytest.fixture(scope="session")
def role_tokens(e2e_config: E2EConfig):
    return build_role_tokens(e2e_config)


@pytest.fixture(scope="session", autouse=True)
def _write_report_on_session_end(e2e_reporter: E2EReporter, e2e_config: E2EConfig):
    yield
    results_dir = os.path.abspath(e2e_config.results_dir)
    os.makedirs(results_dir, exist_ok=True)
    path = os.path.join(results_dir, "control_center_e2e_report.json")
    e2e_reporter.write_json(path)
    e2e_reporter.print_console_summary()
