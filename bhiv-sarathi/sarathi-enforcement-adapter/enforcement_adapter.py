#!/usr/bin/env python3
# NON-RUNTIME REFERENCE — NOT INVOKED BY THE GO SERVICE.
# This file is a historical Python reference port of the PEP design. The live
# Sarathi binary is Go-only; the `--service`, `--live-integration`, and all
# v14.x/v15.x harnesses are implemented in the Go tree and do not spawn Python.
# Keep this file for conceptual reference. Do not rely on it for production.
"""
Sarathi Enforcement Adapter — Policy Enforcement Point (PEP) v1.0
=================================================================

Author: Hemanth B
System: Sarathi Governance Kernel — Enforcement Integration Gate
Host Organization: Blackhole Infiverse (BHIV)
Classification: Internal Sovereign Design / Strictly Confidential

This module implements the non-bypassable enforcement layer for Sarathi.
Every execution in the system MUST pass through this adapter.

Architecture:
    Intent → EnforcementAdapter → SarathiPDP → Verdict → ExecutionEngine

Enforcement Laws:
    1. No execution without PDP decision
    2. No fallback logic — DENY is final
    3. No caching of ALLOW decisions
    4. No retry bypass
    5. No silent success
    6. Every step is cryptographically hash-chained for audit

The EnforcementAdapter is NOT a decision-maker. It is a gate.
It normalizes requests, delegates to PDP, and returns structured verdicts.
It NEVER modifies, interprets, retries, or caches decisions.
"""

import json
import hashlib
import time
import uuid
import copy
import os
import sys
from collections import defaultdict
from typing import Optional, Dict, List, Any, Tuple


# ================================================================
# CRYPTOGRAPHIC UTILITIES
# ================================================================

def sha256hex(data: bytes) -> str:
    """Compute SHA-256 and return hex digest."""
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> str:
    """Produce deterministic canonical JSON for hashing."""
    return json.dumps(obj, separators=(',', ':'), sort_keys=True)


def compute_hash(obj: Any) -> str:
    """Compute SHA-256 of canonical JSON representation."""
    return sha256hex(canonical_json(obj).encode('utf-8'))


# ================================================================
# TRUTH LEVELS — Bell-LaPadula Security Lattice
# ================================================================

TRUTH_LEVELS = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}


# ================================================================
# AUTHORITY RULE
# ================================================================

class AuthorityRule:
    __slots__ = ('rule_id', 'agent_role', 'resource_type', 'action',
                 'classification_max', 'verdict')

    def __init__(self, rule_id, agent_role, resource_type, action,
                 classification_max, verdict):
        self.rule_id = rule_id
        self.agent_role = agent_role
        self.resource_type = resource_type
        self.action = action
        self.classification_max = classification_max
        self.verdict = verdict

    def matches(self, agent_role, resource_type, action):
        return ((self.agent_role == agent_role or self.agent_role == "*") and
                (self.resource_type == resource_type or self.resource_type == "*") and
                (self.action == action or self.action == "*"))


# ================================================================
# POLICY STORE — Immutable, Hash-Verified
# ================================================================

class PolicyStore:
    """Immutable policy container — mirrors Go PolicyStore."""

    def __init__(self, path):
        with open(path) as f:
            matrix = json.load(f)

        self._policy_version = matrix["policy_version"]
        self._frozen_at = matrix.get("frozen_at", "")
        raw_rules = sorted(matrix["rules"], key=lambda r: r["rule_id"])
        self._rules = tuple([
            AuthorityRule(r["rule_id"], r["agent_role"], r["resource_type"],
                          r["action"], r["classification_max"], r["verdict"])
            for r in raw_rules
        ])
        self._resource_classifications = dict(matrix.get("resource_classifications", {}))
        self._policy_hash = self._compute_hash()
        stored_hash = matrix.get("policy_hash", "")
        if stored_hash and stored_hash != self._policy_hash:
            raise ValueError(
                f"POLICY INTEGRITY VIOLATION: stored={stored_hash} computed={self._policy_hash}")
        self._frozen = True

    @property
    def policy_version(self): return self._policy_version
    @property
    def policy_hash(self): return self._policy_hash
    @property
    def frozen_at(self): return self._frozen_at
    @property
    def is_frozen(self): return self._frozen
    def rule_count(self): return len(self._rules)

    @property
    def rules(self):
        return list(self._rules)

    def _compute_hash(self):
        hash_rules = []
        for r in self._rules:
            hash_rules.append({
                "rule_id": r.rule_id, "agent_role": r.agent_role,
                "resource_type": r.resource_type, "action": r.action,
                "classification_max": r.classification_max, "verdict": r.verdict
            })
        return sha256hex(json.dumps(hash_rules, separators=(',', ':')).encode())

    def find_matching_rules(self, agent_role, resource_type, action):
        return [r for r in self._rules if r.matches(agent_role, resource_type, action)]


# ================================================================
# REGISTRY CONFIG + POLICY REGISTRY
# ================================================================

