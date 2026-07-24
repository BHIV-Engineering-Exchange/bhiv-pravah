from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class WorkflowData(BaseModel):
    # ⚠️ MUST be exactly "workflow"
    workflow_type: Literal["workflow"] = Field(
        ..., description="Execution routing indicator"
    )

    # Actual execution instructions live here
    payload: Dict[str, Any] = Field(
        ..., description="Adapter-specific execution payload"
    )


class WorkflowExecuteRequest(BaseModel):
    trace_id: str = Field(..., min_length=1)

    # Guard decision from upstream brain
    decision: Literal[
        "respond",
        "task",
        "workflow",
        "insight",
        "fallback",
    ]

    # Required ONLY when decision == "workflow"
    data: Optional[WorkflowData] = None
