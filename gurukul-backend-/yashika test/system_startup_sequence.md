# Global System Startup Sequence (Gurukul + EMS + Frontend)

This document outlines the deterministic startup order for the complete Gurukul ecosystem to ensure high availability and zero silent failures during deployment.

## 1. Dependency Layer (Manual/Infrastructure)
- **PostgreSQL**: Must be accessible for Core Backend and EMS Backend.
- **MongoDB**: Must be accessible for Karma Tracker features.
- **Environment Variables**: All `.env` files must be laden before service startup.

## 2. Service Layer (Orchestrated)

### Phase 1: Core Backend (Port 3001)
1. **Watchdog Initialization**: 20s timeout wrapper starts.
2. **Auth Router Registration**: Critical path for user entry.
3. **Database Initialization**: SQLAlchemy table verification.
4. **Background Task Launch**: Lazy loading of Summarizer, Soul, and Karma routers.
5. **Health Readiness**: `/health` returns `200 OK` (SQL+Mongo check).

### Phase 2: EMS Backend (Port 3002)
1. **Watchdog Initialization**: Watchdog starts for EMS.
2. **PostgreSQL Check**: Verifies school management DB connectivity.
3. **Multi-Tenant Router Load**: Auth, Schools, and Teacher/Student routers.
4. **Health Readiness**: `/health` returns `200 OK`.

### Phase 3: Frontend (Port 5173 / Production Build)
1. **Environment Audit**: Enforces `VITE_API_URL` check.
2. **Build Optimization**: Vite compiles assets.
3. **Sovereign Entry**: Server serves the static index.html.

## 3. Validation
- Run `./yashika\ task/stress_test_worker.py` to verify all services respond within <100ms.
