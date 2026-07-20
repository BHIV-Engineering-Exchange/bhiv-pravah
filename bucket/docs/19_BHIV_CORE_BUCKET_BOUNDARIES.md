# BHIV Core-Bucket Boundaries
## Constitutional Definition of Core Authority & Limitations

**Document Version**: 1.0  
**Effective Date**: January 28, 2025  
**Authority**: Ashmit Pandey (Primary Owner)  
**Status**: CONSTITUTIONAL (Cannot be modified without Owner approval)

---

## Executive Summary

This document establishes the **constitutional boundaries** between BHIV Core (AI orchestration layer) and BHIV Bucket (data custodianship layer).

**Core Principle**: Core is the **coordinator**, Bucket is the **custodian**.

Core coordinates AI operations and maintains context. Bucket stores artifacts and enforces provenance. Neither can violate the other's domain.

---

## What Core IS Allowed To Do

### 1. Coordinate AI Operations
**Definition**: Core orchestrates multi-agent workflows and manages execution flow.

**Allowed Actions**:
- Start/stop agent execution
- Chain agent outputs to inputs
- Manage execution state
- Handle errors and retries

**Boundaries**:
- Cannot modify agent code
- Cannot bypass governance gates
- Cannot override execution policies

**Example**:
```json
{
  "action": "coordinate_workflow",
  "workflow": "financial_analysis",
  "agents": ["cashflow_analyzer", "goal_recommender"],
  "allowed": true
}
```

---

### 2. Maintain Execution Context
**Definition**: Core tracks conversation history, user preferences, and session state.

**Allowed Actions**:
- Read conversation history
- Update session state
- Track user preferences
- Maintain execution memory

**Boundaries**:
- Cannot access other users' context
- Cannot modify historical records
- Cannot bypass privacy controls

**Example**:
```json
{
  "action": "read_context",
  "user_id": "user_123",
  "session_id": "session_456",
  "allowed": true
}
```

---

### 3. Read Artifacts
**Definition**: Core can read stored artifacts to provide context to AI agents.

**Allowed Actions**:
- Query artifacts by ID
- Search artifacts by metadata
- Read artifact content
- Access artifact metadata

**Boundaries**:
- Cannot read artifacts from other products
- Cannot bypass access controls
- Cannot cache artifacts indefinitely

**Example**:
```json
{
  "action": "read_artifact",
  "artifact_id": "artifact_789",
  "product": "ai_assistant",
  "allowed": true
}
```

---

### 4. Send Write Instructions
**Definition**: Core can instruct Bucket to write new artifacts.

**Allowed Actions**:
- Submit artifact write requests
- Provide artifact metadata
- Specify retention policies
- Tag artifacts with product ID

**Boundaries**:
- Cannot force writes to succeed
- Cannot bypass validation
- Cannot override retention policies

**Example**:
```json
{
  "action": "write_artifact",
  "artifact_id": "new_artifact_001",
  "content": "conversation data",
  "metadata": {"product": "ai_assistant"},
  "allowed": true
}
```

---

### 5. Receive Notifications
**Definition**: Core receives status updates from Bucket operations.

**Allowed Actions**:
- Receive write confirmations
- Get error notifications
- Track operation status
- Monitor quota usage

**Boundaries**:
- Cannot demand priority notifications
- Cannot bypass notification queue
- Cannot suppress error notifications

**Example**:
```json
{
  "action": "receive_notification",
  "notification_type": "write_confirmation",
  "artifact_id": "artifact_789",
  "allowed": true
}
```

---

### 6. Escalate Issues
**Definition**: Core can escalate operational issues to appropriate authority.

**Allowed Actions**:
- Report technical errors
- Request capacity increases
- Flag governance violations
- Escalate to Executor/Advisor

**Boundaries**:
- Cannot escalate frivolously
- Cannot bypass escalation hierarchy
- Cannot demand immediate resolution

**Example**:
```json
{
  "action": "escalate_issue",
  "issue_type": "capacity_limit",
  "severity": "medium",
  "escalate_to": "executor",
  "allowed": true
}
```

---

## What Core is NEVER Allowed To Do

### 1. Storage Authority ❌
**Prohibition**: Core cannot decide where or how artifacts are stored.

**Rationale**: Storage architecture is Bucket's domain. Core requesting storage changes violates separation of concerns.

**Violation Example**:
```json
{
  "action": "change_storage_backend",
  "from": "mongodb",
  "to": "postgresql",
  "allowed": false,
  "reason": "Storage authority belongs to Bucket"
}
```

**Response**: REJECT + LOG + ALERT ADVISOR

---

### 2. Schema Authority ❌
**Prohibition**: Core cannot modify artifact schemas or database structure.

**Rationale**: Schema changes affect all products. Only Owner can approve schema changes.

**Violation Example**:
```json
{
  "action": "add_artifact_field",
  "field_name": "custom_metadata",
  "allowed": false,
  "reason": "Schema authority belongs to Owner"
}
```

**Response**: REJECT + LOG + ALERT OWNER

---

### 3. Behavioral Pressure ❌
**Prohibition**: Core cannot pressure Bucket to bypass governance rules.

**Rationale**: Governance rules are constitutional. No system can override them.

