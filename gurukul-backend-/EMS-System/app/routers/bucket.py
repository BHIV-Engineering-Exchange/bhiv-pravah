from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session  # type: ignore[reportMissingImports]

from app.database import get_db
from app.models import PranaPacket


class PranaPacketIn(BaseModel):
    # Unified PRANA schema (supports both Gurukul and EMS)
    user_id: Optional[str] = None  # For EMS, maps to employee_id
    employee_id: Optional[str] = None  # Legacy field, kept for backward compatibility
    session_id: Optional[str] = None
    lesson_id: Optional[str] = None
    system_type: Optional[Literal["gurukul", "ems"]] = None
    role: Optional[Literal["student", "employee"]] = None
    timestamp: str
    cognitive_state: Optional[str] = None  # Unified states: ON_TASK, THINKING, IDLE, DISTRACTED, AWAY, OFF_TASK, DEEP_FOCUS
    state: Optional[Literal["WORKING", "IDLE", "AWAY", "DISTRACTED", "FAKING"]] = None  # Legacy field
    active_seconds: float
    idle_seconds: float
    away_seconds: float
    focus_score: Optional[float] = Field(None, ge=0.0, le=100.0)  # Unified focus score (0-100)
    integrity_score: Optional[float] = Field(None, ge=0.0, le=1.0)  # Legacy field
    raw_signals: Dict[str, Any]

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        try:
            # Ensure it parses as ISO-8601
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception:
            raise ValueError("timestamp must be a valid ISO-8601 string")
        return v

    @field_validator("raw_signals")
    @classmethod
    def validate_raw_signals(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError("raw_signals must be an object")
        return v

    @field_validator("active_seconds", "idle_seconds", "away_seconds")
    @classmethod
    def non_negative_seconds(cls, v: float) -> float:
        if v < 0:
            raise ValueError("time values must be non-negative")
        return v

    @model_validator(mode='after')
    def validate_cross_fields(self):
        # At least one state field must be provided (handle None explicitly)
        if (self.cognitive_state is None or self.cognitive_state == "") and (self.state is None or self.state == ""):
            raise ValueError("Either 'cognitive_state' or 'state' must be provided")
        
        # At least one user ID field must be provided (handle None explicitly)
        # Allow "unknown" as a fallback for testing/development
        user_id_provided = self.user_id is not None and self.user_id != ""
        employee_id_provided = self.employee_id is not None and self.employee_id != ""
        if not user_id_provided and not employee_id_provided:
            # For development/testing, allow null user_id but log a warning
            # In production, you might want to reject these
            pass  # Allow null for now, will default to "unknown" in handler
        
        # Enforce exact 5-second window (unified PRANA requirement)
        total = self.active_seconds + self.idle_seconds + self.away_seconds
        # Allow small floating point tolerance (±0.1)
        if abs(total - 5.0) > 0.1:
            raise ValueError(f"Sum of active_seconds + idle_seconds + away_seconds must equal 5.0 (got {total})")
        
        return self


class PranaPacketResponse(BaseModel):
    status: str
    packet_id: str
    received_at: str


class PranaPacketError(BaseModel):
    status: str
    reason: str
    details: str


router = APIRouter()


@router.post(
    "/bucket/prana/ingest",
    response_model=PranaPacketResponse,
    responses={
        400: {"model": PranaPacketError},
        422: {"model": PranaPacketError},
    },
)
def ingest_prana_packet(payload: PranaPacketIn, db: Session = Depends(get_db)):
    """
    BHIV Bucket PRANA ingest endpoint.
    - Validates a single PRANA-E packet
    - Appends it as an immutable ledger entry
    """
    try:
        client_ts = datetime.fromisoformat(payload.timestamp.replace("Z", "+00:00"))
    except Exception as e:
        # This should normally be caught by the validator, but we keep this for absolute safety
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "rejected",
                "reason": "validation_error",
                "details": f"Invalid timestamp format: {str(e)}",
            },
        )

    packet_id = str(uuid4())
    received_at = datetime.now(timezone.utc)

    # Map unified schema to database fields
    # Use user_id if provided, otherwise fall back to employee_id (backward compatibility)
    employee_id = payload.user_id or payload.employee_id or "unknown"
    
    # Use cognitive_state if provided (unified), otherwise use legacy state
    state = payload.cognitive_state or payload.state or "ON_TASK"
    
    # Use focus_score if provided, convert to integrity_score (0-1 scale) for backward compatibility
    # If integrity_score is provided directly, use it; otherwise convert focus_score
    if payload.integrity_score is not None:
        integrity_score = payload.integrity_score
    elif payload.focus_score is not None:
        # Convert focus_score (0-100) to integrity_score (0-1)
        integrity_score = payload.focus_score / 100.0
    else:
        # Default to 0.5 if neither provided
        integrity_score = 0.5

    record = PranaPacket(
        packet_id=packet_id,
        employee_id=employee_id,
        state=state,
        integrity_score=integrity_score,
        active_seconds=payload.active_seconds,
        idle_seconds=payload.idle_seconds,
        away_seconds=payload.away_seconds,
        raw_signals=payload.raw_signals,
        client_timestamp=client_ts,
        received_at=received_at,
    )

    db.add(record)
    db.commit()

    return PranaPacketResponse(
        status="ingested",
        packet_id=packet_id,
        received_at=received_at.isoformat(),
    )


