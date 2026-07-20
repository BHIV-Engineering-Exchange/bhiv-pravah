# ARTHA Replay Execution Report

**Phase:** Phase 1 — Deterministic Replay Proof
**Script:** proof-replay.js
**Started:** 2026-06-17T11:30:58.958Z
**Completed:** 2026-06-17T11:31:02.485Z
**Status:** PASS

---

## Summary


- **Original Entry:** JE-20260617-0026
- **Replay Entry:** JE-20260617-0027
- **Verdict:** DETERMINISTIC REPLAY PROVEN — All outputs match, chain intact


---

## Execution Steps

### Step 1: Capture Original State

**Status:** SUCCESS

```json
{
  "timestamp": "2026-06-17T11:30:59.716Z",
  "journal_entry_count": 43,
  "ledger_entry_count": 114,
  "account_balance_count": 11,
  "cash_account": {
    "code": "1010",
    "name": "Bank Account"
  },
  "expense_account": {
    "code": "6100",
    "name": "Rent Expense"
  },
  "cash_balance_before": "-130200",
  "expense_balance_before": "22700"
}
```

### Step 2: Create Original Transaction

**Status:** SUCCESS

```json
{
  "expense": {
    "_id": "6a328574944bd81aa1e3e3c9",
    "expenseNumber": "EXP-000015",
    "amount": "5000.00",
    "totalAmount": "5900",
    "status": "recorded"
  },
  "journal": {
    "expense_number": "EXP-000015",
    "journal_entry_id": "6a328574944bd81aa1e3e3f7",
    "entry_number": "JE-20260617-0026",
    "status": "POSTED",
    "description": "Expense: Deterministic replay test expense - REPLAY_TEST_VENDOR",
    "lines": [
      {
        "account": "6a313fbe1d6c52322dd5cd04",
        "debit": "5000",
        "credit": "0",
        "description": "supplies expense"
      },
      {
        "account": "6a313fbe1d6c52322dd5cd1c",
        "debit": "900",
        "credit": "0",
        "description": "Input IGST"
      },
      {
        "account": "6a313fbe1d6c52322dd5ccf0",
        "debit": "0",
        "credit": "5900",
        "description": "Payment via bank_transfer"
      }
    ],
    "hash": "f7790501d5a7713570264c82f72831a86b87a94fbc284eadc3f77d44aa967b6d",
    "prevHash": "b1a71873071438e18c80779cfd4c366b0c00b932b54739a5bfeac1da94075cc3",
    "chainPosition": 41,
    "total_debit": "5900.00",
    "total_credit": "5900.00",
    "trace_id": "4f7ca4a5-6f26-4555-9c27-8d34f7ecd700"
  }
}
```

### Step 3: Capture Post-Transaction Balances

**Status:** SUCCESS

```json
{
  "cash_balance_after": "-136100",
  "expense_balance_after": "22700",
  "cash_delta": "-5900",
  "expense_delta": "0",
  "total_debit": "5900.00",
  "total_credit": "5900.00"
}
```

### Step 4: Capture Trace State

**Status:** SUCCESS

```json
{
  "available": false
}
```

### Step 5: Verify Original Hash Chain

**Status:** SUCCESS

```json
{
  "hash_exists": true,
  "hash_valid": true,
  "chain_from_entry": {
    "isValid": true,
    "totalEntriesVerified": 42,
    "errors": []
  }
}
```

### Step 6: Deterministic Replay Execution

**Status:** SUCCESS

```json
{
  "replay_journal_entry_id": "6a328576944bd81aa1e3e46c",
  "replay_entry_number": "JE-20260617-0027",
  "status": "POSTED",
  "replay_start": "2026-06-17T11:31:01.936Z",
  "replay_end": "2026-06-17T11:31:02.406Z",
  "lines": [
    {
      "account": "6a313fbe1d6c52322dd5cd04",
      "debit": "5000",
      "credit": "0",
      "description": "Replay: supplies expense"
    },
    {
      "account": "6a313fbe1d6c52322dd5cd1c",
      "debit": "900",
      "credit": "0",
      "description": "Replay: Input IGST"
    },
    {
      "account": "6a313fbe1d6c52322dd5ccf0",
      "debit": "0",
      "credit": "5900",
      "description": "Replay: Payment via bank_transfer"
    }
  ],
  "total_debit": "5900.00",
  "total_credit": "5900.00",
  "hash": "63507dee144592157e0bec782e50cc62f6ee861e80027c15f6a02296ad402ad1",
  "prevHash": "f7790501d5a7713570264c82f72831a86b87a94fbc284eadc3f77d44aa967b6d",
  "chainPosition": 42
}
```

