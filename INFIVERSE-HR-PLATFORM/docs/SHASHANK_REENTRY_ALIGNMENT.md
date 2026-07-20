# SHASHANK RE-ENTRY ALIGNMENT
**Document Type**: Phase 1 — Architecture Refresh
**Author**: Shashank (Sampada, Support Builder)
**Created**: 2026-05-26 | **For**: INFIVERSE-HR (Sampada / BHIV)

> READ THIS BEFORE CONTRIBUTING ANYTHING.
> Your re-entry role is Support Builder — NOT system owner.
> Architecture decisions remain with Rishabh Yadav.

---

## 1. System Purpose

**INFIVERSE-HR (Sampada / BHIV)** is an enterprise AI-enabled recruitment platform designed to orchestrate multi-tenant job and candidate lifecycle management with semantic AI matching, workflow automation, and multi-channel notifications.

### Business Value
- Reduces recruitment time through AI-powered candidate-job semantic matching using Phase 3 sentence transformers
- Automates candidate workflow notifications across Email, WhatsApp, and Telegram channels
- Provides HR operational visibility into recruitment pipeline and candidate status
- Supports competing tenant companies with secure data isolation and multi-tenant architecture
- Integrates with external workflow systems (Complete-Infiverse / EMS) for task management

### Technical Scope
- **Scale**: 111 operational endpoints across 3 microservices
- **Architecture**: Layered microservices with constitutionally-enforced role separation
- **Database**: MongoDB Atlas primary persistence with 14+ collections
- **Authentication**: Triple-layer model (API Key + Client JWT + Candidate JWT)
- **UI**: Multi-portal architecture (Candidate, Recruiter, Client portals)
- **Notifications**: Email (Gmail), WhatsApp (Twilio), Telegram

---

## 2. Constitutional Positioning

### The Locked Separation Model

INFIVERSE-HR implements a **constitutionally enforced layered authority model**. Every role has defined authority limits. This separation is **non-negotiable** — it is the constitutional foundation of the system.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  INFIVERSE-HR CONSTITUTIONAL LAYER MODEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  LAYER 3 — EXECUTION (Highest Authority)
  ┌────────────────────────────────────────┐
  │ Niyantran (Orchestration Authority)    │
  │ Gateway Service, LangGraph Service     │
  │ → Executes all state-changing actions  │
  │ → Owns workflow triggers               │
  │ → Enforces authorization decisions     │
  └────────────────────────────────────────┘
              ↑ (approval gate)
  LAYER 2 — APPROVAL / PARTICIPATION
  ┌────────────────────────────────────────┐
  │ SETU (Approval Bridge)                 │
  │ → Receives intelligence signals        │
  │ → Evaluates recommendations            │
  │ → Approves or rejects before execution │
  │ → Does NOT execute independently       │
  └────────────────────────────────────────┘
              ↑ (signal flow)
  LAYER 1 — VISIBILITY / INTELLIGENCE
  ┌────────────────────────────────────────┐
  │ Sampada (Support Builder / You)        │
  │ → Observes, documents, traces          │
  │ → Provides intelligence signals        │
  │ → READ-ONLY on execution authority     │
  └────────────────────────────────────────┘
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Your Re-Entry Role: SAMPADA (Support Builder)

**Constitutional Authority**: Intelligence + Signals + Visibility

**What You Own**:
- Operational dashboards and intelligence displays
- Trace continuity and request tracking across all services
- Replay reconstruction from audit logs
- Failure state visibility and observability coverage
- Accurate, current documentation of system behavior and architecture
- Developer onboarding and entry guides

**What You DO NOT Own**:
- Execution authority (state-changing decisions)
- Orchestration (workflow triggering, business logic changes)
- Authorization decisions (who can do what)
- Resource allocation or infrastructure
- Acceptance decisions

**Key Constraint**: **Visibility ≠ Execution**
- You can observe and report what happened
- You cannot change what will happen
- You provide intelligence; others make decisions
- You cannot convert observational access into action authority

---

