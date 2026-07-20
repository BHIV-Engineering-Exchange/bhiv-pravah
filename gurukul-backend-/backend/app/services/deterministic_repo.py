import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Type, TypeVar, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.prana_models import PranaPacket, ReviewOutputVersion, NextTaskVersion

logger = logging.getLogger(__name__)

T = TypeVar("T")

class DeterministicRepository:
    """
    Service for managing cryptographically chained ledger entries.
    Implements SHA-256 hash chaining across PRANA telemetry and versioned outputs.
    """

    GENESIS_HASH = "0" * 64

    @staticmethod
    def _canonicalize(data: Dict[str, Any]) -> str:
        """Serialize data to a canonical UTF-8 JSON string."""
        return json.dumps(data, sort_keys=True, separators=(',', ':'), default=str)

    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of canonicalized data."""
        canonical_json = self._canonicalize(data)
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

    def _prepare_packet_data(self, packet: Any, prev_hash: str) -> Dict[str, Any]:
        """Normalize packet data for consistent hashing."""
        # Handle both dict and model instance
        get_val = lambda obj, key: getattr(obj, key) if not isinstance(obj, dict) else obj.get(key)
        
        # Ensure floats are consistent (60 vs 60.0)
        to_float = lambda val: float(val) if val is not None else 0.0
        
        # Ensure timestamp is isoformatted string
        ts = get_val(packet, "client_timestamp")
        if isinstance(ts, datetime):
            ts_str = ts.isoformat()
        else:
            ts_str = str(ts) if ts else None

        return {
            "packet_id": get_val(packet, "packet_id"),
            "user_id": get_val(packet, "user_id"),
            "client_timestamp": ts_str,
            "cognitive_state": get_val(packet, "cognitive_state"),
            "active_seconds": to_float(get_val(packet, "active_seconds")),
            "idle_seconds": to_float(get_val(packet, "idle_seconds")),
            "away_seconds": to_float(get_val(packet, "away_seconds")),
            "integrity_score": to_float(get_val(packet, "integrity_score")),
            "raw_signals": get_val(packet, "raw_signals") or {},
            "previous_hash": prev_hash
        }

    def get_last_hash(self, db: Session, model: Type[T], filter_criteria: Optional[Dict[str, Any]] = None) -> str:
        """Retrieve the current_hash of the most recent record in a chain."""
        query = db.query(model)
        
        if filter_criteria:
            for key, value in filter_criteria.items():
                query = query.filter(getattr(model, key) == value)
        
        if model == PranaPacket:
            last_record = query.order_by(desc(model.received_at)).first()
        else:
            last_record = query.order_by(desc(model.version)).first()
            
        return last_record.current_hash if last_record else self.GENESIS_HASH

    def add_packet(self, db: Session, packet_data: Dict[str, Any]) -> PranaPacket:
        """Add a PranaPacket to the ledger with hash chaining."""
        prev_hash = self.get_last_hash(db, PranaPacket)
        
        # Standardize data for hashing
        data_to_hash = self._prepare_packet_data(packet_data, prev_hash)
        curr_hash = self._calculate_hash(data_to_hash)
        
        record = PranaPacket(**packet_data)
        record.previous_hash = prev_hash
        record.current_hash = curr_hash
        
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def add_review_version(self, db: Session, submission_id: str, review_json: Dict[str, Any]) -> ReviewOutputVersion:
        """Add a new version of a review output with hash chaining."""
        last_version = db.query(ReviewOutputVersion).filter(
            ReviewOutputVersion.submission_id == submission_id
        ).order_by(desc(ReviewOutputVersion.version)).first()
        
        new_version_num = (last_version.version + 1) if last_version else 1
        prev_hash = last_version.current_hash if last_version else self.GENESIS_HASH
        
        created_at = datetime.utcnow()
        
        data_to_hash = {
            "submission_id": submission_id,
            "version": new_version_num,
            "review_json": review_json,
            "created_at": created_at.isoformat(),
            "previous_hash": prev_hash
        }
        
        curr_hash = self._calculate_hash(data_to_hash)
        
        record = ReviewOutputVersion(
            submission_id=submission_id,
            version=new_version_num,
            review_json=review_json,
            created_at=created_at,
            previous_hash=prev_hash,
            current_hash=curr_hash
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def add_next_task_version(self, db: Session, submission_id: str, next_task_json: Dict[str, Any]) -> NextTaskVersion:
        """Add a new version of a next-task recommendation with hash chaining."""
        last_version = db.query(NextTaskVersion).filter(
            NextTaskVersion.submission_id == submission_id
        ).order_by(desc(NextTaskVersion.version)).first()
        
        new_version_num = (last_version.version + 1) if last_version else 1
        prev_hash = last_version.current_hash if last_version else self.GENESIS_HASH
        
        created_at = datetime.utcnow()
        
        data_to_hash = {
            "submission_id": submission_id,
            "version": new_version_num,
            "next_task_json": next_task_json,
            "created_at": created_at.isoformat(),
            "previous_hash": prev_hash
        }
        
        curr_hash = self._calculate_hash(data_to_hash)
        
        record = NextTaskVersion(
            submission_id=submission_id,
            version=new_version_num,
            next_task_json=next_task_json,
            created_at=created_at,
            previous_hash=prev_hash,
            current_hash=curr_hash
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def verify_packet_chain(self, db: Session) -> Dict[str, Any]:
        """Verify the integrity of the entire PranaPacket chain."""
        packets = db.query(PranaPacket).order_by(PranaPacket.received_at.asc()).all()
        
        expected_prev_hash = self.GENESIS_HASH
        for i, packet in enumerate(packets):
            if packet.previous_hash != expected_prev_hash:
                return {
                    "status": "FAIL",
                    "reason": "Linkage Break",
                    "packet_id": packet.packet_id,
                    "index": i,
                    "expected_prev": expected_prev_hash,
                    "actual_prev": packet.previous_hash
                }
            
            data_to_hash = self._prepare_packet_data(packet, packet.previous_hash)
            calculated_hash = self._calculate_hash(data_to_hash)
            
            if packet.current_hash != calculated_hash:
                logger.error(f"Integrity Mismatch at packet {packet.packet_id}")
                return {
                    "status": "FAIL",
                    "reason": "Content Mismatch",
                    "packet_id": packet.packet_id,
                    "index": i,
                    "expected_curr": calculated_hash,
                    "actual_curr": packet.current_hash,
                    "debug_data": data_to_hash
                }
            
            expected_prev_hash = packet.current_hash
            
        return {"status": "PASS", "records_verified": len(packets)}

    def verify_version_chain(self, db: Session, model: Type[T]) -> Dict[str, Any]:
        """Verify the integrity of versioned chains (ReviewOutput or NextTask)."""
        submission_ids = [r[0] for r in db.query(model.submission_id).distinct().all()]
        
        total_records = 0
        for sid in submission_ids:
            versions = db.query(model).filter(model.submission_id == sid).order_by(model.version.asc()).all()
            
            expected_prev_hash = self.GENESIS_HASH
            for i, record in enumerate(versions):
                if record.previous_hash != expected_prev_hash:
                    return {
                        "status": "FAIL",
                        "reason": f"Linkage Break in {model.__tablename__}",
                        "submission_id": sid,
                        "version": record.version,
                        "expected_prev": expected_prev_hash,
                        "actual_prev": record.previous_hash
                    }
                
                created_at_str = record.created_at.isoformat() if isinstance(record.created_at, datetime) else str(record.created_at)
                
                if model == ReviewOutputVersion:
                    data_to_hash = {
                        "submission_id": record.submission_id,
                        "version": record.version,
                        "review_json": record.review_json,
                        "created_at": created_at_str,
                        "previous_hash": record.previous_hash
                    }
                else:
                    data_to_hash = {
                        "submission_id": record.submission_id,
                        "version": record.version,
                        "next_task_json": record.next_task_json,
                        "created_at": created_at_str,
                        "previous_hash": record.previous_hash
                    }
                
                calculated_hash = self._calculate_hash(data_to_hash)
                if record.current_hash != calculated_hash:
                    return {
                        "status": "FAIL",
                        "reason": f"Content Mismatch in {model.__tablename__}",
                        "submission_id": sid,
                        "version": record.version,
                        "expected_curr": calculated_hash,
                        "actual_curr": record.current_hash
                    }
                
                expected_prev_hash = record.current_hash
                total_records += 1
                
        return {"status": "PASS", "records_verified": total_records, "chains_verified": len(submission_ids)}

    def verify_entire_ledger(self, db: Session) -> Dict[str, Any]:
        """Comprehensive verification of all cryptographically chained tables."""
        return {
            "prana_packets": self.verify_packet_chain(db),
            "review_output_versions": self.verify_version_chain(db, ReviewOutputVersion),
            "next_task_versions": self.verify_version_chain(db, NextTaskVersion)
        }

# Global instance
deterministic_repo = DeterministicRepository()
