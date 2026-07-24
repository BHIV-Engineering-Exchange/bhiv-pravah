"""
Tests for Routing Decision Logger
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from app.utils.routing_decision_logger import RoutingDecisionLogger, get_routing_logger


class TestRoutingDecisionLogger:
    """Test cases for RoutingDecisionLogger"""
    
    @pytest.fixture
    def temp_logger(self):
        """Create logger with temporary directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = RoutingDecisionLogger(
                log_dir=temp_dir,
                log_file="test_routing.jsonl",
                retention_days=7
            )
            yield logger
    
    def test_log_decision_basic(self, temp_logger):
        """Test basic decision logging"""
        success = temp_logger.log_decision(
            agent_selected="nlp-001",
            confidence_score=0.85,
            request_id="test-123",
            context={"agent_type": "nlp", "priority": "high"},
            reasoning="Best match for NLP task"
        )
        
        assert success is True
        assert temp_logger.log_file.exists()
        
        # Verify log content
        with open(temp_logger.log_file, 'r') as f:
            line = f.readline().strip()
            entry = json.loads(line)
            
            assert entry["agent_selected"] == "nlp-001"
            assert entry["confidence_score"] == 0.85
            assert entry["request_id"] == "test-123"
            assert entry["decision_reasoning"] == "Best match for NLP task"
            assert "timestamp" in entry
    
    def test_log_decision_with_breakdown(self, temp_logger):
        """Test logging with score breakdown"""
        score_breakdown = {
            "rule_based": {"score": 0.8, "weight": 0.4},
            "feedback_based": {"score": 0.9, "weight": 0.4},
            "availability": {"score": 1.0, "weight": 0.2}
        }
        
        alternatives = [
            {"agent_id": "nlp-002", "confidence": 0.75},
            {"agent_id": "nlp-003", "confidence": 0.70}
        ]
        
        success = temp_logger.log_decision(
            agent_selected="nlp-001",
            confidence_score=0.87,
            request_id="test-breakdown",
            context={"agent_type": "nlp"},
            score_breakdown=score_breakdown,
            alternatives=alternatives,
            response_time_ms=45.5
        )
        
        assert success is True
        
        # Verify detailed content
        with open(temp_logger.log_file, 'r') as f:
            entry = json.loads(f.readline())
            
            assert entry["score_breakdown"] == score_breakdown
            assert entry["alternatives"] == alternatives
            assert entry["response_time_ms"] == 45.5
    
    def test_query_decisions_no_filter(self, temp_logger):
        """Test querying decisions without filters"""
        # Log multiple decisions
        for i in range(5):
            temp_logger.log_decision(
                agent_selected=f"agent-{i:03d}",
                confidence_score=0.8 + (i * 0.02),
                request_id=f"req-{i:03d}",
                context={"agent_type": "nlp"}
            )
        
        decisions = temp_logger.query_decisions()
        
        assert len(decisions) == 5
        assert decisions[0]["agent_selected"] == "agent-000"
        assert decisions[4]["agent_selected"] == "agent-004"
    
    def test_query_decisions_with_agent_filter(self, temp_logger):
        """Test querying decisions with agent filter"""
        # Log decisions for different agents
        agents = ["nlp-001", "nlp-002", "tts-001"]
        for agent in agents:
            temp_logger.log_decision(
                agent_selected=agent,
                confidence_score=0.8,
                request_id=f"req-{agent}",
                context={"agent_type": agent.split("-")[0]}
            )
        
        # Query for specific agent
        nlp_decisions = temp_logger.query_decisions(agent_id="nlp-001")
        
        assert len(nlp_decisions) == 1
        assert nlp_decisions[0]["agent_selected"] == "nlp-001"
    
    def test_query_decisions_with_limit(self, temp_logger):
        """Test querying decisions with limit"""
        # Log many decisions
        for i in range(10):
            temp_logger.log_decision(
                agent_selected=f"agent-{i}",
                confidence_score=0.8,
                request_id=f"req-{i}",
                context={"agent_type": "nlp"}
            )
        
        # Query with limit
        decisions = temp_logger.query_decisions(limit=3)
        
        assert len(decisions) == 3
    
    def test_get_statistics(self, temp_logger):
        """Test statistics calculation"""
        # Log decisions with varying confidence scores
        confidences = [0.7, 0.8, 0.9, 0.85, 0.75]
        response_times = [50, 60, 40, 55, 45]
        
        for i, (conf, time_ms) in enumerate(zip(confidences, response_times)):
            temp_logger.log_decision(
                agent_selected=f"agent-{i}",
                confidence_score=conf,
                request_id=f"req-{i}",
                context={"agent_type": "nlp"},
                response_time_ms=time_ms
            )
        
        stats = temp_logger.get_statistics()
        
        assert stats["total_decisions"] == 5
        assert stats["avg_confidence"] == sum(confidences) / len(confidences)
        assert stats["min_confidence"] == min(confidences)
        assert stats["max_confidence"] == max(confidences)
        assert stats["unique_agents"] == 5
        assert stats["avg_response_time_ms"] == sum(response_times) / len(response_times)
        assert stats["max_response_time_ms"] == max(response_times)
    
    def test_get_statistics_for_specific_agent(self, temp_logger):
        """Test statistics for specific agent"""
        # Log decisions for multiple agents
        agents = ["nlp-001", "nlp-001", "nlp-002", "nlp-001"]
        confidences = [0.8, 0.85, 0.7, 0.9]
        
        for agent, conf in zip(agents, confidences):
            temp_logger.log_decision(
                agent_selected=agent,
                confidence_score=conf,
                request_id=f"req-{agent}-{conf}",
                context={"agent_type": "nlp"}
            )
        
        # Get stats for nlp-001 only
        stats = temp_logger.get_statistics(agent_id="nlp-001")
        
        assert stats["total_decisions"] == 3  # nlp-001 appears 3 times
        assert stats["unique_agents"] == 1
        nlp_001_confidences = [0.8, 0.85, 0.9]
        assert stats["avg_confidence"] == sum(nlp_001_confidences) / len(nlp_001_confidences)
    
    def test_cleanup_old_logs(self, temp_logger):
        """Test cleanup of old log entries"""
        # Create old and new entries
        old_time = (datetime.utcnow() - timedelta(days=10)).isoformat() + "Z"
        new_time = datetime.utcnow().isoformat() + "Z"
        
        # Manually write entries with different timestamps
        old_entry = {
            "timestamp": old_time,
            "agent_selected": "old-agent",
            "confidence_score": 0.8,
            "request_id": "old-req"
        }
        
        new_entry = {
            "timestamp": new_time,
            "agent_selected": "new-agent", 
            "confidence_score": 0.9,
            "request_id": "new-req"
        }
        
        with open(temp_logger.log_file, 'w') as f:
            f.write(json.dumps(old_entry) + '\n')
            f.write(json.dumps(new_entry) + '\n')
        
        # Cleanup (retention_days=7, so 10-day-old entry should be deleted)
        deleted_count = temp_logger.cleanup_old_logs()
        
        assert deleted_count == 1
        
        # Verify only new entry remains
        decisions = temp_logger.query_decisions()
        assert len(decisions) == 1
        assert decisions[0]["agent_selected"] == "new-agent"
    
    def test_context_summarization(self):
        """Test context summarization"""
        # Test various context combinations
        contexts = [
            {"agent_type": "nlp", "priority": "high", "user_id": "user123456789"},
            {"priority": "low"},
            {"user_id": "short"},
            {}
        ]
        
        expected_summaries = [
            "nlp, priority=high, user=user1234",
            "priority=low",
            "user=short",
            "standard"
        ]
        
        for context, expected in zip(contexts, expected_summaries):
            summary = RoutingDecisionLogger._summarize_context(context)
            assert summary == expected
    
    def test_singleton_pattern(self):
        """Test get_routing_logger singleton behavior"""
        logger1 = get_routing_logger()
        logger2 = get_routing_logger()
        
        # Should return same instance
        assert logger1 is logger2
        assert isinstance(logger1, RoutingDecisionLogger)
    
    def test_error_handling_invalid_json(self, temp_logger):
        """Test error handling with corrupted log file"""
        # Write invalid JSON to log file
        with open(temp_logger.log_file, 'w') as f:
            f.write("invalid json line\n")
            f.write('{"valid": "json"}\n')
        
        # Should handle error gracefully
        decisions = temp_logger.query_decisions()
        assert len(decisions) == 1  # Only valid JSON line
        assert decisions[0]["valid"] == "json"
    
    def test_missing_log_file(self, temp_logger):
        """Test behavior with missing log file"""
        # Ensure log file doesn't exist
        if temp_logger.log_file.exists():
            temp_logger.log_file.unlink()
        
        # Query should return empty list
        decisions = temp_logger.query_decisions()
        assert decisions == []
        
        # Statistics should return error
        stats = temp_logger.get_statistics()
        assert "error" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])