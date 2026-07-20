# How to See Multi-Tenant Output (Proof: Two Tenants, Two DBs)

## 1. What’s Actually Done (Not Placeholder)

- **tenant_resolver.py** – real code; resolves tenant from subdomain or `X-Tenant-ID`.
- **db_router.py** – real code; connects to the correct DB per tenant using central registry.
- **database.get_db(request)** – wired; when `MULTI_TENANT_ENABLED=true`, every route using `Depends(get_db)` gets that tenant’s DB session.
- **main.py** – tenant middleware + central table creation on startup; API security (rate limit, payload size).
- **Docs** – all delivered (architecture, data flow, isolation test, auth security, attack surface, db security, secrets, security test report, deployment, final verification).

**EMS wiring:** When super admin creates a school in EMS, EMS calls Gurukul provision-tenant; Gurukul creates the tenant DB and schema automatically (in Gurukul backend only). One school in EMS = one tenant in Gurukul; tenant DB and schema are created in Gurukul when provision-tenant is called. Tenant DBs are created automatically; you only create gurukul_central manually.

---

## 2. Prerequisites (One-Time)

1. **PostgreSQL**: Create **only** the central DB. Tenant DBs (`gurukul_tenant_school_1`, etc.) are **created automatically** when a new school is created in EMS (Gurukul provision-tenant).
   ```sql
   CREATE DATABASE gurukul_central;
   ```

2. **Gurukul backend/.env** — add multi-tenant + the **shared secret** (copy this exact value into EMS in step 4):
   ```env
   MULTI_TENANT_ENABLED=true
   CENTRAL_DATABASE_URL=postgresql://postgres:Somsid%402014@localhost:5432/gurukul_central
   DATABASE_URL=postgresql://postgres:Somsid%402014@localhost:5432/gurukul_central
   TENANT_BASE_DOMAIN=gurukul.blackholeinfiverse.com
   EMS_API_KEY=ems-gurukul-shared-secret-2024
   ```

3. **Start Gurukul once** so `tenant_registry` table is created in `gurukul_central`.

4. **EMS .env** — use the **same secret** as above (copy-paste the value from `EMS_API_KEY`):
   ```env
   GURUKUL_API_BASE_URL=http://localhost:3000
   GURUKUL_API_KEY=ems-gurukul-shared-secret-2024
   ```
   So: **Gurukul** has `EMS_API_KEY=...` and **EMS** has `GURUKUL_API_KEY=...` with the **exact same value** (e.g. `ems-gurukul-shared-secret-2024`). Change the value in production to a strong random string.

5. **Create schools in EMS** (super admin → create school). For each new school, EMS calls Gurukul → Gurukul **automatically** creates the tenant DB (e.g. `gurukul_tenant_school_1`) and applies the schema. No manual CREATE DATABASE or INSERT for tenants.

**Manual path (without EMS):** If you want two tenants without EMS, call **POST /api/v1/ems/provision-tenant** twice (with name + subdomain_slug); Gurukul creates each tenant’s DB and schema. Or create tenant DBs yourself and insert into `tenant_registry`.

---

## 3. How to See the Output

### A. Tenant resolution (no login)

Call the tenant-info endpoint with different headers:

```bash
# Tenant 1 (use UUID from tenant_registry)
curl -s http://localhost:3000/api/v1/tenant-info -H "X-Tenant-ID: 11111111-1111-1111-1111-111111111101"

# Tenant 2
curl -s http://localhost:3000/api/v1/tenant-info -H "X-Tenant-ID: 22222222-2222-2222-2222-222222222202"
```

**Expected:**  
First call: `"resolved_tenant_id": "11111111-1111-1111-1111-111111111101"`.  
Second call: `"resolved_tenant_id": "22222222-2222-2222-2222-222222222202"`.  
So the backend resolves tenant per request.

### B. Two tenants, two DBs (isolation)

1. **Register user for tenant 1**
   ```bash
   curl -s -X POST http://localhost:3000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -H "X-Tenant-ID: 11111111-1111-1111-1111-111111111101" \
     -d '{"email":"student1@school1.com","password":"test123","full_name":"Student One","role":"STUDENT"}'
   ```
   Save the returned `access_token`.

2. **Register user for tenant 2**
   ```bash
   curl -s -X POST http://localhost:3000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -H "X-Tenant-ID: 22222222-2222-2222-2222-222222222202" \
     -d '{"email":"student2@school2.com","password":"test123","full_name":"Student Two","role":"STUDENT"}'
   ```

3. **Verify isolation**
   - With tenant 1 token, call a protected endpoint **with X-Tenant-ID: tenant 2** (or vice versa). You should get 401 (user not in that tenant’s DB) or no data from the other tenant. So: two tenants, two DBs, isolation working.

### C. Subdomain (when DNS is set)

If you have `school1.gurukul.blackholeinfiverse.com` and `school2.gurukul.blackholeinfiverse.com` pointing to your server, open in browser or curl:

- `https://school1.gurukul.../api/v1/tenant-info` → `tenant_slug`: `school1`, `resolved_tenant_id`: tenant 1 UUID.
- `https://school2.gurukul.../api/v1/tenant-info` → tenant 2.

---

## 4. Summary

| Question | Answer |
|----------|--------|
| Are all deliverables done? | Yes: code + docs; auth “refresh token / session invalidation” are documented in auth_security_upgrade.md, not full code. |
| Is it wired or placeholder? | Wired: resolver → middleware; get_db → db_router → tenant DB. |
| Wired with EMS? | Yes. EMS create-school calls Gurukul provision-tenant; Gurukul creates tenant DB + schema and registers tenant. |
| How to see output? | Set env, create DBs, insert registry, then use `/api/v1/tenant-info` and register/login with `X-Tenant-ID` as above. |

For a **video proof**: record (1) two different `X-Tenant-ID` calls to `/api/v1/tenant-info` showing two `resolved_tenant_id`s, (2) register one user per tenant, (3) show that tenant 1 token + tenant 2 header does not return tenant 2 data (isolation).
