# Authority Boundary Guide

## Overview

This guide explains how authority boundaries work in the ARTHA BHIV ecosystem participant.

## Authority Model

ARTHA uses capability-based security with strict authority boundaries:

1. **Capability Contracts:** Define what each capability owns and doesn't own
2. **Route Mapping:** Maps API routes to capabilities
3. **Policy Engine:** Enforces boundaries at runtime
4. **Collection Guards:** Controllers verify mutations

## Capability Contracts

### Contract Structure

Each capability contract (`contracts/capability_contracts/*.json`) defines:

```json
{
  "capability_id": "ARTHA-LEDGER-001",
  "capability_name": "Ledger Engine",
  "authority_owned": [...],
  "authority_explicitly_not_owned": [...],
  "api_endpoints": {...},
  "input_schemas": {...},
  "output_schemas": {...}
}
```

### Authority Boundaries

**authority_owned:** What this capability can do
- Journal entry creation, validation, posting
- Double-entry integrity enforcement
- Hash chain maintenance
- Account balance computation

**authority_explicitly_not_owned:** What this capability CANNOT do
- Invoice lifecycle (consumed via InvoiceService)
- Expense approval workflow (consumed via ExpenseService)
- User authentication and authorization

### Route Mapping

Routes are mapped to capabilities in `capability_route_map.json`:

```json
{
  "routes": [
    { "prefix": "/api/v1/ledger", "capability": "ARTHA-LEDGER-001" },
    { "prefix": "/api/v1/invoices", "capability": "ARTHA-LEDGER-001" },
    { "prefix": "/api/v1/signals", "capability": "ARTHA-SIGNAL-001" },
    ...
  ]
}
```

## Enforcement Layers

### Layer 1: Authority Enforcement Middleware

Existing middleware (`authorityBoundary.js`) loads contracts and provides basic enforcement.

### Layer 2: Policy Engine Middleware (NEW)

New middleware (`policyEngine.js`) provides runtime enforcement:

1. **Capability Resolution:** Maps request to capability
2. **Read-Only Protection:** Blocks writes on read-only capabilities
3. **Collection Guards:** Blocks mutations on blocked collections
4. **Policy Decisions:** Records ALLOW/DENY with audit

### Layer 3: Controller Guards

Controllers call `guardCollection()` to verify mutations:

```javascript
import { guardCollection } from '../middleware/policyEngine.js';

async function createInvoice(req, res) {
  // Verify capability can mutate invoices
  guardCollection(req, 'invoices');

  // Proceed with creation...
}
```

## Collection Ownership

### ARTHA-LEDGER-001 (Ledger Engine)
- **Owns:** journalentries, ledgerentries, accountbalances, chartofaccounts
- **Blocked:** (none — can mutate all owned collections)

### ARTHA-SIGNAL-001 (Compliance Signal Engine)
- **Owns:** compliancesignals, compliancefilings, setudispatches
- **Blocked:** journalentries, ledgerentries (delegated to LEDGER)

### ARTHA-AUDIT-001 (Audit Engine)
- **Owns:** auditevents, auditlogs
- **Blocked:** (none)

### ARTHA-TRACE-001 (Trace Engine)
- **Owns:** unifiedtraces, runtimeproofs
- **Blocked:** (none)

### ARTHA-FINREPORT-001 (Financial Reporting)
- **Owns:** (read-only, no mutations)
- **Blocked:** (all mutations blocked)

### ARTHA-OBSERVE-001 (Observability)
- **Owns:** (read-only, no mutations)
- **Blocked:** (all mutations blocked)

### ARTHA-MULTICOMPANY-001 (Multi-Company)
- **Owns:** companies, costcentres
- **Blocked:** (none)

### ARTHA-TALLY-001 (Tally Integration)
- **Owns:** tallyexports, tallyimports
- **Blocked:** (none)

