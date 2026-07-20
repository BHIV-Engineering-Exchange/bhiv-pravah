# ARTHA v0.1 - Live Demo Scenarios

This document provides step-by-step scenarios to demonstrate all features of ARTHA v0.1.

## Prerequisites

- System running: `docker-compose -f docker-compose.dev.yml up -d`
- Database seeded: `docker exec artha-backend-dev npm run seed`
- Frontend accessible: http://localhost:5173
- Backend API: http://localhost:5000

---

## Scenario 1: Login & Dashboard Overview (3 mins)

### Steps:
1. Navigate to http://localhost:5173
2. Login with:
   - Email: `admin@artha.local`
   - Password: `Admin@123456`
3. Observe Dashboard:
   - KPI cards (Assets, Income, Expenses, Net Income)
   - Balance sheet summary
   - Recent invoices
   - Recent expenses
   - Ledger integrity status (NEW)
4. Check system health:
   - Click "System" in navigation
   - Observe health status and memory usage

### Key Points to Show:
- "Real-time updates without page refresh"
- "All figures are calculated from the ledger in real-time"
- "System health is continuously monitored"

---

## Scenario 2: Ledger Hash-Chain Verification (4 mins)

### Steps:
1. Navigate to Ledger page
2. View "Ledger Integrity Status" widget
3. Click "Verify Chain" button:
   - Shows total entries verified
   - Confirms chain is valid
   - Shows last hash
4. Navigate to Reports → Trial Balance:
   - Generates on-the-fly
   - Shows debit/credit totals
5. Verify Balance Sheet is balanced:
   - Assets = Liabilities + Equity

### Key Points to Show:
- "Every entry is linked with cryptographic hash"
- "Entire chain can be verified in one click"
- "Tampering is immediately detected"
- "Audit trail includes who posted when"

**CURL Examples**:
```bash
# Verify entire chain
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/v1/ledger/verify-chain

# Verify single entry
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/v1/ledger/entries/ENTRY_ID/verify

# Get chain segment (for audit)
curl -H "Authorization: Bearer $TOKEN" "http://localhost:5000/api/v1/ledger/chain-segment?startPosition=0&endPosition=10"
```

---

## Scenario 3: Invoice Creation → Payment Flow (5 mins)

### Steps:
1. Navigate to Invoices
2. Click "+ New Invoice"
3. Fill in details:
   - Customer: "Demo Corp"
   - Date: Today
   - Due: 15 days out
   - Add line: Description "Consulting Services", Qty 5, Price 1000, Tax 18%
4. Create invoice (stays in draft)
5. Click "Send":
   - Shows automatic AR journal entry created
   - Invoice moves to "sent"
6. Record partial payment (3000):
   - Shows payment recorded
   - AR balance reduces
7. Record remaining payment:
   - Invoice moves to "paid"
   - Final ledger entry shows

### Key Points to Show:
- "Invoice creates double-entry AR debit and Sales credit"
- "Payment automatically updates balances"
- "Full audit trail of all changes"

**CURL Example**:
```bash
# Create invoice
curl -X POST -H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "invoiceDate": "2025-02-05",
  "dueDate": "2025-02-20",
  "customerName": "Demo Corp",
  "lines": [{
    "description": "Service",
    "quantity": 1,
    "unitPrice": "5000",
    "taxRate": 18
  }]
}' \
http://localhost:5000/api/v1/invoices

# Send invoice
curl -X POST -H "Authorization: Bearer $TOKEN" \
http://localhost:5000/api/v1/invoices/INVOICE_ID/send

# Record payment
curl -X POST -H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "amount": "5900",
  "paymentMethod": "bank_transfer",
  "reference": "NEFT-12345"
}' \
http://localhost:5000/api/v1/invoices/INVOICE_ID/payment
```

---

## Scenario 4: Expense Creation with OCR Scanning (5 mins)

### Steps:
1. Navigate to Expenses
2. Click "📸 Scan Receipt"
3. OCR Receipt component appears
4. Upload a receipt image (or use test):
   - Shows preview of image
   - Processes and extracts data
   - Shows confidence score
