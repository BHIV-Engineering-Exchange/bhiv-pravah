# ARTHA - Complete Project Analysis

## Executive Summary

**ARTHA v0.1-demo** is a production-ready, enterprise-grade accounting system built with Node.js, Express, MongoDB, Redis, and React. The system implements double-entry accounting with blockchain-inspired hash-chain integrity, India GST/TDS compliance, OCR receipt processing, and comprehensive financial reporting.

---

## 1. ARCHITECTURE OVERVIEW

### Technology Stack
- **Backend**: Node.js 18+, Express 4.18
- **Database**: MongoDB 8.0 (with replica set support for transactions)
- **Cache**: Redis 4.6 (optional, production-only)
- **Frontend**: React 18, Vite, TailwindCSS
- **Infrastructure**: Docker, Docker Compose, Nginx
- **Security**: Helmet, JWT, HMAC-SHA256, Rate Limiting

### Core Design Principles
1. **Double-Entry Accounting**: Every transaction maintains debit = credit
2. **Hash-Chain Integrity**: Blockchain-inspired tamper-evident ledger
3. **Transaction Safety**: MongoDB sessions for ACID compliance
4. **Audit Trail**: Immutable audit logs for all critical operations
5. **Role-Based Access**: Admin, Accountant, Viewer roles
6. **India Compliance**: GST, TDS, PAN, TAN, GSTIN validation

---

## 2. DATABASE MODELS (11 Core Models)

### 2.1 User Model
- **Purpose**: Authentication and authorization
- **Fields**: email, password (bcrypt), name, role, isActive, lastLogin, refreshToken
- **Roles**: admin, accountant, viewer
- **Indexes**: email (unique), role, isActive, lastLogin
- **Security**: Password hashing with bcrypt (10 rounds)

### 2.2 JournalEntry Model (CRITICAL - Hash-Chain Core)
- **Purpose**: Double-entry ledger with tamper-evidence
- **Key Fields**:
  - `entryNumber`: Auto-generated (JE-YYYYMMDD-XXXX)
  - `lines`: Array of debit/credit entries (min 2 lines)
  - `status`: draft, posted, voided
  - `hash`: HMAC-SHA256 hash of entry
  - `prevHash`: Links to previous entry (chain)
  - `chainPosition`: Sequential position in chain
  - `immutable_hash`, `prev_hash`: Legacy fields (backward compatibility)
- **Validation**: 
  - Debits must equal credits
  - Each line has only debit OR credit (not both)
  - All accounts must exist and be active
- **Hash Computation**: Stable field ordering (entryNumber, date, description, lines, status, reference, prevHash)
- **Pre-save Hook**: Auto-generates entryNumber, computes hash, sets chainPosition
- **Methods**: 
  - `verifyHash()`: Validates entry integrity
  - `verifyChainFromEntry()`: Walks chain backwards to genesis

### 2.3 ChartOfAccounts Model
- **Purpose**: Account structure (Assets, Liabilities, Equity, Income, Expenses)
- **Fields**: code (unique), name, type, subtype, normalBalance, parentAccount, isActive
- **Validation**: normalBalance must match type (Asset/Expense=debit, Liability/Equity/Income=credit)
- **Indexes**: code (unique), type, isActive, parentAccount

### 2.4 Invoice Model
- **Purpose**: Customer invoicing with AR integration
- **Fields**: invoiceNumber, customer details, items/lines, amounts, GST breakdown, payments, status
- **Status Flow**: draft → sent → partial → paid (or overdue/cancelled)
- **GST Fields**: gstBreakdown (cgst, sgst, igst, cess), customerGSTIN
- **Virtual**: amountDue (calculated)
- **Pre-save Hook**: Auto-updates status based on payments

### 2.5 Expense Model
- **Purpose**: Expense tracking with approval workflow
- **Fields**: expenseNumber, vendor, category, amounts, receipts (file uploads), status, approvals
- **Status Flow**: pending → approved/rejected → recorded
- **Categories**: travel, meals, supplies, utilities, rent, insurance, marketing, professional_services, equipment, software, other
- **Receipts**: Embedded schema with filename, path, mimetype, size

