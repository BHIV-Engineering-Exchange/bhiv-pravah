# Ecosystem Readiness — ARTHA × BHIV Integration Assessment

**Prepared for:** BHIV Engineering Review  
**Platform:** ARTHA v0.1  
**Assessment Date:** June 2026  
**Scope:** Trace compatibility · Dashboard capability · Observability compatibility · Gap analysis · Future recommendations

---

## Executive Summary

ARTHA is functionally production-ready as a standalone financial platform. Its signal pipeline,
ledger hash-chain, and compliance engine are proven. However, **5 integration-blocking gaps**
must be closed before other BHIV products can consume ARTHA's signals reliably as a shared capability.

**Overall Readiness Score: 72 / 100**

| Domain | Score | Status |
|--------|-------|--------|
| Trace Compatibility | 68 / 100 | ⚠️ Gaps in trace threading |
| Dashboard Capability | 85 / 100 | ✅ Reusable with design-system package |
| Observability Compatibility | 70 / 100 | ⚠️ Missing OpenTelemetry spans |
| SETU Signal Contract | 80 / 100 | ✅ Pipeline implemented; retry missing |
| Data Consistency | 65 / 100 | ⚠️ No replica-set guard, no dedup |

---

## 1. Trace Compatibility Review

### What ARTHA has
- Every `JournalEntry` carries a `trace_id` field (format: `TRC-YYYYMMDD-xxxxxxxx`)
- Signal creation threads the same `trace_id` through: JournalEntry → ComplianceSignal → SETU payload
- `GET /api/v1/signals/trace/:traceId` reconstructs the 5-step chain:
  Signal → ComplianceValidation → ComplianceFiling → JournalEntries → LedgerEntries

### Compatibility Assessment

| Trace Requirement | Status | Evidence |
|-------------------|--------|---------|
| Stable trace_id format | ✅ | `TRC-YYYYMMDD-8hex` — consistent across all modules |
| trace_id in journal entries | ✅ | `JournalEntry.trace_id` field present |
| trace_id in compliance signals | ✅ | `ComplianceSignal.trace_id` field present |
| trace_id in SETU payload | ✅ | `X-Artha-Trace` header + body field |
| trace_id in compliance filings | ⚠️ | **Gap**: `ComplianceFiling` model does not store `trace_id` |
| OpenTelemetry span export | ❌ | No OTel instrumentation — manual trace IDs only |
| Distributed trace correlation | ❌ | No W3C TraceContext headers on ARTHA ↔ SETU calls |
| Trace deduplication | ⚠️ | No idempotency check — duplicate signals can share trace_id |

### Gap: ComplianceFiling trace_id
**Impact:** When a BHIV consumer queries `GET /signals/trace/:traceId`, Step 3 (Compliance Filing)
may return `found: false` even when the filing exists, because the filing was not stored with the trace_id.

**Fix required:**
```javascript
// backend/src/services/gstStatutory.service.js — generateGSTR1()
// Pass and store trace_id on ComplianceFiling creation:
const filing = await ComplianceFiling.create({
  ...filingData,
  trace_id: journalEntry.trace_id,  // ← ADD THIS
});
```

---

## 2. Dashboard Capability Review

### What ARTHA has
- Executive Dashboard (`/dashboard`) — 4-KPI, 3-chart, 2-table layout
- Financial Intelligence Dashboard (`/financial-intelligence`) — 3-zone signal layout
- GST Compliance Dashboard (`/compliance/gst`) — filing status + invoice table
- TDS Management (`/compliance/tds`) — TDS entries + deductions
- Signal Dashboard (`/compliance/signals`) — signal list with severity filter

### Reusability Assessment

| Dashboard | Reusable Without ARTHA Code? | Notes |
|-----------|------------------------------|-------|
| Executive Dashboard pattern | ✅ | Documented in `dashboard_patterns.md` |
| KPI Card component | ✅ | Documented in `component_library.md` |
| Alert Card component | ✅ | Documented with props |
| Timeline Card (Recharts) | ✅ | recharts is a public dependency |
| Signal Intelligence 3-zone | ✅ | Grid pattern documented |
| Compliance Card | ✅ | Documented with extension notes |
| Color system | ✅ | `colors.md` with all CSS tokens |
| Typography system | ✅ | `typography.md` with all tokens |
| Spacing system | ✅ | `spacing.md` with all tokens |
| Dashboard patterns | ✅ | `dashboard_patterns.md` with 5 patterns |

