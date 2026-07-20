# ARTHA Phase 4: Replay & Provenance - Implementation Guide

## Overview

Phase 4 implements comprehensive replay and provenance capabilities for the ARTHA accounting system, providing deterministic transaction replay, complete causality reconstruction, and audit trail verification.

## Key Capabilities

### 1. Transaction Replay
- **Deterministic Replay**: Transactions can be replayed with identical outcomes
- **Simulation Mode**: Replay without creating new database entries
- **Stage-by-Stage Reconstruction**: Each transaction stage can be replayed individually
- **State Validation**: Current state matches expected state from replay

### 2. Provenance Reconstruction
- **Complete Causality Chains**: Full parent-child relationships reconstructed
- **Entity Graphs**: Visual representation of transaction relationships
- **Lineage Tracking**: Historical progression of transaction states
- **Cross-Reference Validation**: Links between traces, journals, and entities verified

### 3. Trace Continuity Verification
- **Unbroken Chains**: Verification that no gaps exist in transaction flow
- **Stage Completeness**: All required stages present and accounted for
- **Temporal Ordering**: Correct chronological sequence maintained
- **Hash Chain Integrity**: HMAC validation across entire trace

## Implementation Details

### Core Models Used
- **UnifiedTrace**: Primary trace management with TRC-YYYYMMDD-UUID format
- **RuntimeProof**: Evidence capture linked to specific traces
- **JournalEntry**: Accounting entries with trace references
- **AccountBalance**: Real-time balances derived from journal entries

### API Endpoints

#### Fetch Complete Trace Chain
```http
GET /api/v1/trace/:traceId
Authorization: Bearer {token}
```

Response includes:
- All stages in chronological order
- Linked entities (expenses, invoices, journal entries)
- Causality relationships
- Completion status and timestamps

#### Reconstruct Provenance
```http
GET /api/v1/trace/:traceId/lineage
Authorization: Bearer {token}
```

Response provides:
- Complete lineage graph
- Parent-child causality chains
- Entity relationship mapping
- Historical state transitions

#### Replay Transaction
```http
POST /api/v1/trace/:traceId/replay
Content-Type: application/json
Authorization: Bearer {token}

{
  "mode": "simulation"
}
```

Features:
- Simulation mode (no database changes)
- Production mode (creates new entries)
- Deterministic validation
- Stage-by-stage replay capability

#### Verify Trace Continuity
```http
GET /api/v1/trace/:traceId/continuity
Authorization: Bearer {token}
```

Validates:
- Unbroken chain from start to finish
- All required stages present
- Correct temporal sequencing
- No missing intermediate steps

### Testing Framework

The `replay-provenance.js` script validates:

1. **Original Transaction Creation**
   - Creates expense with approval workflow
   - Records transaction creating journal entry
   - Generates unified trace with proper ID format

2. **Complete Trace Chain Fetch**
   - Retrieves all stages for given trace
   - Validates stage completeness
   - Confirms required stages present

3. **Provenance Reconstruction**
   - Rebuilds complete causality graph
   - Maps entity relationships
   - Validates lineage integrity

4. **Transaction Replay**
   - Simulates transaction replay
   - Validates deterministic behavior
   - Confirms identical outcomes

5. **Continuity Verification**
   - Checks for gaps in trace chain
   - Validates unbroken flow
   - Confirms temporal consistency

6. **Runtime Proof Validation**
   - Links evidence to specific traces
   - Validates proof coverage
   - Confirms verification status

7. **State Reconstruction**
   - Rebuilds current state from traces
   - Validates consistency with database
   - Confirms historical accuracy

## Evidence Capture

### Automatic Evidence Collection
- **API Responses**: All trace-related API calls captured
- **Database States**: Before/after snapshots for replay operations
- **Causality Maps**: Visual graphs of transaction relationships
- **Replay Results**: Deterministic validation outcomes

### Evidence Files Generated
- `original_transaction_evidence.json`
- `trace_chain_evidence.json`
- `provenance_reconstruction_evidence.json`
- `replay_simulation_evidence.json`
- `trace_continuity_evidence.json`
- `runtime_proofs_evidence.json`
- `state_reconstruction_evidence.json`

## Integration with Existing System

### UnifiedTrace Integration
The UnifiedTrace model integrates with existing services:

```javascript
// In expense service
const trace = await traceabilityService.initializeTrace({
  entityType: 'expense',
  entityId: expense._id,
  operation: 'create_expense'
});

// Add stages as workflow progresses
await traceabilityService.addStage(trace.traceId, {
  stage: 'TRANSACTION_CREATED',
  data: { expenseId: expense._id },
  timestamp: new Date()
});
```

### RuntimeProof Integration
Evidence is automatically captured through middleware:

```javascript
// Middleware captures API responses
app.use('/api/v1/trace', runtimeProofMiddleware);

// Manual evidence capture for specific operations
await runtimeProofService.captureAPIResponse(traceId, {
  endpoint: '/api/v1/trace/:traceId/replay',
  method: 'POST',
  response: replayResult
});
```

## Configuration Requirements

### Environment Variables
```env
NODE_ENV=development|production
MONGODB_URI=mongodb://localhost:27017/artha
REDIS_URL=redis://localhost:6379
JWT_SECRET=your_jwt_secret
```

### Database Indexes
Ensure proper indexing for performance:
```javascript
// UnifiedTrace indexes
{ traceId: 1 }
{ entityId: 1, entityType: 1 }
{ "causality.parentTraceId": 1 }
{ createdAt: -1 }

// RuntimeProof indexes  
{ traceId: 1 }
{ proofType: 1 }
{ verified: 1 }
```

## Performance Considerations

### Replay Operations
- Simulation mode preferred for testing (no database writes)
- Production replay only when creating new historical records
- Batch operations for large trace chains
- Caching for frequently accessed traces

### Provenance Queries
- Limit lineage depth for complex graphs
- Use pagination for large entity sets
- Cache relationship mappings
- Index causality fields for fast lookups

## Troubleshooting

### Common Issues

**Trace Not Found**
```
Error: Trace TRC-20250219-ABC123 not found
Solution: Verify trace ID format and existence in database
```

**Incomplete Stages**
```
Error: Missing required stages: JOURNAL_VALIDATED
Solution: Check workflow completion and stage recording
```

**Replay Failures**
```
Error: Replay was not deterministic
Solution: Verify data consistency and eliminate non-deterministic operations
```

**Continuity Breaks**
```
Error: Trace continuity broken: gap between stages 2 and 4
Solution: Check for missing intermediate operations
```

## Security Considerations

### Access Control
- All endpoints require valid JWT authentication
- Role-based access for trace operations
- Audit logging for all replay operations
- Evidence sanitization removes sensitive data

### Data Protection
- Traces contain references, not sensitive data directly
- Runtime proofs sanitize authorization headers
- Replay operations logged for audit trail
- Causality chains protect transaction integrity

## Next Steps

### Phase 5 Integration
Phase 4 capabilities integrate with Phase 5 (Production Audit):
- Trace completeness audited in production health checks
- Replay capability validated as part of system readiness
- Provenance reconstruction tested for compliance requirements
- Evidence capture verified for regulatory audit trails

### Future Enhancements
- Visual provenance graphs in frontend
- Advanced replay scenarios (partial replay, conditional replay)
- Cross-system trace correlation
- Automated anomaly detection in causality chains

---

**Phase Status**: ✅ COMPLETE  
**Next Phase**: Phase 5 - Production Readiness Audit  
**Documentation Version**: 1.0  
**Last Updated**: February 19, 2025