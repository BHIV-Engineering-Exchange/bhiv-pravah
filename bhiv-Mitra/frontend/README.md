# Frontend Workspace

This repo contains two frontend-related folders:

- `frontend/` -> active React app for Vercel deployment
- `Signup/` -> legacy standalone auth microservice kept only for reference

## Active Architecture

The current integrated deployment uses:

- `../backend` on Render (or Docker/Kubernetes)
- `./frontend` on Vercel

Authentication is served by the FastAPI backend at:

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`

## Components

### Chat Interface
- `ChatMessage.tsx` - Core message rendering with safety/intent/TTS
- `MessageInput.tsx` - Auto-resize textarea with char limit
- `ChatSidebar.tsx` - Conversation history

### Authentication
- `Login.tsx` - Login form
- `Signup.tsx` - Registration form

### Dashboard (NEW)
- `BHIVDashboard.tsx` - Ecosystem overview with KPIs
- `ReplayVisualization.tsx` - Trace pipeline visualization
- `SystemHealthPanel.tsx` - Real-time health monitoring

### Utilities
- `translations.ts` - System internals to friendly text
- `uxTranslations.ts` - Extended UX translations

## Services

- `api.ts` - Backend API service (V3.0.0 contract)
- `authApi.ts` - Auth API service (signup/login/me/logout)

## Contexts

- `AuthContext.tsx` - JWT authentication state
- `LanguageContext.tsx` - Language/i18n state

## The `Signup/` service is deprecated and should not be part of the default deployment path.
