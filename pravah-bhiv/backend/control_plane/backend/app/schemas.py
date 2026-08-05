
"""Pydantic schemas for the stateless RL-style Decision Brain API."""

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Environment(str, Enum):
    """Supported deployment environments."""

    DEV = "DEV"
    STAGE = "STAGE"
    PROD = "PROD"


class EventType(str, Enum):
    """Supported event classifications used by the decision engine."""

    HIGH_CPU = "HIGH_CPU"
    HIGH_MEMORY = "HIGH_MEMORY"
    LATENCY = "LATENCY"


class HealthResponse(BaseModel):
    """Health response model exposed by the API."""

    status: Literal["healthy"] = "healthy"
    demo_frozen: bool = True
    stateless: bool = True
    success_rate: float = 1.0


class ActionScopeResponse(BaseModel):
    """Environment to action-scope mapping response."""

    DEV: list[str]
    STAGE: list[str]
    PROD: list[str]


class DecisionRequest(BaseModel):
    """Input payload for deterministic decision generation."""

    model_config = ConfigDict(extra="forbid")

    environment: Environment
    event_type: EventType
    cpu: int = Field(ge=0, le=100)
    memory: int = Field(ge=0, le=100)


class DecisionResponse(BaseModel):
    """Decision output returned by the API."""

    decision_id: UUID
    environment: Environment
    selected_action: str
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime
    version: str


class RecentActivityResponse(BaseModel):
    """Container for last ten in-memory decisions."""

    items: list[DecisionResponse]


class DashboardMetric(BaseModel):
    """Generic metric item used across dashboard sections."""

    label: str
    value: str
    tone: str | None = None


class DashboardHeader(BaseModel):
    """Header metadata for the RL Reality dashboard."""

    title: str
    subtitle: str


class LiveDomainStatus(BaseModel):
    """Live status card payload for each monitored domain."""

    name: str
    domain: str
    url: str
    status: str
    health_score: float
    response_time_ms: int
    cpu_percent: float
    memory_percent: float
    uptime_percent: float
    last_action: str
    errors_24h: int


class LiveDashboardResponse(BaseModel):
    """Top-level response model for the real-time Control Plane Dashboard."""

    generated_at: datetime
    environment: str
    system_health: dict
    ml_intelligence: dict
    recent_decisions: list[DecisionResponse]
    monitored_services: list[LiveDomainStatus]


class DecisionDashboardSummary(BaseModel):
    """Aggregated summary for the RL Decision Brain UI."""

    total_decisions: int
    last_action: str
    success_rate: float
    demo_frozen: bool
    stateless: bool
