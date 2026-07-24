"""
MITRA REPLAY TEST HARNESS
-------------------------
Provides trace-based replay capability for governance and testing.
Allows replaying any historical trace through the pipeline.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from app.services.bucket_service import BucketService
from app.core.assistant_orchestrator import handle_assistant_request
from app.core.logging import get_logger

logger = get_logger(__name__)


class ReplayResult:
    """Result of a replay operation."""

    def __init__(
        self,
        trace_id: str,
        original_stages: list[Dict[str, Any]],
        replayed_response: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        self.trace_id = trace_id
        self.original_stages = original_stages
        self.replayed_response = replayed_response
        self.error = error
        self.success = error is None and replayed_response is not None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "trace_id": self.trace_id,
            "success": self.success,
            "original_stages_count": len(self.original_stages),
            "original_stages": [s.get("stage") for s in self.original_stages],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        if self.replayed_response:
            result["replayed_response"] = self.replayed_response
        if self.error:
            result["error"] = self.error
        return result


class ReplayHarness:
    """Replay historical traces through the Mitra pipeline."""

    def __init__(self):
        self.bucket = BucketService()

    def load_trace(self, trace_id: str) -> list[Dict[str, Any]]:
        """Load all bucket entries for a given trace_id."""
        return self.bucket.get_trace_logs(trace_id)

    def extract_original_request(self, stages: list[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract the original request from bucket stages."""
        for stage in stages:
            if stage.get("stage") == "mitra_request_log":
                data = stage.get("data", {})
                # Reconstruct the request format
                input_data = data.get("input", {})
                raw_input = input_data.get("raw_input", {})
                message = input_data.get("text") or raw_input.get("message") or ""
                context = data.get("final_output", {}).get("system_context", {})

                return {
                    "version": "3.0.0",
                    "input": {
                        "message": message,
                        "summarized_payload": None,
                    },
                    "context": {
                        "platform": context.get("platform", "replay"),
                        "device": context.get("device", "unknown"),
                        "session_id": context.get("session_id", "replay_session"),
                        "voice_input": context.get("voice_input", False),
                        "preferred_language": context.get("preferred_language", "auto"),
                        "detected_language": context.get("detected_language"),
                        "authenticated_user_context": {
                            "auth_method": "replay",
                            "principal": context.get("user_id", "replay_user"),
                            "platform": context.get("platform", "replay"),
                        },
                    },
                }
        return None

    async def replay(
        self,
        trace_id: str,
        modifications: Optional[Dict[str, Any]] = None,
    ) -> ReplayResult:
        """
        Replay a historical trace through the pipeline.

        Args:
            trace_id: The trace_id to replay
            modifications: Optional modifications to apply to the original request

        Returns:
            ReplayResult with original stages and replayed response
        """
        # Load original trace
        stages = self.load_trace(trace_id)
        if not stages:
            return ReplayResult(
                trace_id=trace_id,
                original_stages=[],
                error="No bucket entries found for trace_id",
            )

        # Extract original request
        original_request = self.extract_original_request(stages)
        if not original_request:
            return ReplayResult(
                trace_id=trace_id,
                original_stages=stages,
                error="Could not extract original request from bucket stages",
            )

        # Apply modifications if provided
        replay_request = original_request.copy()
        if modifications:
            if "input" in modifications:
                replay_request["input"].update(modifications["input"])
            if "context" in modifications:
                replay_request["context"].update(modifications["context"])

        # Replay through pipeline
        try:
            replayed_response = await handle_assistant_request(replay_request)
            return ReplayResult(
                trace_id=trace_id,
                original_stages=stages,
                replayed_response=replayed_response,
            )
        except Exception as e:
            logger.error(f"Replay failed for trace {trace_id}: {e}")
            return ReplayResult(
                trace_id=trace_id,
                original_stages=stages,
                error=str(e),
            )

    def compare(
        self,
        original: Dict[str, Any],
        replayed: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compare original and replayed responses.

        Returns:
            Comparison result with diffs
        """
        differences = []

        # Compare top-level keys
        original_keys = set(original.keys())
        replayed_keys = set(replayed.keys())

        missing_in_replay = original_keys - replayed_keys
        extra_in_replay = replayed_keys - original_keys

        if missing_in_replay:
            differences.append(f"Keys missing in replay: {missing_in_replay}")
        if extra_in_replay:
            differences.append(f"Extra keys in replay: {extra_in_replay}")

        # Compare common keys
        for key in original_keys & replayed_keys:
            orig_val = original[key]
            replay_val = replayed[key]

            if key == "processed_at":
                # Timestamps will always differ
                continue

            if key == "trace_id":
                # Trace IDs may differ for replays
                continue

            if orig_val != replay_val:
                differences.append(
                    f"Key '{key}': original={json.dumps(orig_val)[:100]} "
                    f"vs replayed={json.dumps(replay_val)[:100]}"
                )

        return {
            "identical": len(differences) == 0,
            "differences": differences,
            "difference_count": len(differences),
        }
