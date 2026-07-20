# Architecture Map — ARTHA BHIV Ecosystem Integration

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                   │
│  React 18 + Vite                                                           │
│  ├── Zustand (auth state)                                                  │
│  ├── React Query (server state)                                            │
│  ├── Axios (API client with interceptors)                                  │
│  └── Tailwind CSS (styling)                                                │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │ HTTP/HTTPS
┌─────────────────────────────────────▼───────────────────────────────────────┐
│                              API GATEWAY                                    │
│  CORS → Helmet → Rate Limit → Input Sanitization → Watermark               │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────────┐
│                         AUTHORITY LAYER                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ authorityEnforcement (existing)                                     │   │
│  │ - Loads contracts from contracts/capability_contracts/*.json        │   │
│  │ - Maps routes to capabilities                                       │   │
│  │ - Basic enforcement                                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ policyEnforcement (NEW)                                             │   │
│  │ - Runtime enforcement with deterministic decisions                  │   │
│  │ - Policy decision recording                                         │   │
│  │ - Collection mutation authorization                                 │   │
│  │ - Input schema validation                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────────┐
│                       AUTHENTICATION LAYER                                  │
│  JWT Bearer Token → protect middleware → role authorization                 │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────────┐
│                           ROUTE LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 24 route groups                                                     │   │
│  │ ledger │ accounts │ reports │ invoices │ expenses │ insightflow     │   │
│  │ gst │ tds │ compliance │ settings │ performance │ database         │   │
│  │ users │ statements │ upload │ signals │ runtime │ trace            │   │
│  │ banking │ audit │ ca-workflow │ tally │ multi-company │ tantra     │   │
│  │ governance (NEW)                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 26 controllers                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────────┐
│                          SERVICE LAYER                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Business Services (36 existing)                                     │   │
│  │ ledger │ invoice │ expense │ tds │ gst │ banking │ financialReports│   │
│  │ signalEngine │ traceability │ runtimeProof │ evidenceAutomation    │   │
│  │ cache │ health │ performance │ observability │ database │ export   │   │
│  │ pdf │ ocr │ smartUpload │ bankStatement │ multiCompany │ caWorkflow│   │
│  │ tallyCompatibility │ tantra │ sampadaAdapter │ setu.pipeline      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Governance Services (NEW)                                           │   │
│  │ capabilityRegistry │ provenanceChain │ deterministicReplay          │   │
│  │ circuitBreaker │ independentVerifier │ deploymentEvidence           │   │
│  │ adversarialSuite                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────────┐
│                           DATA LAYER                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ MongoDB (32 models)                                                 │   │
│  │ JournalEntry │ LedgerEntry │ AccountBalance │ ChartOfAccounts      │   │
│  │ Invoice │ Expense │ Payment │ BankStatement │ TDSEntry │ TDSChallan│   │
│  │ GSTReturn │ ComplianceSignal │ ComplianceFiling │ SetuDispatch     │   │
│  │ UnifiedTrace │ RuntimeProof │ AuditEvent │ AuditLog │ Company     │   │
│  │ CostCentre │ FinancialPeriod │ CompanySettings │ User │ TallyExport│   │
│  │ TallyImport │ RLExperience │ ReconcileRecord │ TDSQuarterlyGroup  │   │
│  │ TDSValidationLog │ ComplianceValidationLog │ JournalLine │ Account │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Redis (caching) — optional                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Decimal.js (precision arithmetic)                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Governance Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GOVERNANCE ROUTES                                    │
│  /api/v1/governance/status                                                  │
│  /api/v1/governance/capabilities                                            │
│  /api/v1/governance/provenance                                              │
│  /api/v1/governance/replay                                                  │
│  /api/v1/governance/circuit-breakers                                        │
│  /api/v1/governance/verification                                            │
│  /api/v1/governance/adversarial                                             │
│  /api/v1/governance/evidence                                                │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼───────────────────────────────────────┐
│                      GOVERNANCE SERVICES                                    │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │ Capability       │ │ Provenance       │ │ Replay           │           │
│  │ Registry         │ │ Chain            │ │ System           │           │
│  │ (350 lines)      │ │ (220 lines)      │ │ (180 lines)      │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │ Independent      │ │ Deployment       │ │ Adversarial      │           │
│  │ Verifier         │ │ Evidence         │ │ Suite            │           │
│  │ (280 lines)      │ │ (230 lines)      │ │ (200 lines)      │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│  ┌──────────────────┐ ┌──────────────────┐                                │
│  │ Circuit          │ │ Policy           │                                │
│  │ Breaker          │ │ Engine           │                                │
│  │ (180 lines)      │ │ (250 lines)      │                                │
│  └──────────────────┘ └──────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Request Processing
```
Request → CORS → Helmet → Rate Limit → Sanitize
  → authorityEnforcement (existing)
  → policyEnforcement (NEW)
    → Capability Resolution
    → Read-Only Check
    → Collection Check
    → Policy Decision (ALLOW/DENY)
  → protect (auth)
  → Route Handler
    → Controller
      → guardCollection() (NEW)
      → Service Layer
        → Capability Registry
        → Provenance Chain (NEW)
        → Deterministic Replay (NEW)
        → Circuit Breaker (NEW)
      → Response
```

### Governance Pipeline
```
Governance Request
  → Policy Engine
  → Capability Registry Query
  → Service Execution
  → Provenance Recording
  → Replay Recording
  → Response
```

### Evidence Pipeline
```
Deployment Event
  → Deployment Evidence Generator
  → Evidence Record
  → Content Hash
  → Manifest Generation
```

## Integration Points

### TANTRA Integration
```
ARTHA → TANTRA Runtime
  ├── Registration
  ├── Event Emission
  ├── Heartbeat
  └── Health Reporting
```

### SETU Pipeline
```
ARTHA → SETU API
  ├── Signal Dispatch
  ├── Retry Logic
  ├── Dead Letter Queue
  └── Acknowledgement
```

### BHIV Capability Registry
```
ARTHA ← BHIV Registry
  ├── Contract Registration
  ├── Authority Validation
  └── Runtime Enforcement
```