### 2.6 CompanySettings Model (Singleton)
- **Purpose**: Company configuration and India statutory IDs
- **Fields**: 
  - Basic: companyName, legalName, address, contact
  - Statutory: gstin, pan, tan, cin
  - Bank: bankAccounts array
  - GST Settings: isRegistered, filingFrequency, compositionScheme
  - TDS Settings: isTANActive, defaultTDSRate
  - Accounting: financialYearStart, baseCurrency, decimalPlaces
- **Singleton Pattern**: _id fixed as 'company_settings'

### 2.7 GSTReturn Model
- **Purpose**: GST filing (GSTR-1, GSTR-3B, GSTR-9)
- **Fields**: returnType, period (month/year), gstin, b2b/b2c supplies, outward/inward supplies, netTaxLiability, status
- **Status**: draft, filed, revised

### 2.8 TDSEntry Model
- **Purpose**: TDS deduction tracking
- **Fields**: entryNumber, deductee (name, PAN), section (194A, 194C, etc.), amounts, challan details, status
- **Status**: pending, deducted, deposited, filed
- **Pre-save Hook**: Auto-generates entryNumber, calculates netPayable

### 2.9 RLExperience Model (InsightFlow)
- **Purpose**: Reinforcement Learning experience buffer for analytics
- **Fields**: sessionId, userId, state, action, reward, nextState, isTerminal, metadata
- **Use Case**: Track user interactions for ML-based insights

### 2.10 AuditLog Model (Immutable)
- **Purpose**: Tamper-proof audit trail
- **Fields**: action, entityType, entityId, userId, ipAddress, userAgent, changes, metadata, timestamp
- **Immutability**: Pre-save hook prevents modifications after creation

### 2.11 AccountBalance Model
- **Purpose**: Cached account balances for performance
- **Fields**: account (ref), balance, debitTotal, creditTotal, lastUpdated
- **Updated**: Automatically when journal entries are posted

---

## 3. SERVICE LAYER (18 Services)

### 3.1 ledger.service.js (CORE)
**Key Methods**:
- `createJournalEntry()`: Validates double-entry, computes hash, sets chain position
- `postJournalEntry()`: Verifies hash, updates balances, posts entry
- `voidJournalEntry()`: Creates reversing entry, maintains chain integrity
- `verifyLedgerChain()`: Full chain verification with detailed error reporting
- `getAccountBalances()`: Aggregates balances with filters
- `getLedgerSummary()`: Assets, Liabilities, Equity, Income, Expenses totals
- `updateAccountBalances()`: Updates AccountBalance records in transaction

**Transaction Safety**: All mutations use MongoDB sessions

### 3.2 invoice.service.js
**Key Methods**:
- `createInvoice()`: Creates draft invoice
- `sendInvoice()`: Creates AR journal entry, posts to ledger
- `recordPayment()`: Creates payment journal entry, updates invoice
- `getInvoiceStats()`: Aggregates by status with caching

**Integration**: Tightly coupled with ledger.service for AR/Revenue entries

### 3.3 expense.service.js
**Key Methods**:
- `createExpense()`: Creates expense with file uploads
- `approveExpense()`: Approval workflow
- `recordExpense()`: Maps category to account, creates journal entry
- `deleteReceipt()`: Removes file from filesystem and DB

**Category Mapping**: Maps expense categories to chart of accounts codes

### 3.4 gst.service.js
**Key Methods**:
- `calculateGST()`: Splits into CGST/SGST (intrastate) or IGST (interstate)
- `generateGSTR1()`: Outward supplies from invoices
- `generateGSTR3B()`: Summary with net tax liability
- `validateGSTIN()`: Regex validation

### 3.5 gstFiling.service.js (Enhanced)
**Key Methods**:
- `generateGSTR1FilingPacket()`: Detailed B2B/B2C breakdown
- `generateGSTR3BFilingPacket()`: Outward/inward supplies with ITC
- `exportFilingPacketAsCSV()`: CSV export for filing
- `determineSupplyType()`: Classifies as b2b_intrastate, b2c, export

### 3.6 ocr.service.js
**Key Methods**:
- `extractTextFromReceipt()`: Tesseract.js (optional) or mock extraction
- `parseReceiptText()`: Regex-based field extraction
- `extractVendor()`, `extractDate()`, `extractAmount()`, `extractTaxAmount()`, `extractInvoiceNumber()`
- `calculateConfidence()`: 0-100 score based on extracted fields
- `processReceiptFile()`: Full pipeline (extract → parse)

**Fallback**: Mock extraction when OCR_ENABLED=false

