# Database Security Hardening

## 1. Connection Pooling

- Already in use: SQLAlchemy `pool_size`, `max_overflow`, `pool_pre_ping`, `pool_recycle` in `database.py` and `db_router.py`.
- Per-tenant engines in `db_router` use bounded pool sizes to avoid exhausting connections.

## 2. Credential Protection

- **No hardcoded secrets**: All DB URLs and secrets come from environment variables (e.g. `DATABASE_URL`, `CENTRAL_DATABASE_URL`, `JWT_SECRET_KEY`). Use `.env` (not committed) or a secret manager.
- **Principle of least privilege**: DB user used by the app should have only the rights needed (e.g. no DROP, no superuser). Use separate users for migrations if needed.

## 3. No Hardcoded Secrets in Code

- Config reads from `os.environ` / `.env` via pydantic-settings. Defaults for sensitive values (e.g. `JWT_SECRET_KEY`) must be overridden in production; fail startup if critical secrets are missing in prod.

## 4. TLS for DB Connections

- In production, use `postgresql://...?sslmode=require` (or equivalent) so connections to the database are encrypted.