class RegistryConfig:
    def __init__(self, path):
        with open(path) as f:
            config = json.load(f)
        self.active_version = config["active_version"]
        self.policies_dir = config["policies_dir"]

class PolicyRegistry:
    def __init__(self, policies_dir, config=None):
        self._versions = {}
        self._active_version = None
        self._policies_dir = policies_dir
        self._config = config

    def load_policy(self, version):
        path = os.path.join(self._policies_dir, f"policy_{version}.json")
        store = PolicyStore(path)
        self._versions[version] = {"store": store, "lifecycle": "FROZEN"}
        return store

    def set_active(self, version):
        if version not in self._versions:
            raise ValueError(f"Policy version {version!r} not loaded")
        if self._active_version and self._active_version != version:
            self._versions[self._active_version]["lifecycle"] = "DEPRECATED"
        self._versions[version]["lifecycle"] = "ACTIVE"
        self._active_version = version

    def get_active_policy(self):
        if not self._active_version:
            return None
        return self._versions[self._active_version]["store"]

    def get_active_version(self):
        return self._active_version

    def get_policy(self, version):
        entry = self._versions.get(version)
        return entry["store"] if entry else None

    def verify_policy_version(self, version):
        entry = self._versions.get(version)
        if not entry:
            return None, None, False
        store = entry["store"]
        stored = store.policy_hash
        recomputed = store._compute_hash()
        return stored, recomputed, stored == recomputed

    def initialize_from_config(self):
        if not self._config:
            raise ValueError("No config loaded")
        for fname in sorted(os.listdir(self._policies_dir)):
            if fname.startswith("policy_") and fname.endswith(".json"):
                version = fname[len("policy_"):-len(".json")]
                self.load_policy(version)
        self.set_active(self._config.active_version)


# ================================================================
# AGENT & RESOURCE REGISTRIES
# ================================================================

class AgentInfo:
    __slots__ = ('agent_id', 'agent_role', 'classification_max', 'status')
    def __init__(self, agent_id, agent_role, classification_max, status):
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.classification_max = classification_max
        self.status = status

class ResourceInfo:
    __slots__ = ('resource_id', 'resource_type', 'classification')
    def __init__(self, resource_id, resource_type, classification):
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.classification = classification

class AgentResourceRegistry:
    def __init__(self):
        self.agents = {
            "gov-agent-001": AgentInfo("gov-agent-001", "governance_agent", "L4", "ACTIVE"),
            "gov-agent-002": AgentInfo("gov-agent-002", "governance_agent", "L4", "ACTIVE"),
            "std-agent-001": AgentInfo("std-agent-001", "standard_agent", "L2", "ACTIVE"),
            "std-agent-002": AgentInfo("std-agent-002", "standard_agent", "L2", "ACTIVE"),
            "std-agent-003": AgentInfo("std-agent-003", "standard_agent", "L1", "ACTIVE"),
            "audit-agent-001": AgentInfo("audit-agent-001", "audit_agent", "L4", "ACTIVE"),
            "audit-agent-002": AgentInfo("audit-agent-002", "audit_agent", "L4", "ACTIVE"),
            "safety-mon-001": AgentInfo("safety-mon-001", "safety_monitor", "L3", "ACTIVE"),
            "data-proc-001": AgentInfo("data-proc-001", "data_processor", "L1", "ACTIVE"),
            "data-proc-002": AgentInfo("data-proc-002", "data_processor", "L1", "ACTIVE"),
            "orch-001": AgentInfo("orch-001", "orchestrator", "L2", "ACTIVE"),
            "suspended-agent": AgentInfo("suspended-agent", "standard_agent", "L2", "SUSPENDED"),
            "revoked-agent": AgentInfo("revoked-agent", "standard_agent", "L2", "REVOKED"),
            "terminated-agent": AgentInfo("terminated-agent", "standard_agent", "L2", "TERMINATED"),
        }
        self.resources = {
            "policy-reg-001": ResourceInfo("policy-reg-001", "policy_registry", "L4"),
            "policy-reg-002": ResourceInfo("policy-reg-002", "policy_registry", "L4"),
            "agent-reg-001": ResourceInfo("agent-reg-001", "agent_registry", "L3"),
            "trace-001": ResourceInfo("trace-001", "decision_trace", "L3"),
            "trace-002": ResourceInfo("trace-002", "decision_trace", "L3"),
            "model-reg-001": ResourceInfo("model-reg-001", "model_registry", "L3"),
            "audit-log-001": ResourceInfo("audit-log-001", "audit_log", "L3"),
            "config-001": ResourceInfo("config-001", "configuration", "L2"),
            "config-002": ResourceInfo("config-002", "configuration", "L2"),
            "ops-data-001": ResourceInfo("ops-data-001", "operational_data", "L1"),
            "ops-data-002": ResourceInfo("ops-data-002", "operational_data", "L1"),
            "analytics-001": ResourceInfo("analytics-001", "analytics", "L1"),
            "public-api-001": ResourceInfo("public-api-001", "public_api", "L0"),
        }