### 3.7 cache.service.js
**Key Methods**:
- `getCachedLedgerSummary()`, `cacheLedgerSummary()`
- `getCachedInvoiceStats()`, `cacheInvoiceStats()`
- `invalidateLedgerCaches()`, `invalidateInvoiceCaches()`

**TTL**: Configurable via REDIS_CACHE_TTL (default 300s)

### 3.8 health.service.js
**Key Methods**:
- `getSystemHealth()`: Checks MongoDB, Redis, memory, disk
- `getDetailedHealth()`: Comprehensive system status
- `checkDatabaseHealth()`, `checkRedisHealth()`, `checkMemoryHealth()`

---

## 4. CONTROLLER LAYER (15 Controllers)

### 4.1 ledger.controller.js
**Endpoints**:
- `createJournalEntry`: POST /api/v1/ledger/entries
- `postJournalEntry`: POST /api/v1/ledger/entries/:id/post
- `voidJournalEntry`: POST /api/v1/ledger/entries/:id/void
- `verifyLedgerChain`: GET /api/v1/ledger/verify
- `getChainSegment`: GET /api/v1/ledger/chain-segment
- `verifySingleEntry`: GET /api/v1/ledger/entries/:id/verify

**Authorization**: Admin/Accountant for mutations, all authenticated for reads

### 4.2 invoice.controller.js
**Endpoints**:
- `createInvoice`, `getInvoices`, `getInvoiceById`, `updateInvoice`
- `sendInvoice`: Creates AR entry
- `recordPayment`: Records payment with journal entry
- `cancelInvoice`
- `getInvoiceStats`: Aggregated statistics

### 4.3 expense.controller.js
**Endpoints**:
- `createExpense`, `getExpenses`, `getExpenseById`, `updateExpense`
- `approveExpense`, `rejectExpense`, `recordExpense`
- `deleteReceipt`
- `getExpenseStats`

### 4.4 gstFiling.controller.js
**Endpoints**:
- `getGSTSummary`: GET /api/v1/gst/filing/summary
- `getGSTR1FilingPacket`: GET /api/v1/gst/filing/filing-packet/gstr-1
- `getGSTR3BFilingPacket`: GET /api/v1/gst/filing/filing-packet/gstr-3b
- `exportFilingPacket`: GET /api/v1/gst/filing/export

### 4.5 ocr.controller.js
**Endpoints**:
- `processReceiptOCR`: POST /api/v1/expenses/ocr (with file upload)
- `getOCRStatus`: GET /api/v1/expenses/ocr/status

**File Handling**: Multer middleware, automatic cleanup

---

## 5. ROUTING ARCHITECTURE

### 5.1 Route Structure
```
/api/v1/auth          → auth.routes.js
/api/v1/ledger        → ledger.routes.js
/api/v1/accounts      → accounts.routes.js
/api/v1/invoices      → invoice.routes.js
/api/v1/expenses      → expense.routes.js
/api/v1/gst           → gst.routes.js
/api/v1/tds           → tds.routes.js
/api/v1/settings      → settings.routes.js
/api/v1/reports       → reports.routes.js
/api/v1/insightflow   → insightflow.routes.js
/api/v1/performance   → performance.routes.js
/api/v1/database      → database.routes.js
/health, /ready, /live → health.routes.js
/api                  → index.js (legacy)
```

### 5.2 Middleware Stack (per route)
1. **helmetConfig**: Security headers
2. **cors**: Cross-origin resource sharing
3. **limiter**: Rate limiting (100 req/15min)
4. **watermark**: Trace ID header
5. **requestLogger**: Request logging (production)
6. **performanceMonitor**: Timing metrics (production)
7. **sanitizeInput**: XSS prevention
8. **protect**: JWT authentication
9. **authorize**: Role-based authorization
10. **auditLogger**: Audit trail (critical operations)

---

## 6. HASH-CHAIN IMPLEMENTATION

### 6.1 Chain Structure
```
Genesis (prevHash='0') → Entry1 → Entry2 → Entry3 → ...
```

### 6.2 Hash Computation
```javascript
HMAC-SHA256(
  entryNumber + date + description + 
  sorted(lines) + status + reference + prevHash,
  HMAC_SECRET
)
```

