# PRANA to Policy Architecture

## Purpose

End-to-end architecture explanation of signal propagation from PRANA through Bucket, Core, Policy, and Enforcement layers, preserving strict boundaries and runtime decoupling.

---

## 1. End-to-End Data Flow

### Signal Propagation Path

```
┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────────┐
│  PRANA  │─────▶│ Bucket  │─────▶│  Core   │─────▶│  Policy  │─────▶│ Enforcement │
│         │      │         │      │         │      │          │      │             │
│ Observe │      │ Store   │      │Orchestr │      │ Evaluate │      │  Execute    │
│ Emit    │      │ Replay  │      │ Mediate │      │ Flag     │      │  Action     │
└─────────┘      └─────────┘      └─────────┘      └─────────┘      └─────────────┘
     │                │                 │                │                  │
     │                │                 │                │                  │
     └────────────────┴─────────────────┴────────────────┴──────────────────┘
                                    Audit Trail
```

### Stage-by-Stage Flow

**Stage 1: PRANA Observation**
- Observes interaction signals (keyboard, mouse, scroll, etc.)
- Aggregates signals into counts
- Maps signal patterns to cognitive states
- Emits telemetry packets to Bucket
- **No policy awareness, no enforcement knowledge**

**Stage 2: Bucket Ingestion**
- Receives PRANA telemetry packets
- Validates packet schema
- Appends to immutable storage
- Provides replay capability
- **No interpretation, no evaluation**

**Stage 3: Core Orchestration**
- Reads telemetry from Bucket
- Batches signals for policy evaluation
- Invokes Policy Layer with signal batches
- Receives flags from Policy Layer
- Routes flags to Enforcement Layer
- **Mediates boundaries, enforces isolation**

**Stage 4: Policy Evaluation**
- Receives signal batches from Core
- Applies pattern recognition algorithms
- Evaluates relevance and misuse probability
- Generates advisory flags with confidence scores
- Returns flags to Core
- **No enforcement authority, no action execution**

**Stage 5: Enforcement Execution**
- Receives flags from Core
- Applies authorization rules
- Makes final enforcement decisions
- Executes authorized actions
- Logs enforcement outcomes
- **Independent authority, accountable decisions**

---

## 2. Trust Boundaries

### PRANA Trust Boundary

**PRANA is trusted because:**
- Cannot inspect content (no DOM, no screenshots, no keylogging)
- Cannot make decisions (no policy evaluation, no enforcement)
- Cannot be misused (no user-identifying content, no cross-user correlation)
- Cannot fail dangerously (fail-open, no application impact)

**PRANA trust is preserved by:**
- Runtime isolation (no shared state with other layers)
- Unidirectional communication (emits only, never receives commands)
- No configuration dependencies (no external policy loading)
- Immutable signal surface (documented, frozen contract)

### Bucket Trust Boundary

**Bucket is trusted because:**
- Append-only storage (immutability guarantee)
- No interpretation (raw telemetry storage only)
- No evaluation (no policy logic)
- Replay capability (audit and analysis support)

**Bucket trust is preserved by:**
- Immutable storage (no updates, no deletions)
- Schema validation (enforces PRANA contract)
- Temporal ordering (preserves signal sequence)
- Access control (read-only for PRANA, read-write for Core)

### Core Trust Boundary

**Core is trusted because:**
- Mediates all inter-layer communication
- Enforces isolation between Policy and Enforcement
- Maintains audit trails
- Does not evaluate or enforce (orchestration only)

**Core trust is preserved by:**
- Boundary enforcement (prevents direct Policy→Enforcement communication)
- Audit logging (all interactions recorded)
- Failure isolation (layer failures do not cascade)
- Authorization mediation (routes flags with context)

### Policy Trust Boundary

**Policy Layer is trusted because:**
- Advisory only (no enforcement authority)
- Probabilistic (acknowledges uncertainty)
- Fail-safe (uncertainty → no flag)
- Privacy-preserving (no content inspection)

**Policy Layer trust is preserved by:**
- No execution authority (cannot trigger actions)
- Confidence thresholds (requires high confidence for flags)
- Audit trails (all evaluations logged)
- Isolation from Enforcement (no direct communication)

### Enforcement Trust Boundary

**Enforcement Layer is trusted because:**
- Authorized decisions (requires explicit authorization)
- Accountable actions (all actions logged and attributable)
- Reversible operations (can undo enforcement actions)
- Independent evaluation (makes own decisions on flags)

