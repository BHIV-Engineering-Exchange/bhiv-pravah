import logging
from datetime import datetime, timezone

from .bucket import LocalBucketStore
from .generator import BlueprintGenerator
from .models import BlueprintEnvelope, PromptRunnerInstruction
from .telemetry import InsightFlowTelemetryEmitter
from .utils import (
    SCHEMA_VERSION,
    build_instruction_id,
)


def _build_logger() -> logging.Logger:
    logger = logging.getLogger("creator_core_engine")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler("creator_core.log", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class CreatorCoreService:
    def __init__(
        self,
        generator: BlueprintGenerator | None = None,
        telemetry_emitter: InsightFlowTelemetryEmitter | None = None,
        bucket_store: LocalBucketStore | None = None,
    ):
        self.generator = generator or BlueprintGenerator()
        self.telemetry = telemetry_emitter or InsightFlowTelemetryEmitter()
        self.bucket = bucket_store or LocalBucketStore()
        self.logger = _build_logger()
        

    def build_envelope(
        self,
        instruction: PromptRunnerInstruction,
        instruction_id: str,
        timestamp: str,
    ) -> BlueprintEnvelope:
        blueprint = self.generator.generate(instruction)
        return BlueprintEnvelope(
            instruction_id=instruction_id,
            origin="creator_core",
            intent_type=instruction.intent,
            target_product=blueprint.product_target,
            payload=blueprint,
            schema_version=SCHEMA_VERSION,
            timestamp=timestamp,
        )

    def generate_blueprint(self, instruction: PromptRunnerInstruction | dict) -> BlueprintEnvelope:
        if not isinstance(instruction, PromptRunnerInstruction):
            instruction = PromptRunnerInstruction.model_validate(instruction)

        self.logger.info("request received | module=%s | intent=%s", instruction.module, instruction.intent)

        instruction_payload = instruction.model_dump(mode="json")
        instruction_id = build_instruction_id(instruction_payload)
        timestamp = datetime.now(timezone.utc).isoformat()
        session_for_telemetry = f"session_{instruction_id[:8]}"

        self.telemetry.emit(
            event_name="intent.received",
            instruction_id=instruction_id,
            creative_session_id=session_for_telemetry,
            origin_interface=instruction.product_context,
        )
        self.telemetry.emit(
            event_name="instruction.generated",
            instruction_id=instruction_id,
            creative_session_id=session_for_telemetry,
            origin_interface=instruction.product_context,
            metadata={
                "module": instruction.module,
                "intent": instruction.intent,
            },
        )

        try:
            envelope = self.build_envelope(
                instruction=instruction,
                instruction_id=instruction_id,
                timestamp=timestamp,
            )

            artifact = self.bucket.store_blueprint(envelope=envelope)
            self.telemetry.emit(
                event_name="blueprint.generated",
                instruction_id=instruction_id,
                creative_session_id=session_for_telemetry,
                origin_interface=instruction.product_context,
                metadata={
                    "artifact_hash": artifact.artifact_hash,
                    "target_product": envelope.target_product,
                    "blueprint_type": envelope.payload.blueprint_type,
                },
            )
            self.logger.info(
                "blueprint generated | instruction_id=%s | type=%s | target=%s",
                envelope.instruction_id,
                envelope.payload.blueprint_type,
                envelope.target_product,
            )
            return envelope
        except Exception:
            self.logger.exception("error while generating blueprint")
            raise