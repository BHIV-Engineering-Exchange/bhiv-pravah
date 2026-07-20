import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import asc

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.prana_models import PranaPacket
from app.services.deterministic_repo import deterministic_repo

def migrate_ledger_hashes():
    """
    Backfills previous_hash and current_hash for existing PranaPacket entries.
    Iterates through all records in chronological order (received_at).
    """
    db = SessionLocal()
    try:
        # Get all packets without hashes, ordered by received_at
        packets = db.query(PranaPacket).order_by(asc(PranaPacket.received_at)).all()
        
        print(f"Found {len(packets)} packets to process.")
        
        prev_hash = deterministic_repo.GENESIS_HASH
        
        for i, packet in enumerate(packets):
            # Recalculate hash for this record
            data_to_hash = {
                "packet_id": packet.packet_id,
                "user_id": packet.user_id,
                "client_timestamp": packet.client_timestamp.isoformat(),
                "cognitive_state": packet.cognitive_state,
                "active_seconds": packet.active_seconds,
                "idle_seconds": packet.idle_seconds,
                "away_seconds": packet.away_seconds,
                "integrity_score": packet.integrity_score,
                "raw_signals": packet.raw_signals,
                "previous_hash": prev_hash
            }
            
            curr_hash = deterministic_repo._calculate_hash(data_to_hash)
            
            packet.previous_hash = prev_hash
            packet.current_hash = curr_hash
            
            # Update prev_hash for next record
            prev_hash = curr_hash
            
            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1} packets...")
                db.commit()
        
        db.commit()
        print("Migration complete. All hashes backfilled.")
        
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate_ledger_hashes()