**Enforcement Layer trust is preserved by:**
- Authorization requirements (cannot act without authorization)
- Audit trails (all decisions and actions logged)
- Accountability chains (clear responsibility assignment)
- Isolation from Policy (receives flags, makes own decisions)

---

## 3. Runtime Decoupling Guarantees

### PRANA Decoupling

**PRANA operates independently:**
- No runtime dependencies on Bucket availability
- No runtime dependencies on Core availability
- No runtime dependencies on Policy or Enforcement
- Fail-open behavior (silent cessation on failure)

**PRANA cannot be influenced:**
- No configuration updates at runtime
- No policy changes affect PRANA
- No enforcement actions affect PRANA
- No bidirectional communication

### Layer Decoupling

**Each layer operates independently:**
- Bucket failure → PRANA continues, Policy/Enforcement pause
- Core failure → PRANA/Bucket continue, Policy/Enforcement pause
- Policy failure → PRANA/Bucket/Core continue, Enforcement receives no flags
- Enforcement failure → PRANA/Bucket/Core/Policy continue, no actions executed

**No cascading failures:**
- Layer failures do not propagate upstream
- Layer failures do not propagate downstream
- Each layer fails independently
- Fail-open behavior preserves system availability

### Communication Decoupling

**Asynchronous communication:**
- PRANA→Bucket: Fire-and-forget (no response required)
- Bucket→Core: Pull-based (Core reads when ready)
- Core→Policy: Request-response (Policy evaluates and returns)
- Core→Enforcement: Event-driven (flags trigger evaluation)

**No blocking dependencies:**
- PRANA never waits for Bucket
- Bucket never waits for Core
- Policy evaluation timeout prevents Core blocking
- Enforcement decisions do not block Policy

---

## 4. Provenance and Auditability Design

### Signal Provenance

**Every signal carries provenance:**
- `system_id` - Source system identifier
- `timestamp` - Observation time (ISO8601)
- `observation_window_id` - Unique window identifier
- `prana_version` - PRANA specification version

**Provenance preservation:**
- Bucket preserves all provenance fields
- Core forwards provenance with signal batches
- Policy Layer logs provenance with evaluations
- Enforcement Layer logs provenance with actions

### Audit Trail Structure

**PRANA audit:**
- What signals were observed
- What states were emitted
- When observations occurred
- What transmission attempts were made

**Bucket audit:**
- What packets were received
- When packets were stored
- What schema validations occurred
- What replay operations were performed

**Core audit:**
- What signal batches were created
- When Policy Layer was invoked
- What flags were received
- What flags were routed to Enforcement

**Policy audit:**
- What patterns were evaluated
- What confidence scores were assigned
- What flags were generated
- What uncertainty was encountered

**Enforcement audit:**
- What flags were received
- What authorization was applied
- What decisions were made
- What actions were executed

### Audit Trail Guarantees

**Immutable audit logs:**
- Append-only (no modifications, no deletions)
- Cryptographically signed (tamper detection)
- Temporal ordering (preserves event sequence)
- Complete coverage (all interactions logged)

**Audit accessibility:**
- Read-only access for analysis
- Queryable by time range, system_id, flag type
- Exportable for compliance reporting
- Long-term retention (configurable retention policies)

---

## 5. Event-Driven Interaction Model

### Event Types

**Telemetry Events (PRANA→Bucket):**
- `prana.telemetry.emitted` - State telemetry packet
- Payload: PRANA packet schema
- Frequency: Every 2 seconds (per system)

**Storage Events (Bucket):**
- `bucket.packet.stored` - Packet successfully stored
- `bucket.packet.rejected` - Packet validation failed
- Payload: Packet metadata, validation results

**Orchestration Events (Core):**
- `core.batch.created` - Signal batch prepared for Policy
- `core.policy.invoked` - Policy Layer evaluation requested
- `core.flag.received` - Flag received from Policy Layer
- `core.flag.routed` - Flag routed to Enforcement Layer

**Evaluation Events (Policy):**
- `policy.pattern.evaluated` - Pattern recognition completed
- `policy.flag.generated` - Advisory flag created
- `policy.uncertainty.encountered` - Insufficient confidence
- Payload: Evaluation results, confidence scores

