# ARTHA MongoDB Cluster - Complete Setup Guide

## 🎯 Overview

This guide will help you set up a fresh MongoDB cluster for ARTHA with proper data structure and integrity.

## 📋 Prerequisites

- MongoDB Atlas account (free tier available)
- Node.js 18+ installed
- ARTHA backend code

## 🚀 Step-by-Step Setup

### Step 1: Create MongoDB Atlas Cluster

1. **Go to MongoDB Atlas**
   - Visit: https://cloud.mongodb.com/
   - Sign in or create account

2. **Create New Cluster**
   ```
   - Click "Build a Database"
   - Choose: M0 FREE (or M10+ for production)
   - Cluster Name: artha-cluster
   - Region: Choose closest to you
   - Click "Create"
   ```

3. **Configure Network Access**
   ```
   - Go to "Network Access"
   - Click "Add IP Address"
   - Choose "Allow Access from Anywhere" (0.0.0.0/0)
   - Or add specific IPs for security
   ```

4. **Create Database User**
   ```
   - Go to "Database Access"
   - Click "Add New Database User"
   - Username: artha_admin
   - Password: [Generate strong password]
   - Role: Atlas Admin
   - Click "Add User"
   ```

5. **Get Connection String**
   ```
   - Click "Connect" on cluster
   - Choose "Connect your application"
   - Copy connection string:
   
   mongodb+srv://artha_admin:<password>@artha-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### Step 2: Configure Environment

Update `backend/.env`:

```env
# MongoDB Connection
MONGODB_URI=mongodb+srv://artha_admin:YOUR_PASSWORD@artha-cluster.xxxxx.mongodb.net/artha_production?retryWrites=true&w=majority

# Admin Credentials
ADMIN_EMAIL=admin@artha.local
ADMIN_PASSWORD=Admin@123456

# JWT Secrets (generate strong secrets)
JWT_SECRET=your-super-secret-jwt-key-minimum-32-characters
JWT_REFRESH_SECRET=your-super-secret-refresh-key-minimum-32-characters
HMAC_SECRET=your-super-secret-hmac-key-for-ledger-chain
```

### Step 3: Initialize Database

Run the initialization script:

```bash
cd backend
node scripts/initialize-database.js
```

**For fresh setup (drops existing data):**
```bash
node scripts/initialize-database.js --drop
```

This will:
- ✅ Create all collections
- ✅ Create indexes for performance
- ✅ Seed chart of accounts (28 accounts)
- ✅ Create default company settings
- ✅ Create admin user

### Step 4: Verify Setup

```bash
# Test database connection
node scripts/test-invoice-expense-integration.js
```

Expected output:
```
✅ Connected to MongoDB
✅ Invoice created: INV-YYYYMMDD-0001
✅ Expense created: EXP-000001
✅ Hash chain integrity: VALID
```

## 📊 Database Structure

### Collections Created

1. **users** - User accounts and authentication
2. **chartofaccounts** - Account structure (28 default accounts)
3. **journalentries** - Double-entry ledger with hash-chain
4. **invoices** - Customer invoices
5. **expenses** - Expense management
6. **accountbalances** - Real-time account balances
7. **companysettings** - Company configuration
8. **gstreturns** - GST filing data
9. **tdsentries** - TDS deductions
10. **auditlogs** - Audit trail

### Default Chart of Accounts

**Assets (1000-1999)**
- 1010: Cash
- 1020: Bank Account
- 1100: Accounts Receivable
- 1500: Inventory
- 1800: Equipment

**Liabilities (2000-2999)**
- 2100: Accounts Payable
- 2200: Tax Payable
- 2300: GST Payable
- 2400: TDS Payable

**Equity (3000-3999)**
- 3100: Owner's Capital
- 3200: Retained Earnings

**Income (4000-4999)**
- 4100: Sales Revenue
- 4200: Service Revenue
- 4900: Other Income

**Expenses (6000-6999)**
- 6100: Rent Expense
- 6200: Utilities Expense
- 6300: Office Supplies
- 6400: Salaries Expense
- 6500: Marketing Expense
- 6600: Insurance Expense
- 6700: Professional Services
- 6800: Travel Expense
- 6900: Miscellaneous Expense

## 🔒 Data Integrity Features

### 1. Hash-Chain Ledger
- Every journal entry linked with HMAC-SHA256
- Tamper-evident audit trail
- Chain position tracking
- Automatic verification

### 2. Indexes for Performance
- Optimized queries on all collections
- Compound indexes for common filters
- Unique constraints on critical fields

### 3. Validation Rules
- Schema-level validation
- Business logic validation
- Double-entry accounting rules
- Required field enforcement

## 🔄 Backup & Restore

### Create Backup

```bash
node scripts/backup-database.js
```

Backup saved to: `backend/backups/YYYY-MM-DD-HH-MM-SS/`

### Restore from Backup

```bash
# Manual restore using MongoDB Compass or mongorestore
mongorestore --uri="YOUR_MONGODB_URI" --dir="./backups/TIMESTAMP"
```

## 🧪 Testing Data Integrity

### 1. Test Invoice Flow
```bash
curl -X POST http://localhost:5000/api/v1/invoices \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customerName": "Test Customer",
    "customerEmail": "test@example.com",
    "invoiceDate": "2026-02-14",
    "dueDate": "2026-03-14",
    "items": [{"description": "Service", "quantity": 1, "unitPrice": "1000", "amount": "1000"}],
    "subtotal": "1000",
    "taxAmount": "180",
    "totalAmount": "1180"
  }'