## 3. Layer Separation Understanding

### All Named Roles in the INFIVERSE-HR Architecture

This section maps every named role to its constitutional position, authority, and boundaries.

---

### Role 1: SAMPADA — Intelligence + Signals + Visibility

**Layer**: Layer 1 (Visibility)
**Owner**: Shashank (Support Builder) during this sprint

**Purpose**: Provide the intelligence layer — observations, traces, dashboards, and signals that inform decisions without making them.

**Authority**:
- ✅ Read any data for observability purposes
- ✅ Generate intelligence signals (match scores, anomaly flags, performance metrics)
- ✅ Document system behavior and architecture
- ✅ Collect trace evidence and produce replay reconstructions
- ✅ Run non-disruptive test scenarios (enforcement checks, failure simulations)

**Forbidden Actions**:
- ❌ Mutate database state (no writes that change business data)
- ❌ Trigger workflows (no calls to LangGraph that change candidate/job states)
- ❌ Override authentication or authorization decisions
- ❌ Propose architectural changes without Rishabh's direction

**How Sampada Feeds the System**:
```
Sampada observes → generates signal → SETU evaluates → Niyantran executes
(READ ONLY)         (advisory only)   (decision gate)   (state change)
```

---

### Role 2: NIYANTRAN — Orchestration Authority (Execution Layer)

**Layer**: Layer 3 (Execution)
**Owner**: Rishabh Yadav and the Backend Services Team

**Purpose**: The execution engine of the platform. Niyantran controls all state-changing operations, orchestration flows, and authority enforcement.

**In the Codebase**:
- **Gateway Service** (`backend/services/gateway/app/main.py`) — The primary Niyantran implementation
- **LangGraph Service** (`backend/services/langgraph/`) — Workflow orchestration node

**Authority**:
- ✅ Create, update, delete jobs, candidates, applications, interviews, offers
- ✅ Trigger and manage workflow state machines
- ✅ Enforce authentication (accepts or rejects every request)
- ✅ Execute business logic (matching, notifications, document requests)
- ✅ Write to all MongoDB collections
- ✅ Override or rollback system states

**Interaction with Sampada**:
- Niyantran's actions generate logs that Sampada can observe
- Sampada provides intelligence signals (match scores, anomaly alerts) to inform Niyantran
- Sampada CANNOT instruct Niyantran to execute anything

---

### Role 3: SETU — Approval Bridge (Participation Layer)

**Layer**: Layer 2 (Approval/Participation)
**Owner**: Downstream decision-makers; orchestrated by Rishabh's direction

**Purpose**: SETU acts as the approval gate between intelligence signals and execution. It receives Sampada's signals, evaluates them, and makes recommendations that Niyantran can execute.

**Conceptual Position**:
```
Sampada sends: "Candidate X has 0.92 match score for Job Y"
SETU evaluates: "Based on score + criteria, recommend shortlisting"
Niyantran executes: Candidate status updated to SHORTLISTED
```

**In Practice**:
- SETU is represented by recruiter/client approval actions in the portal
- Shortlist decisions, interview confirmations, offer approvals are all SETU actions
- SETU does not execute independently — it gates the path to Niyantran

**Why This Matters for Sampada**:
- You provide signals TO SETU (via dashboard intelligence)
- You observe the outcome AFTER SETU approves and Niyantran executes
- You CANNOT bypass SETU to directly instruct Niyantran

---

### Role 4: SARATHI — Navigation and Guidance

**Layer**: Cross-layer (operates between Visibility and Approval)
**Owner**: Rishabh Yadav's direction team

**Purpose**: Sarathi provides navigation and guidance signals — helping route decisions through the correct approval pathways. Think of Sarathi as the system's internal compass: it ensures that signals reach the right decision-makers.

**Function**:
- Routes intelligence signals from Sampada to appropriate SETU decision-makers
- Guides candidates and recruiters through complex multi-step workflows
- Provides contextual prompts ("next step is interview scheduling")
- Does NOT make the decision — guides toward the decision point