# ================================================================
# PDP ENGINE — 5-Stage Deterministic Pipeline
# ================================================================

class SarathiPDP:
    """Deterministic PDP engine — mirrors Go implementation.

    IMMUTABILITY CONTRACT:
    - _policy_store is private — no external mutation path.
    - No set/swap/reload methods exist.
    - Created ONLY via from_registry() or for_replay().
    """

    def __init__(self, policy_store, agent_resource_registry, clock_fn):
        self._policy_store = policy_store
        self._registry = agent_resource_registry
        self._clock_fn = clock_fn
        self._frozen = True

    @classmethod
    def from_registry(cls, policy_registry, agent_resource_registry, clock_fn):
        """Production constructor — PDP MUST be created through registry."""
        ps = policy_registry.get_active_policy()
        if ps is None:
            raise RuntimeError("No active policy in registry — cannot create PDP")
        if not ps.is_frozen:
            raise RuntimeError("Active policy is not frozen — governance violation")
        return cls(ps, agent_resource_registry, clock_fn)

    @classmethod
    def for_replay(cls, policy_store, agent_resource_registry, clock_fn):
        """Replay constructor — for historical version verification."""
        return cls(policy_store, agent_resource_registry, clock_fn)

    @property
    def policy_version(self):
        return self._policy_store.policy_version

    @property
    def policy_hash(self):
        return self._policy_store.policy_hash

    def evaluate(self, agent_id, resource_id, action):
        """5-stage deterministic PDP evaluation.

        Returns a PDPResponse dict with full audit trail.
        Every response is stamped with policy_version and policy_hash.
        """
        req = {"agent_id": agent_id, "resource_id": resource_id, "action": action}
        req_json = canonical_json(req)
        request_hash = sha256hex(req_json.encode())

        # Deterministic decision_id = SHA1(request_hash + policy_hash)
        decision_id = str(uuid.uuid5(uuid.NAMESPACE_OID,
                                     request_hash + self._policy_store.policy_hash))
        timestamp = self._clock_fn()

        def emit(verdict, reason, rules, truth_class, agent_role, res_type, stage):
            rule_ids = sorted([r.rule_id for r in rules]) if rules else []
            resp = {
                "decision_id": decision_id,
                "verdict": verdict,
                "policy_version": self._policy_store.policy_version,
                "policy_hash": self._policy_store.policy_hash,
                "determining_rules": rule_ids,
                "truth_classification": truth_class,
                "request_hash": request_hash,
                "timestamp": timestamp,
                "reason": reason,
                "agent_role": agent_role,
                "resource_type": res_type,
                "stage_reached": stage,
            }
            return resp

        class FakeRule:
            def __init__(self, rid):
                self.rule_id = rid

        # STAGE 1: REQUEST VALIDATION
        if not agent_id:
            return emit("DENY", "INVALID_AGENT_ID", None, "UNKNOWN", "UNKNOWN", "UNKNOWN", 1)
        if not resource_id:
            return emit("DENY", "INVALID_RESOURCE_ID", None, "UNKNOWN", "UNKNOWN", "UNKNOWN", 1)
        valid_actions = {"read", "write", "delete", "execute"}
        if action not in valid_actions:
            return emit("DENY", "INVALID_ACTION", None, "UNKNOWN", "UNKNOWN", "UNKNOWN", 1)

        # STAGE 2: REGISTRY LOOKUP
        agent = self._registry.agents.get(agent_id)
        if not agent:
            return emit("DENY", "AGENT_NOT_FOUND", None, "UNKNOWN", "UNKNOWN", "UNKNOWN", 2)
        if agent.status != "ACTIVE":
            return emit("DENY", f"AGENT_{agent.status}", None, "UNKNOWN", agent.agent_role, "UNKNOWN", 2)
        resource = self._registry.resources.get(resource_id)
        if not resource:
            return emit("DENY", "RESOURCE_NOT_FOUND", None, "UNKNOWN", agent.agent_role, "UNKNOWN", 2)

        # STAGE 3: POLICY EVALUATION
        matching = self._policy_store.find_matching_rules(
            agent.agent_role, resource.resource_type, action)

        # STAGE 4: AUTHORITY DECISION
        if not matching:
            return emit("DENY", "NO_MATCHING_RULE", [FakeRule("AUTH-DENY-ALL")],
                        resource.classification, agent.agent_role, resource.resource_type, 4)

        specific = [r for r in matching
                    if r.agent_role != "*" and r.resource_type != "*" and r.action != "*"]
        wildcards = [r for r in matching if r not in specific]
        eval_rules = specific if specific else wildcards

        deny_rules = [r for r in eval_rules if r.verdict == "DENY"]
        allow_rules = [r for r in eval_rules if r.verdict == "ALLOW"]

        if deny_rules:
            return emit("DENY", "EXPLICIT_DENY", deny_rules,
                        resource.classification, agent.agent_role, resource.resource_type, 5)
        if not allow_rules:
            return emit("DENY", "NO_ALLOW_RULE", [FakeRule("AUTH-DENY-ALL")],
                        resource.classification, agent.agent_role, resource.resource_type, 4)

        # Bell-LaPadula classification ceiling
        agent_clear = TRUTH_LEVELS.get(agent.classification_max, 0)
        res_level = TRUTH_LEVELS.get(resource.classification, 0)
        if agent_clear < res_level:
            return emit("DENY", "CLASSIFICATION_CEILING_EXCEEDED", allow_rules,
                        resource.classification, agent.agent_role, resource.resource_type, 5)
        for rule in allow_rules:
            rule_ceil = TRUTH_LEVELS.get(rule.classification_max, 0)
            if rule_ceil < res_level:
                return emit("DENY", "RULE_CLASSIFICATION_CEILING_EXCEEDED", [rule],
                            resource.classification, agent.agent_role, resource.resource_type, 5)

        # STAGE 5: ALLOW
        return emit("ALLOW", "EXPLICIT_ALLOW", allow_rules,
                    resource.classification, agent.agent_role, resource.resource_type, 5)


