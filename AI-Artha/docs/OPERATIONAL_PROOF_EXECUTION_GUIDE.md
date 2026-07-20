# ARTHA OPERATIONAL PROOF - EXECUTION GUIDE

**Purpose**: Complete operational verification of ARTHA system  
**Status**: Core scripts implemented, ready for execution  
**Date**: 2025-02-01

---

## 📋 OVERVIEW

This package contains **3 comprehensive verification scripts** that prove ARTHA is:
- ✅ **Documented** - All endpoints verified
- ✅ **Resilient** - All failure paths tested
- ✅ **Operational** - End-to-end business flows proven
- ✅ **Traceable** - Full lineage captured
- ✅ **Production-Ready** - Auditable and maintainable

---

## 🚀 QUICK START

### Prerequisites

```bash
# 1. Ensure ARTHA backend is running
cd backend
npm install
npm run dev  # or npm start

# 2. Ensure MongoDB is accessible
# 3. Ensure .env is configured with test credentials
```

### Run All Verifications

```bash
# From project root

# 1. Runtime Validation (15-20 tests)
node backend/scripts/runtime-validation.js

# 2. Failure Verification (8+ scenarios)
node backend/scripts/failure-verification.js

# 3. End-to-End Operational Proof (8 steps)
node backend/scripts/e2e-operational-proof.js
```

---

## 📊 SCRIPT 1: Runtime Validation

**File**: `backend/scripts/runtime-validation.js`  
**Purpose**: Validate every operational endpoint  
**Tests**: 15-20 endpoints  
**Evidence**: JSON files + markdown report

### What It Tests

1. **Health Endpoints**
   - `GET /health`
   - `GET /health/detailed`
   - `GET /ready` (Kubernetes readiness)
   - `GET /live` (Kubernetes liveness)
   - `GET /api/v1/runtime/status`

2. **Public Endpoints**
   - `GET /test`
   - `GET /api/test`
   - `GET /api/v1/auth/test`

3. **Authentication**
   - Invalid credentials (401)
   - Missing fields (400)

4. **Protected Endpoints** (no auth)
   - Ledger, Accounts, Invoices, Expenses, Signals, Reports
   - All should return 401

5. **Non-Existent Routes**
   - 404 handling

### Expected Output

```
🧪 ARTHA Runtime Validation

✅ GET /health
✅ GET /health/detailed
✅ GET /ready (Kubernetes readiness)
✅ GET /live (Kubernetes liveness)
✅ GET /api/v1/runtime/status (no auth)
✅ GET /test
✅ GET /api/test
✅ GET /api/v1/auth/test
✅ POST /api/v1/auth/login (invalid credentials)
✅ POST /api/v1/auth/login (missing fields)
✅ GET /api/v1/ledger/entries (no auth)
✅ GET /api/v1/accounts (no auth)
✅ GET /api/v1/invoices (no auth)
✅ GET /api/v1/expenses (no auth)
✅ GET /api/v1/signals (no auth)
✅ GET /api/v1/reports/dashboard (no auth)
✅ GET /api/v1/nonexistent

==================================================
📊 VALIDATION SUMMARY

Total Tests: 17
Passed: 17 ✅
Failed: 0 ❌
Pass Rate: 100.00%

Evidence saved to: docs/evidence/runtime-validation
==================================================
```

### Generated Files

```
docs/
├── RUNTIME_VALIDATION.md          (Report)
└── evidence/runtime-validation/
    ├── validation_results.json    (All results)
    ├── get_health.json            (Evidence for each test)
    ├── get_health_detailed.json
    ├── get_ready.json
    ├── get_live.json
    └── ... (one file per test)
```

---

## 📊 SCRIPT 2: Failure Verification

**File**: `backend/scripts/failure-verification.js`  
**Purpose**: Verify all documented failure paths  
**Scenarios**: 8+ failure scenarios  
**Evidence**: JSON files + markdown report

### What It Tests

1. **F-1: Backend Unavailable**
   - Trigger: Connect to wrong port
   - Expected: ECONNREFUSED

2. **F-2: Invalid Authentication**
   - Trigger: Invalid JWT token
   - Expected: HTTP 401

3. **F-3: Missing Required Fields**
   - Trigger: POST without required fields
   - Expected: HTTP 400

4. **F-4: Non-Existent Resource**
   - Trigger: GET unknown endpoint
   - Expected: HTTP 404

5. **F-5: Invalid JSON Body**
   - Trigger: POST with malformed JSON
   - Expected: HTTP 400

6. **F-6: CORS Violation** (documented)
   - Note: Browser-only, cannot test from Node.js

7. **F-7: Rate Limiting**
   - Trigger: 105 rapid requests
   - Expected: HTTP 429

8. **F-8: Redis Unavailable**
   - Trigger: Check with Redis down
   - Expected: Graceful degradation (200 OK)

### Expected Output