5. Review extracted data:
   - Vendor: Extracted
   - Date: Extracted
   - Amount: Extracted
   - Tax: Extracted
6. Confirm and create expense:
   - Fields pre-filled from OCR
   - User can edit if needed
7. Submit expense:
   - Moves to "pending"
   - Admin needs to approve
8. Approve as admin:
   - Click "Approve"
9. Record expense:
   - Creates ledger entry (Expense debit, Payable credit)
   - Expense moves to "recorded"

### Key Points to Show:
- "OCR saves data entry time"
- "Confidence score shows extraction quality"
- "Manual review step prevents errors"
- "Approval workflow ensures control"

**CURL Examples**:
```bash
# Check OCR status
curl -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/v1/expenses/ocr/status

# Process receipt (with file upload)
curl -X POST -H "Authorization: Bearer $TOKEN" \
-F "receipt=@receipt.jpg" \
http://localhost:5000/api/v1/expenses/ocr

# Approve expense
curl -X POST -H "Authorization: Bearer $TOKEN" \
http://localhost:5000/api/v1/expenses/EXPENSE_ID/approve

# Record expense
curl -X POST -H "Authorization: Bearer $TOKEN" \
http://localhost:5000/api/v1/expenses/EXPENSE_ID/record
```

---

## Scenario 5: GST Filing Packet Generation (4 mins)

### Steps:
1. Navigate to Dashboard
2. Scroll to "GST Summary" widget
3. Select period (e.g., 2025-02):
   - Outward tax: Shows total GST collected
   - Input credit: Shows eligible input tax
   - Net payable: Shows net GST due
4. Click "Export GSTR-1":
   - Downloads CSV of invoices for the period
   - Shows B2B/B2C/Export breakdown
5. Click "Export GSTR-3B":
   - Downloads CSV of tax summary
   - Shows CGST/SGST/IGST split
   - Shows net liability calculation

### Key Points to Show:
- "Ready-to-file GST packets"
- "Compatible with CA software"
- "All calculations built in"
- "One-click export"

**CURL Examples**:
```bash
# Get GST summary
curl -H "Authorization: Bearer $TOKEN" \
"http://localhost:5000/api/v1/gst/summary?period=2025-02"

# Get GSTR-1 packet
curl -H "Authorization: Bearer $TOKEN" \
"http://localhost:5000/api/v1/gst/filing-packet/gstr-1?period=2025-02"

# Get GSTR-3B packet
curl -H "Authorization: Bearer $TOKEN" \
"http://localhost:5000/api/v1/gst/filing-packet/gstr-3b?period=2025-02"

# Export as CSV
curl -H "Authorization: Bearer $TOKEN" \
"http://localhost:5000/api/v1/gst/filing-packet/export?type=gstr-1&period=2025-02" \
> gstr1-2025-02.csv
```

---

## Scenario 6: Financial Reports (6 mins)

### Steps:
1. Navigate to Reports page
2. Generate P&L (Profit & Loss):
   - Select date range: 2025-01-01 to 2025-12-31
   - Shows Income section
   - Shows Expense section
   - Shows Net Income (positive = profit)
3. Generate Balance Sheet:
   - Select date: 2025-12-31
   - Shows Assets (Cash, AR, etc.)
   - Shows Liabilities (AP, etc.)
   - Shows Equity
   - Shows accounting equation: Assets = Liabilities + Equity ✓
4. Generate Cash Flow:
   - Operating activities (from expenses/invoices)
   - Investing activities (from fixed assets)
   - Financing activities (from loans/capital)
   - Net cash change
5. Trial Balance:
   - Lists all accounts
   - Debits and credits must equal
   - Shows if balanced

### Key Points to Show:
- "All reports generated from single source of truth (ledger)"
- "Real-time calculations, no delays"
- "One-click PDF export"
- "Accounting equation verified automatically"

