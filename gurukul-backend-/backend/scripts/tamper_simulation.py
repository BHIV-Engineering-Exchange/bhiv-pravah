import sys
import os
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.prana_models import PranaPacket
from app.services.deterministic_repo import deterministic_repo

def run_simulation():
    db = SessionLocal()
    try:
        print("\n--- STEP 1: Inserting Valid Data ---")
        # Clear existing data for isolation
        db.query(PranaPacket).delete()
        db.commit()
        
        # Add 3 valid packets
        for i in range(3):
            packet_data = {
                "packet_id": f"sim_packet_{i}",
                "user_id": "test_student_1",
                "client_timestamp": datetime.utcnow() - timedelta(minutes=10-i),
                "cognitive_state": "focused" if i % 2 == 0 else "distracted",
                "active_seconds": 60,
                "idle_seconds": 0,
                "away_seconds": 0,
                "integrity_score": 100,
                "raw_signals": {"mouse_entropy": 0.5},
                "received_at": datetime.utcnow() - timedelta(minutes=10-i)
            }
            deterministic_repo.add_packet(db, packet_data)
            print(f"Added packet {i}")
            
        print("\n--- STEP 2: Verifying Initial State ---")
        result = deterministic_repo.verify_packet_chain(db)
        print(f"Initial Verification Status: {result['status']} (Verified {result.get('records_verified')} records)")
        
        if result['status'] != "PASS":
            print(f"ERROR: Initial verification failed! Result: {json.dumps(result, indent=2, default=str)}")
            return

        print("\n--- STEP 3: PERFORMING TAMPER (Content Modification) ---")
        # Find the second packet and change its cognitive_state without updating hash
        target = db.query(PranaPacket).filter(PranaPacket.packet_id == "sim_packet_1").first()
        print(f"Original State: {target.cognitive_state}")
        target.cognitive_state = "TAMPERED_STATE"
        db.commit()
        print(f"Modified cognitive_state to 'TAMPERED_STATE' in DB directly.")
        
        print("\n--- STEP 4: Verifying Tampered State ---")
        result = deterministic_repo.verify_packet_chain(db)
        print(f"Post-Tamper Verification Status: {result['status']}")
        if result['status'] == "FAIL":
            print(f"SUCCESS: Tamper detected! Reason: {result['reason']}")
            # Detail formatting
            print(f"Detected at Packet: {result.get('packet_id')}")
        else:
            print("FAILURE: Tamper was NOT detected!")
            
        print("\n--- STEP 5: PERFORMING TAMPER (Deletion/Gaps) ---")
        # Restore record 1 (fix its content for the next test)
        target.cognitive_state = "distracted" # original value
        db.commit()
        
        # Delete record 1 to create a gap between 0 and 2
        db.delete(target)
        db.commit()
        print(f"Deleted packet 1 to create a gap.")
        
        print("\n--- STEP 6: Verifying Deletion Tamper ---")
        result = deterministic_repo.verify_packet_chain(db)
        print(f"Post-Deletion Verification Status: {result['status']}")
        if result['status'] == "FAIL":
            print(f"SUCCESS: Deletion detected! Reason: {result['reason']}")
            print(f"Detected at Packet: {result.get('packet_id')}")
        else:
            print("FAILURE: Deletion was NOT detected!")

    except Exception as e:
        print(f"Simulation Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_simulation()
