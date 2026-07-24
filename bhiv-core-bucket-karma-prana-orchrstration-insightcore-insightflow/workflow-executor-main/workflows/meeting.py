from typing import Dict, Any
from adapters.meeting_adapter import MeetingAdapter

# Single adapter instance (stateless, safe, pluggable)
adapter = MeetingAdapter()


def execute_meeting(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Meeting workflow execution.

    Delegates execution to MeetingAdapter.
    No business logic lives here.
    """
    return adapter.execute(payload)