```

### 2. Verify Ledger Integrity
```bash
curl http://localhost:5000/api/v1/ledger/verify-chain \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Check Account Balances
```bash
curl http://localhost:5000/api/v1/ledger/balances \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📈 Monitoring

### MongoDB Atlas Dashboard
- Go to your cluster
- Click "Metrics" tab
- Monitor:
  - Operations per second
  - Connections
  - Network traffic
  - Storage usage

### Application Logs
```bash
tail -f backend/logs/combined.log
```

## 🔧 Maintenance

### Regular Tasks

1. **Weekly Backup**
   ```bash
   node scripts/backup-database.js
   ```

2. **Verify Chain Integrity**
   ```bash
   curl http://localhost:5000/api/v1/ledger/verify-chain
   ```

3. **Check Database Size**
   - Monitor in MongoDB Atlas dashboard
   - Optimize indexes if needed

### Troubleshooting

**Connection Issues:**
```bash
# Test connection
node -e "require('mongoose').connect(process.env.MONGODB_URI).then(() => console.log('✅ Connected')).catch(e => console.error('❌', e))"
```

**Slow Queries:**
- Check indexes in MongoDB Atlas
- Review query patterns in logs
- Add indexes if needed

## 🎯 Production Checklist

- [ ] MongoDB Atlas cluster created
- [ ] Network access configured
- [ ] Database user created with strong password
- [ ] Environment variables set
- [ ] Database initialized
- [ ] Admin user created
- [ ] Chart of accounts seeded
- [ ] Integration tests passed
- [ ] Backup script tested
- [ ] Monitoring configured
- [ ] SSL/TLS enabled (Atlas default)
- [ ] IP whitelist configured (if not using 0.0.0.0/0)
- [ ] **BHIV ecosystem integration verified**
- [ ] **Governance API endpoints tested**
- [ ] **Circuit breakers configured**
- [ ] **Provenance chain initialized**

## 🏛️ BHIV Ecosystem Integration

### Services Initialized at Startup
- **Capability Registry**: Loads all capability contracts into memory
- **Provenance Chain**: Genesis block created with hash and timestamp
- **Deterministic Replay**: Ready for governance replay operations
- **Deployment Evidence**: Initial evidence generated

### Governance API Endpoints (19 Total)
```bash
# Get governance status
curl http://localhost:5000/api/v1/governance/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get capabilities
curl http://localhost:5000/api/v1/governance/capabilities \
  -H "Authorization: Bearer YOUR_TOKEN"

# Verify provenance chain
curl http://localhost:5000/api/v1/governance/provenance/verify \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get circuit breakers
curl http://localhost:5000/api/v1/governance/circuit-breakers \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Circuit Breakers (6 Configured)
| Service | Failure Threshold | Reset Timeout | Description |
|---------|-------------------|---------------|-------------|
| mongodb | 3 failures | 30 seconds | Database resilience |
| redis | 3 failures | 30 seconds | Cache resilience |
| setu_api | 3 failures | 120 seconds | External API resilience |
| tantra_runtime | 3 failures | 60 seconds | TANTRA integration |
| ocr_service | 3 failures | 60 seconds | OCR processing |
| evidence_pipeline | 3 failures | 60 seconds | Evidence generation |

### Provenance Chain
- Immutable, append-only, hash-linked governance decision chain
- Genesis block initialized at startup
- SHA-256 hash verification for integrity
- All governance decisions recorded

### Documentation
- `docs/RUNTIME_ARCHITECTURE.md` — BHIV runtime architecture
- `docs/INTEGRATION_GUIDE.md` — BHIV integration guide
- `docs/DEPLOYMENT_GUIDE.md` — BHIV deployment guide
- `docs/OPERATIONS_GUIDE.md` — BHIV operations guide
- `docs/INCIDENT_RECOVERY_GUIDE.md` — Incident recovery procedures
- `docs/AUTHORITY_BOUNDARY_GUIDE.md` — Authority boundaries
- `docs/CAPABILITY_REGISTRATION_GUIDE.md` — Capability registration


## 📞 Support

**MongoDB Atlas Issues:**
- Support: https://support.mongodb.com/
- Documentation: https://docs.atlas.mongodb.com/

**ARTHA Issues:**
- Check logs: `backend/logs/`
- Run tests: `npm test`
- Verify setup: `node scripts/initialize-database.js`

---

**Last Updated**: July 04, 2026  
**Status**: Production Ready - BHIV Ecosystem Integrated ✓  


## ✅ Success Criteria

Your setup is complete when:
- ✅ Database connection successful
- ✅ All collections created
- ✅ Indexes created
- ✅ Admin user can login
- ✅ Invoice creation works
- ✅ Expense creation works
- ✅ Ledger chain valid
- ✅ Account balances update correctly

---

**Status: Ready for Production** 🚀
