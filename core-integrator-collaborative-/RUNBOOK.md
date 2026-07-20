# RUNBOOK.md

## Starting the System

### Local (single service)
```bash
cp .env.example .env
# Fill AUTH_SECRET_KEY and AUTH_API_KEY in .env
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Docker (full stack)
```bash
cp .env.example .env
# Fill MONGO_ROOT_USER, MONGO_ROOT_PASSWORD, AUTH_SECRET_KEY, AUTH_API_KEY
docker-compose up --build
```

---

## Health Checks

```bash
# BHIV Core
curl http://localhost:8001/system/health

# All pipeline components
curl http://localhost:8004/pipeline/health
```

Expected response:
```json
{"status": "ok", "dependencies": {"database": "up", "gateway": "up"}}
```

---

## Common Incidents

### Service returns 401 on all requests
- Check `AUTH_ENABLED` env var
- Verify `AUTH_SECRET_KEY` and `AUTH_API_KEY` are set
- Test: `curl -H "X-API-Key: <key>" http://localhost:8001/system/health`

### Service returns 429 Too Many Requests
- IP or user rate limit exceeded (60/min IP, 30/min user)
- If Redis-backed: check `REDIS_URL` connectivity
- Fallback: restart service to reset in-memory counters (temporary fix)

### Database errors in /system/health
- Check `DB_PATH` env var points to a writable location
- For MongoDB: verify `MONGODB_CONNECTION_STRING` and credentials
- SQLite WAL mode is enabled — check disk space

### Port conflicts
```bash
netstat -an | findstr "8001 8003 8004 8005"
```

---

## Rollback

```bash
git log --oneline -10
git revert <commit-hash>
git push origin master
```

---

## Scaling

- Horizontal: deploy multiple instances behind a load balancer
- Update `REDIS_URL` to shared Redis instance for consistent rate limiting
- Switch `USE_MONGODB=true` for shared persistent storage across instances
- Update all service URLs in `.env` for distributed deployment

---

## Log Access

```bash
# Via API (authenticated)
curl -H "X-API-Key: <key>" http://localhost:8001/system/logs/latest?limit=100

# Direct file access
tail -f logs/bridge/*.log
```

All logs are structured JSON with `trace_id` and `request_id` fields for correlation.
