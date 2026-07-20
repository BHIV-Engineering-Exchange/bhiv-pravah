# File Index — ARTHA BHIV Ecosystem Integration

## New Files Created

| # | File Path | Lines | Purpose |
|---|-----------|-------|---------|
| 1 | `backend/src/services/capabilityRegistry.service.js` | 350 | Canonical capability registry — single source of truth for all capability contracts |
| 2 | `backend/src/middleware/policyEngine.js` | 250 | Runtime policy enforcement middleware with deterministic decisions |
| 3 | `backend/src/services/provenanceChain.service.js` | 220 | Immutable, append-only provenance chain for governance decisions |
| 4 | `backend/src/services/deterministicReplay.service.js` | 180 | Deterministic replay system for governance verification |
| 5 | `backend/src/services/circuitBreaker.service.js` | 180 | Circuit breaker pattern for fail-safe behaviour |
| 6 | `backend/src/services/independentVerifier.service.js` | 280 | Independent verification engine producing non-self-generated evidence |
| 7 | `backend/src/services/deploymentEvidence.service.js` | 230 | Deployment evidence generator for all deployment scenarios |
| 8 | `backend/src/services/adversarialSuite.service.js` | 200 | Genuine adversarial test suite with 12 attack vectors |
| 9 | `backend/src/routes/governance.routes.js` | 280 | Governance API routes (19 endpoints) |
| 10 | `docs/RUNTIME_ARCHITECTURE.md` | 150 | Runtime architecture documentation |
| 11 | `docs/INTEGRATION_GUIDE.md` | 200 | Integration guide with patterns and examples |
| 12 | `docs/DEPLOYMENT_GUIDE.md` | 200 | Production deployment guide |
| 13 | `docs/OPERATIONS_GUIDE.md` | 250 | Day-to-day operations guide |
| 14 | `docs/INCIDENT_RECOVERY_GUIDE.md` | 250 | Incident response and recovery procedures |
| 15 | `docs/AUTHORITY_BOUNDARY_GUIDE.md` | 200 | Authority boundary enforcement guide |
| 16 | `docs/CAPABILITY_REGISTRATION_GUIDE.md` | 200 | How to register new capabilities |
| 17 | `review_packets/REVIEW_PACKET.md` | 400 | Complete review packet for handover |
| 18 | `review_packets/review_code/README.md` | 100 | Review code overview and architecture map |
| 19 | `review_packets/review_code/file_index.md` | 50 | This file |
| 20 | `review_packets/review_code/critical_files.md` | 80 | Critical files explanation |
| 21 | `review_packets/review_code/architecture_map.md` | 100 | Architecture diagram |
| 22 | `review_packets/review_code/changed_files.md` | 50 | Changed files list |

## Modified Files

| # | File Path | Changes |
|---|-----------|---------|
| 1 | `backend/src/server.js` | Added BHIV ecosystem service imports, initialization, policy engine middleware, governance routes, startup logging, deployment evidence |
| 2 | `contracts/capability_contracts/capability_route_map.json` | Added governance route mapping, updated version to 1.1.0 |

## Total Lines Changed

- **New code:** ~2,800 lines
- **Modified code:** ~50 lines
- **Documentation:** ~2,000 lines
- **Total:** ~4,850 lines
