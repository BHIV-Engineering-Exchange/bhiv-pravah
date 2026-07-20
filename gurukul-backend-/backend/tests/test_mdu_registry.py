"""
test_mdu_registry.py — Expanded Unit Tests for MDU Registry Router API

Verifies live health polling, failure simulations, database persistence,
cryptographic provenance chain verification, tamper detection, state reconciliation,
and schema mismatch (TANTRA) validations using a temporary SQLite database.

Run with: pytest backend/tests/test_mdu_registry.py -v
"""

import pytest
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to ensure proper module imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import Base, get_db
from app.models.all_models import (
    Profile, User, Tenant, MduDataset, MduProvenanceEvent, MduReconciliationHistory
)
from app.routers.mdu_registry import router as mdu_router

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh temporary SQLite database for each test to ensure isolation."""
    temp_dir = Path(__file__).resolve().parent / ".tmp"
    temp_dir.mkdir(exist_ok=True)
    db_path = temp_dir / "test_mdu_temp.db"
    db_path.unlink(missing_ok=True)

    engine = create_engine(
        f"sqlite:///{db_path}", 
        connect_args={"check_same_thread": False}
    )
    
    # Create all registered tables in the DB
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        db_path.unlink(missing_ok=True)

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency returning the temporary SQLite session."""
    app = FastAPI()
    app.dependency_overrides[get_db] = lambda: db_session
    app.include_router(mdu_router, prefix="/api/v1")
    yield TestClient(app)

