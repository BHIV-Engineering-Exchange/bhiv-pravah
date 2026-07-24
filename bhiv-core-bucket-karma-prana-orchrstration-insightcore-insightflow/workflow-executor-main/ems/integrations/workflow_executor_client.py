import os
import requests
from typing import Dict, Any

WORKFLOW_EXECUTOR_URL = os.getenv("WORKFLOW_EXECUTOR_URL")

if not WORKFLOW_EXECUTOR_URL:
    raise RuntimeError("WORKFLOW_EXECUTOR_URL is not set")


def send_workflow_to_executor(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    EMS → Workflow Executor bridge.
    EMS NEVER executes side effects directly.
    """

    response = requests.post(
        f"{WORKFLOW_EXECUTOR_URL}/api/workflow/execute",
        json=payload,
        timeout=10,
    )

    response.raise_for_status()
    return response.json()