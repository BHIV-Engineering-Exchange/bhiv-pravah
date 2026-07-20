from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, get_db
from app.models.prana_models import PranaAnomalyEvent, PranaIntegrityLog, PranaVitalityMetric, ReplayValidationLog
from app.routers.prana import router as prana_router
from app.services.prana_runtime import ensure_prana_integrity_append_only_guards


@pytest.fixture()
def observability_client():
    temp_dir = Path(__file__).resolve().parent / ".tmp"
    temp_dir.mkdir(exist_ok=True)
    db_path = temp_dir / "prana_observability.db"
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

    session = session_factory()
    try:
        now = datetime.now(timezone.utc)
        session.add_all(
            [
                PranaIntegrityLog(
                    event_id="evt-1",
                    submission_id="sub-1",
                    event_type="integrity_probe",
                    event_timestamp=now,
                    freshness_timestamp=now,
                    payload={"sequence": 1, "probe": "baseline"},
                    payload_hash="a" * 64,
                    source_system="gurukul",
                    expected_sequence=1,
                    actual_sequence=1,
                    gap_detected=False,
                    out_of_order=False,
                    anomaly_count=0,
                    replay_status="PENDING",
                    received_at=now,
                ),
                PranaIntegrityLog(
                    event_id="evt-2",
                    submission_id="sub-1",
                    event_type="integrity_probe",
                    event_timestamp=now - timedelta(seconds=30),
                    freshness_timestamp=now - timedelta(seconds=30),
                    payload={"sequence": 2, "probe": "baseline"},
                    payload_hash="b" * 64,
                    source_system="gurukul",
                    expected_sequence=2,
                    actual_sequence=2,
                    gap_detected=False,
                    out_of_order=False,
                    anomaly_count=1,
                    replay_status="PENDING",
                    received_at=now - timedelta(seconds=30),
                ),
                PranaAnomalyEvent(
                    event_id="evt-2",
                    submission_id="sub-1",
                    source_system="gurukul",
                    anomaly_type="burst_events",
                    details={"events_in_window": 2},
                    created_at=now,
                ),
                ReplayValidationLog(
                    validation_id="val-1",
                    event_id="evt-1",
                    replay_timestamp=now - timedelta(minutes=1),
                    computed_hash="a" * 64,
                    stored_hash="a" * 64,
                    validation_result="MATCH",
                    source_system="gurukul",
                ),
                ReplayValidationLog(
                    validation_id="val-2",
                    event_id="evt-2",
                    replay_timestamp=now,
                    computed_hash="x" * 64,
                    stored_hash="b" * 64,
                    validation_result="MISMATCH",
                    source_system="gurukul",
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    app = FastAPI()

    def override_get_db():
        test_session = session_factory()
        try:
            yield test_session
        finally:
            test_session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(prana_router, prefix="/api/v1")
    client = TestClient(app)

    try:
        yield client
    finally:
        engine.dispose()
        db_path.unlink(missing_ok=True)


def test_prana_system_health_returns_observability_metrics(observability_client):
    response = observability_client.get("/api/v1/prana/system/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["ingestion_rate"]["events_in_window"] == 2
    assert payload["ingestion_rate"]["window_minutes"] == 5
    assert payload["anomaly_count"] == 1
    assert payload["replay_success_rate"]["successful_validations"] == 1
    assert payload["replay_success_rate"]["total_validations"] == 2
    assert payload["replay_success_rate"]["percent"] == 50.0
    assert payload["last_validation_status"]["status"] == "MISMATCH"
    assert payload["last_validation_status"]["event_id"] == "evt-2"