class TestMduRegistryRouter:
    """Test Suite for Hardened MDU Registry Router API"""

    def test_get_mdu_health(self, client):
        """Test health diagnostics and components response with implementation bounds"""
        response = client.get("/api/v1/mdu/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Healthy"
        assert "sqlite_relational_database" in data["components"]
        assert "chromadb_vector_store" in data["components"]
        assert data["diagnostics"]["sqlite_write_locks_active"] == 0
        
        # Verify implementation bounds are present
        assert "implementation_bounds" in data
        assert data["implementation_bounds"]["sqlite_relational_database"]["status"] == "IMPLEMENTED"
        assert data["implementation_bounds"]["chromadb_vector_store"]["status"] == "SIMULATED"

    def test_simulate_failure_states(self, client):
        """Test failure simulation toggling and graceful 500 error propagation"""
        # Enable failure simulation
        response = client.post("/api/v1/mdu/simulate-failure?enable=true")
        assert response.status_code == 200
        assert response.json()["simulated_failure_active"] is True

        # Health endpoint should now return 500 error
        response = client.get("/api/v1/mdu/health")
        assert response.status_code == 500
        assert "SIMULATED FAILURE" in response.json()["detail"]

        # Restore health endpoint
        response = client.post("/api/v1/mdu/simulate-failure?enable=false")
        assert response.status_code == 200
        assert response.json()["simulated_failure_active"] is False

        # Health should be 200 OK again
        response = client.get("/api/v1/mdu/health")
        assert response.status_code == 200

    def test_get_datasets_list(self, client):
        """Test database retrieval of curriculum catalog listings and autoseeding"""
        response = client.get("/api/v1/mdu/datasets")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        # Verify specific datasets exist in the catalog
        codes = [d["textbook_code"] for d in data]
        assert "NCERT-S10-EN" in codes
        assert "MSB-S10-MR" in codes

    def test_get_datasets_search_filter(self, client):
        """Test textbook database filtering with search querying"""
        response = client.get("/api/v1/mdu/datasets", params={"search": "Science"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        for d in data:
            assert "science" in d["canonical_name"].lower()

    def test_get_dataset_lineage(self, client, db_session):
        """Test Horizontal Lineage Map query with dynamic user profile counts"""
        # Seed user profiles requesting NCERT board
        tenant = Tenant(name="Test Tenant", type="INSTITUTION")
        db_session.add(tenant)
        db_session.commit()

        user1 = User(email="test1@gurukul.com", role="STUDENT", tenant_id=tenant.id)
        user2 = User(email="test2@gurukul.com", role="STUDENT", tenant_id=tenant.id)
        db_session.add_all([user1, user2])
        db_session.commit()

        p1 = Profile(user_id=user1.id, data={"board": "NCERT"})
        p2 = Profile(user_id=user2.id, data={"board": "NCERT"})
        db_session.add_all([p1, p2])
        db_session.commit()

        response = client.get("/api/v1/mdu/lineage/NCERT-S10-EN")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "links" in data
        assert data["nodes"][0]["id"] == "src"
        assert "NCERT" in data["nodes"][0]["label"]
        
        # Verify the dynamic routing label shows active profile count
        runtime_node = next(n for n in data["nodes"] if n["id"] == "routing")
        assert "2 Active Profiles" in runtime_node["label"]
        assert runtime_node["status"] == "COMPLIANT"

    def test_get_dataset_lineage_not_found(self, client):
        """Test non-existent lineage error handling"""
        response = client.get("/api/v1/mdu/lineage/NONEXISTENT-DATASET")
        assert response.status_code == 404
        assert "could not be located" in response.json()["detail"]

    def test_lifecycle_administrative_actions_and_persistence(self, client):
        """Test lifecycle actions transition state in DB and log chained events"""
        payload = {
            "dataset_id": "MSB-S9-EN",
            "action": "ACTIVATE",
            "operator": "Soham Kotkar (Lead)"
        }
        response = client.post("/api/v1/mdu/lifecycle/action", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["updated_state"] == "ACTIVE"

        # Verify dataset state persists in database
        response = client.get("/api/v1/mdu/datasets")
        for d in response.json():
            if d["id"] == "MSB-S9-EN":
                assert d["status"] == "ACTIVE"

    def test_lifecycle_action_validation_fails(self, client):
        """Test invalid lifecycle action error handling"""
        payload = {
            "dataset_id": "MSB-S9-EN",
            "action": "INVALID_ACTION",
            "operator": "Soham"
        }
        response = client.post("/api/v1/mdu/lifecycle/action", json=payload)
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"]

    def test_get_provenance_logs_with_chain_verification(self, client):
        """Test retrieval of provenance logs and on-the-fly hash validation"""
        response = client.get("/api/v1/mdu/provenance")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Assert cryptographic chain verification passes
        for item in data:
            print(f"DEBUG CHAIN: dataset={item['dataset']} hash={item['hash']} verified={item['chain_verified']}")
            assert item["chain_verified"] is True
            assert "hash" in item
            assert "operator" in item

    def test_provenance_cryptographic_tamper_detection(self, client, db_session):
        """Test that modifying a provenance record breaks subsequent validation hashes"""
        # Populate datasets to trigger auto-seeding
        client.get("/api/v1/mdu/datasets")

        # Fetch provenance events from DB
        events = db_session.query(MduProvenanceEvent).all()
        assert len(events) >= 3

        # Tamper with the middle event by changing its action
        tampered_event = events[1]
        tampered_event.action = "Tampered action string"
        db_session.commit()

        # Fetch provenance trail and check validation
        response = client.get("/api/v1/mdu/provenance")
        assert response.status_code == 200
        data = response.json()

        # The oldest event (first seeded, last in descending returned list) should still be verified
        # The middle tampered event and the newest event (which depends on the tampered hash) must fail verification
        verified_by_dataset = {item["dataset"]: item["chain_verified"] for item in data}
        
        # NCERT was seeded first, so it is the root of the chain. 
        assert verified_by_dataset["NCERT-S10-EN"] is True
        
        # MSB-S10-MR is the tampered one, its verification must fail.
        assert verified_by_dataset["MSB-S10-MR"] is False
        
        # MSB-S10-MR-EBAL was seeded third, and its hash incorporates the hash of MSB-S10-MR.
        assert verified_by_dataset["MSB-S10-MR-EBAL"] is False

    def test_mdu_state_reconciliation_persistence(self, client, db_session):
        """Test state reconciliation queries profiles, syncs filters, and saves audit logs"""
        # Seed database users & profiles
        tenant = Tenant(name="Demo Tenant", type="INSTITUTION")
        db_session.add(tenant)
        db_session.commit()

        user_ncert = User(email="ncert@gurukul.com", role="STUDENT", tenant_id=tenant.id)
        user_balbharati = User(email="balbharati@gurukul.com", role="STUDENT", tenant_id=tenant.id)
        db_session.add_all([user_ncert, user_balbharati])
        db_session.commit()

        p_ncert = Profile(user_id=user_ncert.id, data={"board": "NCERT"})
        p_bal = Profile(user_id=user_balbharati.id, data={"board": "BALBHARATI"})
        db_session.add_all([p_ncert, p_bal])
        db_session.commit()

        response = client.post("/api/v1/mdu/reconcile")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RECONCILED"
        assert data["profile_audit_count"] == 2
        assert data["board_preferences"]["NCERT"] == 1
        assert data["board_preferences"]["BALBHARATI"] == 1
        assert len(data["reconciliation_trace"]) == 5

        # Assert reconciliation entry is saved in SQLite database
        reconciliations_saved = db_session.query(MduReconciliationHistory).all()
        assert len(reconciliations_saved) == 1
        assert reconciliations_saved[0].status == "RECONCILED"
        assert reconciliations_saved[0].profile_audit_count == 2
        assert reconciliations_saved[0].board_preferences["NCERT"] == 1

    def test_schema_mismatch_422(self, client):
        """Test schema payload validator blocking (422)"""
        # Payload lacks required keys 'user_id' and 'sequence'
        payload = {
            "registry": "prana.event.contracts",
            "event_type": "task_submit",
            "version": "1.0.0",
            "payload": {
                "title": "Bad payload missing user and sequence fields"
            }
        }
        response = client.post("/api/v1/mdu/schema-mismatch", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["reason"] == "payload_schema_invalid"
        assert "user_id" in [item["field"] for item in data["detail"]["details"]]

    def test_schema_version_409(self, client):
        """Test schema version verification check rejection (409)"""
        payload = {
            "registry": "prana.event.contracts",
            "event_type": "integrity_probe",
            "version": "2.0.0", # Version mismatch - only 1.0.0 is registered
            "payload": {
                "sequence": 1,
                "route": "test",
                "user_id": "user-1"
            }
        }
        response = client.post("/api/v1/mdu/schema-mismatch", json=payload)
        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["reason"] == "version_mismatch"
        assert "1.0.0" in data["detail"]["expected_versions"]
