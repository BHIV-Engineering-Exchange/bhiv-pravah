# Step-by-Step: Two Tenants, Two Databases, Isolation (Real-Time with Frontend + Backend)

Follow these steps in order. At the end you will have: **two tenants**, **two databases**, and **isolation** verified from the Gurukul frontend.

---

## Prerequisites (one-time)

1. **PostgreSQL** running (e.g. localhost:5432). Create the central DB only:
   ```sql
   CREATE DATABASE gurukul_central;
   ```

2. **Gurukul backend/.env** (adjust URLs if needed):
   ```env
   MULTI_TENANT_ENABLED=true
   CENTRAL_DATABASE_URL=postgresql://postgres:Somsid%402014@localhost:5432/gurukul_central
   DATABASE_URL=postgresql://postgres:Somsid%402014@localhost:5432/gurukul_central
   TENANT_BASE_DOMAIN=gurukul.blackholeinfiverse.com
   EMS_API_KEY=ems-gurukul-shared-secret-2024
   ```

3. **EMS .env** (EMS System folder):
   ```env
   GURUKUL_API_BASE_URL=http://localhost:3000
   GURUKUL_API_KEY=ems-gurukul-shared-secret-2024
   ```
   Plus your EMS `DATABASE_URL` and other EMS vars.

4. **PostgreSQL user** must be allowed to **CREATE DATABASE** (e.g. superuser or `CREATEDB`).

---

---

## Step-by-step: Backend then Frontend (how to see the tenant)

### BACKEND – Step 1: Start Gurukul backend

```bash
cd backend
python -m uvicorn app.main:app --reload --port 3000
```

- **What you’ll see:** Terminal shows `Application startup complete` and `Uvicorn running on http://127.0.0.1:3000`.
- **Why:** Creates `tenant_registry` table in `gurukul_central` on first run.

---

### BACKEND – Step 2: Create two tenants (two DBs)

**Option A – From EMS frontend (if you use EMS):**  
Start EMS backend (port 8000) and EMS frontend → log in as super admin → create **School 1**, then **School 2**. Each create calls Gurukul and provisions a tenant.

**Option B – From API (no EMS UI):** In a **new terminal** (Gurukul backend must be running):

```bash
curl -X POST http://localhost:3000/api/v1/ems/provision-tenant -H "Content-Type: application/json" -H "X-API-Key: ems-gurukul-shared-secret-2024" -d "{\"name\":\"School One\",\"subdomain_slug\":\"school_1\"}"
curl -X POST http://localhost:3000/api/v1/ems/provision-tenant -H "Content-Type: application/json" -H "X-API-Key: ems-gurukul-shared-secret-2024" -d "{\"name\":\"School Two\",\"subdomain_slug\":\"school_2\"}"
```

- **What you’ll see:** Each curl returns JSON with `tenant_id` (UUID), `subdomain_slug`, and `message`.
- **Backend check – see tenants in DB:** In PostgreSQL run:
  ```sql
  SELECT id, name, subdomain_slug FROM tenant_registry;
  ```
  You should see **two rows**. Copy both **id** values (e.g. `a1b2c3d4-...` and `e5f6g7h8-...`) — these are **Tenant 1 ID** and **Tenant 2 ID** for the frontend.

---

### BACKEND – Step 3: See which tenant the backend is using (optional)

In browser or curl:

```bash
curl -s http://localhost:3000/api/v1/tenant-info -H "X-Tenant-ID: PASTE_FIRST_UUID_HERE"
```

- **What you’ll see:** JSON with `multi_tenant_enabled: true`, `resolved_tenant_id` = the UUID you sent. Change the header to the second UUID and call again — `resolved_tenant_id` changes. So the **backend** is resolving the tenant from the header.

---

### FRONTEND – Step 4: Start Gurukul frontend

```bash
cd Frontend
npm run dev
```

