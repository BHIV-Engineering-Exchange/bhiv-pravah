# ARTHA Lineage Model - Unified Trace Architecture

## Objective
Establish true end-to-end lineage eliminating trace continuity breaks between Expense → Journal → Ledger → Signal → SETU.

## Current Problem Analysis

### Existing Trace Fragmentation
```
Expense Creation
    ↓
Journal Entry (UUID: 507f1f77bcf86cd799439011)
    ↓
Ledger Posting
    ↓ [BREAK HERE] 
Signal Generation (new trace: TRC-20250219-ABC123)
    ↓
SETU Dispatch
```

**Issue**: Trace continuity breaks between Journal and Signal, violating full lineage expectations.

## Target Architecture

### Unified Trace Lineage
```
Root Transaction (TRC-20250219-ROOT001)
    ├── Expense Entity (TRC-20250219-EXP001)
    │   ├── Approval Stage
    │   └── Recording Stage
    ├── Journal Entity (TRC-20250219-JRN001) 
    │   ├── Creation Stage
    │   ├── Validation Stage
    │   └── Posting Stage
    ├── Ledger Entity (TRC-20250219-LED001)
    │   ├── Entry Creation
    │   └── Chain Integration
    ├── Compliance Entity (TRC-20250219-CMP001)
    │   ├── Rule Evaluation
    │   └── Signal Generation  
    └── Dispatch Entity (TRC-20250219-DSP001)
        ├── SETU Dispatch
        └── Notification Delivery
```

## Lineage Architecture Design

### 1. Root Transaction Identity

#### Canonical Transaction ID Format
```
TRC-{YYYYMMDD}-{SEQUENCE}-{TYPE}

Examples:
- TRC-20250219-000001-ROOT (Root transaction)
- TRC-20250219-000001-EXP  (Child: Expense)
- TRC-20250219-000001-JRN  (Child: Journal)  
- TRC-20250219-000001-LED  (Child: Ledger)
- TRC-20250219-000001-SIG  (Child: Signal)
- TRC-20250219-000001-DSP  (Child: Dispatch)
```

#### Root Transaction Schema
```json
{
  "rootTraceId": "TRC-20250219-000001-ROOT",
  "transactionType": "expense_workflow",
  "initiatedBy": "user@bhiv.in", 
  "initiatedAt": "2025-02-19T12:00:00.000Z",
  "businessContext": {
    "entityType": "expense",
    "workflowType": "approval_recording",
    "complianceRequired": ["tds", "gst"]
  },
  "lineage": {
    "children": [
      "TRC-20250219-000001-EXP",
      "TRC-20250219-000001-JRN",
      "TRC-20250219-000001-LED", 
      "TRC-20250219-000001-SIG",
      "TRC-20250219-000001-DSP"
    ],
    "depth": 5,
    "branchCount": 1
  },
  "status": "completed",
  "completedAt": "2025-02-19T12:05:30.000Z"
}
```

### 2. Child Trace Entities

#### Expense Trace Entity
```json
{
  "traceId": "TRC-20250219-000001-EXP",
  "parentTraceId": "TRC-20250219-000001-ROOT",
  "entityType": "expense",
  "entityId": "65d7890123456abcdef78901",
  "stages": [
    {
      "stage": "EXPENSE_CREATED",
      "timestamp": "2025-02-19T12:00:00.000Z",
      "data": {
        "amount": 5000.00,
        "vendor": "Test Vendor",
        "category": "Office Supplies"
      }
    },
    {
      "stage": "EXPENSE_APPROVED", 
      "timestamp": "2025-02-19T12:01:00.000Z",
      "approvedBy": "manager@bhiv.in"
    },
    {
      "stage": "EXPENSE_RECORDED",
      "timestamp": "2025-02-19T12:02:00.000Z", 
      "journalEntryId": "65d8901234567abcdef89012",
      "nextTrace": "TRC-20250219-000001-JRN"
    }
  ]
}
```

#### Journal Trace Entity
```json
{
  "traceId": "TRC-20250219-000001-JRN",
  "parentTraceId": "TRC-20250219-000001-ROOT", 
  "previousTrace": "TRC-20250219-000001-EXP",
  "entityType": "journal_entry",
  "entityId": "65d8901234567abcdef89012",
  "stages": [
    {
      "stage": "JOURNAL_CREATED",
      "timestamp": "2025-02-19T12:02:00.000Z",
      "data": {
        "entryNumber": "JE-2025-00158",
        "totalDebits": 5900.00,
        "totalCredits": 5900.00
      }
    },
    {
      "stage": "JOURNAL_VALIDATED",
      "timestamp": "2025-02-19T12:02:01.000Z",
      "validation": "double_entry_verified"
    },
    {
      "stage": "JOURNAL_POSTED",
      "timestamp": "2025-02-19T12:02:02.000Z",
      "ledgerPosition": 158,
      "nextTrace": "TRC-20250219-000001-LED"
    }
  ]
}
```

