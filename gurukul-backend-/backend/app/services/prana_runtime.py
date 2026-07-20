from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import event, func, inspect as sa_inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models.prana_models import (
    PranaAnomalyEvent,
    PranaIntegrityLog,
    PranaVitalityMetric,
    ReplayValidationLog,
)
from app.services.prana_determinism import prana_determinism


APPEND_ONLY_RESOURCE = "prana_integrity_log"
APPEND_ONLY_MESSAGE_TEMPLATE = f"{APPEND_ONLY_RESOURCE} is append-only; {{operation}} is forbidden"
SQLITE_APPEND_ONLY_TRIGGER_NAMES = (
    "prana_integrity_log_block_update",
    "prana_integrity_log_block_delete",
)
POSTGRES_APPEND_ONLY_TRIGGER_NAME = "prana_integrity_log_block_mutation"
POSTGRES_APPEND_ONLY_FUNCTION_NAME = "prana_integrity_log_reject_mutation"


class AppendOnlyViolationError(Exception):
    def __init__(
        self,
        *,
        operation: str,
        event_id: Optional[str] = None,
        submission_id: Optional[str] = None,
        source_system: Optional[str] = None,
        changed_fields: Optional[list[str]] = None,
        message: Optional[str] = None,
    ) -> None:
        self.operation = operation.upper()
        self.resource = APPEND_ONLY_RESOURCE
        self.event_id = event_id
        self.submission_id = submission_id
        self.source_system = source_system
        self.changed_fields = changed_fields or []
        self.message = message or APPEND_ONLY_MESSAGE_TEMPLATE.format(operation=self.operation)
        super().__init__(self.message)

    def to_response(self) -> Dict[str, Any]:
        return {
            "status": "rejected",
            "error": "APPEND_ONLY_VIOLATION",
            "message": self.message,
            "resource": self.resource,
            "operation": self.operation,
            "event_id": self.event_id,
            "submission_id": self.submission_id,
            "source_system": self.source_system,
            "changed_fields": self.changed_fields,
        }


def _append_only_trigger_message(operation: str) -> str:
    return APPEND_ONLY_MESSAGE_TEMPLATE.format(operation=operation.upper())


def append_only_violation_from_exception(exc: Exception) -> Optional[AppendOnlyViolationError]:
    message_parts = []
    current = exc
    while current is not None:
        message_parts.append(str(current))
        current = current.__cause__ or current.__context__
    message = " ".join(part for part in message_parts if part)
    if APPEND_ONLY_RESOURCE not in message:
        return None

    operation = "UPDATE"
    if "DELETE" in message.upper():
        operation = "DELETE"
    return AppendOnlyViolationError(operation=operation, message=_append_only_trigger_message(operation))


