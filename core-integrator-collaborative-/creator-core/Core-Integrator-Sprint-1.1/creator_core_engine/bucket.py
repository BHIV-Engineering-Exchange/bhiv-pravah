import json
from pathlib import Path
from typing import Optional

from .models import ArtifactRecord, BlueprintEnvelope
from .utils import build_artifact_hash


class LocalBucketStore:
    def __init__(self, base_dir: str = "db/creator_core_bucket"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def store_blueprint(
        self,
        envelope: BlueprintEnvelope,
        parent_hash: Optional[str] = None,
    ) -> ArtifactRecord:
        payload = envelope.model_dump(mode="json", exclude_none=True)
        artifact_hash = build_artifact_hash(payload)
        artifact = ArtifactRecord(
            artifact_hash=artifact_hash,
            parent_hash=parent_hash,
            payload=payload,
        )

        artifact_path = self.base_dir / f"{artifact_hash}.json"
        if not artifact_path.exists():
            with artifact_path.open("w", encoding="utf-8") as handle:
                json.dump(artifact.model_dump(mode="json", exclude_none=True), handle, ensure_ascii=True, sort_keys=True, separators=(",", ":"))

        return artifact