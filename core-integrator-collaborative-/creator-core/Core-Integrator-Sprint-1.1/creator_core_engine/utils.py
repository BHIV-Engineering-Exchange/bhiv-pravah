import hashlib
import json
import uuid
from typing import Any

from pydantic import BaseModel

SCHEMA_VERSION = "1.0"


def normalize_for_canonical_json(value: Any) -> Any:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", exclude_none=True)

    if isinstance(value, dict):
        return {
            key: normalize_for_canonical_json(value[key])
            for key in sorted(value)
        }

    if isinstance(value, (list, tuple)):
        return [normalize_for_canonical_json(item) for item in value]

    return value


def canonical_json(value: Any) -> str:
    normalized = normalize_for_canonical_json(value)
    return json.dumps(normalized, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def sha256_hex(value: Any) -> str:
    payload = value if isinstance(value, str) else canonical_json(value)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_instruction_id(instruction: Any) -> str:
    return str(uuid.uuid4())


def build_artifact_hash(payload: Any) -> str:
    return sha256_hex(payload)


def build_creative_session_id(instruction_id: str) -> str:
    return f"session_{instruction_id[4:20]}"


def build_project_id(module: str) -> str:
    return f"creator_core::{module}"