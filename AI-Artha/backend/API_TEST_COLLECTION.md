# API Test Collection - Proof Scenarios

This file contains curl commands to test all three proof scenarios.

## Prerequisites

1. Server running on `http://localhost:5000`
2. Valid authentication token
3. Chart of Accounts initialized

## Setup

```bash
# Set your auth token
export TOKEN="your_jwt_token_here"
export BASE_URL="http://localhost:5000/api/v1"
```

---

## Scenario 1: GST Sale (Intra-State)

### Step 1: Get Account IDs

```bash
# Get Accounts Receivable (1100)
curl -X GET "$BASE_URL/accounts?code=1100" \
  -H "Authorization: Bearer $TOKEN"

# Get Revenue (4000)
curl -X GET "$BASE_URL/accounts?code=4000" \
  -H "Authorization: Bearer $TOKEN"

# Get Output CGST (2311)
curl -X GET "$BASE_URL/accounts?code=2311" \
  -H "Authorization: Bearer $TOKEN"

# Get Output SGST (2312)
curl -X GET "$BASE_URL/accounts?code=2312" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 2: Create Journal Entry

```bash
curl -X POST "$BASE_URL/ledger/entries" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-03-15",
    "description": "Sale to ABC Pvt Ltd - Intra-state",
    "lines": [
      {
        "account": "REPLACE_WITH_AR_ID",
        "debit": "1180.00",
        "credit": "0",
        "description": "Accounts Receivable"
      },
      {
        "account": "REPLACE_WITH_REVENUE_ID",
        "debit": "0",
        "credit": "1000.00",
        "description": "Revenue"
      },
      {
        "account": "REPLACE_WITH_OUTPUT_CGST_ID",
        "debit": "0",
        "credit": "90.00",
        "description": "Output CGST @ 9%"
      },
      {
        "account": "REPLACE_WITH_OUTPUT_SGST_ID",
        "debit": "0",
        "credit": "90.00",
        "description": "Output SGST @ 9%"
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
    "source": "MANUAL",
    "reference": "INV-001"
  }'
```

### Step 3: Validate Entry

```bash
# Replace ENTRY_ID with the ID from Step 2 response
curl -X POST "$BASE_URL/ledger/entries/ENTRY_ID/validate" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 4: Post Entry

```bash
curl -X POST "$BASE_URL/ledger/entries/ENTRY_ID/post" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 5: Get GST Summary

```bash
curl -X GET "$BASE_URL/reports/gst-summary?startDate=2024-03-01&endDate=2024-03-31" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "total_output_tax": "180.00",
    "total_input_credit": "0.00",
    "net_payable": "180.00",
    "breakdown": {
      "cgst": "90.00",
      "sgst": "90.00",
      "igst": "0.00"
    }
  }
}
```

---

## Scenario 2: TDS Salary

### Step 1: Create TDS Entry

```bash
curl -X POST "$BASE_URL/tds/entries" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transactionDate": "2024-03-31",
    "section": "192",
    "deductee": {
      "name": "John Doe",
      "pan": "ABCDE1234F",
      "address": "123 Main St, Mumbai"
    },
    "paymentAmount": "50000.00",
    "tdsRate": 10,
    "tdsAmount": "5000.00",
    "netPayable": "45000.00",
    "remarks": "Salary for March 2024"
  }'
```

### Step 2: Record TDS Deduction

```bash
# Replace TDS_ENTRY_ID with the ID from Step 1 response
curl -X POST "$BASE_URL/tds/entries/TDS_ENTRY_ID/record" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 3: Get TDS Summary

```bash
curl -X GET "$BASE_URL/reports/tds-summary?startDate=2024-03-01&endDate=2024-03-31" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "total_tds_deducted": "5000.00",
    "total_tds_payable": "5000.00"
  }
}
```

### Step 4: Get TDS Dashboard

