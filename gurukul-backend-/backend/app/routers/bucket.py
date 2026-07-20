"""
Bucket Router - PRANA Packet Ingestion and Karma Tracker Consumer Endpoints

Handles:
1. Receiving PRANA packets from frontend
2. Storing packets in database
3. Queuing packets in Redis for Karma Tracker
4. Providing consumer endpoints for Karma Tracker to poll and process packets
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Dict, Any, Optional, List
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.redis_client import get_redis_queue
from app.services.prana_runtime import prana_runtime

# Import PranaPacket model
try:
    from app.models.prana_models import PranaPacket
    HAS_PRANA_MODEL = True
except ImportError:
    HAS_PRANA_MODEL = False
    print("[Bucket] PranaPacket model not found, using basic storage")


class PranaPacketIn(BaseModel):
    """Unified PRANA packet schema (supports both Gurukul and EMS)"""
    user_id: Optional[str] = None
    employee_id: Optional[str] = None  # Legacy field
    session_id: Optional[str] = None
    lesson_id: Optional[str] = None
    system_type: Optional[Literal["gurukul", "ems"]] = None
    role: Optional[Literal["student", "employee"]] = None
    timestamp: str
    cognitive_state: Optional[str] = None
    state: Optional[Literal["WORKING", "IDLE", "AWAY", "DISTRACTED", "FAKING"]] = None
    active_seconds: float
    idle_seconds: float
    away_seconds: float
    focus_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    integrity_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    raw_signals: Dict[str, Any]

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        try:
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
        if (self.cognitive_state is None or self.cognitive_state == "") and (self.state is None or self.state == ""):
            raise ValueError("Either 'cognitive_state' or 'state' must be provided")
        
        total = self.active_seconds + self.idle_seconds + self.away_seconds
        if abs(total - 5.0) > 0.1:
            raise ValueError(f"Sum of active_seconds + idle_seconds + away_seconds must equal 5.0 (got {total})")
        return self


class PranaPacketResponse(BaseModel):
    status: str
    packet_id: str
    received_at: str


class PendingPacketResponse(BaseModel):
    packet_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    lesson_id: Optional[str]
    system_type: Optional[str]
    cognitive_state: Optional[str]
    focus_score: Optional[float]
    active_seconds: float
    idle_seconds: float
    away_seconds: float
    raw_signals: Dict[str, Any]
    client_timestamp: str
    received_at: str


class PendingPacketsResponse(BaseModel):
    packets: List[PendingPacketResponse]
    count: int
    queue_size: int


class GeneralArtifactIn(BaseModel):
    """Flexible schema for maritime signals and general TANTRA artifacts"""
    artifact_id: str = Field(..., description="Unique identifier for the artifact")
    content: Dict[str, Any] = Field(..., description="The main payload (e.g. maritime signals)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Provenance and chain metadata")
    timestamp: Optional[str] = None


class MarkProcessedRequest(BaseModel):
    packet_id: str
    karma_actions: Optional[List[Dict[str, Any]]] = None
    success: bool = True
    error_message: Optional[str] = None


router = APIRouter()


@router.get(
    "/bucket/latest-hash",
    response_model=Dict[str, Any],
)
def get_latest_hash(
    model_type: str = Query("packet", description="Type of chain: 'packet', 'review', or 'task'"),
    db: Session = Depends(get_db)
):
    """
    Retrieve the current head hash of the cryptographically chained ledger.
    Used for pipeline chaining and integrity verification.
    """
    from app.models.prana_models import PranaPacket, ReviewOutputVersion, NextTaskVersion
    from app.services.deterministic_repo import deterministic_repo
    
    model_map = {
        "packet": PranaPacket,
        "review": ReviewOutputVersion,
        "task": NextTaskVersion
    }
    
    model = model_map.get(model_type.lower())
    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model_type. Must be one of: {list(model_map.keys())}"
        )
    
    last_hash = deterministic_repo.get_last_hash(db, model)
    return {
        "latest_hash": last_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "chain": model.__name__
    }


@router.get(
    "/audit/artifact/{artifact_id}",
    response_model=Dict[str, Any],
)
def get_artifact_audit(
    artifact_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve an artifact by its ID for read-after-write verification.
    Matches the BHIV audit protocol for artifact inspection.
    """
    if not HAS_PRANA_MODEL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PRANA model not available"
        )
    
    from app.models.prana_models import PranaPacket
    
    packet = db.query(PranaPacket).filter(PranaPacket.packet_id == artifact_id).first()
    if not packet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact {artifact_id} not found"
        )
    
    return {
        "artifact_id": packet.packet_id,
        "data": {
            "user_id": packet.user_id,
            "cognitive_state": packet.cognitive_state,
            "focus_score": packet.focus_score,
            "active_seconds": packet.active_seconds,
            "idle_seconds": packet.idle_seconds,
            "away_seconds": packet.away_seconds,
            "raw_signals": packet.raw_signals
        },
        "provenance": {
            "received_at": packet.received_at.isoformat() if packet.received_at else None,
            "client_timestamp": packet.client_timestamp.isoformat() if packet.client_timestamp else None,
            "previous_hash": packet.previous_hash,
            "current_hash": packet.current_hash
        },
        "status": "verified" if packet.current_hash else "unhashed"
    }


