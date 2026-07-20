# ARTHA_SETU_CONTRACT.md — Artha ↔ SETU Integration Contract

## Overview

This document defines the canonical payload contract for signals emitted
by Artha and consumed by SETU (and downstream by Tantra).

Every signal is:
1. **Deterministic** — same input always produces same signal_id type and context shape
2. **Traceable** — `trace_id` links back to the originating transaction in Artha
3. **Reconstructable** — `source.entity_id` + `source.entity_type` is enough to replay the full chain

---

## Canonical Signal Payload

```json
{
  "signal_id": "SIG_GST_MISMATCH",
  "trace_id": "TRC-20260403-a1b2c3d4",

  "source": {
    "system": "ARTHA",
    "module": "GST_ENGINE",
    "entity_type": "INVOICE",
    "entity_id": "INV-20260403-0001"
  },

  "severity": "HIGH",

  "timestamp": "2026-04-03T10:00:00.000Z",

  "context": {
    "expected_tax": "1800.00",
    "actual_tax": "1500.00",
    "variance": "300.00",
    "gst_rate": 18,
    "customer_state": "MH",
    "company_state": "MH",
    "is_interstate": false
  },

  "recommendation": {
    "code": "REVIEW_GST_COMPUTATION",
    "message": "Invoice tax amount does not match GST engine calculation. Review line-level tax rates."
  }
}
```

---

## Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `signal_id` | string | yes | Signal type identifier. Format: `SIG_{SOURCE}_{EVENT}` |
| `trace_id` | string | yes | Originating transaction trace. Format: `TRC-YYYYMMDD-{uuid8}` |
| `source.system` | string | yes | Always `"ARTHA"` |
| `source.module` | string | yes | Emitting module: `GST_ENGINE`, `TDS_ENGINE`, `LEDGER`, `INVOICE`, `EXPENSE`, `COMPLIANCE_FILING` |
| `source.entity_type` | string | yes | `INVOICE`, `EXPENSE`, `TDS_ENTRY`, `JOURNAL_ENTRY`, `COMPLIANCE_FILING` |
| `source.entity_id` | string | yes | The human-readable ID (invoiceNumber, entryNumber, filingId) |
| `severity` | string | yes | `CRITICAL` \| `HIGH` \| `MEDIUM` \| `LOW` |
| `timestamp` | ISO8601 | yes | UTC timestamp of signal generation |
| `context` | object | yes | Signal-specific key-value pairs (see per-signal schemas below) |
| `recommendation.code` | string | yes | Machine-readable action code |
| `recommendation.message` | string | yes | Human-readable action description |

---

## Per-Signal Context Schemas

### SIG_GST_MISMATCH
```json
{
  "invoice_id": "INV-20260403-0001",
  "expected_tax": "1800.00",
  "actual_tax": "1500.00",
  "variance": "300.00",
  "gst_rate": 18,
  "customer_state": "MH",
  "company_state": "MH",
  "is_interstate": false
}
```

### SIG_GST_INVALID_RATE
```json
{
  "entity_id": "INV-20260403-0001",
  "invalid_rate": 15,
  "allowed_rates": [0, 5, 12, 18, 28]
}
```

### SIG_GST_MIXED_TAX_TYPE
```json
{
  "journal_entry_id": "JE-20260403-0001",
  "has_igst": true,
  "has_cgst_sgst": true
}
```

### SIG_GST_MISSING_GSTIN
```json
{
  "invoice_number": "INV-20260403-0001",
  "supply_type": "B2B",
  "filing_id": "FIL-<uuid>"
}
```

### SIG_GST_PERIOD_MISMATCH
```json
{
  "invoice_number": "INV-20260403-0001",
  "invoice_date": "2026-03-15",
  "filing_period_start": "2026-04-01",
  "filing_period_end": "2026-04-30"
}
```

### SIG_GST_NEGATIVE_LIABILITY
```json
{
  "filing_id": "FIL-<uuid>",
  "filing_type": "GSTR-3B",
  "net_liability": "-500.00"
}
```

### SIG_TDS_MISSING_PAN
```json
{
  "deductee_name": "Vendor ABC",
  "entry_number": "TDS-20260403-0001",
  "section": "194J"
}
```

### SIG_TDS_MISSING_CHALLAN
```json
{
  "entry_number": "TDS-20260403-0001",
  "deductee_pan": "ABCDE1234F",
  "section": "194J",
  "tds_amount": "5000.00"
}
```

