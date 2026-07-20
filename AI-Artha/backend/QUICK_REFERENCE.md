# ARTHA - Quick Reference Guide

## 🎯 System Overview

**Artha** is a CA-grade, GST-compliant accounting system built for Indian statutory requirements.

**Status:** ✅ Production Ready  
**Compliance:** GST, TDS, Double-Entry Accounting  
**Audit Grade:** CA-Compliant with full reconstructability

---

## 📋 Key Features

### ✅ GST Compliance
- Multi-rate support: 0%, 5%, 12%, 18%, 28%
- CGST/SGST for intra-state
- IGST for inter-state
- Automatic tax calculation
- Filing-ready reports

### ✅ TDS Compliance
- Multiple sections: 192, 194A, 194C, 194H, 194I, 194J, 194Q
- Quarterly aggregation
- Challan tracking
- Form 26Q/24Q ready

### ✅ Accounting Core
- Double-entry enforcement
- Immutable ledger (append-only)
- Hash-chain integrity
- Full audit trail
- Reversal entries (no deletion)

---

## 🔌 API Endpoints

### GST Operations

#### Calculate GST Breakdown
```javascript
import { calculateGSTBreakdown } from './services/gstEngine.service.js';

const result = calculateGSTBreakdown({
  transaction_type: 'sale',
  amount: 1000,
  gst_rate: 18,
  supplier_state: 'MH',
  company_state: 'MH'
});
// Returns: { taxable_value, cgst, sgst, igst, total_amount }
```

#### Get GST Summary
```http
GET /api/v1/reports/gst-summary?startDate=2024-04-01&endDate=2024-06-30
```

**Response:**
```json
{
  "total_output_tax": "45000.00",
  "total_input_credit": "18000.00",
  "net_payable": "27000.00",
  "breakdown": {
    "cgst": "13500.00",
    "sgst": "13500.00",
    "igst": "0.00"
  }
}
```

### TDS Operations

#### Create TDS Entry
```http
POST /api/v1/tds/entries
Content-Type: application/json

{
  "transactionDate": "2024-03-31",
  "section": "192",
  "deductee": {
    "name": "John Doe",
    "pan": "ABCDE1234F"
  },
  "paymentAmount": "50000.00",
  "tdsRate": 10
}
```

#### Get TDS Summary
```http
GET /api/v1/reports/tds-summary?startDate=2024-04-01&endDate=2024-06-30
```

**Response:**
```json
{
  "total_tds_deducted": "125000.00",
  "total_tds_payable": "125000.00"
}
```

### Journal Entry Operations

#### Create Journal Entry
```http
POST /api/v1/ledger/entries
Content-Type: application/json

{
  "date": "2024-03-15",
  "description": "Sale to ABC Pvt Ltd",
  "lines": [
    {
      "account": "65f1111111111111111111a1",
      "debit": "1180.00",
      "credit": "0",
      "description": "Accounts Receivable"
    },
    {
      "account": "65f2222222222222222222b2",
      "debit": "0",
      "credit": "1000.00",
      "description": "Revenue"
    },
    {
      "account": "65f3333333333333333333c3",
      "debit": "0",
      "credit": "90.00",
      "description": "Output CGST"
    },
    {
      "account": "65f4444444444444444444d4",
      "debit": "0",
      "credit": "90.00",
      "description": "Output SGST"
    }
  ],
  "gstDetails": [
    {
      "transaction_type": "sale",
      "amount": "1000.00",
      "gst_rate": 18,
      "supplier_state": "MH",
      "company_state": "MH",
      "taxable_value": "1000.00",
      "cgst": "90.00",
      "sgst": "90.00",
      "igst": "0.00"
    }
  ],
  "source": "MANUAL"
}
```

#### Validate Entry
```http
POST /api/v1/ledger/entries/{entryId}/validate
```

#### Post Entry
```http
POST /api/v1/ledger/entries/{entryId}/post
```

#### Create Credit Note
```http
POST /api/v1/ledger/credit-notes
Content-Type: application/json

{
  "amount": 1000,
  "gst_rate": 18,
  "supplier_state": "MH",
  "company_state": "MH",
  "reference": "INV-001",
  "description": "Sales return",
  "customerName": "ABC Pvt Ltd"
}
```

