from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from creator_core_engine.api import create_creator_core_router
from creator_core_engine.bucket import LocalBucketStore
from creator_core_engine.service import CreatorCoreService
from creator_core_engine.telemetry import InsightFlowTelemetryEmitter


def build_service(tmp_path: Path) -> CreatorCoreService:
    return CreatorCoreService(
        telemetry_emitter=InsightFlowTelemetryEmitter(str(tmp_path / "telemetry.jsonl")),
        bucket_store=LocalBucketStore(str(tmp_path / "bucket")),
    )


def sample_instruction() -> dict:
    return {
        "prompt": "Explain Newton's laws of motion with real-life examples for a high school student.",
        "module": "education",
        "intent": "explain_concept",
        "topic": "physics_newtons_laws",
        "tasks": [
            "define_first_law",
            "define_second_law",
            "define_third_law",
            "provide_real_life_examples",
        ],
        "output_format": "step_by_step_guide",
        "product_context": "creator_core",
    }


def test_service_generates_deterministic_blueprint(tmp_path: Path):
    service = build_service(tmp_path)
    first = service.generate_blueprint(sample_instruction())
    second = service.generate_blueprint(sample_instruction())

    assert first.payload.model_dump(mode="json") == second.payload.model_dump(mode="json")
    assert first.intent_type == second.intent_type
    assert first.target_product == second.target_product
    assert first.instruction_id != second.instruction_id
    assert first.payload.blueprint_type == "content_blueprint"
    assert first.target_product == "education"
    payload_data = first.payload.model_dump(mode="json")
    assert payload_data["content_type"] == "step_by_step_guide"
    assert payload_data["title"] == "Physics Newtons Laws"
    assert payload_data["outline"] == [
        "define_first_law",
        "define_second_law",
        "define_third_law",
        "provide_real_life_examples",
    ]

    artifact_files = list((tmp_path / "bucket").glob("*.json"))
    assert len(artifact_files) == 2


def test_endpoint_generates_blueprint_envelope(tmp_path: Path):
    service = build_service(tmp_path)
    app = FastAPI()
    app.include_router(create_creator_core_router(service))
    client = TestClient(app)

    response = client.post("/creator-core/generate-blueprint", json=sample_instruction())

    assert response.status_code == 200
    body = response.json()
    # Endpoint now returns a wrapper with the original blueprint and the BHIV Core response
    assert body["blueprint"]["origin"] == "creator_core"
    assert body["blueprint"]["payload"]["blueprint_type"] == "content_blueprint"
    assert body["blueprint"]["target_product"] == "education"
    assert body["blueprint"]["payload"]["content_type"] == "step_by_step_guide"

    telemetry_path = tmp_path / "telemetry.jsonl"
    telemetry_lines = telemetry_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(telemetry_lines) == 3


def test_finance_blueprint_blocks_trading_execution(tmp_path: Path):
    service = build_service(tmp_path)

    with pytest.raises(ValueError):
        service.generate_blueprint(
            {
                "prompt": "Buy the stock immediately and execute trade.",
                "module": "finance",
                "intent": "trade_execution",
                "topic": "equities",
                "tasks": ["execute_trade"],
                "output_format": "table",
                "product_context": "creator_core",
            }
        )


def test_validation_rejects_extra_fields(tmp_path: Path):
    service = build_service(tmp_path)
    app = FastAPI()
    app.include_router(create_creator_core_router(service))
    client = TestClient(app)

    payload = sample_instruction()
    payload["unexpected_field"] = "not_allowed"

    response = client.post("/creator-core/generate-blueprint", json=payload)
    assert response.status_code == 422


def test_unknown_module_falls_back_to_content_blueprint(tmp_path: Path):
    service = build_service(tmp_path)
    response = service.generate_blueprint(
        {
            "prompt": "Create a short summary",
            "module": "unknown_domain",
            "intent": "summarize",
            "topic": "demo_topic",
            "tasks": ["step_one", "step_two"],
            "output_format": "bullets",
            "product_context": "creator_core",
        }
    )

    assert response.payload.blueprint_type == "content_blueprint"
    assert response.target_product == "creator"