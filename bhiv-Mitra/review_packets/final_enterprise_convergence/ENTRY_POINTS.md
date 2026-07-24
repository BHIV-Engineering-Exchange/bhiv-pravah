# MITRA Entry Points

## Primary API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | None | API info and endpoint listing |
| `/health` | GET | None | Health check with MongoDB probe |
| `/health/system` | GET | None | Deep system health snapshot |
| `/metrics` | GET | None | Prometheus metrics endpoint |

## Authentication Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/signup` | POST | None | User registration |
| `/api/auth/login` | POST | None | User authentication |
| `/api/auth/me` | GET | JWT | Get current user |
| `/api/auth/logout` | POST | JWT | User logout |

## Core Assistant

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/assistant` | POST | API Key | Main chat endpoint (V3.0.0) |
| `/api/mitra/evaluate` | POST | API Key | Policy evaluation |

## Ecosystem Integration (NEW)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/ecosystem/products` | GET | API Key | List all BHIV products |
| `/api/ecosystem/manifests` | GET | API Key | Get integration manifests |
| `/api/ecosystem/health` | GET | API Key | Integration health check |
| `/api/ecosystem/query` | POST | API Key | Query a BHIV product |
| `/api/ecosystem/execute` | POST | API Key | Execute on a BHIV product |
| `/api/ecosystem/snapshot` | GET | API Key | Full registry snapshot |

## Execution & Webhooks

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/webhooks/whatsapp` | POST/GET | Verify Token | WhatsApp inbound |
| `/webhooks/telegram` | POST/GET | None | Telegram inbound |
| `/webhooks/email` | POST | None | Email inbound |
| `/webhooks/instagram` | POST/GET | Verify Token | Instagram inbound |
| `/webhooks/call` | POST | None | Telephony inbound |

## Voice

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/tts` | POST | API Key | Text-to-speech |
| `/api/tts/status` | GET | None | TTS engine status |

## Replay & Audit

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/replay/{trace_id}` | POST | API Key | Replay a trace |
| `/api/replay/{trace_id}/stages` | GET | API Key | Get trace stages |
| `/api/replay/compare` | POST | API Key | Compare traces |

## Observability

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/metrics` | GET | API Key | Basic system metrics |
| `/api/metrics/system` | GET | API Key | Detailed system metrics |
| `/api/metrics/enforcement` | GET | API Key | Enforcement metrics |

## Security Model

1. **API Key**: `X-API-Key` header on all `/api/*` routes
2. **JWT**: `Authorization: Bearer <token>` for user sessions
3. **Rate Limiting**: Per-IP throttling (100 req/min default)
4. **Gateway Auth**: HMAC-signed executor tokens
5. **SHA-256 Traces**: Every action logged with integrity hash

## Request Contracts

### Assistant Request (V3.0.0)

```json
{
  "version": "3.0.0",
  "input": {
    "message": "string",
    "summarized_payload": {},
    "audio_data": "bytes",
    "audio_format": "mp3"
  },
  "context": {
    "platform": "web",
    "device": "desktop",
    "session_id": "string",
    "voice_input": false,
    "preferred_language": "auto"
  }
}
```

### Ecosystem Query Request

```json
{
  "product": "UniGuru",
  "action": "courses",
  "payload": {}
}
```

### Ecosystem Execute Request

```json
{
  "product": "SETU",
  "action": "create_service_request",
  "payload": {},
  "user_id": "string",
  "session_id": "string"
}
```
