from contextvars import ContextVar
from typing import Optional

# Global context for trace_id
_trace_id_ctx: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

def set_trace_id(trace_id: Optional[str]) -> None:
    """Set the trace_id in the current context."""
    _trace_id_ctx.set(trace_id)

def get_trace_id() -> Optional[str]:
    """Get the trace_id from the current context."""
    return _trace_id_ctx.get()
