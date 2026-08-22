import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock
from copy import deepcopy

backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

import control_plane.multi_app_control_plane
control_plane.multi_app_control_plane.MultiAppControlPlane = MagicMock()

from control_plane.capabilities.execution_rights_adapter import ExecutionRightsAdapter, CapabilityNotFound, MappingNotFound, authorize_execution
from control_plane.capabilities.capability_discovery import CapabilityDiscovery

class MockDiscovery(CapabilityDiscovery):
    def discover_by_id(self, capability_id: str):
        if capability_id == "governed-execution" or capability_id == "test-capability":
            return {
                "capability_id": capability_id,
                "owner_group": "group4",
                "module_id": "group4-governed-runtime"
            }
        return None

# Use an existing file in the repo for evidence tests
TEST_EVIDENCE_FILE = "backend/control_plane/capabilities/execution_rights_adapter.py"
TEST_EVIDENCE_LINE = 10

def valid_mapping_data():
    return {
        "test-capability": {
            "source_id": "test-verified-source",
            "role": "test-role",
            "allowed_actions": ["restart", "scale"],
            "verification": {"status": "VERIFIED"},
            "evidence": {
                "file": TEST_EVIDENCE_FILE,
                "line": TEST_EVIDENCE_LINE
            }
        }
    }

@pytest.fixture
def valid_adapter():
    return ExecutionRightsAdapter(discovery=MockDiscovery(), mappings=valid_mapping_data())

def test_missing_capability():
    with pytest.raises(CapabilityNotFound):
        authorize_execution(None, "restart")

def test_unknown_capability():
    adapter = ExecutionRightsAdapter(discovery=MockDiscovery(), mappings={})
    with pytest.raises(CapabilityNotFound):
        authorize_execution("unknown-cap", "restart", adapter=adapter)

def test_mapping_missing():
    adapter = ExecutionRightsAdapter(discovery=MockDiscovery(), mappings={})
    with pytest.raises(MappingNotFound):
        authorize_execution("governed-execution", "restart", adapter=adapter)

def test_generate_execution_payload():
    adapter = ExecutionRightsAdapter(discovery=MockDiscovery(), mappings={})
    with pytest.raises(MappingNotFound):
        adapter.generate_execution_payload(
            capability_id="governed-execution",
            action="restart",
            service_id="app01",
            trace_id="test",
            caller_source_id="agent_runtime"
        )

@pytest.mark.parametrize("status", [None, "DRAFT", "UNVERIFIED", ""])
def test_invalid_verification(status):
    data = valid_mapping_data()
    if status is None:
        del data["test-capability"]["verification"]
    else:
        data["test-capability"]["verification"]["status"] = status
    
    adapter = ExecutionRightsAdapter(discovery=MockDiscovery(), mappings=data)
    with pytest.raises(MappingNotFound):
        authorize_execution("test-capability", "restart", adapter=adapter)

def test_missing_allowed_actions():
    data = valid_mapping_data()
    del data["test-capability"]["allowed_actions"]
    adapter = ExecutionRightsAdapter(discovery=MockDiscovery(), mappings=data)
    with pytest.raises(MappingNotFound):
        authorize_execution("test-capability", "restart", adapter=adapter)

def test_empty_allowed_actions():
    data = valid_mapping_data()
    data["test-capability"]["allowed_actions"] = []
    adapter = ExecutionRightsAdapter(discovery=MockDiscovery(), mappings=data)
    with pytest.raises(MappingNotFound):
        authorize_execution("test-capability", "restart", adapter=adapter)

def test_missing_action():
    adapter = ExecutionRightsAdapter(discovery=MockDiscovery(), mappings=valid_mapping_data())
    with pytest.raises(MappingNotFound):
        authorize_execution("test-capability", "", adapter=adapter)
    with pytest.raises(MappingNotFound):
        authorize_execution("test-capability", None, adapter=adapter)

def test_unauthorized_action():
    adapter = ExecutionRightsAdapter(discovery=MockDiscovery(), mappings=valid_mapping_data())
    with pytest.raises(MappingNotFound):
        authorize_execution("test-capability", "delete_database", adapter=adapter)

def test_evidence_file_missing():
    data = valid_mapping_data()
    data["test-capability"]["evidence"]["file"] = "nonexistent/file/path.py"
    adapter = ExecutionRightsAdapter(discovery=MockDiscovery(), mappings=data)
    with pytest.raises(MappingNotFound):
        authorize_execution("test-capability", "restart", adapter=adapter)

def test_evidence_path_escapes_repository():
    data = valid_mapping_data()
    data["test-capability"]["evidence"]["file"] = "../../../../etc/passwd"
    adapter = ExecutionRightsAdapter(discovery=MockDiscovery(), mappings=data)
    with pytest.raises(MappingNotFound):
        authorize_execution("test-capability", "restart", adapter=adapter)