#### Signal Trace Entity  
```json
{
  "traceId": "TRC-20250219-000001-SIG",
  "parentTraceId": "TRC-20250219-000001-ROOT",
  "previousTrace": "TRC-20250219-000001-LED",
  "entityType": "compliance_signal",
  "entityId": "65d9012345678abcdef90123",
  "stages": [
    {
      "stage": "COMPLIANCE_EVALUATED",
      "timestamp": "2025-02-19T12:03:00.000Z",
      "rules": ["tds_threshold_check", "expense_categorization"]
    },
    {
      "stage": "SIGNAL_GENERATED", 
      "timestamp": "2025-02-19T12:03:01.000Z",
      "signalType": "tds_threshold_alert",
      "priority": "medium"
    },
    {
      "stage": "SIGNAL_DISPATCHED",
      "timestamp": "2025-02-19T12:03:02.000Z",
      "nextTrace": "TRC-20250219-000001-DSP"
    }
  ]
}
```

### 3. Cross-Link Strategy

#### Entity Reference Matrix
```json
{
  "crossReferences": {
    "TRC-20250219-000001-EXP": {
      "entityId": "65d7890123456abcdef78901",
      "entityCollection": "expenses",
      "linkedEntities": [
        {
          "type": "journal_entry",
          "id": "65d8901234567abcdef89012", 
          "trace": "TRC-20250219-000001-JRN"
        }
      ]
    },
    "TRC-20250219-000001-JRN": {
      "entityId": "65d8901234567abcdef89012",
      "entityCollection": "journalentries",
      "linkedEntities": [
        {
          "type": "expense",
          "id": "65d7890123456abcdef78901",
          "trace": "TRC-20250219-000001-EXP"
        },
        {
          "type": "ledger_entry", 
          "id": "65d9012345678abcdef90123",
          "trace": "TRC-20250219-000001-LED"
        }
      ]
    }
  }
}
```

#### Bi-directional Linkage
```javascript
// Forward linkage: Expense → Journal → Ledger → Signal
expense.traceInfo = {
  traceId: "TRC-20250219-000001-EXP",
  rootTraceId: "TRC-20250219-000001-ROOT", 
  nextTrace: "TRC-20250219-000001-JRN"
};

// Backward linkage: Signal → Ledger → Journal → Expense  
signal.traceInfo = {
  traceId: "TRC-20250219-000001-SIG",
  rootTraceId: "TRC-20250219-000001-ROOT",
  previousTrace: "TRC-20250219-000001-LED",
  originTrace: "TRC-20250219-000001-EXP"
};
```

### 4. Replay Strategy

#### Transaction Reconstruction Process
```javascript
class TransactionReconstructor {
  async reconstructTransaction(rootTraceId) {
    // 1. Retrieve root transaction
    const rootTrace = await this.getRootTrace(rootTraceId);
    
    // 2. Retrieve all child traces
    const childTraces = await this.getChildTraces(rootTrace.lineage.children);
    
    // 3. Reconstruct chronological flow
    const timeline = this.buildTimeline(rootTrace, childTraces);
    
    // 4. Verify linkage integrity
    const integrity = this.verifyLinkageIntegrity(timeline);
    
    // 5. Build entity graph
    const entityGraph = this.buildEntityGraph(timeline);
    
    return {
      rootTrace,
      childTraces,
      timeline,
      integrity,
      entityGraph,
      replayable: integrity.valid
    };
  }
  
  buildTimeline(rootTrace, childTraces) {
    const allEvents = [];
    
    // Add root transaction events
    allEvents.push({
      timestamp: rootTrace.initiatedAt,
      traceId: rootTrace.rootTraceId,
      event: "TRANSACTION_INITIATED",
      data: rootTrace.businessContext
    });
    
    // Add child trace stages
    childTraces.forEach(trace => {
      trace.stages.forEach(stage => {
        allEvents.push({
          timestamp: stage.timestamp,
          traceId: trace.traceId, 
          event: stage.stage,
          data: stage.data || {},
          entityType: trace.entityType,
          entityId: trace.entityId
        });
      });
    });
    
    // Sort chronologically
    return allEvents.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
  }
}
```

### 5. Ownership Model

