# System Architecture Guide

## Overview

This guide documents the architecture of the BHIV Core-Integrator system and the roles of each major component.
The architecture is intentionally modular: each component owns a bounded responsibility, communicates over HTTP, and writes artifacts into a centralized bucket.

## Components

### Prompt Runner

**Location:** `prompt-runner01/run_server.py`

**What it owns**
- Receiving a user prompt
- Converting prompts into structured instruction payloads
- Responding to `/generate` and `/health` requests

**What it does NOT own**
- Blueprint creation
- Execution logic
- Artifact storage beyond its own instruction payload

**What can influence it**
- User prompt quality and context
- Request schema expected by `integration_bridge.py`

**What it can influence**
- The instruction structure passed to Creator Core
- The overall pipeline trace ID and artifact lineage

**Execution rights**
- Reads incoming prompts from HTTP POST
- Writes instruction payloads to the pipeline

**Authority rights**
- No authority enforcement is implemented today

**Constitutional boundaries**
- Must not bypass Creator Core or BHIV Core
- Must not generate artifacts directly into Bucket without the bridge

**Notes**
- The current prompt runner is a stub echo server. It is a placeholder, not a production prompt processor.

---

### Creator Core

**Location:** `creator-core/Core-Integrator-Sprint-1.1/main.py`

**What it owns**
- Receiving prompt instructions
- Generating blueprint envelopes from instructions
- Storing blueprint artifacts in the local Creator Core bucket store
- Emitting telemetry through InsightFlow

**What it does NOT own**
- Direct execution of blueprints
- Final result assembly
- Trace-level replay beyond its own artifact persistence

**What can influence it**
- Instruction payload validation in `creator_core_engine/service.py`
- Module-to-blueprint mapping in `creator_core_engine/generator.py`
- Local bucket storage available in `creator_core_engine/bucket.py`

**What it can influence**
- Blueprint shape, product target, and payload content
- Metadata used by BHIV Core and Integration Bridge
- Telemetry emitted to InsightFlow

**Execution rights**
- Accepts HTTP requests at `/creator-core/generate-blueprint`
- Creates `BlueprintEnvelope` objects and stores them

**Authority rights**
- Validates incoming instructions against `PromptRunnerInstruction`
- Emits telemetry events for each generation

**Constitutional boundaries**
- Must not execute blueprints directly
- Must not accept arbitrary schemas outside `PromptRunnerInstruction`
- Must not bypass artifact storage when generating blueprints

---

### BHIV Core

**Location:** `main.py`

**What it owns**
- Central execution gateway for the platform
- Module routing and intent handling
- Security validation for incoming user requests
- Context and history storage via `db/context.db`
- Replay endpoints under `/replay`

**What it does NOT own**
- Prompt-to-instruction conversion
- Blueprint creation
- Artifact storage in BHIV Bucket

**What can influence it**
- Config validation in `config/config.py`
- Runtime feature flags (`SSPL_ENABLED`, `INTEGRATOR_USE_NOOPUR`, `DISABLE_VIDEO_SERVICE`)
- Module handlers in `src/core/gateway.py`

**What it can influence**
- Final execution output returned to Integration Bridge or external clients
- Replay validation status and deterministic proof
- Internal memory and user session history

**Execution rights**
- Listens on `/core` and `/system/*`
- Performs security and response sanitization

**Authority rights**
- Gatekeeper for replay endpoints and diagnostics
- Enforces request-level validation through security middleware

**Constitutional boundaries**
- Should not accept instructions without valid user identity
- Should only execute in the configured runtime mode
- Must not expose raw internal system state outside diagnostics

---

### CET (Constitutional Execution Translator)

**Location:** represented in `full_tantra_flow_test.py`

**What it owns**
- The conceptual contract generation stage between blueprint and execution
- Deterministic execution plan creation
- Replay-safe contract formation

**What it does NOT own**
- Actual service deployment in this repo
- Independent API surface outside the validation harness

**What can influence it**
- Blueprint payload structure
- Contract validation rules in the test harness

**What it can influence**
- Contract hash and replay safety metadata
- Authority validation decisions downstream

**Execution rights**
- Only exists in the simulation / validation layer today

**Authority rights**
- No live authority rights outside `full_tantra_flow_test.py`

**Constitutional boundaries**
- Must not be bypassed by direct execution tests
- Must remain deterministic and replay-safe

---

### Sarathi Authority Layer

**Location:** represented in `full_tantra_flow_test.py`

**What it owns**
- Validation of contract structure and authority claims
- Decisioning for whether a contract is valid and allowed

**What it does NOT own**
- Service process or API endpoint deployment
- Artifact storage or execution logic

**What can influence it**
- Contract payload fields such as `contract_id`, `trace_id`, `execution_plan` and constraints

**What it can influence**
- Gate decision outcomes
- Authority and audit metadata

**Execution rights**
- Only executed within the end-to-end test harness

**Authority rights**
- Simulated approval/rejection for pipeline flows

**Constitutional boundaries**
- Must keep validation checks strict and explicit
- Should not accept invalid or malformed contract payloads

---

### Execution Gate

**Location:** represented in `full_tantra_flow_test.py`

**What it owns**
- Interpretation of authority output into execution readiness
- Gate-level pass/fail decisions before execution

**What it does NOT own**
- Execution engine internals
- Artifact persistence beyond the test harness

**What can influence it**
- Sarathi decisions
- Contract constraints and execution plan details

**What it can influence**
- Whether the system moves to execution or rejects the request

**Execution rights**
- Simulated gating logic during validation

