# 🛠️ Operational Dashboard Foundation MVP - Deploy & Run Guide

This document describes how to configure, run, and verify the role-based dashboard, alert, action, and audit trail backend services.

---

## 1. Local Development Setup

### Python Environment
Activate your virtual environment and install dependencies:
```bash
pip install -r requirements.txt
```

### Database Seeding
The database tables are automatically initialized on FastAPI startup. To seed the database with the realistic **5,000 students, 200 teachers, and 20 institutions** dataset, run:
```bash
python scripts/seed_dashboard_scale.py
```
*Note: This script uses optimized bulk mapping operations and pre-computed password hashing, completing the seeding of over 40,000 records in under 25 seconds.*

### Running the Development Server
To launch the FastAPI dev server on `http://localhost:3000`:
```powershell
./run_dev.ps1
```

---

## 2. Docker Setup

To build and run the entire stack (Gurukul Backend, Frontend, and EMS Backend/Frontend) via Docker Compose:
```bash
cd docker
docker compose up --build
```
This mounts the backend container on port `3000` and configures environment variables automatically.

---

## 3. Core API Endpoints

### Health Endpoint
Verify service diagnostics:
*   `GET http://localhost:3000/health`

### Role-Based Dashboard Aggregation
Retrieve role-specific telemetry summaries (KPIs, open alerts, pending actions, recent activity):
*   `GET http://localhost:3000/api/v1/dashboard/student` (restricted to Student & above)
*   `GET http://localhost:3000/api/v1/dashboard/teacher` (restricted to Teacher & above)
*   `GET http://localhost:3000/api/v1/dashboard/institution-admin` (restricted to Admin & above)
*   `GET http://localhost:3000/api/v1/dashboard/regional-admin` (restricted to Regional Admin)
*   `GET http://localhost:3000/api/v1/dashboard/aggregate` (Context-aware; resolves metrics based on the logged-in user's role)

### Alert Engine
Manage anomalies and system flags:
*   `POST http://localhost:3000/api/v1/alerts` (Create alert)
*   `GET http://localhost:3000/api/v1/alerts` (List alerts with filters)
*   `PUT http://localhost:3000/api/v1/alerts/{id}/assign` (Assign alert)
*   `PUT http://localhost:3000/api/v1/alerts/{id}/status` (Update status: OPEN, RESOLVED, CLOSED)

### Action Engine
Manage tasks and status lifecycles:
*   `POST http://localhost:3000/api/v1/actions` (Create action)
*   `GET http://localhost:3000/api/v1/actions` (List actions with filters)
*   `PUT http://localhost:3000/api/v1/actions/{id}/assign` (Assign action)
*   `PUT http://localhost:3000/api/v1/actions/{id}/status` (Update status: Created, Assigned, In Progress, Completed, Closed, Cancelled)

### Audit & Provenance History
Track operations performed across the system:
*   `GET http://localhost:3000/api/v1/audit-logs` (Queryable list of operations)

---

## 4. Verification Protocols
You can verify the backend correctness by running the dashboard test suite:
```bash
pytest backend/tests/test_dashboard.py -v
```
This verifies role restrictions, alert/action state transitions, audit logging, and payload boundaries.
