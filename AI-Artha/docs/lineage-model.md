# ARTHA Lineage Model

## Overview
This document describes the data lineage architecture in ARTHA — how a financial event (invoice, expense, TDS deduction)
flows from origination through the ledger, into compliance processing, and ultimately into a signal dispatched to SETU.

Every step in this chain is **traceable by a single `trace_id`** that threads through all layers.

---

## Lineage Philosophy

> Every INR that enters or leaves ARTHA must leave an immutable, verifiable trail from the originating
> business event through to the compliance filing and any resulting signal.

This is implemented via:
1. **Dual hash-chain** — Journal entries and ledger entries each maintain independent SHA-256/HMAC-SHA256 chains
2. **trace_id threading** — a single trace ID connects journal → compliance → signal → SETU
3. **Reconstruction endpoint** — `GET /signals/trace/:traceId` proves every step by querying the DB

---

## Lineage Graph

```
                                    ORIGINATING EVENT
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
      InvoiceService              ExpenseService               TDSService
      .sendInvoice()              .recordExpense()              .recordTDSDeduction()
              │                           │                           │
              └───────────────────────────┼───────────────────────────┘
                                          │
                                          ▼
                                 LedgerService
                            .createJournalEntry()
                                          │
                            ┌─────────────┼─────────────┐
                            │             │             │
                    validateJournalEntry() │    postJournalEntry()
                            │             │             │
                      balance check   GST check   LedgerEntries written
                            │             │             │
                            └─────────────┼─────────────┘
                                          │
                                   JournalEntry (POSTED)
                                   trace_id: TRC-*
                                   hash: HMAC-SHA256
                                          │
                                          ▼
                               COMPLIANCE ENGINE
                            gstStatutory.service.js
                            tdsStatutory.service.js
                                          │
                            ┌─────────────┼─────────────┐
                            │             │             │
                      GSTR-1        GSTR-3B        Form26Q
                   generation     generation     generation
                            │             │             │
                            └─────────────┼─────────────┘
                                          │
                                ComplianceFiling
                                (stored in MongoDB)
                                          │
                                 validationService
                                 .validateGSTR1()
                                 .validateGSTR3B()
                                          │
                                 validation result
                                 { filing_ready, errors[] }
                                          │
                                          ▼
                                signalEngineService
                               .evaluateFilingResult()
                                          │
                                   emitSignal()
                                          │
                                          ▼
                                ComplianceSignal
                                (persisted BEFORE dispatch)
                                trace_id: TRC-* ← same ID
                                          │
                                          ▼
                                 SETU PIPELINE
                              normalizeSignal()
                              validateSignal()
                              mapToSetuPayload()
                              serializeForSetu()
                                          │
                                          ▼
                            POST {SETU_URL}/api/v1/signals/ingest
                            X-Artha-Trace: TRC-*
                            X-Signal-Type: SIG_*
                            X-Severity: HIGH|MEDIUM|LOW
```

---

## Entity Relationships

```
JournalEntry
  ├── _id:          ObjectId
  ├── entryNumber:  "JE-YYYYMMDD-NNNN"
  ├── trace_id:     "TRC-YYYYMMDD-xxxxxxxx"  ← lineage anchor
  ├── status:       DRAFT | VALIDATED | POSTED
  ├── hash:         HMAC-SHA256(payload, HMAC_SECRET)
  ├── prevHash:     hash of previous JournalEntry
  └── lines[]:
        ├── account_id
        ├── type:   DEBIT | CREDIT
        ├── amount: Decimal128
        └── gstDetails: { gst_rate, taxable_value, cgst, sgst, igst }

LedgerEntry
  ├── _id:          ObjectId
  ├── journal_id:   → JournalEntry._id
  ├── account_id:   COA account reference
  ├── type:         DEBIT | CREDIT
  ├── amount:       Decimal128
  ├── hash:         SHA-256(journalId+accountId+amount+prevHash)
  └── prev_hash:    hash of previous LedgerEntry

ComplianceFiling
  ├── _id:          ObjectId
  ├── filing_id:    "FIL-<uuid>"
  ├── filing_type:  "GSTR-1" | "GSTR-3B" | "Form26Q"
  ├── period:       "2026-04"
  ├── trace_id:     "TRC-YYYYMMDD-xxxxxxxx"  ← CURRENTLY GAP: not always stored
  ├── filing_ready: boolean
  └── errors[]:     validation error objects

ComplianceSignal
  ├── _id:          ObjectId
  ├── signal_id:    "SIG-<uuid>"
  ├── type:         "SIG_GST_MISMATCH" | "SIG_TDS_MISSING_PAN" | ...
  ├── trace_id:     "TRC-YYYYMMDD-xxxxxxxx"  ← threads to JournalEntry
  ├── severity:     CRITICAL | HIGH | MEDIUM | LOW
  ├── source:       { system: "ARTHA", module: "GST_ENGINE", ... }
  ├── context:      { signal-type-specific payload }
  ├── recommendation: string
  ├── dispatch_status: pending | dispatched | failed
  └── created_at:   ISO timestamp
```

---

## Trace Reconstruction (5 Steps)