#### Trace Ownership Hierarchy
```json
{
  "ownership": {
    "root": {
      "owner": "transaction_initiator",
      "permissions": ["read", "reconstruct", "audit"]
    },
    "children": {
      "expense_trace": {
        "owner": "expense_service",
        "permissions": ["read", "write", "stage_update"]
      },
      "journal_trace": {
        "owner": "ledger_service", 
        "permissions": ["read", "write", "verification"]
      },
      "signal_trace": {
        "owner": "compliance_service",
        "permissions": ["read", "write", "dispatch"]
      }
    },
    "global": {
      "audit_team": ["read", "reconstruct"],
      "admin": ["read", "write", "reconstruct", "audit"]
    }
  }
}
```

### 6. Versioning Strategy

#### Trace Version Management
```json
{
  "versionControl": {
    "traceId": "TRC-20250219-000001-EXP",
    "version": "1.0.0",
    "revisions": [
      {
        "version": "1.0.0",
        "timestamp": "2025-02-19T12:00:00.000Z",
        "changes": ["initial_creation"],
        "modifiedBy": "expense_service"
      },
      {
        "version": "1.1.0", 
        "timestamp": "2025-02-19T12:01:00.000Z",
        "changes": ["approval_stage_added"],
        "modifiedBy": "approval_service"
      }
    ],
    "immutableAfter": "completion",
    "retentionPolicy": "7_years"
  }
}
```

## Implementation Strategy

### 1. Database Schema Design

#### UnifiedTrace Collection Enhancement
```javascript
// Enhanced UnifiedTrace schema
const UnifiedTraceSchema = {
  // Core identification
  traceId: { type: String, required: true, unique: true },
  rootTraceId: { type: String, required: true },
  parentTraceId: { type: String },
  
  // Lineage information
  lineage: {
    level: { type: Number }, // 0 = root, 1 = child, 2 = grandchild
    position: { type: Number }, // Order in sequence
    previousTrace: { type: String },
    nextTrace: { type: String }
  },
  
  // Entity linkage
  entityType: { type: String, required: true },
  entityId: { type: String, required: true },
  entityCollection: { type: String, required: true },
  
  // Stages and timeline
  stages: [{
    stage: { type: String, required: true },
    timestamp: { type: Date, required: true },
    data: { type: Object },
    userId: { type: String },
    systemGenerated: { type: Boolean, default: false }
  }],
  
  // Cross-references
  linkedEntities: [{
    entityType: { type: String },
    entityId: { type: String },
    traceId: { type: String },
    relationship: { type: String } // 'parent', 'child', 'sibling'
  }],
  
  // Replay information
  replayInfo: {
    replayable: { type: Boolean, default: true },
    requiredPreconditions: [{ type: String }],
    expectedOutcomes: [{ type: String }]
  },
  
  // Metadata
  status: { type: String, enum: ['active', 'completed', 'failed'], default: 'active' },
  version: { type: String, default: '1.0.0' },
  createdAt: { type: Date, default: Date.now },
  completedAt: { type: Date },
  
  // Indexing fields
  dateCreated: { type: String }, // YYYY-MM-DD for efficient querying
  transactionType: { type: String },
  businessContext: { type: Object }
};
```

### 2. Service Integration Points

#### Expense Service Integration
```javascript
// In expense.service.js
class ExpenseService {
  async createExpense(expenseData, userId) {
    // 1. Create root trace
    const rootTrace = await traceabilityService.initializeRootTransaction({
      transactionType: 'expense_workflow',
      businessContext: {
        amount: expenseData.amount,
        vendor: expenseData.vendor,
        category: expenseData.category
      },
      initiatedBy: userId
    });
    
    // 2. Create expense
    const expense = await Expense.create(expenseData);
    
    // 3. Create expense trace  
    const expenseTrace = await traceabilityService.createChildTrace({
      rootTraceId: rootTrace.rootTraceId,
      entityType: 'expense',
      entityId: expense._id,
      stage: 'EXPENSE_CREATED',
      data: {
        amount: expense.amount,
        vendor: expense.vendor,
        category: expense.category
      }
    });
    
    // 4. Link expense to trace
    expense.traceInfo = {
      rootTraceId: rootTrace.rootTraceId,
      traceId: expenseTrace.traceId
    };
    await expense.save();
    
    return { expense, rootTrace, expenseTrace };
  }
}
```

#### Ledger Service Integration
```javascript
// In ledger.service.js  
class LedgerService {
  async createJournalEntry(expenseId, entryData) {
    // 1. Retrieve expense trace
    const expense = await Expense.findById(expenseId);
    const expenseTrace = await traceabilityService.getTrace(expense.traceInfo.traceId);
    
    // 2. Create journal entry
    const journalEntry = await JournalEntry.create(entryData);
    
    // 3. Create journal trace linked to expense trace
    const journalTrace = await traceabilityService.createChildTrace({
      rootTraceId: expenseTrace.rootTraceId,
      parentTraceId: expenseTrace.traceId,
      previousTrace: expenseTrace.traceId,
      entityType: 'journal_entry',
      entityId: journalEntry._id,
      stage: 'JOURNAL_CREATED',
      data: {
        entryNumber: journalEntry.entryNumber,
        totalDebits: journalEntry.totalDebits,
        totalCredits: journalEntry.totalCredits
      }
    });
    
    // 4. Update cross-references
    await traceabilityService.linkTraces(expenseTrace.traceId, journalTrace.traceId);
    
    return { journalEntry, journalTrace };
  }
}
```

