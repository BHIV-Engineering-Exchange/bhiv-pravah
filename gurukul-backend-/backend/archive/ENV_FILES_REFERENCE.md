# .env Files: Gurukul vs EMS (Separate, Not Shared)

Use **two different .env files**. Do not merge them or use the same file for both apps.

---

## 1. Gurukul Backend — `backend/.env`

Use this only for the **Gurukul** backend. EMS does not read this file.

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Default/fallback DB (e.g. first tenant or when multi-tenant off). |
| `MULTI_TENANT_ENABLED` | `true` = DB-per-tenant; `false` = single DB. |
| `CENTRAL_DATABASE_URL` | Tenant registry DB (e.g. `.../gurukul_central`). |
| `TENANT_BASE_DOMAIN` | Base domain for subdomain resolution (e.g. `gurukul.blackholeinfiverse.com`). |
| `JWT_SECRET_KEY` | Gurukul JWT signing secret (change in production). |
| `EMS_API_KEY` | Optional. If set, EMS must send this as `X-API-Key` when calling Gurukul (e.g. provision-tenant). |
| `EMS_API_BASE_URL` | Gurukul → EMS (e.g. for student sync). Not for multi-tenant. |
| `EMS_ADMIN_EMAIL`, `EMS_ADMIN_PASSWORD` | Optional; for auto-creating students in EMS from Gurukul. |
| (+ API keys, PORT, etc.) | Rest of Gurukul config. |

**Remove from Gurukul .env:**  
Anything like `GURUKUL_API_BASE_URL` or `GURUKUL_API_KEY` — those belong in **EMS** .env (EMS calls Gurukul, not the other way around for that).

---

## 2. EMS System — `EMS System/.env` (or `EMS System/app/.env`)

Use this only for the **EMS** app. Gurukul does not read this file.

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | **EMS own DB** (e.g. `.../school_management_db`). Different from Gurukul. |
| `SECRET_KEY` | EMS JWT secret. |
| `GURUKUL_API_BASE_URL` | Gurukul backend URL (e.g. `http://localhost:3000`). EMS calls this for provision-tenant and student sync. |
| `GURUKUL_API_KEY` | Optional. If Gurukul has `EMS_API_KEY` set, set this to the **same value** so EMS can call provision-tenant. |
| `FRONTEND_URL` | EMS frontend URL (e.g. for password reset links). |
| (+ email, BREVO/SENDGRID, etc.) | Rest of EMS config. |

**Remove from EMS .env:**  
Anything like `MULTI_TENANT_ENABLED`, `CENTRAL_DATABASE_URL`, `TENANT_BASE_DOMAIN`, or `EMS_API_KEY` — those are **Gurukul-only**. EMS does not need tenant registry or DB-per-tenant vars.

---

## 3. Same Value, Different Names (When Wiring EMS ↔ Gurukul)

For **provision-tenant** (EMS → Gurukul):

- **Gurukul** `.env`: `EMS_API_KEY=your-secret-key`
- **EMS** `.env`: `GURUKUL_API_KEY=your-secret-key` (same value)

So the **value** is the same; the **variable name** is different in each app. Keep both; do not remove one because the other exists.

---

## 4. Summary

| | Gurukul `backend/.env` | EMS `EMS System/.env` |
|---|------------------------|------------------------|
| Same file? | No | No |
| DATABASE_URL | Gurukul DB(s) | EMS DB (school_management_db) |
| Multi-tenant vars | Yes (MULTI_TENANT_ENABLED, CENTRAL_DATABASE_URL, etc.) | No — remove if present |
| GURUKUL_* | No — remove if present | Yes (GURUKUL_API_BASE_URL, GURUKUL_API_KEY) |
| EMS_API_KEY | Yes (for EMS calling Gurukul) | No (EMS uses GURUKUL_API_KEY with same value) |

Keep both .env files; keep each app’s vars in its own file; remove from each file any vars that belong to the other app.
