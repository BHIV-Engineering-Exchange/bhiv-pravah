from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .utils import SCHEMA_VERSION

BlueprintType = Literal[
    "content_blueprint",
    "analysis_blueprint",
    "workflow_blueprint",
    "knowledge_query_blueprint",
    "assistant_reasoning_blueprint",
]
InputType = Literal["text", "structured_json", "dataset_reference", "file_metadata"]


class PromptRunnerInstruction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str
    module: str
    intent: str
    topic: str
    tasks: List[str]
    output_format: str
    product_context: str


class BlueprintPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    blueprint_type: BlueprintType
    product_target: str


class BlueprintEnvelope(BaseModel):
    instruction_id: str
    origin: Literal["creator_core"] = "creator_core"
    intent_type: str
    target_product: str
    payload: BlueprintPayload
    schema_version: str = SCHEMA_VERSION
    timestamp: str


class ArtifactRecord(BaseModel):
    artifact_type: Literal["blueprint"] = "blueprint"
    source_module_id: Literal["creator_core"] = "creator_core"
    artifact_hash: str
    parent_hash: Optional[str] = None
    payload: Dict[str, Any]


class TelemetryEvent(BaseModel):
    event_name: Literal["intent.received", "instruction.generated", "blueprint.generated"]
    instruction_id: str
    creative_session_id: str
    origin_interface: str
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)