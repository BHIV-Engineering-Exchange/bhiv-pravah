import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .models import TelemetryEvent


class InsightFlowTelemetryEmitter:
    def __init__(self, output_path: str = "db/creator_core_telemetry/insightflow_events.jsonl"):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(
        self,
        event_name: str,
        instruction_id: str,
        creative_session_id: str,
        origin_interface: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TelemetryEvent:
        event = TelemetryEvent(
            event_name=event_name,
            instruction_id=instruction_id,
            creative_session_id=creative_session_id,
            origin_interface=origin_interface,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {},
        )

        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=True, sort_keys=True))
            handle.write("\n")

        return event