### Remaining Actions for Full Capability Extraction
1. Publish `@bhiv/design-system` as an npm package
2. Extract `Card`, `Badge`, `Button`, `Loading` to a shared package
3. Create a Storybook instance for interactive component preview
4. Generate visual screenshots for each component (referenced in component_library.md)

---

## 3. Observability Compatibility Review

### What ARTHA has
- Manual trace IDs (not OpenTelemetry)
- Backend Morgan HTTP request logging
- Error logging to console
- `dispatch_status` field on ComplianceSignal (persisted before SETU dispatch)
- Hash-chain verification endpoint (`GET /ledger/verify-chain`)

### What ARTHA is missing

| Observability Requirement | Status | Priority |
|---------------------------|--------|---------|
| OpenTelemetry spans | ❌ | HIGH |
| Structured JSON logs | ⚠️ | MEDIUM — Morgan is semi-structured |
| Metrics endpoint (Prometheus) | ❌ | MEDIUM |
| Error rate alerting | ❌ | HIGH |
| SETU dispatch retry with backoff | ❌ | CRITICAL |
| Dead letter queue for failed signals | ❌ | HIGH |
| Signal deduplication | ❌ | HIGH |
| Health check endpoint | ⚠️ | Available via `GET /health` — not documented |

### OpenTelemetry Integration Path
```javascript
// Recommended: Add @opentelemetry/sdk-node to backend
// backend/src/telemetry.js

const { NodeSDK } = require('@opentelemetry/sdk-node');
const { Resource } = require('@opentelemetry/resources');
const { SEMRESATTRS_SERVICE_NAME } = require('@opentelemetry/semantic-conventions');

const sdk = new NodeSDK({
  resource: new Resource({ [SEMRESATTRS_SERVICE_NAME]: 'artha-backend' }),
  traceExporter: new OTLPTraceExporter({ url: process.env.OTEL_ENDPOINT }),
});
sdk.start();
```

Once OTel is instrumented, trace_id can be derived from OTel span context instead of manual generation,
enabling automatic correlation with any OTel-compatible backend (Jaeger, Tempo, Zipkin).

---

## 4. Known Gaps Report

### GAP-001: SETU Dispatch Has No Retry
**Severity:** CRITICAL  
**Description:** `dispatchToSetu()` makes a single HTTP call. On failure, the signal remains in DB with `dispatch_status: pending` but is never retried.  
**Impact:** SETU may never receive compliance signals in production if network is intermittent.  
**Fix:** Implement a scheduled job (cron or BullMQ) that polls for `dispatch_status: pending` signals older than 5 minutes and retries dispatch up to 3 times with exponential backoff.

### GAP-002: No Signal Deduplication
**Severity:** HIGH  
**Description:** `ComplianceSignal.create()` does not check for existing signals with the same `type + trace_id`. A retry of a compliance filing can emit duplicate signals.  
**Impact:** SETU receives duplicate signals; dashboards show inflated issue counts.  
**Fix:**
```javascript
// Add before ComplianceSignal.create():
const existing = await ComplianceSignal.findOne({ type: signalData.type, trace_id: signalData.trace_id });
if (existing) return existing;  // idempotent
```

### GAP-003: MongoDB Replica Set Not Enforced
**Severity:** HIGH  
**Description:** ARTHA uses `withTransaction()` which falls back to non-transactional mode if no replica set is detected. Journal entries can be partially written without rollback.  
**Impact:** Orphaned `VALIDATED` journal entries that never post; account balances not updated.  
**Fix:** Add startup guard:
```javascript
const topology = mongoose.connection.client.topology;
if (!topology?.s?.replicaSetName) {
  throw new Error('ARTHA requires MongoDB replica set for ACID transactions');
}
```

### GAP-004: Dual Signal Vocabulary
**Severity:** MEDIUM  
**Description:** `ComplianceSignal.type` field contains both old-style keys (e.g. `GST_TDS_LOAD`) and new-style keys (e.g. `SIG_GST_TDS_LOAD`). No schema enforcement.  
**Impact:** Signal dashboard shows inconsistent type labels; pipeline-check may fail validation.  
**Fix:** Add enum validation to `ComplianceSignal` schema:
```javascript
type: { type: String, enum: Object.values(SIGNAL_TYPES), required: true }
```

