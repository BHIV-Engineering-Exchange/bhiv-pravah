# Bank Statement Upload Feature

## Overview
Upload bank account statements (CSV format) to automatically extract transactions and create expenses in the system.

## Features

### 1. Upload Statements
- **Supported Formats**: CSV, Excel (XLS/XLSX), PDF
- **Maximum File Size**: 25MB
- **Recommended Format**: CSV for best results

### 2. Automatic Processing
The system automatically:
- Parses transaction data from your statement
- Categorizes transactions (debit/credit)
- Identifies payees from descriptions
- Matches transactions with existing expenses

### 3. Transaction Matching
- Automatically matches bank transactions with recorded expenses
- Shows unmatched transactions for manual review
- Allows bulk creation of expenses from unmatched transactions

### 4. Expense Creation
- Select unmatched transactions
- Create multiple expenses at once
- Expenses are pre-filled with transaction details
- Created expenses follow normal approval workflow

## How to Use

### Step 1: Export from Bank
1. Login to your bank's internet banking portal
2. Navigate to account statements/transaction history
3. Select the date range you want
4. Export/download as CSV (preferred) or Excel

### Step 2: Upload to System
1. Go to **Statements → Upload Statement**
2. Fill in account details:
   - Bank name
   - Account number
   - Account holder name
   - Statement period
   - Opening and closing balances
3. Upload the exported file
4. Click "Upload Statement"

### Step 3: Process Transactions
1. View uploaded statement in **Statements** list
2. Wait for automatic processing (or click "Process" manually)
3. Once processed, click on the statement to view transactions

### Step 4: Match & Create Expenses
1. Click "Match Transactions" to auto-match with existing expenses
2. Review matched transactions
3. Select unmatched debit transactions
4. Click "Create Expenses" to bulk create expense entries
5. Created expenses will appear in **Expenses → Approval Queue**

## CSV Format Requirements

### Required Columns
The system looks for these column names (case-insensitive):

| Your Column Name | Maps To | Examples |
|-----------------|---------|----------|
| Date | Transaction Date | `Date`, `Transaction Date`, `Txn Date`, `Value Date` |
| Description | Transaction Details | `Description`, `Particulars`, `Narration`, `Details` |
| Debit | Money Out | `Debit`, `Withdrawal`, `Out`, `Amount` |
| Credit | Money In | `Credit`, `Deposit`, `In` |
| Balance | Running Balance (optional) | `Balance`, `Running Balance` |
| Reference | Reference Number (optional) | `Reference`, `Ref No`, `Cheque No`, `Txn Id` |

### Example CSV Structure
```csv
Date,Description,Debit,Credit,Balance
01/04/2025,OPENING BALANCE,,,50000.00
02/04/2025,OFFICE SUPPLIES - STORE,1500.00,,48500.00
03/04/2025,SALARY PAYMENT,25000.00,,23500.00
05/04/2025,CUSTOMER PAYMENT ABC LTD,,10000.00,33500.00
```

### Sample Files by Bank

#### HDFC Bank
```csv
Transaction Date,Particulars,Debit Amount,Credit Amount,Balance
01-Apr-2025,To Salary Payment,50000.00,,
02-Apr-2025,By Customer Receipt,,25000.00,
```

#### ICICI Bank
```csv
Date,Description,Withdrawal,Deposit,Balance
01/04/2025,RENT PAYMENT,15000.00,,
02/04/2025,SALE PROCEEDS,,30000.00,
```

#### SBI
```csv
Txn Date,Narration,Dr,Cr,Balance
01.04.2025,NEFT - Vendor Payment,8500.00,,
02.04.2025,IMPS Credit,,-5000.00,
```

## Transaction Categories

The system automatically categorizes transactions:

### Debit Transactions
- **Payment**: Regular vendor/customer payments
- **Transfer**: Bank transfers
- **Fee**: Bank charges and fees
- **Withdrawal**: Cash withdrawals
- **Other**: Uncategorized

### Credit Transactions
- **Deposit**: Customer payments and deposits
- **Interest**: Interest earned
- **Refund**: Refunds received
- **Transfer**: Incoming transfers
- **Other**: Uncategorized

## Tips for Best Results

1. **Use CSV Format**: CSV files parse most accurately
2. **Check Date Format**: Ensure dates are in standard format (DD/MM/YYYY or MM/DD/YYYY)
3. **Separate Debit/Credit**: Have separate columns for debits and credits
4. **Clean Data**: Remove any header/footer rows from exported files
5. **Complete Data**: Include all columns - don't hide columns before export

## Troubleshooting

### File Upload Fails
- Check file size (max 25MB)
- Ensure file is CSV, XLS, XLSX, or PDF format
- Try re-exporting from bank portal

### Processing Errors
- Verify CSV has required columns (Date, Description, Debit/Credit)
- Check for special characters or unusual formatting
- Ensure dates are recognizable

### Missing Transactions
- Check if transactions were already entered manually
- Review date range covers all transactions
- Verify no duplicate filtering occurred

### Matching Issues
- Transactions match based on amount and date (±3 days)
- Ensure expense amounts match bank statement exactly
- Check that expenses are approved/recorded status

## API Endpoints

### Upload Statement
```
POST /api/v1/statements/upload
Content-Type: multipart/form-data

FormData:
- statement: [file]
- accountNumber: string
- bankName: string
- accountHolderName: string
- startDate: date
- endDate: date
- openingBalance: number
- closingBalance: number
```

### Get All Statements
```
GET /api/v1/statements
Query Params:
- page: number
- limit: number
- status: pending|processing|completed|failed
- dateFrom: date
- dateTo: date
```

### Get Statement Details
```
GET /api/v1/statements/:id
```

### Process Statement
```
POST /api/v1/statements/:id/process
```

### Match Transactions
```
POST /api/v1/statements/:id/match
```

### Create Expenses from Transactions
```
POST /api/v1/statements/:id/create-expenses
Body: {
  transactionIds: [string]
}
```

## Security & Permissions

- **View Statements**: All authenticated users
- **Upload Statements**: Admin and Accountant roles
- **Process Statements**: Admin and Accountant roles
- **Create Expenses**: Admin and Accountant roles

## Database Model

### BankStatement Schema
```javascript
{
  statementNumber: String (unique),
  accountNumber: String,
  bankName: String,
  accountHolderName: String,
  startDate: Date,
  endDate: Date,
  openingBalance: Decimal,
  closingBalance: Decimal,
  file: {
    filename: String,
    path: String,
    mimetype: String,
    size: Number
  },
  transactions: [{
    date: Date,
    description: String,
    reference: String,
    debit: Decimal,
    credit: Decimal,
    balance: Decimal,
    type: 'debit' | 'credit',
    category: String,
    payee: String,
    matched: Boolean,
    matchedExpenseId: ObjectId (ref: 'Expense')
  }],
  status: 'pending' | 'processing' | 'completed' | 'failed',
  totalDebits: Decimal,
  totalCredits: Decimal,
  transactionCount: Number,
  uploadedBy: ObjectId (ref: 'User'),
  processedAt: Date
}
```

## Future Enhancements

- [ ] Excel file parsing support (requires xlsx package)
- [ ] PDF file parsing support (requires pdf-parse package)
- [ ] Advanced matching algorithms (fuzzy matching on descriptions)
- [ ] Recurring transaction detection
- [ ] Auto-categorization learning from past expenses
- [ ] Multi-currency support
- [ ] Bank API integrations for direct fetch

## Support

For issues or questions:
1. Check this documentation first
2. Review error messages in the UI
3. Contact support with statement format sample (remove sensitive data)
