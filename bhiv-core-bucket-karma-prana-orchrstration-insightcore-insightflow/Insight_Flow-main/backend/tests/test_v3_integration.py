# tests/test_v3_integration.py
"""
V3 Integration Tests

Tests full telemetry, STP, and Q-learning flow.
"""

import pytest
import asyncio
from app.telemetry_bus.service import TelemetryBusService
from app.stp_bridge.stp_bridge_integration import STPBridgeIntegration
from app.ml.q_learning_updater import QLearningUpdater


class TestV3Integration:
    """Test complete V3 integration"""
    
    def test_telemetry_to_dashboard_flow(self):
        """Test telemetry packet flow"""
        # TODO: Implement WebSocket client test
        pass
    
    def test_stp_feedback_processing(self):
        """Test STP feedback parsing and enrichment"""
        stp_bridge = STPBridgeIntegration(enable_feedback=True)
        
        # Test feedback parsing
        feedback_payload = {
            "karmic_weight": 0.34,
            "reward_value": 0.5,
            "context_tags": ["discipline", "consistency"],
            "stp_version": "stp-1"
        }
        
        parsed = stp_bridge.parse_stp_feedback(feedback_payload)
        
        assert parsed.reward == 0.5
        assert parsed.weights["karmic_weight"] == 0.34
        assert "discipline" in parsed.context_tags
    
    def test_q_learning_updates(self):
        """Test Q-learning update logic"""
        q_updater = QLearningUpdater(enable_updates=True)
        
        # Perform update
        old_conf, new_conf = q_updater.q_update(
            state="state1",
            action="agent1",
            reward=0.8,
            request_id="test-123"
        )
        
        assert 0.0 <= new_conf <= 1.0
        assert new_conf != old_conf
    
    def test_q_learning_bounds(self):
        """Test Q-values stay within bounds"""
        q_updater = QLearningUpdater(enable_updates=True)
        
        # Extreme rewards should not break bounds
        for reward in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            _, new_conf = q_updater.q_update(
                state="test",
                action="agent",
                reward=reward
            )
            
            assert 0.0 <= new_conf <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])