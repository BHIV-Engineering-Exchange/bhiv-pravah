"""
test_compliance_routing.py — Unit Tests for State Board Curriculum Compliance Router

Verifies deterministic dynamic resolution, guest sandbox default paths, and
correct localized standard chapter indexing without requiring full model loads.

Run with: pytest backend/tests/test_compliance_routing.py -v
"""

import pytest
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add parent directory to path to ensure proper module imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.routers.compliance import router as compliance_router

@pytest.fixture(scope="module")
def client():
    # Use isolated FastAPI app for ultra-fast, dependency-free router unit testing
    app = FastAPI()
    app.include_router(compliance_router, prefix="/api/v1")
    yield TestClient(app)

class TestComplianceRouting:
    """Test Suite for Curriculum Resolution Layer API"""

    def test_curriculum_resolve_defaults(self, client):
        """Test guest path / uninitialized context resolver (Fail-Open Defaults)"""
        response = client.get("/api/v1/compliance/curriculum/resolve")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["resolution"]["resolved_board"] == "NCERT"
        assert data["resolution"]["medium"] == "en"
        assert data["resolution"]["class_standard"] == 10
        assert "NCERT-S10-EN" in data["resolution"]["textbook_code"]

    def test_curriculum_resolve_custom_board(self, client):
        """Test specific Balbharati Maharashtra State Board resolution"""
        response = client.get(
            "/api/v1/compliance/curriculum/resolve",
            params={"board": "BALBHARATI", "medium": "mr", "class_std": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["resolution"]["resolved_board"] == "BALBHARATI"
        assert data["resolution"]["medium"] == "mr"
        assert data["resolution"]["class_standard"] == 10
        assert data["resolution"]["textbook_code"] == "MSB-S10-MR"
        assert "Maharashtra State Board" in data["resolution"]["canonical_name"]

    def test_get_chapters_balbharati(self, client):
        """Test chapter retrieval for Balbharati standard 10 in Marathi Medium"""
        response = client.get(
            "/api/v1/compliance/curriculum/chapters",
            params={"board": "BALBHARATI", "medium": "mr", "class_std": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["board"] == "BALBHARATI"
        assert data["medium"] == "mr"
        assert data["class_standard"] == 10
        assert data["subject"] == "science_and_technology_1"
        assert len(data["chapters"]) > 0
        assert data["chapters"][0]["chapter_number"] == 1
        assert "Gravitation" in data["chapters"][0]["title"]

    def test_get_chapters_ncert(self, client):
        """Test chapter retrieval for NCERT standard 10 in English Medium"""
        response = client.get(
            "/api/v1/compliance/curriculum/chapters",
            params={"board": "NCERT", "medium": "en", "class_std": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["board"] == "NCERT"
        assert data["medium"] == "en"
        assert data["class_standard"] == 10
        assert len(data["chapters"]) > 0
        assert "Chemical Reactions" in data["chapters"][0]["title"]

    def test_get_chapters_graceful_fallback(self, client):
        """Test that unmapped boards fall back gracefully to NCERT English instead of crashing"""
        response = client.get(
            "/api/v1/compliance/curriculum/chapters",
            params={"board": "GUJARAT_BOARD", "medium": "gu", "class_std": 8}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["board"] == "GUJARAT_BOARD"
        assert data["medium"] == "gu"
        assert data["class_standard"] == 8
        # Verifies that chapters catalog fell back gracefully
        assert len(data["chapters"]) > 0
        assert "Chemical Reactions" in data["chapters"][0]["title"]