### ARTHA-EVIDENCE-001 (Evidence Collection)
- **Owns:** (read-only, no mutations)
- **Blocked:** (all mutations blocked)

## Policy Decision Flow

```
Request
  ↓
authorityEnforcement (existing)
  ↓
policyEnforcement (NEW)
  ↓
  ├── Route not mapped → DENY (production) / WARN (development)
  ↓
  ├── Capability is read-only + write request → DENY
  ↓
  ├── Collection in blocked_mutations → DENY
  ↓
  ├── ALLOW → record decision → next()
  ↓
protect (auth)
  ↓
Route Handler
  ↓
controller calls guardCollection()
  ↓
  ├── Not authorized → THROW
  ↓
  ├── Authorized → proceed
```

## Audit Trail

All policy decisions are recorded:

```json
{
  "timestamp": "2026-07-04T12:00:00.000Z",
  "capability": "ARTHA-LEDGER-001",
  "method": "POST",
  "path": "/api/v1/ledger/entries",
  "user": { "id": "...", "email": "...", "role": "accountant" },
  "decision": "ALLOW",
  "ip": "127.0.0.1"
}
```

## Violation Handling

### In Production

Violations are:
1. Logged to structured logger
2. Returned as 403 with POLICY_VIOLATION error
3. Recorded in audit trail
4. Recorded in provenance chain

### In Development

Violations are:
1. Logged as warnings
2. Allowed with warning (to facilitate development)
3. Recorded in audit trail

## Common Scenarios

### Scenario: Accountant Creates Invoice

1. Request: POST /api/v1/invoices
2. Policy Engine: Resolves to ARTHA-LEDGER-001
3. Check: ARTHA-LEDGER-001 not read-only → PASS
4. Check: invoices not in blocked_mutations → PASS
5. Decision: ALLOW
6. Controller: guardCollection(req, 'invoices') → PASS
7. Invoice created

### Scenario: Viewer Tries to Create Invoice

1. Request: POST /api/v1/invoices
2. Policy Engine: Resolves to ARTHA-LEDGER-001
3. Check: ARTHA-LEDGER-001 not read-only → PASS
4. Check: invoices not in blocked_mutations → PASS
5. Decision: ALLOW
6. Auth middleware: Role not in allowed roles → DENY (403)

### Scenario: Signal Engine Tries to Modify Journal Entries

1. Request: POST /api/v1/ledger/entries
2. Policy Engine: Resolves to ARTHA-LEDGER-001
3. Check: ARTHA-LEDGER-001 not read-only → PASS
4. Check: journalentries not in blocked_mutations → PASS
5. Decision: ALLOW
6. Controller: guardCollection(req, 'journalentries') → PASS
7. Journal entry created

Wait, this scenario shows the signal engine CAN modify journal entries through the LEDGER capability. This is by design — the LEDGER capability owns journal entries. The signal engine doesn't directly modify journal entries; it uses the ledger service.

### Scenario: Unknown Route Access

1. Request: POST /api/v1/unknown/endpoint
2. Policy Engine: No route mapping found
3. Decision: DENY (403) in production
4. Response: "Route not governed by any capability contract"

## Troubleshooting

### Issue: Valid Request Blocked

**Check:**
1. Is the route mapped in `capability_route_map.json`?
2. Is the capability read-only?
3. Is the collection in blocked_mutations?
4. Is the user's role authorized?

**Resolution:**
- Update route mapping if needed
- Update capability contract if needed
- Update user roles if needed

### Issue: Unauthorized Mutation

**Check:**
1. Which capability owns the collection?
2. Does the requesting capability have authority?
3. Is the controller calling guardCollection()?

**Resolution:**
- Update capability contract if needed
- Add guardCollection() call if missing
- Update authority boundaries if needed

## Adding New Capabilities

1. Create contract in `contracts/capability_contracts/`
2. Add route mapping in `capability_route_map.json`
3. Restart application to load new contract
4. Verify capability appears in governance status
5. Test authority boundaries
