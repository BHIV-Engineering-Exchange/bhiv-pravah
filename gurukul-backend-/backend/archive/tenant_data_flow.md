# Tenant Data Flow

## 1. Request Path

1. **Incoming request**  
   e.g. `GET https://school1.gurukul.blackholeinfiverse.com/api/v1/learning/tracks`

2. **Tenant resolution (middleware / dependency)**  
   - **Subdomain**: Host = `school1.gurukul.blackholeinfiverse.com` → slug `school1` → lookup in central DB by `subdomain_slug` → `tenant_id`.  
   - **Header**: `X-Tenant-ID: <tenant_id>` (for API clients / same-domain).  
   - If neither yields a valid tenant → 400/404 (no default tenant in production).

3. **Set context**  
   `request.state.tenant_id = <tenant_id>`

4. **Database session**  
   `get_tenant_db(tenant_id)` uses DB router → returns SQLAlchemy session for **that tenant’s DB only**.

5. **Auth (if protected)**  
   JWT validated; user loaded from **same tenant DB** (by email/sub). Reject if user’s tenant_id != request tenant_id.

6. **Business logic**  
   All reads/writes use the injected tenant-scoped session → no cross-tenant data access.

## 2. Tenant Registration Flow (Admin)

1. Admin uses central DB (or bootstrap DB) to create tenant record: name, type, `database_url`, optional `subdomain_slug`.
2. Provisioner creates empty DB and runs migrations for that DB.
3. New tenant DB is ready; resolver can resolve subdomain/header to `tenant_id` and router can open sessions to it.

## 3. Data Isolation Guarantee

- **Single DB per request**: Each request gets at most one tenant DB session.
- **No cross-tenant queries**: No JOINs or shared sessions across tenant DBs.
- **Central DB**: Used only for tenant lookup and optional global config; no tenant user data.