```bash
curl -X GET "$BASE_URL/tds/dashboard?quarter=Q4&financialYear=FY2023-24" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Scenario 3: Reversal Entry

### Step 1: Create Original Entry

```bash
curl -X POST "$BASE_URL/ledger/entries" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-03-15",
    "description": "Rent payment for March 2024",
    "lines": [
      {
        "account": "REPLACE_WITH_RENT_EXPENSE_ID",
        "debit": "10000.00",
        "credit": "0",
        "description": "Rent Expense"
      },
      {
        "account": "REPLACE_WITH_CASH_ID",
        "debit": "0",
        "credit": "10000.00",
        "description": "Cash payment"
      }
    ],
    "source": "MANUAL",
    "reference": "RENT-MAR-2024"
  }'
```

### Step 2: Validate and Post

```bash
# Validate
curl -X POST "$BASE_URL/ledger/entries/ORIGINAL_ENTRY_ID/validate" \
  -H "Authorization: Bearer $TOKEN"

# Post
curl -X POST "$BASE_URL/ledger/entries/ORIGINAL_ENTRY_ID/post" \
  -H "Authorization: Bearer $TOKEN"
```

### Step 3: Create Reversal

```bash
curl -X POST "$BASE_URL/ledger/entries/ORIGINAL_ENTRY_ID/reversal" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Incorrect amount posted - should be 12000"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "_id": "REVERSAL_ENTRY_ID",
    "entryNumber": "JE-20240315-0002",
    "status": "POSTED",
    "description": "Reversal of JE-20240315-0001 - Incorrect amount posted",
    "reference": "REV-JE-20240315-0001",
    "reference_entry_id": "ORIGINAL_ENTRY_ID",
    "lines": [
      {
        "account": "CASH_ID",
        "debit": "10000.00",
        "credit": "0",
        "description": "REVERSAL: Cash payment"
      },
      {
        "account": "RENT_EXPENSE_ID",
        "debit": "0",
        "credit": "10000.00",
        "description": "REVERSAL: Rent Expense"
      }
    ]
  }
}
```

### Step 4: Verify Net Effect

```bash
# Get account balance for Rent Expense
curl -X GET "$BASE_URL/ledger/balances?accountType=Expense" \
  -H "Authorization: Bearer $TOKEN"

# Should show net effect of 0 for Rent Expense
```

---

## Additional Tests

### Test 1: Inter-State GST (IGST)

```bash
curl -X POST "$BASE_URL/ledger/entries" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-03-15",
    "description": "Sale to XYZ Ltd - Inter-state",
    "lines": [
      {
        "account": "REPLACE_WITH_AR_ID",
        "debit": "1180.00",
        "credit": "0",
        "description": "Accounts Receivable"
      },
      {
        "account": "REPLACE_WITH_REVENUE_ID",
        "debit": "0",
        "credit": "1000.00",
        "description": "Revenue"
      },
      {
        "account": "REPLACE_WITH_OUTPUT_IGST_ID",
        "debit": "0",
        "credit": "180.00",
        "description": "Output IGST @ 18%"
      }
    ],
    "gstDetails": [
      {
        "transaction_type": "sale",
        "amount": "1000.00",
        "gst_rate": 18,
        "supplier_state": "DL",
        "company_state": "MH",
        "taxable_value": "1000.00",
        "cgst": "0.00",
        "sgst": "0.00",
        "igst": "180.00"
      }
    ],
    "source": "MANUAL",
    "reference": "INV-002"
  }'
```

### Test 2: Credit Note

```bash
curl -X POST "$BASE_URL/ledger/credit-notes" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000,
    "gst_rate": 18,
    "supplier_state": "MH",
    "company_state": "MH",
    "reference": "INV-001",
    "description": "Sales return - defective goods",
    "customerName": "ABC Pvt Ltd",
    "date": "2024-03-20"
  }'
```

### Test 3: Debit Note

```bash
curl -X POST "$BASE_URL/ledger/debit-notes" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000,
    "expenseAccountCode": "6100",
    "reference": "BILL-001",
    "description": "Additional charges for services",
    "date": "2024-03-20"
  }'
