"""
Tests for production hardening:
- Malformed list fields fail-closed
- API request size limit (413)
- API HTTP error handlers (404, 405)
- Bucket MAX_ENTRIES eviction
- InsightFlow MAX_EVENTS eviction
- Non-ValueError exceptions in pipeline layers are caught (fail-closed)
"""

import copy

import pytest

from analyzer.analyze_blockage import analyze_and_recommend
from tantra import bucket, insightflow
from tantra.pipeline import run_tantra_pipeline

VALID_INPUT = {
    "trace_id": "prod-trace-001",
    "execution_id": "exec-prod-001",
    "tasks": [{"task_id": "T1", "depends_on": []}],
    "constraint_results": [{"task_id": "T1", "is_valid": False, "unsatisfied_dependencies": []}],
    "propagation_results": [{"task_id": "T1", "affected_tasks": [], "impact_score": 5}],
}

FAIL_RESPONSE = {"status": "FAIL", "reason": "INVALID_INPUT_CONTRACT", "trace_id": ""}


@pytest.fixture(autouse=True)
def reset_stores():
    bucket.clear()
    insightflow.clear()
    yield
    bucket.clear()
    insightflow.clear()


# ── malformed list fields ─────────────────────────────────────────────────────

@pytest.mark.parametrize("field", ["tasks", "constraint_results", "propagation_results"])
def test_malformed_list_field_fails_closed(field):
    """Non-list value for list fields must return FAIL — no unhandled TypeError."""
    bad = {"trace_id": "t", "execution_id": "e", field: "not-a-list"}
    assert analyze_and_recommend(bad) == FAIL_RESPONSE


# ── pipeline catches non-ValueError layer exceptions ─────────────────────────

def test_pipeline_catches_unexpected_rajya_exception(monkeypatch):
    from tantra import rajya
    monkeypatch.setattr(rajya, "consume", lambda _o, _t: (_ for _ in ()).throw(RuntimeError("boom")))
    result = run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    assert result["status"] == "FAIL"
    assert len(bucket.all_trace_ids()) == 0


def test_pipeline_catches_unexpected_sarathi_exception(monkeypatch):
    from tantra import sarathi
    monkeypatch.setattr(sarathi, "enforce", lambda _: (_ for _ in ()).throw(RuntimeError("boom")))
    result = run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    assert result["status"] == "FAIL"
    assert len(bucket.all_trace_ids()) == 0


def test_pipeline_catches_unexpected_core_exception(monkeypatch):
    from tantra import core
    monkeypatch.setattr(core, "execute", lambda _: (_ for _ in ()).throw(RuntimeError("boom")))
    result = run_tantra_pipeline(copy.deepcopy(VALID_INPUT))
    assert result["status"] == "FAIL"
    assert len(bucket.all_trace_ids()) == 0


# ── bucket eviction ───────────────────────────────────────────────────────────

def test_bucket_evicts_oldest_when_full(monkeypatch):
    """Bucket must not grow beyond MAX_ENTRIES; oldest entry is evicted."""
    monkeypatch.setattr(bucket, "MAX_ENTRIES", 3)
    for i in range(4):
        inp = {**VALID_INPUT, "trace_id": f"evict-trace-{i}", "execution_id": f"exec-{i}"}
        run_tantra_pipeline(inp)
    ids = bucket.all_trace_ids()
    assert len(ids) == 3
    assert "evict-trace-0" not in ids
    assert "evict-trace-3" in ids


# ── insightflow eviction ──────────────────────────────────────────────────────

def test_insightflow_evicts_oldest_when_full(monkeypatch):
    """InsightFlow must not grow beyond MAX_EVENTS; oldest event is evicted."""
    monkeypatch.setattr(insightflow, "MAX_EVENTS", 3)
    for i in range(4):
        inp = {**VALID_INPUT, "trace_id": f"if-trace-{i}", "execution_id": f"exec-{i}"}
        run_tantra_pipeline(inp)
    events = insightflow.get_events()
    assert len(events) == 3
    assert events[0]["trace_id"] == "if-trace-1"
    assert events[-1]["trace_id"] == "if-trace-3"


# ── API error handlers ────────────────────────────────────────────────────────

@pytest.fixture()
def client():
    from api import app
    from fastapi.testclient import TestClient
    yield TestClient(app)


def test_api_404(client):
    resp = client.get("/nonexistent")
    assert resp.status_code == 404
    assert resp.json()["reason"] == "NOT_FOUND"


def test_api_405(client):
    resp = client.get("/analyze")
    assert resp.status_code == 405
    assert resp.json()["reason"] == "METHOD_NOT_ALLOWED"


def test_api_413_request_too_large(client, monkeypatch):
    import api
    monkeypatch.setattr(api, "MAX_CONTENT_LENGTH", 1)  # 1 byte limit
    resp = client.post(
        "/analyze",
        content=b'{"trace_id":"t","execution_id":"e"}',
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 413
    assert resp.json()["reason"] == "REQUEST_TOO_LARGE"


def test_api_415_wrong_content_type(client):
    resp = client.post("/analyze", content=b"hello", headers={"content-type": "text/plain"})
    assert resp.status_code == 415


def test_api_400_invalid_json(client):
    resp = client.post("/analyze", content=b"{bad json", headers={"content-type": "application/json"})
    assert resp.status_code == 400
