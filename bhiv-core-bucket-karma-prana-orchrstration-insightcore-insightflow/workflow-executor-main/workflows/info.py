from typing import Dict, Any
from adapters.info_adapter import InfoAdapter

# Single adapter instance (stateless, safe, pluggable)
adapter = InfoAdapter()


def execute_info(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Informational workflow execution.

    Delegates execution to InfoAdapter.
    No business logic lives here.
    """
    return adapter.execute(payload)
