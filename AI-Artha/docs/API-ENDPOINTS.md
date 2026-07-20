# ARTHA API Endpoints

**Base URL**: http://localhost:5000

## 🔐 Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login user |
| GET | `/api/v1/auth/me` | Get current user |
| POST | `/api/v1/auth/logout` | Logout user |

## 📊 Chart of Accounts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/accounts` | Get all accounts |
| GET | `/api/v1/accounts/:id` | Get single account |
| POST | `/api/v1/accounts` | Create account |
| PUT | `/api/v1/accounts/:id` | Update account |
| DELETE | `/api/v1/accounts/:id` | Delete account |
| POST | `/api/v1/accounts/seed` | Seed default accounts |

## 📝 Ledger Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ledger/entries` | Get journal entries |
| GET | `/api/v1/ledger/entries/:id` | Get single entry |
| POST | `/api/v1/ledger/entries` | Create journal entry |
| POST | `/api/v1/ledger/entries/:id/post` | Post entry |
| POST | `/api/v1/ledger/entries/:id/void` | Void entry |
| GET | `/api/v1/ledger/balances` | Get account balances |
| GET | `/api/v1/ledger/summary` | Get ledger summary |
| GET | `/api/v1/ledger/verify` | Verify ledger integrity |

## 🧾 Invoices

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/invoices` | Get all invoices |
| GET | `/api/v1/invoices/stats` | Get invoice statistics |
| GET | `/api/v1/invoices/:id` | Get single invoice |
| POST | `/api/v1/invoices` | Create invoice |
| PUT | `/api/v1/invoices/:id` | Update invoice |
| POST | `/api/v1/invoices/:id/send` | Send invoice |
| POST | `/api/v1/invoices/:id/payment` | Record payment |
| POST | `/api/v1/invoices/:id/cancel` | Cancel invoice |

## 💰 Expenses

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/expenses` | Get all expenses |
| GET | `/api/v1/expenses/stats` | Get expense statistics |
| GET | `/api/v1/expenses/:id` | Get single expense |
| POST | `/api/v1/expenses` | Create expense |
| PUT | `/api/v1/expenses/:id` | Update expense |
| POST | `/api/v1/expenses/:id/approve` | Approve expense |
| POST | `/api/v1/expenses/:id/reject` | Reject expense |
| POST | `/api/v1/expenses/:id/record` | Record in ledger |

## 🇮🇳 GST & Compliance

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/gst/returns/gstr1` | Generate GSTR1 |
| GET | `/api/v1/gst/returns/gstr3b` | Generate GSTR3B |
| POST | `/api/v1/gst/file-return` | File GST return |
| GET | `/api/v1/tds/entries` | Get TDS entries |
| POST | `/api/v1/tds/entries` | Create TDS entry |
| POST | `/api/v1/tds/calculate` | Calculate TDS |

## 📈 Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reports/general-ledger` | General Ledger PDF |
| GET | `/api/v1/reports/profit-loss` | P&L Statement |
| GET | `/api/v1/reports/balance-sheet` | Balance Sheet |
| GET | `/api/v1/reports/cash-flow` | Cash Flow Statement |
| GET | `/api/v1/reports/trial-balance` | Trial Balance |

## 🏥 Health & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/detailed` | Detailed system health |
| GET | `/ready` | Readiness probe |
| GET | `/live` | Liveness probe |
| GET | `/metrics` | Performance metrics |
| GET | `/status` | System status |

## 🔧 Performance & Database

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/performance/metrics` | Performance metrics |
| GET | `/api/v1/performance/health` | Performance health |
| POST | `/api/v1/performance/reset` | Reset metrics |
| GET | `/api/v1/database/stats` | Database statistics |
| GET | `/api/v1/database/optimize` | Optimization suggestions |

## 🧪 Quick Test Commands

### Login and Get Token
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@artha.local","password":"Admin@123456"}'
```

### Test with Token
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/v1/accounts
```

### Health Check
```bash
curl http://localhost:5000/health/detailed
```