### GAP-005: No W3C TraceContext on SETU Calls
**Severity:** MEDIUM  
**Description:** ARTHA sends `X-Artha-Trace` header to SETU but does not use the W3C `traceparent` / `tracestate` headers. Cross-system correlation in Jaeger/Grafana Tempo is impossible.  
**Impact:** BHIV cannot correlate ARTHA signals with downstream processing in an OTel observability stack.  
**Fix:** When OpenTelemetry is added (GAP-OTel), auto-inject W3C headers via OTel HTTP propagator.

### GAP-006: Company Settings Not Validated at Startup
**Severity:** HIGH (reported in REVIEW_PACKET.md)  
**Description:** If company settings document is missing from MongoDB, every invoice send fails with a generic 500 error.  
**Fix:** Add startup health check that verifies `CompanySettings.findById('company_settings')` returns a document. Fail startup (or emit a loud log warning) if missing.

---

## 5. Future Integration Recommendations

### Recommendation A: Publish @bhiv/design-system Package
**Priority:** HIGH  
**Effort:** Medium  
Extract the design-system directory into a standalone npm package. Other BHIV products import it directly.
```json
{
  "name": "@bhiv/design-system",
  "version": "1.0.0",
  "exports": {
    "./colors": "./src/tokens/colors.css",
    "./typography": "./src/tokens/typography.css",
    "./components": "./src/components/index.js"
  }
}
```

### Recommendation B: Add OpenTelemetry Instrumentation
**Priority:** HIGH  
**Effort:** Medium  
Replace manual `trace_id` generation with OTel span context. This makes ARTHA compatible with:
- Grafana Tempo
- Jaeger
- AWS X-Ray
- Google Cloud Trace

### Recommendation C: Implement SETU Signal Retry Queue
**Priority:** CRITICAL  
**Effort:** Low–Medium  
Use BullMQ (Redis-backed) to queue SETU dispatch jobs. On failure, retry up to 3× with exponential backoff.
Dead-letter queue for signals that fail all retries, with alert.

### Recommendation D: Add Prometheus Metrics Endpoint
**Priority:** MEDIUM  
**Effort:** Low  
Add `GET /metrics` endpoint exposing:
- `artha_signals_emitted_total` — counter by type + severity
- `artha_setu_dispatch_total` — counter by status (success/fail)
- `artha_ledger_verify_duration_ms` — histogram
- `artha_journal_entries_total` — counter by status

### Recommendation E: Enforce Read Model Separation
**Priority:** LOW  
**Effort:** High  
ARTHA currently mixes read and write operations in the same service methods.
For BHIV scale, introduce a CQRS pattern:
- Write side: InvoiceService, ExpenseService, TDSService, LedgerService
- Read side: ReportQueryService, DashboardQueryService with denormalized views

### Recommendation F: Add Storybook Component Catalog
**Priority:** MEDIUM  
**Effort:** Low  
Add Storybook to `frontend/` so BHIV teams can browse and interact with all design-system components
without running the full ARTHA application.

---

## Integration Readiness Matrix

| BHIV Product Type | Can Integrate Today? | Blockers |
|-------------------|---------------------|---------|
| Internal Finance Dashboard | ✅ Yes | Minor — close GAP-001 first |
| Compliance Reporting Tool | ✅ Yes | Close GAP-002, GAP-004 |
| Observability Platform | ⚠️ Partial | Needs OTel (GAP-OTel) |
| Real-Time Alert System | ❌ Not yet | Needs retry queue (GAP-001) |
| Executive BI Dashboard | ✅ Yes | Use dashboard_patterns.md directly |
| Audit Trail System | ⚠️ Partial | Close GAP-003 (replica set) |

---

## Conclusion

ARTHA is a solid foundation. The **dashboard capability** is immediately reusable via the design-system
package created in this sprint. The **signal pipeline** is architecturally sound but needs operational
hardening (retry, dedup, dedup, OTel) before it can be a shared BHIV ecosystem capability.

**Recommended sprint order:**
1. Close GAP-001 (SETU retry) — blocks production reliability
2. Close GAP-002 (signal dedup) — blocks data integrity  
3. Close GAP-003 (replica set guard) — blocks ACID guarantees
4. Add OpenTelemetry — enables ecosystem observability
5. Publish @bhiv/design-system — enables multi-product reuse

---

**Document Version**: 1.0  
**Owner**: BHIV Platform Engineering  
**Review Cycle**: After each ARTHA sprint  