When `GET /api/v1/signals/trace/:traceId` is called, the system performs 5 DB queries:

```
Step 1: ComplianceSignal.findOne({ trace_id })
  → returns signal metadata, severity, type

Step 2: ComplianceFiling.findOne({ trace_id })
  → returns filing type, period, filing_ready, error count

Step 3: ComplianceFiling + filing document
  → returns source transaction count, filing period

Step 4: JournalEntry.find({ trace_id })
  → returns journal entries with status, hash, lines

Step 5: LedgerEntry.find({ journal_id: { $in: journalIds } })
  → returns individual debit/credit movements with hashes
```

Each step response includes `{ step, label, found: true|false, data }`.

**Reconstruction proof:**
```json
{
  "trace_id": "TRC-20260403-a1b2c3d4",
  "steps": [
    { "step": 1, "label": "Signal",                "found": true, "data": { "type": "SIG_FILING_NOT_READY", "severity": "HIGH" }},
    { "step": 2, "label": "Compliance Validation", "found": true, "data": { "filing_ready": false, "error_count": 1 }},
    { "step": 3, "label": "Compliance Filing",     "found": true, "data": { "filingType": "GSTR-1", "sourceCount": 4 }},
    { "step": 4, "label": "Journal Entries",       "found": true, "data": [{ "entryNumber": "JE-20260403-0001", "status": "POSTED" }]},
    { "step": 5, "label": "Ledger Entries",        "found": true, "data": [{ "account_id": "2311", "type": "CREDIT", "amount": "1500.00" }]}
  ]
}
```

---

## Hash Chain Integrity

ARTHA maintains two independent hash chains for tamper detection.

### Chain 1 — JournalEntry (HMAC-SHA256)
```
JE-001  prevHash="0"            hash=HMAC(payload)
JE-002  prevHash=JE-001.hash    hash=HMAC(payload)
JE-003  prevHash=JE-002.hash    hash=HMAC(payload)
```
- Algorithm: HMAC-SHA256 with `HMAC_SECRET` env var
- Purpose: Detect tampering of the accounting record itself
- Verification: `GET /api/v1/ledger/verify-chain` re-computes and compares all hashes

### Chain 2 — LedgerEntry (SHA-256)
```
LE-001  prev_hash="0"           hash=SHA256(journalId+accountId+amount+prev_hash)
LE-002  prev_hash=LE-001.hash   hash=SHA256(...)
```
- Algorithm: SHA-256 (no secret — deterministic from content)
- Purpose: Immutable audit trail of every debit/credit movement
- Verification: Same endpoint recomputes ledger chain

**If any record is modified after posting, the hash chain breaks at that point.**
The verification endpoint reports the first broken link, enabling forensic investigation.

---

## Lineage Guarantees

| Guarantee | Mechanism | Status |
|-----------|-----------|--------|
| Every journal entry has a unique trace_id | Generated at JE creation time | ✅ |
| Signal carries the same trace_id | Signal engine receives and stores it | ✅ |
| SETU payload carries trace_id | X-Artha-Trace header + body field | ✅ |
| Ledger is append-only | No UPDATE on posted entries | ✅ |
| Hash chain detects tampering | HMAC-SHA256 chain | ✅ |
| Compliance filing linked to trace | ComplianceFiling.trace_id | ⚠️ Gap — not always stored |
| Atomic journal + ledger creation | MongoDB transactions | ⚠️ Requires replica set |

---

## Known Lineage Gaps

### Gap L-1: ComplianceFiling.trace_id Not Stored
**Impact:** Trace reconstruction Step 3 returns `found: false` even when filing exists.  
**Fix:** Pass `trace_id` from JournalEntry into `generateGSTR1()` and store on `ComplianceFiling`.

### Gap L-2: Expense Auto-Record Signal Not Emitted
**Impact:** If expense recording fails after approval, no lineage signal is emitted.  
**Documented in:** `CONVERGENCE_GAPS.md` — `SIG_EXPENSE_RECORD_FAILED` is logged but not persisted.

### Gap L-3: No Trace on Direct Ledger Queries
**Impact:** When viewing ledger entries directly (`GET /ledger/entries`), there is no trace_id filter.
A consumer cannot query "show me all ledger entries for trace TRC-*".  
**Fix:** Add `GET /ledger/entries?traceId=TRC-*` query support.

---

## Extension Points for Other BHIV Products

Other products consuming ARTHA lineage:

1. **Pass trace_id in HTTP headers:** `X-BHIV-Trace-ID: TRC-*` when calling ARTHA APIs
2. **Store trace_id on your own entities:** Reference ARTHA's trace_id in your system records
3. **Call trace reconstruction:** `GET /api/v1/signals/trace/:traceId` for audit proof
4. **Subscribe to signals:** Poll `GET /api/v1/signals?trace_id=TRC-*` for lineage-linked signals

---

**Document Version**: 1.0  
**Last Updated**: June 2026  
**Owner**: BHIV Platform Engineering  
**Related Documents**: `REVIEW_PACKET.md`, `SIGNAL_MAPPING.md`, `ARTHA_SETU_CONTRACT.md`  
