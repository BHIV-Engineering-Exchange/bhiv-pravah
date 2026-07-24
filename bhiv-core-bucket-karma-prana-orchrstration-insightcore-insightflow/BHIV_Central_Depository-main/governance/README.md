# 🏛️ BHIV Bucket v1 - Governance Layer

## Overview

This directory contains the governance implementation for BHIV Bucket v1, establishing formal ownership, custodianship, and artifact management policies.

## Files

- **`config.py`** - Core governance configuration and validation logic
- **`snapshot.py`** - Schema snapshot and drift detection
- **`integration.py`** - Integration boundary and data flow validation
- **`artifacts.py`** - Artifact admission policy and validation
- **`provenance.py`** - Provenance guarantees and honest gaps assessment
- **`retention.py`** - Data retention and lifecycle policy
- **`integration_gate.py`** - Integration approval process and checklist
- **`executor_lane.py`** - Execution boundaries for Akanksha (Executor)
- **`escalation_protocol.py`** - Escalation protocol for Vijay (Technical Advisor)
- **`owner_principles.py`** - Core principles for Ashmit (Primary Owner)
- **`__init__.py`** - Module exports
- **`IMPLEMENTATION.md`** - Detailed implementation documentation
- **`BUCKET_V1_SNAPSHOT.md`** - Official baseline state (Document 02)
- **`INTEGRATION_BOUNDARY.md`** - Integration policy (Document 03)
- **`RETENTION_POSTURE.md`** - Retention and deletion policy (Document 06)
- **`INTEGRATION_GATE_CHECKLIST.md`** - Integration approval process (Document 07)
- **`EXECUTOR_LANE.md`** - Execution boundaries for Akanksha (Document 08)
- **`ESCALATION_PROTOCOL.md`** - Escalation protocol for Vijay (Document 09)
- **`OWNER_PRINCIPLES.md`** - Core principles for Ashmit (Document 10)

## Quick Start

### Check Governance Info
```python
from governance import get_bucket_info

info = get_bucket_info()
print(f"Bucket Version: {info['bucket_version']}")
print(f"Owner: {info['owner']}")
```

### Get Schema Snapshot
```python
from governance import get_snapshot_info

snapshot = get_snapshot_info()
print(f"Snapshot Date: {snapshot['snapshot_date']}")
print(f"Collections: {snapshot['mongodb_collections']}")
```

### Validate Artifact Class
```python
from governance import validate_artifact_class

result = validate_artifact_class("agent_specifications")
if result["approved"]:
    print("Artifact class approved for storage")
else:
    print(f"Rejected: {result['reason']}")
```

### Validate MongoDB Schema
```python
from governance import validate_mongodb_schema

document = {
    "agent": "test_agent",
    "message": "Test message",
    "timestamp": "2026-01-13T00:00:00Z",
    "level": "info"
}

result = validate_mongodb_schema("logs", document)
print(result)  # {"valid": True, "reason": "Schema validation passed"}
```

## API Endpoints

### Document 01: Governance & Ownership
- **GET /governance/info** - Returns governance metadata

### Document 02: Schema Snapshot
- **GET /governance/snapshot** - Returns Bucket v1 schema snapshot
- **POST /governance/validate-schema** - Validates MongoDB document

### Document 03: Integration Boundary
- **GET /governance/integration-requirements** - Get integration requirements
- **GET /governance/boundary** - Get boundary definition
- **POST /governance/validate-integration-pattern** - Validate integration pattern
- **POST /governance/validate-data-flow** - Validate data flow direction
- **POST /governance/validate-integration-checklist** - Validate integration checklist

### Document 04: Artifact Admission
- **GET /governance/artifact-policy** - Get artifact admission policy
- **GET /governance/artifact-details/{artifact_class}** - Get artifact details
- **GET /governance/decision-criteria** - Get admission criteria
- **POST /governance/validate-artifact** - Validate artifact class
- **POST /governance/validate-artifact-admission** - Validate artifact admission

