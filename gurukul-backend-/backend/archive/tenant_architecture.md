# Multi-Tenant Architecture (Gurukul Backend)

## 1. Tenant Model & tenant_id System

- **Tenant**: Logical school/institution. Each tenant has a unique `tenant_id` (UUID string).
- **Tenant record** (central DB): `id`, `name`, `type` (INSTITUTION | FAMILY), `database_url` (per-tenant DB connection string), `subdomain_slug` (optional, for subdomain resolution).
- **tenant_id** is the single source of truth for isolation: all data access is scoped by the DB that belongs to that tenant.

## 2. DB-per-Tenant vs Schema-per-Tenant

| Criteria | DB-per-tenant | Schema-per-tenant |
|----------|----------------|------------------|
| Isolation | Strong (separate process/DB) | Weaker (same DB) |
| Backup/restore | Per-tenant | Per-schema or full DB |
| Scaling | Per-tenant (e.g. move heavy tenant) | Shared |
| Complexity | Higher (many connections) | Lower |
| **Choice** | **Recommended** | — |

**Decision: DB-per-tenant.** Each tenant has a dedicated database; connection is chosen at request time via `tenant_id`.

## 3. High-Level Architecture

```
[Request] → [Tenant Resolver] → tenant_id (subdomain or X-Tenant-ID)
                ↓
[DB Router] → Central DB (tenant registry) → resolve tenant_id → Per-tenant DB URL
                ↓
[get_tenant_db(tenant_id)] → Session for that tenant's DB only
                ↓
[All queries] → Run only against that session (no cross-tenant access)
```

## 4. Components

- **Central database**: Stores tenant registry (id, name, type, database_url, subdomain_slug). Used only for tenant lookup and optional admin.
- **Per-tenant databases**: Same schema as current Gurukul (users, cohorts, flashcards, etc.). One DB per tenant.
- **Tenant resolver** (`tenant_resolver.py`): Derives `tenant_id` from request (subdomain or `X-Tenant-ID` header).
- **DB router** (`db_router.py`): Provides `get_central_db()` and `get_tenant_db(tenant_id)`; caches engines/sessions per tenant.

## 5. Security Principles

- No request is served without a resolved, valid `tenant_id` (except health/static).
- JWT and session checks run **after** tenant resolution; user must belong to the resolved tenant’s DB.
- No shared session between tenants; no cross-tenant queries.
