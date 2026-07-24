# BHIV Bucket v1 - Governance Implementation

## Document 01: Ownership & Custodianship

**Version**: 1.0.0  
**Effective Date**: January 13, 2026  
**Primary Owner**: Ashmit  
**Executor**: Akanksha  
**Technical Advisor**: Vijay Dhawan

---

## Implementation Status

### ✅ Implemented Features

1. **Governance Configuration** (`governance/config.py`)
   - Bucket version tracking (v1.0.0)
   - Ownership metadata
   - Approved artifact classes
   - Rejected artifact classes
   - Artifact validation logic

2. **New API Endpoints**
   - `GET /governance/info` - Get governance information
   - `POST /governance/validate-artifact` - Validate artifact classes
   - Enhanced `/health` endpoint with bucket version

3. **Backward Compatibility**
   - All existing endpoints unchanged
   - No breaking changes to API contracts
   - Governance layer is additive only

---

## API Endpoints

### Governance Endpoints

#### GET /governance/info
Returns BHIV Bucket v1 governance information.

**Response**:
```json
{
  "bucket_version": "1.0.0",
  "owner": "Ashmit",
  "executor": "Akanksha",
  "technical_advisor": "Vijay Dhawan",
  "effective_date": "2026-01-13",
  "approved_artifacts": [
    "agent_specifications",
    "basket_configurations",
    "execution_metadata",
    "agent_outputs",
    "logs",
    "state_data",
    "event_records",
    "configuration_metadata",
    "audit_trails"
  ],
  "governance_active": true
}
```

#### POST /governance/validate-artifact
Validates if an artifact class is approved for storage.

**Query Parameters**:
- `artifact_class` (required): The artifact class to validate

**Response**:
```json
{
  "approved": true,
  "reason": "Approved artifact class"
}
```

Or for rejected artifacts:
```json
{
  "approved": false,
  "reason": "Rejected: ai_model_weights not allowed in Bucket v1"
}
```

---

## Approved Artifact Classes

✅ **Allowed in Bucket v1**:
- `agent_specifications` - Agent metadata and schemas
- `basket_configurations` - Workflow definitions
- `execution_metadata` - Execution tracking data
- `agent_outputs` - Agent result data
- `logs` - Timestamped execution logs
- `state_data` - Agent internal state
- `event_records` - Agent event history
- `configuration_metadata` - System configuration snapshots
- `audit_trails` - Who did what, when

---

## Rejected Artifact Classes

❌ **Not Allowed in Bucket v1**:
- `ai_model_weights` - Belongs in separate model storage
- `video_files` - Belongs in object storage (S3, GCS)
- `business_logic_code` - Belongs in agent implementations
- `user_credentials` - Belongs in secret management
- `long_term_application_state` - Belongs in databases
- `unstructured_binary_data` - Belongs in blob storage
- `user_personal_data_pii` - Belongs in compliance storage

---

## Boundary Principle

**Bucket is for provenance and orchestration metadata, NOT application data.**

If you're asking "should we store this?", the answer is:
- Execution/agent related? → Probably yes
- Application data? → Probably no
- Unsure? → Escalate to Ashmit

---

## Versioning Strategy

### Current Version: 1.0.0

**Version Format**: MAJOR.MINOR.PATCH

- **MAJOR** (1.x.x): Breaking changes, schema changes, new artifact classes
- **MINOR** (x.1.x): New non-breaking features, new agents
- **PATCH** (x.x.1): Bug fixes, performance improvements

### Evolution Rules

- Small bug fixes → v1.0.1 (no approval needed)
- New non-breaking agent → v1.0.2 (document, note it)
- New artifact class → v1.1 (formal review, notify users)
- Schema change → v2.0 (major decision, migration path)

---

## Authority & Responsibility

### Ashmit (Primary Owner)

**Authority**:
- ✅ Final decision on integrations (approve/reject)
- ✅ Authority over all governance documents
- ✅ Define team roles and boundaries
- ✅ Set Bucket policy and direction

**Responsibility**:
- ✅ Ensure schema integrity
- ✅ Maintain provenance guarantees
- ✅ Review integrations against criteria
- ✅ Update governance docs
- ✅ Communicate decisions clearly

### Akanksha (Executor)

**Authority**:
- ✅ Execute approved changes (code, deployment)
- ✅ Decide on non-breaking implementation details
- ✅ Refactor for maintainability
- ✅ Optimize performance

**Authority Limits**:
- ❌ Cannot change schema without approval
- ❌ Cannot add new artifact classes
- ❌ Cannot weaken provenance guarantees
- ❌ Cannot bypass governance review

### Vijay Dhawan (Technical Advisor)

**Authority**:
- ✅ Provide expert perspective on complex decisions
- ✅ Identify risks and mitigation strategies
- ✅ Offer architectural guidance
- ✅ Challenge assumptions constructively

**Authority Limits**:
- ❌ Cannot make final decisions
- ❌ Cannot override Ashmit's governance
- ❌ Not part of approval chain (advisory only)

---

## Integration Request Flow

```
Integration Request Arrives
    ↓
Ashmit Reviews Against Gate Checklist
    ↓
Missing Info? → Request from team
    ↓
Complex Decision? → Escalate to Vijay
    ↓
Ashmit Makes Final Decision
    ├─ APPROVED → Akanksha Implements
    ├─ REJECTED → Clear feedback to team
    └─ CONDITIONAL → Specify conditions, review after
```

---

## Testing Governance Endpoints

### Test Governance Info
```bash
curl http://localhost:8000/governance/info
```

### Test Artifact Validation (Approved)
```bash
curl -X POST "http://localhost:8000/governance/validate-artifact?artifact_class=agent_specifications"
```

### Test Artifact Validation (Rejected)
```bash
curl -X POST "http://localhost:8000/governance/validate-artifact?artifact_class=ai_model_weights"
```

### Test Enhanced Health Check
```bash
curl http://localhost:8000/health
```

---

## Backward Compatibility Guarantee

All existing endpoints remain unchanged:
- ✅ `/health` - Enhanced with bucket_version
- ✅ `/agents` - No changes
- ✅ `/baskets` - No changes
- ✅ `/run-agent` - No changes
- ✅ `/run-basket` - No changes
- ✅ `/create-basket` - No changes
- ✅ `/delete-basket` - No changes
- ✅ All other endpoints - No changes

New governance endpoints are additive only.

---

## Next Steps

1. **Phase 2 Features** (Future):
   - Integration approval workflow
   - Audit trail storage
   - Provenance tracking enhancements
   - Schema versioning system

2. **Documentation Updates**:
   - Update README.md with governance info
   - Add governance examples
   - Document integration request process

3. **Team Communication**:
   - Notify teams of governance endpoints
   - Provide integration guidelines
   - Establish review process

---

## Confirmation

**Implementation Date**: January 13, 2026  
**Implemented By**: System  
**Approved By**: Ashmit (Primary Owner)  
**Status**: ✅ Active and Operational

---

**Governance is now active. All integrations must follow the approval process.**