### Document 05: Provenance Sufficiency
- **GET /governance/provenance/guarantees** - Get real guarantees
- **GET /governance/provenance/gaps** - Get honest gaps
- **GET /governance/provenance/details/{item_name}** - Get specific details
- **GET /governance/provenance/risk-matrix** - Get risk assessment
- **GET /governance/provenance/roadmap** - Get Phase 2 roadmap
- **GET /governance/provenance/compliance** - Get compliance status
- **GET /governance/provenance/trust-recommendations** - Get trust recommendations

### Document 06: Retention Posture
- **GET /governance/retention/config** - Get retention configuration
- **GET /governance/retention/rules** - Get per-artifact retention rules
- **GET /governance/retention/lifecycle** - Get data lifecycle stages
- **GET /governance/retention/deletion-strategy** - Get deletion strategy
- **GET /governance/retention/gdpr** - Get GDPR process
- **GET /governance/retention/legal-hold** - Get legal hold process
- **GET /governance/retention/storage-impact** - Get storage analysis
- **GET /governance/retention/cleanup-procedures** - Get cleanup procedures
- **GET /governance/retention/compliance-checklist** - Get compliance checklist
- **GET /governance/retention/dsar** - Get DSAR process
- **POST /governance/retention/calculate** - Calculate retention date

### Document 07: Integration Gate Checklist
- **GET /governance/integration-gate/requirements** - Get integration requirements
- **GET /governance/integration-gate/checklist** - Get 50-item approval checklist
- **GET /governance/integration-gate/blocking-criteria** - Get blocking criteria
- **GET /governance/integration-gate/timeline** - Get approval timeline
- **GET /governance/integration-gate/approval-likelihood** - Get approval likelihood
- **GET /governance/integration-gate/conditional-examples** - Get conditional examples
- **POST /governance/integration-gate/validate-request** - Validate integration request
- **POST /governance/integration-gate/validate-section** - Validate checklist section
- **POST /governance/integration-gate/check-blocking** - Check blocking criteria
- **POST /governance/integration-gate/generate-approval** - Generate approval decision
- **POST /governance/integration-gate/generate-rejection** - Generate rejection feedback
- **POST /governance/integration-gate/calculate-deadline** - Calculate approval deadline

### Document 08: Executor Lane (Akanksha)
- **GET /governance/executor/role** - Get executor role definition
- **GET /governance/executor/can-execute** - Get changes executable without approval
- **GET /governance/executor/requires-approval** - Get changes requiring approval
- **GET /governance/executor/forbidden** - Get forbidden actions
- **GET /governance/executor/checkpoints** - Get code review checkpoints
- **GET /governance/executor/success-metrics** - Get success metrics
- **GET /governance/executor/escalation-path** - Get escalation path
- **GET /governance/executor/default-rule** - Get default rule (IF UNSURE, ASK)
- **POST /governance/executor/categorize-change** - Categorize a change
- **POST /governance/executor/validate-change** - Validate change request

### Document 09: Escalation Protocol (Vijay)
- **GET /governance/escalation/advisor-role** - Get advisor role definition
- **GET /governance/escalation/triggers** - Get escalation triggers
- **GET /governance/escalation/response-timeline** - Get response timeline
- **GET /governance/escalation/response-format** - Get response format template
- **GET /governance/escalation/decision-authority** - Get decision authority boundaries
- **GET /governance/escalation/disagreement-protocol** - Get disagreement protocol
- **GET /governance/escalation/advisor-success-metrics** - Get advisor success metrics
- **GET /governance/escalation/process** - Get escalation process flow
- **POST /governance/escalation/create** - Create escalation to Vijay
- **POST /governance/escalation/validate-response** - Validate escalation response
- **POST /governance/escalation/assess-conflict** - Assess conflict of interest

### Document 10: Owner Core Principles
- **GET /governance/owner/metadata** - Get document metadata
- **GET /governance/owner/principles** - Get all 10 core principles
- **GET /governance/owner/principle/{number}** - Get specific principle details
- **GET /governance/owner/checklist** - Get responsibility checklist
- **GET /governance/owner/confirmation** - Get owner confirmation
- **GET /governance/owner/closing-thought** - Get closing thought
- **POST /governance/owner/validate-principle** - Validate principle adherence
- **POST /governance/owner/check-confirmation** - Check confirmation status

