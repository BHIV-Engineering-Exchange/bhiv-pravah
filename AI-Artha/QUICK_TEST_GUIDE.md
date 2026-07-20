# Quick Test Guide

## Run All Tests (2 minutes)

### Option 1: CLI Test (Fastest)
```bash
# Ensure backend is running on :5000
node test-endpoints.js
```

### Option 2: Browser Test
```bash
# Open http://localhost:5173
# Open browser console (F12)
# Run:
runArthaTests()
```

## Expected Output

```
🚀 ARTHA Backend Integration Tests
==================================================

🔐 Testing Authentication
✅ auth.login
✅ auth.getProfile

📊 Testing Chart of Accounts
✅ accounts.getAll
✅ accounts.getById

📝 Testing Journal Entries
✅ journalEntries.getAll
✅ journalEntries.create
✅ journalEntries.getBalances
✅ journalEntries.verifyChain

🧾 Testing Invoices
✅ invoices.getAll
✅ invoices.create

💰 Testing Expenses
✅ expenses.getAll
✅ expenses.create

📈 Testing Reports
✅ reports.dashboard
✅ reports.profitLoss
✅ reports.balanceSheet

🏛️ Testing GST Compliance
✅ gst.getSummary
✅ gst.gstr1Packet

==================================================
✅ Tests completed
==================================================
```

## If Tests Fail

1. **Check backend is running**: `curl http://localhost:5000/health`
2. **Check database is initialized**: `cd backend && node scripts/initialize-database.js`
3. **Check credentials**: admin@artha.local / Admin@123456
4. **Check logs**: `cd backend && npm run dev` (watch console)

## Manual Testing

### 1. Login
- URL: http://localhost:5173/login
- Email: admin@artha.local
- Password: Admin@123456

### 2. Test Each Tab
- **Chart of Accounts**: Create account with code 9999
- **Journal Entries**: Create balanced entry (debit = credit)
- **Invoices**: Create invoice for Test Customer
- **Expenses**: Create expense with receipt
- **Reports**: View dashboard
- **GST**: View summary for period 2025-02

### 3. Expected Result
All operations succeed without errors ✅

## Troubleshooting

### "Valid account ID required"
- **Fixed**: Update `frontend/src/pages/accounting/JournalEntryCreate.jsx`
- Change `accountId` to `account` in payload mapping

### "Failed to save invoice"
- Check payload format matches backend validation
- Ensure amounts are strings, not numbers

### "Failed to save expense"
- Check category mapping (frontend → backend)
- Ensure paymentMethod is in allowed list

### "Authentication failed"
- Run database initialization: `node scripts/initialize-database.js`
- Check admin user exists in MongoDB

## Documentation

- **Full Test Results**: `INTEGRATION_TEST_RESULTS.md`
- **Fix Details**: `ACCOUNTING_TABS_FIX.md`
- **Summary**: `TABS_VERIFICATION_SUMMARY.md`
