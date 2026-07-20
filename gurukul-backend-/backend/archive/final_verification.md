# Full System Verification (Multi-Tenant)

## 1. Tenant Creation

- **Step**: Use admin flow to create a tenant (or insert into central `tenant_registry`: id, name, type, database_url, subdomain_slug). Create the per-tenant DB and run migrations.
- **Verify**: Tenant appears in registry; subdomain or `X-Tenant-ID` resolves to that tenant.

## 2. Tenant Login

- **Step**: From tenant A’s subdomain (or with `X-Tenant-ID: A`), register or login. Receive JWT.
- **Verify**: Login returns 200 and JWT; `/api/v1/auth/me` (or equivalent) returns user belonging to tenant A. Same from tenant B with a different user.

## 3. Tenant Isolation

- **Step**: With tenant A JWT, call an endpoint with `X-Tenant-ID: B` (or from tenant B subdomain).
- **Verify**: 403 or 404 – no data from tenant B returned to tenant A’s user. Reverse test: tenant B user cannot access with tenant A resolution.

## 4. Two Tenants, Two DBs

- **Proof**: Configure two tenants with different `database_url` values. Create user in each. Confirm each user’s data is stored in and read from the correct DB only (e.g. by DB logs or by querying each DB and checking only that tenant’s data exists).

## 5. Video / Evidence

- Record a short run: (1) Create/login tenant A and show response, (2) Create/login tenant B and show response, (3) Show isolation (e.g. A’s token with B’s tenant ID rejected or empty). Optionally show two different DBs (e.g. connection strings or DB names in config) to prove DB-per-tenant.
