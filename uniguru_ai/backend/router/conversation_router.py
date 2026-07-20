
from __future__ import annotations

import hashlib
import os
import re
import threading
import time
import uuid
import requests

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from integrations import BucketTelemetryClient, CoreReaderClient, LanguageAdapter, TelemetryEvent, OllamaClient

from service.live_service import LiveUniGuruService
from service.query_classifier import QueryType, classify_query


class QueryRoutingType(str, Enum):
    KNOWLEDGE_QUERY = "KNOWLEDGE_QUERY"
    SYSTEM_QUERY = "SYSTEM_QUERY"
    WORKFLOW_QUERY = "WORKFLOW_QUERY"
    TOOL_QUERY = "TOOL_QUERY"
    GENERAL_LLM_QUERY = "GENERAL_LLM_QUERY"


class RouteTarget(str, Enum):
    ROUTE_ONTOLOGY = "ROUTE_ONTOLOGY"
    ROUTE_WORKFLOW = "ROUTE_WORKFLOW"
    ROUTE_SYSTEM = "ROUTE_SYSTEM"
    ROUTE_REJECT = "ROUTE_REJECT"


_SYSTEM_PATTERNS = (
    r"\bsudo\b",
    r"\brm\s+-",
    r"\bdel\s+",
    r"\bformat\s+",
    r"\bshutdown\b",
    r"\brestart\b",
    r"\bsystemctl\b",
    r"\bpowershell\b",
    r"\bcmd\.exe\b",
)

_WORKFLOW_PATTERNS = (
    r"\bcreate\b.*\b(ticket|task|workflow|incident|approval)\b",
    r"\bupdate\b.*\b(ticket|task|workflow|incident|approval)\b",
    r"\bapprove\b.*\b(request|workflow|task|ticket)\b",
    r"\bschedule\b.*\b(call|meeting|job|workflow|task)\b",
    r"\bstart\b.*\bworkflow\b",
    r"\btrigger\b.*\bworkflow\b",
)

_TOOL_PATTERNS = (
    r"\buse\b.*\btool\b",
    r"\binvoke\b.*\bapi\b",
    r"\bexecute\b.*\bscript\b",
    r"\brun\b.*\b(sql|query|tool)\b",
)

SAFE_FALLBACK_PREFIX = (
    "I am still learning this topic, but here is a basic explanation..."
)


@dataclass(frozen=True)
class RoutingDecision:
    query_type: QueryRoutingType
    route: RouteTarget


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class _LatencyCircuitBreaker:
    def __init__(self, threshold_ms: float, open_seconds: float) -> None:
        self.threshold_ms = threshold_ms
        self.open_seconds = open_seconds
        self._open_until = 0.0
        self._lock = threading.Lock()

    def should_fallback(self) -> bool:
        now = time.monotonic()

        with self._lock:
            return now < self._open_until

    def record_latency(self, latency_ms: float) -> None:
        if latency_ms <= self.threshold_ms:
            return

        with self._lock:
            self._open_until = max(
                self._open_until,
                time.monotonic() + self.open_seconds,
            )


