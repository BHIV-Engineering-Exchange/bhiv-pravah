# Frontend Authentication Structure

This document describes how authentication and role-based access currently work in the React frontend.

## Beginner learning order

If you are new to this codebase, read in this order:

1. `src/pages/auth/AuthPage.tsx` (what user submits)
2. `src/context/AuthContext.tsx` (how app state changes)
3. `src/services/authService.ts` (which backend endpoint is called)
4. `src/utils/authStorage.ts` (where token/user data is stored)
5. `src/components/ProtectedRoute.tsx` (how role access is enforced)
6. `src/services/api.ts` (how auth header is attached)

## Core files

- `src/services/authService.ts` - login/register/logout + token wiring
- `src/context/AuthContext.tsx` - global auth state and role resolution
- `src/utils/authStorage.ts` - storage abstraction (sessionStorage-first)
- `src/components/ProtectedRoute.tsx` - route-level authorization
- `src/pages/auth/AuthPage.tsx` - login/register UI
- `src/services/api.ts` - axios instance + auth interceptor

## Current auth model

- Backend issues JWT tokens.
- Frontend stores token and user metadata in `authStorage`.
- Request interceptor in `api.ts` adds `Authorization: Bearer <token>`.
- `ProtectedRoute` checks auth state and role before rendering page layouts.

## Storage behavior (important)

`authStorage` uses:

1. `sessionStorage` when available (default)
2. fallback to `localStorage` only if needed

This means auth is effectively per browser tab/session by default, reducing role collisions across tabs.

### Stored keys

- `auth_token`
- `user_data`
- `user_role`
- `user_email`
- `user_name`
- `isAuthenticated`
- `candidate_id`
- `backend_candidate_id`
- `client_id`
- `candidate_profile_data`

## Role handling

Supported roles:

- `candidate`
- `recruiter`
- `client`

Role source priority on restore/login:

1. JWT payload role (preferred)
2. role in stored `user_data`
3. `user_role` in storage
4. fallback default

## Login flow (actual behavior)

1. User submits credentials on `AuthPage`.
2. `AuthContext.signIn` calls `authService.login`.
3. `authService` selects endpoint based on role or fallback detection:
   - Client path: `/v1/client/login`
   - Candidate/recruiter path: `/v1/candidate/login`
4. On success, token and user metadata are stored.
5. `AuthContext` decodes JWT payload, finalizes role, sets axios default header.
6. `ProtectedRoute` grants access to the role-specific area.

Quick debug rule:

- If login succeeds but page redirects incorrectly, inspect resolved role in `AuthContext`.
- If login succeeds but API calls fail, inspect token storage and `Authorization` header.

## Registration flow (actual behavior)

1. `AuthContext.signUp` calls `authService.register`.
2. Registration stores initial metadata.
3. Auto-login runs immediately to obtain JWT.
4. Token is verified in storage before user state is marked authenticated.

## Logout flow

1. `signOut` clears all auth keys via `clearAuthStorage`.
2. Authorization header is removed.
3. User is redirected to `/auth`.

## Route protection model

- `PublicRoute`: blocks logged-in users from auth screen.
- `ProtectedRoute`: requires authentication and checks `allowedRoles`.
- Unauthorized role attempts are redirected to the correct role area.

### Beginner mental model

- `PublicRoute` = "Only for logged-out users"
- `ProtectedRoute` = "Only for logged-in users with allowed role"

## Backend dependencies

Auth currently depends on these gateway endpoints:

- `POST /v1/client/login`
- `POST /v1/client/register`
- `POST /v1/candidate/login`
- `POST /v1/candidate/register`

## Security notes

- Never persist secrets in frontend env beyond public runtime config.
- JWT validation/expiration authority remains backend; frontend only checks exp for UX/session restore.
- Keep auth keys limited to `authStorage` APIs, do not scatter direct storage access in new code.

## Debugging checklist

1. Check token existence in browser storage (`auth_token`).
2. Decode JWT payload and verify `exp` and `role`.
3. Confirm `Authorization` header is attached in network requests.
4. Confirm `VITE_API_BASE_URL` points to active gateway.
5. Validate backend login endpoint response shape (`success`, token field, user payload).

## Recommended maintenance

- Keep endpoint response shapes consistent between client/candidate login APIs.
- Avoid logging sensitive auth payloads in production builds.
- Keep `authStorage` as the only write path for auth keys.

## Full file locations

- `INFIVERSE-HR/frontend/AUTHENTICATION_STRUCTURE.md`
- `INFIVERSE-HR/frontend/src/services/authService.ts`
- `INFIVERSE-HR/frontend/src/context/AuthContext.tsx`
- `INFIVERSE-HR/frontend/src/utils/authStorage.ts`
- `INFIVERSE-HR/frontend/src/components/ProtectedRoute.tsx`
- `INFIVERSE-HR/frontend/src/pages/auth/AuthPage.tsx`
- `INFIVERSE-HR/frontend/src/services/api.ts`

