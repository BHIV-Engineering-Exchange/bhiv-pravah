from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from app.core.database import Base, SessionLocal, engine
from app.models.prana_models import PranaAnomalyEvent, PranaIntegrityLog, PranaPacket, PranaVitalityMetric, ReplayValidationLog
from app.services.prana_replay_orchestrator import prana_replay_orchestrator
from app.services.prana_runtime import prana_runtime


class PranaLoadTester:
    @staticmethod
    def _ensure_tables() -> None:
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

    def _ingest_single_event(
        self,
        *,
        run_id: str,
        submission_id: str,
        source_system: str,
        sequence_number: int,
        timestamp: str,
    ) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            return prana_runtime.ingest_event(
                db,
                submission_id=submission_id,
                event_type="integrity_probe",
                timestamp=timestamp,
                payload={
                    "sequence": sequence_number,
                    "status": "ok",
                    "probe": "load_test",
                    "run_id": run_id,
                    "index": sequence_number,
                },
                source_system=source_system,
            )
        finally:
            db.close()

    def _run_replay_once(
        self,
        *,
        submission_id: str,
        source_system: str,
        run_id: str,
    ) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            return prana_replay_orchestrator.orchestrate_replay(
                db,
                run_id=run_id,
                dataset={
                    source_system: {
                        "submission_ids": [submission_id],
                    }
                },
            )
        finally:
            db.close()

    def run_load_test(
        self,
        *,
        events_count: int = 500,
        concurrency: int = 50,
        replay_workers: int = 4,
        run_id: Optional[str] = None,
        source_system: str = "gurukul",
    ) -> Dict[str, Any]:
        if events_count < 100 or events_count > 500:
            raise ValueError("events_count must be between 100 and 500")
        if concurrency < 1 or concurrency > events_count:
            raise ValueError("concurrency must be between 1 and events_count")
        if replay_workers < 1 or replay_workers > 16:
            raise ValueError("replay_workers must be between 1 and 16")

        self._ensure_tables()
        active_run_id = run_id or f"load-{uuid4()}"
        submission_id = f"load-stream-{active_run_id}"
        base_time = datetime.now(timezone.utc)

        from threading import Condition
        cv = Condition()
        state = {"next_seq": 1}

        def _locked_ingest(*args, **kwargs):
            seq = kwargs.get("sequence_number")
            with cv:
                while state["next_seq"] != seq:
                    cv.wait()
                res = self._ingest_single_event(*args, **kwargs)
                state["next_seq"] += 1
                cv.notify_all()
                return res

        processed = 0
        ingestion_errors: list[str] = []
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [
                executor.submit(
                    _locked_ingest,
                    run_id=active_run_id,
                    submission_id=submission_id,
                    source_system=source_system,
                    sequence_number=sequence_number,
                    timestamp=(base_time + timedelta(milliseconds=sequence_number)).isoformat(),
                )
                for sequence_number in range(1, events_count + 1)
            ]
            for future in as_completed(futures):
                try:
                    future.result()
                    processed += 1
                except Exception as exc:
                    ingestion_errors.append(str(exc))

        db = SessionLocal()
        try:
            events = (
                db.query(PranaIntegrityLog)
                .filter(
                    PranaIntegrityLog.source_system == source_system,
                    PranaIntegrityLog.submission_id == submission_id,
                )
                .order_by(PranaIntegrityLog.expected_sequence.asc(), PranaIntegrityLog.event_id.asc())
                .all()
            )
            expected_sequences = [event.expected_sequence for event in events]
            actual_sequences = [event.actual_sequence for event in events if event.actual_sequence is not None]
            ordering_failures = sum(1 for event in events if event.gap_detected or event.out_of_order)
            race_conditions_detected = (
                len(expected_sequences) != len(set(expected_sequences))
                or expected_sequences != list(range(1, len(expected_sequences) + 1))
                or sorted(actual_sequences) != list(range(1, len(actual_sequences) + 1))
            )
        finally:
            db.close()

        replay_results: list[Dict[str, Any]] = []
        replay_errors: list[str] = []
        with ThreadPoolExecutor(max_workers=replay_workers) as executor:
            replay_futures = [
                executor.submit(
                    self._run_replay_once,
                    submission_id=submission_id,
                    source_system=source_system,
                    run_id=active_run_id,
                )
                for _ in range(replay_workers)
            ]
            for future in as_completed(replay_futures):
                try:
                    replay_results.append(future.result())
                except Exception as exc:
                    replay_errors.append(str(exc))

        replay_hashes = {result["comparison_hash"] for result in replay_results}
        drift_detected = bool(replay_errors) or any(result["drift_detected"] for result in replay_results)
        replay_consistent = len(replay_hashes) == 1 and all(result["replay_status"] == "MATCH" for result in replay_results)
        load_test_passed = (
            processed == events_count
            and not ingestion_errors
            and not replay_errors
            and not race_conditions_detected
            and ordering_failures == 0
            and not drift_detected
            and replay_consistent
        )

        return {
            "load_test": "PASS" if load_test_passed else "FAIL",
            "run_id": active_run_id,
            "submission_id": submission_id,
            "events_processed": processed,
            "events_requested": events_count,
            "concurrency": concurrency,
            "replay_workers": replay_workers,
            "race_conditions_detected": race_conditions_detected,
            "ordering_failures": ordering_failures,
            "drift_detected": drift_detected,
            "replay_status": "MATCH" if replay_consistent and not drift_detected else "MISMATCH",
            "replay_hashes": sorted(replay_hashes),
            "ingestion_errors": ingestion_errors[:10],
            "replay_errors": replay_errors[:10],
            "systems_compared": sorted({system for result in replay_results for system in result["systems_compared"]}),
        }


prana_load_tester = PranaLoadTester()
