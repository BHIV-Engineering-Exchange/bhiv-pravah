import sys
from pathlib import Path
from datetime import datetime, timezone
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, get_db
from app.models.prana_models import PranaPacket, ReviewOutputVersion, NextTaskVersion
from app.routers.bucket import router as bucket_router

@pytest.fixture()
def bucket_client():
    temp_dir = Path(__file__).resolve().parent / ".tmp"
    temp_dir.mkdir(exist_ok=True)
    db_path = temp_dir / "test_bucket.db"
    db_path.unlink(missing_ok=True)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    # Create all tables needed for bucket tests
    Base.metadata.create_all(bind=engine)
    
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    app = FastAPI()

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(bucket_router, prefix="/api/v1")
    
    client = TestClient(app)

    try:
        yield client
    finally:
        engine.dispose()
        db_path.unlink(missing_ok=True)

def _sample_packet():
    return {
        "user_id": "test-user-123",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cognitive_state": "WORKING",
        "active_seconds": 3.0,
        "idle_seconds": 1.0,
        "away_seconds": 1.0,
        "focus_score": 85.0,
        "raw_signals": {"run_id": "test-run", "content": "testing"}
    }

def test_ingest_and_latest_hash(bucket_client):
    # 1. Ingest a packet
    payload = _sample_packet()
    response = bucket_client.post("/api/v1/bucket/prana/ingest", json=payload)
    assert response.status_code == 200
    packet_id = response.json()["packet_id"]
    
    # 2. Check latest-hash
    response = bucket_client.get("/api/v1/bucket/latest-hash")
    assert response.status_code == 200
    data = response.json()
    assert "latest_hash" in data
    assert data["latest_hash"] != "0" * 64
    latest_hash = data["latest_hash"]
    
    # 3. Ingest another packet and verify hash changes
    payload2 = _sample_packet()
    payload2["timestamp"] = datetime.now(timezone.utc).isoformat()
    response = bucket_client.post("/api/v1/bucket/prana/ingest", json=payload2)
    assert response.status_code == 200
    
    response = bucket_client.get("/api/v1/bucket/latest-hash")
    assert response.status_code == 200
    new_hash = response.json()["latest_hash"]
    assert new_hash != latest_hash

def test_audit_artifact_endpoint(bucket_client):
    # 1. Ingest
    payload = _sample_packet()
    response = bucket_client.post("/api/v1/bucket/prana/ingest", json=payload)
    packet_id = response.json()["packet_id"]
    
    # 2. Audit
    response = bucket_client.get(f"/api/v1/audit/artifact/{packet_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["artifact_id"] == packet_id
    assert data["data"]["user_id"] == "test-user-123"
    assert "provenance" in data
    assert data["provenance"]["current_hash"] is not None

def test_contract_aliases(bucket_client):
    # Test POST /bucket/artifact
    payload = _sample_packet()
    response = bucket_client.post("/api/v1/bucket/artifact", json=payload)
    assert response.status_code == 200
    assert "packet_id" in response.json()
    
    # Test POST /bucket/artifact/write
    artifact_payload = {
        "artifact_id": "test-artifact-123",
        "content": payload,
        "metadata": {
            "trace_id": "trace-123",
            "product": "test-product"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    response = bucket_client.post("/api/v1/bucket/artifact/write", json=artifact_payload)
    assert response.status_code == 200
    assert "packet_id" in response.json()

def test_audit_artifact_not_found(bucket_client):
    response = bucket_client.get("/api/v1/audit/artifact/non-existent-id")
    assert response.status_code == 404
