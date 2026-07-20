import pytest
import asyncio
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from state import CandidateApplicationState
from graphs import create_application_workflow
from langchain_core.messages import HumanMessage

@pytest.fixture
def workflow():
    """Create workflow instance"""
    return create_application_workflow()

@pytest.fixture
def sample_state():
    """Create sample application state"""
    return {
        "candidate_id": 1,
        "job_id": 1,
        "application_id": 1,
        "candidate_email": "test@candidate.com",
        "candidate_phone": "+919876543210",
        "candidate_name": "Test Candidate",
        "job_title": "Software Engineer",
        "job_description": "Develop backend APIs",
        "application_status": "pending",
        "messages": [HumanMessage(content="Test application")],
        "notifications_sent": [],
        "matching_score": 0.0,
        "ai_recommendation": "",
        "sentiment": "neutral",
        "next_action": "screening",
        "workflow_stage": "screening",
        "error": None,
        "timestamp": datetime.now().isoformat(),
        "voice_input_path": None,
        "voice_response_path": None
    }

@pytest.mark.asyncio
async def test_workflow_initialization(workflow):
    """Test that workflow initializes correctly"""
    assert workflow is not None
    assert hasattr(workflow, 'ainvoke')
    print("✅ Workflow initialized successfully")

@pytest.mark.asyncio
async def test_workflow_state_structure(sample_state):
    """Test that state structure is valid"""
    assert sample_state["application_id"] == 1
    assert sample_state["workflow_stage"] == "screening"
    print("✅ State structure valid")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])