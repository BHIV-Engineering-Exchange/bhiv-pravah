# ARTHA Replay Proof

## Overview
This document provides the conceptual model, API contract, and implementation guide for the
**end-to-end replay system** — the ability to reconstruct any past financial transaction from
the raw event sequence, verify its integrity against the hash chain, and produce a complete
audit report.

---

## What Is Replay?

Replay is the process of taking a `trace_id` and:
1. Finding every system artifact associated with it (journal, ledger, filing, signal)
2. Re-computing the hash chain from scratch
3. Comparing the recomputed hashes to the stored hashes
4. Asserting whether the transaction is **intact** (no tampering) or **compromised** (hash mismatch)

Unlike trace reconstruction (which queries existing data), replay **re-derives** the expected
state from first principles and validates it against what is stored.

---

## Replay Architecture

```
REPLAY REQUEST
  trace_id: "TRC-20260403-a1b2c3d4"
        │
        ▼
  Step 1: Load JournalEntry by trace_id
        │
        ├── Re-compute JE hash from payload fields
        ├── Compare to JournalEntry.hash
        ├── Result: INTACT | TAMPERED
        │
        ▼
  Step 2: Load LedgerEntries by journal_id
        │
        ├── For each LedgerEntry:
        │     re-compute hash = SHA256(journalId + accountId + amount + prevHash)
        │     compare to LedgerEntry.hash
        ├── Rebuild chain: each hash must equal prev_hash of next
        ├── Result: CHAIN_INTACT | CHAIN_BROKEN (at entry N)
        │
        ▼
  Step 3: Verify double-entry balance
        │
        ├── Sum all DEBIT lines
        ├── Sum all CREDIT lines
        ├── Assert: ΣDEBIT === ΣCREDIT
        ├── Result: BALANCED | IMBALANCED
        │
        ▼
  Step 4: Re-run GST calculation
        │
        ├── Re-execute gstEngine.calculateGSTBreakdown() with stored inputs
        ├── Compare to stored gstDetails on journal lines
        ├── Assert: computed === stored (within ₹0.01 tolerance)
        ├── Result: GST_VALID | GST_MISMATCH
        │
        ▼
  Step 5: Load ComplianceFiling and ComplianceSignal by trace_id
        │
        ├── Verify filing_ready status matches actual validation result
        ├── Verify signal severity matches validation error severity
        ├── Result: COMPLIANCE_CONSISTENT | COMPLIANCE_INCONSISTENT
        │
        ▼
  REPLAY REPORT
  {
    trace_id,
    journal: { status, hash_check, balance_check, gst_check },
    ledger: { chain_intact, first_broken_entry },
    compliance: { filing_found, filing_ready, signal_found, signal_severity },
    overall: "REPLAY_PASS" | "REPLAY_FAIL",
    discrepancies: []
  }
```

---

## Replay API Contract

### Endpoint
```
POST /api/v1/replay/:traceId
Authorization: Bearer <token>
Role: admin
```

### Response (success)
```json
{
  "status": "ok",
  "data": {
    "trace_id": "TRC-20260403-a1b2c3d4",
    "replayed_at": "2026-06-11T10:00:00.000Z",
    "replay_duration_ms": 142,
    "journal": {
      "entry_number": "JE-20260403-0001",
      "status": "POSTED",
      "hash_check": "INTACT",
      "balance_check": "BALANCED",
      "gst_check": "GST_VALID",
      "debits_total": "18000.00",
      "credits_total": "18000.00"
    },
    "ledger": {
      "entry_count": 4,
      "chain_check": "CHAIN_INTACT",
      "first_broken_entry": null
    },
    "compliance": {
      "filing_found": true,
      "filing_type": "GSTR-1",
      "filing_ready": false,
      "signal_found": true,
      "signal_type": "SIG_FILING_NOT_READY",
      "signal_severity": "HIGH"
    },
    "overall": "REPLAY_PASS",
    "discrepancies": []
  }
}
```

### Response (replay failure — tampered ledger)
```json
{
  "status": "ok",
  "data": {
    "trace_id": "TRC-20260403-a1b2c3d4",
    "overall": "REPLAY_FAIL",
    "discrepancies": [
      {
        "step": "ledger_chain",
        "entry_id": "LE-20260403-0002",
        "expected_hash": "abc123...",
        "actual_hash":   "def456...",
        "message": "Ledger entry hash mismatch — possible tampering detected"
      }
    ]
  }
}
```

---

## Reference Implementation

The replay script at `backend/scripts/replay-provenance-proof.js` demonstrates the replay pattern
using direct MongoDB queries.

```javascript
// backend/scripts/replay-provenance-proof.js (key excerpt)
async function replayTrace(traceId) {
  // Step 1: Load journal entry
  const journal = await JournalEntry.findOne({ trace_id: traceId });
  if (!journal) throw new Error(`No journal entry for trace ${traceId}`);

  // Step 2: Re-compute journal hash
  const recomputed = computeJournalHash(journal);
  const journalIntact = recomputed === journal.hash;

  // Step 3: Load ledger entries
  const ledgerEntries = await LedgerEntry.find({ journal_id: journal._id })
    .sort({ createdAt: 1 });

  // Step 4: Verify ledger chain
  let chainIntact = true;
  let firstBroken = null;
  let prevHash = '0';
  for (const entry of ledgerEntries) {
    const expectedHash = computeLedgerHash(entry, prevHash);
    if (expectedHash !== entry.hash) {
      chainIntact = false;
      firstBroken = entry._id;
      break;
    }
    prevHash = entry.hash;
  }

  // Step 5: Double-entry balance check
  const debits  = journal.lines.filter(l => l.type === 'DEBIT').reduce((s, l) => s + l.amount, 0);
  const credits = journal.lines.filter(l => l.type === 'CREDIT').reduce((s, l) => s + l.amount, 0);
  const balanced = Math.abs(debits - credits) < 0.01;

  return {
    trace_id:     traceId,
    journalIntact,
    chainIntact,
    firstBroken,
    balanced,
    overall: (journalIntact && chainIntact && balanced) ? 'REPLAY_PASS' : 'REPLAY_FAIL',
  };
}
```