# ================================================================
# EXECUTION REQUEST — Structured, Validated, Hash-Bound
# ================================================================

class ExecutionRequest:
    """Immutable execution request — the single entry point for all execution intents.

    VALIDATION RULES (pre-PDP):
    - agent_id: required, non-empty string
    - resource_id: required, non-empty string
    - action: required, must be one of {read, write, delete, execute}
    - correlation_id: required, non-empty UUID string
    - policy_version: optional, if provided must match active registry version

    HASH BINDING:
    - request_hash is computed on construction from canonical fields
    - request_hash is immutable — any modification is detectable
    """

    VALID_ACTIONS = frozenset({"read", "write", "delete", "execute"})

    def __init__(self, agent_id: str, resource_id: str, action: str,
                 correlation_id: str, policy_version: Optional[str] = None):
        # Store raw values
        self._agent_id = agent_id if agent_id else ""
        self._resource_id = resource_id if resource_id else ""
        self._action = action if action else ""
        self._correlation_id = correlation_id if correlation_id else ""
        self._policy_version = policy_version if policy_version else ""
        import datetime
        self._created_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # Compute request hash — binds this request immutably
        self._request_hash = self._compute_hash()

        # Validate
        self._validation_errors = self._validate()
        self._is_valid = len(self._validation_errors) == 0

    def _compute_hash(self) -> str:
        """SHA-256 of canonical request fields — immutable after construction."""
        payload = {
            "agent_id": self._agent_id,
            "resource_id": self._resource_id,
            "action": self._action,
            "correlation_id": self._correlation_id,
            "policy_version": self._policy_version,
        }
        return compute_hash(payload)

    def _validate(self) -> List[str]:
        """Pre-PDP validation — structural checks only."""
        errors = []
        if not self._agent_id:
            errors.append("MISSING_AGENT_ID")
        if not self._resource_id:
            errors.append("MISSING_RESOURCE_ID")
        if not self._action:
            errors.append("MISSING_ACTION")
        elif self._action not in self.VALID_ACTIONS:
            errors.append(f"INVALID_ACTION:{self._action}")
        if not self._correlation_id:
            errors.append("MISSING_CORRELATION_ID")
        return errors

    # --- Read-only accessors ---
    @property
    def agent_id(self): return self._agent_id
    @property
    def resource_id(self): return self._resource_id
    @property
    def action(self): return self._action
    @property
    def correlation_id(self): return self._correlation_id
    @property
    def policy_version(self): return self._policy_version
    @property
    def request_hash(self): return self._request_hash
    @property
    def is_valid(self): return self._is_valid
    @property
    def validation_errors(self): return list(self._validation_errors)
    @property
    def created_at(self): return self._created_at

    def to_dict(self) -> dict:
        return {
            "agent_id": self._agent_id,
            "resource_id": self._resource_id,
            "action": self._action,
            "correlation_id": self._correlation_id,
            "policy_version": self._policy_version,
            "request_hash": self._request_hash,
            "created_at": self._created_at,
            "is_valid": self._is_valid,
            "validation_errors": self._validation_errors,
        }


# ================================================================
# EXECUTION RESPONSE — Hash-Chained, Immutable Decision Record
# ================================================================

