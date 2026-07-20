import json
from typing import Any, Dict
from urllib import request

from .models import BlueprintEnvelope


class BhivCoreClient:
    def __init__(self, core_url: str):
        self.core_url = core_url.rstrip("/")

    def send_envelope(self, envelope: BlueprintEnvelope) -> Dict[str, Any]:
        payload = json.dumps(envelope.model_dump(mode="json", exclude_none=True)).encode("utf-8")
        http_request = request.Request(
            url=f"{self.core_url}/core",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(http_request) as response:
            return json.loads(response.read().decode("utf-8"))

    def send_to_execute_task(self, envelope_json: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Map Creator Core envelope to BHIV TaskPayload and send to /execute_task."""
        mapped_payload = {
            "task_id": envelope_json["instruction_id"],
            "input": prompt,
            "agent": envelope_json["target_product"],
            "tags": [envelope_json["intent_type"]],
            "source_texts": [envelope_json["payload"]],
        }

        payload = json.dumps(mapped_payload).encode("utf-8")
        http_request = request.Request(
            url=f"{self.core_url}/execute_task",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(http_request) as response:
            return json.loads(response.read().decode("utf-8"))