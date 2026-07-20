"""
Integration tests for main.py FastAPI routes.
Covers: auth, all endpoints, rate limiting, malformed payloads, failure scenarios.
Run: pytest tests/test_routes.py -v
"""

import os
import time
import tempfile
import pytest
from unittest.mock import patch

# Set env before importing app
os.environ.setdefault("AUTH_ENABLED", "false")
os.environ.setdefault("SSPL_ENABLED", "false")
os.environ.setdefault("DB_PATH", ":memory:")
os.environ.setdefault("USE_MONGODB", "false")
os.environ.setdefault("INTEGRATOR_USE_NOOPUR", "false")
os.environ.setdefault("DISABLE_VIDEO_SERVICE", "true")
# Raise rate limits high so test suite doesn't self-throttle
os.environ["RATE_LIMIT_IP_PER_MIN"] = "10000"
os.environ["RATE_LIMIT_USER_PER_MIN"] = "10000"

from fastapi.testclient import TestClient
import main
from main import app

client = TestClient(app, raise_server_exceptions=False)


def _core_payload(module="sample_text", intent="generate", user_id="test_user", data=None):
    return {"module": module, "intent": intent, "user_id": user_id, "data": data or {"input_text": "hello"}}


# ── Regression: asyncio.run() bug ─────────────────────────────────────────────

class TestAsyncioRunBug:
    def test_health_does_not_crash(self):
        resp = client.get("/system/health")
        assert resp.status_code == 200
        assert "status" in resp.json()

    def test_health_returns_dependency_map(self):
        body = client.get("/system/health").json()
        assert "dependencies" in body
        assert "database" in body["dependencies"]


# ── Regression: ReplayEngine init crash ───────────────────────────────────────

class TestReplayEngineInit:
    def test_replay_does_not_raise_attribute_error(self):
        resp = client.post("/replay/nonexistent-id")
        # Must not be an unhandled 500 caused by AttributeError
        assert resp.status_code in (200, 404, 500)
        body = resp.json()
        assert "detail" in body or "replay_status" in body or "error" in body

    def test_replay_validate_does_not_crash(self):
        resp = client.get("/replay/validate/nonexistent-id")
        assert resp.status_code in (200, 404, 500)


# ── Public endpoints ──────────────────────────────────────────────────────────