---

## Replay Packet Format

A **replay packet** is a JSON document containing the complete replay result for a given
trace, including all raw data, hash checks, and a human-readable summary.

```json
{
  "packet_id": "RPK-20260611-001",
  "generated_at": "2026-06-11T10:00:00.000Z",
  "platform": "ARTHA v0.1",
  "trace_id": "TRC-20260403-a1b2c3d4",
  "originating_event": {
    "type": "INVOICE_SENT",
    "entity_id": "INV-20260403-0001",
    "amount": "18000.00",
    "currency": "INR"
  },
  "journal_proof": {
    "entry_number": "JE-20260403-0001",
    "status": "POSTED",
    "hash": "abc123def456...",
    "hash_algorithm": "HMAC-SHA256",
    "hash_check": "INTACT",
    "balance_check": "BALANCED",
    "lines": [
      { "account": "1100 Accounts Receivable", "type": "DEBIT",  "amount": "18000.00" },
      { "account": "4000 Revenue",             "type": "CREDIT", "amount": "15000.00" },
      { "account": "2311 Output CGST",         "type": "CREDIT", "amount": "1500.00" },
      { "account": "2312 Output SGST",         "type": "CREDIT", "amount": "1500.00" }
    ]
  },
  "ledger_proof": {
    "entry_count": 4,
    "chain_algorithm": "SHA-256",
    "chain_check": "CHAIN_INTACT",
    "entries": [
      { "entry_id": "LE-001", "account": "1100", "type": "DEBIT",  "hash": "...", "chain_valid": true },
      { "entry_id": "LE-002", "account": "4000", "type": "CREDIT", "hash": "...", "chain_valid": true }
    ]
  },
  "compliance_proof": {
    "filing_type": "GSTR-1",
    "period": "2026-04",
    "filing_ready": false,
    "error_count": 1,
    "signal_type": "SIG_FILING_NOT_READY",
    "signal_severity": "HIGH"
  },
  "setu_proof": {
    "payload_valid": true,
    "dispatch_status": "dispatched",
    "dispatched_at": "2026-04-03T10:00:30.000Z",
    "x_artha_trace": "TRC-20260403-a1b2c3d4"
  },
  "overall": "REPLAY_PASS",
  "discrepancies": [],
  "auditor_notes": "Transaction replayed successfully. All hash chains intact. GST mismatch signal correctly generated."
}
```

---

## Running the Replay Proof

### Using the provided script
```bash
# From project root
node backend/scripts/replay-provenance-proof.js

# Or for a specific trace ID:
REPLAY_TRACE_ID=TRC-20260403-a1b2c3d4 node backend/scripts/replay-provenance-proof.js
```

### Expected output
```
[REPLAY] Starting replay for trace: TRC-20260403-a1b2c3d4
[REPLAY] Step 1: Journal entry found — JE-20260403-0001 (POSTED)
[REPLAY] Step 1: Hash check — INTACT ✓
[REPLAY] Step 2: Ledger chain — 4 entries, chain INTACT ✓
[REPLAY] Step 3: Balance check — BALANCED (DR:18000 = CR:18000) ✓
[REPLAY] Step 4: GST check — VALID ✓
[REPLAY] Step 5: Compliance signal — SIG_FILING_NOT_READY (HIGH) ✓
[REPLAY] Overall: REPLAY_PASS ✓
[REPLAY] Packet written to: docs/replay-proof/replay-TRC-20260403-a1b2c3d4.json
```

---

## Replay Limitations (Current)

| Limitation | Description | Mitigation |
|------------|-------------|------------|
| No HTTP endpoint yet | Replay only available via script | Add `POST /replay/:traceId` API |
| GST re-computation uses live company_state | If company state changed, re-run may differ | Snapshot company_state at journal creation |
| Replay does not simulate SETU response | Cannot verify what SETU received | Store SETU response body in ComplianceSignal |
| No replay for snapshot-derived signals | Signals from `/signals/snapshot` have no trace_id | Document as known limitation |

---

## Forensic Use Cases

| Scenario | Replay Action | Expected Result |
|----------|--------------|----------------|
| Auditor questions an invoice | Replay trace_id → verify journal hash, balance | REPLAY_PASS with full line detail |
| Ledger tampering suspected | Replay all traces → find first broken hash | REPLAY_FAIL with broken entry ID |
| Signal dispute | Replay to confirm signal was correctly generated | Compliance proof section |
| SETU non-receipt claim | Replay → check dispatch_status + setu_proof | Dispatch evidence |

---

**Document Version**: 1.0  
**Last Updated**: June 2026  
**Owner**: BHIV Platform Engineering  
**Related**: `docs/lineage-model.md`, `REVIEW_PACKET.md`, `backend/scripts/replay-provenance-proof.js`  
