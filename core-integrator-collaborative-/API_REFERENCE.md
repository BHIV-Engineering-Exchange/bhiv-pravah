# API_REFERENCE.md

Base URL: `http://localhost:8001`

## Authentication

All endpoints except `GET /` and `GET /system/health` require:
```
X-API-Key: <key>
# or
Authorization: Bearer <jwt>
```

---

## Public Endpoints

### GET /
Returns API info.
```json
{"message": "Unified Backend Bridge API", "version": "1.0.0", "docs": "/docs"}
```

### GET /system/health
Returns live dependency status.
```json
{
  "status": "ok",
  "dependencies": {"database": "up", "gateway": "up", "noopur": "disabled"},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## Protected Endpoints

### POST /core
Execute a module request.

**Request:**
```json
{
  "module": "finance|education|creator|sample_text|video",
  "intent": "generate|analyze|review|get_status|list_videos|feedback|history",
  "user_id": "alphanumeric_max64",
  "data": {}
}
```

**Response:**
```json
{"status": "success", "message": "...", "result": {}}
```

---

### GET /get-history?user_id=<id>
Returns last 10 interactions for a user (max 5 per module stored).

### GET /get-context?user_id=<id>
Returns last 3 interactions for context pre-warming.

---

### GET /system/diagnostics
Returns internal status. Requires auth. No secrets or paths exposed.

### GET /system/logs/latest?limit=50
Returns last N log lines (max 200). Requires auth.

---

### POST /replay/{instruction_id}
Deterministically replay a stored instruction.

### GET /replay/validate/{instruction_id}
Check if an instruction is replayable.

### GET /replay/statistics
Replay system stats.

---

### GET /lineage/{instruction_id}
Full artifact lineage for an instruction.

### GET /artifacts/{artifact_id}
Get artifact by ID.

### GET /bucket/statistics
Bucket storage stats.

---

## Response Headers

| Header | Description |
|---|---|
| `X-Trace-Id` | Trace ID (propagated or auto-generated) |
| `X-Request-Id` | Unique per-request ID |
| `X-Response-Time-Ms` | Server processing time in ms |

---

## Error Codes

| Code | Meaning |
|---|---|
| 400 | Invalid input (bad user_id format etc.) |
| 401 | Missing or invalid authentication |
| 422 | Schema validation failed |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
