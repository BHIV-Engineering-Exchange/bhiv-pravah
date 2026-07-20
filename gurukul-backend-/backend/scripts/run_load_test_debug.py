import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from app.core.database import Base, engine, SessionLocal
from app.services.prana_load_tester import prana_load_tester
from app.services.prana_runtime import ensure_prana_integrity_append_only_guards
from app.models.prana_models import PranaAnomalyEvent, PranaIntegrityLog, PranaVitalityMetric, ReplayValidationLog

def run_debug():
    print("--- RUNNING PRANA LOAD TEST DEBUG ---")
    
    # Re-create tables and guards
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
    
    result = prana_load_tester.run_load_test(
        events_count=100,
        concurrency=16,
        replay_workers=3,
        run_id="debug-load-run",
        source_system="gurukul",
    )
    
    import pprint
    pprint.pprint(result)

if __name__ == "__main__":
    run_debug()
