import os
import requests
from typing import Dict, Any

WORKFLOW_EXECUTOR_URL = os.getenv("WORKFLOW_EXECUTOR_URL")

if not WORKFLOW_EXECUTOR_URL:
    raise RuntimeError("WORKFLOW_EXECUTOR_URL not set")

def execute_workflow(payload: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(
        f"{WORKFLOW_EXECUTOR_URL}/api/workflow/execute",
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