**In the Codebase**:
- Sarathi logic is embedded in the LangGraph notification flow
- The "what happens next" automation (interview scheduling prompts, offer extension guidance) is Sarathi's functional expression
- Webhook events like `candidate-shortlisted` → "schedule interview" follow-up is Sarathi guiding the process

---

### Role 5: BUCKET — Data Collection and Holding Layer

**Layer**: Infrastructure/Data Layer
**Owner**: Infra team (Vinayak/Raj), governed by Rishabh

**Purpose**: Bucket is the data holding and collection layer — responsible for receiving, storing, and making available all signals, events, audit logs, and operational data that other layers depend on.

**In the Codebase**:
- **MongoDB Atlas** is the primary Bucket implementation
- **Audit log collection** (`audit_logs` collection) is the core bucket for replay and observability
- **RL feedback collection** (`rl_feedback`) is the bucket for intelligence model inputs
- **CSP violation log** (`security_csp`) is the security signal bucket

**Bucket Roles in Evidence Gathering**:
- Sampada reads FROM the Bucket (audit logs, feedback, health metrics)
- Niyantran writes TO the Bucket (all state changes)
- SETU decisions are recorded IN the Bucket (approval timestamps, decision metadata)

**Constitutional Rule**: Sampada can READ the Bucket but CANNOT write to it as part of its support role. Evidence collection is read-only access to bucket data.

---

### Role 6: OBSERVABILITY / INSIGHT ROLE — Sampada's Primary Function

**Layer**: Layer 1 (Visibility)
**Owner**: Shashank (Sampada) — this IS your role

**Purpose**: This is the primary mission of the Sampada re-entry. The Observability/Insight role is responsible for:

**Trace Continuity**:
- Track every request from entry to resolution across all services
- Assign and propagate correlation IDs (`X-Correlation-ID` header)
- Document timestamp chains showing service-to-service propagation
- Produce: `evidence/trace-continuity/` artifacts

**Replay Reconstruction**:
- Read the Bucket (audit logs) to reconstruct historical workflow states
- Prove that the system's behavior is deterministic and recoverable
- Build scripts that replay operations from logs to verify state consistency
- Produce: `evidence/replay/` artifacts

**Failure Observability**:
- Simulate controlled, non-disruptive failure scenarios
- Verify that error states are captured with full context (request, state, error, recovery path)
- Confirm that services continue running after errors (graceful degradation)
- Produce: `evidence/failure/` artifacts

