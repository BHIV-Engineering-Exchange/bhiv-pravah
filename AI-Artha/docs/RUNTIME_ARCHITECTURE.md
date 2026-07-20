# Runtime Architecture

## Overview

ARTHA operates as a governed runtime service within the BHIV ecosystem. The architecture follows capability-based security principles with deterministic execution, replayability, observability, and authority enforcement.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  React 18 + Vite → Zustand (auth) → React Query (server state) │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTP/HTTPS
┌─────────────────────────────▼───────────────────────────────────┐
│                         API GATEWAY                             │
│  CORS → Helmet → Rate Limit → Input Sanitization               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                    AUTHORITY LAYER                              │
│  authorityEnforcement (existing)                                │
│  policyEnforcement (NEW - runtime enforcement)                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                    AUTHENTICATION LAYER                         │
│  JWT Bearer Token → protect middleware → role authorization     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                    ROUTE LAYER                                  │
│  24 route groups → 26 controllers                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                    SERVICE LAYER                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Business Services                                       │   │
│  │ ledger │ invoice │ expense │ tds │ gst │ banking │ etc  │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Governance Services (NEW)                               │   │
│  │ capabilityRegistry │ provenanceChain │ deterministicReplay│  │
│  │ circuitBreaker │ independentVerifier │ deploymentEvidence │  │
│  │ adversarialSuite                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                    DATA LAYER                                   │
│  MongoDB (32 models) │ Redis (caching) │ Decimal.js            │
└─────────────────────────────────────────────────────────────────┘
```

## Capability-Based Security

### Capability Registry
- **Single Source of Truth:** All capability contracts loaded from `contracts/capability_contracts/*.json`
- **Runtime Queries:** `resolveRoute()`, `canMutateCollection()`, `validateInput()`
- **Contract Integrity:** SHA-256 hash verification for tamper detection

### Policy Engine
- **Runtime Enforcement:** Middleware-level enforcement of capability boundaries
- **Deterministic Decisions:** ALLOW/DENY with audit recording
- **Collection Guards:** Controllers call `guardCollection()` to verify mutations

### Authority Boundaries
- **9 Capability Contracts:** Each defines owned collections, blocked mutations, API endpoints
- **Route Mapping:** 32 route-to-capability mappings
- **Read-Only Protection:** Write operations blocked on read-only capabilities

## Deterministic Execution

### Hash Chain Integrity
- **Journal Entries:** HMAC-SHA256 hash chain (prevHash + entry data)
- **Ledger Entries:** Individual hash chain per account
- **Verification:** Walk chain from tip to genesis, verify each link

### Deterministic Replay
- **Execution Recording:** Input/output captures with deterministic hashes
- **Replay Verification:** SHA-256 hash comparison for determinism
- **Proof Generation:** Replay proof documents for independent verification

## Observability

### Provenance Chain
- **Append-Only Log:** Hash-linked governance decisions
- **Event Types:** Capability decisions, policy events, contract verification, deployments, adversarial attempts
- **Integrity Verification:** Chain walk with hash validation

### Circuit Breakers
- **6 Registered Breakers:** mongodb, redis, setu_api, tantra_runtime, ocr_service, evidence_pipeline
- **State Machine:** CLOSED → OPEN → HALF_OPEN
- **Configurable Thresholds:** Failure count, recovery time, monitoring window

### Deployment Evidence
- **Evidence Types:** Clean deployment, fresh install, startup, health, failover, contract enforcement, authority rejection, adversarial attempts, replay verification
- **Content Hash:** SHA-256 for tamper detection
- **Manifest Generation:** Complete deployment evidence manifest

## Integration Points

### TANTRA Integration
- **Registration:** Bridge registered as governed runtime participant
- **Event Emission:** Runtime events emitted to TANTRA
- **Heartbeat:** Periodic health status reporting

### SETU Pipeline
- **Signal Dispatch:** Compliance signals dispatched to SETU
- **Retry Logic:** Exponential backoff with dead letter queue
- **Acknowledgement:** SETU callbacks processed

### BHIV Capability Registry
- **Contract Registration:** Capabilities registered with BHIV
- **Authority Validation:** Boundaries validated against BHIV contracts
- **Runtime Enforcement:** Policy engine enforces BHIV authority

## Data Flow

### Invoice Lifecycle
```
Create (Draft) → Send (JE: DR AR 1100, CR Revenue 4000, CR GST 2311/2312/2313)
  → Payment (JE: DR Cash 1010, CR AR 1100)
  → Status: draft → sent → partial → paid
```

### Trace Pipeline
```
Transaction → Journal Entry → Signals → Compliance Filing → SETU Dispatch
  → SETU Callback → Runtime Proof
```

### Governance Pipeline
```
Request → Policy Engine → Capability Resolution → Route Handler
  → Service → Provenance Recording → Replay Recording
  → Response
```

## Security Model

### Authentication
- JWT Bearer tokens with multiple secret support
- Token expiration enforcement
- Refresh token support

### Authorization
- Role-based access control (admin, accountant, viewer)
- Capability-based authorization
- Collection-level mutation authorization

### Adversarial Resistance
- 12 adversarial test scenarios
- All attacks blocked with deterministic evidence
- Safe failure with audit recording
