from datetime import datetime, timezone
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, get_db
from app.models.prana_models import (
    PranaAnomalyEvent,
    PranaIntegrityLog,
    PranaPacket,
    PranaVitalityMetric,
    ReplayValidationLog,
)
from app.routers.prana import router as prana_router
from app.services.prana_replay_orchestrator import prana_replay_orchestrator
from app.services.prana_runtime import ensure_prana_integrity_append_only_guards, prana_runtime


@pytest.fixture()
def sqlite_session_factory():
    temp_dir = Path(__file__).resolve().parent / ".tmp"
    temp_dir.mkdir(exist_ok=True)
    db_path = temp_dir / "prana_replay_orchestrator.db"
    db_path.unlink(missing_ok=True)
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            PranaPacket.__table__,
            PranaAnomalyEvent.__table__,
            PranaIntegrityLog.__table__,
            PranaVitalityMetric.__table__,
            ReplayValidationLog.__table__,
        ],
    )
    ensure_prana_integrity_append_only_guards(engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    try:
        yield factory
    finally:
        engine.dispose()
        db_path.unlink(missing_ok=True)


def _seed_replay_run(session_factory, *, run_id: str, corrupt_gurukul: bool = False):
    session = session_factory()
    try:
        if corrupt_gurukul:
            event_id = str(uuid4())
            now = datetime.now(timezone.utc)
            session.add(
                PranaIntegrityLog(
                    event_id=event_id,
                    submission_id=f"gurukul-{run_id}",
                    event_type="integrity_probe",
                    event_timestamp=now,
                    freshness_timestamp=now,
                    payload={"sequence": 1, "run_id": run_id, "probe": "gurukul"},
                    payload_hash="0" * 64,
                    source_system="gurukul",
                    expected_sequence=1,
                    actual_sequence=1,
                    gap_detected=False,
                    out_of_order=False,
                    anomaly_count=0,
                    replay_status="PENDING",
                )
            )
            session.commit()
            gurukul_event = {"event_id": event_id}
        else:
            gurukul_event = prana_runtime.ingest_event(
                session,
                submission_id=f"gurukul-{run_id}",
                event_type="integrity_probe",
                timestamp=datetime.now(timezone.utc).isoformat(),
                payload={"sequence": 1, "run_id": run_id, "probe": "gurukul"},
                source_system="gurukul",
            )

        packet = PranaPacket(
            packet_id=f"bucket-{run_id}",
            user_id="bucket-user",
            employee_id=None,
            session_id="bucket-session",
            lesson_id="bucket-lesson",
            system_type="gurukul",
            role="student",
            client_timestamp=datetime.now(timezone.utc),
            cognitive_state="ON_TASK",
            state="WORKING",
            active_seconds=5.0,
            idle_seconds=0.0,
            away_seconds=0.0,
            focus_score=95.0,
            integrity_score=0.95,
            raw_signals={"run_id": run_id, "content": "bucket replay"},
            processed_by_karma=False,
        )
        session.add(packet)
        session.commit()

        prana_runtime.ingest_event(
            session,
            submission_id=packet.packet_id,
            event_type="bucket_memory_saved",
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload={"sequence": 1, "packet_id": packet.packet_id, "run_id": run_id},
            source_system="Bucket",
        )
        prana_runtime.ingest_event(
            session,
            submission_id=f"karma-{run_id}",
            event_type="truth_classification",
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload={"sequence": 1, "classification_result": "PAAP", "run_id": run_id},
            source_system="Karma",
        )

        return {
            "gurukul_event_id": gurukul_event["event_id"],
            "bucket_submission_id": packet.packet_id,
            "karma_submission_id": f"karma-{run_id}",
        }
    finally:
        session.close()


def test_orchestrator_matches_clean_run(sqlite_session_factory):
    _seed_replay_run(sqlite_session_factory, run_id="run-clean")
    session = sqlite_session_factory()
    try:
        result = prana_replay_orchestrator.orchestrate_replay(session, run_id="run-clean")
    finally:
        session.close()

    assert result["replay_status"] == "MATCH"
    assert result["drift_detected"] is False
    assert result["systems_compared"] == ["gurukul", "Bucket", "Karma"]


def test_orchestrator_detects_drift_from_dataset(sqlite_session_factory):
    seeded = _seed_replay_run(sqlite_session_factory, run_id="run-drift", corrupt_gurukul=True)
    session = sqlite_session_factory()
    try:
        result = prana_replay_orchestrator.orchestrate_replay(
            session,
            dataset={
                "gurukul": {"event_ids": [seeded["gurukul_event_id"]]},
                "bucket": {"submission_ids": [seeded["bucket_submission_id"]]},
                "karma": {"submission_ids": [seeded["karma_submission_id"]]},
            },
        )
    finally:
        session.close()

    assert result["replay_status"] == "MISMATCH"
    assert result["drift_detected"] is True
    assert result["system_results"]["gurukul"]["replay_status"] == "MISMATCH"


def test_replay_endpoint_returns_orchestrated_result(sqlite_session_factory):
    _seed_replay_run(sqlite_session_factory, run_id="run-api")

    app = FastAPI()

    def override_get_db():
        session = sqlite_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(prana_router, prefix="/api/v1")
    client = TestClient(app)

    response = client.post("/api/v1/prana/replay", json={"run_id": "run-api"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["replay_status"] == "MATCH"
    assert payload["systems_compared"] == ["gurukul", "Bucket", "Karma"]