### 6.3 Chain Verification
1. **Single Entry**: Recompute hash, compare with stored hash
2. **Full Chain**: Walk from latest to genesis, verify each link
3. **Tamper Detection**: Hash mismatch throws error on posting

### 6.4 Backward Compatibility
- New fields: `hash`, `prevHash`, `chainPosition`, `hashTimestamp`
- Legacy fields: `immutable_hash`, `prev_hash`, `immutable_chain_valid`
- Both synced in pre-save hook

---

## 7. TRANSACTION FLOW EXAMPLES

### 7.1 Invoice Payment Flow
1. User creates invoice (draft)
2. User sends invoice → Creates AR journal entry (Debit AR, Credit Revenue)
3. Customer pays → Creates payment journal entry (Debit Cash, Credit AR)
4. Invoice status updates to 'paid'

### 7.2 Expense Recording Flow
1. User submits expense with receipts (pending)
2. Accountant approves expense (approved)
3. Accountant records expense → Creates journal entry (Debit Expense, Credit Cash)
4. Expense status updates to 'recorded'

### 7.3 GST Filing Flow
1. System aggregates invoices for period
2. Generates GSTR-1 (outward supplies)
3. Generates GSTR-3B (net tax liability with ITC)
4. Exports to CSV for filing

---

## 8. SECURITY ARCHITECTURE

### 8.1 Authentication
- JWT tokens (access + refresh)
- Bcrypt password hashing (10 rounds)
- Token expiration: 24h (configurable)

### 8.2 Authorization
- Role-based: admin, accountant, viewer
- Route-level: `authorize('admin', 'accountant')`
- Resource-level: Users can only access their own expenses

### 8.3 Input Validation
- express-validator for schema validation
- XSS sanitization middleware
- File upload validation (mimetype, size)

### 8.4 Rate Limiting
- Global: 100 req/15min
- Auth endpoints: 5 req/15min
- Configurable via env vars

### 8.5 Audit Trail
- Immutable AuditLog for all mutations
- Tracks: action, entity, user, IP, changes
- Cannot be modified after creation

---

## 9. PERFORMANCE OPTIMIZATIONS

### 9.1 Database Indexes
- User: email, role, isActive, lastLogin
- JournalEntry: entryNumber, status, date, chainPosition, hash, prevHash, lines.account
- Invoice: invoiceNumber, status, invoiceDate, dueDate, customerName, customerGSTIN
- Expense: expenseNumber, status, date, category, submittedBy, vendor
- ChartOfAccounts: code, type, isActive
- Compound indexes for common queries

### 9.2 Redis Caching
- Ledger summary (TTL: 5min)
- Invoice stats (TTL: 5min)
- Expense stats (TTL: 5min)
- Cache invalidation on mutations

### 9.3 Aggregation Pipelines
- Account balances: $lookup + $unwind + $match + $project
- Statistics: $group + $sum + $avg

### 9.4 Pagination
- Default: 20 items per page
- Configurable limit
- Skip + limit for offset pagination

---

## 10. TESTING STRATEGY

### 10.1 Test Coverage
- Unit tests: Services, models
- Integration tests: Controllers, routes
- End-to-end tests: Full workflows
- Coverage target: >80%

### 10.2 Test Files (30+ test suites)
- ledger-chain.test.js: Hash-chain verification
- ocr.test.js: OCR extraction and parsing
- gst-filing.test.js: GST packet generation
- invoice.test.js: Invoice workflows
- expense.routes.test.js: Expense CRUD
- redis-cache.test.js: Cache operations
- performance.test.js: Performance monitoring
- health-monitoring.test.js: Health checks

### 10.3 Test Environment
- Separate MongoDB test database
- In-memory Redis (optional)
- Jest with supertest
- Cross-env for NODE_ENV=test

---

## 11. DEPLOYMENT ARCHITECTURE

### 11.1 Development (docker-compose.dev.yml)
- Backend: Node.js with nodemon
- Frontend: Vite dev server
- MongoDB: Single instance
- Volumes: Hot reload

### 11.2 Production (docker-compose.prod.yml)
- Backend: Multi-stage Docker build
- Frontend: Nginx static serving
- MongoDB: Replica set (3 nodes)
- Redis: Persistent cache
- Nginx: Reverse proxy with compression
- Health checks: /health, /ready, /live

### 11.3 Monitoring
- Winston logging (combined.log, error.log)
- Performance metrics: /metrics endpoint
- Health checks: Kubernetes-compatible
- Prometheus integration (optional)

