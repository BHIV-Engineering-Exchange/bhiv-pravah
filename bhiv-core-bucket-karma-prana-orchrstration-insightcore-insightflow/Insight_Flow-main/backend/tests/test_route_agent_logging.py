# tests/test_route_agent_logging.py
"""
Test route-agent endpoint logging integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_feedback_service():
    """Mock feedback service"""
    service = Mock()
    service.get_agent_score = AsyncMock(return_value=0.85)
    return service


@pytest.fixture
def mock_agent_service():
    """Mock agent service"""
    service = Mock()
    service.get_active_agents = AsyncMock(return_value=[
        {
            "id": "nlp-001",
            "type": "nlp",
            "status": "active",
            "performance_score": 0.8,
            "success_rate": 0.9
        }
    ])
    service.get_agent_by_id = AsyncMock(return_value={
        "id": "nlp-001",
        "status": "active"
    })
    return service


@pytest.fixture
def mock_routing_logger():
    """Mock routing logger"""
    logger = Mock()
    logger.log_decision = Mock(return_value=True)
    return logger


class TestRouteAgentLogging:
    """Test route-agent endpoint with logging"""
    
    @patch('app.routers.routing.get_routing_logger')
    @patch('app.routers.routing.get_scoring_engine')
    @patch('app.services.agent_service.agent_service')
    @patch('app.routers.routing.get_feedback_service')
    def test_route_agent_logs_decision(
        self,
        mock_get_feedback,
        mock_agent_service_patch,
        mock_get_scoring,
        mock_get_logger,
        mock_feedback_service,
        mock_agent_service,
        mock_routing_logger
    ):
        """Test that route-agent endpoint logs decisions"""
        # Setup mocks
        mock_get_feedback.return_value = mock_feedback_service
        mock_agent_service_patch.return_value = mock_agent_service
        mock_get_logger.return_value = mock_routing_logger
        
        # Mock scoring engine
        mock_confidence = Mock()
        mock_confidence.final_score = 0.87
        mock_confidence.get_breakdown.return_value = {
            "rule_based": 0.8,
            "feedback": 0.85,
            "availability": 1.0
        }
        
        mock_scoring = Mock()
        mock_scoring.calculate_confidence.return_value = mock_confidence
        mock_get_scoring.return_value = mock_scoring
        
        # Make request
        request_data = {
            "agent_type": "nlp",
            "context": {"priority": "normal"},
            "confidence_threshold": 0.5,
            "request_id": "test-123"
        }
        
        response = client.post("/api/v1/routing/route-agent", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "nlp-001"
        assert data["confidence_score"] == 0.87
        assert "score_breakdown" in data
        assert "routing_reasoning" in data
        
        # Verify logging was called
        mock_routing_logger.log_decision.assert_called_once()
        call_args = mock_routing_logger.log_decision.call_args
        
        # Check logging parameters
        assert call_args[1]["agent_selected"] == "nlp-001"
        assert call_args[1]["confidence_score"] == 0.87
        assert call_args[1]["request_id"] == "test-123"
        assert "response_time_ms" in call_args[1]
        assert call_args[1]["response_time_ms"] > 0
    
    @patch('app.routers.routing.get_routing_logger')
    @patch('app.routers.routing.get_scoring_engine')
    @patch('app.services.agent_service.agent_service')
    @patch('app.routers.routing.get_feedback_service')
    def test_route_agent_timing_measurement(
        self,
        mock_get_feedback,
        mock_agent_service_patch,
        mock_get_scoring,
        mock_get_logger,
        mock_feedback_service,
        mock_agent_service,
        mock_routing_logger
    ):
        """Test that route-agent measures response time"""
        # Setup mocks (similar to above)
        mock_get_feedback.return_value = mock_feedback_service
        mock_agent_service_patch.return_value = mock_agent_service
        mock_get_logger.return_value = mock_routing_logger
        
        mock_confidence = Mock()
        mock_confidence.final_score = 0.87
        mock_confidence.get_breakdown.return_value = {}
        
        mock_scoring = Mock()
        mock_scoring.calculate_confidence.return_value = mock_confidence
        mock_get_scoring.return_value = mock_scoring
        
        # Make request
        request_data = {
            "agent_type": "nlp",
            "request_id": "timing-test"
        }
        
        response = client.post("/api/v1/routing/route-agent", json=request_data)
        
        # Verify timing was measured
        assert response.status_code == 200
        mock_routing_logger.log_decision.assert_called_once()
        
        call_args = mock_routing_logger.log_decision.call_args
        response_time = call_args[1]["response_time_ms"]
        
        # Response time should be positive and reasonable (< 1000ms for test)
        assert response_time > 0
        assert response_time < 1000