**CURL Examples**:
```bash
# P&L Report
curl -H "Authorization: Bearer $TOKEN" \
"http://localhost:5000/api/v1/reports/profit-loss?startDate=2025-01-01&endDate=2025-12-31" | jq

# Balance Sheet
curl -H "Authorization: Bearer $TOKEN" \
"http://localhost:5000/api/v1/reports/balance-sheet?asOfDate=2025-12-31" | jq

# Cash Flow
curl -H "Authorization: Bearer $TOKEN" \
"http://localhost:5000/api/v1/reports/cash-flow?startDate=2025-01-01&endDate=2025-12-31" | jq

# Trial Balance
curl -H "Authorization: Bearer $TOKEN" \
"http://localhost:5000/api/v1/reports/trial-balance?asOfDate=2025-12-31" | jq
```

---

## Scenario 7: System Health & Monitoring (2 mins)

### Steps:
1. Check basic health:
```bash
curl http://localhost:5000/health
```
Shows: API is running, version, uptime

2. Check detailed health:
```bash
curl http://localhost:5000/health/detailed
```
Shows:
- MongoDB status
- Redis status
- Memory usage
- Heap information

3. Check readiness (for Kubernetes):
```bash
curl http://localhost:5000/ready
```
Shows: 200 if ready to accept traffic

4. Check liveness (for Kubernetes):
```bash
curl http://localhost:5000/live
```
Shows: 200 if process is alive

### Key Points to Show:
- "Production-grade monitoring"
- "Kubernetes-compatible probes"
- "Real-time system metrics"
- "Automatic service detection"

---

## Demo Tips

### Smooth Transitions:
1. Pre-seed sample data with realistic invoices/expenses
2. Use consistent test period (Feb 2025)
3. Have different user roles logged in (admin vs accountant)
4. Prepare test receipt images for OCR

### Common Questions to Address:
- **"How does hash-chain prevent fraud?"** → Show verification check, explain immutability
- **"Can I edit posted entries?"** → No, they're immutable (by design)
- **"How often does OCR work?"** → Mock OCR always works, real OCR depends on image quality
- **"Is GST calculation automatic?"** → Yes, all tax is calculated real-time
- **"Can I export reports?"** → Yes, CSV and PDF supported

### Highlight Unique Features:
- ✨ Hash-chain ledger (rarely seen in accounting software)
- ✨ OCR-integrated expense entry
- ✨ Real-time GST filing packets
- ✨ Production-ready deployment with Pravah
- ✨ Complete audit trail on every transaction

---

## Full Workflow Demo (25 minutes)

If showing everything in sequence:

1. **5 min**: Dashboard & health overview
2. **4 min**: Ledger integrity verification
3. **5 min**: Create invoice, send, receive payment
4. **5 min**: Create expense with OCR scanning
5. **3 min**: Generate financial reports
6. **2 min**: GST filing packet export
7. **1 min**: Q&A

---

## Troubleshooting During Demo

| Issue | Solution |
|-------|----------|
| Backend not responding | `docker logs artha-backend-dev` |
| No data showing | `docker exec artha-backend-dev npm run seed` |
| API returns 401 | Get new token with `POST /auth/login` |
| OCR gives poor results | Use mock OCR (enabled by default in dev) |
| Reports show 0 values | Ensure invoices/expenses are recorded, not just pending |
| Hash verification fails | Restart containers: `docker-compose restart` |

---

## Demo Video Script (Optional)

If recording a video:

**[0:00-0:30]** "ARTHA v0.1 - Production-Ready Accounting System"
- Show dashboard with KPIs

**[0:30-1:30]** "Feature 1: Hash-Chain Ledger Verification"
- Click verify chain button
- Show all entries verified
- Explain tamper-proofing

**[1:30-3:00]** "Feature 2: Complete Invoice Lifecycle"
- Create invoice
- Send (auto-create AR entry)
- Record payment
- Show final ledger entries

**[3:00-4:30]** "Feature 3: OCR-Powered Expense Entry"
- Show OCR upload
- Auto-extract fields
- Confidence score
- Approve and record

**[4:30-5:30]** "Feature 4: GST Filing Ready"
- Generate GSTR-1
- Generate GSTR-3B
- Download CSV
- Show format

**[5:30-6:00]** "Built for Production"
- Show health monitoring
- Mention Docker, Kubernetes ready
- Highlight audit trail

**[6:00-7:00]** "Questions?"

Total: ~7 minutes