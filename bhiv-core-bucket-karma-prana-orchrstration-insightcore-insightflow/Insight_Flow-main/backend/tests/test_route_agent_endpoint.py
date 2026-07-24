"""
Tests for /route-agent endpoint with weighted scoring
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app

client = TestClient(app)


class TestRouteAgentEndpoint:
    """Test cases for /route-agent endpoint"""
    
    @pytest.fixture
    def mock_feedback_service(self):
        """Mock feedback service"""
        service = AsyncMock()
        service.get_agent_score.return_value = 0.85
        return service
    
    @pytest.fixture
    def mock_agents(self):
        """Mock agent data"""
        return [
            {
                "id": "nlp-001",
                "name": "NLP Agent 1",
                "type": "nlp",
                "status": "active",
                "performance_score": 0.8,
                "success_rate": 0.9
            },
            {
                "id": "nlp-002", 
                "name": "NLP Agent 2",
                "type": "nlp",
                "status": "active",
                "performance_score": 0.7,
                "success_rate": 0.8
            }
        ]
    
    def test_route_agent_success(self, mock_feedback_service, mock_agents):
        """Test successful agent routing"""
        with patch('app.routers.routing.get_feedback_service') as mock_get_feedback:
            mock_get_feedback.return_value = mock_feedback_service
            
            with patch('app.routers.routing._get_candidate_agents') as mock_get_candidates:
                mock_get_candidates.return_value = mock_agents
                
                response = client.post(
                    "/api/v1/routing/route-agent",
                    json={
                        "agent_type": "nlp",
                        "confidence_threshold": 0.5,
                        "context": {"priority": "high"},
                        "request_id": "test-123"
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert "agent_id" in data
                assert "confidence_score" in data
                assert "score_breakdown" in data
                assert "alternative_agents" in data
                assert "routing_reasoning" in data
                
                # Check score breakdown structure
                breakdown = data["score_breakdown"]
                assert "rule_based_score" in breakdown
                assert "feedback_based_score" in breakdown
                assert "availability_score" in breakdown
                assert "rule_weight" in breakdown
                assert "feedback_weight" in breakdown
                assert "availability_weight" in breakdown
    
    def test_route_agent_missing_agent_type(self):
        """Test error when agent_type is missing"""
        response = client.post(
            "/api/v1/routing/route-agent",
            json={
                "confidence_threshold": 0.5,
                "context": {}
            }
        )
        
        assert response.status_code == 400
        assert "Missing 'agent_type' or 'task_type'" in response.json()["detail"]
    
    def test_route_agent_no_candidates(self, mock_feedback_service):
        """Test error when no candidate agents found"""
        with patch('app.routers.routing.get_feedback_service') as mock_get_feedback:
            mock_get_feedback.return_value = mock_feedback_service
            
            with patch('app.routers.routing._get_candidate_agents') as mock_get_candidates:
                mock_get_candidates.return_value = []
                
                response = client.post(
                    "/api/v1/routing/route-agent",
                    json={
                        "agent_type": "nonexistent",
                        "confidence_threshold": 0.5
                    }
                )
                
                assert response.status_code == 404
                assert "No agents available for type" in response.json()["detail"]
    
    def test_route_agent_low_confidence(self, mock_feedback_service, mock_agents):
        """Test error when no agent meets confidence threshold"""
        with patch('app.routers.routing.get_feedback_service') as mock_get_feedback:
            mock_get_feedback.return_value = mock_feedback_service
            mock_feedback_service.get_agent_score.return_value = 0.1  # Low feedback score
            
            with patch('app.routers.routing._get_candidate_agents') as mock_get_candidates:
                mock_get_candidates.return_value = mock_agents
                
                response = client.post(
                    "/api/v1/routing/route-agent",
                    json={
                        "agent_type": "nlp",
                        "confidence_threshold": 0.9  # High threshold
                    }
                )
                
                assert response.status_code == 503
                assert "No suitable agent found meeting confidence threshold" in response.json()["detail"]
    
    def test_route_agent_v2_format(self, mock_feedback_service, mock_agents):
        """Test with v2 format using task_type"""
        with patch('app.routers.routing.get_feedback_service') as mock_get_feedback:
            mock_get_feedback.return_value = mock_feedback_service
            
            with patch('app.routers.routing._get_candidate_agents') as mock_get_candidates:
                mock_get_candidates.return_value = mock_agents
                
                response = client.post(
                    "/api/v1/routing/route-agent",
                    json={
                        "task_type": "nlp",  # v2 format
                        "confidence_threshold": 0.5,
                        "correlation_id": "v2-test-123"  # v2 format
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["agent_id"] in ["nlp-001", "nlp-002"]
    
    def test_route_agent_alternative_agents(self, mock_feedback_service, mock_agents):
        """Test that alternative agents are returned"""
        with patch('app.routers.routing.get_feedback_service') as mock_get_feedback:
            mock_get_feedback.return_value = mock_feedback_service
            
            with patch('app.routers.routing._get_candidate_agents') as mock_get_candidates:
                mock_get_candidates.return_value = mock_agents
                
                response = client.post(
                    "/api/v1/routing/route-agent",
                    json={
                        "agent_type": "nlp",
                        "confidence_threshold": 0.5
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Should have alternative agents
                alternatives = data["alternative_agents"]
                assert isinstance(alternatives, list)
                assert len(alternatives) <= 2  # Top 2 alternatives
                
                for alt in alternatives:
                    assert "agent_id" in alt
                    assert "confidence_score" in alt
    
    def test_calculate_rule_based_score(self):
        """Test rule-based score calculation"""
        from app.routers.routing import _calculate_rule_based_score
        
        agent = {
            "performance_score": 0.8,
            "success_rate": 0.9
        }
        
        context = {"priority": "high"}
        
        score = _calculate_rule_based_score(agent, context)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.8  # Should be high due to good performance and high priority
    
    @pytest.mark.asyncio
    async def test_get_availability_score(self):
        """Test availability score calculation"""
        from app.routers.routing import _get_availability_score
        
        with patch('app.routers.routing.agent_service') as mock_service:
            # Test active agent
            mock_service.get_agent_by_id.return_value = {"status": "active"}
            score = await _get_availability_score("test-agent")
            assert score == 1.0
            
            # Test maintenance agent
            mock_service.get_agent_by_id.return_value = {"status": "maintenance"}
            score = await _get_availability_score("test-agent")
            assert score == 0.5
            
            # Test inactive agent
            mock_service.get_agent_by_id.return_value = {"status": "inactive"}
            score = await _get_availability_score("test-agent")
            assert score == 0.3
    
    @pytest.mark.asyncio
    async def test_get_candidate_agents(self):
        """Test candidate agent retrieval"""
        from app.routers.routing import _get_candidate_agents
        
        mock_agents = [
            {"id": "nlp-001", "type": "nlp"},
            {"id": "tts-001", "type": "tts"},
            {"id": "nlp-002", "type": "nlp"}
        ]
        
        with patch('app.routers.routing.agent_service') as mock_service:
            mock_service.get_active_agents.return_value = mock_agents
            
            candidates = await _get_candidate_agents("nlp")
            
            assert len(candidates) == 2
            assert all(agent["type"] == "nlp" for agent in candidates)
            assert candidates[0]["id"] == "nlp-001"
            assert candidates[1]["id"] == "nlp-002"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])