## Governance Principles

1. **Versioning is Sacred** - Bucket v1 is locked, changes require versioning
2. **Ownership is Clear** - Ashmit is Primary Owner with final authority
3. **Boundaries are Defined** - Only approved artifact classes allowed
4. **Backward Compatibility** - All existing endpoints remain unchanged
5. **Drift Detection** - Schema changes are tracked and validated
6. **One-Way Data Flow** - External → Bucket only (no push to external systems)
7. **Honest Provenance** - Document what IS and ISN'T guaranteed
8. **Retention Policy** - Clear lifecycle: tombstoning + TTL deletion

## Roles

- **Primary Owner**: Ashmit (final decisions)
- **Executor**: Akanksha (implementation)
- **Technical Advisor**: Vijay Dhawan (advisory)

## Approved Artifacts

✅ agent_specifications, basket_configurations, execution_metadata, agent_outputs, logs, state_data, event_records, configuration_metadata, audit_trails

## Rejected Artifacts

❌ ai_model_weights, video_files, business_logic_code, user_credentials, long_term_application_state, unstructured_binary_data, user_personal_data_pii

## Schema Snapshot (v1.0.0)

### MongoDB Collections
- **logs** - Agent execution logs with indexes on agent, timestamp, execution_id, level

### Redis Structures
- **execution_logs** - 24hr TTL
- **agent_outputs** - 1hr TTL
- **agent_state** - 1hr TTL
- **basket_execution** - 24hr TTL
- **basket_executions_list** - No TTL, rolling 100 items

## Drift Detection

Compare current state with baseline snapshot:
```bash
curl http://localhost:8000/governance/snapshot
```

Any schema changes = drift detected → escalate to owner.

---

## Document Summary

### Document 01: Governance & Ownership
- **Status**: ✅ Implemented
- **Purpose**: Formal ownership structure with Ashmit as Primary Owner
- **Endpoints**: 1

### Document 02: Schema Snapshot
- **Status**: ✅ Implemented
- **Purpose**: Baseline state for drift detection
- **Endpoints**: 2

### Document 03: Integration Boundary
- **Status**: ✅ Implemented
- **Purpose**: One-way data flow policy (External → Bucket)
- **Endpoints**: 5

### Document 04: Artifact Admission
- **Status**: ✅ Implemented
- **Purpose**: Approved/rejected artifact classes (12 approved, 8 rejected)
- **Endpoints**: 5

### Document 05: Provenance Sufficiency
- **Status**: ✅ Implemented
- **Purpose**: Honest assessment of audit guarantees (8 real, 7 gaps)
- **Endpoints**: 7

### Document 06: Retention Posture
- **Status**: ✅ Implemented
- **Purpose**: Data deletion and lifecycle policy (tombstoning + TTL)
- **Endpoints**: 11

### Document 07: Integration Gate Checklist
- **Status**: ✅ Implemented
- **Purpose**: Integration approval process (50-item checklist, 7-day timeline)
- **Endpoints**: 13

### Document 08: Executor Lane (Akanksha)
- **Status**: ✅ Implemented
- **Purpose**: Execution boundaries for Akanksha (9 can-execute, 8 requires-approval, 6 forbidden)
- **Endpoints**: 10

### Document 09: Escalation Protocol (Vijay)
- **Status**: ✅ Implemented
- **Purpose**: Advisory escalation protocol for Vijay (8 triggers, 4 urgency levels)
- **Endpoints**: 11

### Document 10: Owner Core Principles
- **Status**: ✅ Implemented
- **Purpose**: Core principles for Ashmit (10 principles, 8-item checklist)
- **Endpoints**: 8

**Total Governance Endpoints**: 73

---

**For detailed documentation, see `IMPLEMENTATION.md`, `BUCKET_V1_SNAPSHOT.md`, `INTEGRATION_BOUNDARY.md`, and `RETENTION_POSTURE.md`**
