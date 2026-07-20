from typing import Any, Dict

from .adapters import AssistantAdapter, ContentAdapter, FinanceAdapter, LegalAdapter, WorkflowAdapter
from .models import BlueprintPayload, PromptRunnerInstruction


class BlueprintGenerator:
    MODULE_TO_BLUEPRINT = {
        "creator": "content_blueprint",
        "education": "content_blueprint",
        "finance": "analysis_blueprint",
        "workflow": "workflow_blueprint",
        "architecture": "workflow_blueprint",
        "legal": "knowledge_query_blueprint",
        "assistant": "assistant_reasoning_blueprint",
    }

    MODULE_TO_TARGET_PRODUCT = {
        "creator": "creator",
        "education": "education",
        "finance": "finance",
        "workflow": "workflow",
        "architecture": "architecture",
        "legal": "legal",
        "assistant": "assistant",
    }

    def __init__(self):
        self.adapters = {
            "content_blueprint": ContentAdapter(),
            "analysis_blueprint": FinanceAdapter(),
            "workflow_blueprint": WorkflowAdapter(),
            "knowledge_query_blueprint": LegalAdapter(),
            "assistant_reasoning_blueprint": AssistantAdapter(),
        }

    def generate(self, instruction: PromptRunnerInstruction) -> BlueprintPayload:
        blueprint_type = self.MODULE_TO_BLUEPRINT.get(instruction.module, "content_blueprint")

        generic_payload = self._build_generic_payload(instruction)
        adapter = self.adapters[blueprint_type]
        product_payload = adapter.transform(instruction, generic_payload)
        target_product = self.MODULE_TO_TARGET_PRODUCT.get(instruction.module, "creator")

        merged_payload = {
            "blueprint_type": blueprint_type,
            "product_target": target_product,
            **product_payload,
        }
        return BlueprintPayload.model_validate(merged_payload)

    def _build_generic_payload(self, instruction: PromptRunnerInstruction) -> Dict[str, Any]:
        return {
            "prompt": instruction.prompt,
            "module": instruction.module,
            "intent": instruction.intent,
            "topic": instruction.topic,
            "tasks": list(instruction.tasks),
            "output_format": instruction.output_format,
            "product_context": instruction.product_context,
        }