from datetime import datetime, timezone
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, get_db
from app.models.prana_models import PranaAnomalyEvent, PranaIntegrityLog, PranaVitalityMetric, ReplayValidationLog
from app.routers.prana import router as prana_router
from app.services.prana_contract_registry import (
    IngressContractViolationError,
    PRANA_CONTRACT_REGISTRY_NAME,
)
from app.services.prana_runtime import ensure_prana_integrity_append_only_guards


@pytest.fixture()
def contract_client():
    temp_dir = Path(__file__).resolve().parent / ".tmp"
    temp_dir.mkdir(exist_ok=True)
    db_path = temp_dir / "prana_contract_enforcement.db"
    db_path.unlink(missing_ok=True)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            PranaAnomalyEvent.__table__,
            PranaIntegrityLog.__table__,
            PranaVitalityMetric.__table__,
            ReplayValidationLog.__table__,
        ],
    )
    ensure_prana_integrity_append_only_guards(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    app = FastAPI()

    @app.exception_handler(IngressContractViolationError)
    async def ingress_contract_violation_handler(request: Request, exc: IngressContractViolationError):
        return JSONResponse(status_code=exc.status_code, content=exc.to_response())

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(prana_router, prefix="/api/v1")
    client = TestClient(app)

    try:
        yield client
    finally:
        engine.dispose()
        db_path.unlink(missing_ok=True)


def _valid_ingress_payload():
    return {
        "registry_reference": {
            "registry": PRANA_CONTRACT_REGISTRY_NAME,
            "event_type": "integrity_probe",
            "version": "1.0.0",
        },
        "submission_id": "contract-test-submission",
        "event_type": "integrity_probe",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "sequence": 1,
            "status": "ok",
            "probe": "baseline",
            "run_id": "contract-test-run",
            "index": 1,
        },
        "source_system": "gurukul",
    }


def test_prana_ingress_accepts_valid_registered_contract(contract_client):
    response = contract_client.post("/api/v1/prana/ingest", json=_valid_ingress_payload())
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_prana_ingress_rejects_malformed_payload(contract_client):
    payload = _valid_ingress_payload()
    del payload["payload"]["probe"]

    response = contract_client.post("/api/v1/prana/ingest", json=payload)
    body = response.json()

    assert response.status_code == 422
    assert body["status"] == "rejected"
    assert body["reason"] == "payload_schema_invalid"
    assert any(item["field"] == "probe" for item in body["details"])


def test_prana_ingress_rejects_version_mismatch(contract_client):
    payload = _valid_ingress_payload()
    payload["registry_reference"]["version"] = "2.0.0"

    response = contract_client.post("/api/v1/prana/ingest", json=payload)
    body = response.json()

    assert response.status_code == 409
    assert body["status"] == "rejected"
    assert body["reason"] == "version_mismatch"
    assert body["expected_versions"] == ["1.0.0"]