**Enforcement Verification**:
- Verify RBAC boundaries (wrong role → 403 Forbidden)
- Verify tenant isolation (Client B cannot access Client A's data)
- Verify authentication enforcement (no token → 401 Unauthorized)
- Produce: `evidence/enforcement/` artifacts

**Constitutional Signals**:
- Generate intelligence dashboards showing system health
- Provide match quality signals for recruiter decision support
- Flag anomalies without taking corrective action

---

## 4. Ownership Understanding

### Responsibility Matrix

| Domain | Owner | Shashank's Role | Boundary |
|--------|-------|----------------|----------|
| System Architecture | Rishabh Yadav | Observer | No changes without Rishabh |
| Backend Microservices | Rishabh / Backend team | Evidence collector | Read-only access |
| Frontend / Dashboard | Nikhil | Phase 4 support if requested | No frontend changes without Nikhil |
| Infrastructure / Docker | Vinayak | Blocker escalator | Cannot restart production containers |
| Network / DNS / Ports | Raj | Blocker escalator | Cannot change port mappings |
| Documentation | Shashank (Sampada) | **Primary owner** | Full ownership |
| Trace Evidence | Shashank (Sampada) | **Primary owner** | Full ownership |
| Observability Scripts | Shashank (Sampada) | **Primary owner** | Full ownership |
| Convergence Proof Package | Shashank (Sampada) | **Primary owner** | For Rishabh's acceptance |
| Acceptance Sign-Off | Rishabh Yadav | Submitter | Cannot self-approve |

### Key Constraint on Ownership
```
What Sampada OWNS → Must not require execution authority to produce
What Sampada SUPPORTS → Must wait for direction from role owner before acting
What Sampada ESCALATES → Goes to Rishabh with full context, no suggested architecture
```

---

## 5. Boundary Understanding

### Non-Negotiable Rules (Locked — From Task17.md)

#### Rule 1: DO NOT Convert Visibility Into Execution Authority
```
❌ Wrong: "I can see candidates are stuck at review stage, so I'll update their status"
✅ Right: "Candidates are stuck at review stage. Here is the trace showing the delay.
          Rishabh to decide on corrective action."
```

#### Rule 2: DO NOT Create Parallel Signal Systems
```
❌ Wrong: "I'll add a webhook that bypasses LangGraph for faster notifications"
✅ Right: All notifications go through established LangGraph workflow.
         Document any notification gaps for Rishabh's attention.
```

#### Rule 3: DO NOT Restart Architecture Discussions
```
❌ Wrong: "Maybe SETU should have more authority over workflow triggers"
✅ Right: SETU's authority is constitutionally defined. If there's a gap,
         document it in CONVERGENCE_SUPPORT_LOG.md and escalate.
```

#### Rule 4: DO NOT Expand Scope Outside Convergence Needs
```
❌ Wrong: "While I'm here, let me add a new analytics dashboard feature"
✅ Right: Focus on trace, replay, enforcement, observability proofs only.
         New features require Rishabh's direction to commence.
```

#### Rule 5: DO NOT Challenge Constitutional Boundaries
```
❌ Wrong: "Sampada should be able to trigger interviews for efficiency"
✅ Right: Sampada role: Intelligence + Signals + Visibility. Fixed.
         Execution authority belongs to Niyantran (Gateway/LangGraph).
```

### Boundary Test: "Can Sampada Do This?"
When unsure if an action is within bounds, use this test:
1. Does it CHANGE any database state? → **NO** (escalate or observe only)
2. Does it TRIGGER a workflow? → **NO** (document and signal to SETU)
3. Does it CREATE a new architectural pattern? → **NO** (escalate to Rishabh)
4. Does it EXPAND Sampada's authority? → **NO** (preserve layer separation)
5. Does it DOCUMENT or OBSERVE? → **YES** ✅

---

## 6. Current Architecture Understanding

### Microservice Topology
```
Frontend (React + Vite :3000)
  │ HTTPS + JWT
  ▼
Gateway Service (:8000) — FastAPI 4.2.0
  │  Triple-layer auth: API Key | Client JWT | Candidate JWT
  │  80 core endpoints | Audit logging | Input validation (XSS/SQLi)
  │  Multi-tenant isolation (per-endpoint filtering)
  │
  ├──── AI Agent (:9000) — FastAPI 3.0.0
  │     Semantic matching (sentence transformers)
  │     GET /v1/match/{job_id}/top → ranked candidates
  │
  ├──── LangGraph (:9001) — FastAPI 1.0.0
  │     Workflow state machine
  │     Webhook endpoints: candidate-applied, shortlisted, interview-scheduled
  │     Notification dispatch: Email | WhatsApp | Telegram
  │
  └──── MongoDB Atlas
        14+ collections | Audit logs | RL feedback | CSP logs
```

### Authentication Architecture (Triple-Layer)

| Auth Type | Scope | JWT Payload | Use Case |
|-----------|-------|-------------|----------|
| **API Key** | Full system admin | N/A (bearer token) | Internal ops, testing, automation |
| **Client JWT** | Tenant-scoped | `{client_id, email, role:"client"}` | Client portal, job management |
| **Candidate JWT** | Self-service | `{candidate_id, email, role:"candidate"}` | Candidate portal |

### Multi-Tenant Isolation Model
```
Client A (TECH001)
  └── Their jobs → Only visible when authenticated as TECH001
  └── Their applications → Filtered by job ownership
  └── Attempt by STARTUP01 to access TECH001 job → 403 Forbidden

Client B (STARTUP01)
  └── Their jobs → Only visible when authenticated as STARTUP01
  └── Cross-tenant access → Blocked at Gateway (per-endpoint check)
```

### Monitoring Architecture
```
AdvancedMonitor class (monitoring.py)
  ├── CPU/Memory metrics (psutil)
  ├── Database connection health (motor/pymongo)
  ├── API latency tracking (middleware hooks)
  ├── Prometheus metrics endpoint
  └── Structured logging → logs/bhiv_hr_platform.log
```

---

## 7. Re-Entry Observations

### Current Sprint Context (2026-05-26)
Rishabh's active convergence sprint requires formal proof across 10 evidence categories before acceptance. This is the immediate focus for the Sampada re-entry.

### What Was Achieved in This Sprint
| Deliverable | Status | Evidence |
|------------|--------|---------|
| All 5 docs/ files updated | ✅ Complete | This session |
| REVIEW_PACKET.md (10 parts) | ✅ Complete | Root directory |
| Live E2E execution trace | ✅ Captured | trace-continuity/ |
| RBAC enforcement tests | ✅ 5/5 passed | enforcement/ |
| Tenant isolation verified | ✅ 403 confirmed | enforcement/ |
| Replay reconstruction | ✅ SUCCESS | replay/ |
| Failure observability (8 scenarios) | ✅ 8/8 passed | failure/ |
| Constitutional boundary verification | ✅ Complete | boundaries/ |

### What Remains
1. **Docker restart** — Services went down after server restart. Vinayak/Raj to restart Docker Desktop, then run `docker compose up -d` in backend/.
2. **Rishabh's acceptance sign-off** — Submit REVIEW_PACKET.md for formal review.
3. **Nikhil coordination** — Phase 4 frontend wiring only if Rishabh explicitly requests.

### How to Reproduce All Evidence
```powershell
# 1. Start backend (Docker must be running)
cd backend
docker compose -f docker-compose.production.yml up -d

# 2. Verify all 3 services are healthy
curl http://localhost:8000/health
curl http://localhost:9000/health
curl http://localhost:9001/health

# 3. Re-run full evidence collection
node C:\Users\Shani\.gemini\antigravity\brain\be0034f8-3c5f-4337-a805-758c276b8991\scratch\run_convergence_evidence.js

# 4. Re-run controlled failure simulations
node C:\Users\Shani\.gemini\antigravity\brain\be0034f8-3c5f-4337-a805-758c276b8991\scratch\test_failure_simulations.js

# 5. Re-run replay reconstruction
node evidence/replay/replay_script.js
```

### Key Takeaways for Your Re-Entry
1. **Your Role**: Support Builder — visibility, intelligence, documentation. NOT execution authority.
2. **Your Leader**: Rishabh sets direction; you contribute within it. No alternate architectures.
3. **Your Constraint**: Visibility ≠ Execution. Preserve all 5 layer separation rules.
4. **Your Focus**: Trace, replay, enforcement, observability proofs for Rishabh's acceptance.
5. **Your Escalation**: Any ambiguity → document and escalate to Rishabh. Never self-decide.

---

## References

| Document | Purpose |
|----------|---------|
| `Task17.md` | Full re-entry requirements and non-negotiable rules |
| `REVIEW_PACKET.md` | 10-part convergence proof package |
| `SAMPADA_CURRENT_STATE.md` | Developer handover (12 sections) |
| `docs/EXECUTION_UNDERSTANDING_SUMMARY.md` | Sprint priorities and acceleration points |
| `docs/CONVERGENCE_SUPPORT_LOG.md` | Timestamped work log |
| `docs/ALIGNMENT_SYNC_NOTES.md` | Team alignment decisions |
| `backend/handover/ROLE_MATRIX.md` | Authentication and permission matrix |
| `backend/handover/SYSTEM_BEHAVIOR.md` | Architecture specifications and contracts |
| `backend/docs/api/API_DOCUMENTATION.md` | Complete API reference (111 endpoints) |
| `evidence/` | All convergence proof artifacts |
