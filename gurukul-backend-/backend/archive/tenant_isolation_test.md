# Tenant Isolation Validation

## Objective

Ensure **no cross-tenant data access**: Tenant A cannot read or write Tenant B data.

## How Isolation Is Enforced

1. **Request → tenant_id**: Every request gets a single `tenant_id` from subdomain or `X-Tenant-ID` header (see `tenant_resolver.py`).
2. **Single DB per request**: `get_db(request)` yields a session for **only that tenant’s database** (see `db_router.py`). There is no shared session across tenants.
3. **No tenant_id in query**: Per-tenant DBs do not contain other tenants’ data; the physical DB is the boundary.

## Test: Tenant A Cannot Read Tenant B Data

### Prerequisites

- Two tenants in central registry with different `database_url` values (e.g. `gurukul_tenant_a`, `gurukul_tenant_b`).
- User U1 in tenant A DB, user U2 in tenant B DB.

### Test 1: Header-based

1. Login as U1, get JWT.
2. Call `GET /api/v1/auth/me` (or any tenant-scoped endpoint) with:
   - `Authorization: Bearer <U1_token>`
   - `X-Tenant-ID: <tenant_B_id>`
3. **Expected**: 404 Tenant not found, or 403 (e.g. if we add a check that user’s tenant_id matches request tenant_id).  
   **Critical**: Response must never return U2’s data. If the backend uses only request tenant_id for DB selection, then with `X-Tenant-ID: B` the DB is B’s; the JWT still identifies U1 who is in DB A. So we must **validate that the authenticated user belongs to the resolved tenant** (see below).

### Test 2: Subdomain

1. Login as U1 on tenant A (e.g. `schoolA.gurukul.blackholeinfiverse.com`), get JWT.
2. Call same endpoint from `schoolB.gurukul.blackholeinfiverse.com` (tenant B subdomain) with U1’s JWT.
3. **Expected**: 403 Forbidden – “User does not belong to this tenant” (user’s tenant_id ≠ request tenant_id). No data from tenant B’s DB for U1.

### Validation Rule to Implement

In auth (e.g. `get_current_user` or a dependency): after loading user from **tenant-scoped DB** (session from `get_db(request)`), ensure `user.tenant_id == request_tenant_id`. If the request was resolved to tenant B but the user is in tenant A, return 403. This prevents “tenant spoofing” (using a valid JWT with another tenant’s subdomain/header).

## Test 3: Direct IDOR

1. Tenant A user gets resource ID from their tenant (e.g. flashcard id from DB A).
2. Send request with `X-Tenant-ID: B` and the same resource ID.
3. **Expected**: 404 or empty – tenant B’s DB does not contain that ID. So no cross-tenant leak.

## Checklist

- [ ] Two tenants use two different DBs (different `database_url` in registry).
- [ ] Request with tenant A resolution never gets a session for tenant B.
- [ ] User from tenant A cannot access tenant B by switching subdomain or `X-Tenant-ID`.
- [ ] Auth layer rejects when JWT user’s tenant_id ≠ resolved request tenant_id.