---

## 12. KEY INTEGRATION POINTS

### 12.1 Ledger ↔ Invoice
- sendInvoice() creates AR journal entry
- recordPayment() creates payment journal entry

### 12.2 Ledger ↔ Expense
- recordExpense() creates expense journal entry
- Maps category to chart of accounts

### 12.3 Invoice ↔ GST
- Invoice data feeds GSTR-1 generation
- GST breakdown (CGST/SGST/IGST) calculated

### 12.4 Expense ↔ OCR
- OCR extracts receipt data
- Auto-fills expense form fields

### 12.5 All Services ↔ Cache
- Cache invalidation on mutations
- Cache reads on queries

---

## 13. CRITICAL DEPENDENCIES

### 13.1 Production Dependencies
- express: Web framework
- mongoose: MongoDB ODM
- redis: Caching layer
- jsonwebtoken: Authentication
- bcryptjs: Password hashing
- decimal.js: Precise decimal arithmetic
- helmet: Security headers
- winston: Logging
- multer: File uploads
- pdfkit: PDF generation

### 13.2 Optional Dependencies
- tesseract.js: OCR (fallback to mock)

---

## 14. ENVIRONMENT CONFIGURATION

### 14.1 Required Variables
- MONGODB_URI: Database connection
- JWT_SECRET: Token signing (min 32 chars)
- HMAC_SECRET: Hash-chain signing (min 32 chars)
- PORT: Server port (default 5000)

### 14.2 Optional Variables
- REDIS_URL: Cache connection
- OCR_ENABLED: Enable Tesseract OCR
- RATE_LIMIT_MAX: Rate limit threshold
- FRONTEND_URL: CORS origin

---

## 15. BACKWARD COMPATIBILITY

### 15.1 Legacy Routes
- /api/auth/* → /api/v1/auth/*
- /api/ledger/journal-entries → /api/v1/ledger/entries
- /api/ledger/verify-chain → /api/v1/ledger/verify

### 15.2 Legacy Fields
- JournalEntry: immutable_hash, prev_hash synced with hash, prevHash
- Invoice: lines aliased to items

---

## 16. FUTURE EXTENSIBILITY

### 16.1 Planned Features
- Multi-currency support
- Bank reconciliation
- Payroll integration
- Advanced reporting (custom queries)
- Mobile app API

### 16.2 Extension Points
- Plugin system for custom accounts
- Webhook support for integrations
- GraphQL API layer
- Real-time updates (WebSocket)

---

## 17. KNOWN LIMITATIONS

1. **Single Company**: No multi-tenancy (yet)
2. **File Storage**: Local filesystem (not S3)
3. **OCR Accuracy**: Mock extraction by default
4. **Reporting**: Limited to predefined reports
5. **Transactions**: Requires MongoDB replica set in production

---

## 18. MAINTENANCE GUIDELINES

### 18.1 Database Migrations
- Use scripts/migrate-hash-chain.js for schema changes
- Always backup before migration
- Test on staging first

### 18.2 Index Management
- Run scripts/create-indexes.js after schema changes
- Monitor slow queries with database.service.js

### 18.3 Cache Management
- Clear Redis on major updates
- Monitor cache hit rates
- Adjust TTL based on usage

### 18.4 Log Management
- Rotate logs daily (Winston config)
- Archive old logs
- Monitor error.log for issues

---

## 19. TROUBLESHOOTING

### 19.1 Hash-Chain Issues
- Run verify:hash-chain script
- Check HMAC_SECRET consistency
- Verify chainPosition sequence

### 19.2 Transaction Failures
- Ensure MongoDB replica set
- Check session timeout settings
- Review transaction logs

### 19.3 Performance Issues
- Check Redis connection
- Review slow query logs
- Optimize aggregation pipelines

---

## 20. CONCLUSION

ARTHA is a well-architected, production-ready accounting system with:
- ✅ Robust double-entry ledger with hash-chain integrity
- ✅ Comprehensive India compliance (GST, TDS)
- ✅ Modern tech stack with best practices
- ✅ Extensive test coverage
- ✅ Production-grade security
- ✅ Scalable architecture
- ✅ Clear separation of concerns
- ✅ Backward compatibility
- ✅ Comprehensive documentation

**Ready for production deployment and future enhancements.**