class ExecutionResponse:
    """Immutable execution response — the ONLY thing the ExecutionEngine accepts.

    ENFORCEMENT LAWS:
    - verdict can only be ALLOW, DENY, or ESCALATE
    - ALLOW requires a valid decision_id from PDP
    - DENY is final — no retry, no override
    - ESCALATE means human review required — execution halted
    - response_hash chains: request_hash → pdp_decision_hash → enforcement_hash
    - Any break in the hash chain = DENY
    """

    VALID_VERDICTS = frozenset({"ALLOW", "DENY", "ESCALATE"})

    def __init__(self, execution_request: ExecutionRequest,
                 pdp_response: Optional[dict],
                 enforcement_stage: str,
                 enforcement_reason: str):
        self._correlation_id = execution_request.correlation_id
        self._request_hash = execution_request.request_hash
        self._enforcement_stage = enforcement_stage
        self._enforcement_reason = enforcement_reason

        if pdp_response:
            self._verdict = pdp_response["verdict"]
            self._decision_id = pdp_response["decision_id"]
            self._policy_version = pdp_response["policy_version"]
            self._policy_hash = pdp_response["policy_hash"]
            self._pdp_reason = pdp_response["reason"]
            self._determining_rules = pdp_response["determining_rules"]
            self._truth_classification = pdp_response["truth_classification"]
            self._pdp_request_hash = pdp_response["request_hash"]
            self._agent_role = pdp_response["agent_role"]
            self._resource_type = pdp_response["resource_type"]
            self._stage_reached = pdp_response["stage_reached"]
            self._pdp_timestamp = pdp_response["timestamp"]
            # Compute PDP decision hash for chain verification
            self._pdp_decision_hash = compute_hash(pdp_response)
        else:
            # Pre-PDP rejection (validation failure)
            self._verdict = "DENY"
            self._decision_id = ""
            self._policy_version = ""
            self._policy_hash = ""
            self._pdp_reason = ""
            self._determining_rules = []
            self._truth_classification = "UNKNOWN"
            self._pdp_request_hash = ""
            self._agent_role = "UNKNOWN"
            self._resource_type = "UNKNOWN"
            self._stage_reached = 0
            self._pdp_timestamp = ""
            self._pdp_decision_hash = "NO_PDP_EVALUATION"

        # Enforcement nonce — unique per evaluation, prevents replay confusion.
        # Even if two evaluations have identical inputs and identical PDP outputs,
        # the enforcement_hash will differ because the nonce is a fresh UUID4.
        # This is the enforcement layer's anti-replay mechanism.
        self._enforcement_nonce = str(uuid.uuid4())

        # Compute enforcement hash — chains request → PDP → enforcement
        self._enforcement_hash = self._compute_enforcement_hash()
        import datetime
        self._enforced_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def _compute_enforcement_hash(self) -> str:
        """SHA-256 chain: request_hash + pdp_decision_hash + enforcement metadata.

        CRITICAL: Includes enforcement_nonce (UUID4) to ensure every enforcement
        evaluation produces a unique hash, even for identical requests with
        identical PDP outcomes. This is the enforcement layer's primary defense
        against replay attacks. The PDP is intentionally deterministic (same
        inputs → same outputs for replay verification), but the enforcement
        layer must distinguish every individual evaluation. The nonce ensures
        that replayed requests get different enforcement_hashes, making them
        distinguishable in the audit chain.
        """
        chain_payload = {
            "request_hash": self._request_hash,
            "pdp_decision_hash": self._pdp_decision_hash,
            "verdict": self._verdict,
            "enforcement_stage": self._enforcement_stage,
            "enforcement_reason": self._enforcement_reason,
            "correlation_id": self._correlation_id,
            "decision_id": self._decision_id,
            "enforcement_nonce": self._enforcement_nonce,
        }
        return compute_hash(chain_payload)

    # --- Read-only accessors ---
    @property
    def verdict(self): return self._verdict
    @property
    def decision_id(self): return self._decision_id
    @property
    def correlation_id(self): return self._correlation_id
    @property
    def policy_version(self): return self._policy_version
    @property
    def policy_hash(self): return self._policy_hash
    @property
    def request_hash(self): return self._request_hash
    @property
    def enforcement_hash(self): return self._enforcement_hash
    @property
    def pdp_decision_hash(self): return self._pdp_decision_hash
    @property
    def enforcement_stage(self): return self._enforcement_stage
    @property
    def enforcement_reason(self): return self._enforcement_reason
    @property
    def pdp_reason(self): return self._pdp_reason
    @property
    def determining_rules(self): return list(self._determining_rules)
    @property
    def truth_classification(self): return self._truth_classification
    @property
    def agent_role(self): return self._agent_role
    @property
    def resource_type(self): return self._resource_type
    @property
    def stage_reached(self): return self._stage_reached
    @property
    def enforcement_nonce(self): return self._enforcement_nonce

    def to_dict(self) -> dict:
        return {
            "correlation_id": self._correlation_id,
            "verdict": self._verdict,
            "decision_id": self._decision_id,
            "policy_version": self._policy_version,
            "policy_hash": self._policy_hash,
            "request_hash": self._request_hash,
            "pdp_decision_hash": self._pdp_decision_hash,
            "enforcement_hash": self._enforcement_hash,
            "enforcement_nonce": self._enforcement_nonce,
            "enforcement_stage": self._enforcement_stage,
            "enforcement_reason": self._enforcement_reason,
            "pdp_reason": self._pdp_reason,
            "determining_rules": self._determining_rules,
            "truth_classification": self._truth_classification,
            "agent_role": self._agent_role,
            "resource_type": self._resource_type,
            "stage_reached": self._stage_reached,
            "enforced_at": self._enforced_at,
        }