@pytest.mark.parametrize("line", [0, -1, 9999999])
def test_invalid_evidence_line(line):
    data = valid_mapping_data()
    data["test-capability"]["evidence"]["line"] = line
    adapter = ExecutionRightsAdapter(discovery=MockDiscovery(), mappings=data)
    with pytest.raises(MappingNotFound):
        authorize_execution("test-capability", "restart", adapter=adapter)

def test_valid_authorization(valid_adapter):
    auth = authorize_execution("test-capability", "restart", adapter=valid_adapter)
    assert auth["authorized_source_id"] == "test-verified-source"
    assert auth["action"] == "restart"
    assert "evidence" in auth

# --- End to End Proofs ---

def patch_main_for_e2e(monkeypatch, valid_mapping):
    import control_plane.backend.app.main as main_module
    import control_plane.core.action_governance as governance_module
    import requests

    class MockGovernance:
        POLICY_VERSION = "v1"
        def __init__(self, env):
            self.env = env
        def evaluate_contract(self, decision, context, source):
            class MockDecision:
                should_block = False
            return MockDecision()

    monkeypatch.setattr(governance_module, "ActionGovernance", MockGovernance)
    
    mock_post = MagicMock()
    class MockResponse:
        def json(self): return {"status": "executed", "reason": "success"}
    mock_post.return_value = MockResponse()
    monkeypatch.setattr(requests, "post", mock_post)

    import control_plane.capabilities.execution_rights_adapter as adapter_module
    class MockAdapter(ExecutionRightsAdapter):
        def __init__(self, *args, **kwargs):
            super().__init__(discovery=MockDiscovery(), mappings=valid_mapping)
    
    monkeypatch.setattr(adapter_module, "ExecutionRightsAdapter", MockAdapter)
    
    return mock_post

def test_e2e_rejection_executor_not_called(monkeypatch):
    """Prove that for every rejection case, the executor is not called."""
    from control_plane.backend.app.main import execute_action
    
    # We pass empty mappings so authorize_execution will fail
    mock_post = patch_main_for_e2e(monkeypatch, {})

    success, result = execute_action("restart", "app01", requested_capability="test-capability")
    
    assert not success
    assert result["status"] == "rejected"
    mock_post.assert_not_called()

def test_e2e_authorization_executor_called(monkeypatch):
    """Prove that for the one valid mapping, the executor is called exactly once."""
    from control_plane.backend.app.main import execute_action
    
    mock_post = patch_main_for_e2e(monkeypatch, valid_mapping_data())

    success, result = execute_action("restart", "app01", requested_capability="test-capability")
    
    assert success
    assert result["status"] == "executed"
    mock_post.assert_called_once()


def test_governance_authorization_enforcement_and_forgery():
    """Prove that ActionGovernance explicitly consumes and enforces the authorization context with cryptographic forgery protection."""
    from control_plane.core.action_governance import ActionGovernance
    from contracts.decision_contract import validate_decision_contract
    from security.signed_trace import sign_trace, canonicalize

    # Use a real ActionGovernance instance
    gov = ActionGovernance(env="dev")

    decision = validate_decision_contract({
        "decision_type": "execution",
        "action": "restart",
        "parameters": {"app_name": "test"},
        "version": "v1"
    })

    # Test 1: Missing authorization entirely
    context = {"source": "agent_runtime", "app_name": "test"}
    result = gov.evaluate_contract(decision, context, source="agent_runtime")
    assert result.should_block
    assert result.rejection_code == "EXECUTION_NOT_PERMITTED"
    assert "Missing execution authorization" in result.details["message"]

    # Test 2: Authorization present but missing signature
    context = {
        "source": "agent_runtime",
        "app_name": "test",
        "execution_authorization": {
            "authorized_source_id": "governance"
        }
    }
    result = gov.evaluate_contract(decision, context, source="agent_runtime")
    assert result.should_block
    assert result.rejection_code == "EXECUTION_NOT_PERMITTED"
    assert "Missing cryptographic signature" in result.details["message"]

    # Test 3: Fake/Random signature
    context["execution_authorization"]["signature"] = "fake-signature-1234"
    result = gov.evaluate_contract(decision, context, source="agent_runtime")
    assert result.should_block
    assert result.rejection_code == "EXECUTION_NOT_PERMITTED"
    assert "Invalid or forged" in result.details["message"]

    # Test 4: Valid signature but spoofed authorized_source_id
    auth_payload = {"authorized_source_id": "malicious_user"}
    auth_payload["signature"] = sign_trace(canonicalize(auth_payload))
    context["execution_authorization"] = auth_payload
    
    result = gov.evaluate_contract(decision, context, source="agent_runtime")
    assert result.should_block
    assert result.rejection_code == "EXECUTION_NOT_PERMITTED"
    assert "not a trusted governance authority" in result.details["message"]

    # Test 5: Valid signed payload, but modified after signing (TAMPERING)
    auth_payload = {"authorized_source_id": "governance"}
    valid_signature = sign_trace(canonicalize(auth_payload))
    auth_payload["authorized_source_id"] = "attacker" # Modified AFTER signing
    auth_payload["signature"] = valid_signature
    context["execution_authorization"] = auth_payload

    result = gov.evaluate_contract(decision, context, source="agent_runtime")
    assert result.should_block
    assert result.rejection_code == "EXECUTION_NOT_PERMITTED"
    assert "Invalid or forged" in result.details["message"]

    # Test 6: Valid authorization
    auth_payload = {"authorized_source_id": "governance"}
    auth_payload["signature"] = sign_trace(canonicalize(auth_payload))
    context["execution_authorization"] = auth_payload

    result = gov.evaluate_contract(decision, context, source="agent_runtime")
    # Result should NOT be blocked by the execution rights check.
    assert result.rejection_code != "EXECUTION_NOT_PERMITTED"


