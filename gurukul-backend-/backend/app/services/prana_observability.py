from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.prana_models import PranaAnomalyEvent, PranaIntegrityLog, ReplayValidationLog


class PranaObservabilityService:
    """
    Minimal PRANA observability service backed by persisted runtime tables.

    The endpoint intentionally reports a compact operational view:
    - recent ingestion rate
    - anomaly count
    - replay success rate
    - latest validation outcome
    """

    INGESTION_WINDOW_MINUTES = 5

    @staticmethod
    def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _build_last_validation_status(self, validation: Optional[ReplayValidationLog]) -> Dict[str, Any]:
        if validation is None:
            return {
                "status": "NO_VALIDATIONS_YET",
                "event_id": None,
                "validation_id": None,
                "source_system": None,
                "timestamp": None,
            }

        return {
            "status": validation.validation_result,
            "event_id": validation.event_id,
            "validation_id": validation.validation_id,
            "source_system": validation.source_system,
            "timestamp": self._as_utc(validation.replay_timestamp).isoformat()
            if validation.replay_timestamp
            else None,
        }

    def get_system_health(self, db: Session) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=self.INGESTION_WINDOW_MINUTES)

        ingested_in_window = (
            db.query(func.count(PranaIntegrityLog.event_id))
            .filter(PranaIntegrityLog.received_at >= window_start)
            .scalar()
            or 0
        )
        ingestion_rate_per_minute = round(
            ingested_in_window / self.INGESTION_WINDOW_MINUTES,
            2,
        )

        total_anomalies = db.query(func.count(PranaAnomalyEvent.id)).scalar() or 0

        total_validations = (
            db.query(func.count(ReplayValidationLog.validation_id)).scalar() or 0
        )
        successful_validations = (
            db.query(func.count(ReplayValidationLog.validation_id))
            .filter(ReplayValidationLog.validation_result == "MATCH")
            .scalar()
            or 0
        )
        replay_success_rate = round(
            (successful_validations / total_validations) * 100,
            2,
        ) if total_validations else 0.0

        latest_validation = (
            db.query(ReplayValidationLog)
            .order_by(
                ReplayValidationLog.replay_timestamp.desc(),
                ReplayValidationLog.validation_id.desc(),
            )
            .first()
        )

        return {
            "status": "healthy",
            "ingestion_rate": {
                "events_in_window": int(ingested_in_window),
                "window_minutes": self.INGESTION_WINDOW_MINUTES,
                "events_per_minute": ingestion_rate_per_minute,
            },
            "anomaly_count": int(total_anomalies),
            "replay_success_rate": {
                "percent": replay_success_rate,
                "successful_validations": successful_validations,
                "total_validations": total_validations,
            },
            "last_validation_status": self._build_last_validation_status(latest_validation),
            "generated_at": now.isoformat(),
        }


prana_observability = PranaObservabilityService()
