# Task19 Requirement → Evidence Matrix

**Updated:** 2026-06-03  
**Scope:** Governance deliverables (Phases 1–5) + runtime hardening + production deployment

| Task19 requirement (summary) | Status | Runtime evidence | Verification |
|-----------------------------|--------|------------------|--------------|
| Government-scale multi-org boundaries documented | Complete | `docs/SAMPADA_GOVERNMENT_SCALE_ARCHITECTURE.md` | Doc review |
| Policy/governance separation documented | Complete | `docs/SAMPADA_POLICY_GOVERNANCE_MODEL.md` | Doc review |
| Federated workforce model documented | Complete | `docs/SAMPADA_FEDERATED_WORKFORCE_MODEL.md` | Doc review |
| Command center governance model documented | Complete | `docs/SAMPADA_COMMAND_CENTER_GOVERNANCE_MODEL.md` | Doc review |
| Human safety model documented | Complete | `docs/SAMPADA_HUMAN_SAFETY_MODEL.md` | Doc review |
| Centralized tenant/org/policy scope enforcement | Complete | `backend/services/gateway/app/control_center_governance.py`, scoped `/v1/candidates/stats` | `backend/tests/gateway/test_control_center_governance.py` |
| Live audit write + read + replay APIs | Complete | `POST/GET /v1/control-center/audit-events`, `GET /v1/control-center/audit-replay` | Acceptance pack + E2E |
| Backend-driven funnel/dept aggregates (no synthetic default) | Complete | `GET /v1/control-center/dashboard-aggregates` | Frontend hiring zone + E2E |
| Cross-service correlation propagation | Complete | Gateway/Agent/LangGraph `X-Correlation-ID` middleware | Health responses include `correlation_id` |
| Agent/LangGraph authz alignment (sensitive ops) | Complete | RL `POST /rl/retrain` requires API key; health governance metadata | `test_control_center_governance.py` |
| Control center live replay (no seeded default) | Complete | `ControlCenter.tsx` → `fetchControlCenterAuditReplay` | UI replay zone; `source: audit_logs` |
| Policy scope visible in UI | Complete | `readPolicyScopeLabel` + data-scope strip in `ControlCenter.tsx` | Manual `/control` |
| Parallel load + 30s silent refresh | Complete | `Promise.all` in `loadControlCenterData`; `CONTROL_CENTER_REFRESH_MS = 30_000` | Code review + UI |
| Role-gated control center + nav discoverability | Complete | `ProtectedRoute`, sidebars when `VITE_ENABLE_CONTROL_CENTER=true` | Manual role test |
| E2E control center framework | Complete | `backend/tests/e2e/control_center/`, `docs/CONTROL_CENTER_E2E_TEST_FRAMEWORK.md` | `run_control_center_e2e.py` (8 pass / 2 skip without JWT) |
| End-to-end acceptance pack | Complete | `docs/TASK19_ACCEPTANCE_TEST_PACK.md` | pytest governance + E2E |
| Review packet objective closure | Complete | `REVIEW_PACKET.md` § Task19 Runtime Evidence | Acceptance reviewer |
| Production deployment (Render + Vercel) | Complete (health) | Render gateway/agent/langgraph `/health` → 200 (2026-06-03) | `docs/CENTRAL_CONTROL_LIVE_EXECUTION_CHECKLIST.md` §F |
| Production UI smoke + JWT matrix on prod | Pending | Vercel `/control` with Render URLs in service cards | Checklist §F open items |

## Doc-only / no full runtime (Task19 constitutional scope)

| Requirement area | Status | Notes |
|------------------|--------|-------|
| Ministry→office hierarchy in datastore | Doc only | Architecture doc; hiring DB still tenant/job scoped |
| Policy engine / rule provenance runtime | Doc only | Patterns in governance model; not a live policy engine |
| Full SETU cross-domain signal exchange | Partial | Convergence map + correlation; not all owner APIs wired |
| Ownership metadata beyond correlation IDs | Partial | `policy_scope` on control-center responses; not platform-wide |

## Former runtime gaps (closed)

1. **Seeded replay trace** → live scoped audit replay API + UI wiring.
2. **Platform-wide stats for scoped roles** → `compute_scoped_candidate_stats` with job-id isolation.
3. **Synthetic funnel/dept visuals** → MongoDB aggregates by pipeline stage and job department.
4. **Fragmented auth on LangGraph RL retrain** → API key required.
5. **Missing acceptance mapping** → matrix + pytest + E2E suite.
6. **Rollout “pending only”** → Render+Vercel live; production UI/JWT canary still open in checklist §F.