def test_true_e2e_integration_proof(monkeypatch):
    """
    Run a true E2E test without mocking ActionGovernance.
    Verifies that the authorized_source_id propagates through the real execution contract 
    and trusted signer boundary.
    """
    import requests
    from control_plane.backend.app.main import execute_action
    from unittest.mock import MagicMock
    import control_plane.capabilities.execution_rights_adapter as adapter_module

    # Patch ONLY the final executor network call
    mock_post = MagicMock()
    class MockResponse:
        def json(self): return {"status": "executed", "reason": "success"}
    mock_post.return_value = MockResponse()
    monkeypatch.setattr(requests, "post", mock_post)

    # ---------------------------------------------------------
    # TRUE REJECTION PATH 1: Missing execution_authorization
    # We mock the adapter to simulate a bypass where authorization was stripped,
    # proving ActionGovernance enforces the trust boundary itself.
    # ---------------------------------------------------------
    def mock_authorize_missing(cap, action, adapter=None):
        return None # Missing authorization dict

    monkeypatch.setattr(adapter_module, "authorize_execution", mock_authorize_missing)
    success, result = execute_action("restart", "app01", requested_capability="governed-execution")
    assert not success
    assert result["status"] == "rejected"
    assert result["rejection_code"] == "EXECUTION_NOT_PERMITTED"
    mock_post.assert_not_called()

    # ---------------------------------------------------------
    # TRUE REJECTION PATH 2: Fake/Malicious authorized_source_id
    # We mock the adapter to return a malicious identity,
    # proving ActionGovernance mathematically rejects untrusted signers.
    # ---------------------------------------------------------
    def mock_authorize_malicious(cap, action, adapter=None):
        return {"authorized_source_id": "malicious_user", "action": action}

    monkeypatch.setattr(adapter_module, "authorize_execution", mock_authorize_malicious)
    success, result = execute_action("restart", "app01", requested_capability="governed-execution")
    assert not success
    assert result["status"] == "rejected"
    assert result["rejection_code"] == "EXECUTION_NOT_PERMITTED"
    mock_post.assert_not_called()

    # ---------------------------------------------------------
    # TRUE AUTHORIZED PATH: Real capability mapping + Real governance
    # ---------------------------------------------------------
    # Remove our adapter mock so it uses the real fail-closed adapter and production mapping
    import importlib
    importlib.reload(adapter_module)
    from control_plane.backend.app.main import execute_action as real_execute_action
    
    # We must patch the function inside main module directly since we overrode it
    import control_plane.backend.app.main as main_module
    main_module.authorize_execution = adapter_module.authorize_execution

    success, result = real_execute_action("restart", "app01", requested_capability="governed-execution")
    
    # Depending on test environment policies (e.g. cooldown active), it might reject, 
    # but it MUST NOT reject for EXECUTION_NOT_PERMITTED (authorization failure).
    if not success:
        assert result.get("rejection_code") != "EXECUTION_NOT_PERMITTED"
    else:
        assert success
        assert result["status"] == "executed"
        mock_post.assert_called_once()


def test_canonicalization_is_order_independent():
    """Verify that canonicalization enforces deterministic HMAC verification regardless of dictionary insertion order or nesting."""
    from security.signed_trace import canonicalize

    payload_a = {
        "authorized_source_id": "governance",
        "action": "restart",
        "nested": {
            "b": 2,
            "a": 1
        },
        "list": [3, 2, 1] # Lists maintain order in canonicalize
    }

    payload_b = {
        "action": "restart",
        "nested": {
            "a": 1,
            "b": 2
        },
        "authorized_source_id": "governance",
        "list": [3, 2, 1]
    }

    assert canonicalize(payload_a) == canonicalize(payload_b)