@router.post(
    "/bucket/artifact",
    response_model=PranaPacketResponse,
    tags=["Contract Alias"]
)
def ingest_artifact_alias_direct(payload: PranaPacketIn, db: Session = Depends(get_db)):
    """
    Direct alias for /bucket/prana/ingest to match BHIV Core request.
    """
    return ingest_prana_packet(payload, db)


@router.post(
    "/bucket/artifact/write",
    response_model=Dict[str, Any],
    tags=["General Artifacts"]
)
def ingest_general_artifact(payload: GeneralArtifactIn, db: Session = Depends(get_db)):
    """
    General Artifact Ingestion Endpoint.
    Supports maritime signals, system logs, and other non-educational data.
    Stores in PranaIntegrityLog with append-only guarantees.
    """
    from app.services.prana_runtime import prana_runtime
    from app.services.bucket_adapter import bucket_adapter
    
    received_at = datetime.now(timezone.utc)
    timestamp = payload.timestamp or received_at.isoformat()
    
    # Extract chain metadata if provided
    parent_hash = payload.metadata.get("parent_hash")
    trace_id = payload.metadata.get("trace_id", payload.artifact_id)
    product = payload.metadata.get("product", "general")

    try:
        # 1. Store in the append-only Integrity Log
        event_record = prana_runtime.ingest_event(
            db,
            submission_id=payload.artifact_id,
            event_type="artifact_write",
            timestamp=timestamp,
            payload={
                "content": payload.content,
                "metadata": payload.metadata,
                "trace_id": trace_id,
                "parent_hash": parent_hash
            },
            source_system=product,
        )
        
        # 2. Forward to external bucket if configured
        try:
            bucket_adapter.emit_artifact(
                artifact_id=payload.artifact_id,
                content=payload.content,
                metadata=payload.metadata
            )
        except Exception as be:
            print(f"[Bucket] Forwarding to external bucket failed: {be}")

        return {
            "status": "success",
            "artifact_id": payload.artifact_id,
            "packet_id": payload.artifact_id,  # backward-compatibility alias
            "internal_id": event_record["event_id"],
            "stored_at": received_at.isoformat(),
            "chain_hash": event_record["payload_hash"]
        }

    except Exception as e:
        print(f"[Bucket] Failed to ingest general artifact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Artifact ingestion failed: {str(e)}"
        )