**Enforcement Events (Enforcement):**
- `enforcement.flag.received` - Flag received from Core
- `enforcement.decision.made` - Authorization decision
- `enforcement.action.executed` - Action performed
- Payload: Decision rationale, action details

### Event Flow Characteristics

**Unidirectional flow:**
- Events flow downstream (PRANA → Bucket → Core → Policy → Enforcement)
- No upstream event propagation
- No event loops or circular dependencies

**Event independence:**
- Each event is self-contained
- No event dependencies (except temporal ordering)
- Events can be processed out of order (with ordering metadata)

**Event durability:**
- Critical events persisted to audit log
- Events can be replayed for analysis
- Events support system recovery

---

## 6. Signal Propagation Without Violating PRANA Sovereignty

### Sovereignty Preservation Mechanisms

**PRANA remains unaware:**
- PRANA does not know Policy Layer exists
- PRANA does not know Enforcement Layer exists
- PRANA does not know how signals are used
- PRANA does not receive feedback or commands

**PRANA remains independent:**
- PRANA operates regardless of downstream availability
- PRANA signal surface is frozen (no runtime changes)
- PRANA has no enforcement hooks
- PRANA has no policy evaluation logic

**PRANA remains limited:**
- PRANA emits telemetry only (no flags, no recommendations)
- PRANA observes signals only (no content, no behavior)
- PRANA operates deterministically (no adaptation, no learning)

### Signal Transformation Points

**PRANA → Bucket:**
- No transformation (raw telemetry storage)
- Sovereignty preserved: PRANA contract unchanged

**Bucket → Core:**
- Batching and aggregation (multiple packets → single batch)
- Sovereignty preserved: No interpretation, no evaluation

**Core → Policy:**
- Signal batching and metadata addition (non-sensitive)
- Sovereignty preserved: PRANA signals unchanged, only batched

**Policy → Enforcement:**
- Flag generation (signals → flags)
- Sovereignty preserved: Flags are Policy Layer output, not PRANA output

### Boundary Enforcement

**Core enforces boundaries:**
- Prevents Policy Layer from accessing PRANA directly
- Prevents Enforcement Layer from accessing PRANA directly
- Prevents Policy Layer from accessing Enforcement Layer directly
- Mediates all inter-layer communication

**Architecture enforces boundaries:**
- Separate execution environments
- No shared state between layers
- Unidirectional communication only
- Immutable contracts

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           BHIV System Architecture                       │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│    PRANA     │  Observational Telemetry System
│              │  • Signal observation only
│  [SOVEREIGN] │  • No policy awareness
│              │  • No enforcement knowledge
└──────┬───────┘
       │ Telemetry (unidirectional)
       ▼
┌──────────────┐
│    Bucket    │  Append-Only Storage
│              │  • Immutable storage
│              │  • Replay capability
└──────┬───────┘
       │ Signal batches (pull-based)
       ▼
┌──────────────┐
│     Core     │  Orchestration Layer
│              │  • Mediates boundaries
│              │  • Enforces isolation
└───┬──────┬───┘
    │      │
    │      │ Flags (event-driven)
    │      ▼
    │ ┌──────────────┐
    │ │   Policy     │  Relevance/Misuse Intelligence
    │ │              │  • Pattern evaluation
    │ │              │  • Advisory flags only
    └─▶│              │
       └──────┬───────┘
              │ Flags (advisory)
              ▼
       ┌──────────────┐
       │ Enforcement  │  Action Execution
       │              │  • Authorized decisions
       │              │  • Accountable actions
       └──────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                           Audit Trail (All Layers)                       │
│                    Immutable, Append-Only, Queryable                     │
└─────────────────────────────────────────────────────────────────────────┘

Trust Boundaries:
  • PRANA: Isolated, unidirectional, no dependencies
  • Bucket: Immutable, no interpretation
  • Core: Mediation only, no evaluation
  • Policy: Advisory only, no enforcement
  • Enforcement: Authorized only, independent decisions
```

---

## Summary

The PRANA-to-Policy architecture:
- Preserves PRANA sovereignty through isolation and unidirectional communication
- Enables intelligent policy evaluation through indirect signal consumption
- Maintains clear trust boundaries between all layers
- Ensures runtime decoupling (failures do not cascade)
- Provides complete auditability (provenance and audit trails)
- Operates event-driven (asynchronous, non-blocking)

This architecture enables safe, decoupled intelligence layers while preserving PRANA's observational nature and sovereignty.

