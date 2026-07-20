# Bank Statement Upload - Quick Start Guide

## 🎯 What This Does

Upload your bank account statement (CSV file) and the system will:
1. **Automatically extract** all transactions
2. **Categorize** debits and credits
3. **Match** with existing expenses
4. **Create new expenses** from unmatched transactions

## 📋 Prerequisites

- Bank statement exported as CSV (recommended), Excel, or PDF
- Admin or Accountant role in the system
- Bank internet banking credentials

## 🚀 Quick Start

### Step 1: Export Bank Statement

#### HDFC Bank
1. Login to [HDFC NetBanking](https://netbanking.hdfcbank.com)
2. Go to **Accounts** → **Download Statement**
3. Select account and date range
4. Choose **CSV** format
5. Click **Download**

#### ICICI Bank
1. Login to [ICICI Internet Banking](https://infinity.icicibank.co.in)
2. Click **Accounts & Save** → **Download Transaction History**
3. Select period
4. Choose **CSV** format
5. Download

#### SBI
1. Login to [Yono SBI](https://yonosbi.sbi) or Internet Banking
2. Go to **Accounts** → **Transaction History**
3. Select date range
4. Download as CSV/Excel
5. If Excel, convert to CSV (File → Save As → CSV)

#### Other Banks
Look for options like:
- "Download Statement"
- "Transaction History"
- "Account Statement"
- Export format: **CSV preferred**, Excel acceptable

### Step 2: Upload to Artha

1. **Navigate to Statements**
   - Click **Statements** in the sidebar
   - Select **Upload Statement**

2. **Fill Account Details**
   ```
   Bank Name: HDFC Bank
   Account Number: 1234567890
   Account Holder Name: Your Company Name
   ```

3. **Enter Statement Period**
   ```
   Start Date: 01/04/2025
   End Date: 30/04/2025
   Opening Balance: 50000.00
   Closing Balance: 41250.00
   ```

4. **Upload File**
   - Drag & drop CSV file OR
   - Click "browse" to select file
   - Maximum size: 25MB

5. **Click "Upload Statement"**
   - Processing starts automatically
   - Takes 10-30 seconds typically

### Step 3: Process & Review

1. **Wait for Processing**
   - Status changes: Pending → Processing → Completed
   - Refresh list if needed

2. **View Statement**
   - Click on statement number or eye icon
   - See all transactions listed

3. **Match Transactions**
   - Click **"Match Transactions"** button
   - System finds matching expenses
   - Shows matched/unmatched status

### Step 4: Create Expenses

1. **Select Unmatched Transactions**
   - Check boxes next to debit transactions
   - Or click **"Select All Unmatched"**

2. **Create Expenses**
   - Click **"Create Expenses"** button
   - System creates expense entries
   - Pre-filled with transaction details

3. **Review Created Expenses**
   - Go to **Expenses** → **All Expenses**
   - Look for notes: "From bank statement: STMT-XXXXXX"
   - Approve and record as normal

## 📊 CSV Format Guide

### Required Columns

Your CSV should have these columns (names may vary):

| What You Need | Column Names Banks Use | Example |
|--------------|----------------------|---------|
| **Date** | Date, Transaction Date, Txn Date, Value Date | 01/04/2025 |
| **Description** | Description, Particulars, Narration, Details | OFFICE SUPPLIES |
| **Debit** | Debit, Withdrawal, Out, Amount, Dr | 1500.00 |
| **Credit** | Credit, Deposit, In, Cr | 10000.00 |
| **Balance** (optional) | Balance, Running Balance | 50000.00 |
| **Reference** (optional) | Reference, Ref No, Cheque No, Txn Id | CHQ123456 |

### Sample CSV Structure

```csv
Date,Description,Reference,Debit,Credit,Balance
01/04/2025,OPENING BALANCE,,,50000.00
02/04/2025,OFFICE SUPPLIES STORE,CHQ123456,1500.00,,48500.00
05/04/2025,CUSTOMER PAYMENT ABC,NEFT789,,10000.00,58500.00
```

### Common Bank Formats

**HDFC:**
```csv
Transaction Date,Particulars,Debit Amount,Credit Amount,Balance
01-Apr-2025,SALARY PAYMENT,50000.00,,
```

**ICICI:**
```csv
Date,Description,Withdrawal,Deposit,Balance
01/04/2025,RENT PAYMENT,15000.00,,
```

**SBI:**
```csv
Txn Date,Narration,Dr,Cr,Balance
01.04.2025,VENDOR PAYMENT,8500.00,,
```

## ✅ Best Practices

### Do's
- ✅ Use CSV format when possible
- ✅ Export full statement period
- ✅ Include all columns (don't hide)
- ✅ Check dates are in standard format
- ✅ Remove any custom headers/footers added by bank

### Don'ts
- ❌ Don't manually edit CSV in Excel (can corrupt formatting)
- ❌ Don't delete columns before upload
- ❌ Don't upload password-protected files
- ❌ Don't merge multiple statements in one file

## 🔧 Troubleshooting

### "Invalid file type" Error
**Solution:** Ensure file is .csv, .xls, .xlsx, or .pdf
- Re-export from bank
- Save Excel as CSV: File → Save As → CSV (Comma delimited)

### "Processing Failed" Error
**Possible causes:**
- Missing required columns (Date, Description, Debit/Credit)
- Unrecognizable date format
- Corrupted file

**Solutions:**
1. Open CSV in text editor (Notepad)
2. Verify first row has column headers
3. Check dates look like: 01/04/2025 or 01-Apr-2025
4. Re-export from bank if needed

### No Transactions Showing
**Check:**
- File isn't empty
- Correct file was uploaded
- Processing completed (status = Completed)
- Refresh page

### Transactions Not Matching
**Why:**
- Amount doesn't match exactly (check decimals)
- Date difference > 3 days
- Expense not yet recorded in system

**Fix:**
- Create expenses manually from unmatched transactions
- System will auto-match future transactions

## 📱 Mobile Banking Apps

Most banks allow statement export from mobile apps too:

**HDFC MobileBanking:**
- Accounts → Download e-Statement → Email to yourself

**ICICI iMobile:**
- Accounts → Transaction History → Share → CSV

**SBI Yono:**
- Accounts → View Transaction → Export → CSV

## 🎓 Video Tutorials

*(Add links to video tutorials if available)*

## 📞 Support

Need help?
1. Check [BANK_STATEMENTS_FEATURE.md](./BANK_STATEMENTS_FEATURE.md) for detailed docs
2. Review error message in the UI
3. Contact support team

## 🔄 What Happens Behind the Scenes

1. **Upload** → File stored securely in `uploads/statements/`
2. **Parse** → CSV reader extracts transactions
3. **Categorize** → AI identifies transaction types
4. **Match** → Compares with existing expenses
5. **Store** → Saves to database with cryptographic hash
6. **Link** → Creates audit trail in ledger

## 🔒 Security

- Files stored encrypted
- Access restricted by role
- Full audit trail maintained
- Bank data never shared externally

## 📈 Next Steps

After uploading statements:
1. Review created expenses
2. Approve/reject as needed
3. Record in ledger
4. Generate reports
5. File GST (if applicable)

---

**Ready to try?** Go to **Statements → Upload Statement** and get started!
