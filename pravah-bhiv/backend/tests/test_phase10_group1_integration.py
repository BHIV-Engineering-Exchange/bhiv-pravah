import pytest
import requests
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from control_plane.capabilities.capability_discovery import CapabilityDiscovery

def test_group1_observation_api_live_health():
    """
    Registry-to-runtime integration test for group1-observation-api.
    Reads the endpoint from CapabilityDiscovery and verifies the actual HTTP service is reachable.
    """
    discovery = CapabilityDiscovery()
    cap = discovery.discover_by_id("group1-observation-api")
    
    assert cap is not None, "group1-observation-api capability not found in registry"
    endpoint = cap.get("endpoint")
    assert endpoint is not None, "Endpoint is missing in registry for group1-observation-api"
    
    # Verify the live endpoint is healthy
    response = requests.get(
        f"{endpoint}/health",
        timeout=10
    )

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"

    body = response.json()
    assert body.get("status") == "healthy", f"Expected status='healthy', got {body.get('status')}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
                