#### Create Debit Note
```http
POST /api/v1/ledger/debit-notes
Content-Type: application/json

{
  "amount": 5000,
  "expenseAccountCode": "6100",
  "reference": "BILL-001",
  "description": "Purchase correction"
}
```

#### Create Reversal Entry
```http
POST /api/v1/ledger/entries/{entryId}/reversal
Content-Type: application/json

{
  "reason": "Incorrect amount posted"
}
```

---

## 📊 Chart of Accounts (Key Codes)

### Assets
- **1010** - Cash
- **1100** - Accounts Receivable
- **2301** - Input CGST (Asset)
- **2302** - Input SGST (Asset)
- **2303** - Input IGST (Asset)

### Liabilities
- **2000** - Accounts Payable
- **2311** - Output CGST (Liability)
- **2312** - Output SGST (Liability)
- **2313** - Output IGST (Liability)
- **2400** - TDS Payable

### Income
- **4000** - Revenue
- **4010** - Sales Returns (Contra Revenue)

### Expenses
- **6100** - Salary Expense
- **6200** - Rent Expense
- **6700** - Professional Fees

---

## 🔐 Validation Rules

### Double-Entry
```javascript
// Every journal entry must balance
Total Debits = Total Credits
```

### GST Validation
```javascript
// Intra-state
IF supplier_state == company_state:
  CGST + SGST must exist
  IGST must be 0

// Inter-state
ELSE:
  IGST must exist
  CGST & SGST must be 0
```

### TDS Validation
```javascript
// TDS cannot exceed expense
TDS Amount ≤ Expense Amount
```

### Line Integrity
```javascript
// Each line must have EITHER debit OR credit (not both)
(debit > 0 AND credit = 0) OR (debit = 0 AND credit > 0)
```

---

## 🔍 Audit Trail Structure

Every journal entry has:

```javascript
{
  auditTrace: {
    action: "POSTED",
    entity_id: "65f123...",
    before_state: { status: "VALIDATED", ... },
    after_state: { status: "POSTED", ... },
    action_user: "65f987...",
    timestamp: "2024-03-15T10:30:45.123Z",
    trace_id: "550e8400-e29b-41d4-a716-446655440000"
  },
  auditTrail: [
    { action: "ENTRY_CREATED", ... },
    { action: "VALIDATED", ... },
    { action: "POSTED", ... }
  ]
}
```

---

## 🔗 Hash-Chain Integrity

### Structure
```javascript
{
  prevHash: "abc123...",  // Hash of previous entry
  hash: "def456...",      // Hash of current entry
  chainPosition: 42       // Position in chain
}
```

### Verification
```http
GET /api/v1/ledger/verify-chain
```

**Response:**
```json
{
  "isValid": true,
  "totalEntries": 1000,
  "errors": [],
  "message": "Ledger chain is valid and tamper-proof"
}
```

---

## 🧪 Testing

### Run Proof Scenarios
```bash
node tests/proof-scenarios.js
```

### Expected Output
```
✅ Scenario 1: GST Sale (Intra-State) - PASSED
✅ Scenario 2: TDS Salary - PASSED
✅ Scenario 3: Reversal Entry - PASSED
```

---

## 📦 Dependencies

### Core
- **decimal.js** - Arbitrary precision arithmetic (no floating-point errors)
- **mongoose** - MongoDB ODM with transaction support
- **crypto** - HMAC-SHA256 for hash-chain

### Validation
- **express-validator** - Input validation

---

## 🚀 Deployment Checklist

- [ ] Set `HMAC_SECRET` environment variable
- [ ] Configure MongoDB with replica set (for transactions)
- [ ] Ensure all compliance accounts exist (run `ensureComplianceAccounts()`)
- [ ] Verify hash-chain integrity (`/api/v1/ledger/verify-chain`)
- [ ] Test GST calculation for all rates (0%, 5%, 12%, 18%, 28%)
- [ ] Test TDS deduction for all sections
- [ ] Verify audit trail completeness
- [ ] Run proof scenarios (`node tests/proof-scenarios.js`)

---

## 📞 Support

For issues or questions:
1. Check `REVIEW_PACKET.md` for detailed documentation
2. Run proof scenarios to verify system integrity
3. Review audit logs for transaction history

---

## 📄 License

Proprietary - CA-Grade Accounting System

---

**Last Updated:** 2024-03-15  
**Version:** 1.0.0  
**Status:** Production Ready ✅
