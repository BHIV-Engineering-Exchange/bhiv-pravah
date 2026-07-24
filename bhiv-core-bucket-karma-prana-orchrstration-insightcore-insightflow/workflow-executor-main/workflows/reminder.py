from typing import Dict, Any
from adapters.reminder_adapter import ReminderAdapter

# Single adapter instance (stateless, safe, pluggable)
adapter = ReminderAdapter()


def execute_reminder(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reminder workflow execution.

    Delegates execution to ReminderAdapter.
    No business logic lives here.
    """
    return adapter.execute(payload)