# ================================================================
# ENFORCEMENT ADAPTER — The Non-Bypassable Gate
# ================================================================

class EnforcementAdapter:
    """Policy Enforcement Point (PEP) — the single gate for all execution.

    ENFORCEMENT CONTRACT:
    1. Every execution intent MUST pass through enforce().
    2. enforce() validates the request BEFORE calling PDP.
    3. enforce() calls PDP and returns the verdict WITHOUT modification.
    4. enforce() NEVER retries, caches, or interprets decisions.
    5. enforce() maintains a hash-chained audit trail.
    6. The adapter is stateless — no request memory, no decision cache.
    7. Policy version mismatch → DENY (no fallback to different version).

    WHAT THE ADAPTER DOES:
    - Validates ExecutionRequest structure
    - Verifies policy version matches active registry version (if specified)
    - Delegates to SarathiPDP.evaluate()
    - Wraps PDPResponse in ExecutionResponse
    - Maintains enforcement trace chain

    WHAT THE ADAPTER DOES NOT:
    - Modify PDP decisions
    - Retry failed evaluations
    - Cache ALLOW decisions
    - Fall back to alternate policies
    - Interpret or enrich verdicts
    - Silently succeed on any path
    """

    def __init__(self, pdp: SarathiPDP, policy_registry: PolicyRegistry):
        self._pdp = pdp
        self._policy_registry = policy_registry
        self._enforcement_count = 0
        self._prev_enforcement_hash = "GENESIS"  # Chain anchor
        self._enforcement_chain = []  # Append-only trace

    def enforce(self, request: ExecutionRequest) -> ExecutionResponse:
        """The ONLY entry point for execution authorization.

        Flow:
        1. Pre-PDP validation (structural checks)
        2. Policy version verification (if specified)
        3. PDP evaluation
        4. Response construction with hash chain
        5. Enforcement trace recording

        Returns ExecutionResponse — the ONLY thing the ExecutionEngine accepts.
        """
        self._enforcement_count += 1

        # STEP 1: Pre-PDP validation
        if not request.is_valid:
            resp = ExecutionResponse(
                execution_request=request,
                pdp_response=None,
                enforcement_stage="PRE_PDP_VALIDATION",
                enforcement_reason=f"VALIDATION_FAILED:{','.join(request.validation_errors)}"
            )
            self._record_trace(request, resp)
            return resp

        # STEP 2: Policy version verification
        # If the request specifies a policy version, it MUST match the active version.
        # No fallback — mismatch is a hard DENY.
        if request.policy_version:
            active_version = self._policy_registry.get_active_version()
            active_policy = self._policy_registry.get_active_policy()
            if request.policy_version != active_policy.policy_version:
                resp = ExecutionResponse(
                    execution_request=request,
                    pdp_response=None,
                    enforcement_stage="POLICY_VERSION_CHECK",
                    enforcement_reason=f"POLICY_VERSION_MISMATCH:requested={request.policy_version},active={active_policy.policy_version}"
                )
                self._record_trace(request, resp)
                return resp

        # STEP 3: PDP evaluation — the ONLY decision path
        pdp_response = self._pdp.evaluate(
            agent_id=request.agent_id,
            resource_id=request.resource_id,
            action=request.action
        )

        # STEP 4: Verify PDP response integrity
        # The PDP response must contain a valid decision_id and policy_hash
        if not pdp_response.get("decision_id"):
            resp = ExecutionResponse(
                execution_request=request,
                pdp_response=None,
                enforcement_stage="PDP_RESPONSE_VALIDATION",
                enforcement_reason="PDP_RESPONSE_MISSING_DECISION_ID"
            )
            self._record_trace(request, resp)
            return resp

        if not pdp_response.get("policy_hash"):
            resp = ExecutionResponse(
                execution_request=request,
                pdp_response=None,
                enforcement_stage="PDP_RESPONSE_VALIDATION",
                enforcement_reason="PDP_RESPONSE_MISSING_POLICY_HASH"
            )
            self._record_trace(request, resp)
            return resp

        # STEP 5: Verify request hash binding — PDP must have evaluated the same request
        pdp_req_hash = pdp_response.get("request_hash", "")
        expected_pdp_req = compute_hash({
            "agent_id": request.agent_id,
            "resource_id": request.resource_id,
            "action": request.action,
        })
        if pdp_req_hash != expected_pdp_req:
            resp = ExecutionResponse(
                execution_request=request,
                pdp_response=None,
                enforcement_stage="REQUEST_HASH_BINDING",
                enforcement_reason=f"REQUEST_HASH_MISMATCH:expected={expected_pdp_req[:16]},got={pdp_req_hash[:16]}"
            )
            self._record_trace(request, resp)
            return resp

        # STEP 6: Construct enforcement response — NO modification of verdict
        resp = ExecutionResponse(
            execution_request=request,
            pdp_response=pdp_response,
            enforcement_stage="PDP_EVALUATED",
            enforcement_reason=pdp_response["reason"]
        )

        self._record_trace(request, resp)
        return resp

    def _record_trace(self, request: ExecutionRequest, response: ExecutionResponse):
        """Append-only enforcement trace with hash chaining."""
        trace_entry = {
            "sequence": self._enforcement_count,
            "correlation_id": request.correlation_id,
            "request_hash": request.request_hash,
            "enforcement_hash": response.enforcement_hash,
            "pdp_decision_hash": response.pdp_decision_hash,
            "verdict": response.verdict,
            "enforcement_stage": response.enforcement_stage,
            "enforcement_reason": response.enforcement_reason,
            "policy_version": response.policy_version,
            "policy_hash": response.policy_hash,
            "prev_enforcement_hash": self._prev_enforcement_hash,
        }
        # Chain hash: previous + current
        chain_payload = canonical_json({
            "prev": self._prev_enforcement_hash,
            "current": response.enforcement_hash,
            "sequence": self._enforcement_count,
        })
        trace_entry["trace_hash"] = sha256hex(chain_payload.encode())

        self._prev_enforcement_hash = trace_entry["trace_hash"]
        self._enforcement_chain.append(trace_entry)

    def get_enforcement_chain(self) -> List[dict]:
        """Return a defensive copy of the enforcement chain."""
        return [dict(e) for e in self._enforcement_chain]

    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        """Verify the integrity of the enforcement hash chain."""
        expected_prev = "GENESIS"
        for i, entry in enumerate(self._enforcement_chain):
            if entry["prev_enforcement_hash"] != expected_prev:
                return False, f"Chain break at index {i}: expected prev={expected_prev}, got={entry['prev_enforcement_hash']}"
            # Recompute chain hash
            chain_payload = canonical_json({
                "prev": entry["prev_enforcement_hash"],
                "current": entry["enforcement_hash"],
                "sequence": entry["sequence"],
            })
            recomputed = sha256hex(chain_payload.encode())
            if entry["trace_hash"] != recomputed:
                return False, f"Hash mismatch at index {i}: stored={entry['trace_hash']}, recomputed={recomputed}"
            expected_prev = entry["trace_hash"]
        return True, None

    @property
    def enforcement_count(self):
        return self._enforcement_count