@router.post(
    "/bucket/prana/ingest",
    response_model=PranaPacketResponse,
    responses={
        400: {"description": "Validation error"},
        422: {"description": "Invalid packet format"},
    },
)
def ingest_prana_packet(payload: PranaPacketIn, db: Session = Depends(get_db)):
    """
    PRANA Packet Ingestion Endpoint
    
    Receives packets from PRANA frontend and:
    1. Validates the packet
    2. Stores in database
    3. Queues in Redis for Karma Tracker processing
    """
    try:
        client_ts = datetime.fromisoformat(payload.timestamp.replace("Z", "+00:00"))
    except Exception as e:
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
    user_id = payload.user_id or payload.employee_id or "unknown"
    cognitive_state = payload.cognitive_state or payload.state or "ON_TASK"
    
    # Convert focus_score to integrity_score if needed
    if payload.integrity_score is not None:
        integrity_score = payload.integrity_score
    elif payload.focus_score is not None:
        integrity_score = payload.focus_score / 100.0
    else:
        integrity_score = 0.5

    # Store in database
    if HAS_PRANA_MODEL:
        try:
            # Use DeterministicRepository (Phase 1)
            packet_data = {
                "packet_id": packet_id,
                "user_id": user_id,
                "employee_id": payload.employee_id,
                "session_id": payload.session_id,
                "lesson_id": payload.lesson_id,
                "system_type": payload.system_type,
                "role": payload.role,
                "client_timestamp": client_ts,
                # received_at handled by DB default, but we can pass it for deterministic hashing if needed
                # However, DeterministicRepository uses received_at for ordering.
                "cognitive_state": cognitive_state,
                "state": payload.state,
                "active_seconds": payload.active_seconds,
                "idle_seconds": payload.idle_seconds,
                "away_seconds": payload.away_seconds,
                "focus_score": payload.focus_score,
                "integrity_score": integrity_score,
                "raw_signals": payload.raw_signals,
                "processed_by_karma": False,
            }
            
            from app.services.deterministic_repo import deterministic_repo
            record = deterministic_repo.add_packet(db, packet_data)
            
            # Queue in Redis for Karma Tracker
            redis_queue = get_redis_queue()
            redis_packet_data = packet_data.copy()
            redis_packet_data["client_timestamp"] = client_ts.isoformat()
            redis_packet_data["received_at"] = record.received_at.isoformat()
            redis_packet_data["previous_hash"] = record.previous_hash
            redis_packet_data["current_hash"] = record.current_hash
            
            redis_queue.enqueue_packet(packet_id, redis_packet_data)
            
        except Exception as e:
            print(f"[Bucket] Failed to save packet to cryptographically chained ledger: {e}")
            # Still acknowledge receipt even if storage fails
            
        except Exception as e:
            print(f"[Bucket] Failed to save packet to database: {e}")
            # Still acknowledge receipt even if storage fails
    else:
        print(f"[Bucket] Received PRANA packet (no storage): user_id={user_id}, state={cognitive_state}")

    try:
        prana_runtime.ingest_event(
            db,
            submission_id=packet_id,
            event_type="bucket_memory_saved",
            timestamp=received_at.isoformat(),
            payload={
                "sequence": 1,
                "operation": "CREATE",
                "route": "/api/v1/bucket/prana/ingest",
                "packet_id": packet_id,
                "user_id": user_id,
                "run_id": payload.raw_signals.get("run_id"),
                "category": payload.raw_signals.get("category", "learning"),
                "content": payload.raw_signals.get("content"),
                "cognitive_state": cognitive_state,
            },
            source_system="Bucket",
        )
    except Exception as e:
        print(f"[Bucket] Failed to emit PRANA runtime event for packet {packet_id}: {e}")

    return PranaPacketResponse(
        status="ingested",
        packet_id=packet_id,
        received_at=received_at.isoformat(),
    )


@router.get(
    "/bucket/prana/packets/pending",
    response_model=PendingPacketsResponse,
)
def get_pending_packets(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of packets to return"),
    db: Session = Depends(get_db)
):
    """
    Get pending packets for Karma Tracker to process.
    
    Returns unprocessed packets from the queue.
    """
    redis_queue = get_redis_queue()
    
    # Get packets from Redis queue
    queued_packets = redis_queue.dequeue_packets(limit=limit)
    
    # Convert to response format
    packets = []
    for item in queued_packets:
        packet_data = item.get("data", {})
        packets.append(PendingPacketResponse(
            packet_id=item["packet_id"],
            user_id=packet_data.get("user_id"),
            session_id=packet_data.get("session_id"),
            lesson_id=packet_data.get("lesson_id"),
            system_type=packet_data.get("system_type"),
            cognitive_state=packet_data.get("cognitive_state"),
            focus_score=packet_data.get("focus_score"),
            active_seconds=packet_data.get("active_seconds", 0.0),
            idle_seconds=packet_data.get("idle_seconds", 0.0),
            away_seconds=packet_data.get("away_seconds", 0.0),
            raw_signals=packet_data.get("raw_signals", {}),
            client_timestamp=packet_data.get("client_timestamp", ""),
            received_at=packet_data.get("received_at", ""),
        ))
    
    queue_size = redis_queue.get_queue_size()
    
    return PendingPacketsResponse(
        packets=packets,
        count=len(packets),
        queue_size=queue_size,
    )


