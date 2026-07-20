# ARTHA → Tantra Integration Mapping

Generated: 2026-06-17

## Overview

This document maps how ARTHA (India-Compliant Double-Entry Accounting System) connects to Tantra (Observability & Runtime Proof Layer).

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ARTHA TRANSACTION                            │
│  Invoice / Expense / Journal Entry                                  │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        LEDGER POSTING                               │
│  Double-entry journal → Hash chain → Tamper-proof ledger            │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        COMPLIANCE SIGNAL                            │
│  SIG_FILING_GENERATED → GSTR-1 / GSTR-3B packet                    │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FILING                                       │
│  ComplianceFiling → Validated → Ready for SETU                      │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SETU DISPATCH                                │
│  HTTP POST → GST Network Gateway → SETU reference                   │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        RUNTIME PROOF                                │
│  UnifiedTrace → Evidence chain → Audit trail                        │
└──────────────────────┬──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        TANTRA OBSERVABILITY                         │
│  Monitoring → Alerts → Dashboards → Compliance Reports              │
└─────────────────────────────────────────────────────────────────────┘
```

## Entity Mapping

### ARTHA → Tantra Data Flow

| ARTHA Entity | Tantra Consumer | Purpose |
|-------------|-----------------|---------|
| JournalEntry | Transaction Proof | Ledger integrity verification |
| LedgerEntry | Hash Chain | Tamper-proof chain validation |
| ComplianceSignal | Signal Monitor | Filing lifecycle tracking |
| ComplianceFiling | Filing Tracker | GST compliance status |
| UnifiedTrace | Trace Explorer | End-to-end lineage |
| RuntimeProof | Evidence Store | Audit trail preservation |

### Trace Fields → Tantra Fields

| ARTHA Field | Tantra Field | Description |
|------------|--------------|-------------|
| `trace_id` | `correlation_id` | Unique transaction identifier |
| `stages` | `span_list` | Execution stages as spans |
| `current_stage` | `current_span` | Active processing stage |
| `status` | `trace_status` | COMPLETED / FAILED / IN_PROGRESS |
| `linked_entities` | `entity_graph` | Connected entities |
| `initiated_at` | `start_time` | Trace start timestamp |
| `completed_at` | `end_time` | Trace end timestamp |

## Observability Hooks

### Metrics (Prometheus-compatible)

```
# Transaction metrics
artha_journal_entries_total{status="POSTED|DRAFT|REJECTED"}
artha_journal_entries_duration_seconds{operation="create|validate|post"}

# Ledger metrics
artha_ledger_chain_length
artha_ledger_chain_valid{valid="true|false"}
artha_ledger_entries_total

# Compliance metrics
artha_compliance_signals_total{type="SIG_FILING_GENERATED|SIG_FILING_VALIDATED"}
artha_compliance_filings_total{type="GSTR-1|GSTR-3B",status="READY|VALIDATED|DISPATCHED"}
artha_setu_dispatches_total{status="SUCCESS|FAILED|SIMULATED"}

# Audit metrics
artha_audit_score{phase="replay|compliance|audit"}
artha_certification_status{type="integrity|production",status="CERTIFIED|FAILED"}
```

### Events (OpenTelemetry-compatible)

```json
{
  "event": "arthajournal.posted",
  "trace_id": "TRC-20260617-xxxxx",
  "span_id": "SPAN-001",
  "attributes": {
    "arthajournal.id": "JE-20260617-0001",
    "arthajournal.status": "POSTED",
    "arthajournal.total_debit": "5000.00",
    "arthajournal.total_credit": "5000.00",
    "arthajournal.hash": "abc123..."
  }
}
```

## Integration Points

### 1. Transaction → Ledger
- **Hook**: `ledgerService.postJournalEntry()`
- **Event**: `arthajournal.posted`
- **Metrics**: `artha_journal_entries_total`, `artha_ledger_chain_length`

### 2. Ledger → Signal
- **Hook**: `complianceService.generateSignal()`
- **Event**: `artha.signal.generated`
- **Metrics**: `artha_compliance_signals_total`

### 3. Signal → Filing
- **Hook**: `complianceService.createFiling()`
- **Event**: `artha.filing.created`
- **Metrics**: `artha_compliance_filings_total`

### 4. Filing → SETU
- **Hook**: `signalEngine.dispatchToSetu()`
- **Event**: `artha.setu.dispatched`
- **Metrics**: `artha_setu_dispatches_total`

### 5. SETU → RuntimeProof
- **Hook**: `traceabilityService.addStage()`
- **Event**: `artha.trace.stage_added`
- **Metrics**: `artha_audit_score`

## Dashboard Queries

### Transaction Health
```promql
rate(artha_journal_entries_total[5m]) > 0
```

### Ledger Integrity
```promql
artha_ledger_chain_valid == 0
```

### Compliance Status
```promql
artha_compliance_filings_total{status="READY"} > 0
```

### SETU Dispatch Rate
```promql
rate(artha_setu_dispatches_total{status="SUCCESS"}[5m])
```

## Tantra Configuration

```yaml
# tantra.config.yml
observability:
  enabled: true
  provider: opentelemetry
  
  metrics:
    enabled: true
    port: 9090
    path: /metrics
    
  tracing:
    enabled: true
    exporter: otlp
    endpoint: localhost:4317
    
  logging:
    enabled: true
    level: info
    format: json

  events:
    enabled: true
    buffer_size: 1000
    flush_interval: 5000

arthra:
  trace_id_header: X-ARTHA-Trace-ID
  span_id_header: X-ARTHA-Span-ID
  service_name: artha-backend
  service_version: 0.1.0
```

## Status

| Component | Status | Notes |
|-----------|--------|-------|
| ARTHA Transaction Layer | ✅ Complete | All transaction types supported |
| Ledger Posting | ✅ Complete | Hash chain, double-entry verified |
| Compliance Signals | ✅ Complete | GSTR-1/3B generation working |
| Filing Pipeline | ✅ Complete | Validation working |
| SETU Dispatch | ⚠️ Mock | Pipeline proven, real dispatch pending |
| RuntimeProof | ✅ Complete | Trace model exists |
| Tantra Observability | 📋 Designed | This document — integration pending |