class ConversationRouter:
    def __init__(
        self,
        uniguru_service: Optional[LiveUniGuruService] = None,
        latency_threshold_ms: Optional[float] = None,
        breaker_open_seconds: Optional[float] = None,
    ) -> None:

        self._service = uniguru_service or LiveUniGuruService()

        threshold = latency_threshold_ms or float(
            os.getenv(
                "UNIGURU_ROUTER_LATENCY_THRESHOLD_MS",
                "1200",
            )
        )

        open_seconds = breaker_open_seconds or float(
            os.getenv(
                "UNIGURU_ROUTER_CIRCUIT_OPEN_SECONDS",
                "30",
            )
        )

        self._breaker = _LatencyCircuitBreaker(
            threshold_ms=threshold,
            open_seconds=open_seconds,
        )
        self._ollama = OllamaClient()

    async def route_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Async entry point for routing logic."""
        context_map = dict(context or {})

        query_type = self.classify(
            query=query,
            context=context_map,
        )

        target = self.select_route(query_type=query_type)

        session_id = context_map.get("session_id")

        if target == RouteTarget.ROUTE_SYSTEM:
            response = self._build_system_block_response(
                query_type=query_type,
                session_id=session_id,
            )
        elif target == RouteTarget.ROUTE_WORKFLOW:
            response = self._build_workflow_response(
                query=query,
                query_type=query_type,
                session_id=session_id,
            )
        else:
            response = await self._dispatch_to_uniguru(
                query=query,
                context=context_map,
                query_type=query_type,
            )

        return response

    def classify(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> QueryRoutingType:

        text = query.strip().lower()

        if not text:
            return QueryRoutingType.GENERAL_LLM_QUERY

        if any(re.search(pattern, text) for pattern in _SYSTEM_PATTERNS):
            return QueryRoutingType.SYSTEM_QUERY

        if any(re.search(pattern, text) for pattern in _WORKFLOW_PATTERNS):
            return QueryRoutingType.WORKFLOW_QUERY

        if any(re.search(pattern, text) for pattern in _TOOL_PATTERNS):
            return QueryRoutingType.TOOL_QUERY

        upstream_type = classify_query(text)

        if upstream_type in {
            QueryType.KNOWLEDGE_QUERY,
            QueryType.CONCEPT_QUERY,
            QueryType.EXPLANATION_QUERY,
            QueryType.WEB_LOOKUP,
        }:
            return QueryRoutingType.KNOWLEDGE_QUERY

        return QueryRoutingType.GENERAL_LLM_QUERY

    @staticmethod
    def select_route(query_type: QueryRoutingType) -> RouteTarget:

        if query_type == QueryRoutingType.KNOWLEDGE_QUERY:
            return RouteTarget.ROUTE_ONTOLOGY

        if query_type == QueryRoutingType.SYSTEM_QUERY:
            return RouteTarget.ROUTE_SYSTEM

        if query_type in {
            QueryRoutingType.WORKFLOW_QUERY,
            QueryRoutingType.TOOL_QUERY,
        }:
            return RouteTarget.ROUTE_WORKFLOW

        # IMPORTANT FIX
        return RouteTarget.ROUTE_ONTOLOGY

    async def _dispatch_to_uniguru(
        self,
        query: str,
        context: Dict[str, Any],
        query_type: QueryRoutingType,
    ) -> Dict[str, Any]:

        session_id = context.get("session_id")
        allow_web = bool(context.get("allow_web", False))
        legacy_type = classify_query(query)

        effective_allow_web = (
            allow_web or legacy_type == QueryType.WEB_LOOKUP
        )

        if self._breaker.should_fallback():
            return await self._build_llm_fallback_response(
                query=query,
                query_type=query_type,
                session_id=session_id,
                reason="Latency circuit breaker active",
            )

        try:
            # AWAIT the async ask method
            response = await self._service.ask(
                user_query=query,
                session_id=session_id,
                context=context,
                allow_web_retrieval=effective_allow_web,
            )

        except Exception as exc:
            return await self._build_llm_fallback_response(
                query=query,
                query_type=query_type,
                session_id=session_id,
                reason=f"UniGuru service failed: {str(exc)}",
            )

        return response


    async def _build_llm_fallback_response(
        self,
        query: str,
        query_type: QueryRoutingType,
        session_id: Optional[str],
        reason: str,
    ) -> Dict[str, Any]:
        """
        Attempts to get an answer from Ollama if configured, otherwise returns a rejection.
        """
        if self._ollama.enabled:
            system_prompt = "You are UniGuru, a sovereign AI knowledge assistant. Provide a helpful, concise answer based on general knowledge since no specific verified documents were found."
            answer = self._ollama.generate(query, system_prompt=system_prompt)
            
            if answer:
                return self._build_router_contract_response(
                    decision="answer",
                    answer=answer,
                    reason=f"Ollama fallback active: {reason}",
                    query_type=query_type,
                    route=RouteTarget.ROUTE_ONTOLOGY,
                    verification_status="UNVERIFIED",
                    session_id=session_id,
                    governance_allowed=True,
                    governance_reason="Ollama fallback successful",
                    retrieval_confidence=0.3,
                    ontology_reference={
                        "concept_id": "llm::ollama",
                        "domain": "generative",
                    },
                    source="ollama"
                )

        return self._build_router_contract_response(
            decision="reject",
            answer="I am unable to provide an answer as no verified knowledge was found and local LLM fallback is unavailable.",
            reason=reason,
            query_type=query_type,
            route=RouteTarget.ROUTE_ONTOLOGY,
            verification_status="FAILED",
            session_id=session_id,
            governance_allowed=False,
            governance_reason="LLM fallback disabled or unavailable",
            retrieval_confidence=0.0,
            ontology_reference={
                "concept_id": "none",
                "domain": "none",
            },
            source="none"
        )

    def _build_system_block_response(
        self,
        query_type: QueryRoutingType,
        session_id: Optional[str],
    ) -> Dict[str, Any]:

        return self._build_router_contract_response(
            decision="reject",
            answer="System-level command requests are blocked.",
            reason="System commands are restricted.",
            query_type=query_type,
            route=RouteTarget.ROUTE_SYSTEM,
            verification_status="FAILED",
            session_id=session_id,
            governance_allowed=False,
            governance_reason="System protection enabled.",
        )

    def _build_workflow_response(
        self,
        query: str,
        query_type: QueryRoutingType,
        session_id: Optional[str],
    ) -> Dict[str, Any]:

        return self._build_router_contract_response(
            decision="answer",
            answer=f"Delegated to workflow engine: {query}",
            reason="Workflow routing applied.",
            query_type=query_type,
            route=RouteTarget.ROUTE_WORKFLOW,
            verification_status="VERIFIED",
            session_id=session_id,
            governance_allowed=True,
            governance_reason="Workflow delegation successful.",
        )

    def _build_router_contract_response(
        self,
        decision: str,
        answer: str,
        reason: str,
        query_type: QueryRoutingType,
        route: RouteTarget,
        verification_status: str,
        session_id: Optional[str],
        governance_allowed: bool,
        governance_reason: str,
        retrieval_confidence: float = 0.0,
        ontology_reference: Optional[Dict[str, Any]] = None,
        source: str = "hybrid"
    ) -> Dict[str, Any]:

        return {
            "decision": decision,
            "confidence": round(retrieval_confidence, 2),
            "source": source,
            "answer": answer,
            "reasoning": {
                "query_type": query_type.value,
                "retrieval_method": route.value,
                "validation_status": verification_status
            }
        }


_DEFAULT_ROUTER = ConversationRouter()


def route_query(
    query: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    return _DEFAULT_ROUTER.route_query(
        query=query,
        context=context,
    )
