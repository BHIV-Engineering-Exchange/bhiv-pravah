from fastapi import APIRouter, HTTPException
import os

from .models import PromptRunnerInstruction
from .service import CreatorCoreService
from .bhiv_client import BhivCoreClient


def create_creator_core_router(service: CreatorCoreService) -> APIRouter:
    router = APIRouter(prefix="/creator-core", tags=["creator-core"])

    @router.post("/generate-blueprint")
    async def generate_blueprint(request: PromptRunnerInstruction) -> dict:
        try:
            # Generate envelope (unchanged blueprint)
            envelope = service.generate_blueprint(request)

            # Prepare JSON for external transport (do not mutate envelope)
            envelope_json = envelope.model_dump(mode="json", exclude_none=True)

            # BHIV Core forwarding (defaults to local BHIV Core at 127.0.0.1:8001)
            core_url = os.environ.get("BHIV_CORE_URL", "http://127.0.0.1:8001")
            forward_to_bhiv = os.environ.get("ENABLE_BHIV_FORWARD", "false").strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }

            if forward_to_bhiv:
                client = BhivCoreClient(core_url)

                mapped_payload = {
                    "task_id": envelope_json["instruction_id"],
                    "input": request.prompt,
                    "agent": envelope_json["target_product"],
                    "tags": [envelope_json["intent_type"]],
                    "source_texts": [envelope_json["payload"]],
                }
                service.logger.info("SENDING TO BHIV CORE: %s", mapped_payload)

                try:
                    core_response = client.send_to_execute_task(envelope_json, request.prompt)
                    service.logger.info("CORE RESPONSE: %s", core_response)
                except Exception:  # pragma: no cover - network I/O
                    service.logger.exception("BHIV Core call failed | instruction_id=%s", envelope.instruction_id)
                    core_response = {"status": "error", "message": "Core request failed"}
            else:
                service.logger.info(
                    "BHIV forwarding disabled | instruction_id=%s | set ENABLE_BHIV_FORWARD=true to enable",
                    envelope.instruction_id,
                )
                core_response = {
                    "status": "skipped",
                    "message": "BHIV forwarding disabled",
                    "core_url": core_url,
                }

            if forward_to_bhiv:
                return {"blueprint": envelope_json, "core_response": core_response}
            return {"blueprint": envelope_json}
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    return router