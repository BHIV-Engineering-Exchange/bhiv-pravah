# ARTHA Evidence Generation Report

## Evidence Automation Architecture

### Auto-Capture Mechanisms
1. **API Response Evidence**: Every API response automatically captured as RuntimeProof
2. **Database State Evidence**: Before/after snapshots for mutations
3. **Chain Verification Evidence**: Hash-chain integrity proofs
4. **Balance Sheet Evidence**: Accounting equation verification

### Evidence Types
| Type | Trigger | Content |
|------|---------|---------|
| API_RESPONSE | Every API call | Request/response, latency, status |
| DATABASE_STATE | Data mutations | Before/after document state |
| CHAIN_VERIFICATION | Chain check | Hash validity, entry count |
| BALANCE_SHEET | Report generation | Assets, liabilities, equity |
| TERMINAL_LOG | Commands | Command, output, exit code |
| SCREENSHOT | Visual capture | UI state at point in time |

### Evidence Storage
- **Collection**: RuntimeProof
- **Indexing**: By trace_id, proof_type, timestamp
- **Retention**: Per retentionDays (default 7 years)
- **Integrity**: Immutable once created

### Evidence Retrieval
- **By Trace**: `GET /api/v1/tantra/evidence/:traceId`
- **Summary**: `GET /api/v1/tantra/evidence`
- **Dashboard**: `GET /health/dashboard`

### Workflow Evidence Coverage
| Workflow | Evidence Generated |
|----------|-------------------|
| Invoice Create | API proof, DB state |
| Invoice Send | Journal proof, ledger proof |
| Invoice Payment | Payment proof, journal proof |
| Expense Create | API proof, DB state |
| Expense Approve | Journal proof, ledger proof |
| Payment Initiate | Payment proof, trace init |
| Payment Process | Payment completion proof |
| Payment Retry | Retry evidence, failure reason |
| Payment Reverse | Reversal proof, journal reversal |
| Journal Create | Hash computation, chain link |
| Journal Validate | Validation proof, compliance check |
| Journal Post | Posting proof, ledger entries |
| Month Close | Close checklist, snapshot |
| Quarter Close | GST/TDS reconciliation |
| Annual Close | Closing entries, final TB |
| Bank Reconcile | Match evidence, journal creation |
| GST Filing | Filing packet, validation |
| TDS Filing | Form generation, validation |
| SETU Dispatch | Dispatch proof, acknowledgement |

### Certification Readiness
- **Ledger Integrity**: Auto-verified, hash-chained
- **Audit Trail**: Immutable, 7-year retention
- **Evidence Automation**: Runtime-generated, no manual intervention
- **Replay Capability**: Full trace reconstruction available
- **Observability**: Health, metrics, dashboard operational
