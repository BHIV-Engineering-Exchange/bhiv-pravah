from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.prana_contract_registry import (
    PRANA_CONTRACT_REGISTRY_NAME,
    IngressContractViolationError,
    validate_prana_ingress_request,
)
from app.services.prana_load_tester import prana_load_tester
from app.services.prana_observability import prana_observability
from app.services.prana_replay_orchestrator import prana_replay_orchestrator
from app.services.prana_runtime import AppendOnlyViolationError, prana_runtime


class ReplayDatasetSystemSpec(BaseModel):
    event_ids: list[str] = Field(default_factory=list)
    submission_ids: list[str] = Field(default_factory=list)


class PranaReplayRequest(BaseModel):
    run_id: Optional[str] = None
    dataset: Optional[Dict[str, ReplayDatasetSystemSpec]] = None

    @model_validator(mode="after")
    def validate_inputs(self):
        if not self.run_id and not self.dataset:
            raise ValueError("Either run_id or dataset must be provided")
        return self


class PranaLoadTestRequest(BaseModel):
    events_count: int = Field(500, ge=100, le=500)
    concurrency: int = Field(50, ge=1, le=500)
    replay_workers: int = Field(4, ge=1, le=16)
    run_id: Optional[str] = None
    source_system: str = "gurukul"


router = APIRouter()


PRANA_INGEST_EXAMPLE = {
    "registry_reference": {
        "registry": PRANA_CONTRACT_REGISTRY_NAME,
        "event_type": "integrity_probe",
        "version": "1.0.0",
    },
    "submission_id": "probe-20260406-demo",
    "event_type": "integrity_probe",
    "timestamp": "2026-04-06T11:00:00Z",
    "payload": {
        "sequence": 1,
        "status": "ok",
        "probe": "baseline",
        "run_id": "20260406-PRANA-DEMO",
        "index": 1,
    },
    "source_system": "gurukul",
}


@router.post(
    "/prana/ingest",
    responses={
        409: {
            "description": "Version mismatch",
            "content": {
                "application/json": {
                    "example": {
                        "status": "rejected",
                        "reason": "version_mismatch",
                        "message": "registry_reference.version does not match the registered contract version",
                        "event_type": "integrity_probe",
                        "registry_reference": {
                            "registry": "prana.event.contracts",
                            "event_type": "integrity_probe",
                            "version": "2.0.0",
                        },
                        "expected_versions": ["1.0.0"],
                        "details": {"received_version": "2.0.0"},
                    }
                }
            },
        },
        422: {
            "description": "Schema enforcement rejection",
            "content": {
                "application/json": {
                    "example": {
                        "status": "rejected",
                        "reason": "payload_schema_invalid",
                        "message": "payload does not conform to the registered event contract",
                        "event_type": "integrity_probe",
                        "registry_reference": {
                            "registry": "prana.event.contracts",
                            "event_type": "integrity_probe",
                            "version": "1.0.0",
                        },
                        "expected_versions": ["1.0.0"],
                        "details": [
                            {
                                "field": "probe",
                                "message": "Field required",
                                "type": "missing",
                            }
                        ],
                    }
                }
            },
        },
    },
)
def ingest_prana_event(
    request_body: Dict[str, Any] = Body(
        ...,
        examples={
            "registered_contract": {
                "summary": "Valid PRANA ingress event",
                "value": PRANA_INGEST_EXAMPLE,
            }
        },
    ),
    db: Session = Depends(get_db),
):
    try:
        request = validate_prana_ingress_request(request_body)
        result = prana_runtime.ingest_event(
            db,
            submission_id=request.submission_id,
            event_type=request.event_type,
            timestamp=request.timestamp,
            payload=request.payload,
            source_system=request.source_system,
        )
        return {"status": "success", **result}
    except IngressContractViolationError:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to ingest PRANA event: {exc}") from exc


@router.get("/prana/events")
def get_prana_events(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    return prana_runtime.get_recent_events(db, limit=limit)


@router.get("/prana/vitality")
def get_prana_vitality(db: Session = Depends(get_db)):
    return prana_runtime.get_vitality_summary(db)


@router.get("/prana/system/health")
def get_prana_system_health(db: Session = Depends(get_db)):
    try:
        return prana_observability.get_system_health(db)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to compute PRANA system health: {exc}") from exc


@router.post("/prana/verify")
def verify_prana_event(event_id: Optional[str] = None, db: Session = Depends(get_db)):
    try:
        if event_id:
            return prana_runtime.verify_event(db, event_id)
        return prana_runtime.verify_all(db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to verify PRANA event(s): {exc}") from exc


@router.post("/prana/replay")
def orchestrate_prana_replay(request: PranaReplayRequest, db: Session = Depends(get_db)):
    try:
        dataset = None
        if request.dataset:
            dataset = {
                system_name: spec.model_dump()
                for system_name, spec in request.dataset.items()
            }
        return prana_replay_orchestrator.orchestrate_replay(
            db,
            run_id=request.run_id,
            dataset=dataset,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to orchestrate PRANA replay: {exc}") from exc


@router.post("/prana/load-test")
def run_prana_load_test(request: PranaLoadTestRequest):
    try:
        return prana_load_tester.run_load_test(
            events_count=request.events_count,
            concurrency=request.concurrency,
            replay_workers=request.replay_workers,
            run_id=request.run_id,
            source_system=request.source_system,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to run PRANA load test: {exc}") from exc


@router.put("/prana/events/{event_id}")
@router.patch("/prana/events/{event_id}")
def reject_prana_event_mutation(event_id: str):
    raise AppendOnlyViolationError(operation="UPDATE", event_id=event_id, changed_fields=[])


@router.delete("/prana/events/{event_id}")
def reject_prana_event_delete(event_id: str):
    raise AppendOnlyViolationError(operation="DELETE", event_id=event_id, changed_fields=[])
