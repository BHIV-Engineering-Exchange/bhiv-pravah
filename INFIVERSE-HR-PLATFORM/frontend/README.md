# INFIVERSE-HR Frontend

React + TypeScript single-page app for candidate, recruiter, and client portals.

## Start here (0 knowledge)

Follow this order:

1. Complete root setup first: `../QUICK_START.md`
2. Start backend services and confirm `http://localhost:8000/health`
3. Start frontend (`npm run dev`) and open `http://localhost:3000`
4. Test login page (`/auth`)
5. Read auth flow: `AUTHENTICATION_STRUCTURE.md`

If login fails, fix backend/env first. Most frontend errors are API base URL or token related.

## Stack

- React 18
- TypeScript
- Vite
- React Router
- Tailwind CSS
- Axios (`src/services/api.ts`)
- React Hot Toast

## Local setup

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Default app URL: `http://localhost:3000`

## Environment

In `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

The frontend talks to gateway endpoints via this base URL.

Beginner check:

- If backend is local, keep `http://localhost:8000`.
- If backend is remote, replace this URL with remote gateway URL.

## Scripts

- `npm run dev` - start dev server
- `npm run build` - production build
- `npm run preview` - preview production build
- `npm run lint` - lint checks

## Route map (from `src/App.tsx`)

### Public

- `/auth`

### Candidate

- `/candidate/dashboard`
- `/candidate/profile`
- `/candidate/jobs`
- `/candidate/applied-jobs`
- `/candidate/interviews`
- `/candidate/tasks`
- `/candidate/tasks/:taskId`
- `/candidate/feedback`

### Recruiter

- `/recruiter`
- `/recruiter/create-job`
- `/recruiter/upload-candidates`
- `/recruiter/candidate-search`
- `/recruiter/screening`
- `/recruiter/applicants/:jobId`
- `/recruiter/schedule-interview`
- `/recruiter/values-assessment`
- `/recruiter/feedback/:candidateId`
- `/recruiter/export-reports`
- `/recruiter/client-jobs`
- `/recruiter/batch-operations`
- `/recruiter/automation`

### Client

- `/client`
- `/client/dashboard`
- `/client/jobs`
- `/client/candidates`
- `/client/matches`
- `/client/live-monitoring`
- `/client/reports`

## Important frontend behaviors

- Role-based access is enforced with `ProtectedRoute`.
- Auth state is managed in `AuthContext`.
- Tokens and user metadata are stored through `authStorage` (sessionStorage-first).
- Axios interceptor injects `Authorization: Bearer <token>`.
- Role navbar notification polling updates unread count and triggers background refresh events.
- Candidate/client/recruiter document workflows are surfaced in:
  - `src/pages/candidate/AppliedJobs.tsx`
  - `src/pages/client/ClientDashboard.tsx`
  - `src/pages/recruiter/Dashboard.tsx`

## Folder guide

```text
frontend/
├── src/
│   ├── components/            # shared UI + layouts + navbars
│   ├── context/               # auth/theme/recruiter connection state
│   ├── pages/
│   │   ├── auth/
│   │   ├── candidate/
│   │   ├── recruiter/
│   │   └── client/
│   ├── services/
│   │   ├── api.ts             # primary backend API client
│   │   └── authService.ts     # login/register/token operations
│   ├── utils/
│   │   └── authStorage.ts
│   └── App.tsx
└── AUTHENTICATION_STRUCTURE.md
```

## Build and verification checklist

1. Run backend services (gateway + agent + langgraph).
2. Run `npm run dev`.
3. Verify login for each role (`candidate`, `recruiter`, `client`).
4. Verify key pages:
   - Candidate tasks and applied jobs document upload
   - Client applicants tab and document request flow
   - Recruiter applicants tab and document review flow
5. Run `npm run build` before handover or deployment.

## Related docs

- Auth deep dive: `frontend/AUTHENTICATION_STRUCTURE.md`
- Root quick start: `QUICK_START.md`
- Backend docs index: `backend/docs/README.md`

## Full file locations

- `INFIVERSE-HR/frontend/README.md`
- `INFIVERSE-HR/frontend/AUTHENTICATION_STRUCTURE.md`
- `INFIVERSE-HR/QUICK_START.md`
- `INFIVERSE-HR/backend/docs/README.md`
