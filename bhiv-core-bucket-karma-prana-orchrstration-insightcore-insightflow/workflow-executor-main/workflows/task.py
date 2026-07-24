from typing import Dict, Any
from adapters.task_adapter import TaskAdapter

# Single adapter instance (safe, stateless, pluggable)
adapter = TaskAdapter()


def execute_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Task workflow execution.

    Delegates execution to TaskAdapter.
    This function contains NO business logic.
    """
    return adapter.execute(payload)