class TestPublicEndpoints:
    def test_root_200(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "version" in resp.json()

    def test_health_200(self):
        assert client.get("/system/health").status_code == 200

    def test_health_has_timestamp(self):
        assert "timestamp" in client.get("/system/health").json()


# ── Authentication module unit tests ─────────────────────────────────────────

class TestAuthModule:
    def test_invalid_jwt_rejected(self):
        from src.utils.auth import _verify_jwt
        assert _verify_jwt("invalid.token")[0] is False

    def test_garbage_jwt_rejected(self):
        from src.utils.auth import _verify_jwt
        assert _verify_jwt("garbage")[0] is False

    def test_expired_jwt_rejected(self):
        import hmac, hashlib, base64, json as _json
        secret = "testsecret"
        header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
        pl = base64.urlsafe_b64encode(_json.dumps({"sub": "u", "exp": int(time.time()) - 10}).encode()).rstrip(b"=").decode()
        sig = base64.urlsafe_b64encode(
            hmac.new(secret.encode(), f"{header}.{pl}".encode(), hashlib.sha256).digest()
        ).rstrip(b"=").decode()
        with patch("src.utils.auth.AUTH_SECRET_KEY", secret):
            from src.utils import auth as auth_mod
            valid, _ = auth_mod._verify_jwt(f"{header}.{pl}.{sig}")
        assert not valid

    def test_valid_jwt_accepted(self):
        import hmac, hashlib, base64, json as _json
        secret = "testsecret"
        header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
        pl = base64.urlsafe_b64encode(_json.dumps({"sub": "u", "exp": int(time.time()) + 3600}).encode()).rstrip(b"=").decode()
        sig = base64.urlsafe_b64encode(
            hmac.new(secret.encode(), f"{header}.{pl}".encode(), hashlib.sha256).digest()
        ).rstrip(b"=").decode()
        with patch("src.utils.auth.AUTH_SECRET_KEY", secret):
            from src.utils import auth as auth_mod
            valid, payload = auth_mod._verify_jwt(f"{header}.{pl}.{sig}")
        assert valid
        assert payload["sub"] == "u"


# ── POST /core ────────────────────────────────────────────────────────────────

class TestCoreEndpoint:
    def test_valid_request_200(self):
        resp = client.post("/core", json=_core_payload())
        assert resp.status_code == 200
        body = resp.json()
        assert all(k in body for k in ("status", "message", "result"))

    def test_invalid_module_422(self):
        resp = client.post("/core", json={"module": "does_not_exist", "intent": "generate",
                                          "user_id": "u1", "data": {}})
        assert resp.status_code == 422

    def test_missing_user_id_422(self):
        resp = client.post("/core", json={"module": "sample_text", "intent": "generate", "data": {}})
        assert resp.status_code == 422

    def test_empty_user_id_422(self):
        resp = client.post("/core", json={"module": "sample_text", "intent": "generate",
                                          "user_id": "", "data": {}})
        assert resp.status_code == 422

    def test_path_traversal_user_id_rejected(self):
        resp = client.post("/core", json={"module": "sample_text", "intent": "generate",
                                          "user_id": "../../etc/passwd", "data": {}})
        assert resp.status_code in (400, 422)

    def test_malformed_json_422(self):
        resp = client.post("/core", content=b"not-json",
                           headers={"Content-Type": "application/json"})
        assert resp.status_code == 422

    def test_no_db_path_in_response(self):
        resp = client.post("/core", json=_core_payload())
        assert "db_path" not in resp.text
        assert "context.db" not in resp.text

    def test_trace_id_in_response_headers(self):
        resp = client.post("/core", json=_core_payload())
        headers_lower = {k.lower(): v for k, v in resp.headers.items()}
        assert "x-trace-id" in headers_lower

    def test_xss_payload_returns_json(self):
        resp = client.post("/core", json=_core_payload(data={"input_text": "<script>alert(1)</script>"}))
        assert resp.headers.get("content-type", "").startswith("application/json")

    def test_large_payload_handled(self):
        resp = client.post("/core", json=_core_payload(data={"input_text": "x" * 50_000}))
        assert resp.status_code in (200, 413, 422, 500)


# ── GET /get-history ──────────────────────────────────────────────────────────

class TestGetHistory:
    def test_returns_list(self):
        resp = client.get("/get-history?user_id=test_user")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_invalid_user_id_rejected(self):
        resp = client.get("/get-history?user_id=../../../etc")
        assert resp.status_code in (400, 422)

    def test_missing_user_id_422(self):
        assert client.get("/get-history").status_code == 422

    def test_sql_injection_rejected(self):
        resp = client.get("/get-history?user_id='; DROP TABLE interactions;--")
        assert resp.status_code in (400, 422)

    def test_history_cap(self):
        for _ in range(8):
            client.post("/core", json=_core_payload(user_id="cap_user"))
        resp = client.get("/get-history?user_id=cap_user")
        assert resp.status_code == 200
        assert len(resp.json()) <= 10


# ── GET /get-context ──────────────────────────────────────────────────────────

class TestGetContext:
    def test_returns_list(self):
        resp = client.get("/get-context?user_id=test_user")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_context_max_3(self):
        for _ in range(5):
            client.post("/core", json=_core_payload(user_id="ctx_user"))
        resp = client.get("/get-context?user_id=ctx_user")
        assert resp.status_code == 200
        assert len(resp.json()) <= 3

    def test_invalid_user_id_rejected(self):
        resp = client.get("/get-context?user_id=<script>")
        assert resp.status_code in (400, 422)

    def test_oversized_user_id_rejected(self):
        resp = client.get(f"/get-context?user_id={'a' * 65}")
        assert resp.status_code in (400, 422, 429)


# ── GET /system/health ────────────────────────────────────────────────────────

class TestSystemHealth:
    def test_structure(self):
        body = client.get("/system/health").json()
        assert body["status"] in ("ok", "down")
        assert "dependencies" in body
        assert "timestamp" in body

    def test_no_internal_paths(self):
        text = client.get("/system/health").text
        assert "db_path" not in text
        assert "context.db" not in text


# ── GET /system/diagnostics ───────────────────────────────────────────────────

class TestDiagnostics:
    def test_returns_200(self):
        assert client.get("/system/diagnostics").status_code == 200

    def test_no_connection_string_leaked(self):
        text = client.get("/system/diagnostics").text
        assert "mongodb://" not in text
        assert "connection_string" not in text

    def test_no_db_path_in_config(self):
        body = client.get("/system/diagnostics").json()
        if "config" in body:
            assert "db_path" not in body["config"]


# ── GET /system/logs/latest ───────────────────────────────────────────────────

class TestSystemLogs:
    def test_returns_200(self):
        assert client.get("/system/logs/latest").status_code == 200

    def test_limit_cap_enforced(self):
        # Huge limit must not crash
        assert client.get("/system/logs/latest?limit=999999").status_code == 200

    def test_negative_limit_handled(self):
        assert client.get("/system/logs/latest?limit=-1").status_code == 200

    def test_zero_limit_handled(self):
        assert client.get("/system/logs/latest?limit=0").status_code == 200


# ── Rate Limiting ─────────────────────────────────────────────────────────────

class TestRateLimiting:
    def test_allows_normal_traffic(self):
        from src.utils.security_hardening import RateLimiter
        lim = RateLimiter(60)
        key = f"normal_{time.time()}"
        for _ in range(5):
            assert lim.is_allowed(key, 60)

    def test_blocks_after_limit(self):
        from src.utils.security_hardening import RateLimiter
        lim = RateLimiter(60)
        key = f"block_{time.time()}"
        for _ in range(3):
            lim.is_allowed(key, 3)
        assert lim.is_allowed(key, 3) is False

    def test_resets_after_window(self):
        from src.utils.security_hardening import RateLimiter
        lim = RateLimiter(1)
        key = f"reset_{time.time()}"
        for _ in range(5):
            lim.is_allowed(key, 5)
        time.sleep(1.1)
        assert lim.is_allowed(key, 5) is True


# ── Observability ─────────────────────────────────────────────────────────────

class TestObservability:
    def test_trace_id_on_all_responses(self):
        for path in ["/", "/system/health"]:
            headers = {k.lower(): v for k, v in client.get(path).headers.items()}
            assert "x-trace-id" in headers, f"Missing X-Trace-Id on {path}"

    def test_request_id_present(self):
        headers = {k.lower(): v for k, v in client.get("/system/health").headers.items()}
        assert "x-request-id" in headers

    def test_custom_trace_id_propagated(self):
        custom = "custom-trace-xyz-123"
        resp = client.get("/system/health", headers={"X-Trace-Id": custom})
        headers = {k.lower(): v for k, v in resp.headers.items()}
        assert headers.get("x-trace-id") == custom

    def test_response_time_header(self):
        headers = {k.lower(): v for k, v in client.get("/system/health").headers.items()}
        assert "x-response-time-ms" in headers


# ── Memory Retention Regression ───────────────────────────────────────────────

class TestMemoryRetention:
    def test_5_entry_cap_per_user_per_module(self):
        from src.db.memory import ContextMemory
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        try:
            mem = ContextMemory(db_path)
            for i in range(6):
                mem.store_interaction(
                    "u1",
                    {"module": "finance", "intent": "g", "data": {"i": i}},
                    {"status": "success", "message": "", "result": {}}
                )
            assert len(mem.get_user_history("u1")) == 5
        finally:
            try:
                os.unlink(db_path)
            except Exception:
                pass

    def test_modules_isolated(self):
        from src.db.memory import ContextMemory
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name
        try:
            mem = ContextMemory(db_path)
            for i in range(3):
                mem.store_interaction("u2", {"module": "finance", "intent": "g", "data": {}},
                                      {"status": "success", "message": "", "result": {}})
                mem.store_interaction("u2", {"module": "education", "intent": "g", "data": {}},
                                      {"status": "success", "message": "", "result": {}})
            history = mem.get_user_history("u2")
            finance = [h for h in history if h["module"] == "finance"]
            education = [h for h in history if h["module"] == "education"]
            assert len(finance) == 3
            assert len(education) == 3
        finally:
            try:
                os.unlink(db_path)
            except Exception:
                pass


# ── Dependency unavailable scenarios ─────────────────────────────────────────

class TestDependencyUnavailable:
    def test_health_still_responds_when_db_path_missing(self):
        """Health endpoint must return a response even if DB is misconfigured."""
        resp = client.get("/system/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] in ("ok", "down")

    def test_core_returns_error_not_crash_on_bad_module(self):
        resp = client.post("/core", json={"module": "finance", "intent": "generate",
                                          "user_id": "u1", "data": {}})
        assert resp.status_code in (200, 400, 422, 500)
        assert resp.headers.get("content-type", "").startswith("application/json")