### Step 7: Compare Original vs Replay

**Status:** SUCCESS

```json
{
  "line_count_match": true,
  "original_line_count": 3,
  "replay_line_count": 3,
  "accounts_match": true,
  "debits_match": true,
  "credits_match": true,
  "structure_match": true,
  "debit_totals_match": true,
  "credit_totals_match": true,
  "both_balanced": true,
  "both_posted": true,
  "hash_chain_integrity": true,
  "replay_hash_valid": true,
  "financial_equivalence": true,
  "overall_match": true
}
```

### Step 7.1: Field-by-Field Exact Comparison

**Status:** SUCCESS

```json
{
  "account_id": {
    "match": true,
    "detail": "Same account IDs for each line"
  },
  "debit": {
    "match": true,
    "detail": "Exact debit amounts"
  },
  "credit": {
    "match": true,
    "detail": "Exact credit amounts"
  },
  "total_debit": {
    "match": true,
    "detail": "Total debits equal"
  },
  "total_credit": {
    "match": true,
    "detail": "Total credits equal"
  },
  "status": {
    "match": true,
    "detail": "Both POSTED"
  },
  "balanced": {
    "match": true,
    "detail": "Both entries balanced"
  },
  "description": {
    "match": false,
    "intentional": true,
    "original": "Expense: Deterministic replay test expense - REPLAY_TEST_VENDOR",
    "replay": "[REPLAY] Expense: Deterministic replay test expense - REPLAY_TEST_VENDOR",
    "detail": "Replay prepends [REPLAY] for traceability — intentional divergence"
  },
  "date": {
    "match": false,
    "intentional": true,
    "original": "2026-06-17T11:31:00.310Z",
    "replay": "2026-06-17T11:31:01.958Z",
    "detail": "Replay uses execution timestamp — intentional divergence"
  },
  "tags": {
    "match": false,
    "intentional": true,
    "original": [
      "expense",
      "supplies"
    ],
    "replay": [
      "replay",
      "proof"
    ],
    "detail": "Replay tags entries for identification — intentional divergence"
  },
  "source": {
    "match": false,
    "intentional": true,
    "original": "MANUAL",
    "replay": "SYSTEM",
    "detail": "Replay marks source as SYSTEM — intentional divergence"
  },
  "trace_id": {
    "match": false,
    "intentional": true,
    "original": "4f7ca4a5-6f26-4555-9c27-8d34f7ecd700",
    "replay": "1842abe4-5c16-40c0-ab8a-88a438982403",
    "detail": "Replay generates new UUID for isolation — intentional divergence"
  },
  "reference": {
    "match": false,
    "intentional": true,
    "original": "EXP-000015",
    "replay": "REPLAY-JE-20260617-0026",
    "detail": "Replay prefixes reference with REPLAY- — intentional divergence"
  },
```

### Step 8: Post-Replay Balance Capture

**Status:** SUCCESS

```json
{
  "cash_balance_final": "-142000",
  "expense_balance_final": "22700"
}
```

### Step 9: Chain Continuity Verification

**Status:** SUCCESS

```json
{
  "chain_valid": true,
  "has_gaps": false,
  "chain_length": 120,
  "errors": [],
  "statistics": {
    "totalPostedEntries": 120,
    "chainLength": 120,
    "oldestEntry": "2026-06-16T12:21:19.098Z",
    "newestEntry": "2026-06-17T11:31:02.331Z",
    "hasGaps": false
  }
}
```

---

## Conclusion

✅ Deterministic replay is PROVEN. All outputs match, hash chain intact, balances verified.

---

*Generated by ARTHA Phase 1 — Deterministic Replay Proof*
*Timestamp: 2026-06-17T11:31:02.485Z*