Open the URL (e.g. http://localhost:5173).

---

### FRONTEND – Step 5: See tenant in the frontend (tenant-info)

1. Press **F12** → **Console**.
2. Set the tenant and call tenant-info:
   ```js
   localStorage.setItem('gurukul_tenant_id', 'PASTE_TENANT_1_UUID_HERE');
   fetch('http://localhost:3000/api/v1/tenant-info', { headers: { 'X-Tenant-ID': localStorage.getItem('gurukul_tenant_id') } }).then(r => r.json()).then(console.log);
   ```
3. **What you’ll see:** In the console, an object with `resolved_tenant_id` equal to Tenant 1’s UUID. So the **frontend** is sending the tenant and the **backend** is returning it.
4. Switch to Tenant 2 and run again:
   ```js
   localStorage.setItem('gurukul_tenant_id', 'PASTE_TENANT_2_UUID_HERE');
   fetch('http://localhost:3000/api/v1/tenant-info', { headers: { 'X-Tenant-ID': localStorage.getItem('gurukul_tenant_id') } }).then(r => r.json()).then(console.log);
   ```
   **What you’ll see:** `resolved_tenant_id` is now Tenant 2’s UUID. So you can **see** which tenant is active from the frontend.

---

### FRONTEND – Step 6: Register user for Tenant 1 (user in DB 1)

1. In Console:
   ```js
   localStorage.setItem('gurukul_tenant_id', 'TENANT_1_UUID');   // use your real UUID
   location.href = '/signup';
   ```
2. On the Sign Up page, register e.g. **user1@school1.com** / **test123**.
3. **What you’ll see:** You are logged in and see the dashboard. This user is stored in **DB 1** (`gurukul_tenant_school_1`).

---

### FRONTEND – Step 7: Register user for Tenant 2 (user in DB 2)

1. Log out (or open an incognito window).
2. In Console:
   ```js
   localStorage.setItem('gurukul_tenant_id', 'TENANT_2_UUID');   // use your real UUID
   location.href = '/signup';
   ```
3. Register **user2@school2.com** / **test123**.
4. **What you’ll see:** You are logged in. This user is in **DB 2** (`gurukul_tenant_school_2`). So **two tenants, two databases**, each with one user.

---

### FRONTEND – Step 8: See isolation (tenant A cannot see tenant B)

1. Log in as **user1@school1.com** with `gurukul_tenant_id` = Tenant 1 UUID. Use the app — everything is from DB 1.
2. **Without logging out**, in Console run:
   ```js
   localStorage.setItem('gurukul_tenant_id', 'TENANT_2_UUID');
   location.reload();
   ```
3. **What you’ll see:** After reload, the app calls `/auth/me` with **Tenant 2** and user1’s token. User1 is not in Tenant 2’s DB → **401** or you are logged out. So **isolation works**: Tenant 1’s user cannot see Tenant 2’s DB.
4. Log in as **user2@school2.com** with Tenant 2 set. Then set `gurukul_tenant_id` to Tenant 1 and reload — again **401**. So Tenant 2’s user cannot see Tenant 1’s DB.

---

## Summary: What you see where

| Where | What you see |
|-------|----------------|
| **Backend terminal** | Gurukul on :3000; provision-tenant returns `tenant_id` per school. |
| **PostgreSQL** | `tenant_registry` has two rows; DBs `gurukul_tenant_school_1` and `gurukul_tenant_school_2` exist. |
| **Backend API** | `GET /api/v1/tenant-info` with `X-Tenant-ID` returns that `resolved_tenant_id`. |
| **Frontend Console** | `localStorage.gurukul_tenant_id` + fetch to tenant-info shows which tenant the backend resolved. |
| **Frontend app** | User1 (Tenant 1) and User2 (Tenant 2) each log in only when their tenant is set; switching tenant with same token → 401 (isolation). |

Frontend sends **X-Tenant-ID** from `localStorage.gurukul_tenant_id` on every request (apiClient + AuthContext). Set it in Console before Sign Up / Sign In to choose which tenant (which DB) you are using.
