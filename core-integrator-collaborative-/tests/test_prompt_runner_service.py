import importlib.util
from pathlib import Path
from fastapi.testclient import TestClient

_module_path = Path(__file__).resolve().parents[1] / "prompt-runner01" / "run_server.py"
_spec = importlib.util.spec_from_file_location("prompt_runner_service", _module_path)
_module = importlib.util.module_from_spec(_spec)
assert _spec is not None and _spec.loader is not None
_spec.loader.exec_module(_module)
app = _module.app


client = TestClient(app)


def test_prompt_runner_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "prompt_runner"


def test_prompt_runner_generate_extracts_video():
    payload = {"prompt": "Create a video lesson about Python basics", "origin": "ttv"}
    resp = client.post("/generate", json=payload)
    body = resp.json()
    assert resp.status_code == 200
    assert body["module"] == "video"
    assert "generate_video_script" in body["tasks"]
    assert body["product_context"] == "ttv"


def test_prompt_runner_generate_defaults():
    resp = client.post("/generate", json={"prompt": "Build a project plan"})
    body = resp.json()
    assert resp.status_code == 200
    assert body["module"] == "creator"
    assert body["intent"] == "generate"
    assert body["output_format"] == "json"
