# Authentication Security Hardening

## 1. JWT Expiry Enforcement

- **Access token**: Set short expiry (e.g. 15–60 minutes). Already configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` in config; ensure production uses a low value (e.g. 15).
- **Enforcement**: `jwt.decode(..., options={"verify_exp": True})` (default). Do not disable `verify_exp`.
- **Clock skew**: Use `datetime.utcnow()` consistently; optional `leeway` in decode for minor skew.

## 2. Refresh Token Logic

- **Flow**: Issue long-lived refresh token (e.g. 7 days) alongside short-lived access token; store refresh token server-side (e.g. in DB or Redis) keyed by user/session.
- **Endpoint**: `POST /api/v1/auth/refresh` with body `{ "refresh_token": "..." }`. Validate refresh token, revoke it, issue new access + refresh pair.
- **Rotation**: On each refresh, invalidate old refresh token and issue a new one (refresh token rotation).

## 3. Session Invalidation

- **Session store**: Maintain a session/blocklist store (DB table or Redis) with `jti` (JWT ID) or `session_id` from token.
- **Logout**: On logout, add token `jti` to blocklist (or remove from allowlist). On each request, after decoding JWT, check `jti` is not in blocklist.
- **Password change / “logout all”**: Invalidate all sessions for that user (e.g. delete or mark all sessions for user_id).

## 4. Multi-Tenant Consistency

- Resolve tenant from request (subdomain or `X-Tenant-ID`) **before** loading user. Load user from **that tenant’s DB** only. Reject if `user.tenant_id != resolved_tenant_id` with 403.

## 5. Config Checklist

- `JWT_SECRET_KEY`: Strong random value from env; never default in production.
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Short in production (e.g. 15).
- Refresh token expiry and storage configured; blocklist/allowlist for logout and invalidation.