# ================================================================
# EXECUTION ENGINE — The Final Gate
# ================================================================

class ExecutionEngine:
    """Simulated execution engine — the ONLY consumer of EnforcementAdapter output.

    EXECUTION LAWS:
    1. ExecutionEngine ONLY accepts ExecutionResponse objects.
    2. ALLOW → EXECUTION_PERMITTED (simulated)
    3. DENY → EXECUTION_BLOCKED
    4. ESCALATE → EXECUTION_HALTED (human review required)
    5. No alternate path exists.
    6. Every execution attempt is logged with hash verification.
    7. ExecutionEngine verifies the enforcement_hash before proceeding.
    """

    def __init__(self):
        self._execution_log = []
        self._execution_count = 0
        self._prev_execution_hash = "GENESIS"

    def attempt_execution(self, response: ExecutionResponse) -> dict:
        """The ONLY way to execute — through a verified ExecutionResponse.

        Returns an execution trace record.
        """
        self._execution_count += 1

        # INVARIANT: Every execution must have a valid enforcement_hash
        if not response.enforcement_hash:
            outcome = self._create_outcome(
                response, "EXECUTION_BLOCKED",
                "MISSING_ENFORCEMENT_HASH", False)
            self._log(outcome)
            return outcome

        # INVARIANT: Every execution must have a valid correlation_id
        if not response.correlation_id:
            outcome = self._create_outcome(
                response, "EXECUTION_BLOCKED",
                "MISSING_CORRELATION_ID", False)
            self._log(outcome)
            return outcome

        # INVARIANT: ALLOW requires a valid decision_id from PDP
        if response.verdict == "ALLOW":
            if not response.decision_id:
                outcome = self._create_outcome(
                    response, "EXECUTION_BLOCKED",
                    "ALLOW_WITHOUT_DECISION_ID", False)
                self._log(outcome)
                return outcome

            # INVARIANT: ALLOW requires matching policy_hash
            if not response.policy_hash:
                outcome = self._create_outcome(
                    response, "EXECUTION_BLOCKED",
                    "ALLOW_WITHOUT_POLICY_HASH", False)
                self._log(outcome)
                return outcome

            # EXECUTION PERMITTED
            outcome = self._create_outcome(
                response, "EXECUTION_PERMITTED",
                "AUTHORIZED_BY_PDP", True)
            self._log(outcome)
            return outcome

        elif response.verdict == "DENY":
            outcome = self._create_outcome(
                response, "EXECUTION_BLOCKED",
                response.enforcement_reason, False)
            self._log(outcome)
            return outcome

        elif response.verdict == "ESCALATE":
            outcome = self._create_outcome(
                response, "EXECUTION_HALTED",
                "HUMAN_REVIEW_REQUIRED", False)
            self._log(outcome)
            return outcome

        else:
            # Unknown verdict — fail closed
            outcome = self._create_outcome(
                response, "EXECUTION_BLOCKED",
                f"UNKNOWN_VERDICT:{response.verdict}", False)
            self._log(outcome)
            return outcome

    def _create_outcome(self, response: ExecutionResponse,
                        execution_state: str, execution_reason: str,
                        executed: bool) -> dict:
        outcome = {
            "execution_sequence": self._execution_count,
            "correlation_id": response.correlation_id,
            "verdict": response.verdict,
            "execution_state": execution_state,
            "execution_reason": execution_reason,
            "executed": executed,
            "decision_id": response.decision_id,
            "policy_version": response.policy_version,
            "policy_hash": response.policy_hash,
            "request_hash": response.request_hash,
            "enforcement_hash": response.enforcement_hash,
            "pdp_decision_hash": response.pdp_decision_hash,
            "enforcement_stage": response.enforcement_stage,
            "pdp_reason": response.pdp_reason,
            "determining_rules": response.determining_rules,
            "truth_classification": response.truth_classification,
            "agent_role": response.agent_role,
            "resource_type": response.resource_type,
            "stage_reached": response.stage_reached,
            "prev_execution_hash": self._prev_execution_hash,
        }
        # Compute execution hash for chain
        outcome["execution_hash"] = compute_hash(outcome)
        return outcome

    def _log(self, outcome: dict):
        self._prev_execution_hash = outcome["execution_hash"]
        self._execution_log.append(outcome)

    def get_execution_log(self) -> List[dict]:
        return [dict(e) for e in self._execution_log]

    def verify_execution_chain(self) -> Tuple[bool, Optional[str]]:
        """Verify the execution hash chain integrity."""
        expected_prev = "GENESIS"
        for i, entry in enumerate(self._execution_log):
            if entry["prev_execution_hash"] != expected_prev:
                return False, f"Execution chain break at index {i}"
            # Recompute
            verify = dict(entry)
            stored_hash = verify.pop("execution_hash")
            recomputed = compute_hash(verify)
            if stored_hash != recomputed:
                return False, f"Execution hash mismatch at index {i}"
            expected_prev = stored_hash
        return True, None

    @property
    def execution_count(self):
        return self._execution_count


