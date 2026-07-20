from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError


PRANA_CONTRACT_REGISTRY_NAME = "prana.event.contracts"


class RegistryReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registry: str
    event_type: str
    version: str


class PranaIngressEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registry_reference: RegistryReference
    submission_id: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)
    timestamp: str = Field(..., min_length=1)
    payload: Dict[str, Any]
    source_system: str = "gurukul"


class IntegrityProbePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int
    status: str
    probe: str
    run_id: Optional[str] = None
    index: Optional[int] = None


class TaskSubmitPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int
    route: str
    user_id: str
    title: str
    source: str
    source_type: str
    content_length: int


class ReviewCompletedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int
    route: str
    user_id: str
    difficulty: str
    next_review_days: int
    confidence: float


class BucketMemorySavedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int
    operation: str
    route: str
    packet_id: str
    user_id: str
    category: str
    cognitive_state: str
    content: Optional[str] = None
    run_id: Optional[str] = None


class TruthClassificationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int
    route: str
    karma_event_type: str
    source: str
    status: str
    classification_input: Optional[str] = None
    classification_action: Optional[str] = None
    classification_result: Optional[str] = None
    run_id: Optional[str] = None


class AdaptiveDecisionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int
    decision_id: str
    user_id: str
    policy_version: str
    input_state: Dict[str, Any]
    output_decision: Dict[str, Any]
    trace_proof: str
    determinism_hash: str
    run_id: Optional[str] = None


@dataclass(frozen=True)
class PranaContractDefinition:
    payload_model: Type[BaseModel]
    versions: List[str]


PRANA_EVENT_CONTRACTS: Dict[str, PranaContractDefinition] = {
    "integrity_probe": PranaContractDefinition(
        payload_model=IntegrityProbePayload,
        versions=["1.0.0"],
    ),
    "task_submit_failed": PranaContractDefinition(
        payload_model=IntegrityProbePayload,
        versions=["1.0.0"],
    ),
    "task_submit": PranaContractDefinition(
        payload_model=TaskSubmitPayload,
        versions=["1.0.0"],
    ),
    "review_completed": PranaContractDefinition(
        payload_model=ReviewCompletedPayload,
        versions=["1.0.0"],
    ),
    "bucket_memory_saved": PranaContractDefinition(
        payload_model=BucketMemorySavedPayload,
        versions=["1.0.0"],
    ),
    "truth_classification": PranaContractDefinition(
        payload_model=TruthClassificationPayload,
        versions=["1.0.0"],
    ),
    "adaptive_decision": PranaContractDefinition(
        payload_model=AdaptiveDecisionPayload,
        versions=["1.0.0"],
    ),
}


class IngressContractViolationError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        reason: str,
        message: str,
        event_type: Optional[str] = None,
        registry_reference: Optional[Dict[str, Any]] = None,
        details: Optional[Any] = None,
        expected_versions: Optional[List[str]] = None,
    ) -> None:
        self.status_code = status_code
        self.reason = reason
        self.message = message
        self.event_type = event_type
        self.registry_reference = registry_reference
        self.details = details
        self.expected_versions = expected_versions or []
        super().__init__(message)

    def to_response(self) -> Dict[str, Any]:
        return {
            "status": "rejected",
            "reason": self.reason,
            "message": self.message,
            "event_type": self.event_type,
            "registry_reference": self.registry_reference,
            "expected_versions": self.expected_versions,
            "details": self.details,
        }


def _format_validation_errors(errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "field": ".".join(str(part) for part in error.get("loc", [])),
            "message": error.get("msg"),
            "type": error.get("type"),
        }
        for error in errors
    ]


def validate_prana_ingress_request(request_body: Dict[str, Any]) -> PranaIngressEnvelope:
    try:
        envelope = TypeAdapter(PranaIngressEnvelope).validate_python(request_body)
    except ValidationError as exc:
        event_type = request_body.get("event_type") if isinstance(request_body, dict) else None
        registry_reference = request_body.get("registry_reference") if isinstance(request_body, dict) else None
        raise IngressContractViolationError(
            status_code=422,
            reason="schema_validation_failed",
            message="Ingress request failed contract envelope validation",
            event_type=event_type,
            registry_reference=registry_reference if isinstance(registry_reference, dict) else None,
            details=_format_validation_errors(exc.errors()),
        ) from exc

    registry_reference = envelope.registry_reference.model_dump()
    if envelope.registry_reference.registry != PRANA_CONTRACT_REGISTRY_NAME:
        raise IngressContractViolationError(
            status_code=422,
            reason="registry_reference_invalid",
            message=f"registry_reference.registry must be '{PRANA_CONTRACT_REGISTRY_NAME}'",
            event_type=envelope.event_type,
            registry_reference=registry_reference,
            details={"received_registry": envelope.registry_reference.registry},
        )

    if envelope.registry_reference.event_type != envelope.event_type:
        raise IngressContractViolationError(
            status_code=422,
            reason="registry_reference_event_mismatch",
            message="registry_reference.event_type must match event_type",
            event_type=envelope.event_type,
            registry_reference=registry_reference,
            details={
                "received_registry_event_type": envelope.registry_reference.event_type,
                "received_event_type": envelope.event_type,
            },
        )

    contract = PRANA_EVENT_CONTRACTS.get(envelope.event_type)
    if contract is None:
        raise IngressContractViolationError(
            status_code=422,
            reason="event_type_not_registered",
            message=f"event_type '{envelope.event_type}' is not registered for PRANA ingress",
            event_type=envelope.event_type,
            registry_reference=registry_reference,
            details={"registered_event_types": sorted(PRANA_EVENT_CONTRACTS.keys())},
        )

    if envelope.registry_reference.version not in contract.versions:
        raise IngressContractViolationError(
            status_code=409,
            reason="version_mismatch",
            message="registry_reference.version does not match the registered contract version",
            event_type=envelope.event_type,
            registry_reference=registry_reference,
            expected_versions=contract.versions,
            details={"received_version": envelope.registry_reference.version},
        )

    try:
        TypeAdapter(contract.payload_model).validate_python(envelope.payload)
    except ValidationError as exc:
        raise IngressContractViolationError(
            status_code=422,
            reason="payload_schema_invalid",
            message="payload does not conform to the registered event contract",
            event_type=envelope.event_type,
            registry_reference=registry_reference,
            details=_format_validation_errors(exc.errors()),
            expected_versions=contract.versions,
        ) from exc

    return envelope