```
🧪 ARTHA Failure Verification

✅ F-1: Backend Unavailable
✅ F-2: Invalid Authentication
✅ F-3: Missing Required Fields
✅ F-4: Non-Existent Resource
✅ F-5: Invalid JSON Body
✅ F-6: CORS Violation (Documented)
✅ F-7: Rate Limiting
✅ F-8: Redis Unavailable

==================================================
📊 FAILURE VERIFICATION SUMMARY

Total Scenarios: 8
Verified: 8 ✅
Failed: 0 ❌
Verification Rate: 100.00%

Evidence saved to: docs/evidence/failure-verification
==================================================
```

### Generated Files

```
docs/
├── FAILURE_VERIFICATION.md        (Report)
└── evidence/failure-verification/
    ├── failure_verification_results.json
    ├── f1_backend_unavailable.json
    ├── f2_invalid_auth.json
    ├── f3_missing_fields.json
    ├── f4_nonexistent_resource.json
    ├── f5_invalid_json.json
    ├── f6_cors_violation.json
    ├── f7_rate_limiting.json
    └── f8_redis_unavailable.json
```

---

## 📊 SCRIPT 3: End-to-End Operational Proof

**File**: `backend/scripts/e2e-operational-proof.js`  
**Purpose**: Demonstrate complete business flow  
**Flow**: Expense → Approval → Ledger → Signal → Trace  
**Evidence**: Full transaction evidence with DB impact

### What It Proves

**8-Step Complete Flow**:

1. **Authentication**
   - Login with test credentials
   - Obtain JWT token

2. **Create Expense**
   - POST expense data
   - Capture expense ID, number, status

3. **Approve Expense**
   - Change status to approved
   - Record approver and timestamp

4. **Record Expense** (Ledger Integration)
   - Create journal entry
   - Post to ledger
   - Update hash chain

5. **Check Account Balances**
   - Verify debits/credits applied
   - Confirm accounting equation

6. **Check Signals**
   - Verify signal generation
   - Capture signal IDs

7. **Check Runtime Status**
   - Verify system reflects changes
   - Confirm real-time updates

8. **Check Trace** (if available)
   - Verify trace continuity
   - Capture trace_id

### Expected Output

```
🧪 ARTHA End-to-End Operational Proof

==================================================
STEP 1: Authentication
==================================================

✅ Authenticated successfully
   Token: eyJhbGciOiJIUzI1Ni...
   User ID: 507f1f77bcf86cd799439011
   Evidence: step1_login.json

==================================================
STEP 2: Create Expense
==================================================

✅ Expense created
   Expense ID: 507f191e810c19729de860ea
   Expense Number: EXP-000042
   Status: pending
   Amount: ₹11,800
   Evidence: step2_create_expense.json

📊 Database State Captured
   Evidence: step2_db_state.json

==================================================
STEP 3: Approve Expense
==================================================

✅ Expense approved
   Status: approved
   Approved By: 507f1f77bcf86cd799439011
   Evidence: step3_approve_expense.json

==================================================
STEP 4: Record Expense (Create Ledger Entry)
==================================================

✅ Expense recorded
   Status: recorded
   Journal Entry ID: 507f1f77bcf86cd799439012
   Evidence: step4_record_expense.json

📊 Ledger Impact Captured
   Journal Entry: JE-20250201-0042
   Status: POSTED
   Hash: 2f4e8a6b3c1d5f9a...
   Chain Position: 142
   Evidence: step4_ledger_impact.json

==================================================
STEP 5: Check Account Balances
==================================================

✅ Account balances retrieved
   Total Accounts: 33
   Expense Account Balance: ₹158,200
   Cash Account Balance: ₹842,000
   Evidence: step5_account_balances.json

==================================================
STEP 6: Check Signals
==================================================

✅ Signals retrieved
   Total Signals: 5
   Recent Signals:
     - EXPENSE_THRESHOLD_WARNING [MEDIUM]
     - GST_INPUT_CREDIT_AVAILABLE [LOW]
     - CASH_FLOW_HEALTHY [LOW]
   Evidence: step6_signals.json

==================================================
STEP 7: Check Runtime Status
==================================================

✅ Runtime status retrieved
   System Status: operational
   Posted Journals: 143
   Ledger Entries: 428
   Signals in DB: 5
   Evidence: step7_runtime_status.json

==================================================
STEP 8: Check Trace Availability
==================================================

✅ Trace check completed
   Trace available
   Evidence: step8_trace.json

==================================================
📊 E2E OPERATIONAL PROOF SUMMARY

Expense Created: ✅
  - ID: 507f191e810c19729de860ea
  - Number: EXP-000042
  - Amount: ₹11,800

Expense Approved: ✅
  - Status: approved

Ledger Entry Generated: ✅
  - ID: 507f1f77bcf86cd799439012
  - Number: JE-20250201-0042
  - Status: POSTED
  - Chain Position: 142
  - Hash: 2f4e8a6b3c1d5f9a...

Account Balances Updated: ✅
  - 33 accounts retrieved

Signals Available: ✅
  - 5 signals in database

Runtime Status Reflects Changes: ✅
  - System Status: operational
  - Posted Journals: 143

Trace Available: ✅
  - Trace ID: TRC-20250201-abc123

Evidence Directory: docs/evidence/e2e-proof
Total Steps: 8
==================================================

✅ E2E Operational Proof Complete
```

