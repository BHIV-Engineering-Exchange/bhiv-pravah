from datetime import datetime, timezone
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to path for direct pytest execution from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, get_db
from app.models.prana_models import (
    PranaAnomalyEvent,
    PranaIntegrityLog,
    PranaVitalityMetric,
    ReplayValidationLog,
)
from app.routers.prana import router as prana_router
from app.services.prana_runtime import (
    AppendOnlyViolationError,
    append_only_violation_from_exception,
    ensure_prana_integrity_append_only_guards,
    prana_runtime,
)


@pytest.fixture()
def sqlite_session_factory():
    temp_dir = Path(__file__).resolve().parent / ".tmp"
    temp_dir.mkdir(exist_ok=True)
    db_path = temp_dir / "prana_append_only.db"
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
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    try:
        yield factory, engine
    finally:
        engine.dispose()
        db_path.unlink(missing_ok=True)


def _seed_event(session_factory):
    session = session_factory()
    try:
        result = prana_runtime.ingest_event(
            session,
            submission_id="append-only-test",
            event_type="integrity_probe",
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload={"sequence": 1, "probe": "append_only"},
            source_system="PRANA_TEST",
        )
        return result["event_id"]
    finally:
        session.close()


def test_prana_integrity_log_rejects_raw_update_and_delete(sqlite_session_factory):
    session_factory, engine = sqlite_session_factory
    event_id = _seed_event(session_factory)

    with engine.begin() as connection:
        with pytest.raises(Exception) as update_exc:
            connection.exec_driver_sql(
                "UPDATE prana_integrity_log SET replay_status = 'MATCH' WHERE event_id = ?",
                (event_id,),
            )
        update_violation = append_only_violation_from_exception(update_exc.value)
        assert update_violation is not None
        assert update_violation.operation == "UPDATE"

    with engine.begin() as connection:
        with pytest.raises(Exception) as delete_exc:
            connection.exec_driver_sql(
                "DELETE FROM prana_integrity_log WHERE event_id = ?",
                (event_id,),
            )
        delete_violation = append_only_violation_from_exception(delete_exc.value)
        assert delete_violation is not None
        assert delete_violation.operation == "DELETE"


def test_prana_api_rejects_mutation_attempts_with_structured_response(sqlite_session_factory):
    session_factory, _ = sqlite_session_factory
    event_id = _seed_event(session_factory)

    app = FastAPI()

    @app.exception_handler(AppendOnlyViolationError)
    async def append_only_handler(request, exc: AppendOnlyViolationError):
        return JSONResponse(status_code=409, content=exc.to_response())

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(prana_router, prefix="/api/v1")

    client = TestClient(app)
    update_response = client.put(f"/api/v1/prana/events/{event_id}", json={"replay_status": "MATCH"})
    delete_response = client.delete(f"/api/v1/prana/events/{event_id}")

    assert update_response.status_code == 409
    assert delete_response.status_code == 409
    assert update_response.json()["error"] == "APPEND_ONLY_VIOLATION"
    assert delete_response.json()["error"] == "APPEND_ONLY_VIOLATION"
    assert update_response.json()["operation"] == "UPDATE"
    assert delete_response.json()["operation"] == "DELETE"