### 3. API Endpoints for Lineage

#### Trace Lookup API
```javascript
// GET /api/v1/trace/:traceId/full-lineage
router.get('/:traceId/full-lineage', async (req, res) => {
  try {
    const { traceId } = req.params;
    
    // Get trace and determine if root or child
    const trace = await traceabilityService.getTrace(traceId);
    const rootTraceId = trace.rootTraceId || traceId;
    
    // Reconstruct full transaction
    const reconstruction = await traceabilityService.reconstructTransaction(rootTraceId);
    
    res.json({
      success: true,
      data: {
        rootTrace: reconstruction.rootTrace,
        fullLineage: reconstruction.timeline,
        entityGraph: reconstruction.entityGraph,
        integrity: reconstruction.integrity,
        replayable: reconstruction.replayable
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

#### Transaction Reconstruction API  
```javascript
// GET /api/v1/trace/reconstruct/:rootTraceId
router.get('/reconstruct/:rootTraceId', async (req, res) => {
  try {
    const { rootTraceId } = req.params;
    const { includeEntities = false } = req.query;
    
    const reconstruction = await traceabilityService.reconstructTransaction(rootTraceId);
    
    if (includeEntities) {
      // Load actual entity data for each trace
      reconstruction.entityData = await traceabilityService.loadEntityData(reconstruction.childTraces);
    }
    
    res.json({
      success: true,
      data: reconstruction
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

#### Lineage Lookup API
```javascript
// GET /api/v1/trace/lineage/:entityType/:entityId
router.get('/lineage/:entityType/:entityId', async (req, res) => {
  try {
    const { entityType, entityId } = req.params;
    
    // Find trace by entity
    const trace = await traceabilityService.getTraceByEntity(entityType, entityId);
    
    // Get full lineage
    const lineage = await traceabilityService.getFullLineage(trace.rootTraceId);
    
    res.json({
      success: true,
      data: {
        entity: { type: entityType, id: entityId },
        trace: trace,
        lineage: lineage,
        relatedEntities: lineage.crossReferences
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

## Success Criteria

### 1. Unbroken Lineage ✅
- Single root trace ID spans entire transaction lifecycle
- Child traces properly linked with previousTrace/nextTrace
- No orphaned traces or broken chains
- Complete audit trail from initiation to completion

### 2. Reconstructable Flow ✅  
- Any entity can be traced back to root transaction
- Complete timeline reconstruction possible
- All intermediary stages preserved
- Entity relationships maintained

### 3. Replay Capability ✅
- Deterministic transaction replay from trace data
- State reconstruction at any point in timeline
- Verification of expected vs actual outcomes
- Rollback capability for failed transactions

### 4. Cross-Entity Navigation ✅
- Bi-directional entity navigation (expense ↔ journal ↔ signal)
- Entity graph visualization possible
- Related entity discovery functional
- Impact analysis capabilities

### 5. Performance Optimized ✅
- Trace lookups under 100ms
- Lineage reconstruction under 500ms
- Efficient indexing on traceId, rootTraceId, entityId
- Pagination support for large lineages

## Implementation Timeline

1. **Phase 1**: Enhanced UnifiedTrace model with lineage fields
2. **Phase 2**: Service integration (expense, journal, signal services)
3. **Phase 3**: API endpoints for trace lookup and reconstruction  
4. **Phase 4**: Cross-reference linkage and entity graph building
5. **Phase 5**: Replay functionality and verification
6. **Phase 6**: Performance optimization and indexing

## Conclusion

This lineage model eliminates trace continuity breaks by:

- **Unified Identity**: Single root trace ID spans entire transaction
- **Hierarchical Structure**: Parent-child relationships maintain lineage
- **Cross-Linkage**: Bi-directional entity references enable navigation
- **Replay Capability**: Complete transaction reconstruction from traces
- **Performance**: Optimized queries for sub-second lineage lookup

The result is true end-to-end lineage where any entity can be traced back to its root transaction and the complete flow can be reconstructed deterministically.

---

**Model Version**: 1.0  
**Implementation Status**: Ready for Development  
**Expected Impact**: Eliminates all trace continuity breaks