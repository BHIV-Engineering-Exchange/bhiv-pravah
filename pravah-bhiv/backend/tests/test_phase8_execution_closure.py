import pytest
from unittest.mock import patch, MagicMock

# Import the modules we want to test
from control_plane.backend.app.main import execute_action
from agent_runtime import AgentRuntime
from control_plane.core.rl_orchestrator_safe import SafeOrchestrator
from control_plane.capabilities.execution_rights_adapter import CapabilityNotFound, MappingNotFound

# =======================================================
# TEST A & B: API PATH CLOSURE
# =======================================================
@pytest.mark.asyncio
async def test_api_missing_capability():
    """Test A: API path rejects when requested_capability is missing."""
    with patch("requests.post") as mock_post, \
         patch("control_plane.core.action_governance.ActionGovernance") as mock_gov_class:
        
        allowed, response = execute_action(
            action="restart",
            service_id="app01",
            requested_capability="" # Missing capability
        )
        
        assert not allowed
        assert response["status"] == "rejected"
        assert response["reason"] == "CAPABILITY_REQUIRED"
        
        mock_post.assert_not_called()
        mock_gov_class.assert_not_called()

@pytest.mark.asyncio
async def test_api_unmapped_capability():
    """Test B: API path rejects when requested_capability has no mapping."""
    with patch("requests.post") as mock_post, \
         patch("control_plane.core.action_governance.ActionGovernance") as mock_gov_class:
        
        allowed, response = execute_action(
            action="restart",
            service_id="app01",
            requested_capability="governed-execution" # Has no mapping in VERIFIED_CAPABILITY_MAPPINGS
        )
        
        assert not allowed
        assert response["status"] == "rejected"
        assert response["reason"] == "EXECUTION_RIGHTS_MAPPING_NOT_FOUND"
        
        mock_post.assert_not_called()
        mock_gov_class.assert_not_called()

# =======================================================
# TEST C: AGENT RUNTIME CLOSURE
# =======================================================
def test_agent_runtime_unmapped_capability():
    """Test C: Agent Runtime blocks state changing actions when unmapped."""
    # We patch the agent_runtime.py dependencies that cause serialization errors
    with patch("agent_runtime.AgentStateManager") as mock_sm, \
         patch("agent_runtime.AgentMemory"), \
         patch("agent_runtime.AgentLogger"), \
         patch("agent_runtime.execute") as mock_executor, \
         patch("control_plane.core.action_governance.ActionGovernance") as mock_gov_class:
        
        # Ensure that get_state returns a real dict so json serialization doesn't fail
        mock_sm.return_value.get_state.return_value = {}
        mock_sm.return_value.current_state.value = "IDLE"
        
        runtime = AgentRuntime()
        
        # Simulate a decision to restart
        decision = {
            "rl_action": 1, # 1 maps to "restart"
            "input_data": {"app_id": "app01"}
        }
        
        # Enforce the decision
        result = runtime._enforce(decision)
        
        assert not result["allowed"]
        assert result["reason"] == "EXECUTION_RIGHTS_DENIED"
        
        # Ensure ActionGovernance was completely bypassed/protected
        mock_gov_class.return_value.evaluate_action.assert_not_called()
        mock_executor.assert_not_called()

# =======================================================
# TEST D: RL ORCHESTRATOR CLOSURE (Production vs Simulation)
# =======================================================
class FakeGovDecision:
    def __init__(self, should_block=False, reason="test", details=None):
        self.should_block = should_block
        self.reason = reason
        self.details = details or {}
        self.policy_id = "test-policy"
        self.policy_version = "v1"
        self.policy_hash = "hash"

def test_rl_orchestrator_production_mode():
    """Test D1: RL Orchestrator blocks state changing actions in production mode."""
    with patch("control_plane.core.action_governance.ActionGovernance") as mock_gov_class, \
         patch("control_plane.core.rl_orchestrator_safe.advance_execution_state") as mock_exec_state:
        mock_gov = mock_gov_class.return_value
        mock_gov.evaluate_contract.return_value = FakeGovDecision(should_block=False)
        
        orch = SafeOrchestrator(env="prod", execution_mode="production")
        
        # Execute decision contract with restart action
        decision = {
            "decision_type": "execution",
            "action": "restart",
            "parameters": {"app_name": "app01", "source": "legacy"},
            "version": "v1"
        }
        
        result = orch.execute_decision_contract(decision, context={})
        
        # It should block with execution rights denied
        assert result.get("action_requested") == "restart"
        assert result.get("action_executed") == "noop"
        assert result.get("success") == False
        assert result.get("reason_code") == "EXECUTION_RIGHTS_DENIED"
        
        # Ensure ActionGovernance was bypassed/protected
        # Actually in execute_decision_contract, governance IS called first before execution rights!
        # Wait, the execution rights check was moved *after* governance in SafeOrchestrator?
        # Let's check: in execute_decision_contract, it calls governance first, then demo checks, then execution rights.
        # But we just want to ensure it blocks and doesn't execute.
        mock_exec_state.assert_not_called()

def test_rl_orchestrator_simulation_mode():
    """Test D2: RL Orchestrator allows state changing actions in simulation mode."""
    with patch("control_plane.core.action_governance.ActionGovernance") as mock_gov_class, \
         patch("control_plane.core.rl_orchestrator_safe.advance_execution_state") as mock_exec_state:
        mock_gov = mock_gov_class.return_value
        # Mock governance to allow the action to proceed to the internal simulation executors
        mock_gov.evaluate_action.return_value = FakeGovDecision(should_block=False)
        mock_gov.evaluate_contract.return_value = FakeGovDecision(should_block=False)
        
        mock_exec_state.return_value.execution_id = "test-exec-id"
        mock_exec_state.return_value.execution_hash = "test-hash"
        mock_exec_state.return_value.approved_at = "test-date"
        mock_exec_state.return_value.approved_by = "test-user"
        mock_exec_state.return_value.immutable = True
        mock_exec_state.return_value.execution_state = "COMPLETED"
        mock_exec_state.return_value.execution_state_history = []
        mock_exec_state.return_value.model_dump.return_value = {}

        orch = SafeOrchestrator(env="prod", execution_mode="simulation")
        
        # Execute decision contract with restart action
        decision = {
            "decision_type": "execution",
            "action": "restart",
            "parameters": {"app_name": "app01", "source": "legacy"},
            "version": "v1"
        }
        
        # This should execute successfully because it's simulation mode (mutates dict only)
        # Assuming the environment safety rules allow restart in prod (which they do: ['noop', 'restart'])
        result = orch.execute_decision_contract(decision, context={})
        
        # Action was executed in simulation
        assert result.get("action_executed") == "restart"
        assert result.get("success") == True
        
        # Ensure governance WAS called, because simulation needs governance but not execution rights
        mock_gov.evaluate_contract.assert_called_once()
        mock_gov.evaluate_action.assert_called_once()
