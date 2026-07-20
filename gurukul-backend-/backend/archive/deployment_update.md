# Deployment Integration (Multi-Tenant Backend)

## 1. Environment Variables

- Set on the live host/container:
  - `MULTI_TENANT_ENABLED=true`
  - `CENTRAL_DATABASE_URL` – connection string for tenant registry DB (or same as `DATABASE_URL` if registry is on same server)
  - `TENANT_BASE_DOMAIN=gurukul.blackholeinfiverse.com` (or your main domain)
  - `DATABASE_URL` – used when multi-tenant is off; for central/registry if `CENTRAL_DATABASE_URL` is unset
  - All other existing vars (JWT, API keys, etc.)

## 2. DNS / Subdomain Routing

- Wildcard or per-tenant CNAME: `*.gurukul.blackholeinfiverse.com` (or `school1.gurukul...`, `school2.gurukul...`) must resolve to the same backend (load balancer or app server). The app resolves tenant from `Host` (subdomain).

## 3. CORS

- Allow tenant subdomains: e.g. `https://*.gurukul.blackholeinfiverse.com` if your platform supports it, or list known tenant origins. Ensure `allow_credentials=True` and allowed methods/headers match frontend.

## 4. Central Registry and Per-Tenant DBs

- Run migrations (or create schema) on central DB for `tenant_registry` table (see `central_registry.py`). Insert one row per tenant: `id`, `name`, `type`, `database_url`, `subdomain_slug`.
- Each tenant DB must have the application schema (users, cohorts, etc.). Run same migrations against each tenant DB.

## 5. Health Check

- `/health` should not require tenant. Optionally check central DB and one tenant DB connectivity. Keep response minimal (no internal secrets).