```

### Test 4: Verify Hash-Chain

```bash
curl -X GET "$BASE_URL/ledger/verify-chain" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "isValid": true,
    "totalEntries": 100,
    "errors": [],
    "lastHash": "abc123...",
    "chainLength": 100,
    "message": "Ledger chain is valid and tamper-proof"
  }
}
```

### Test 5: Get Ledger Summary

```bash
curl -X GET "$BASE_URL/ledger/summary" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "success": true,
  "data": {
    "assets": "500000.00",
    "liabilities": "200000.00",
    "equity": "250000.00",
    "income": "100000.00",
    "expenses": "50000.00",
    "netIncome": "50000.00",
    "isBalanced": true,
    "balanceDifference": "0.00"
  }
}
```

---

## Validation Tests

### Test Invalid GST (Mixed Tax Types)

```bash
# This should FAIL validation
curl -X POST "$BASE_URL/ledger/entries" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-03-15",
    "description": "Invalid entry - mixed GST",
    "lines": [
      {
        "account": "AR_ID",
        "debit": "1180.00",
        "credit": "0"
      },
      {
        "account": "REVENUE_ID",
        "debit": "0",
        "credit": "1000.00"
      },
      {
        "account": "OUTPUT_CGST_ID",
        "debit": "0",
        "credit": "90.00"
      },
      {
        "account": "OUTPUT_IGST_ID",
        "debit": "0",
        "credit": "90.00"
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
        "sgst": "0.00",
        "igst": "90.00"
      }
    ]
  }'
```

**Expected Error:**
```json
{
  "success": false,
  "error": {
    "code": "GST_VALIDATION_ERROR",
    "message": "Mixed GST tax types are not allowed",
    "details": {
      "entryId": "..."
    }
  }
}
```

### Test Unbalanced Entry

```bash
# This should FAIL validation
curl -X POST "$BASE_URL/ledger/entries" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-03-15",
    "description": "Unbalanced entry",
    "lines": [
      {
        "account": "EXPENSE_ID",
        "debit": "1000.00",
        "credit": "0"
      },
      {
        "account": "CASH_ID",
        "debit": "0",
        "credit": "900.00"
      }
    ]
  }'
```

**Expected Error:**
```json
{
  "success": false,
  "error": {
    "message": "Journal not balanced"
  }
}
```

---

## Performance Tests

### Bulk Entry Creation

```bash
# Create 100 entries in sequence
for i in {1..100}; do
  curl -X POST "$BASE_URL/ledger/entries" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"date\": \"2024-03-15\",
      \"description\": \"Test entry $i\",
      \"lines\": [
        {
          \"account\": \"EXPENSE_ID\",
          \"debit\": \"1000.00\",
          \"credit\": \"0\"
        },
        {
          \"account\": \"CASH_ID\",
          \"debit\": \"0\",
          \"credit\": \"1000.00\"
        }
      ]
    }"
done
```

---

## Cleanup

### Void an Entry (if needed)

```bash
curl -X POST "$BASE_URL/ledger/entries/ENTRY_ID/void" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Test entry - cleanup"
  }'
```

---

## Notes

1. Replace all `REPLACE_WITH_*_ID` placeholders with actual MongoDB ObjectIds
2. All amounts use string format for precision (e.g., "1000.00")
3. Dates are in ISO 8601 format (YYYY-MM-DD)
4. All entries go through: CREATE → VALIDATE → POST workflow
5. Posted entries cannot be modified, only reversed

---

## Success Criteria

✅ All three proof scenarios execute successfully  
✅ GST summary shows correct output tax and input credit  
✅ TDS summary shows correct deductions  
✅ Reversal entry creates zero net effect  
✅ Hash-chain verification passes  
✅ Ledger remains balanced (Assets = Liabilities + Equity)  
✅ Audit trail captures all actions  

---

**Last Updated:** 2024-03-15  
**Version:** 1.0.0