### SIG_TDS_EXCESS_DEDUCTION
```json
{
  "entry_number": "TDS-20260403-0001",
  "payment_amount": "10000.00",
  "tds_amount": "12000.00"
}
```

### SIG_LEDGER_IMBALANCE
```json
{
  "journal_entry_id": "JE-20260403-0001",
  "total_debit": "10000.00",
  "total_credit": "9500.00",
  "difference": "500.00"
}
```

### SIG_LEDGER_HASH_TAMPER
```json
{
  "ledger_entry_position": 42,
  "journal_id": "JE-20260403-0001",
  "expected_hash": "abc123...",
  "actual_hash": "def456..."
}
```

### SIG_LEDGER_CHAIN_BREAK
```json
{
  "position": 42,
  "expected_prev_hash": "abc123...",
  "actual_prev_hash": "xyz789..."
}
```

### SIG_CASHFLOW_NEGATIVE
```json
{
  "cash_flow": "-25000.00",
  "account_codes": ["1000", "1010"],
  "period_start": "2026-04-01",
  "period_end": "2026-04-30"
}
```

### SIG_INVOICE_OVERDUE
```json
{
  "invoice_number": "INV-20260403-0001",
  "customer_name": "Client XYZ",
  "due_date": "2026-03-31",
  "days_overdue": 3,
  "amount_due": "50000.00"
}
```

### SIG_FILING_NOT_READY
```json
{
  "filing_id": "FIL-<uuid>",
  "filing_type": "GSTR-1",
  "period": "2026-04",
  "error_count": 3,
  "errors": [
    { "code": "MISSING_GSTIN", "severity": "HIGH", "reference_id": "INV001" }
  ]
}
```

---

## Recommendation Codes

| Code | Applies To |
|------|-----------|
| `REVIEW_GST_COMPUTATION` | SIG_GST_MISMATCH, SIG_GST_INVALID_RATE |
| `CORRECT_TAX_CLASSIFICATION` | SIG_GST_MIXED_TAX_TYPE |
| `ADD_CUSTOMER_GSTIN` | SIG_GST_MISSING_GSTIN |
| `VERIFY_INVOICE_PERIOD` | SIG_GST_PERIOD_MISMATCH |
| `REVIEW_ITC_CLAIMS` | SIG_GST_NEGATIVE_LIABILITY |
| `UPDATE_DEDUCTEE_PAN` | SIG_TDS_MISSING_PAN |
| `LINK_CHALLAN` | SIG_TDS_MISSING_CHALLAN |
| `REVIEW_TDS_RATE` | SIG_TDS_EXCESS_DEDUCTION |
| `INVESTIGATE_LEDGER` | SIG_LEDGER_IMBALANCE, SIG_LEDGER_HASH_TAMPER, SIG_LEDGER_CHAIN_BREAK |
| `PRIORITIZE_COLLECTIONS` | SIG_CASHFLOW_NEGATIVE, SIG_INVOICE_OVERDUE |
| `RESOLVE_FILING_ERRORS` | SIG_FILING_NOT_READY |

---

## SETU Endpoint (Proposed)

```
POST {SETU_BASE_URL}/api/v1/signals/ingest
Authorization: Bearer {SETU_API_KEY}
Content-Type: application/json

Body: <Canonical Signal Payload>
```

Expected response:
```json
{
  "acknowledged": true,
  "setu_signal_id": "SETU-SIG-<uuid>",
  "received_at": "2026-04-03T10:00:01.000Z"
}
```

---

## Artha → SETU → Tantra Flow

```
Artha Event (Invoice sent / Expense recorded / Filing generated)
  │
  ▼
signalEngine.service.js
  │  evaluates ledger snapshot + compliance state
  │  generates canonical signal payload
  │
  ▼
ComplianceSignal.create()   ← persisted in Artha DB
  │
  ▼
POST {SETU_BASE_URL}/signals/ingest   ← HTTP delivery
  │
  ▼
SETU
  │  routes by signal_id type
  │  enriches with SETU context
  │
  ▼
Tantra
  │  receives structured signal
  │  triggers workflow / alert / dashboard update
```

---

## Environment Variables Required

```env
SETU_BASE_URL=https://setu.example.com
SETU_API_KEY=<api_key>
SETU_ENABLED=true
SETU_TIMEOUT_MS=5000
```

When `SETU_ENABLED=false` (default), signals are persisted to `ComplianceSignal`
but not dispatched to SETU. This allows local development without SETU dependency.
