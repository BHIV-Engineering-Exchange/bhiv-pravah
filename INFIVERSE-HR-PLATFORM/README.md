# 🌌 INFIVERSE-HR (Sampada / BHIV)

Enterprise AI-enabled HR recruitment platform with dedicated portals for Candidates, Recruiters, and Clients. The backend consists of a Python FastAPI microservice suite, and the frontend is built using React + Vite + TypeScript.

---

## 🧭 Developer Onboarding Path (Start Here)

If this is your first day on the project, follow this exact sequence:

1. **Read** [QUICK_START.md](file:///c:/Users/Shani/Downloads/INFIVERSE-HR-PLATFORM-main/QUICK_START.md) to set up your local database and run the system.
2. **Review** the [REVIEW_PACKET.md](file:///c:/Users/Shani/Downloads/INFIVERSE-HR-PLATFORM-main/REVIEW_PACKET.md) to see the verified proofs, traces, and isolation verifications for the active sprint.
3. **Examine** documentation folders:
   - [SHASHANK_REENTRY_ALIGNMENT.md](docs/SHASHANK_REENTRY_ALIGNMENT.md) — System boundaries and constitutional separation model.
   - [EXECUTION_UNDERSTANDING_SUMMARY.md](docs/EXECUTION_UNDERSTANDING_SUMMARY.md) — Active convergence sprint goals and effort layout.
   - [SAMPADA_CURRENT_STATE.md](SAMPADA_CURRENT_STATE.md) — Developer Handover and current state documentation.
   - [ALIGNMENT_SYNC_NOTES.md](docs/ALIGNMENT_SYNC_NOTES.md) — Core sync decisions with System Owner Rishabh Yadav.

### Task19 (government-scale governance + live control center)

| Document | Purpose |
|----------|---------|
| [Task19.md](Task19.md) | Phase requirements and implementation status |
| [REVIEW_PACKET.md](REVIEW_PACKET.md) | Acceptance index for Rishabh review |
| [docs/TASK19_REQUIREMENT_EVIDENCE_MATRIX.md](docs/TASK19_REQUIREMENT_EVIDENCE_MATRIX.md) | Requirement → evidence mapping |
| [docs/TASK19_ACCEPTANCE_TEST_PACK.md](docs/TASK19_ACCEPTANCE_TEST_PACK.md) | pytest, E2E, and production smoke steps |
| [docs/CONTROL_CENTER_E2E_TEST_FRAMEWORK.md](docs/CONTROL_CENTER_E2E_TEST_FRAMEWORK.md) | `backend/tests/e2e/control_center/` runner |
| [docs/CENTRAL_CONTROL_LIVE_EXECUTION_CHECKLIST.md](docs/CENTRAL_CONTROL_LIVE_EXECUTION_CHECKLIST.md) | Live wiring + rollout verification |
| [docs/CENTRAL_CONTROL_API_CONTRACT_FREEZE.md](docs/CENTRAL_CONTROL_API_CONTRACT_FREEZE.md) | Frozen API surfaces for UI |
| [frontend/VERCEL_DEPLOYMENT.md](frontend/VERCEL_DEPLOYMENT.md) | Vercel env vars (`VITE_LANGGRAPH_SERVICE_URL`) |

Five governance boundary docs: `docs/SAMPADA_GOVERNMENT_SCALE_ARCHITECTURE.md`, `SAMPADA_POLICY_GOVERNANCE_MODEL.md`, `SAMPADA_FEDERATED_WORKFORCE_MODEL.md`, `SAMPADA_COMMAND_CENTER_GOVERNANCE_MODEL.md`, `SAMPADA_HUMAN_SAFETY_MODEL.md`.

---

## 💼 Portals & Main User Roles

- **Candidate Portal**: Profiles, job application lifecycle, tasks, scheduled interviews, and feedback.
- **Recruiter Console**: Job creations, applicant matching status, semantic search scores, notifications, and workflow executions.
- **Client Portal**: Active job openings, applicant pipelines, custom document requests (CV, Resume, NDAs), and feedback submissions.

---

## 🛠️ Core Technology Stack

### Frontend
- React 18, TypeScript, Vite, Vanilla CSS + Tailwind CSS, Axios + authorization interceptors.

### Backend Microservices (FastAPI)
- **Gateway Service (`:8000`)**: Core routing, triple-layer authentication (API Key, Client JWT, Candidate JWT), input validations (XSS/SQLi blocking), and Multi-Tenant Isolation rules.
- **AI Agent Service (`:9000`)**: Semantic candidate-job similarity matching using sentence transformers.
- **LangGraph Service (`:9001`)**: Workflow automation, notification dispatchers (Email, WhatsApp, Telegram), and state machine management.

### Database
- MongoDB Atlas (primary datastore).

### External Systems
- **Complete-Infiverse / EMS**: Downstream candidate task bridge.

---

## 🗺️ Project Structure

```text
INFIVERSE-HR-PLATFORM-main/
├── docs/                                 # Architectural & re-entry alignment documentation
│   ├── ALIGNMENT_SYNC_NOTES.md           # Decisions from team alignment syncs
│   ├── CONVERGENCE_SUPPORT_LOG.md        # Support builder work log
│   ├── EXECUTION_UNDERSTANDING_SUMMARY.md # Concise sprint priorities
│   └── SHASHANK_REENTRY_ALIGNMENT.md     # Layer separation and rules
├── evidence/                             # Verification proof artifacts
│   ├── boundaries/                       # Visibility boundary verification checks
│   ├── enforcement/                      # RBAC and tenant isolation logs
│   ├── entry-points/                     # Token templates and curl test examples
│   ├── failure/                          # Vulnerability blocks and failure logs
│   ├── general/                          # Unified verification summaries
│   ├── ownership/                        # Responsibility matrix
│   ├── replay/                           # Chronological state reconstruction
│   ├── tests/                            # Uptime logs and webhook responses
│   └── trace-continuity/                 # Correlation ID request logs
├── backend/                              # FastAPI backend services
│   ├── services/
│   │   ├── gateway/                      # Port 8000
│   │   ├── agent/                        # Port 9000
│   │   └── langgraph/                    # Port 9001
│   ├── run_services.py                   # Local multi-service launcher script
│   ├── setup_venv.bat                    # Virtual environment creation (Windows)
│   └── run_with_venv.bat                 # Activates venv & runs run_services.py
├── frontend/                             # React + Vite frontend source code
│   └── src/                              # Components, views, routing
├── QUICK_START.md                        # Quick setup guidelines
├── REVIEW_PACKET.md                      # Compilation of convergence proof
├── SAMPADA_CURRENT_STATE.md              # 12-section system handoff document
└── run_project.ps1                       # Complete background startup script
```

---

## 🏃 Local Setup and Startup

### Step 1: Backend Environment Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   copy .env.example .env
   ```
2. Open `backend/.env` and configure:
   - `DATABASE_URL` (MongoDB connection URI)
   - `API_KEY_SECRET`, `JWT_SECRET_KEY`, `CANDIDATE_JWT_SECRET_KEY`, `GATEWAY_SECRET_KEY`

### Step 2: Start Backend Services
- **Windows (Automatic bat flow)**:
  ```powershell
  cd backend
  .\setup_venv.bat
  .\run_with_venv.bat
  ```
- **Manual Flow**:
  ```bash
  cd backend
  python -m venv venv
  source venv/bin/activate  # venv\Scripts\activate on Windows
  pip install -r requirements.txt
  python run_services.py
  ```

This launches the three microservices at:
- Gateway: `http://localhost:8000`
- Agent: `http://localhost:9000`
- LangGraph: `http://localhost:9001`

### Step 3: Start Frontend App
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:3000`.

---

## 🐳 Docker Deployment

The platform is fully containerized for production setups.

1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Build and run containers in the background:
   ```bash
   docker compose -f docker-compose.production.yml up --build -d
   ```
3. Check container logs:
   ```bash
   docker compose -f docker-compose.production.yml logs -f gateway
   docker compose -f docker-compose.production.yml logs -f agent
   docker compose -f docker-compose.production.yml logs -f langgraph
   ```

---

## 🧪 Testing & Verification Scripts

We have provided a set of tools to verify system resilience, RBAC enforcement, and trace continuity locally:

### 1. Collect All Evidence Logs
```powershell
node C:\Users\Shani\.gemini\antigravity\brain\be0034f8-3c5f-4337-a805-758c276b8991\scratch\run_convergence_evidence.js
```
This performs a full E2E execution flow (job posting, AI matching, candidate application, LangGraph trigger, multi-tenant blocking, and downstream notifications) and records evidence files in the `evidence/` directory.

### 2. Run Controlled Failure Simulations
```powershell
node C:\Users\Shani\.gemini\antigravity\brain\be0034f8-3c5f-4337-a805-758c276b8991\scratch\test_failure_simulations.js
```
Validates XSS injection blocking, SQL injection prevention, weak password policy rejections, bad TOTP 2FA handling, and CSP observability log pipelines.

### 3. Replay State Reconstruction
```powershell
node evidence/replay/replay_script.js
```
Sequentially processes chronological audit logs to verify deterministic state recovery and transition mapping.

---

## 🔒 Constitutional Alignment Rules

As a developer working on the **Sampada** scope:
- **Visibility Only**: All dashboard and intelligence features are strictly read-only on execution authority. You must not introduce parallel orchestration frameworks or state-mutating handlers.
- **System Boundaries**: Escalation authority, database schema mutations, security authorization overrides, and final prioritization remain with System Owner **Rishabh Yadav**.