**Authority rights**
- Must only allow execution when authority checks pass

**Constitutional boundaries**
- Should reject flows with missing or inconsistent metadata

---

### Bucket

**Location:** `bhiv_bucket.py`

**What it owns**
- Append-only artifact storage for artifacts: instruction, blueprint, execution, result
- Trace index management for `trace_id` → artifact chain
- Artifact retrieval by ID and by trace
- Bucket stats and trace listing

**What it does NOT own**
- Artifact interpretation
- Artifact transformation or reconstruction logic
- Execution semantics

**What can influence it**
- Artifact IDs and trace IDs produced by upstream services
- Schema version metadata embedded in each stored record

**What it can influence**
- Replay and reconstruction capabilities
- Trace continuity and audit history

**Execution rights**
- Accepts bucket API calls at `/bucket/store`, `/bucket/artifact/{artifact_id}`, `/bucket/trace/{trace_id}`, and `/bucket/stats`

**Authority rights**
- Data storage only; no policy enforcement

**Constitutional boundaries**
- Must remain append-only
- Must not modify existing artifacts after creation
- Must keep trace indices consistent

---

### InsightFlow

**Location:** `creator-core/Core-Integrator-Sprint-1.1/creator_core_engine/telemetry.py`

**What it owns**
- Telemetry emission for Creator Core events
- Recording event payloads to `db/creator_core_telemetry/insightflow_events.jsonl`

**What it does NOT own**
- Business logic for blueprint creation
- Artifact storage
- Replay logic

**What can influence it**
- Creator Core event lifecycle and instruction metadata

**What it can influence**
- Observability and audit trace of Creator Core operations
- InsightFlow analytics and proof generation

**Execution rights**
- Emits local telemetry events

**Authority rights**
- No enforcement authority

**Constitutional boundaries**
- Must not store sensitive secrets in telemetry payloads
- Must only log events related to Creator Core processing

---

### Replay System

**Location:** `integration_bridge.py`, `main.py` (core replay endpoints), `full_tantra_flow_test.py`

**What it owns**
- Trace-level replay via bucket retrieval
- Deterministic hash proof generation
- Core-level instruction replay

**What it does NOT own**
- Independent distributed replay validator process (not deployed)
- Automatic artifact reconstruction beyond stored data

**What can influence it**
- Artifact chain completeness in Bucket
- Deterministic hash computation method

**What it can influence**
- Audit confidence in pipeline reproducibility
- Replay result validation for instruction and trace IDs

**Execution rights**
- Accepts replay requests via `/pipeline/replay/{trace_id}` and `/replay/{instruction_id}`

**Authority rights**
- Provides evidence, not authorization

**Constitutional boundaries**
- Must not claim full deterministic proof if artifacts are missing
- Must provide a precise error when replay cannot be completed

---

### Integration Bridge

**Location:** `integration_bridge.py`

**What it owns**
- Orchestrating the full pipeline from prompt to final result
- Calling Prompt Runner, Creator Core, BHIV Core, and Bucket
- Creating and updating artifact chains
- Performing pipeline health checks
- Exposing the end-to-end execution API

**What it does NOT own**
- Business logic inside Creator Core and BHIV Core
- Artifact storage semantics beyond invoking the bucket
- Complex replay beyond bucket retrieval fallback

**What can influence it**
- Environment variables for service URLs
- Upstream service availability and response schemas

**What it can influence**
- Final result payload shape
- Trace ID consistency and artifact chain completeness
- Pipeline health status

**Execution rights**
- Sends HTTP requests to upstream services
- Stores artifacts in the Bucket via HTTP

**Authority rights**
- No explicit trust domain enforcement beyond request chaining

**Constitutional boundaries**
- Must never bypass the configured pipeline order
- Must not call BHIV Core or Bucket directly with unverified data

---

### TTG / TTV / Gurukul / Simulation Participation

**Location:** mostly architectural references and product target mappings.

**What it owns**
- Design-time product target classification in Creator Core
- Future integration surfaces through `product_target` metadata

**What it does NOT own**
- Concrete runtime connectors or deployment adapters in this repo

**What can influence it**
- Creator Core blueprint payload mapping
- External integration requirements

**What it can influence**
- How future product-specific modules are selected and executed

**Execution rights**
- None in the current runtime—it is a planning and product routing layer.

**Authority rights**
- None today; it simply carries a `product_target` label.

**Constitutional boundaries**
- Must not be interpreted as a fully implemented integration channel
- Must not modify core pipeline behavior until actual adapters are added

---

## Component Relationship Summary

- `integration_bridge.py` is the pipeline coordinator.
- `prompt-runner01/run_server.py` supplies a prompt instruction payload.
- `creator-core/Core-Integrator-Sprint-1.1/main.py` creates blueprints and stores them.
- `main.py` is the BHIV Core execution engine and replay gateway.
- `bhiv_bucket.py` stores artifacts persistently and provides replay trace retrieval.
- `full_tantra_flow_test.py` demonstrates the full TANTRA sequence including CET/Sarathi/Gate and replay validation.

## Architecture boundaries

- **Upstream boundary:** user prompt enters through the Integration Bridge or Prompt Runner.
- **Midstream boundary:** Creator Core and BHIV Core exchange blueprint and execution payloads.
- **Downstream boundary:** Bucket stores and reconstructions occur after execution.
- **Audit boundary:** InsightFlow telemetry and replay logs are the main observability outputs.

## Operational note

A new developer should treat Prompt Runner, CET, Sarathi, and Gate as architecture placeholders until they are fully implemented as deployable services.