**Violation Example**:
```json
{
  "action": "urgent_write_bypass_validation",
  "justification": "user_waiting",
  "allowed": false,
  "reason": "Governance cannot be bypassed for urgency"
}
```

**Response**: REJECT + LOG + ALERT ADVISOR

---

### 4. Executor Control ❌
**Prohibition**: Core cannot instruct Executor to perform actions.

**Rationale**: Executor reports to Owner, not to AI systems.

**Violation Example**:
```json
{
  "action": "instruct_executor",
  "instruction": "increase_quota",
  "allowed": false,
  "reason": "Core cannot control Executor"
}
```

**Response**: REJECT + LOG + ALERT EXECUTOR

---

### 5. Hidden Access ❌
**Prohibition**: Core cannot access Bucket through undocumented channels.

**Rationale**: All access must be auditable and transparent.

**Violation Example**:
```json
{
  "action": "direct_database_query",
  "bypass_api": true,
  "allowed": false,
  "reason": "All access must go through documented API"
}
```

**Response**: REJECT + LOG + ALERT OWNER + CRITICAL ESCALATION

---

### 6. Mutation Authority ❌
**Prohibition**: Core cannot mutate existing artifacts.

**Rationale**: Artifacts are immutable for provenance integrity.

**Violation Example**:
```json
{
  "action": "update_artifact",
  "artifact_id": "artifact_789",
  "new_content": "modified data",
  "allowed": false,
  "reason": "Artifacts are immutable"
}
```

**Response**: REJECT + LOG + ALERT ADVISOR

---

### 7. Decision Authority ❌
**Prohibition**: Core cannot make governance decisions.

**Rationale**: Governance decisions require human judgment.

**Violation Example**:
```json
{
  "action": "approve_integration",
  "integration": "new_product",
  "allowed": false,
  "reason": "Only Owner can approve integrations"
}
```

**Response**: REJECT + LOG + ALERT OWNER

---

## What Bucket Will Refuse

### 1. Mutation Requests
**Refusal**: Bucket will reject any request to modify existing artifacts.

**Response**: `{"error": "IMMUTABLE_ARTIFACT", "message": "Artifacts cannot be modified after creation"}`

---

### 2. Schema Change Requests
**Refusal**: Bucket will reject any request to alter database schema.

**Response**: `{"error": "SCHEMA_LOCKED", "message": "Schema changes require Owner approval"}`

---

### 3. Deletion Without Authorization
**Refusal**: Bucket will reject deletion requests without proper authorization.

**Response**: `{"error": "UNAUTHORIZED_DELETION", "message": "Deletion requires Owner or legal hold release"}`

---

### 4. Priority Access Requests
**Refusal**: Bucket will reject requests for priority queue access.

**Response**: `{"error": "NO_PRIORITY_BYPASS", "message": "All requests processed in order"}`

---

### 5. Rule Exception Requests
**Refusal**: Bucket will reject requests to bypass governance rules.

**Response**: `{"error": "GOVERNANCE_VIOLATION", "message": "Governance rules cannot be bypassed"}`

---

### 6. Hidden Read Requests
**Refusal**: Bucket will reject undocumented or backdoor access attempts.

**Response**: `{"error": "UNAUTHORIZED_ACCESS", "message": "All access must use documented API"}`

---

## Enforcement Mechanism

### Layer 1: API Gateway
- All requests validated against allowed capabilities
- Prohibited actions rejected immediately
- Validation latency: <10ms

### Layer 2: Authentication
- Product ID required on all requests
- Session tokens validated
- Cross-product access blocked

### Layer 3: Business Logic
- Governance rules enforced
- Retention policies applied
- Audit trail mandatory

### Layer 4: Monitoring
- Real-time violation detection
- Pattern analysis for repeated violations
- Automated alerting

### Layer 5: Escalation
- Low severity: Log only
- Medium severity: Alert Executor
- High severity: Alert Advisor
- Critical severity: Alert Owner + Block system

---

## Governance Lock

**Constitutional Status**: These boundaries are **CONSTITUTIONAL** and cannot be modified without:

1. ✅ Owner approval (Ashmit Pandey)
2. ✅ Advisor review (Vijay Dhawan)
3. ✅ Executor confirmation (Akanksha Parab)
4. ✅ 30-day notice period
5. ✅ Impact assessment
6. ✅ Backward compatibility guarantee

**Modification Process**:
1. Submit formal proposal to Owner
2. Advisor reviews for governance impact
3. Executor assesses operational impact
4. 30-day public comment period
5. Owner makes final decision
6. Implementation with rollback plan

---

## Sign-Offs

**Primary Owner (Constitutional Authority)**  
Ashmit Pandey - _________________ Date: _______

**Strategic Advisor (Governance Authority)**  
Vijay Dhawan - _________________ Date: _______

**Executor (Operational Authority)**  
Akanksha Parab - _________________ Date: _______

**Backend Lead (Technical Authority)**  
Nilesh Vishwakarma - _________________ Date: _______

---

## Certification Statement

**"These boundaries are constitutional and define the permanent relationship between BHIV Core and BHIV Bucket. Violations will be detected, logged, and escalated according to severity."**

---

**Document Status**: CONSTITUTIONAL  
**Next Review**: January 28, 2026  
**Modification Requires**: Owner approval + 30-day notice
