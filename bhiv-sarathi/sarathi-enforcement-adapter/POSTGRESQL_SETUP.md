# Sarathi Persistent Audit — PostgreSQL Setup Guide

**Author:** Hemanth B
**System:** Sarathi Governance Kernel — Persistent Audit Layer (v5.0)
**Host Organization:** Blackhole Infiverse (BHIV)
**Updated:** March 2026

---

## Overview

PostgreSQL is the production audit backend for Sarathi v5.0. All enforcement decisions, hash chain entries, key events, and system events are persisted to PostgreSQL for durable, queryable, tamper-resistant audit.

**The system works without PostgreSQL** — it falls back to in-memory audit. PostgreSQL is required only for production-grade persistent audit.

---

## Option 1: Docker (Recommended for Local Development)

```bash
# Start PostgreSQL 15 on port 5433
docker run -d \
  --name sarathi-db \
  -p 5433:5432 \
  -e POSTGRES_USER=sarathi_admin \
  -e POSTGRES_PASSWORD=sarathi_secure_2024 \
  -e POSTGRES_DB=sarathi_governance \
  postgres:15

# Verify
docker exec sarathi-db pg_isready -U sarathi_admin
# Expected: accepting connections

# Connect via psql
docker exec -it sarathi-db psql -U sarathi_admin -d sarathi_governance
```

## Option 2: Native PostgreSQL Install

1. Install PostgreSQL 15+ from https://www.postgresql.org/download/
2. Create database and user:

```sql
CREATE USER sarathi_admin WITH PASSWORD 'sarathi_secure_2024';
CREATE DATABASE sarathi_governance OWNER sarathi_admin;
GRANT ALL PRIVILEGES ON DATABASE sarathi_governance TO sarathi_admin;
```

## Option 3: Cloud Managed

- **AWS RDS**: PostgreSQL 15+, db.t3.micro for dev
- **Google Cloud SQL**: PostgreSQL 15+
- **Azure Database**: PostgreSQL Flexible Server

---

## Environment Variables

Set these before running the Sarathi binary:

```bash
export SARATHI_DB_HOST=localhost
export SARATHI_DB_PORT=5433
export SARATHI_DB_NAME=sarathi_governance
export SARATHI_DB_USER=sarathi_admin
export SARATHI_DB_PASSWORD=sarathi_secure_2024
export SARATHI_DB_SSLMODE=disable    # use verify-full for production
```

---

## Schema

The schema is auto-created on first connection via `EnsureSchema()`. 7 tables:

| Table | Purpose |
|-------|---------|
| `sarathi_enforcement_log` | Every enforcement decision (core audit trail) |
| `sarathi_enforcement_chain` | Enforcement hash chain (append-only) |
| `sarathi_execution_chain` | Execution hash chain (append-only) |
| `sarathi_token_log` | Capability token issuance and consumption |
| `sarathi_key_events` | Key lifecycle events (generation, rotation, revocation) |
| `sarathi_system_events` | System events (startup, shutdown, config changes) |
| `sarathi_bridge_log` | Bridge routing log (every request through the gated bridge) |

10 indexes on common query patterns (correlation_id, agent_id, verdict, timestamp, hashes).

---

## Useful Queries

```sql
-- Recent enforcement decisions
SELECT timestamp, agent_id, action, verdict, enforcement_hash
FROM sarathi_enforcement_log
ORDER BY timestamp DESC LIMIT 20;

-- Denied requests
SELECT timestamp, agent_id, action, block_reason
FROM sarathi_enforcement_log
WHERE verdict = 'DENY'
ORDER BY timestamp DESC;

-- Chain integrity
SELECT COUNT(*) as total_entries FROM sarathi_enforcement_chain;

-- System events
SELECT timestamp, event_type, detail
FROM sarathi_system_events
ORDER BY timestamp DESC LIMIT 10;

-- Audit statistics
SELECT verdict, COUNT(*) as count
FROM sarathi_enforcement_log
GROUP BY verdict;
```

---

## Cleanup

```bash
docker stop sarathi-db
docker rm sarathi-db
```

---

## Security Notes

- In production, use `SARATHI_DB_SSLMODE=verify-full`
- Use IAM-based authentication where available (AWS RDS, GCP Cloud SQL)
- All tables are append-only by design — no UPDATE or DELETE in normal operation
- Consider PostgreSQL row-level security for multi-tenant isolation
- Set up automated backups with point-in-time recovery
