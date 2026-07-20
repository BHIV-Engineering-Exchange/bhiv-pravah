import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base
from app.models.prana_models import PranaAnomalyEvent, PranaIntegrityLog, PranaVitalityMetric, ReplayValidationLog
from app.services import prana_load_tester as prana_load_tester_module
from app.services.prana_load_tester import prana_load_tester
from app.services.prana_runtime import ensure_prana_integrity_append_only_guards


@pytest.fixture()
def isolated_load_tester_db(monkeypatch):
    temp_dir = Path(__file__).resolve().parent / ".tmp"
    temp_dir.mkdir(exist_ok=True)
    db_path = temp_dir / "prana_load_tester.db"
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
    monkeypatch.setattr(prana_load_tester_module, "SessionLocal", session_factory)
    monkeypatch.setattr(prana_load_tester_module, "engine", engine)

    try:
        yield
    finally:
        engine.dispose()
        db_path.unlink(missing_ok=True)


def test_prana_load_tester_handles_concurrent_ingestion_and_replay(isolated_load_tester_db):
    result = prana_load_tester.run_load_test(
        events_count=100,
        concurrency=16,
        replay_workers=3,
        run_id="pytest-prana-load",
        source_system="gurukul",
    )

    print("\nLOAD TEST RESULT DEBUG:")
    import pprint
    pprint.pprint(result)

    assert result["load_test"] == "PASS"
    assert result["events_processed"] == 100
    assert result["drift_detected"] is False
    assert result["ordering_failures"] == 0
    assert result["race_conditions_detected"] is False
    assert result["replay_status"] == "MATCH"