# ================================================================
# FULL ENFORCEMENT PIPELINE — Intent → Adapter → PDP → Engine
# ================================================================

class SarathiEnforcementPipeline:
    """Complete enforcement pipeline — the system law.

    This class binds the registry, PDP, adapter, and engine together.
    It provides the ONLY authorized path for execution.

    PIPELINE:
    1. Load and verify policies from registry
    2. Create PDP from registry (not direct file load)
    3. Create enforcement adapter bound to PDP + registry
    4. Create execution engine
    5. Every intent → enforce() → attempt_execution()
    """

    def __init__(self, policies_dir: str, config_path: str):
        # Load registry from config
        config = RegistryConfig(config_path)
        self._registry = PolicyRegistry(policies_dir, config)
        self._registry.initialize_from_config()

        # Create agent/resource registry
        self._agent_registry = AgentResourceRegistry()

        # Deterministic clock for reproducibility
        self._clock_fn = lambda: "2026-03-17T00:00:00.000000Z"

        # Create PDP from registry — the ONLY production path
        self._pdp = SarathiPDP.from_registry(
            self._registry, self._agent_registry, self._clock_fn)

        # Create enforcement adapter
        self._adapter = EnforcementAdapter(self._pdp, self._registry)

        # Create execution engine
        self._engine = ExecutionEngine()

    def execute(self, agent_id: str, resource_id: str, action: str,
                correlation_id: str = "",
                policy_version: str = "") -> dict:
        """The SINGLE authorized path for execution.

        Returns a complete execution trace with full hash chain.
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Step 1: Create execution request
        request = ExecutionRequest(
            agent_id=agent_id,
            resource_id=resource_id,
            action=action,
            correlation_id=correlation_id,
            policy_version=policy_version,
        )

        # Step 2: Enforce through adapter → PDP
        enforcement_response = self._adapter.enforce(request)

        # Step 3: Attempt execution through engine
        execution_outcome = self._engine.attempt_execution(enforcement_response)

        # Step 4: Return complete trace
        return {
            "request": request.to_dict(),
            "enforcement": enforcement_response.to_dict(),
            "execution": execution_outcome,
        }

    @property
    def adapter(self): return self._adapter
    @property
    def engine(self): return self._engine
    @property
    def registry(self): return self._registry
    @property
    def pdp(self): return self._pdp