def ensure_prana_integrity_append_only_guards(engine: Engine) -> None:
    with engine.begin() as connection:
        dialect = connection.dialect.name
        if dialect == "sqlite":
            connection.execute(
                text(f"""
                CREATE TRIGGER IF NOT EXISTS {SQLITE_APPEND_ONLY_TRIGGER_NAMES[0]}
                BEFORE UPDATE ON {APPEND_ONLY_RESOURCE}
                BEGIN
                    SELECT RAISE(ABORT, '{_append_only_trigger_message("UPDATE")}');
                END;
                """)
            )
            connection.execute(
                text(f"""
                CREATE TRIGGER IF NOT EXISTS {SQLITE_APPEND_ONLY_TRIGGER_NAMES[1]}
                BEFORE DELETE ON {APPEND_ONLY_RESOURCE}
                BEGIN
                    SELECT RAISE(ABORT, '{_append_only_trigger_message("DELETE")}');
                END;
                """)
            )
            return

        if dialect == "postgresql":
            connection.execute(
                text(f"""
                CREATE OR REPLACE FUNCTION {POSTGRES_APPEND_ONLY_FUNCTION_NAME}()
                RETURNS trigger AS $$
                BEGIN
                    RAISE EXCEPTION '{APPEND_ONLY_RESOURCE} is append-only; % is forbidden', TG_OP;
                END;
                $$ LANGUAGE plpgsql;
                """)
            )
            connection.execute(
                text(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_trigger
                        WHERE tgname = '{POSTGRES_APPEND_ONLY_TRIGGER_NAME}'
                    ) THEN
                        CREATE TRIGGER {POSTGRES_APPEND_ONLY_TRIGGER_NAME}
                        BEFORE UPDATE OR DELETE ON {APPEND_ONLY_RESOURCE}
                        FOR EACH ROW
                        EXECUTE FUNCTION {POSTGRES_APPEND_ONLY_FUNCTION_NAME}();
                    END IF;
                END $$;
                """)
            )


class PranaRuntimeService:
    """
    Monitoring-only PRANA runtime.

    It stores append-only integrity signals, emits anomaly markers, maintains a
    lightweight vitality view, and verifies deterministic payload hashing.
    """

    STALE_AFTER_SECONDS = 120
    BURST_WINDOW_SECONDS = 10
    BURST_THRESHOLD = 5
    REPEATED_FAILURE_THRESHOLD = 3

    def __init__(self) -> None:
        self._log_dir = Path(__file__).resolve().parents[2] / "runtime_logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._execution_log = self._log_dir / "prana_execution.jsonl"
        self._stream_locks: dict[str, Lock] = {}
        self._stream_locks_guard = Lock()

    @staticmethod
    def _canonical_json(data: Dict[str, Any]) -> str:
        return prana_determinism.canonical_json(data)

    def _hash_payload(self, payload: Dict[str, Any]) -> str:
        return prana_determinism.hash_payload(payload)

    @staticmethod
    def _parse_timestamp(raw_value: str) -> datetime:
        parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _stream_key(source_system: str, submission_id: str) -> str:
        return f"{source_system}:{submission_id}"

    def _get_stream_lock(self, source_system: str, submission_id: str) -> Lock:
        stream_key = self._stream_key(source_system, submission_id)
        with self._stream_locks_guard:
            lock = self._stream_locks.get(stream_key)
            if lock is None:
                lock = Lock()
                self._stream_locks[stream_key] = lock
            return lock

    def _append_runtime_log(self, record: Dict[str, Any]) -> None:
        with self._execution_log.open("a", encoding="utf-8") as handle:
            handle.write(self._canonical_json(record) + "\n")

    @staticmethod
    def _burst_window_start(reference_time: datetime, window_seconds: int) -> datetime:
        return reference_time - timedelta(seconds=window_seconds)

    def _record_replay_validation(self, db: Session, event: PranaIntegrityLog, computed_hash: str) -> ReplayValidationLog:
        validation_result = "MATCH" if computed_hash == event.payload_hash else "MISMATCH"
        validation = ReplayValidationLog(
            validation_id=str(uuid4()),
            event_id=event.event_id,
            replay_timestamp=datetime.now(timezone.utc),
            computed_hash=computed_hash,
            stored_hash=event.payload_hash,
            validation_result=validation_result,
            source_system=event.source_system,
        )
        db.add(validation)
        return validation

    def observe_append_only_violation(self, target: PranaIntegrityLog, *, operation_type: str, changed_fields: Optional[list[str]] = None) -> Dict[str, Any]:
        observed_at = datetime.now(timezone.utc)
        submission_id = target.submission_id or target.event_id or "prana_integrity_log"
        source_system = target.source_system or "PRANA"
        payload = {
            "operation_type": operation_type,
            "observed": True,
            "enforced": True,
            "severity": "HIGH",
            "observed_event_id": target.event_id,
            "changed_fields": changed_fields or [],
        }
        payload_hash = self._hash_payload(payload)
        runtime_record = {
            "logged_at": observed_at.isoformat(),
            "event_id": str(uuid4()),
            "submission_id": submission_id,
            "event_type": "APPEND_ONLY_VIOLATION",
            "source_system": source_system,
            "payload_hash": payload_hash,
            "expected_sequence": None,
            "actual_sequence": None,
            "gap_detected": False,
            "out_of_order": False,
            "anomaly_count": 1,
            "freshness_status": "fresh",
            "replay_status": "REJECTED",
            "payload": payload,
        }
        self._append_runtime_log(runtime_record)
        return runtime_record

    def _latest_validation_statuses(self, db: Session, event_ids: list[str]) -> Dict[str, str]:
        if not event_ids:
            return {}

        rows = (
            db.query(ReplayValidationLog)
            .filter(ReplayValidationLog.event_id.in_(event_ids))
            .order_by(ReplayValidationLog.event_id.asc(), ReplayValidationLog.replay_timestamp.desc())
            .all()
        )
        statuses: Dict[str, str] = {}
        for row in rows:
            statuses.setdefault(row.event_id, row.validation_result)
        return statuses

    def ingest_event(
        self,
        db: Session,
        *,
        submission_id: str,
        event_type: str,
        timestamp: str,
        payload: Dict[str, Any],
        source_system: str = "gurukul",
    ) -> Dict[str, Any]:
        event_timestamp = self._parse_timestamp(timestamp)
        freshness_timestamp = datetime.now(timezone.utc)
        stream_key = self._stream_key(source_system, submission_id)

        with self._get_stream_lock(source_system, submission_id):
            previous_event = (
                db.query(PranaIntegrityLog)
                .filter(
                    PranaIntegrityLog.source_system == source_system,
                    PranaIntegrityLog.submission_id == submission_id,
                )
                .order_by(PranaIntegrityLog.freshness_timestamp.desc(), PranaIntegrityLog.event_id.desc())
                .first()
            )

            expected_sequence = 1 if previous_event is None else previous_event.expected_sequence + 1
            actual_sequence = payload.get("sequence")
            if actual_sequence is not None:
                try:
                    actual_sequence = int(actual_sequence)
                except (TypeError, ValueError):
                    actual_sequence = None

            gap_detected = actual_sequence is not None and actual_sequence != expected_sequence
            previous_event_timestamp = self._as_utc(previous_event.event_timestamp) if previous_event is not None else None
            out_of_order = previous_event_timestamp is not None and event_timestamp < previous_event_timestamp

            payload_hash = self._hash_payload(payload)
            replay_status = "PENDING"

            event_id = str(uuid4())
            integrity_event = PranaIntegrityLog(
                event_id=event_id,
                submission_id=submission_id,
                event_type=event_type,
                event_timestamp=event_timestamp,
                freshness_timestamp=freshness_timestamp,
                payload=payload,
                payload_hash=payload_hash,
                source_system=source_system,
                expected_sequence=expected_sequence,
                actual_sequence=actual_sequence,
                gap_detected=gap_detected,
                out_of_order=out_of_order,
                replay_status=replay_status,
            )
            db.add(integrity_event)

            anomaly_count = 0
            if gap_detected:
                anomaly_count += 1
                db.add(
                    PranaAnomalyEvent(
                        event_id=event_id,
                        submission_id=submission_id,
                        source_system=source_system,
                        anomaly_type="sequence_gap",
                        details={
                            "expected_sequence": expected_sequence,
                            "actual_sequence": actual_sequence,
                        },
                    )
                )
            if out_of_order:
                anomaly_count += 1
                db.add(
                    PranaAnomalyEvent(
                        event_id=event_id,
                        submission_id=submission_id,
                        source_system=source_system,
                        anomaly_type="out_of_order_timestamp",
                        details={
                            "previous_timestamp": previous_event_timestamp.isoformat() if previous_event_timestamp else None,
                            "event_timestamp": event_timestamp.isoformat(),
                        },
                    )
                )

            burst_since = self._burst_window_start(freshness_timestamp, self.BURST_WINDOW_SECONDS)
            burst_count_before_insert = (
                db.query(PranaIntegrityLog)
                .filter(
                    PranaIntegrityLog.source_system == source_system,
                    PranaIntegrityLog.submission_id == submission_id,
                    PranaIntegrityLog.freshness_timestamp >= burst_since,
                )
                .count()
            )
            burst_count = burst_count_before_insert + 1
            if burst_count >= self.BURST_THRESHOLD and burst_count_before_insert < self.BURST_THRESHOLD:
                anomaly_count += 1
                db.add(
                    PranaAnomalyEvent(
                        event_id=event_id,
                        submission_id=submission_id,
                        source_system=source_system,
                        anomaly_type="burst_events",
                        details={
                            "window_seconds": self.BURST_WINDOW_SECONDS,
                            "events_in_window": burst_count,
                        },
                    )
                )

            failure_like = event_type.lower().endswith("failed") or payload.get("status") == "failed"
            if failure_like:
                recent_failures = (
                    db.query(PranaIntegrityLog)
                    .filter(
                        PranaIntegrityLog.source_system == source_system,
                        PranaIntegrityLog.submission_id == submission_id,
                        PranaIntegrityLog.event_type.in_(["task_submit_failed", "review_failed", event_type]),
                    )
                    .count()
                ) + 1
                if recent_failures >= self.REPEATED_FAILURE_THRESHOLD:
                    anomaly_count += 1
                    db.add(
                        PranaAnomalyEvent(
                            event_id=event_id,
                            submission_id=submission_id,
                            source_system=source_system,
                            anomaly_type="repeated_failures",
                            details={
                                "failure_events": recent_failures,
                                "threshold": self.REPEATED_FAILURE_THRESHOLD,
                            },
                        )
                    )

            integrity_event.anomaly_count = anomaly_count

            vitality = db.get(PranaVitalityMetric, stream_key)
            if vitality is None:
                vitality = PranaVitalityMetric(
                    stream_key=stream_key,
                    source_system=source_system,
                    submission_id=submission_id,
                )
                db.add(vitality)

            vitality.last_seen = freshness_timestamp
            vitality.gap_count = (vitality.gap_count or 0) + (1 if gap_detected else 0)
            vitality.anomaly_count = (vitality.anomaly_count or 0) + anomaly_count
            vitality.freshness_status = "stale" if (freshness_timestamp - event_timestamp).total_seconds() > self.STALE_AFTER_SECONDS else "fresh"

            db.commit()
            db.refresh(integrity_event)
            db.refresh(vitality)

            runtime_record = {
                "logged_at": freshness_timestamp.isoformat(),
                "event_id": event_id,
                "submission_id": submission_id,
                "event_type": event_type,
                "source_system": source_system,
                "payload_hash": payload_hash,
                "expected_sequence": expected_sequence,
                "actual_sequence": actual_sequence,
                "gap_detected": gap_detected,
                "out_of_order": out_of_order,
                "anomaly_count": anomaly_count,
                "freshness_status": vitality.freshness_status,
                "replay_status": replay_status,
            }
        self._append_runtime_log(runtime_record)
        return runtime_record

    def verify_event(self, db: Session, event_id: str) -> Dict[str, Any]:
        event = db.get(PranaIntegrityLog, event_id)
        if event is None:
            raise ValueError(f"PRANA event {event_id} not found")

        recomputed_hash = self._hash_payload(event.payload or {})
        validation = self._record_replay_validation(db, event, recomputed_hash)
        db.commit()
        db.refresh(validation)

        return {
            "event_id": event.event_id,
            "submission_id": event.submission_id,
            "stored_hash": event.payload_hash,
            "recomputed_hash": recomputed_hash,
            "status": validation.validation_result,
            "validation_id": validation.validation_id,
            "replay_timestamp": validation.replay_timestamp.isoformat() if validation.replay_timestamp else None,
        }

    def verify_all(self, db: Session) -> Dict[str, Any]:
        events = db.query(PranaIntegrityLog).order_by(PranaIntegrityLog.received_at.asc()).all()
        matches = 0
        mismatches = []
        validation_ids = []
        for event in events:
            recomputed_hash = self._hash_payload(event.payload or {})
            validation = self._record_replay_validation(db, event, recomputed_hash)
            validation_ids.append(validation.validation_id)
            if validation.validation_result == "MATCH":
                matches += 1
            else:
                mismatches.append(
                    {
                        "event_id": event.event_id,
                        "submission_id": event.submission_id,
                        "stored_hash": event.payload_hash,
                        "recomputed_hash": recomputed_hash,
                        "validation_id": validation.validation_id,
                    }
                )
        db.commit()
        return {
            "status": "MATCH" if not mismatches else "MISMATCH",
            "events_verified": len(events),
            "matches": matches,
            "mismatches": mismatches,
            "validation_ids": validation_ids,
        }

    def verify_chain(self, db: Session, source_system: str) -> Dict[str, Any]:
        events = (
            db.query(PranaIntegrityLog)
            .filter(PranaIntegrityLog.source_system == source_system)
            .order_by(PranaIntegrityLog.received_at.asc())
            .all()
        )
        matches = 0
        mismatches = []
        validation_ids = []
        for event in events:
            recomputed_hash = self._hash_payload(event.payload or {})
            validation = self._record_replay_validation(db, event, recomputed_hash)
            validation_ids.append(validation.validation_id)
            if validation.validation_result == "MATCH":
                matches += 1
            else:
                mismatches.append(
                    {
                        "event_id": event.event_id,
                        "submission_id": event.submission_id,
                        "stored_hash": event.payload_hash,
                        "recomputed_hash": recomputed_hash,
                        "validation_id": validation.validation_id,
                    }
                )
        db.commit()
        return {
            "source_system": source_system,
            "status": "VALID" if not mismatches else "INVALID",
            "events_verified": len(events),
            "matches": matches,
            "mismatches": mismatches,
            "validation_ids": validation_ids,
        }

    def get_vitality_summary(self, db: Session) -> Dict[str, Any]:
        metrics = db.query(PranaVitalityMetric).order_by(PranaVitalityMetric.updated_at.desc()).all()
        return {
            "streams": [
                {
                    "stream_key": metric.stream_key,
                    "source_system": metric.source_system,
                    "submission_id": metric.submission_id,
                    "last_seen": metric.last_seen.isoformat() if metric.last_seen else None,
                    "gap_count": metric.gap_count,
                    "anomaly_count": metric.anomaly_count,
                    "freshness_status": metric.freshness_status,
                }
                for metric in metrics
            ],
            "stream_count": len(metrics),
        }

    def get_recent_events(self, db: Session, limit: int = 20) -> Dict[str, Any]:
        events = (
            db.query(PranaIntegrityLog)
            .order_by(PranaIntegrityLog.freshness_timestamp.desc(), PranaIntegrityLog.event_id.desc())
            .limit(limit)
            .all()
        )
        anomalies = (
            db.query(PranaAnomalyEvent)
            .order_by(PranaAnomalyEvent.created_at.desc(), PranaAnomalyEvent.id.desc())
            .limit(limit)
            .all()
        )
        latest_validation_statuses = self._latest_validation_statuses(
            db,
            [event.event_id for event in events],
        )
        return {
            "events": [
                {
                    "event_id": event.event_id,
                    "submission_id": event.submission_id,
                    "event_type": event.event_type,
                    "timestamp": event.event_timestamp.isoformat(),
                    "source_system": event.source_system,
                    "expected_sequence": event.expected_sequence,
                    "actual_sequence": event.actual_sequence,
                    "gap_detected": event.gap_detected,
                    "out_of_order": event.out_of_order,
                    "payload_hash": event.payload_hash,
                    "replay_status": latest_validation_statuses.get(event.event_id, event.replay_status),
                }
                for event in events
            ],
            "anomalies": [
                {
                    "id": anomaly.id,
                    "event_id": anomaly.event_id,
                    "submission_id": anomaly.submission_id,
                    "source_system": anomaly.source_system,
                    "anomaly_type": anomaly.anomaly_type,
                    "details": anomaly.details,
                    "created_at": anomaly.created_at.isoformat() if anomaly.created_at else None,
                }
                for anomaly in anomalies
            ],
        }


prana_runtime = PranaRuntimeService()


@event.listens_for(PranaIntegrityLog, "before_update")
def _observe_prana_integrity_update(mapper, connection, target):
    state = sa_inspect(target)
    changed_fields = [attr.key for attr in state.attrs if attr.history.has_changes()]
    prana_runtime.observe_append_only_violation(
        target,
        operation_type="UPDATE",
        changed_fields=changed_fields,
    )
    raise AppendOnlyViolationError(
        operation="UPDATE",
        event_id=target.event_id,
        submission_id=target.submission_id,
        source_system=target.source_system,
        changed_fields=changed_fields,
    )


@event.listens_for(PranaIntegrityLog, "before_delete")
def _observe_prana_integrity_delete(mapper, connection, target):
    prana_runtime.observe_append_only_violation(
        target,
        operation_type="DELETE",
        changed_fields=[],
    )
    raise AppendOnlyViolationError(
        operation="DELETE",
        event_id=target.event_id,
        submission_id=target.submission_id,
        source_system=target.source_system,
        changed_fields=[],
    )
