# SECURITY.md

## Authentication

All endpoints except `GET /` and `GET /system/health` require authentication.

**Option A — API Key:**
```
X-API-Key: <your-api-key>
```

**Option B — JWT (HS256):**
```
Authorization: Bearer <token>
```

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `AUTH_ENABLED` | No | Set `true` (default) to enforce auth |
| `AUTH_SECRET_KEY` | Yes (if AUTH_ENABLED) | HS256 signing secret, min 32 chars |
| `AUTH_API_KEY` | Yes (if AUTH_ENABLED) | Static API key for service-to-service |

**Never commit `.env` files.** Always use `.env.example` as the template.

---

## Rate Limiting

- IP-level: 60 requests/minute
- User-level: 30 requests/minute
- Backend: Redis when `REDIS_URL` is set, in-memory fallback otherwise

```
REDIS_URL=redis://localhost:6379/0
```

---

## Secrets Management

1. Copy `.env.example` → `.env`
2. Fill in real values
3. `.env` is in `.gitignore` — never commit it
4. Rotate `AUTH_SECRET_KEY` and `AUTH_API_KEY` immediately if ever exposed

---

## Dependency Vulnerabilities

All dependencies are pinned to patched versions in `requirements.txt`:

| Package | Min safe version | CVE |
|---|---|---|
| python-multipart | 0.0.18 | GHSA-59g5-xgcq-4qw3 (DoS) |
| pymongo | 4.7.0 | GHSA-m87m-mmvp-v9qm (OOB read) |
| requests | 2.32.4 | GHSA-9hjg-9r4m-mvj7 (credential leak) |
| python-dotenv | 1.2.2 | GHSA-mf9w-mj56-hr94 (symlink) |

Run `pip install -r requirements.txt` to apply upgrades.

---

## Reporting Vulnerabilities

Open a private issue or contact the maintainer directly. Do not disclose in public issues.