@router.post(
    "/bucket/prana/packets/mark-processed",
    response_model=Dict[str, Any],
)
def mark_packet_processed(
    request: MarkProcessedRequest,
    db: Session = Depends(get_db)
):
    """
    Mark a packet as processed by Karma Tracker.
    
    Updates the database record and removes from Redis queue.
    """
    if not HAS_PRANA_MODEL:
        return {"status": "ok", "message": "Model not available, packet marked as processed"}
    
    try:
        # Update database record
        packet = db.query(PranaPacket).filter(PranaPacket.packet_id == request.packet_id).first()
        
        if not packet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Packet {request.packet_id} not found"
            )
        
        packet.processed_by_karma = True
        packet.processed_at = datetime.now(timezone.utc)
        
        if request.success:
            packet.karma_actions = request.karma_actions or []
        else:
            packet.processing_error = request.error_message
        
        db.commit()
        
        # Remove from Redis
        redis_queue = get_redis_queue()
        redis_queue.remove_packet(request.packet_id)
        
        return {
            "status": "ok",
            "message": "Packet marked as processed",
            "packet_id": request.packet_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark packet as processed: {str(e)}"
        )


@router.get(
    "/bucket/prana/packets/user/{user_id}",
    response_model=List[Dict[str, Any]],
)
def get_user_packets(
    user_id: str,
    limit: int = Query(50, ge=1, le=500),
    processed_only: bool = Query(False, description="Only return processed packets"),
    db: Session = Depends(get_db)
):
    """
    Get packets for a specific user.
    
    Useful for debugging and user activity tracking.
    """
    if not HAS_PRANA_MODEL:
        return []
    
    query = db.query(PranaPacket).filter(PranaPacket.user_id == user_id)
    
    if processed_only:
        query = query.filter(PranaPacket.processed_by_karma == True)
    else:
        query = query.filter(PranaPacket.processed_by_karma == False)
    
    packets = query.order_by(desc(PranaPacket.received_at)).limit(limit).all()
    
    return [
        {
            "packet_id": p.packet_id,
            "user_id": p.user_id,
            "session_id": p.session_id,
            "lesson_id": p.lesson_id,
            "cognitive_state": p.cognitive_state,
            "focus_score": p.focus_score,
            "active_seconds": p.active_seconds,
            "idle_seconds": p.idle_seconds,
            "away_seconds": p.away_seconds,
            "received_at": p.received_at.isoformat() if p.received_at else None,
            "processed_at": p.processed_at.isoformat() if p.processed_at else None,
            "processed_by_karma": p.processed_by_karma,
            "karma_actions": p.karma_actions,
        }
        for p in packets
    ]


@router.get(
    "/bucket/prana/status",
    response_model=Dict[str, Any],
)
def get_bucket_status(db: Session = Depends(get_db)):
    """
    Get bucket status and statistics.
    
    Returns queue size, total packets, processed count, etc.
    """
    redis_queue = get_redis_queue()
    queue_size = redis_queue.get_queue_size()
    
    stats = {
        "queue_size": queue_size,
        "redis_connected": redis_queue.is_connected,
        "model_available": HAS_PRANA_MODEL,
    }
    
    if HAS_PRANA_MODEL:
        try:
            total_packets = db.query(PranaPacket).count()
            processed_packets = db.query(PranaPacket).filter(PranaPacket.processed_by_karma == True).count()
            pending_packets = db.query(PranaPacket).filter(PranaPacket.processed_by_karma == False).count()
            
            stats.update({
                "total_packets": total_packets,
                "processed_packets": processed_packets,
                "pending_packets": pending_packets,
            })
        except Exception as e:
            stats["database_error"] = str(e)
    
    return stats