### Generated Files

```
docs/
├── END_TO_END_RUNTIME_PROOF.md    (Report)
└── evidence/e2e-proof/
    ├── complete_e2e_evidence.json (Full flow)
    ├── step1_login.json
    ├── step2_create_expense.json
    ├── step2_db_state.json
    ├── step3_approve_expense.json
    ├── step4_record_expense.json
    ├── step4_ledger_impact.json
    ├── step5_account_balances.json
    ├── step6_signals.json
    ├── step7_runtime_status.json
    └── step8_trace.json
```

---

## 🔧 CONFIGURATION

### Environment Variables (.env)

```env
# API Configuration
API_BASE=http://localhost:5000

# Test Credentials
TEST_USER_EMAIL=admin@artha.com
TEST_USER_PASSWORD=admin123

# Database
MONGODB_URI=mongodb://localhost:27017/artha
```

---

## 🎯 SUCCESS CRITERIA

### Runtime Validation
- ✅ All health endpoints return 200
- ✅ Protected endpoints return 401 without auth
- ✅ Invalid requests return appropriate errors
- ✅ Non-existent routes return 404
- ✅ Pass rate: 100%

### Failure Verification
- ✅ Backend unavailable: ECONNREFUSED
- ✅ Invalid auth: 401
- ✅ Missing fields: 400
- ✅ Malformed JSON: 400
- ✅ Rate limiting: 429 after threshold
- ✅ Redis down: Graceful degradation
- ✅ Verification rate: 100%

### E2E Operational Proof
- ✅ Transaction created
- ✅ Approval workflow works
- ✅ Ledger entry generated with hash
- ✅ Account balances updated
- ✅ Signals generated (if applicable)
- ✅ Runtime status reflects changes
- ✅ Trace continuity maintained

---

## 🐛 TROUBLESHOOTING

### Script Won't Run

```bash
# Check Node.js version
node --version  # Should be 18+

# Install dependencies
cd backend
npm install

# Check backend is running
curl http://localhost:5000/health
```

### Authentication Fails

```bash
# Check .env file
cat backend/.env | grep TEST_USER

# Verify user exists in database
mongo artha --eval "db.users.findOne({email: 'admin@artha.com'})"

# Or create test user manually via signup endpoint
```

### Database Connection Failed

```bash
# Check MongoDB is running
systemctl status mongod  # Linux
brew services list | grep mongodb  # macOS

# Check connection string
cat backend/.env | grep MONGODB_URI
```

### Evidence Files Not Generated

```bash
# Check write permissions
ls -la docs/evidence/

# Create directories manually if needed
mkdir -p docs/evidence/runtime-validation
mkdir -p docs/evidence/failure-verification
mkdir -p docs/evidence/e2e-proof
```

---

## 📝 NEXT STEPS

After running all scripts:

1. **Review Generated Reports**
   - `docs/RUNTIME_VALIDATION.md`
   - `docs/FAILURE_VERIFICATION.md`
   - `docs/END_TO_END_RUNTIME_PROOF.md`

2. **Check Evidence Files**
   - All JSON files in `docs/evidence/*/`
   - Verify requests, responses, timestamps

3. **Create Completion Packet**
   - Document what was verified
   - Note any failures or gaps
   - Prepare for handover

4. **Optional: Run Additional Tests**
   - Invoice flow (similar to expense)
   - TDS workflow
   - GST filing generation
   - Signal generation triggers

---

## 📚 RELATED DOCUMENTATION

- `docs/RUNTIME_PROOF_IMPLEMENTATION_GUIDE.md` - Full implementation guide
- `docs/RUNTIME_PROOF_SUMMARY.md` - Summary of all changes
- `README.md` - Project overview
- `backend/QUICK_REFERENCE.md` - API quick reference

---

## ✅ CHECKLIST

Before declaring ARTHA complete:

- [ ] Runtime Validation: 100% pass rate
- [ ] Failure Verification: All scenarios verified
- [ ] E2E Proof: Complete flow demonstrated
- [ ] Evidence captured for all tests
- [ ] Reports generated and reviewed
- [ ] No critical failures found
- [ ] System behaves as documented
- [ ] Recovery paths verified
- [ ] Graceful degradation confirmed

---

**Document Version**: 1.0  
**Last Updated**: 2025-02-01  
**Status**: Ready for Execution
