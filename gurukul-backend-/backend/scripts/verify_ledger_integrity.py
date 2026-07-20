import sys
import os
import json
from sqlalchemy.orm import Session

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.services.deterministic_repo import deterministic_repo

def run_verification():
    """
    Runs comprehensive cryptographic verification of the PRANA ledger.
    """
    db = SessionLocal()
    try:
        print("==" * 30)
        print("PRANA LEDGER CRYPTOGRAPHIC VERIFICATION ENGINE")
        print("==" * 30)
        
        results = deterministic_repo.verify_entire_ledger(db)
        
        overall_pass = True
        
        for table, result in results.items():
            status = result.get("status", "UNKNOWN")
            print(f"\nTable: {table}")
            print(f"Status: {status}")
            
            if status == "PASS":
                print(f"Verified {result.get('records_verified')} records.")
                if "chains_verified" in result:
                    print(f"Verified {result.get('chains_verified')} independent chains.")
            else:
                overall_pass = False
                print(f"REASON: {result.get('reason')}")
                if "packet_id" in result:
                    print(f"Packet ID: {result.get('packet_id')}")
                if "submission_id" in result:
                    print(f"Submission ID: {result.get('submission_id')} (Version {result.get('version')})")
                print(f"Details: {json.dumps(result, indent=2)}")
        
        print("\n" + "==" * 30)
        if overall_pass:
            print("FINAL VERDICT: LEDGER INTEGRITY VERIFIED (PASS)")
        else:
            print("FINAL VERDICT: TAMPER DETECTED! (FAIL)")
        print("==" * 30)
        
    except Exception as e:
        print(f"Verification Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_verification()
